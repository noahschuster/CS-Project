import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random
from database_manager import get_calendar_events, save_calendar_event, get_learning_type_status
from api_connection import get_user_courses
import calendar_study

# Am Anfang von learning_suggestions.py
from database_manager import (
    get_calendar_events, 
    save_calendar_event, 
    get_learning_type_status,
    save_study_task,
    get_study_tasks,  # Stelle sicher, dass diese Zeile vorhanden ist
    update_study_task_status,
    update_study_task,  # Neue Funktion hinzufügen
    delete_study_task   # Neue Funktion hinzufügen
)

def display_learning_suggestions(user_id):
    st.title("Personalisierte Lernvorschläge")
    
    # Prüfen, ob der Lerntyp bereits festgelegt wurde
    learning_type, completed = get_learning_type_status(user_id)
    
    if not completed:
        st.warning("Du hast deinen Lerntyp noch nicht festgelegt. Bitte beantworte zuerst die Fragen zum Lerntyp.")
        from learning_type import display_learning_type
        display_learning_type(user_id)
        return
    
    # Tabs für verschiedene Funktionen
    tab1, tab2 = st.tabs(["Lernplan generieren", "Meine Lernaufgaben"])
    
    with tab1:
        st.subheader("Lernplan basierend auf deinem Lerntyp")
        st.write(f"Dein Lerntyp: **{learning_type}**")
        
        # Kurse des Nutzers abrufen
        user_courses = get_user_courses(user_id)
        
        if user_courses.empty:
            st.info("Du hast noch keine Kurse ausgewählt. Bitte wähle zuerst deine Kurse aus.")
            return
        
        # Formular zur Erstellung des Lernplans
        with st.form("generate_study_plan"):
            st.write("Wähle die Kurse aus, für die du einen Lernplan erstellen möchtest:")
            
            selected_courses = []
            for _, course in user_courses.iterrows():
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
        
        ###
        # Ändere den Code im if-Block nach dem Generieren des Lernplans
        if submit_button and selected_courses:
            # Bestehende Kalendereinträge abrufen
            calendar_events = get_calendar_events(user_id)
            
            # Lernplan generieren
            study_plan = generate_study_plan(
                user_id, 
                selected_courses, 
                start_date, 
                weeks, 
                learning_type, 
                calendar_events
            )
            
            if study_plan:
                # Speichere den Lernplan in der Session State
                st.session_state.study_plan = study_plan
                
                st.success(f"Lernplan für {len(selected_courses)} Kurse über {weeks} Wochen erstellt!")
                
                # Anzeigen des Lernplans
                display_study_plan(study_plan)

        # Ändere den Code für den Speichern-Button
        if st.button("Lernplan im Kalender speichern", key="save_calendar_button"):
            print("button1")
            # Prüfe, ob ein Lernplan in der Session State existiert
            if 'study_plan' in st.session_state and st.session_state.study_plan:
                save_study_plan_to_calendar(user_id, st.session_state.study_plan)
                st.success("Lernplan wurde im Kalender gespeichert!")
                st.rerun()
            else:
                st.error("Kein Lernplan zum Speichern vorhanden. Bitte generiere zuerst einen Lernplan.")

    
    with tab2:
        display_study_tasks(user_id)

