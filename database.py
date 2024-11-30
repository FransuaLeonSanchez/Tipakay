import psycopg2
from psycopg2.extras import RealDictCursor
import json
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()


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
        cursor.execute("""
            SELECT chat_history 
            FROM conversations 
            WHERE phone_number = %s
        """, (phone_number,))

        result = cursor.fetchone()

        if result and result['chat_history']:
            return json.loads(result['chat_history'])

        # Si no existe, crear un registro vacío
        cursor.execute("""
            INSERT INTO conversations (phone_number, chat_history) 
            VALUES (%s, %s)
        """, (phone_number, json.dumps([])))

        conn.commit()
        return []

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
        cursor.execute("""
            SELECT chat_history 
            FROM conversations 
            WHERE phone_number = %s
            FOR UPDATE
        """, (phone_number,))

        result = cursor.fetchone()

        if result and result['chat_history']:
            history = json.loads(result['chat_history'])
        else:
            history = []

        # Añadir el nuevo mensaje
        history.append(new_message)

        # Actualizar solo los últimos 50 mensajes
        history = history[-50:]

        # Actualizar el registro
        cursor.execute("""
            UPDATE conversations 
            SET chat_history = %s
            WHERE phone_number = %s
        """, (json.dumps(history), phone_number))

        if cursor.rowcount == 0:
            # Si no existe el registro, crearlo
            cursor.execute("""
                INSERT INTO conversations (phone_number, chat_history) 
                VALUES (%s, %s)
            """, (phone_number, json.dumps([new_message])))

        conn.commit()
        return history

    except Exception as e:
        print(f"Error updating chat history: {str(e)}")
        conn.rollback()
        return None
    finally:
        if conn:
            conn.close()