import sqlite3

conn = sqlite3.connect('bot_data.db', check_same_thread=False)
cursor = conn.cursor()

def setup_database():
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                      chat_id INTEGER PRIMARY KEY,
                      username TEXT UNIQUE,
                      password TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_files (
                      chat_id INTEGER,
                      collection_name TEXT,
                      filename TEXT,
                      PRIMARY KEY (chat_id, collection_name))''')
    conn.commit()
