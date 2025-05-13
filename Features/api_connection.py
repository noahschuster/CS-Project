import streamlit as st
import pandas as pd
import requests
import json
from database_manager import SessionLocal, Course, UserCourse, CourseSchedule  

import os
from datetime import datetime

# HSG API Konfiguration (Schlüssel usw. sind in der .env)
API_APPLICATION_ID = "587acf1c-24d0-4801-afda-c98f081c4678"
API_VERSION = "1"
API_BASE_URL = "https://integration.preprod.unisg.ch"
LANGUAGE_MAP = {2: "German", 21: "English"}

#api request an hsg server
def api_request(endpoint, headers=None, timeout=10):
    if headers is None:
        headers = {
            "X-ApplicationId": API_APPLICATION_ID,
            "API-Version": API_VERSION,
            "X-RequestedLanguage": "de"
        }
    
    response = requests.get(f"{API_BASE_URL}{endpoint}", headers=headers, timeout=timeout)
    return response.json()

# Aktuellen Term rausfinden mit api request Funktion
def fetch_current_term():
    return api_request("/eventapi/timeLines/currentTerm")

# Aufruf der api request Funktion um die Kurse des aktuellen Semesters abzurufen
def fetch_courses_for_term(term_id):
    return api_request(f"/eventapi/Events/byTerm/{term_id}")

# Aufruf der api request Funktion um Zeitplan für Kurse abzurufen
def fetch_course_schedule(term_id, event_id):
    return api_request(f"/eventapi/EventDates/byEvent/{event_id}")

# Sync die Kurse mit dem integrierten Kalender
def sync_course_schedule_to_calendar(user_id):
    from database_manager import get_calendar_events, save_calendar_event, CourseSchedule
    
    # Aktuelle Kurse des Benutzers abrufen
    user_courses = get_user_courses(user_id)
    if not user_courses:
        return 0
    
    events_added = 0
    
    # Bestehende Kalendereinträge abrufen, um Duplikate zu vermeiden
    existing_events = get_calendar_events(user_id)
    existing_event_titles = set()
    if existing_events:
        for event in existing_events:
            if isinstance(event, dict) and 'title' in event and 'date' in event and 'time' in event:
                event_key = f"{event['title']}_{event['date']}_{event['time']}"
                existing_event_titles.add(event_key)
    
    session = SessionLocal()
    try:
        for course in user_courses:
            course_id = course['course_id']
            course_title = course['title']
            course_code = course['meeting_code']
            
            # Gespeicherte Kurstermine abrufen statt API-Aufruf
            course_dates = session.query(CourseSchedule).filter(
                CourseSchedule.course_id == course_id
            ).all()
            
            if not course_dates:
                continue
            
            for date in course_dates:
                # Ereignistitel erstellen
                event_title = f"{course_code} - {course_title}"
                
                # Prüfen, ob der Termin bereits existiert
                event_key = f"{event_title}_{date.start_date}_{date.start_time}"
                if event_key in existing_event_titles:
                    continue
                
                # Kalenderereignis erstellen
                event_data = {
                    'title': event_title,
                    'date': date.start_date,
                    'time': date.start_time,
                    'end_time': date.end_time,
                    'type': "Vorlesung",
                    'color': "#ccccff",
                    'user_id': user_id,
                    'description': f"Raum: {date.room}"
                }
                
                # Ereignis zum Kalender hinzufügen
                event_id = save_calendar_event(user_id, event_data)
                if event_id:
                    events_added += 1
        
        return events_added
    except Exception as e:
        st.error(f"Fehler beim Synchronisieren der Kurstermine: {e}")
        return 0
    finally:
        session.close()

# alle kurse die der Nutzer ausgewählt hat laden
def get_user_courses(user_id):
    session = SessionLocal()
    # Auswählen der Kurse des Benutzers
    user_courses = session.query(
        Course
    ).join(
        UserCourse, Course.course_id == UserCourse.course_id
    ).filter(
        UserCourse.user_id == user_id
    ).all()
    
    # in Liste umwandeln
    courses_list = []
    for course in user_courses:
        courses_list.append({
            'course_id': course.course_id,
            'meeting_code': course.meeting_code,
            'title': course.title,
            'description': course.description,
            'language_id': course.language_id,
            'term_name': course.term_name,
            'link_course_info': course.link_course_info
        })
    
    return courses_list

