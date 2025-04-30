# dashboard.py
import streamlit as st
import os
from learning_tipps import display_learning_tips
from datetime import datetime, timedelta
from streamlit_cookies_manager import EncryptedCookieManager
# Assuming api_connection and utils are correctly set up for Azure SQL
import api_connection 
from utils import get_user_sessions, get_user_learning_type
# Import the specific function needed for logout from database_manager
from database_manager import delete_session_token

# --- Configuration (should match main.py) ---
# IMPORTANT: Use environment variables or a shared config module in a real app
COOKIE_PASSWORD = os.environ.get("COOKIE_PASSWORD", "default_insecure_password_change_me_12345")
SESSION_COOKIE_NAME = "studybuddy_session_token"

# --- Helper Functions ---
def check_login():
    """Ensures the user is logged in via session_state."""
    if not st.session_state.get("logged_in", False):
        st.warning("Please log in to access the dashboard.")
        # Redirect to login or stop execution if not logged in
        # Since this is called from main.py after checks, 
        # this might indicate an unexpected state.
        st.stop() 
    return st.session_state.get("user_id"), st.session_state.get("username")

def logout_user(cookies):
    """Handles user logout: deletes token, cookie, and clears session state."""
    print("Logout initiated.") # Debug
    
    # 1. Get session token from cookie
    session_token = cookies.get(SESSION_COOKIE_NAME)
    
    # 2. Delete token from database if it exists
    if session_token:
        print(f"Deleting session token {session_token[:8]}... from DB.") # Debug
        deleted_from_db = delete_session_token(session_token)
        if not deleted_from_db:
            print(f"Warning: Session token {session_token[:8]}... not found or error during DB deletion.")
    else:
        print("No session cookie found during logout.") # Debug

    # 3. Delete the cookie from the browser
    if session_token: # Only try deleting if we think one existed 
        # Use dictionary-style deletion 
        try: 
            del cookies[SESSION_COOKIE_NAME]
            cookies.save() # Save immediately
            print("Session cookie deleted from browser.") # Debug
        except KeyError:
            print(f"Cookie {SESSION_COOKIE_NAME} not found for deletion, might have already been removed.") # Debug

    # 4. Clear Streamlit session state
    print("Clearing Streamlit session state.") # Debug
    # Store keys to delete, then delete to avoid modifying during iteration
    keys_to_delete = list(st.session_state.keys())
    for key in keys_to_delete:
        del st.session_state[key]
    
    # 5. Clear URL parameters (optional but good practice)
    try:
        st.query_params.clear()
        print("Query parameters cleared.") # Debug
    except Exception as e:
        print(f"Error clearing query params during logout: {e}")

    # 6. Re-initialize minimal session state for login page
    # This prevents errors if parts of the login page rely on these keys existing
    st.session_state["logged_in"] = False
    st.session_state["username"] = None
    st.session_state["user_id"] = None
    st.session_state["login_attempted"] = False # Reset login attempt flag
    st.session_state["learning_type_completed"] = False # Reset learning type flag
    print("Logout process complete.") # Debug
    
    # 7. Force a complete browser reload using JavaScript
    import streamlit.components.v1 as components
    
    # Simple JavaScript to reload the page
    components.html(
        """
        <script>
            // Force a complete page reload
            window.parent.location.reload();
        </script>
        <p>Logging out...</p>
        """,
        height=50
    )
    
    # Stop execution to prevent any further code from running
    st.stop()

def display_upcoming_deadlines(user_id):
    """Display upcoming deadlines on the dashboard."""
    from database_manager import get_calendar_events
    
    # Get today's date
    today = datetime.now().date()
    
    # Get events from database
    events = get_calendar_events(user_id)
    
    # Filter deadlines - using is_deadline flag from database
    deadline_types = ["Assignment Due", "Exam", "Project Due"]
    upcoming_deadlines = [
        event for event in events
        if (event.get('is_deadline', False) or 
            event.get('type') in deadline_types) and
           today <= datetime.strptime(event['date'], "%Y-%m-%d").date() <= today + timedelta(days=14)
    ]
    
    # Sort by date
    upcoming_deadlines.sort(key=lambda e: datetime.strptime(e['date'], "%Y-%m-%d"))
    
    # Display deadlines
    if upcoming_deadlines:
        for deadline in upcoming_deadlines:
            deadline_date = datetime.strptime(deadline['date'], "%Y-%m-%d").date()
            days_left = (deadline_date - today).days
            
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


