import streamlit as st
from datetime import datetime
import streamlit.components.v1 as components

# Import unserer Module
from courses import get_user_courses
from learning_type import get_user_learning_type
from database_manager import get_user_sessions
from database_manager import delete_session_token, get_calendar_events
from dashboard_charts import (
    create_pie_chart_learning_time_by_subject,
    create_pie_chart_next_week_usage
)

# Konstanten
SESSION_COOKIE_NAME = "studybuddy_session_token"

# manche dependencies (e.g., streamlit_cookie_manager) nutzen die alte Version st.cache aber streamlit hat diese Funktion durch cache_data oder cache_resource ersetzt, da wir die libraries nicht überschreiben können ersetzen wir st.cache hiermit (wir haben diese Lösung im Streamlit Discussion Forum gefunden)
if hasattr(st, "cache"):
    st.cache = st.cache_data

# prüfe ob Nutzer eingeloggt ist
def check_login():
    if not st.session_state.get("logged_in", False):
        st.warning("Bitte melden Sie sich an, um auf das Dashboard zuzugreifen.")
        st.stop()
    return st.session_state.get("user_id"), st.session_state.get("username")

# nutzer abmelden
def logout_user(cookies):
    # holt session token aus cookies
    session_token = cookies.get(SESSION_COOKIE_NAME)

    # löscht token von datenbank wenn existiert
    if session_token:
        delete_session_token(session_token)

    # löscht cookie vom browser
    if session_token:
        try:
            del cookies[SESSION_COOKIE_NAME]
            cookies.save()
        except KeyError:
            pass  # pass, weil es sein kann, dass Cookie schon entfernt wurde / nicht existiert

    # Streamlit session state löschen
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    # minimal Session state zurücksetzen
    st.session_state.update({
        "logged_in": False,
        "username": None,
        "user_id": None,
        "login_attempted": False,
        "learning_type_completed": False
    })

    # URL parameter löschen
    try:
        st.query_params.clear()
    except Exception:
        pass

    # page reload erzwingen
    components.html(
        """
        <script>window.parent.location.reload();</script>
        <p>Logging out...</p>
        """,
        height=50
    )
    st.stop()

# anzeigen anstehender Fristen
def display_upcoming_deadlines(user_id):
    today = datetime.now().date()  # heutiges Datum
    events = get_calendar_events(user_id)  # kalender events holen
    
    if not events:
        st.info("Keine Kalendereinträge vorhanden.")
        return
    
    # Korrekte Deadline-Typen definieren
    deadline_types = ["Fällige Aufgabe", "Prüfung", "Projekt fällig"]
    
    upcoming_deadlines = []
    
    for event in events:
        # Überprüfe, ob es sich um ein Deadline-Event handelt
        event_type = event.get('type', '')
        is_deadline = event.get('is_deadline', False)
        is_deadline_type = event_type in deadline_types
        
        if not (is_deadline or is_deadline_type):
            continue
        
        # Überprüfe, ob das Event ein gültiges Datum hat
        if 'date' not in event or not event['date']:
            continue
        
        try:
            deadline_date = datetime.strptime(event['date'], "%Y-%m-%d").date()
            days_left = (deadline_date - today).days
            
            # Nur Events der nächsten 14 Tage anzeigen
            if 0 <= days_left <= 14:
                event['days_left'] = days_left
                upcoming_deadlines.append(event)
        except ValueError:
            continue
    
    # Nach Datum sortieren
    upcoming_deadlines.sort(key=lambda e: e.get('days_left', 14))
    
    # Deadlines anzeigen
    if upcoming_deadlines:
        for deadline in upcoming_deadlines:
            days_left = deadline['days_left']
            # Formatieren
            if days_left == 0:
                days_text = "⚠️ HEUTE"
            elif days_left == 1:
                days_text = "⚠️ MORGEN"
            else:
                days_text = f"In {days_left} Tagen"
            
            # Custom Styling
            st.markdown(
                f"""<div style='background-color: {deadline['color']}; padding: 8px;
                 border-radius: 5px; margin-bottom: 5px;'>
                <strong>{deadline['title']}</strong> ({deadline['type']})<br>
                Fällig: {deadline['date']} um {deadline['time']} - <strong>{days_text}</strong>
                </div>""",
                unsafe_allow_html=True
            )
    else:
        st.info("Keine Termine in den nächsten 14 Tage! 🎉")

