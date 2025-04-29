import streamlit as st
from login import authenticate, add_user, log_session, generate_auth_token, validate_auth_token
from datetime import datetime, timedelta

# Set page configuration at the very beginning of your script
st.set_page_config(
    page_title="StudyBuddy",
    page_icon="📚",
    layout="centered"
)

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

def main():
    # Check URL parameters for auth token
    auth_token = st.query_params.get('auth_token', None)
    
    # If we have a token and not logged in yet, try to validate it
    if auth_token and not st.session_state.get('logged_in', False):
        user = validate_auth_token(auth_token)
        if user:
            user_id, username = user
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.session_state['user_id'] = user_id
            
            # Log this session
            session_id = log_session(user_id)
            st.session_state['session_id'] = session_id
            
            # Keep the token in the URL
            st.query_params['auth_token'] = auth_token
    
    if not st.session_state.get('logged_in', False):
        show_login_page()
    else:
        import dashboard
        dashboard.main()

def show_login_page():
    st.title("StudyBuddy")
    st.subheader("Optimize your learning journey")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.header("Welcome back!")
        
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            login_button = st.button("Login")
            
        if login_button:
            if username and password:
                user = authenticate(username, password)
                if user:
                    user_id, username = user
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.session_state['user_id'] = user_id
                    
                    session_id = log_session(user_id)
                    st.session_state['session_id'] = session_id
                    
                    # Generate and set auth token in URL
                    auth_token = generate_auth_token(user_id)
                    st.query_params['auth_token'] = auth_token
                    
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.warning("Please enter both username and password")
    
    with tab2:
        st.header("Create an account")
        
        new_username = st.text_input("Username", key="signup_username")
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            signup_button = st.button("Sign Up")
            
        if signup_button:
            if new_username and new_email and new_password:
                if new_password == confirm_password:
                    if '@' in new_email and '.' in new_email:
                        user_id = add_user(new_username, new_password, new_email)
                        if user_id:
                            st.success("Account created successfully! You can now log in.")
                        else:
                            st.error("Username or email already exists")
                    else:
                        st.error("Please enter a valid email address")
                else:
                    st.error("Passwords do not match")
            else:
                st.warning("Please fill in all fields")

if __name__ == "__main__":
    main()
