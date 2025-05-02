# dashboard.py
import os
import streamlit as st
from datetime import datetime, timedelta
import streamlit.components.v1 as components
from streamlit_cookies_manager import EncryptedCookieManager
from functools import lru_cache
import pandas as pd
from procrastination_risk import display_procrastination_assessment, display_dashboard_warning

# Import specific functions to avoid unnecessarily importing entire modules
from api_connection import get_user_courses
from utils import get_user_sessions, get_user_learning_type
from database_manager import delete_session_token, get_calendar_events

# Constants
SESSION_COOKIE_NAME = "studybuddy_session_token"

# Cache functions for performance - updating to use st.cache_data instead of lru_cache
@st.cache_data(ttl=600, max_entries=32)
def get_cached_user_learning_type(user_id):
    """Cached version of get_user_learning_type to reduce DB calls"""
    return get_user_learning_type(user_id)

@st.cache_data(ttl=600, max_entries=32)
def get_cached_user_courses(user_id):
    """Cached version of get_user_courses to reduce DB calls"""
    return get_user_courses(user_id)

@st.cache_data(ttl=300, max_entries=32)
def get_cached_calendar_events(user_id):
    """Cached version of get_calendar_events to reduce DB calls"""
    return get_calendar_events(user_id)

def check_login():
    """Verifies user login status"""
    if not st.session_state.get("logged_in", False):
        st.warning("Please log in to access the dashboard.")
        st.stop()
    return st.session_state.get("user_id"), st.session_state.get("username")

def logout_user(cookies):
    """Handles user logout process"""
    # Get session token from cookie
    session_token = cookies.get(SESSION_COOKIE_NAME)
    
    # Delete token from database if exists
    if session_token:
        delete_session_token(session_token)
    
    # Delete the cookie from browser
    if session_token:
        try:
            del cookies[SESSION_COOKIE_NAME]
            cookies.save()
        except KeyError:
            pass  # Cookie may already be removed

    # Clear Streamlit session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    # Reset minimal session state
    st.session_state.update({
        "logged_in": False,
        "username": None,
        "user_id": None,
        "login_attempted": False,
        "learning_type_completed": False
    })
    
    # Clear URL parameters
    try:
        st.query_params.clear()
    except Exception:
        pass
    
    # Force page reload
    components.html(
        """
        <script>window.parent.location.reload();</script>
        <p>Logging out...</p>
        """,
        height=50
    )
    
    st.stop()

def display_upcoming_deadlines(user_id):
    """Display upcoming deadlines with efficient data handling"""
    # Get today's date
    today = datetime.now().date()
    
    # Get events from database (cached)
    events = get_cached_calendar_events(user_id)
    
    # Define deadline types
    deadline_types = ["Assignment Due", "Exam", "Project Due"]
    
    # Filter and sort deadlines in one pass
    upcoming_deadlines = []
    
    for event in events:
        # Check if it's a deadline
        if not (event.get('is_deadline', False) or event.get('type') in deadline_types):
            continue
            
        # Parse date once
        try:
            deadline_date = datetime.strptime(event['date'], "%Y-%m-%d").date()
            
            # Check date range
            if today <= deadline_date <= today + timedelta(days=14):
                # Add days_left calculation here to avoid recomputing later
                event['days_left'] = (deadline_date - today).days
                upcoming_deadlines.append(event)
        except (ValueError, TypeError):
            continue  # Skip invalid dates
    
    # Sort by date
    upcoming_deadlines.sort(key=lambda e: e.get('days_left', 14))
    
    # Display deadlines
    if upcoming_deadlines:
        for deadline in upcoming_deadlines:
            days_left = deadline['days_left']
            
            # Format days left text
            if days_left == 0:
                days_text = "⚠️ TODAY"
            elif days_left == 1:
                days_text = "⚠️ TOMORROW"
            else:
                days_text = f"In {days_left} days"
            
            st.markdown(
                f"""<div style='background-color: {deadline['color']}; padding: 8px;
                 border-radius: 5px; margin-bottom: 5px;'>
                <strong>{deadline['title']}</strong> ({deadline['type']})<br>
                Due: {deadline['date']} at {deadline['time']} - <strong>{days_text}</strong>
                </div>""",
                unsafe_allow_html=True
            )
    else:
        st.info("No upcoming deadlines in the next 14 days! 🎉")

