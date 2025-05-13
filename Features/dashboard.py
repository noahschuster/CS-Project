import streamlit as st
from datetime import datetime, timedelta
import streamlit.components.v1 as components
import pandas as pd

# Import unserer Module
from api_connection import get_user_courses
from utils import get_user_sessions, get_user_learning_type
from database_manager import delete_session_token, get_calendar_events
# Updated import for Seaborn chart functions
from dashboard_charts import (
    create_donut_chart_lernzeiten_seaborn,  # Changed function name
    create_donut_chart_next_week_seaborn    # Changed function name
)

# Konstanten
SESSION_COOKIE_NAME = "studybuddy_session_token"

# Cache Funktionen um die Datenbankabfragen zu optimieren (Empfehlung von Stackoverflow um Ladezeiten zu reduzieren)
@st.cache_data(ttl=600, max_entries=32)
def get_cached_user_learning_type(user_id):
    return get_user_learning_type(user_id)

@st.cache_data(ttl=600, max_entries=32)
def get_cached_user_courses(user_id):
    return get_user_courses(user_id)

@st.cache_data(ttl=300, max_entries=32)
def get_cached_calendar_events(user_id):
    return get_calendar_events(user_id)

# prüfe ob Nutzer eingeloggt ist
def check_login():
    """Überprüft den Status der Benutzeranmeldung"""
    if not st.session_state.get("logged_in", False):
        st.warning("Bitte melden Sie sich an, um auf das Dashboard zuzugreifen.")
        st.stop()
    return st.session_state.get("user_id"), st.session_state.get("username")

def logout_user(cookies):
    """Erledigt die Benutzerabmeldung"""
    session_token = cookies.get(SESSION_COOKIE_NAME)
    if session_token:
        delete_session_token(session_token)
        try:
            del cookies[SESSION_COOKIE_NAME]
            cookies.save()
        except KeyError:
            pass
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.update({
        "logged_in": False,
        "username": None,
        "user_id": None,
        "login_attempted": False,
        "learning_type_completed": False
    })
    try:
        st.query_params.clear()
    except Exception:
        pass
    components.html(
        """
        <script>window.parent.location.reload();</script>
        <p>Logging out...</p>
        """,
        height=50
    )
    st.stop()

def display_upcoming_deadlines(user_id):
    """Anzeige anstehender Fristen mit effizienter Datenverarbeitung"""
    today = datetime.now().date()
    events = get_cached_calendar_events(user_id)
    deadline_types = ["Aufgabe fällig", "Prüfung", "Projekt fällig"]
    upcoming_deadlines = []
    for event in events:
        if not (event.get("is_deadline", False) or event.get("type") in deadline_types):
            continue
        try:
            deadline_date = datetime.strptime(event["date"], "%Y-%m-%d").date()
            if today <= deadline_date <= today + timedelta(days=14):
                event["days_left"] = (deadline_date - today).days
                upcoming_deadlines.append(event)
        except (ValueError, TypeError):
            continue
    upcoming_deadlines.sort(key=lambda e: e.get("days_left", 14))
    if upcoming_deadlines:
        for deadline in upcoming_deadlines:
            days_left = deadline["days_left"]
            if days_left == 0:
                days_text = "⚠️ HEUTE"
            elif days_left == 1:
                days_text = "⚠️ MORGEN"
            else:
                days_text = f"In {days_left} Tagen"
            st.markdown(
                f"""<div style=\'background-color: {deadline['color']}; padding: 8px;
                 border-radius: 5px; margin-bottom: 5px;\'>
                <strong>{deadline['title']}</strong> ({deadline['type']})<br>
                Fällig: {deadline['date']} um {deadline['time']} - <strong>{days_text}</strong>
                </div>""",
                unsafe_allow_html=True
            )
    else:
        st.info("Keine Termine in den nächsten 14 Tagen! 🎉")

