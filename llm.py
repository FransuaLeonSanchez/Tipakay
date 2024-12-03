import logging
from openai import OpenAI
import os
from datetime import datetime
from database import get_chat_history, update_chat_history
import twilio_chat
from functools import lru_cache


class OpenAIClient:
    _instance = None  # Variable privada para almacenar la única instancia

    @classmethod
    def get_client(cls):
        if not cls._instance:
            cls._instance = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return cls._instance


def clean_phone_number(phone_number: str) -> str:
    """Elimina cualquier prefijo o caracteres especiales del número"""
    return phone_number.replace("whatsapp:", "").replace("+", "")


def format_whatsapp_number(phone_number: str) -> str:
    """Formatea el número para WhatsApp"""
    if not phone_number.startswith('whatsapp:'):
        return f'whatsapp:+{phone_number}'
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


def messages_to_tuple(messages):
    """Convierte la lista de mensajes a una tupla que puede ser cacheada"""
    return tuple((msg["role"], msg["content"]) for msg in messages)


@lru_cache(maxsize=100)
def get_cached_completion(messages_tuple):
    """Obtiene una respuesta cacheada de OpenAI"""
    client = OpenAIClient.get_client()
    completion = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL"),
        messages=[{"role": role, "content": content} for role, content in messages_tuple],
        timeout=30,
    )
    return completion.choices[0].message.content


def get_completion(prompt: str, phone_number: str) -> str:
    try:
        # Limpiar número para la base de datos
        clean_number = clean_phone_number(phone_number)
        whatsapp_number = format_whatsapp_number(clean_number)

        # Cargar historial existente solo para el contexto de OpenAI
        history = get_chat_history(clean_number)
        messages = [
            {"role": msg["role"], "content": msg["content"]} for msg in history[-10:]
        ]

        # Convertir mensajes a formato cacheable
        messages_tuple = messages_to_tuple(messages)

        # Obtener respuesta de OpenAI
        logging.info(f"Consultando a OpenAI para el número: {clean_number}")
        try:
            # Intentar obtener respuesta del caché
            try:
                response_content = get_cached_completion(messages_tuple)
                logging.info(f"Respuesta obtenida del caché para el número: {clean_number}")
            except Exception as cache_error:
                logging.error(f"Error al obtener del caché: {cache_error}")
                # Si falla el caché, obtener directamente de OpenAI
                client = OpenAIClient.get_client()
                completion = client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL"),
                    messages=messages,
                    timeout=30,
                )
                response_content = completion.choices[0].message.content

            # Procesar respuesta
            response_content = response_content.replace("<", "").replace(">", "")
            response_content = response_content.replace("**", "*")

            if len(response_content) > 1590:
                response_content = response_content[:1587] + "..."
                logging.info(f"Respuesta truncada a 1600 caracteres para el número: {clean_number}")

            # Verificar keywords y enviar respuesta primero
            response_lower = response_content.lower()
            keywords = ["echowave", "smart", "audio", "hogar", "precios"]

            # Primero enviar respuesta vía Twilio
            if all(keyword in response_lower for keyword in keywords):
                send_twilio_response(
                    formatted_number=whatsapp_number,
                    response_content=response_content,
                    media_url="https://tipakay.obs.la-north-2.myhuaweicloud.com/echowave_ews.jpg"
                )
            else:
                send_twilio_response(
                    formatted_number=whatsapp_number,
                    response_content=response_content
                )

            # Luego actualizar la base de datos
            user_message = {
                "role": "user",
                "content": prompt,
                "timestamp": datetime.now().isoformat(),
            }
            update_chat_history(clean_number, user_message)

            assistant_message = {
                "role": "assistant",
                "content": response_content,
                "timestamp": datetime.now().isoformat(),
            }
            update_chat_history(clean_number, assistant_message)

            if all(keyword in response_lower for keyword in keywords):
                media_message = {
                    "role": "media_assistant",
                    "content": "https://tipakay.obs.la-north-2.myhuaweicloud.com/echowave_ews.jpg",
                    "timestamp": datetime.now().isoformat(),
                }
                update_chat_history(clean_number, media_message)

            # Imprimir info del caché
            info = get_cached_completion.cache_info()
            logging.info(f"Cache hits: {info.hits}, misses: {info.misses}")

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