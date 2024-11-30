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


@app.get("/")
async def root():
    return {"status": "active"}


@app.post("/webhook")
async def receive_message(request: Request):
    try:
        form_data = await request.form()
        message, from_number = await twilio_chat.process_incoming_message(form_data)

        if message and from_number:
            # Limpiar el número de teléfono para usarlo como nombre de archivo
            clean_number = from_number.replace('whatsapp:', '').replace('+', '')

            # Obtener respuesta de OpenAI con historial
            ai_response = get_completion(message, clean_number)

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