def display_dashboard(user_id, username):
    """Main dashboard display with optimized data fetching"""
    st.title("StudyBuddy Dashboard")
    st.subheader("Your Learning Journey")

    # Zeige Prokrastinations-Warnung an (wenn Risiko hoch ist)
    display_dashboard_warning(user_id)

    # Get user data with caching
    learning_type = get_cached_user_learning_type(user_id)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Quick Stats")
        
        # Fetch course data
        try:
            user_courses = get_cached_user_courses(user_id)
            course_count = len(user_courses) if user_courses else 0
        except Exception as e:
            st.error(f"Error fetching courses: {str(e)}")
            course_count = "Error"
        
        # Fetch session data once
        try:
            sessions_df = get_user_sessions(user_id)
            session_count = len(sessions_df)
            
            # Calculate total hours efficiently
            if not sessions_df.empty and 'duration_hours' in sessions_df.columns:
                total_hours = sessions_df["duration_hours"].sum()
            else:
                total_hours = 0
        except Exception as e:
            st.error(f"Error fetching sessions: {str(e)}")
            session_count = "Error"
            total_hours = "Error"
            sessions_df = pd.DataFrame()  # Empty dataframe for safe access later
        
        # Display metrics
        st.metric("Courses Enrolled", course_count)
        st.metric("Study Sessions", session_count)
        st.metric("Total Study Hours", f"{total_hours:.1f}" if isinstance(total_hours, (int, float)) else total_hours)
        
        # Display learning profile
        st.subheader("Your Learning Profile")
        if learning_type:
            st.info(f"Your identified learning type: {learning_type}")
            st.write("Based on your learning type, we've customized your experience.")
        else:
            st.warning("You haven't set your learning type yet. Go to the Learning Type section to take the quiz.")
    
    with col2:
        st.subheader("Recent Activity")
        
        # Process session data efficiently
        if isinstance(session_count, int) and session_count > 0 and not sessions_df.empty:
            # Get only the needed columns and rows
            recent_sessions = sessions_df.head(5)
            
            for _, session in recent_sessions.iterrows():
                login_time = session.get("login_time", "N/A")
                login_time_str = login_time.strftime("%Y-%m-%d %H:%M") if isinstance(login_time, datetime) else str(login_time)
                duration = session.get("duration_hours", 0)
                st.write(f"📚 Study session on {login_time_str} - Duration: {duration:.1f} hours")
        elif session_count == 0:
            st.write("No recent activity recorded.")
        
        st.subheader("Upcoming Deadlines")
        display_upcoming_deadlines(user_id)

def main(cookies):
    """Entry point for dashboard"""
    # Only check cookie readiness once
    if not cookies.ready():
        st.stop()
    
    user_id, username = check_login()
    
    # Check if learning type is completed - redirect if not
    if not st.session_state.get("learning_type_completed", False):
        # Import only when needed
        from learning_type import display_learning_type
        display_learning_type(user_id)
        return
    
    # Create sidebar
    with st.sidebar:
        st.title("StudyBuddy")
        st.write(f"Welcome, {username}!")
        
        # Navigation options
        pages = {
            "Dashboard": display_dashboard,
            "Calendar": "calendar_study.display_calendar",
            "Courses": "courses.display_courses",
            "Learning Type": "learning_type.display_learning_type",
            "Study Sessions": "study_sessions.display_study_sessions",
            "Learning Tips": "learning_tipps.display_learning_tips",
            "Learning Suggestions": "learning_suggestions.display_learning_suggestions",
            "Prokrastinations-Risiko": "procrastination_risk.display_procrastination_assessment"
        }
        
        page = st.radio("Navigation", list(pages.keys()))
        
        if st.button("Logout", key="logout_button"):
            logout_user(cookies)
    
    # Load page dynamically - only import the module when needed
    if page == "Dashboard":
        display_dashboard(user_id, username)
    else:
        # Dynamic import to avoid circular dependencies and minimize loading time
        module_name, function_name = pages[page].split(".")
        module = __import__(module_name)
        getattr(module, function_name)(user_id)