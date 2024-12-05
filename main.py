from fastapi import FastAPI, Request, Response
import uvicorn
from dotenv import load_dotenv
import os
import logging
import time
import traceback

from database import delete_chat_history, get_db_connection, check_conversation_exists
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
        clean_number = phone_number.replace("whatsapp:", "").replace("+", "")
        logger.info(f"Verificando existencia de datos para número: {clean_number}")

        # Verificar existencia
        exists_in_db = check_conversation_exists(clean_number)
        from llm import get_cached_completion, clear_cache_for_number
        exists_in_cache = len(get_cached_completion.cache_info().currsize) > 0

        if not exists_in_db and not exists_in_cache:
            return {
                "status": "not_found",
                "message": "No hay datos que borrar para este número",
                "details": {
                    "cache_exists": False,
                    "database_exists": False
                }
            }

        # Proceder con el borrado
        deletion_status = {
            "cache": False,
            "database": False
        }

        # Intentar borrar caché
        if exists_in_cache:
            try:
                clear_cache_for_number()
                deletion_status["cache"] = True
                logger.info(f"Caché limpiado para el número: {clean_number}")
            except Exception as e:
                logger.error(f"Error limpiando caché: {str(e)}")

        # Intentar borrar base de datos
        if exists_in_db:
            deletion_status["database"] = delete_chat_history(clean_number)
            if deletion_status["database"]:
                logger.info(f"Base de datos limpiada para el número: {clean_number}")

        # Preparar respuesta
        details = []
        if deletion_status["cache"]:
            details.append("caché")
        if deletion_status["database"]:
            details.append("base de datos")

        if details:
            return {
                "status": "success",
                "message": f"Conversación eliminada de: {' y '.join(details)}",
                "details": deletion_status
            }
        else:
            return {
                "status": "error",
                "message": "No se pudo eliminar la conversación de ningún sistema",
                "details": deletion_status
            }

    except Exception as e:
        logger.error(f"Error en proceso de borrado - Número: {clean_number} - Error: {str(e)}")
        return {
            "status": "error",
            "message": f"Error en el proceso: {str(e)}",
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