# --- Main Dashboard UI --- 
def main(cookies):
    # Ensure cookie manager is ready (important if dashboard could be entry point)
    if not cookies.ready():
        st.stop()
    
    user_id, username = check_login()
    
    # Check if learning type is completed - redirect if not
    if not st.session_state.get("learning_type_completed", False):
        # Redirect to learning type page
        from learning_type import display_learning_type
        display_learning_type(user_id)
        return
    
    with st.sidebar:
        st.title("StudyBuddy")
        st.write(f"Welcome, {username}!")
        
        page = st.radio(
            "Navigation",
            ["Dashboard", "Calendar", "Courses", "Learning Type", "Study Sessions", "Learning Tips", "Learning Suggestions"])
        
        if st.button("Logout", key="logout_button"):
            logout_user(cookies) # Pass cookies object
            # logout_user now handles rerun, so no need for state changes here
    
    # Page Routing (ensure imports are within functions or conditional)
    if page == "Dashboard":
        display_dashboard(user_id, username)
    elif page == "Courses":
        # Lazy import to avoid circular dependencies or loading unused code
        from courses import display_courses 
        display_courses(user_id)
    elif page == "Learning Type":
        from learning_type import display_learning_type
        display_learning_type(user_id)
    elif page == "Study Sessions":
        from study_sessions import display_study_sessions
        display_study_sessions(user_id)
    elif page == "Learning Tips":
        from learning_tipps import display_learning_tips
        display_learning_tips(user_id)
    elif page == "Calendar":
        from calendar_study import display_calendar
        display_calendar(user_id)
    elif page == "Learning Suggestions":
        from learning_suggestions import display_learning_suggestions
        display_learning_suggestions(user_id)

def display_dashboard(user_id, username):
    st.title("StudyBuddy Dashboard")
    st.subheader("Your Learning Journey")

    # Assuming get_user_learning_type and get_user_sessions use the correct DB connection
    learning_type = get_user_learning_type(user_id)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Quick Stats")
        
        try:
            # Assuming api_connection uses the correct DB connection
            user_courses = api_connection.get_user_courses(user_id)
            course_count = len(user_courses) if user_courses else 0
        except Exception as e:
            st.error(f"Error fetching courses: {e}")
            course_count = "Error"
        
        try:
            sessions_df = get_user_sessions(user_id)
            session_count = len(sessions_df)
            total_hours = sessions_df["duration_hours"].sum() if not sessions_df.empty else 0
        except Exception as e:
            st.error(f"Error fetching sessions: {e}")
            session_count = "Error"
            total_hours = "Error"
        
        st.metric("Courses Enrolled", course_count)
        st.metric("Study Sessions", session_count)
        st.metric("Total Study Hours", f"{total_hours:.1f}" if isinstance(total_hours, (int, float)) else total_hours)
        
        st.subheader("Your Learning Profile")
        if learning_type:
            st.info(f"Your identified learning type: {learning_type}")
            st.write("Based on your learning type, we've customized your experience.")
        else:
            st.warning("You haven't set your learning type yet. Go to the Learning Type section to take the quiz.")
    
    with col2:
        st.subheader("Recent Activity")
        
        if session_count != "Error" and not sessions_df.empty:
            recent_sessions = sessions_df.head(5)
            for _, session in recent_sessions.iterrows():
                # Ensure columns exist and format nicely
                login_time_str = session.get("login_time", "N/A")
                if isinstance(login_time_str, datetime):
                    login_time_str = login_time_str.strftime("%Y-%m-%d %H:%M")
                duration = session.get("duration_hours", 0)
                st.write(f"📚 Study session on {login_time_str} - Duration: {duration:.1f} hours")
        elif session_count == 0:
            st.write("No recent activity recorded.")
        # Error message handled by the try-except block above
        
        st.subheader("Upcoming Deadlines")
        display_upcoming_deadlines(user_id)

# The main() function is the entry point when called from main.py
