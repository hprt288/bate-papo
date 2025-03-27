import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import time
from datetime import datetime, timedelta
import pytz

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

def add_user(username, email, password):
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        hashed_password = generate_password_hash(password)
        c.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                 (username, email, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user_id(username):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def save_message(user_id, username, content):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    # Usar timezone Brasil/São Paulo
    tz = pytz.timezone('America/Sao_Paulo')
    timestamp = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
    c.execute('INSERT INTO messages (user_id, username, content, timestamp) VALUES (?, ?, ?, ?)',
              (user_id, username, content, timestamp))
    conn.commit()
    conn.close()

def get_messages(limit=50):
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  # Permite acessar colunas pelo nome
    c = conn.cursor()
    c.execute('''
        SELECT messages.*, users.username,
        strftime('%d/%m/%Y %H:%M', messages.timestamp) as formatted_time
        FROM messages 
        JOIN users ON messages.user_id = users.id 
        ORDER BY messages.timestamp DESC LIMIT ?
    ''', (limit,))
    messages = c.fetchall()
    conn.close()
    return reversed(messages)  # Retorna as mensagens em ordem cronológica

# Dicionário para armazenar tentativas de login
login_attempts = {}
MAX_ATTEMPTS = 3
LOCKOUT_TIME = 300  # 5 minutos em segundos

def check_login_attempts(username):
    if username in login_attempts:
        attempts, lockout_time = login_attempts[username]
        if attempts >= MAX_ATTEMPTS:
            if time.time() - lockout_time < LOCKOUT_TIME:
                remaining_time = int(LOCKOUT_TIME - (time.time() - lockout_time))
                return False, remaining_time
            else:
                login_attempts[username] = (0, 0)
    return True, 0

def record_failed_attempt(username):
    current_time = time.time()
    if username in login_attempts:
        attempts, _ = login_attempts[username]
        login_attempts[username] = (attempts + 1, current_time)
    else:
        login_attempts[username] = (1, current_time)

def reset_attempts(username):
    if username in login_attempts:
        login_attempts.pop(username)

def verify_user(username, password):
    can_attempt, wait_time = check_login_attempts(username)
    
    if not can_attempt:
        return False, wait_time
        
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT password FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    conn.close()
    
    if result and check_password_hash(result[0], password):
        reset_attempts(username)
        return True, 0
    else:
        record_failed_attempt(username)
        return False, 0
