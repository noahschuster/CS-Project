import streamlit as st
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union

from database_manager import (
    get_calendar_events,
    save_calendar_event,
    get_learning_type_status,
    save_study_task,
    get_study_tasks,
    update_study_task_status,
    update_study_task,
    delete_study_task
)
from api_connection import get_user_courses


def display_learning_suggestions(user_id: str) -> None:
    """Main function to display personalized learning suggestions based on learning type."""
    st.title("Personalisierte Lernvorschläge")
    
    # Check if learning type is already set
    learning_type, completed = get_learning_type_status(user_id)
    
    if not completed:
        st.warning("Du hast deinen Lerntyp noch nicht festgelegt. Bitte beantworte zuerst die Fragen zum Lerntyp.")
        from learning_type import display_learning_type
        display_learning_type(user_id)
        return
    
    # Tabs for different functions
    tab1, tab2 = st.tabs(["Lernplan generieren", "Meine Lernaufgaben"])
    
    with tab1:
        _display_learning_plan_generator(user_id, learning_type)
    
    with tab2:
        display_study_tasks(user_id)


def _display_learning_plan_generator(user_id: str, learning_type: str) -> None:
    """Display the learning plan generator interface."""
    st.subheader("Lernplan basierend auf deinem Lerntyp")
    st.write(f"Dein Lerntyp: **{learning_type}**")
    
    # Get user courses
    user_courses = get_user_courses(user_id)
    
    # Fix: Check if list is empty using Python's standard way
    if not user_courses:
        st.info("Du hast noch keine Kurse ausgewählt. Bitte wähle zuerst deine Kurse aus.")
        return
    
    # Form for creating a study plan
    with st.form("generate_study_plan"):
        st.write("Wähle die Kurse aus, für die du einen Lernplan erstellen möchtest:")
        
        selected_courses = []
        for course in user_courses:  # Assuming user_courses is a list of course dictionaries
            if st.checkbox(f"{course['meeting_code']} - {course['title']}", value=True):
                selected_courses.append({
                    'id': course['course_id'],
                    'title': course['title'],
                    'code': course['meeting_code']
                })
        
        st.write("Zeitraum für den Lernplan:")
        start_date = st.date_input("Startdatum", datetime.now().date())
        weeks = st.slider("Anzahl Wochen", 1, 4, 2)
        
        submit_button = st.form_submit_button("Lernplan generieren")
    
    # Generate study plan when submitted
    if submit_button and selected_courses:
        _handle_study_plan_generation(user_id, selected_courses, start_date, weeks, learning_type)

    # Save button for the generated plan
    if st.button("Lernplan im Kalender speichern", key="save_calendar_button"):
        _handle_study_plan_saving(user_id)


def _handle_study_plan_generation(
    user_id: str, 
    selected_courses: List[Dict[str, str]], 
    start_date: datetime.date, 
    weeks: int, 
    learning_type: str
) -> None:
    """Handle the generation of a study plan and display it."""
    # Get existing calendar events
    calendar_events = get_calendar_events(user_id)
    
    # Generate study plan
    study_plan = generate_study_plan(
        user_id, 
        selected_courses, 
        start_date, 
        weeks, 
        learning_type, 
        calendar_events
    )
    
    if study_plan:
        # Save the study plan in session state
        st.session_state.study_plan = study_plan
        
        st.success(f"Lernplan für {len(selected_courses)} Kurse über {weeks} Wochen erstellt!")
        
        # Display the study plan
        display_study_plan(study_plan)


def _handle_study_plan_saving(user_id: str) -> None:
    """Handle saving the generated study plan to the calendar."""
    if 'study_plan' in st.session_state and st.session_state.study_plan:
        success = save_study_plan_to_calendar(user_id, st.session_state.study_plan)
        if success:
            st.success("Lernplan wurde im Kalender gespeichert!")
            st.rerun()
    else:
        st.error("Kein Lernplan zum Speichern vorhanden. Bitte generiere zuerst einen Lernplan.")


