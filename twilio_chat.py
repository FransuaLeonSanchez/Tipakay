from twilio.rest import Client
import os
import logging

TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"

# Remover inicialización global del cliente
client = None


def get_twilio_client():
    global client
    if client is None:
        # Inicializar cliente solo cuando se necesite
        ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
        AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
        if not ACCOUNT_SID or not AUTH_TOKEN:
            raise ValueError("Twilio credentials not found in environment variables")
        client = Client(ACCOUNT_SID, AUTH_TOKEN)
    return client


async def process_incoming_message(form_data):
    try:
        incoming_msg = form_data.get("Body", "")
        from_number = form_data.get("From", "")

        if incoming_msg and from_number:
            return incoming_msg, from_number
        return None, None
    except Exception as e:
        logging.error(f"Error procesando mensaje: {str(e)}")
        return None, None


def send_message(to_number: str, message: str) -> None:
    try:
        # Obtener cliente cuando sea necesario
        twilio_client = get_twilio_client()
        # Desactivar los logs de HTTP de Twilio
        twilio_client.http_client.logger.setLevel(logging.WARNING)

        twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER, body=message, to=to_number
        )
    except Exception as e:
        logging.error(f"Error enviando mensaje: {str(e)}")
        raise e

def send_message_with_media(to_number: str, message: str, media_url: str) -> None:
    try:
        twilio_client = get_twilio_client()
        twilio_client.http_client.logger.setLevel(logging.WARNING)

        twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=message,
            media_url=[media_url],  # Lista de URLs de media
            to=to_number
        )
    except Exception as e:
        logging.error(f"Error enviando mensaje con media: {str(e)}")
        raise e
