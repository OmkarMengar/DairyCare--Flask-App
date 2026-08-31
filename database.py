import sqlite3

def init_db():
    conn = sqlite3.connect('dairycare.db')
    cursor = conn.cursor()

    # Users Table (शेतकऱ्यांचे अकाउंट्स)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT UNIQUE NOT NULL
        )
    ''')

    # Cows Table (user_phone कॉल्म जोडला आहे)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_phone TEXT NOT NULL,
            tag_no TEXT UNIQUE NOT NULL,
            name TEXT,
            breed TEXT,
            age INTEGER,
            pregnancy_status TEXT,
            ai_date TEXT,
            expected_calving_date TEXT,
            supplements TEXT,
            treatment_history TEXT,
            vaccination_history TEXT
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()