def generate_study_plan(user_id, courses, start_date, weeks, learning_type, existing_events):
    """
    Generiert einen Lernplan basierend auf den Kursen, dem Lerntyp und dem Zeitraum.
    Berücksichtigt bestehende Kalendereinträge, um Konflikte zu vermeiden.
    """
    study_plan = []
    
    # Arbeitstag zwischen 10 und 18 Uhr
    work_hours = list(range(10, 18))
    
    # Konvertiere bestehende Events in ein Format für einfachen Zugriff
    busy_slots = {}
    for event in existing_events:
        date = event['date']
        time_parts = event['time'].split(':')
        hour = int(time_parts[0])
        
        if date not in busy_slots:
            busy_slots[date] = []
        
        # Blockiere 2 Stunden für jedes Event (angenommen, Events dauern ca. 2 Stunden)
        busy_slots[date].extend([hour, hour + 1])
    
    # Für jeden Kurs 4 Stunden pro Woche einplanen (2 Sessions à 2 Stunden)
    for course in courses:
        for week in range(weeks):
            # Berechne das Datum für diese Woche
            current_week_start = start_date + timedelta(days=week * 7)
            
            # Versuche, 2 Sessions pro Woche zu planen
            sessions_planned = 0
            attempts = 0
            
            while sessions_planned < 2 and attempts < 20:  # Begrenze Versuche, um Endlosschleifen zu vermeiden
                attempts += 1
                
                # Zufälligen Tag in dieser Woche wählen
                random_day = random.randint(0, 6)
                session_date = current_week_start + timedelta(days=random_day)
                date_str = session_date.strftime("%Y-%m-%d")
                
                # Zufällige Startzeit wählen (muss mindestens 2 Stunden vor Ende des Arbeitstages sein)
                available_hours = [h for h in work_hours[:-1] if 
                                  date_str not in busy_slots or 
                                  (h not in busy_slots.get(date_str, []) and 
                                   h+1 not in busy_slots.get(date_str, []))]
                
                if not available_hours:
                    continue  # Keine verfügbaren Zeiten an diesem Tag
                
                start_hour = random.choice(available_hours)
                
                # Lerninhalt basierend auf Kurs und Lerntyp generieren
                study_content = generate_study_content(course, learning_type)
                
                # Session zum Plan hinzufügen
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
                
                # Markiere diese Zeit als belegt
                if date_str not in busy_slots:
                    busy_slots[date_str] = []
                busy_slots[date_str].extend([start_hour, start_hour + 1])
                
                sessions_planned += 1
    
    # Sortiere den Plan nach Datum und Uhrzeit
    study_plan.sort(key=lambda x: (x['date'], x['start_time']))
    
    return study_plan

def generate_study_content(course, learning_type):
    """
    Generiert Lerninhalt basierend auf dem Kurs und dem Lerntyp.
    Hier würde später die Fächerzusammenfassung einbezogen werden.
    """
    # Beispielhafte Inhalte basierend auf dem Lerntyp
    if learning_type == "Visual":
        methods = [
            "Erstelle Mind-Maps zu den Hauptkonzepten",
            "Arbeite mit farbigen Notizen und Markierungen",
            "Visualisiere Prozesse durch Diagramme",
            "Nutze Videos und visuelle Lernmaterialien"
        ]
    elif learning_type == "Auditory":
        methods = [
            "Nimm die Vorlesungsinhalte auf und höre sie nochmal",
            "Diskutiere den Stoff mit Kommilitonen",
            "Erkläre die Konzepte laut",
            "Nutze Podcasts und Audioressourcen"
        ]
    elif learning_type == "Reading/Writing":
        methods = [
            "Erstelle detaillierte Zusammenfassungen",
            "Schreibe Karteikarten zu Schlüsselkonzepten",
            "Lies die empfohlene Literatur",
            "Formuliere Antworten auf mögliche Prüfungsfragen"
        ]
    elif learning_type == "Kinesthetic":
        methods = [
            "Löse praktische Übungen und Fallstudien",
            "Wende Konzepte auf reale Situationen an",
            "Nutze Rollenspiele oder Simulationen",
            "Baue physische Modelle oder Demonstrationen"
        ]
    else:
        methods = [
            "Wiederhole die Vorlesungsnotizen",
            "Löse Übungsaufgaben",
            "Diskutiere den Stoff mit Kommilitonen",
            "Erstelle Zusammenfassungen"
        ]
    
    # Zufällige Auswahl von 2 Methoden
    selected_methods = random.sample(methods, 2)
    
    return {
        'topic': f"Kapitel {random.randint(1, 10)} in {course['title']}",
        'methods': selected_methods
    }

