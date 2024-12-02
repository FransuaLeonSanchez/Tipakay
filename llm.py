import logging
from openai import OpenAI
import os
from datetime import datetime
from database import get_chat_history, update_chat_history

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
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            completion = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL"),
                messages=messages,
                timeout=30,  # Añadir timeout
            )

            # Obtener y limpiar la respuesta inmediatamente
            response_content = completion.choices[0].message.content
            response_content = response_content.replace("<", "").replace(">", "")
            response_content = response_content.replace("**", "*")

            # Limitar la respuesta a 1600 caracteres si es más larga
            if len(response_content) > 1590:
                response_content = response_content[:1587] + "..."
                logging.info(
                    f"Respuesta truncada a 1600 caracteres para el número: {phone_number}"
                )

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

        # Crear mensaje del asistente con la respuesta ya limpia y limitada
        assistant_message = {
            "role": "assistant",
            "content": response_content,
            "timestamp": datetime.now().isoformat(),
        }

        # Actualizar historial con respuesta del asistente
        update_chat_history(phone_number, assistant_message)

        return response_content
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error general en get_completion: {error_msg}")
        return "Lo siento, hubo un error en el servicio. Por favor, inténtalo de nuevo en unos momentos."