def generate_study_plan(
    user_id: str, 
    courses: List[Dict[str, str]], 
    start_date: datetime.date, 
    weeks: int, 
    learning_type: str, 
    existing_events: List[Dict[str, str]]
) -> List[Dict[str, Any]]:
    """
    Generate a study plan based on courses, learning type, and timeframe.
    Takes into account existing calendar events to avoid conflicts.
    """
    study_plan = []
    
    # Working hours between 10 and 18
    work_hours = list(range(10, 18))
    
    # Convert existing events to a format for easy access
    busy_slots = _get_busy_time_slots(existing_events)
    
    # Plan 4 hours per week for each course (2 sessions of 2 hours each)
    for course in courses:
        for week in range(weeks):
            # Calculate the date for this week
            current_week_start = start_date + timedelta(days=week * 7)
            
            # Try to plan 2 sessions per week
            sessions_planned = 0
            attempts = 0
            
            while sessions_planned < 2 and attempts < 20:  # Limit attempts to avoid infinite loops
                attempts += 1
                
                # Choose a random day this week
                random_day = random.randint(0, 6)
                session_date = current_week_start + timedelta(days=random_day)
                date_str = session_date.strftime("%Y-%m-%d")
                
                # Choose a random start time (must be at least 2 hours before end of working day)
                available_hours = [
                    h for h in work_hours[:-1] if 
                    date_str not in busy_slots or 
                    (h not in busy_slots.get(date_str, []) and h+1 not in busy_slots.get(date_str, []))
                ]
                
                if not available_hours:
                    continue  # No available times on this day
                
                start_hour = random.choice(available_hours)
                
                # Generate study content based on course and learning type
                study_content = generate_study_content(course, learning_type)
                
                # Add session to plan
                session = {
                    'course_id': course['id'],
                    'course_title': course['title'],
                    'course_code': course['code'],
                    'date': date_str,
                    'start_time': f"{start_hour:02d}:00",
                    'end_time': f"{start_hour+2:02d}:00",
                    'content': study_content,
                    'completed': False
                }
                
                study_plan.append(session)
                
                # Mark this time as occupied
                if date_str not in busy_slots:
                    busy_slots[date_str] = []
                busy_slots[date_str].extend([start_hour, start_hour + 1])
                
                sessions_planned += 1
    
    # Sort the plan by date and time
    study_plan.sort(key=lambda x: (x['date'], x['start_time']))
    
    return study_plan


def _get_busy_time_slots(events: List[Dict[str, str]]) -> Dict[str, List[int]]:
    """Extract busy time slots from calendar events."""
    busy_slots = {}
    
    for event in events:
        date = event['date']
        hour = int(event['time'].split(':')[0])
        
        if date not in busy_slots:
            busy_slots[date] = []
        
        # Block 2 hours for each event
        busy_slots[date].extend([hour, hour + 1])
    
    return busy_slots


