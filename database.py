import sqlite3

def init_db():
    conn = sqlite3.connect('dairycare.db', timeout=20)
    cursor = conn.cursor()
    
    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT UNIQUE,
            telegram_chat_id TEXT
        )
    ''')
    
    # Cows Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_phone TEXT,
            tag_no TEXT UNIQUE,
            name TEXT,
            breed TEXT,
            age TEXT,
            pregnancy_status TEXT,
            ai_date TEXT,
            expected_calving_date TEXT,
            supplements TEXT,
            treatment_history TEXT,
            vaccination_history TEXT,
            is_calved INTEGER DEFAULT 0
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
