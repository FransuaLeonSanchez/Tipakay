import logging
from openai import OpenAI
import os
from datetime import datetime
from database import get_chat_history, update_chat_history
import twilio_chat


class OpenAIClient:
    _instance = None  # Variable privada para almacenar la única instancia

    @classmethod
    def get_client(cls):
        if not cls._instance:
            cls._instance = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return cls._instance


def check_and_format_number(phone_number: str) -> str:
    """Asegura que el número tenga el prefijo whatsapp: correcto"""
    if not phone_number.startswith("whatsapp:"):
        return f"whatsapp:{phone_number}"
    return phone_number

def send_twilio_response(formatted_number: str, response_content: str, media_url: str = None):
    """Función auxiliar para enviar mensajes vía Twilio una sola vez"""
    if media_url:
        twilio_chat.send_message_with_media(
            to_number=formatted_number,
            message=response_content,
            media_url=media_url
        )
    else:
        twilio_chat.send_message(
            to_number=formatted_number,
            message=response_content
        )

def get_completion(prompt: str, phone_number: str) -> str:
    try:
        # Cargar historial existente
        history = get_chat_history(phone_number)

        # Crear mensaje del usuario
        user_message = {
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().isoformat(),
        }

        # Actualizar historial con mensaje del usuario
        history = update_chat_history(phone_number, user_message)

        # Preparar mensajes para OpenAI
        messages = [
            {"role": msg["role"], "content": msg["content"]} for msg in history[-10:]
        ]

        # Obtener respuesta de OpenAI
        logging.info(f"Consultando a OpenAI para el número: {phone_number}")
        try:
            client = OpenAIClient.get_client()
            completion = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL"),
                messages=messages,
                timeout=30,
            )

            # Obtener y limpiar la respuesta inmediatamente
            response_content = completion.choices[0].message.content
            response_content = response_content.replace("<", "").replace(">", "")
            response_content = response_content.replace("**", "*")

            # Convertir el texto a minúsculas y verificar las palabras clave
            response_lower = response_content.lower()
            keywords = ["echowave", "smart", "audio", "hogar", "precios"]

            # Formatear número para cualquier caso
            formatted_number = check_and_format_number(phone_number)

            # Enviar mensaje según condición
            if all(keyword in response_lower for keyword in keywords):
                # Si todas las palabras clave están presentes, registrar la imagen
                media_message = {
                    "role": "media_assistant",
                    "content": "https://tipakay.obs.la-north-2.myhuaweicloud.com/echowave_ews.jpg",
                    "timestamp": datetime.now().isoformat(),
                }
                update_chat_history(phone_number, media_message)

                send_twilio_response(
                    formatted_number=formatted_number,
                    response_content=response_content,
                    media_url="https://tipakay.obs.la-north-2.myhuaweicloud.com/echowave_ews.jpg"
                )
            else:
                send_twilio_response(
                    formatted_number=formatted_number,
                    response_content=response_content
                )

            return response_content

        except Exception as openai_error:
            error_detail = str(openai_error)
            logging.error(f"Error en la llamada a OpenAI: {error_detail}")
            # Verificar el tipo de error
            if "api_key" in error_detail.lower():
                return "Error de configuración: Problema con la API key de OpenAI"
            elif "timeout" in error_detail.lower():
                return "Lo siento, el servicio está tardando mucho en responder. Por favor, inténtalo de nuevo."
            elif "connection" in error_detail.lower():
                return "Hay un problema de conexión con el servicio. Por favor, inténtalo de nuevo en unos momentos."
            else:
                return f"Lo siento, hubo un problema con el servicio. Error: {error_detail}"

    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error general en get_completion: {error_msg}")
        return "Lo siento, hubo un error en el servicio. Por favor, inténtalo de nuevo en unos momentos."