def get_course_content(course_code: str) -> List[str]:
    """
    Get content from the subject summary for a specific course.
    """
    # Example course contents - in a complete implementation we would parse the subject summary document
    course_contents = {
        "BWL": [
            "Geschäftsprozesse und Marketingkonzept",
            "Marktanalyse",
            "Marketingstrategie",
            "Marktleistungsgestaltung",
            "Preisgestaltung, Kommunikation, Distribution",
            "Controlling und Innovation",
            "Management und Managementmodelle",
            "Entscheidungen und Kommunikation",
            "Strategie und Entwicklungsmodi",
            "Struktur und Kultur",
            "Führung und Governance",
            "Umwelt und Interaktionsthemen"
        ],
        "VWL": [
            "Grundlagen der ökonomischen Denkweise",
            "Spezialisierung und Tausch",
            "Angebot und Nachfrage",
            "Externe Effekte und die Grenzen des Marktes",
            "Kosten & Unternehmen auf Märkten mit Vollständiger Konkurrenz",
            "Unternehmensverhalten auf Monopolmärkten",
            "Grundlagen der Spieltheorie",
            "Unternehmensverhalten auf Oligopolmärkten"
        ],
        "Buchhaltung": [
            "Zweck der Buchhaltung, Inventar und Bilanz",
            "Bilanzkonten und Buchungssatz",
            "Erfolgsrechnung",
            "Einzelunternehmen, Warenhandel",
            "Zahlungsverkehr, Produktionsbetrieb",
            "Abschreibungen, Wertberichtigungen, Forderungsverluste",
            "Immobilien, Rechnungsabgrenzung und Rückstellungen",
            "Wertschriften",
            "Aktiengesellschaft",
            "Stille Reserven"
        ],
        "Mathe": [
            "Mathematische Logik Folgen & Reihen",
            "Folgen & Reihen",
            "Funktionen",
            "Differenzierbarkeit I",
            "Differenzierbarkeit II Extremstellen",
            "Taylorpolynome",
            "Funktionen zweier reeller Variablen",
            "Der Satz über die implizite Funktion",
            "Extrema von Funktionen zweier Variablen mit & ohne Nebenbedingungen",
            "Funktionen zweier reeller Variablen",
            "Deskriptive Statistik und Wahrscheinlichkeitstheorie",
            "Optimierungsprobleme in Wirtschaft und Statistik"
        ],
        "Recht": [
            "Einführung ins Privatrecht",
            "Einführung in das Vertragsrecht und Willensbildung",
            "Vertragsgestaltung und -erfüllung",
            "Vertragsänderung, -durchführung und -verletzung",
            "Haftung",
            "Schlechterfüllung und Gewährleistung",
            "Produkthaftung und vertragliche Sanktionen",
            "Erlöschen vertraglicher Pflichten"
        ]
    }
    
    # Try to identify the course by code
    for course_name, topics in course_contents.items():
        if course_name.lower() in course_code.lower():
            return topics
    
    # If no matching course was found, return a general list
    return ["Kapitel 1", "Kapitel 2", "Kapitel 3", "Kapitel 4", "Kapitel 5"]


def generate_study_content(course: Dict[str, str], learning_type: str) -> Dict[str, Any]:
    """
    Generate study content based on course and learning type.
    Uses the subject summary for relevant content.
    """
    # Get course content from the subject summary
    course_topics = get_course_content(course['code'])
    
    # Choose a random topic
    topic = random.choice(course_topics) if course_topics else f"Kapitel {random.randint(1, 10)}"
    
    # Learning methods based on learning type
    method_map = {
        "Visual": [
            f"Erstelle Mind-Maps zu '{topic}'",
            f"Arbeite mit farbigen Notizen und Markierungen zu '{topic}'",
            f"Visualisiere die Prozesse in '{topic}' durch Diagramme",
            f"Suche Videos und visuelle Materialien zu '{topic}'",
            f"Erstelle Infografiken zu den Schlüsselkonzepten in '{topic}'"
        ],
        "Auditory": [
            f"Nimm deine Zusammenfassung von '{topic}' auf und höre sie mehrmals",
            f"Diskutiere '{topic}' mit Kommilitonen in einer Studiengruppe",
            f"Erkläre die Konzepte von '{topic}' laut, als würdest du sie jemandem beibringen",
            f"Suche Podcasts oder Vorlesungsaufzeichnungen zu '{topic}'",
            f"Führe ein Selbstgespräch über '{topic}' und stelle dir selbst Fragen"
        ],
        "Reading/Writing": [
            f"Erstelle eine detaillierte Zusammenfassung von '{topic}'",
            f"Schreibe Karteikarten zu den Schlüsselkonzepten in '{topic}'",
            f"Lies die empfohlene Literatur zu '{topic}' und mache Notizen",
            f"Formuliere Antworten auf mögliche Prüfungsfragen zu '{topic}'",
            f"Erstelle ein Glossar der wichtigsten Begriffe in '{topic}'"
        ],
        "Kinesthetic": [
            f"Löse praktische Übungen und Fallstudien zu '{topic}'",
            f"Wende die Konzepte von '{topic}' auf reale Situationen an",
            f"Erstelle ein physisches Modell oder eine Demonstration zu '{topic}'",
            f"Bewege dich beim Lernen von '{topic}' (z.B. beim Gehen wiederholen)",
            f"Führe Rollenspiele oder Simulationen zu '{topic}' durch"
        ]
    }
    
    # Default methods if the learning type is not recognized
    default_methods = [
        f"Wiederhole die Vorlesungsnotizen zu '{topic}'",
        f"Löse Übungsaufgaben zu '{topic}'",
        f"Diskutiere '{topic}' mit Kommilitonen",
        f"Erstelle eine Zusammenfassung von '{topic}'",
        f"Bereite Fragen zu '{topic}' vor und beantworte sie"
    ]
    
    methods = method_map.get(learning_type, default_methods)
    
    # Choose 2-3 methods
    selected_methods = random.sample(methods, min(3, len(methods)))
    
    return {
        'topic': topic,
        'methods': selected_methods
    }