#Abrufen der Kurse mit den oben definierten Funktionen aus der HSG API. Bereich "Admin" in der Anwendung
def fetch_and_store_courses():
    status = st.empty()
    status.info("Abruf von Kursdaten aus der HSG API...")
    
    current_term = fetch_current_term()
    
    term_id = current_term['id']
    term_name = current_term['shortName']
    term_description = current_term['description']
    
    status.info(f"Abruf von Kursen für  {term_description}...")
    courses_data = fetch_courses_for_term(term_id)
    
    session = SessionLocal()
    try:
        courses_added = 0
        schedules_added = 0
        
        # Erstelle einen Fortschrittsbalken
        progress_bar = st.progress(0)
        
        for i, course in enumerate(courses_data):
            
            # Aktualisiere den Fortschrittsbalken
            progress = (i + 1) / len(courses_data)
            progress_bar.progress(progress)
            
            # Aktualisiere den Status
            if i % 50 == 0 or i == len(courses_data) - 1:
                status.info(f"Verarbeite Kurs {i+1}/{len(courses_data)}: {course.get('title', '')}")
            
            course_id = str(course.get('id', ''))
            existing_course = session.query(Course).filter(Course.course_id == course_id).first()
            
            course_data = {
                'course_id': course_id,
                'meeting_code': course.get('meetingCode', ''),
                'title': course.get('title', ''),
                'description': course.get('remark', ''),
                'language_id': course.get('languageId', 0),
                'max_credits': json.dumps(course.get('maxCredits', [])),
                'term_id': term_id,
                'term_name': term_name,
                'term_description': term_description,
                'link_course_info': course.get('linkCourseInformationSheet', '')
            }
            
            if existing_course:
                for key, value in course_data.items():
                    setattr(existing_course, key, value)
            else:
                session.add(Course(**course_data))
            
            # Hole und speichere Kurszeiten direkt für jeden Kurs
            course_dates = fetch_course_schedule(term_id, course_id)
            if course_dates:
                store_course_schedule(course_id, course_dates)
                schedules_added += 1
            
            # Commit alle 50 Kurse, um den Speicher zu entlasten
            if i % 50 == 0:
                session.commit()
            
            courses_added += 1
        
        # Finaler Commit
        session.commit()
        
        # Entferne den Fortschrittsbalken und zeige Erfolgsmeldung
        progress_bar.empty()
        status.success(f"Erfolgreich importierte {courses_added} Kurse mit {schedules_added} Zeitplänen für {term_description}")
        
        # Lade die Seite neu, um die Änderungen anzuzeigen
        st.rerun()
        
        return True
    except Exception as e:
        session.rollback()
        st.error(f"Fehler beim Speichern von Kursen: {str(e)}")
        return False
    finally:
        session.close()

# Kurszeiten in Datenbank speichern
def store_course_schedule(course_id, course_dates):
    if not course_dates:
        st.warning(f"Keine Kurstermine für Kurs {course_id} gefunden.")
        return
        
    session = SessionLocal()
    try:
        # Lösche vorhandene Termine
        session.query(CourseSchedule).filter(CourseSchedule.course_id == course_id).delete()
        
        # Zähle erfolgreich gespeicherte Termine
        saved_dates = 0
        
        # Speichere neue Termine
        for date in course_dates:
            try:
                # Daten aus der API extrahieren
                start_datetime = date.get('startTime')
                end_datetime = date.get('endTime')
                room = date.get('location', 'Kein Raum angegeben')
                
                if not start_datetime or not end_datetime:
                    continue
                
                # Datum und Zeit formatieren
                start_date = start_datetime.split('T')[0]  # YYYY-MM-DD
                start_time = start_datetime.split('T')[1][:5]  # HH:MM
                end_time = end_datetime.split('T')[1][:5]  # HH:MM
                
                # Speichere den Termin
                schedule_entry = CourseSchedule(
                    course_id=course_id,
                    start_date=start_date,
                    start_time=start_time,
                    end_time=end_time,
                    room=room
                )
                session.add(schedule_entry)
                saved_dates += 1
            except Exception as e:
                st.error(f"Fehler bei der Verarbeitung des Kurstermins: {e}")
                continue
        
        if saved_dates > 0:
            session.commit()
            st.success(f"{saved_dates} Kurstermine für Kurs {course_id} gespeichert.")
        else:
            st.warning(f"Keine Kurstermine für Kurs {course_id} gespeichert.")
    except Exception as e:
        session.rollback()
        st.error(f"Fehler beim Speichern der Kurstermine: {str(e)}")
    finally:
        session.close()

# Kursauswahl des Nutzers speichern
def save_user_course_selections(user_id, course_ids):
    session = SessionLocal()
    session.query(UserCourse).filter(UserCourse.user_id == user_id).delete()
    
    for course_id in course_ids:
        session.add(UserCourse(user_id=user_id, course_id=course_id))
    
    session.commit()
    return True