def display_study_plan(study_plan):
    """Zeigt den generierten Lernplan an"""
    for session in study_plan:
        with st.expander(f"{session['date']} | {session['start_time']} - {session['end_time']} | {session['course_code']}"):
            st.write(f"**Kurs:** {session['course_title']}")
            st.write(f"**Thema:** {session['content']['topic']}")
            st.write("**Empfohlene Lernmethoden:**")
            for method in session['content']['methods']:
                st.write(f"- {method}")

def display_study_tasks(user_id):
    """Zeigt die Lernaufgaben des Nutzers an und ermöglicht das Abhaken, Verschieben und Löschen"""
    st.subheader("Meine Lernaufgaben")
    
    # Lade Aufgaben aus der Datenbank
    user_tasks = get_study_tasks(user_id)
    
    if not user_tasks:
        st.info("Du hast noch keine Lernaufgaben. Erstelle einen Lernplan, um loszulegen!")
        return
    
    # Nach Datum sortieren und in vergangene/zukünftige aufteilen
    today = datetime.now().date()
    
    upcoming_tasks = []
    past_tasks = []
    
    for task in user_tasks:
        task_date = datetime.strptime(task['date'], "%Y-%m-%d").date()
        if task_date >= today:
            upcoming_tasks.append(task)
        else:
            past_tasks.append(task)
    
    # Sortiere nach Datum und Zeit
    upcoming_tasks.sort(key=lambda x: (x['date'], x['start_time']))
    past_tasks.sort(key=lambda x: (x['date'], x['start_time']), reverse=True)
    
    # Zukünftige Aufgaben anzeigen
    if upcoming_tasks:
        st.write("### Anstehende Lernaufgaben")
        for task in upcoming_tasks:
            col1, col2, col3 = st.columns([4, 1, 1])
            
            with col1:
                status = "✅" if task['completed'] else "⏳"
                expander_label = f"{status} {task['date']} | {task['start_time']} - {task['end_time']} | {task['course_code']}"
                
                with st.expander(expander_label):
                    st.write(f"**Kurs:** {task['course_title']}")
                    st.write(f"**Thema:** {task['topic']}")
                    st.write("**Empfohlene Lernmethoden:**")
                    for method in task['methods']:
                        st.write(f"- {method}")
                    
                    # Verschieben-Funktion innerhalb des Expanders
                    st.write("---")
                    st.write("**Termin verschieben:**")
                    
                    # Verfügbare Termine abrufen (freie Zeiten im Kalender)
                    calendar_events = get_calendar_events(user_id)
                    busy_slots = {}
                    
                    for event in calendar_events:
                        date = event['date']
                        time_parts = event['time'].split(':')
                        hour = int(time_parts[0])
                        
                        if date not in busy_slots:
                            busy_slots[date] = []
                        
                        # Blockiere 2 Stunden für jedes Event
                        busy_slots[date].extend([hour, hour + 1])
                    
                    # Datumsauswahl für die Verschiebung
                    new_date = st.date_input("Neues Datum", 
                                            datetime.strptime(task['date'], "%Y-%m-%d").date(),
                                            key=f"new_date_{task['id']}")
                    
                    # Verfügbare Zeitslots für das ausgewählte Datum
                    date_str = new_date.strftime("%Y-%m-%d")
                    work_hours = list(range(8, 20))  # 8:00 - 20:00
                    
                    # Freie Zeitslots finden
                    available_hours = [h for h in work_hours[:-1] if
                                      date_str not in busy_slots or
                                      (h not in busy_slots.get(date_str, []) and
                                       h+1 not in busy_slots.get(date_str, []))]
                    
                    # Formatiere die Stunden für die Anzeige
                    time_options = [f"{h:02d}:00" for h in available_hours]
                    
                    # Wenn keine freien Slots verfügbar sind, alle Zeiten anzeigen
                    if not time_options:
                        time_options = [f"{h:02d}:00" for h in work_hours[:-1]]
                    
                    # Startzeit auswählen
                    new_start_time = st.selectbox("Neue Startzeit", 
                                                time_options,
                                                index=time_options.index(task['start_time']) if task['start_time'] in time_options else 0,
                                                key=f"new_start_{task['id']}")
                    
                    # Endzeit berechnen (2 Stunden nach Startzeit)
                    start_hour = int(new_start_time.split(':')[0])
                    new_end_time = f"{start_hour+2:02d}:00"
                    
                    st.write(f"Neue Endzeit: {new_end_time}")
                    
                    # Button zum Speichern der Änderungen
                    if st.button("Termin verschieben", key=f"move_{task['id']}"):
                        # Daten für die Aktualisierung vorbereiten
                        update_data = {
                            'date': date_str,
                            'start_time': new_start_time,
                            'end_time': new_end_time
                        }
                        
                        # Aktualisiere die Aufgabe in der Datenbank
                        if update_study_task(task['id'], update_data):
                            st.success("Termin erfolgreich verschoben!")
                            st.rerun()
                        else:
                            st.error("Fehler beim Verschieben des Termins.")
            
            with col2:
                # Checkbox zum Abhaken
                completed = st.checkbox("Erledigt", value=task['completed'], key=f"task_{task['id']}")
                
                if completed != task['completed']:
                    # Status in der Datenbank aktualisieren
                    if update_study_task_status(task['id'], completed):
                        st.success("Status aktualisiert")
                        st.rerun()
            
            with col3:
                # Button zum Löschen
                if st.button("Löschen", key=f"delete_{task['id']}"):
                    # Lösche die Aufgabe aus der Datenbank
                    if delete_study_task(task['id']):
                        st.success(f"Aufgabe gelöscht")
                        st.rerun()
                    else:
                        st.error("Fehler beim Löschen der Aufgabe")
    
    # Vergangene Aufgaben anzeigen
    if past_tasks:
        with st.expander("Vergangene Lernaufgaben"):
            for task in past_tasks:
                status = "✅" if task['completed'] else "❌"
                st.write(f"{status} **{task['date']}** | {task['start_time']} - {task['end_time']} | {task['course_code']} - {task['topic']}")