def display_study_plan(study_plan: List[Dict[str, Any]]) -> None:
    """Display the generated study plan."""
    for session in study_plan:
        with st.expander(f"{session['date']} | {session['start_time']} - {session['end_time']} | {session['course_code']}"):
            st.write(f"**Kurs:** {session['course_title']}")
            st.write(f"**Thema:** {session['content']['topic']}")
            st.write("**Empfohlene Lernmethoden:**")
            for method in session['content']['methods']:
                st.write(f"- {method}")


def save_study_plan_to_calendar(user_id: str, study_plan: List[Dict[str, Any]]) -> bool:
    """Save the study plan to the calendar and as study tasks."""
    try:
        for session in study_plan:
            # Save to calendar
            event_data = {
                'title': f"Lernen: {session['course_code']}",
                'date': session['date'],
                'time': session['start_time'],
                'type': "Study Session",
                'color': "#ccffcc",  # Light green
                'user_id': user_id
            }
            
            # Save event to calendar
            save_calendar_event(user_id, event_data)
            
            # Also save as study task
            task_data = {
                'course_id': session['course_id'],
                'course_title': session['course_title'],
                'course_code': session['course_code'],
                'date': session['date'],
                'start_time': session['start_time'],
                'end_time': session['end_time'],
                'topic': session['content']['topic'],
                'methods': session['content']['methods']
            }
            
            save_study_task(user_id, task_data)
            
        return True
    except Exception as e:
        st.error(f"Fehler beim Speichern: {e}")
        return False


def display_study_tasks(user_id: str) -> None:
    """Display the user's study tasks and enable checking, rescheduling, and deleting."""
    st.subheader("Meine Lernaufgaben")
    
    # Load tasks from database
    user_tasks = get_study_tasks(user_id)
    
    if not user_tasks:
        st.info("Du hast noch keine Lernaufgaben. Erstelle einen Lernplan, um loszulegen!")
        return
    
    # Split tasks into upcoming and past
    today = datetime.now().date()
    upcoming_tasks, past_tasks = _split_tasks_by_date(user_tasks, today)
    
    # Display upcoming tasks
    if upcoming_tasks:
        st.write("### Anstehende Lernaufgaben")
        for task in upcoming_tasks:
            col1, col2, col3 = st.columns([4, 1, 1])
            
            with col1:
                _display_task_details(task, user_id)
            
            with col2:
                _handle_task_completion(task)
            
            with col3:
                _handle_task_deletion(task)
    
    # Display past tasks
    if past_tasks:
        with st.expander("Vergangene Lernaufgaben"):
            for task in past_tasks:
                status = "✅" if task['completed'] else "❌"
                st.write(f"{status} **{task['date']}** | {task['start_time']} - {task['end_time']} | {task['course_code']} - {task['topic']}")


