# main.py
import streamlit as st

# --- Set page config FIRST ---
st.set_page_config(
    page_title="StudyBuddy",
    page_icon="📚",
    layout="centered"
)

import os
import dashboard # Import the dashboard module
from datetime import datetime, timedelta
from streamlit_cookies_manager import EncryptedCookieManager

# Import database functions - ensure all needed ones are imported
from database_manager import (
    authenticate,
    add_user,
    log_session, 
    generate_auth_token, # For potential email links
    validate_auth_token, # For potential email links
    generate_session_token, # For persistent cookie sessions
    validate_session_token, # For persistent cookie sessions
    init_db # To ensure tables exist
)

# --- Configuration ---
# IMPORTANT: Set a strong secret password in environment variables or secrets management
# For demonstration, using a default, but CHANGE THIS IN PRODUCTION.
COOKIE_PASSWORD = os.environ.get("COOKIE_PASSWORD", "default_insecure_password_change_me_12345")
SESSION_COOKIE_NAME = "studybuddy_session_token"
SESSION_EXPIRY_DAYS = 30

# --- Initialization ---

# Initialize Database (optional here, could be run once separately)
# Consider adding error handling if DB connection fails
try:
    init_db()
except Exception as e:
    # Display error *after* page config
    st.error(f"Database connection failed: {e}. Please check configuration and ensure the database is running.")
    st.stop()

# Initialize Cookie Manager
# Use a prefix for better cookie organization if running multiple apps on the same domain
cookies = EncryptedCookieManager(
    prefix="sb/sess/",
    password=COOKIE_PASSWORD,
)
if not cookies.ready():
    # Wait for cookie manager to be ready before processing anything else
    # This st.stop() is fine here as page config is already done.
    st.stop()