def save_study_task(user_id, session):
    """Speichert eine Lernaufgabe in der Datenbank"""
    # Hier würde die Implementierung zur Speicherung in einer neuen Tabelle folgen
    # Für jetzt simulieren wir dies mit Session State
    if 'study_tasks' not in st.session_state:
        st.session_state.study_tasks = []
    
    task_id = len(st.session_state.study_tasks) + 1
    
    task = {
        'id': task_id,
        'user_id': user_id,
        'course_id': session['course_id'],
        'course_title': session['course_title'],
        'course_code': session['course_code'],
        'date': session['date'],
        'start_time': session['start_time'],
        'end_time': session['end_time'],
        'topic': session['content']['topic'],
        'methods': session['content']['methods'],
        'completed': False
    }
    
    st.session_state.study_tasks.append(task)

def display_study_tasks(user_id):
    """Zeigt die Lernaufgaben des Nutzers an und ermöglicht das Abhaken, Verschieben und Löschen"""
    st.subheader("Meine Lernaufgaben")
    
    # Lade Aufgaben aus der Datenbank
    user_tasks = get_study_tasks(user_id)
    
    if not user_tasks:
        st.info("Du hast noch keine Lernaufgaben. Erstelle einen Lernplan, um loszulegen!")
        return
    
    # Nach Datum sortieren und in vergangene/zukünftige aufteilen
    today = datetime.now().date()
    
    upcoming_tasks = []
    past_tasks = []
    
    for task in user_tasks:
        task_date = datetime.strptime(task['date'], "%Y-%m-%d").date()
        if task_date >= today:
            upcoming_tasks.append(task)
        else:
            past_tasks.append(task)
    
    # Sortiere nach Datum und Zeit
    upcoming_tasks.sort(key=lambda x: (x['date'], x['start_time']))
    past_tasks.sort(key=lambda x: (x['date'], x['start_time']), reverse=True)
    
    # Zukünftige Aufgaben anzeigen
    if upcoming_tasks:
        st.write("### Anstehende Lernaufgaben")
        for task in upcoming_tasks:
            col1, col2, col3 = st.columns([4, 1, 1])
            
            with col1:
                status = "✅" if task['completed'] else "⏳"
                expander_label = f"{status} {task['date']} | {task['start_time']} - {task['end_time']} | {task['course_code']}"
                
                with st.expander(expander_label):
                    st.write(f"**Kurs:** {task['course_title']}")
                    st.write(f"**Thema:** {task['topic']}")
                    st.write("**Empfohlene Lernmethoden:**")
                    for method in task['methods']:
                        st.write(f"- {method}")
                    
                    # Verschieben-Funktion innerhalb des Expanders
                    st.write("---")
                    st.write("**Termin verschieben:**")
                    
                    # Verfügbare Termine abrufen (freie Zeiten im Kalender)
                    calendar_events = get_calendar_events(user_id)
                    busy_slots = {}
                    
                    for event in calendar_events:
                        date = event['date']
                        time_parts = event['time'].split(':')
                        hour = int(time_parts[0])
                        
                        if date not in busy_slots:
                            busy_slots[date] = []
                        
                        # Blockiere 2 Stunden für jedes Event
                        busy_slots[date].extend([hour, hour + 1])
                    
                    # Datumsauswahl für die Verschiebung
                    new_date = st.date_input("Neues Datum", 
                                            datetime.strptime(task['date'], "%Y-%m-%d").date(),
                                            key=f"new_date_{task['id']}")
                    
                    # Verfügbare Zeitslots für das ausgewählte Datum
                    date_str = new_date.strftime("%Y-%m-%d")
                    work_hours = list(range(8, 20))  # 8:00 - 20:00
                    
                    # Freie Zeitslots finden
                    available_hours = [h for h in work_hours[:-1] if
                                      date_str not in busy_slots or
                                      (h not in busy_slots.get(date_str, []) and
                                       h+1 not in busy_slots.get(date_str, []))]
                    
                    # Formatiere die Stunden für die Anzeige
                    time_options = [f"{h:02d}:00" for h in available_hours]
                    
                    # Wenn keine freien Slots verfügbar sind, alle Zeiten anzeigen
                    if not time_options:
                        time_options = [f"{h:02d}:00" for h in work_hours[:-1]]
                    
                    # Startzeit auswählen
                    new_start_time = st.selectbox("Neue Startzeit", 
                                                time_options,
                                                index=time_options.index(task['start_time']) if task['start_time'] in time_options else 0,
                                                key=f"new_start_{task['id']}")
                    
                    # Endzeit berechnen (2 Stunden nach Startzeit)
                    start_hour = int(new_start_time.split(':')[0])
                    new_end_time = f"{start_hour+2:02d}:00"
                    
                    st.write(f"Neue Endzeit: {new_end_time}")
                    
                    # Button zum Speichern der Änderungen
                    if st.button("Termin verschieben", key=f"move_{task['id']}"):
                        # Daten für die Aktualisierung vorbereiten
                        update_data = {
                            'date': date_str,
                            'start_time': new_start_time,
                            'end_time': new_end_time
                        }
                        
                        # Aktualisiere die Aufgabe in der Datenbank
                        if update_study_task(task['id'], update_data):
                            st.success("Termin erfolgreich verschoben!")
                            st.rerun()
                        else:
                            st.error("Fehler beim Verschieben des Termins.")
            
            with col2:
                # Checkbox zum Abhaken
                completed = st.checkbox("Erledigt", value=task['completed'], key=f"task_{task['id']}")
                
                if completed != task['completed']:
                    # Status in der Datenbank aktualisieren
                    if update_study_task_status(task['id'], completed):
                        st.success("Status aktualisiert")
                        st.rerun()
            
            with col3:
                # Button zum Löschen
                if st.button("Löschen", key=f"delete_{task['id']}"):
                    # Lösche die Aufgabe aus der Datenbank
                    if delete_study_task(task['id']):
                        st.success(f"Aufgabe gelöscht")
                        st.rerun()
                    else:
                        st.error("Fehler beim Löschen der Aufgabe")
    
    # Vergangene Aufgaben anzeigen
    if past_tasks:
        with st.expander("Vergangene Lernaufgaben"):
            for task in past_tasks:
                status = "✅" if task['completed'] else "❌"
                st.write(f"{status} **{task['date']}** | {task['start_time']} - {task['end_time']} | {task['course_code']} - {task['topic']}")