def _split_tasks_by_date(
    tasks: List[Dict[str, Any]], 
    reference_date: datetime.date
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Split tasks into upcoming and past based on date."""
    upcoming = []
    past = []
    
    for task in tasks:
        task_date = datetime.strptime(task['date'], "%Y-%m-%d").date()
        if task_date >= reference_date:
            upcoming.append(task)
        else:
            past.append(task)
    
    # Sort by date and time
    upcoming.sort(key=lambda x: (x['date'], x['start_time']))
    past.sort(key=lambda x: (x['date'], x['start_time']), reverse=True)
    
    return upcoming, past


def _display_task_details(task: Dict[str, Any], user_id: str) -> None:
    """Display details of a task and provide rescheduling options."""
    status = "✅" if task['completed'] else "⏳"
    expander_label = f"{status} {task['date']} | {task['start_time']} - {task['end_time']} | {task['course_code']}"
    
    with st.expander(expander_label):
        st.write(f"**Kurs:** {task['course_title']}")
        st.write(f"**Thema:** {task['topic']}")
        st.write("**Empfohlene Lernmethoden:**")
        for method in task['methods']:
            st.write(f"- {method}")
        
        # Rescheduling function
        st.write("---")
        st.write("**Termin verschieben:**")
        
        # Get available time slots
        calendar_events = get_calendar_events(user_id)
        busy_slots = _get_busy_time_slots(calendar_events)
        
        # Date selection for rescheduling
        new_date = st.date_input(
            "Neues Datum", 
            datetime.strptime(task['date'], "%Y-%m-%d").date(),
            key=f"new_date_{task['id']}"
        )
        
        # Find available time slots for the selected date
        date_str = new_date.strftime("%Y-%m-%d")
        work_hours = list(range(8, 20))  # 8:00 - 20:00
        
        # Find free time slots
        available_hours = [
            h for h in work_hours[:-1] if
            date_str not in busy_slots or
            (h not in busy_slots.get(date_str, []) and h+1 not in busy_slots.get(date_str, []))
        ]
        
        # Format hours for display
        time_options = [f"{h:02d}:00" for h in available_hours]
        
        # If no free slots are available, show all times
        if not time_options:
            time_options = [f"{h:02d}:00" for h in work_hours[:-1]]
        
        # Select start time
        try:
            default_index = time_options.index(task['start_time']) if task['start_time'] in time_options else 0
        except (ValueError, IndexError):
            default_index = 0
            
        new_start_time = st.selectbox(
            "Neue Startzeit", 
            time_options,
            index=default_index,
            key=f"new_start_{task['id']}"
        )
        
        # Calculate end time (2 hours after start time)
        start_hour = int(new_start_time.split(':')[0])
        new_end_time = f"{start_hour+2:02d}:00"
        
        st.write(f"Neue Endzeit: {new_end_time}")
        
        # Button to save changes
        if st.button("Termin verschieben", key=f"move_{task['id']}"):
            # Prepare data for update
            update_data = {
                'date': date_str,
                'start_time': new_start_time,
                'end_time': new_end_time
            }
            
            # Update task in database
            if update_study_task(task['id'], update_data):
                st.success("Termin erfolgreich verschoben!")
                st.rerun()
            else:
                st.error("Fehler beim Verschieben des Termins.")


def _handle_task_completion(task: Dict[str, Any]) -> None:
    """Handle marking a task as completed."""
    completed = st.checkbox("Erledigt", value=task['completed'], key=f"task_{task['id']}")
    
    if completed != task['completed']:
        # Update status in database
        if update_study_task_status(task['id'], completed):
            st.success("Status aktualisiert")
            st.rerun()


def _handle_task_deletion(task: Dict[str, Any]) -> None:
    """Handle deleting a task."""
    if st.button("Löschen", key=f"delete_{task['id']}"):
        # Delete task from database
        if delete_study_task(task['id']):
            st.success(f"Aufgabe gelöscht")
            st.rerun()
        else:
            st.error("Fehler beim Löschen der Aufgabe")