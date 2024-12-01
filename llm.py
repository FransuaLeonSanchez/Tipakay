import logging
from openai import OpenAI
from dotenv import load_dotenv
import os
from datetime import datetime
from database import get_chat_history, update_chat_history

load_dotenv()


def get_completion(prompt: str, phone_number: str) -> str:
    try:
        # Cargar historial existente
        history = get_chat_history(phone_number)

        # Crear mensaje del usuario
        user_message = {
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().isoformat()
        }

        # Actualizar historial con mensaje del usuario
        history = update_chat_history(phone_number, user_message)

        # Preparar mensajes para OpenAI
        messages = [{"role": msg["role"], "content": msg["content"]}
                    for msg in history[-10:]]

        # Obtener respuesta de OpenAI
        logging.info(f"Consultando a OpenAI para el número: {phone_number}")
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        completion = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL"),
            messages=messages
        )

        response_content = completion.choices[0].message.content

        # Limpiar la respuesta
        cleaned_response = response_content.replace('<', '').replace('>', '')
        cleaned_response = cleaned_response.replace('**', '*')

        # Crear mensaje del asistente con la respuesta limpia
        assistant_message = {
            "role": "assistant",
            "content": cleaned_response,
            "timestamp": datetime.now().isoformat()
        }

        # Actualizar historial con respuesta del asistente
        update_chat_history(phone_number, assistant_message)

        return cleaned_response
    except Exception as e:
        return f"Error al procesar la solicitud: {str(e)}"