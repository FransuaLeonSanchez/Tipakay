import logging

from psycopg2.extras import RealDictCursor
import json
import psycopg2
import os
from config import (
    SYSTEM_CONTEXT,
)  # Importar la variable SYSTEM_CONTEXT del archivo llm.py
from datetime import datetime


def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            cursor_factory=RealDictCursor,
        )
        return conn
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None


def get_chat_history(phone_number: str) -> list:
    """Obtiene el historial del chat desde la base de datos"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()

        # Verificar si existe el registro
        cursor.execute(
            """
            SELECT chat_history 
            FROM conversations 
            WHERE phone_number = %s
        """,
            (phone_number,),
        )

        result = cursor.fetchone()

        if result and result["chat_history"]:
            return json.loads(result["chat_history"])

        # Si no existe, crear un registro con el mensaje inicial del sistema
        initial_message = {
            "role": "system",
            "content": SYSTEM_CONTEXT,
            "timestamp": datetime.now().isoformat(),
        }

        cursor.execute(
            """
            INSERT INTO conversations (phone_number, chat_history) 
            VALUES (%s, %s)
        """,
            (phone_number, json.dumps([initial_message])),
        )

        conn.commit()
        return [initial_message]

    except Exception as e:
        print(f"Error getting chat history: {str(e)}")
        return []
    finally:
        if conn:
            conn.close()


def update_chat_history(phone_number: str, new_message: dict):
    """Actualiza el historial del chat añadiendo un nuevo mensaje"""
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()

        # Obtener el historial actual
        cursor.execute(
            """
            SELECT chat_history 
            FROM conversations 
            WHERE phone_number = %s
            FOR UPDATE
        """,
            (phone_number,),
        )

        result = cursor.fetchone()

        if result and result["chat_history"]:
            history = json.loads(result["chat_history"])
        else:
            history = []

        # Añadir el nuevo mensaje
        history.append(new_message)

        # Actualizar solo los últimos 50 mensajes
        history = history[-50:]

        # Actualizar el registro
        cursor.execute(
            """
            UPDATE conversations 
            SET chat_history = %s
            WHERE phone_number = %s
        """,
            (json.dumps(history), phone_number),
        )

        if cursor.rowcount == 0:
            # Si no existe el registro, crearlo
            cursor.execute(
                """
                INSERT INTO conversations (phone_number, chat_history) 
                VALUES (%s, %s)
            """,
                (phone_number, json.dumps([new_message])),
            )

        conn.commit()
        return history

    except Exception as e:
        print(f"Error updating chat history: {str(e)}")
        conn.rollback()
        return None
    finally:
        if conn:
            conn.close()


def delete_chat_history(phone_number: str) -> bool:
    """Elimina el historial de chat de la base de datos"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM conversations WHERE phone_number = %s",
            (phone_number,)
        )
        conn.commit()
        return True
    except Exception as e:
        logging.error(f"Error eliminando chat de base de datos: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


def check_conversation_exists(phone_number: str) -> bool:
    """Verifica si existe una conversación en la base de datos"""
    conn = get_db_connection()
    if not conn:
        logging.error("No se pudo conectar a la base de datos")
        return False

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT EXISTS(
                SELECT 1 
                FROM conversations 
                WHERE phone_number = %s
            ) as exists
            """,
            (phone_number,)
        )
        result = cursor.fetchone()
        exists = result['exists'] if result else False

        logging.info(
            f"Verificación de existencia en BD para número {phone_number}: {'existe' if exists else 'no existe'}")
        return exists

    except Exception as e:
        logging.error(f"Error verificando existencia de conversación: {str(e)}")
        return False
    finally:
        if conn:
            cursor.close()
            conn.close()