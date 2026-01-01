import sqlite3
import datetime

DB_NAME = "spy_app.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  query TEXT, 
                  date TEXT, 
                  result_count INTEGER)''')
    conn.commit()
    conn.close()

def add_history(query, result_count):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO history (query, date, result_count) VALUES (?, ?, ?)", 
              (query, date_str, result_count))
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Access columns by name
    c = conn.cursor()
    c.execute("SELECT * FROM history ORDER BY id DESC LIMIT 50")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]
