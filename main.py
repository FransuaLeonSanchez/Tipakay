from fastapi import FastAPI, Request, Response
import uvicorn
from dotenv import load_dotenv
import os
import logging
import time
import traceback

from database import delete_chat_history, get_db_connection
from llm import get_completion
import twilio_chat

load_dotenv()
app = FastAPI()
PORT = int(os.getenv("PORT", "3000"))

# Configuración simple pero efectiva del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

# Desactivar logs innecesarios
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


@app.post("/webhook")
async def receive_message(request: Request):
    start_time = time.time()
    try:
        form_data = await request.form()
        message, from_number = await twilio_chat.process_incoming_message(form_data)

        if message and from_number:
            logger.info(
                f"Mensaje recibido | Número: {from_number} | "
                f"Longitud mensaje: {len(message)} caracteres | "
                f"Tiempo: {(time.time() - start_time):.2f}s"
            )

            # Obtener respuesta de OpenAI con historial
            ai_response = get_completion(message, from_number)

            logger.info(
                f"Respuesta enviada | Número: {from_number} | "
                f"Longitud respuesta: {len(ai_response)} caracteres | "
                f"Tiempo total: {(time.time() - start_time):.2f}s"
            )

        return Response(
            content="<?xml version='1.0' encoding='UTF-8'?><Response></Response>",
            media_type="application/xml",
        )
    except Exception as e:
        logger.error(
            f"Error en webhook | "
            f"Tipo: {type(e).__name__} | "
            f"Error: {str(e)} | "
            f"Tiempo: {(time.time() - start_time):.2f}s | "
            f"Traza: {traceback.format_exc()}"
        )
        return Response(
            content="<?xml version='1.0' encoding='UTF-8'?><Response></Response>",
            media_type="application/xml",
        )


@app.delete("/conversation/{phone_number}")
async def delete_conversation(phone_number: str):
    try:
        # Limpiar el número de teléfono
        clean_number = phone_number.replace("whatsapp:", "").replace("+", "")

        logger.info(f"Iniciando borrado para número: {clean_number}")

        # Para almacenar el estado de cada operación
        deletion_status = {
            "cache": False,
            "database": False
        }

        try:
            # Intentar limpiar caché
            from llm import clear_cache_for_number, get_cached_completion
            get_cached_completion.cache_clear()
            deletion_status["cache"] = True
            logger.info(f"Caché limpiado para el número: {clean_number}")
        except Exception as cache_error:
            logger.error(f"Error limpiando caché: {str(cache_error)}")

        try:
            # Intentar eliminar de la base de datos
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM conversations WHERE phone_number = %s",
                    (clean_number,)
                )
                conn.commit()
                deletion_status["database"] = True
                logger.info(f"Base de datos limpiada para el número: {clean_number}")
        except Exception as db_error:
            logger.error(f"Error limpiando base de datos: {str(db_error)}")
        finally:
            if conn:
                conn.close()

        # Preparar mensaje detallado
        details = []
        if deletion_status["cache"]:
            details.append("caché")
        if deletion_status["database"]:
            details.append("base de datos")

        if details:
            message = f"Conversación eliminada de: {' y '.join(details)}"
            status = "success"
        else:
            message = "No se pudo eliminar la conversación de ningún sistema"
            status = "error"

        return {
            "status": status,
            "message": message,
            "details": {
                "cache_deleted": deletion_status["cache"],
                "database_deleted": deletion_status["database"]
            }
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error en proceso de borrado - Número: {clean_number} - Error: {error_msg}")
        return {
            "status": "error",
            "message": f"Error en el proceso: {error_msg}",
            "details": {
                "cache_deleted": False,
                "database_deleted": False
            }
        }


@app.get("/health")
async def health_check():
    try:
        db_status = "up" if get_db_connection() else "down"
        status = {
            "status": "healthy",
            "database": db_status,
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "twilio": bool(os.getenv("TWILIO_ACCOUNT_SID")),
        }

        # Solo logear si hay algún problema
        if db_status == "down" or not status["openai"] or not status["twilio"]:
            logger.warning(f"Health check con problemas | Estado: {status}")

        return status
    except Exception as e:
        logger.error(f"Error en health check | Error: {str(e)}")
        raise


if __name__ == "__main__":
    logger.info(f"Servidor iniciado en puerto {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")