def get_course_content(course_code):
    """
    Liest die Inhalte aus der Fächerzusammenfassung für einen bestimmten Kurs.
    """
    try:
        # In einer vollständigen Implementierung würden wir hier die Fächerzusammenfassung.docx parsen
        # und die relevanten Inhalte für den angegebenen Kurs extrahieren
        
        # Für jetzt simulieren wir dies mit einigen Beispielinhalten
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
        
        # Versuche, den Kurs anhand des Codes zu identifizieren
        for course_name, topics in course_contents.items():
            if course_name.lower() in course_code.lower():
                return topics
        
        # Wenn kein passender Kurs gefunden wurde, gib eine allgemeine Liste zurück
        return ["Kapitel 1", "Kapitel 2", "Kapitel 3", "Kapitel 4", "Kapitel 5"]
    
    except Exception as e:
        print(f"Fehler beim Lesen der Kursinhalte: {e}")
        return ["Kapitel 1", "Kapitel 2", "Kapitel 3", "Kapitel 4", "Kapitel 5"]

def generate_study_content(course, learning_type):
    """
    Generiert Lerninhalt basierend auf dem Kurs und dem Lerntyp.
    Verwendet die Fächerzusammenfassung für relevante Inhalte.
    """
    # Hole die Kursinhalte aus der Fächerzusammenfassung
    course_topics = get_course_content(course['code'])
    
    # Wähle ein zufälliges Thema aus
    topic = random.choice(course_topics) if course_topics else f"Kapitel {random.randint(1, 10)}"
    
    # Lernmethoden basierend auf dem Lerntyp
    if learning_type == "Visual":
        methods = [
            f"Erstelle Mind-Maps zu '{topic}'",
            f"Arbeite mit farbigen Notizen und Markierungen zu '{topic}'",
            f"Visualisiere die Prozesse in '{topic}' durch Diagramme",
            f"Suche Videos und visuelle Materialien zu '{topic}'",
            f"Erstelle Infografiken zu den Schlüsselkonzepten in '{topic}'"
        ]
    elif learning_type == "Auditory":
        methods = [
            f"Nimm deine Zusammenfassung von '{topic}' auf und höre sie mehrmals",
            f"Diskutiere '{topic}' mit Kommilitonen in einer Studiengruppe",
            f"Erkläre die Konzepte von '{topic}' laut, als würdest du sie jemandem beibringen",
            f"Suche Podcasts oder Vorlesungsaufzeichnungen zu '{topic}'",
            f"Führe ein Selbstgespräch über '{topic}' und stelle dir selbst Fragen"
        ]
    elif learning_type == "Reading/Writing":
        methods = [
            f"Erstelle eine detaillierte Zusammenfassung von '{topic}'",
            f"Schreibe Karteikarten zu den Schlüsselkonzepten in '{topic}'",
            f"Lies die empfohlene Literatur zu '{topic}' und mache Notizen",
            f"Formuliere Antworten auf mögliche Prüfungsfragen zu '{topic}'",
            f"Erstelle ein Glossar der wichtigsten Begriffe in '{topic}'"
        ]
    elif learning_type == "Kinesthetic":
        methods = [
            f"Löse praktische Übungen und Fallstudien zu '{topic}'",
            f"Wende die Konzepte von '{topic}' auf reale Situationen an",
            f"Erstelle ein physisches Modell oder eine Demonstration zu '{topic}'",
            f"Bewege dich beim Lernen von '{topic}' (z.B. beim Gehen wiederholen)",
            f"Führe Rollenspiele oder Simulationen zu '{topic}' durch"
        ]
    else:
        methods = [
            f"Wiederhole die Vorlesungsnotizen zu '{topic}'",
            f"Löse Übungsaufgaben zu '{topic}'",
            f"Diskutiere '{topic}' mit Kommilitonen",
            f"Erstelle eine Zusammenfassung von '{topic}'",
            f"Bereite Fragen zu '{topic}' vor und beantworte sie"
        ]
    
    # Wähle 2-3 Methoden aus
    selected_methods = random.sample(methods, min(3, len(methods)))
    
    return {
        'topic': topic,
        'methods': selected_methods
    }

