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
                  credits INTEGER DEFAULT 10,
                  role TEXT DEFAULT 'user')''')
                  
    # History table
    c.execute('''CREATE TABLE IF NOT EXISTS history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  user_id TEXT,
                  query TEXT, 
                  date TEXT, 
                  result_count INTEGER,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
                  
    # Migrations
    try:
        c.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
    except:
        pass

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
    
    # Determine role and credits
    role = 'user'
    credits = 10
    if user_info['email'] == 'samadly728@gmail.com':
        role = 'admin'
        credits = 999999
    
    if user:
        # Update info
        # If it's the admin, ensure they keep admin role and high credits
        if user_info['email'] == 'samadly728@gmail.com':
             c.execute("UPDATE users SET name = ?, email = ?, profile_pic = ?, role = ?, credits = ? WHERE id = ?",
                  (user_info['name'], user_info['email'], user_info['picture'], role, credits, user_info['sub']))
        else:
             c.execute("UPDATE users SET name = ?, email = ?, profile_pic = ? WHERE id = ?",
                  (user_info['name'], user_info['email'], user_info['picture'], user_info['sub']))
    else:
        # Create new user
        c.execute("INSERT INTO users (id, name, email, profile_pic, credits, role) VALUES (?, ?, ?, ?, ?, ?)",
                  (user_info['sub'], user_info['name'], user_info['email'], user_info['picture'], credits, role))
    
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

def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_all_history():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''
        SELECT history.*, users.name as user_name, users.email as user_email 
        FROM history 
        JOIN users ON history.user_id = users.id 
        ORDER BY history.id DESC
    ''')
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]
