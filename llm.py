import logging
from openai import OpenAI
import os
from datetime import datetime
import twilio_chat
from database import get_chat_history, update_chat_history


class OpenAIClient:
    _instance = None  # Variable privada para almacenar la única instancia

    @classmethod
    def get_client(cls):
        if not cls._instance:
            cls._instance = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return cls._instance


def get_completion(prompt: str, phone_number: str) -> str:
    try:
        history = get_chat_history(phone_number)
        user_message = {
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().isoformat(),
        }
        history = update_chat_history(phone_number, user_message)
        messages = [
            {"role": msg["role"], "content": msg["content"]} for msg in history[-10:]
        ]

        logging.info(f"Consultando a OpenAI para el número: {phone_number}")
        try:
            client = OpenAIClient.get_client()
            completion = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL"),
                messages=messages,
                timeout=30,
            )

            response_content = completion.choices[0].message.content
            response_content = response_content.replace("<", "").replace(">", "")
            response_content = response_content.replace("**", "*")

            # Convertir el texto a minúsculas y verificar las palabras clave
            response_lower = response_content.lower()
            keywords = ["echowave", "smart", "audio", "hogar", "precios"]
            if all(keyword in response_lower for keyword in keywords):
                # Si todas las palabras clave están presentes, registrar la imagen
                media_message = {
                    "role": "media_assistant",
                    "content": "https://tipakay.obs.la-north-2.myhuaweicloud.com/echowave_ews.jpg",
                    "timestamp": datetime.now().isoformat(),
                }
                update_chat_history(phone_number, media_message)

                # Enviar imagen por Twilio
                twilio_chat.send_message_with_media(
                    to_number=phone_number,
                    message=response_content,
                    media_url="https://tipakay.obs.la-north-2.myhuaweicloud.com/echowave_ews.jpg"
                )
                return response_content

            if len(response_content) > 1590:
                response_content = response_content[:1587] + "..."
                logging.info(
                    f"Respuesta truncada a 1600 caracteres para el número: {phone_number}"
                )

            assistant_message = {
                "role": "assistant",
                "content": response_content,
                "timestamp": datetime.now().isoformat(),
            }
            update_chat_history(phone_number, assistant_message)

            # Enviar mensaje normal por Twilio si no se detectaron las palabras clave
            twilio_chat.send_message(to_number=phone_number, message=response_content)

            return response_content
        except Exception as e:
            error_msg = str(e)
            logging.error(f"Error general en get_completion: {error_msg}")
            return "Lo siento, hubo un error en el servicio. Por favor, inténtalo de nuevo en unos momentos."