def display_dashboard(user_id, username):
    """Hauptanzeige des Dashboards mit optimiertem Datenabruf"""
    st.title("StudyBuddy Dashboard")
    st.subheader("Deine Learning Journey")

    learning_type = get_cached_user_learning_type(user_id)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Quick Stats")
        try:
            user_courses = get_cached_user_courses(user_id)
            course_count = len(user_courses) if user_courses else 0
        except Exception as e:
            st.error(f"Fehler beim Abrufen von Kursen: {str(e)}")
            course_count = "Error"
        try:
            sessions_df = get_user_sessions(user_id)
            session_count = len(sessions_df)
            if not sessions_df.empty and "duration_hours" in sessions_df.columns:
                total_hours = sessions_df["duration_hours"].sum()
            else:
                total_hours = 0
        except Exception as e:
            st.error(f"Fehler beim Abrufen von Sitzungen: {str(e)}")
            session_count = "Error"
            total_hours = "Error"
            sessions_df = pd.DataFrame()
        st.metric("Eingeschriebene Kurse", course_count)
        st.metric("Lern-Sessions", session_count)
        st.metric("Studienstunden insgesamt", f"{total_hours:.1f}" if isinstance(total_hours, (int, float)) else total_hours)

        st.write("### Lernzeiten nach Thema")
        st.write("Dieses Diagramm zeigt, wie viel Zeit du für die einzelnen Themen oder Fächer aufgewendet hast. Es hilft dir, deine Lernzeit besser zu verstehen und zu priorisieren.")
        # Updated to call Seaborn chart function and display with st.pyplot
        fig1 = create_donut_chart_lernzeiten_seaborn(user_id)
        st.pyplot(fig1)
    
    with col2:
        st.subheader("Letzte Aktivitäten")
        if isinstance(session_count, int) and session_count > 0 and not sessions_df.empty:
            recent_sessions = sessions_df.head(5)
            for _, session in recent_sessions.iterrows():
                login_time = session.get("login_time", "N/A")
                login_time_str = login_time.strftime("%Y-%m-%d %H:%M") if isinstance(login_time, datetime) else str(login_time)
                duration = session.get("duration_hours", 0)
                st.write(f"📚 Study session am {login_time_str} - Dauer: {duration:.1f} Stunden")
        elif session_count == 0:
            st.write("In letzter Zeit wurden keine Aktivitäten verzeichnet.")
        
        st.subheader("Kommende Fristen")
        display_upcoming_deadlines(user_id)

        st.subheader("Dein Lernprofil")
        if learning_type:
            st.info(f"Ihr identifizierter Lerntyp: {learning_type}")
            st.write("Auf der Grundlage Ihres Lerntyps haben wir Ihr Erlebnis individuell gestaltet.")
        else:
            st.warning("Sie haben Ihren Lerntyp noch nicht festgelegt. Gehen Sie zum Abschnitt Lerntyp, um das Quiz zu absolvieren.")
            
        st.write("### Zeitnutzung der nächsten Woche")
        st.write("Das Diagramm zeigt, wie viel Zeit von den geplanten 40 Stunden der nächsten Woche bereits durch Termine belegt ist. So kannst du sehen, wie viel Kapazität dir noch zur Verfügung steht.")
        # Updated to call Seaborn chart function and display with st.pyplot
        fig2 = create_donut_chart_next_week_seaborn(user_id)
        st.pyplot(fig2)

def main(cookies):
    """Einstiegspunkt für das Dashboard"""
    if not cookies.ready():
        st.stop()
    user_id, username = check_login()
    if not st.session_state.get("learning_type_completed", False):
        from learning_type import display_learning_type
        display_learning_type(user_id)
        return
    with st.sidebar:
        st.title("StudyBuddy")
        st.write(f"Willkommen, {username.capitalize()}!")
        pages = {
            "Dashboard": display_dashboard,
            "Kalender": "calendar_study.display_calendar",
            "Kurse": "api_connection.display_hsg_api_page",
            "Lern-Tips": "learning_tipps.display_learning_tips",
            "Lern-Empfehlungen": "learning_suggestions.display_learning_suggestions",
            "Prokrastinations-Risiko": "procrastination_risk.run_procrastination_questionnaire"
        }
        page = st.radio("Navigation", list(pages.keys()))
        if st.button("Logout", key="logout_button"):
            logout_user(cookies)
    if page == "Dashboard":
        display_dashboard(user_id, username)
    else:
        module_name, function_name = pages[page].split(".")
        module = __import__(module_name)
        if page == "Prokrastinations-Risiko" and function_name == "run_procrastination_questionnaire":
            getattr(module, function_name)()
        else:
            getattr(module, function_name)(user_id)

