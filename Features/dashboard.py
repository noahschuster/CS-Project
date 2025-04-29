import streamlit as st
from datetime import datetime
import api_connection
from utils import get_user_sessions, get_user_learning_type
import sqlite3

def check_login():
    if not st.session_state.get('logged_in', False):
        st.warning("Please log in to access the dashboard")
        st.stop()
    return st.session_state.get('user_id'), st.session_state.get('username')

def main():
    user_id, username = check_login()
    
    with st.sidebar:
        st.title("StudyBuddy")
        st.write(f"Welcome, {username}!")
        
        page = st.radio(
            "Navigation",
            ["Dashboard", "Courses", "Learning Type", "Study Sessions", "Learning Tips"]
        )
        
        if st.button("Logout"):
            logout_user()
            st.session_state['logged_in'] = False
            st.rerun()
    
    if page == "Dashboard":
        display_dashboard(user_id, username)
    elif page == "Courses":
        from courses import display_courses
        display_courses(user_id)
    elif page == "Learning Type":
        from learning_type import display_learning_type
        display_learning_type(user_id)
    elif page == "Study Sessions":
        from study_sessions import display_study_sessions
        display_study_sessions(user_id)
    elif page == "Learning Tips":
        from learning_tips import display_learning_tips
        display_learning_tips(user_id)

def display_dashboard(user_id, username):
    st.title("StudyBuddy Dashboard")
    st.subheader("Your Learning Journey")
    
    learning_type = get_user_learning_type(user_id)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Quick Stats")
        
        try:
            user_courses = api_connection.get_user_courses(user_id)
            course_count = len(user_courses)
        except:
            course_count = 0
        
        sessions_df = get_user_sessions(user_id)
        session_count = len(sessions_df)
        total_hours = sessions_df["duration_hours"].sum() if not sessions_df.empty else 0
        
        st.metric("Courses Enrolled", course_count)
        st.metric("Study Sessions", session_count)
        st.metric("Total Study Hours", f"{total_hours:.1f}")
        
        st.subheader("Your Learning Profile")
        if learning_type:
            st.info(f"Your identified learning type: {learning_type}")
            st.write("Based on your learning type, we've customized your experience.")
        else:
            st.warning("You haven't set your learning type yet. Go to the Learning Type section to take the quiz.")
    
    with col2:
        st.subheader("Recent Activity")
        
        if not sessions_df.empty:
            recent_sessions = sessions_df.head(5)
            for _, session in recent_sessions.iterrows():
                login_time = session['login_time']
                duration = session['duration_hours']
                st.write(f"📚 Study session on {login_time} - Duration: {duration:.1f} hours")
        else:
            st.write("No recent activity recorded.")
        
        st.subheader("Upcoming Deadlines")
        st.info("This feature is coming soon. You'll be able to track your course deadlines here.")

def logout_user():
    with sqlite3.connect('./data/users.db') as conn:
        c = conn.cursor()
        logout_time = datetime.now()
        session_id = st.session_state.get('session_id')
        
        if session_id:
            c.execute('UPDATE user_sessions SET logout_time = ? WHERE id = ?', (logout_time, session_id))
            conn.commit()
    
    for key in list(st.session_state.keys()):
        del st.session_state[key]