# Dashboard anzeigen
def display_dashboard(user_id, username):
    st.title("StudyBuddy Dashboard")
    st.subheader("Deine Learning Journey")
    
    # lerntyp, kurse und sessions holen
    learning_type = get_user_learning_type(user_id)
    user_courses = get_user_courses(user_id) or []
    sessions_df = get_user_sessions(user_id)
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Quick Stats")
        
        # metriken kalkulieren
        course_count = len(user_courses)
        session_count = len(sessions_df)
        total_hours = sessions_df["duration_hours"].sum() if not sessions_df.empty else 0

        # metriken anzeigen
        st.metric("Eingeschriebene Kurse", course_count)
        st.metric("Lern-Sessions", session_count)
        st.metric("Studienstunden insgesamt", f"{total_hours:.1f}")

        # Diagramm 1
        st.write("### Lernzeiten nach Thema")
        st.write("Dieses Diagramm zeigt, wie viel Zeit du für die einzelnen Themen oder Fächer aufgewendet hast. Es hilft dir, deine Lernzeit besser zu verstehen und zu priorisieren.")
        create_pie_chart_learning_time_by_subject(user_id)

    with col2:
        st.subheader("Letzte Aktivitäten")
        
        # die letzten sessions anzeigen
        if session_count > 0:
            recent_sessions = sessions_df.head(5)
            for _, session in recent_sessions.iterrows():
                login_time = session.get("login_time", "N/A")
                login_time_str = login_time.strftime("%Y-%m-%d %H:%M") if isinstance(login_time, datetime) else str(login_time)
                duration = session.get("duration_hours", 0)
                st.write(f"📚 Study session am {login_time_str} - Dauer: {duration:.1f} Stunden")
        else:
            st.write("In letzter Zeit wurden keine Aktivitäten verzeichnet.")

        # deadlines und lerntyp /profil anzeigen
        st.subheader("Kommende Fristen")
        display_upcoming_deadlines(user_id)

        st.subheader("Dein Lernprofil")
        if learning_type:
            st.info(f"Ihr identifizierter Lerntyp: {learning_type}")
            st.write("Auf der Grundlage Ihres Lerntyps haben wir Ihr Erlebnis individuell gestaltet.")
        else:
            st.warning("Sie haben Ihren Lerntyp noch nicht festgelegt. Gehen Sie zum Abschnitt Lerntyp, um das Quiz zu absolvieren.")

        # Diagramm 2
        st.write("### Zeitnutzung der nächsten Woche")
        st.write("Das Diagramm zeigt, wie viel Zeit von den geplanten 40 Stunden der nächsten Woche bereits durch Termine belegt ist. So kannst du sehen, wie viel Kapazität dir noch zur Verfügung steht.")
        create_pie_chart_next_week_usage(user_id)

# Einstiegspunkt Dashboard
def main(cookies):
    # cookie readiness checken
    if not cookies.ready():
        st.stop()

    user_id, username = check_login()

    # überprüfe ob das Questionnaire zum Lerntyp schon ausgefüllt wurde; wenn nicht, dann wird User nochmal dorthin geleitet es nochmal auszufüllen
    if not st.session_state.get("learning_type_completed", False):
        # Nur importieren, wenn nötig
        from learning_type import display_learning_type
        display_learning_type(user_id)
        return

    # streamlit sidebar
    with st.sidebar:
        st.title("StudyBuddy")
        st.write(f"Willkommen, {username.capitalize()}!")

        # Navigationselemente
        pages = {
            "Dashboard": display_dashboard,
            "Kalender": "calendar_study.display_calendar",
            "Kurse": "courses.display_hsg_api_page",
            "Lern-Tips": "learning_tipps.display_learning_tips",
            "Lern-Empfehlungen": "learning_suggestions.display_learning_suggestions",
            "Prokrastinations-Risiko": "procrastination_risk.run_procrastination_questionnaire" # MODIFIED HERE
        }

        page = st.radio("Navigation", list(pages.keys()))

        if st.button("Logout", key="logout_button"):
            logout_user(cookies)

    # Seite dynamisch laden
    if page == "Dashboard":
        display_dashboard(user_id, username)
    else:
        # dynamischer import um effizienz zu erhöhen
        module_name, function_name = pages[page].split(".")
        module = __import__(module_name)

        if page == "Prokrastinations-Risiko" and function_name == "run_procrastination_questionnaire":
            getattr(module, function_name)()
        else:
            getattr(module, function_name)(user_id)