# Initialize session state variables if they don't exist
def initialize_session_state():
    defaults = {
        'logged_in': False,
        'username': None,
        'user_id': None,
        'session_id': None, # ID from user_sessions table (optional usage)
        'login_attempted': False # Flag to prevent multiple login attempts per run
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()

# --- Core Authentication Logic ---
def attempt_login_from_cookie():
    """Checks for session cookie and attempts to log in user."""
    if not st.session_state.logged_in: # Only check if not already logged in
        session_token = cookies.get(SESSION_COOKIE_NAME)
        if session_token:
            print(f"Found session cookie: {session_token[:8]}...") # Debug
            user_info = validate_session_token(session_token)
            if user_info:
                user_id, username = user_info
                print(f"Session cookie validated for user: {username} (ID: {user_id})") # Debug
                st.session_state.logged_in = True
                st.session_state.user_id = user_id
                st.session_state.username = username
                # Optionally log a new session entry or find the last one?
                # For simplicity, we just restore the state.
                # st.session_state.session_id = log_session(user_id) # Creates new session log on every cookie validation?
                st.rerun() # Rerun to update the UI immediately
            else:
                print("Session cookie invalid or expired, deleting.") # Debug
                # Invalid or expired token found in cookie, remove it
                del cookies[SESSION_COOKIE_NAME]
                cookies.save() # Ensure deletion is saved immediately
                # No rerun needed here, proceed to other login methods / login page
        else:
            print("No session cookie found.") # Debug

def attempt_login_from_url_token():
    """Checks for a one-time auth token in URL and attempts login."""
    if not st.session_state.logged_in: # Only check if not logged in
        auth_token = st.query_params.get('auth_token', None)
        if auth_token:
            print(f"Found URL auth token: {auth_token[:8]}...") # Debug
            user_info = validate_auth_token(auth_token)
            if user_info:
                user_id, username = user_info
                print(f"URL auth token validated for user: {username} (ID: {user_id})") # Debug
                st.session_state.logged_in = True
                st.session_state.user_id = user_id
                st.session_state.username = username
                st.session_state.session_id = log_session(user_id) # Log session for URL token login
                
                # --- Set Persistent Session Cookie ---
                persistent_token = generate_session_token(user_id, days_valid=SESSION_EXPIRY_DAYS)
                if persistent_token:
                    # Use dictionary-style assignment
                    cookies[SESSION_COOKIE_NAME] = persistent_token
                    cookies.save() # Save immediately
                    print("Persistent session cookie set after URL token login.") # Debug
                else:
                    st.warning("Could not generate persistent session token after URL login.")
                
                # --- Clean up URL and Rerun ---
                try:
                    # Use st.query_params.clear() or selectively delete
                    st.query_params["auth_token"] = "" # Clear the specific param
                except Exception as e:
                    print(f"Error clearing query params: {e}")
                st.rerun()
            else:
                print("URL auth token invalid or expired.") # Debug
                # Invalid token, remove from URL and show error
                try:
                   st.query_params["auth_token"] = "" # Clear the specific param
                except Exception as e:
                    print(f"Error clearing query params: {e}")
                st.error("Invalid or expired authentication link.")
                # Proceed to show login page
        else:
             print("No URL auth token found.") # Debug

def show_login_page():
    """Displays the login and sign-up form."""
    st.title("StudyBuddy")
    st.subheader("Optimize your learning journey")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.header("Welcome back!")
        
        # Use unique keys to avoid conflicts if widgets are recreated
        username = st.text_input("Username", key="login_username_input")
        password = st.text_input("Password", type="password", key="login_password_input")
        
        login_button = st.button("Login", key="login_button")
            
        if login_button and not st.session_state.login_attempted:
            st.session_state.login_attempted = True # Prevent multiple clicks processing
            if username and password:
                user_info = authenticate(username, password)
                if user_info:
                    user_id, retrieved_username = user_info
                    print(f"Password login successful for user: {retrieved_username} (ID: {user_id})") # Debug
                    st.session_state.logged_in = True
                    st.session_state.username = retrieved_username
                    st.session_state.user_id = user_id
                    st.session_state.session_id = log_session(user_id) # Log session for password login
                    
                    # --- Set Persistent Session Cookie ---
                    session_token = generate_session_token(user_id, days_valid=SESSION_EXPIRY_DAYS)
                    if session_token:
                        # Use dictionary-style assignment
                        cookies[SESSION_COOKIE_NAME] = session_token
                        cookies.save() # Save immediately
                        print("Persistent session cookie set after password login.") # Debug
                    else:
                        st.warning("Could not generate persistent session token after login.")
                        
                    # Rerun to switch to the dashboard view
                    st.rerun()
                else:
                    st.error("Invalid username or password")
                    st.session_state.login_attempted = False # Allow retry on failure
            else:
                st.warning("Please enter both username and password")
                st.session_state.login_attempted = False # Allow retry if fields were empty
        elif not login_button:
             st.session_state.login_attempted = False # Reset flag if button not pressed
    
    with tab2:
        st.header("Create an account")
        
        new_username = st.text_input("Username", key="signup_username_input")
        new_email = st.text_input("Email", key="signup_email_input")
        new_password = st.text_input("Password", type="password", key="signup_password_input")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password_input")
        
        signup_button = st.button("Sign Up", key="signup_button")
            
        if signup_button:
            # Add validation logic here (same as before)
            if new_username and new_email and new_password:
                if new_password == confirm_password:
                    if '@' in new_email and '.' in new_email.split('@')[-1]:
                        user_id = add_user(new_username, new_password, new_email)
                        if user_id:
                            st.success("Account created successfully! Please proceed to the Login tab.")
                            # Clear signup fields is tricky with rerun, maybe handle differently
                        else:
                            st.error("Username or email already exists. Please try different ones.")
                    else:
                        st.error("Please enter a valid email address.")
                else:
                    st.error("Passwords do not match.")
            else:
                st.warning("Please fill in all required fields.")

# --- Main Application Flow ---
def main():
    # 1. Attempt login via session cookie (if not already logged in state)
    attempt_login_from_cookie()
    
    # If cookie login caused a rerun, st.session_state.logged_in might be True now
    
    # 2. Check if logged in via session state (could be from cookie or previous action)
    if st.session_state.logged_in:
        # Ensure URL token is cleared if present (e.g., user bookmarked link)
        if 'auth_token' in st.query_params:
             try:
                 st.query_params["auth_token"] = "" # Clear the specific param
             except Exception as e:
                 print(f"Error clearing query params: {e}")
        # Load and display the dashboard, passing the cookies object
        dashboard.main(cookies=cookies) 
        return # Stop execution here
        
    # 3. Attempt login via URL token (if not logged in yet)
    attempt_login_from_url_token()
    
    # If URL token login caused a rerun, the script restarts, and step 2 should catch it.
    
    # 4. If still not logged in, show the login/signup page
    if not st.session_state.logged_in:
        show_login_page()

if __name__ == "__main__":
    main()
