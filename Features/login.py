import streamlit as st
import pandas as pd
import hashlib
import sqlite3
from datetime import datetime
import os

# Page configuration
st.set_page_config(
    page_title="StudyBuddy - Login",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Create database directory if it doesn't exist
if not os.path.exists("./data"):
    os.makedirs("./data")

# Database setup
def init_db():
    conn = sqlite3.connect('./data/users.db')
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
    conn.close()

# Initialize the database
init_db()

# Password hashing function
def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# User authentication
def authenticate(username, password):
    conn = sqlite3.connect('./data/users.db')
    c = conn.cursor()
    
    hashed_pw = make_hash(password)
    c.execute('SELECT id, username FROM users WHERE username = ? AND password = ?', (username, hashed_pw))
    result = c.fetchone()
    conn.close()
    
    return result

# User registration
def add_user(username, password, email):
    conn = sqlite3.connect('./data/users.db')
    c = conn.cursor()
    
    hashed_pw = make_hash(password)
    try:
        c.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)', 
                 (username, hashed_pw, email))
        conn.commit()
        user_id = c.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None

# Log user session
def log_session(user_id):
    conn = sqlite3.connect('./data/users.db')
    c = conn.cursor()
    
    login_time = datetime.now()
    c.execute('INSERT INTO user_sessions (user_id, login_time) VALUES (?, ?)', 
             (user_id, login_time))
    
    conn.commit()
    session_id = c.lastrowid
    conn.close()
    
    return session_id

# App header
st.title("StudyBuddy")
st.subheader("Optimize your learning journey")

# Create tabs for login and signup
tab1, tab2 = st.tabs(["Login", "Sign Up"])

with tab1:
    # Login form
    st.header("Welcome back!")
    
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    
    # Right-aligned login button
    col1, col2 = st.columns([3, 1])
    with col2:
        login_button = st.button("Login")
    
    if login_button:
        if username and password:
            user = authenticate(username, password)
            if user:
                user_id, username = user
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.session_state['user_id'] = user_id
                
                # Log the session
                session_id = log_session(user_id)
                st.session_state['session_id'] = session_id
                
                st.success(f"Welcome back, {username}!")
                st.rerun()
            else:
                st.error("Invalid username or password")
        else:
            st.warning("Please enter both username and password")

with tab2:
    # Signup form
    st.header("Create an account")
    
    new_username = st.text_input("Username", key="signup_username")
    new_email = st.text_input("Email", key="signup_email")
    new_password = st.text_input("Password", type="password", key="signup_password")
    confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
    
    # Right-aligned signup button
    col1, col2 = st.columns([3, 1])
    with col2:
        signup_button = st.button("Sign Up")
    
    if signup_button:
        if new_username and new_email and new_password:
            if new_password == confirm_password:
                # Check if email is valid (simple check)
                if '@' in new_email and '.' in new_email:
                    user_id = add_user(new_username, new_password, new_email)
                    if user_id:
                        st.success("Account created successfully! You can now log in.")
                        st.query_params["tab"] = "login"
                    else:
                        st.error("Username or email already exists")
                else:
                    st.error("Please enter a valid email address")
            else:
                st.error("Passwords do not match")
        else:
            st.warning("Please fill in all fields")

# Check if user is logged in and redirect to dashboard
if st.session_state.get('logged_in', False):
    st.header(f"You are logged in as {st.session_state['username']}")
    st.write("Redirecting to dashboard...")
    
    # Here you would typically redirect to dashboard
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Go to Dashboard"):
            # This would be replaced with proper navigation in a multi-page app
            st.info("This would navigate to the dashboard in a complete app")

# Footer
st.markdown("---")
st.caption("© 2025 StudyBuddy | Your Personalized Learning Assistant")