def generate_study_content(course, learning_type):
    """
    Generiert Lerninhalt basierend auf dem Kurs und dem Lerntyp.
    Verwendet die Fächerzusammenfassung für relevante Inhalte.
    """
    # Hole die Kursinhalte aus der Fächerzusammenfassung
    course_topics = get_course_content(course['code'])
    
    # Wähle ein zufälliges Thema aus
    topic = random.choice(course_topics) if course_topics else f"Kapitel {random.randint(1, 10)}"
    
    # Lernmethoden basierend auf dem Lerntyp
    if learning_type == "Visual":
        methods = [
            f"Erstelle Mind-Maps zu '{topic}'",
            f"Arbeite mit farbigen Notizen und Markierungen zu '{topic}'",
            f"Visualisiere die Prozesse in '{topic}' durch Diagramme",
            f"Suche Videos und visuelle Materialien zu '{topic}'",
            f"Erstelle Infografiken zu den Schlüsselkonzepten in '{topic}'"
        ]
    elif learning_type == "Auditory":
        methods = [
            f"Nimm deine Zusammenfassung von '{topic}' auf und höre sie mehrmals",
            f"Diskutiere '{topic}' mit Kommilitonen in einer Studiengruppe",
            f"Erkläre die Konzepte von '{topic}' laut, als würdest du sie jemandem beibringen",
            f"Suche Podcasts oder Vorlesungsaufzeichnungen zu '{topic}'",
            f"Führe ein Selbstgespräch über '{topic}' und stelle dir selbst Fragen"
        ]
    elif learning_type == "Reading/Writing":
        methods = [
            f"Erstelle eine detaillierte Zusammenfassung von '{topic}'",
            f"Schreibe Karteikarten zu den Schlüsselkonzepten in '{topic}'",
            f"Lies die empfohlene Literatur zu '{topic}' und mache Notizen",
            f"Formuliere Antworten auf mögliche Prüfungsfragen zu '{topic}'",
            f"Erstelle ein Glossar der wichtigsten Begriffe in '{topic}'"
        ]
    elif learning_type == "Kinesthetic":
        methods = [
            f"Löse praktische Übungen und Fallstudien zu '{topic}'",
            f"Wende die Konzepte von '{topic}' auf reale Situationen an",
            f"Erstelle ein physisches Modell oder eine Demonstration zu '{topic}'",
            f"Bewege dich beim Lernen von '{topic}' (z.B. beim Gehen wiederholen)",
            f"Führe Rollenspiele oder Simulationen zu '{topic}' durch"
        ]
    else:
        methods = [
            f"Wiederhole die Vorlesungsnotizen zu '{topic}'",
            f"Löse Übungsaufgaben zu '{topic}'",
            f"Diskutiere '{topic}' mit Kommilitonen",
            f"Erstelle eine Zusammenfassung von '{topic}'",
            f"Bereite Fragen zu '{topic}' vor und beantworte sie"
        ]
    
    # Wähle 2-3 Methoden aus
    selected_methods = random.sample(methods, min(3, len(methods)))
    
    return {
        'topic': topic,
        'methods': selected_methods
    }

