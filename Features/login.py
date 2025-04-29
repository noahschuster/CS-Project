import streamlit as st
import sqlite3
import hashlib
from datetime import datetime, timedelta
import os
import secrets


def generate_auth_token(user_id):
    token = secrets.token_hex(16)  # Generate a secure random token
    expiry = datetime.now() + timedelta(days=7)  # Token valid for 7 days
    
    with sqlite3.connect('./data/users.db') as conn:
        c = conn.cursor()
        
        # Create auth_tokens table if it doesn't exist
        c.execute('''
        CREATE TABLE IF NOT EXISTS auth_tokens (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            token TEXT UNIQUE,
            created_at TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Store the new token
        c.execute('''
        INSERT INTO auth_tokens (user_id, token, created_at, expires_at)
        VALUES (?, ?, ?, ?)
        ''', (user_id, token, datetime.now(), expiry))
        
        conn.commit()
        return token

def validate_auth_token(token):
    with sqlite3.connect('./data/users.db') as conn:
        c = conn.cursor()
        
        # Get user associated with token if it's not expired
        c.execute('''
        SELECT u.id, u.username FROM auth_tokens t
        JOIN users u ON t.user_id = u.id
        WHERE t.token = ? AND t.expires_at > ?
        ''', (token, datetime.now()))
        
        result = c.fetchone()
        return result  # Returns (user_id, username) or None


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
