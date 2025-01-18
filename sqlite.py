import sqlite3
import logging

def get_db_connection():
    conn = sqlite3.connect("telegram_bot.db")  # SQLite faylı
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            chat_id INTEGER UNIQUE,
            name TEXT
        )
        """)

        # Admin cədvəli
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY,
            chat_id INTEGER UNIQUE,
            name TEXT
        )
        """)

        # Mesajlar cədvəli
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (admin_id) REFERENCES admins (id)
        )
        """)

        conn.commit()


def add_user(chat_id, name):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (chat_id, name)
                VALUES (?, ?)
            """, (chat_id, name))
            conn.commit()
        except sqlite3.IntegrityError:
            pass 
        
def get_admin_ids():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT chat_id FROM admins")
        admin_ids = [row["chat_id"] for row in cursor.fetchall()]
    return admin_ids
    
def get_user_ids():
    with get_db_connection()as conn:
        cursor =conn.cursor()
        cursor.execute("SELECT chat_id FROM users")
        user_ids = [row["chat_id"] for row in cursor.fetchall()]
    return user_ids

def add_message(admin_id, message):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO messages(admin_id, message)
                VALUES (?, ?)          
            """, (admin_id, message))
            conn.commit()
        except sqlite3.IntegrityError:
            pass 
        
def delete_user(chat_id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Parametri tuple formatında göndərin
            cursor.execute("""
                DELETE FROM users WHERE chat_id = ?
            """, (chat_id,))
            conn.commit()
            print(f"İstifadəçi silindi: {chat_id}")
    except Exception as e:
        logging.error(f"İstifadəçi silinərkən xəta baş verdi: {e}")