def display_study_plan(study_plan):
    """Zeigt den generierten Lernplan an"""
    for session in study_plan:
        with st.expander(f"{session['date']} | {session['start_time']} - {session['end_time']} | {session['course_code']}"):
            st.write(f"**Kurs:** {session['course_title']}")
            st.write(f"**Thema:** {session['content']['topic']}")
            st.write("**Empfohlene Lernmethoden:**")
            for method in session['content']['methods']:
                st.write(f"- {method}")

def save_study_plan_to_calendar(user_id, study_plan):
    """Speichert den Lernplan im Kalender und als Lernaufgaben"""
    success_count = 0
    print("save_study_plan_to_calendar")
    
    for session in study_plan:
        try:
            # Speichere im Kalender
            event_data = {
                'title': f"Lernen: {session['course_code']}",
                'date': session['date'],
                'time': session['start_time'],
                'type': "Study Session",
                'color': "#ccffcc",  # Hellgrün
                'user_id': user_id
            }
            
            # Event im Kalender speichern
            event_id = save_calendar_event(user_id, event_data)
            success_count += 1
            
            # Versuche, auch als Lernaufgabe zu speichern (optional)
            try:
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
                
                # Hier die korrekte Datenbankfunktion aus database_manager verwenden
                from database_manager import save_study_task as db_save_study_task
                task_id = db_save_study_task(user_id, task_data)
            except Exception as e:
                print(f"Fehler beim Speichern der Lernaufgabe: {e}")
                # Ignoriere Fehler beim Speichern der Lernaufgaben, 
                # da die Kalendereinträge bereits erfolgreich gespeichert wurden
        except Exception as e:
            print(f"Fehler beim Speichern des Kalendereintrags: {e}")
    
    return success_count > 0


