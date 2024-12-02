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
            cursor_factory=RealDictCursor
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
            SELECT chat_history->-50: FROM conversations 
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
    """Elimina el historial de chat de un número específico"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM conversations 
            WHERE phone_number = %s
        """,
            (phone_number,),
        )

        conn.commit()
        # Retorna True si se eliminó algún registro
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting chat history: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()