# Streamlit Frontend Implementierung
def display_hsg_api_page(user_id):
    st.title("HSG Kurse")
    
    user_id = st.session_state.get('user_id')
    username = st.session_state.get('username')
    
    st.write(f"Grüezi {username}! Hier können Sie Ihre Kurse an der Universität St. Gallen verwalten.")
    
    session = SessionLocal()
    try:
        course_count = session.query(Course).count()
        
        with st.expander("Verwaltung: Kursdatenbank aktualisieren"):
            if course_count > 0:
                st.info(f"Aktuell enthält die Datenbank {course_count} Kurs.")
            else:
                st.warning("Noch keine Kurse in der Datenbank.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Neueste Kurse von HSG API abrufen"):
                    fetch_and_store_courses()
        
        if course_count > 0:
            tab1, tab2 = st.tabs(["Kurse auswählen", "Mein Stundenplan"])
            
            with tab1:
                all_courses = session.query(
                    Course.course_id, Course.meeting_code, Course.title, 
                    Course.description, Course.language_id
                ).all()
                
                user_course_ids = [uc.course_id for uc in session.query(
                    UserCourse.course_id).filter(UserCourse.user_id == user_id).all()
                ]
                
                df_courses = pd.DataFrame([{
                    'course_id': c.course_id,
                    'meeting_code': c.meeting_code,
                    'title': c.title,
                    'description': c.description,
                    'language_id': c.language_id,
                    'selected': 1 if c.course_id in user_course_ids else 0
                } for c in all_courses])
                
                search_term = st.text_input("Suche nach Kursen nach Titel oder Code:", key="search_courses")
                
                filtered_df = df_courses
                if search_term and not df_courses.empty:
                    filtered_df = df_courses[
                        df_courses['title'].str.contains(search_term, case=False) | 
                        df_courses['meeting_code'].str.contains(search_term, case=False)
                    ]
                
                languages = sorted(filtered_df['language_id'].unique()) if not filtered_df.empty else []
                language_options = ["All"] + [LANGUAGE_MAP.get(lang, f"Language {lang}") for lang in languages]
                selected_language = st.selectbox("Nach Sprache filtern:", language_options)
                
                if selected_language != "All" and not filtered_df.empty:
                    lang_id = [k for k, v in LANGUAGE_MAP.items() if v == selected_language][0]
                    filtered_df = filtered_df[filtered_df['language_id'] == lang_id]
                
                st.write(f"Zeige {len(filtered_df)} Kurse")
                
                with st.form("course_selection_form"):
                    # Container für die scrollbare Liste erstellen
                    course_container = st.container()
                    
                    # Speicherplatz für den Button reservieren (außerhalb des scrollbaren Bereichs)
                    submit_button_placeholder = st.empty()
                    
                    # Scrollbaren Bereich definieren
                    with course_container:
                        st.markdown("""
                        <style>
                        [data-testid="stVerticalBlock"] > div:nth-child(1) {
                            max-height: 400px;
                            overflow-y: auto;
                        }
                        </style>
                        """, unsafe_allow_html=True)
                        
                        selected_courses = []
                        for _, row in filtered_df.iterrows():
                            course_id = row['course_id']
                            title = row['title']
                            code = row['meeting_code']
                            lang = LANGUAGE_MAP.get(row['language_id'], f"Language {row['language_id']}")
                            
                            is_selected = st.checkbox(
                                f"{code} - {title} ({lang})",
                                value=(row['selected'] == 1),
                                key=f"course_{course_id}"
                            )
                            
                            if is_selected:
                                selected_courses.append(course_id)
                    
                    # Button außerhalb des scrollbaren Bereichs platzieren
                    if submit_button_placeholder.form_submit_button("Kursauswahl speichern"):
                        if save_user_course_selections(user_id, selected_courses):
                            st.success("Ihre Kursauswahl wurde gespeichert!!")
                            st.rerun()
            
            with tab2:
                user_courses = session.query(
                    Course.course_id, Course.meeting_code, Course.title, Course.description, 
                    Course.language_id, Course.link_course_info
                ).join(
                    UserCourse, Course.course_id == UserCourse.course_id
                ).filter(
                    UserCourse.user_id == user_id
                ).all()
                
                if len(user_courses) == 0:
                    st.info("Du hast noch keine Kurse ausgewählt. Gehe zum 'Kurse auswählen'-Tab, um Kurse hinzuzufügen.")
                else:
                    st.write(f"Du hast {len(user_courses)} Kurse ausgewählt:")
                    
                    # Button zum Synchronisieren der Kurstermine mit dem Kalender
                    if st.button("Kurszeiten mit Kalender synchronisieren"):
                        with st.spinner("Synchronisiere Kurszeiten mit deinem Kalender..."):
                            events_added = sync_course_schedule_to_calendar(user_id)
                            if events_added > 0:
                                st.success(f"{events_added} Kurstermine wurden zu deinem Kalender hinzugefügt!")
                            else:
                                st.warning("Es wurden keine Kurstermine gefunden oder sie sind bereits in deinem Kalender.")
                    
                    for course in user_courses:
                        with st.expander(f"{course.meeting_code} - {course.title}"):
                            st.write(f"**Sprache:** {LANGUAGE_MAP.get(course.language_id, 'Unbekannt')}")
                            if course.description:
                                st.write(f"**Beschreibung:** {course.description}")
                            if course.link_course_info:
                                st.markdown(f"[Kursmerkblatt]({course.link_course_info})")

    
    except Exception as e:
        st.error(f"Fehler beim Zugriff auf die Datenbank: {str(e)}")
    finally:
        session.close()

if __name__ == "__main__":
    display_hsg_api_page()