def display_study_tasks(user_id):
    """Zeigt die Lernaufgaben des Nutzers an und ermöglicht das Abhaken"""
    st.subheader("Meine Lernaufgaben")
    
    # Lade Aufgaben aus der Datenbank
    user_tasks = get_study_tasks(user_id)
    
    if not user_tasks:
        st.info("Du hast noch keine Lernaufgaben. Erstelle einen Lernplan, um loszulegen!")
        return
    
    # Nach Datum sortieren und in vergangene/zukünftige aufteilen
    today = datetime.now().date()
    
    upcoming_tasks = []
    past_tasks = []
    
    for task in user_tasks:
        task_date = datetime.strptime(task['date'], "%Y-%m-%d").date()
        if task_date >= today:
            upcoming_tasks.append(task)
        else:
            past_tasks.append(task)
    
    # Sortiere nach Datum und Zeit
    upcoming_tasks.sort(key=lambda x: (x['date'], x['start_time']))
    past_tasks.sort(key=lambda x: (x['date'], x['start_time']), reverse=True)
    
    # Zukünftige Aufgaben anzeigen
    if upcoming_tasks:
        st.write("### Anstehende Lernaufgaben")
        for task in upcoming_tasks:
            col1, col2 = st.columns([5, 1])
            
            with col1:
                status = "✅" if task['completed'] else "⏳"
                expander_label = f"{status} {task['date']} | {task['start_time']} - {task['end_time']} | {task['course_code']}"
                
                with st.expander(expander_label):
                    st.write(f"**Kurs:** {task['course_title']}")
                    st.write(f"**Thema:** {task['topic']}")
                    st.write("**Empfohlene Lernmethoden:**")
                    for method in task['methods']:
                        st.write(f"- {method}")
            
            with col2:
                # Checkbox zum Abhaken
                completed = st.checkbox("Erledigt", value=task['completed'], key=f"task_{task['id']}")
                
                if completed != task['completed']:
                    # Status in der Datenbank aktualisieren
                    if update_study_task_status(task['id'], completed):
                        st.success("Status aktualisiert")
                        st.rerun()
    
    # Vergangene Aufgaben anzeigen
    if past_tasks:
        with st.expander("Vergangene Lernaufgaben"):
            for task in past_tasks:
                status = "✅" if task['completed'] else "❌"
                st.write(f"{status} **{task['date']}** | {task['start_time']} - {task['end_time']} | {task['course_code']} - {task['topic']}")


