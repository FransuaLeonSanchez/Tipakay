from fastapi import FastAPI, Request, Response
import uvicorn
from dotenv import load_dotenv
import os
import logging
from llm import get_completion
import twilio_chat

load_dotenv()
app = FastAPI()
PORT = int(os.getenv('PORT', '3000'))

# Configurar el formato del logging para que sea más limpio
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Establecer nivel WARNING para los logs de uvicorn y otros módulos
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

@app.get("/")
async def root():
    return {"status": "active"}


@app.post("/webhook")
async def receive_message(request: Request):
    try:
        form_data = await request.form()
        message, from_number = await twilio_chat.process_incoming_message(form_data)

        if message and from_number:
            # Log del mensaje recibido
            logging.info(f"Mensaje recibido - Número: {from_number} | Mensaje: {message}")

            # Limpiar el número de teléfono para usarlo como nombre de archivo
            clean_number = from_number.replace('whatsapp:', '').replace('+', '')

            # Obtener respuesta de OpenAI con historial
            ai_response = get_completion(message, clean_number)

            # Log de la respuesta del bot
            logging.info(f"Respuesta enviada - Número: {from_number} | Respuesta: {ai_response}")

            # Enviar respuesta vía Twilio
            twilio_chat.send_message(from_number, ai_response)

        return Response(
            content="<?xml version='1.0' encoding='UTF-8'?><Response></Response>",
            media_type="application/xml"
        )
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return Response(
            content="<?xml version='1.0' encoding='UTF-8'?><Response></Response>",
            media_type="application/xml"
        )


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info"
    )