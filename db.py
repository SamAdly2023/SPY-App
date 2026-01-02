import sqlite3
import datetime

DB_NAME = "spy_app.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id TEXT PRIMARY KEY, 
                  name TEXT, 
                  email TEXT, 
                  profile_pic TEXT,
                  credits INTEGER DEFAULT 10)''')
                  
    # History table
    c.execute('''CREATE TABLE IF NOT EXISTS history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  user_id TEXT,
                  query TEXT, 
                  date TEXT, 
                  result_count INTEGER,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
                  
    # Check if user_id exists in history (migration hack for existing db)
    try:
        c.execute("SELECT user_id FROM history LIMIT 1")
    except sqlite3.OperationalError:
        try:
            c.execute("ALTER TABLE history ADD COLUMN user_id TEXT")
        except:
            pass

    conn.commit()
    conn.close()

def create_or_update_user(user_info):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Check if user exists
    c.execute("SELECT * FROM users WHERE id = ?", (user_info['sub'],))
    user = c.fetchone()
    
    if user:
        # Update info
        c.execute("UPDATE users SET name = ?, email = ?, profile_pic = ? WHERE id = ?",
                  (user_info['name'], user_info['email'], user_info['picture'], user_info['sub']))
    else:
        # Create new user
        c.execute("INSERT INTO users (id, name, email, profile_pic, credits) VALUES (?, ?, ?, ?, ?)",
                  (user_info['sub'], user_info['name'], user_info['email'], user_info['picture'], 10)) # Default 10 credits
    
    conn.commit()
    conn.close()
    return user_info['sub']

def get_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def add_history(user_id, query, result_count):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO history (user_id, query, date, result_count) VALUES (?, ?, ?, ?)", 
              (user_id, query, date_str, result_count))
    conn.commit()
    conn.close()

def get_history(user_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM history WHERE user_id = ? ORDER BY id DESC LIMIT 50", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_credits(user_id, amount):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET credits = credits + ? WHERE id = ?", (amount, user_id))
    conn.commit()
    conn.close()
