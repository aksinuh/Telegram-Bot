import sqlite3

# Verilənlər bazası ilə əlaqə qur
conn = sqlite3.connect("telegram_bot.db")
cursor = conn.cursor()

# İstifadəçi cədvəli
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
conn.close()
