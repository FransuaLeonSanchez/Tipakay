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
        clean_number = phone_number.replace("whatsapp:", "").replace("+", "")
        success = delete_chat_history(clean_number)

        if success:
            logger.info(f"Conversación eliminada | Número: {clean_number}")
            return {
                "status": "success",
                "message": f"Conversación eliminada para el número {phone_number}",
            }
        else:
            logger.warning(f"No se encontró conversación | Número: {clean_number}")
            return {
                "status": "not_found",
                "message": f"No se encontró conversación para el número {phone_number}",
            }

    except Exception as e:
        logger.error(
            f"Error al eliminar conversación | "
            f"Número: {clean_number if 'clean_number' in locals() else phone_number} | "
            f"Error: {str(e)}"
        )
        return {"status": "error", "message": str(e)}


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