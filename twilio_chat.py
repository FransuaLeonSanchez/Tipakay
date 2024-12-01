from twilio.rest import Client
from dotenv import load_dotenv
import os
import logging

load_dotenv()

ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = 'whatsapp:+14155238886'

client = Client(ACCOUNT_SID, AUTH_TOKEN)


async def process_incoming_message(form_data):
    try:
        incoming_msg = form_data.get('Body', '')
        from_number = form_data.get('From', '')

        if incoming_msg and from_number:
            return incoming_msg, from_number
        return None, None
    except Exception as e:
        logging.error(f"Error procesando mensaje: {str(e)}")
        return None, None


def send_message(to_number: str, message: str) -> None:
    try:
        # Desactivar los logs de HTTP de Twilio
        client.http_client.logger.setLevel(logging.WARNING)

        client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=message,
            to=to_number
        )
    except Exception as e:
        logging.error(f"Error enviando mensaje: {str(e)}")
        raise e