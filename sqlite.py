import sqlite3

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