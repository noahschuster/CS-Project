import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import os

if not os.path.exists("./data"):
    os.makedirs("./data")

def init_db():
    with sqlite3.connect('./data/users.db') as conn:
        c = conn.cursor()
        
        c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE,
            learning_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        c.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            login_time TIMESTAMP,
            logout_time TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        conn.commit()

init_db()

def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def authenticate(username, password):
    with sqlite3.connect('./data/users.db') as conn:
        c = conn.cursor()
        hashed_pw = make_hash(password)
        c.execute('SELECT id, username FROM users WHERE username = ? AND password = ?', (username, hashed_pw))
        result = c.fetchone()
        return result

def add_user(username, password, email):
    with sqlite3.connect('./data/users.db') as conn:
        c = conn.cursor()
        hashed_pw = make_hash(password)
        try:
            c.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)', (username, hashed_pw, email))
            conn.commit()
            user_id = c.lastrowid
            return user_id
        except sqlite3.IntegrityError:
            return None

def log_session(user_id):
    with sqlite3.connect('./data/users.db') as conn:
        c = conn.cursor()
        login_time = datetime.now()
        c.execute('INSERT INTO user_sessions (user_id, login_time) VALUES (?, ?)', (user_id, login_time))
        conn.commit()
        session_id = c.lastrowid
        return session_id
