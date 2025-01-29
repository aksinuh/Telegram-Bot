import sqlite3
import logging
import datetime

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
        
        
        # Kripto valyutalar cədvəli
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cryptocurrencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
        """)
        
        # İstifadəçilərin baxış qeydləri
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_crypto_views (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            crypto TEXT,
            crypto_price REAL,
            viewed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)
        
        # İstifadəçi izləmə cədvəli
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            crypto_id INTEGER,
            target_price REAL,
            direction TEXT CHECK(direction IN ('yuxarı', 'aşağı')),
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (crypto_id) REFERENCES cryptocurrencies (id)
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
        
def get_all_cryptos():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM cryptocurrencies")
        return [row["name"] for row in cursor.fetchall()]
    
def log_crypto_view(user_id, crypto, crypto_price):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO user_crypto_views(user_id,crypto, crypto_price)
        VALUES (?, ?, ?)              
        """, (user_id, crypto, crypto_price))
        conn.commit()
        
def add_to_watchlist(user_id, crypto_id, target_price, direction):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO user_watchlist(user_id, crypto_id, target_price, direction)
        VALUES (?, ?, ?, ?)               
        """, (user_id, crypto_id, target_price, direction))
        conn.commit()
        
def get_user_watchlist(user_id):
    query = """
    SELECT 
        cryptocurrencies.name AS crypto_name,
        user_watchlist.target_price,
        user_watchlist.direction
    FROM user_watchlist
    JOIN cryptocurrencies ON user_watchlist.crypto_id = cryptocurrencies.id
    WHERE user_watchlist.user_id = ?
    """

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (user_id,))
        result = cursor.fetchall()

    return result

def save_crypto_view(user_id, crypto, crypto_price):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO user_crypto_views (user_id, crypto, crypto_price, viewed_at)
        VALUES (?, ?, ?, ?)
        """, (user_id, crypto, crypto_price, datetime.datetime.now()))
        conn.commit()
        
def get_user_watchlist(user_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT id, crypto_id, target_price, direction
        FROM user_watchlist
        WHERE user_id = ?
        """, (user_id,))
        return cursor.fetchall()
        
def delete_watchlist_entry(entry_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_watchlist WHERE id = ?", (entry_id,))
        conn.commit()

def get_crypto_symbol_by_id(crypto_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM cryptocurrencies WHERE id = ?", (crypto_id,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            print(f"Xəta: Kriptovalyuta ID {crypto_id} tapılmadı.")
            return None
        
def delete_user_watchlist(user_id, crypto_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_watchlist WHERE user_id = ? AND crypto_id = ?", (user_id, crypto_id))
        conn.commit()

def get_user_watchlist_2(user_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT crypto_id FROM user_watchlist WHERE user_id = ?", (user_id,))
        watchlist = cursor.fetchall()
        return [crypto[0] for crypto in watchlist]
    
def delete_all_user_watchlist(user_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_watchlist WHERE user_id = ?", (user_id,))
        conn.commit()