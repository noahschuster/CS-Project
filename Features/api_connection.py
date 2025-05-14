import streamlit as st
import pandas as pd
import requests
import json
from database_manager import SessionLocal, Course, UserCourse, CourseSchedule, Term, Language

# HSG API Konfiguration
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
    from database_manager import get_calendar_events, save_calendar_event # CourseSchedule already imported
    
    user_courses = get_user_courses(user_id) 
    if not user_courses:
        return 0
    
    events_added = 0
    
    existing_events = get_calendar_events(user_id)
    existing_event_titles = set()
    if existing_events:
        for event in existing_events:
            if isinstance(event, dict) and 'title' in event and 'date' in event and 'time' in event:
                event_key = f"{event['title']}_{event['date']}_{event['time']}"
                existing_event_titles.add(event_key)
    
    db_session = SessionLocal()
    try:
        for course_info in user_courses: 
            course_id = course_info['course_id']
            course_title = course_info['title']
            course_code = course_info['meeting_code']
            
            course_dates = db_session.query(CourseSchedule).filter(
                CourseSchedule.course_id == course_id
            ).all()
            
            if not course_dates:
                continue
            
            for date_entry in course_dates:
                event_title = f"{course_code} - {course_title}"
                event_key = f"{event_title}_{date_entry.start_date}_{date_entry.start_time}"
                if event_key in existing_event_titles:
                    continue
                
                event_data = {
                    'title': event_title,
                    'date': date_entry.start_date,
                    'time': date_entry.start_time,
                    'end_time': date_entry.end_time,
                    'type': "Vorlesung",
                    'color': "#ccccff",
                    'user_id': user_id,
                    'description': f"Raum: {date_entry.room}"
                }
                
                event_id = save_calendar_event(user_id, event_data)
                if event_id:
                    events_added += 1
        
        return events_added
    except Exception as e:
        st.error(f"Fehler beim Synchronisieren der Kurstermine: {e}")
        return 0
    finally:
        db_session.close()

def get_user_courses(user_id):
    db_session = SessionLocal()
    try:
        user_course_objects = db_session.query(
            Course
        ).join(
            UserCourse, Course.course_id == UserCourse.course_id
        ).filter(
            UserCourse.user_id == user_id
        ).all()
        
        courses_list = []
        for course_obj in user_course_objects:
            term_name_value = "N/A"
            if course_obj.term_id:
                term_entry = db_session.query(Term).filter(Term.term_id == course_obj.term_id).first()
                if term_entry:
                    term_name_value = term_entry.term_name
            
            courses_list.append({
                'course_id': course_obj.course_id,
                'meeting_code': course_obj.meeting_code,
                'title': course_obj.title,
                'description': course_obj.description, 
                'language_id': course_obj.language_id,
                'term_id': course_obj.term_id, 
                'term_name': term_name_value, 
                'link_course_info': course_obj.link_course_info
            })
        
        return courses_list
    finally:
        db_session.close()

def fetch_and_store_courses():
    status = st.empty()
    status.info("Abruf von Kursdaten aus der HSG API...")
    
    current_term_api_data = fetch_current_term()
    
    term_id_from_api = current_term_api_data['id']
    term_name_from_api = current_term_api_data['shortName']
    term_description_from_api = current_term_api_data['description']
    
    db_session = SessionLocal()
    try:
        term_db_entry = db_session.query(Term).filter(Term.term_id == term_id_from_api).first()
        if not term_db_entry:
            new_term = Term(term_id=term_id_from_api, term_name=term_name_from_api, term_description=term_description_from_api)
            db_session.add(new_term)
            status.info(f"Neuer Term '{term_name_from_api}' zur Datenbank hinzugefügt.")
        else:
            term_db_entry.term_name = term_name_from_api
            term_db_entry.term_description = term_description_from_api
            status.info(f"Term '{term_name_from_api}' in der Datenbank aktualisiert.")

        for lang_id_map, lang_name_map in LANGUAGE_MAP.items():
            lang_db_entry = db_session.query(Language).filter(Language.id == lang_id_map).first()
            if not lang_db_entry:
                lang_code_val = "DE" if lang_name_map == "German" else "EN" if lang_name_map == "English" else lang_name_map[:2].upper()
                new_lang_entry = Language(id=lang_id_map, language_name=lang_name_map, language_code=lang_code_val)
                db_session.add(new_lang_entry)
                status.info(f"Neue Sprache '{lang_name_map}' zur Datenbank hinzugefügt.")

        status.info(f"Abruf von Kursen für {term_description_from_api} ({term_name_from_api})...")
        courses_api_data = fetch_courses_for_term(term_id_from_api)
        
        courses_added_count = 0
        schedules_added_count = 0
        
        progress_bar = st.progress(0)
        
        for i, course_api_item in enumerate(courses_api_data):
            progress = (i + 1) / len(courses_api_data)
            progress_bar.progress(progress)
            
            if i % 50 == 0 or i == len(courses_api_data) - 1:
                status.info(f"Verarbeite Kurs {i+1}/{len(courses_api_data)}: {course_api_item.get('title', '')}")
            
            course_id_api = str(course_api_item.get('id', ''))
            existing_course_db = db_session.query(Course).filter(Course.course_id == course_id_api).first()
            
            course_data_for_db = {
                'course_id': course_id_api,
                'meeting_code': course_api_item.get('meetingCode', ''),
                'title': course_api_item.get('title', ''),
                'description': course_api_item.get('remark', ''),
                'language_id': course_api_item.get('languageId', 0),
                'max_credits': json.dumps(course_api_item.get('maxCredits', [])),
                'term_id': term_id_from_api, 
                'link_course_info': course_api_item.get('linkCourseInformationSheet', '')
            }
            
            if existing_course_db:
                for key, value in course_data_for_db.items():
                    setattr(existing_course_db, key, value)
            else:
                db_session.add(Course(**course_data_for_db))
            
            course_dates_api = fetch_course_schedule(term_id_from_api, course_id_api)
            if course_dates_api:
                schedules_added_this_course = store_course_schedule(db_session, course_id_api, course_dates_api)
                schedules_added_count += schedules_added_this_course
            
            if i % 50 == 0:
                db_session.commit()
            
            courses_added_count += 1
        
        db_session.commit()
        
        progress_bar.empty()
        status.success(f"Erfolgreich importierte {courses_added_count} Kurse mit {schedules_added_count} Zeitplänen für {term_description_from_api} ({term_name_from_api}).")
        
        st.rerun()
        return True
    except Exception as e:
        db_session.rollback()
        st.error(f"Fehler beim Speichern von Kursen: {str(e)}")
        return False
    finally:
        db_session.close()

def store_course_schedule(db_session, course_id, course_dates_api):
    if not course_dates_api:
        return 0
        
    try:
        db_session.query(CourseSchedule).filter(CourseSchedule.course_id == course_id).delete()
        
        saved_dates_count = 0
        for date_api_item in course_dates_api:
            try:
                start_datetime = date_api_item.get('startTime')
                end_datetime = date_api_item.get('endTime')
                room = date_api_item.get('location', 'Kein Raum angegeben')
                
                if not start_datetime or not end_datetime:
                    continue
                
                start_date_val = start_datetime.split('T')[0]
                start_time_val = start_datetime.split('T')[1][:5]
                end_time_val = end_datetime.split('T')[1][:5]
                
                schedule_entry = CourseSchedule(
                    course_id=course_id,
                    start_date=start_date_val,
                    start_time=start_time_val,
                    end_time=end_time_val,
                    room=room
                )
                db_session.add(schedule_entry)
                saved_dates_count += 1
            except Exception as e:
                print(f"Error processing schedule item for course {course_id}: {e}")
                continue
        return saved_dates_count
    except Exception as e:
        print(f"Error storing course schedules for course {course_id}: {str(e)}")
        raise 

def save_user_course_selections(user_id, course_ids):
    db_session = SessionLocal()
    try:
        db_session.query(UserCourse).filter(UserCourse.user_id == user_id).delete()
        for course_id_val in course_ids:
            db_session.add(UserCourse(user_id=user_id, course_id=course_id_val))
        db_session.commit()
        return True
    except Exception as e:
        db_session.rollback()
        print(f"Error saving user course selections for user {user_id}: {e}")
        return False
    finally:
        db_session.close()

def display_hsg_api_page(user_id):
    st.title("HSG Kurse")
    
    user_id = st.session_state.get('user_id')
    username = st.session_state.get('username')
    
    st.write(f"Grüezi {username}! Hier können Sie Ihre Kurse an der Universität St. Gallen verwalten.")
    
    db_session = SessionLocal()
    try:
        course_count_db = db_session.query(Course).count()
        
        with st.expander("Verwaltung: Kursdatenbank aktualisieren"):
            if course_count_db > 0:
                st.info(f"Aktuell enthält die Datenbank {course_count_db} Kurs(e).")
            else:
                st.warning("Noch keine Kurse in der Datenbank.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Neueste Kurse von HSG API abrufen"):
                    fetch_and_store_courses()
        
        if course_count_db > 0:
            # Define local_lang_map once before tabs if used in multiple tabs, or inside each tab if specific
            languages_in_db = db_session.query(Language).all()
            local_lang_map = {lang.id: lang.language_name for lang in languages_in_db}

            tab1, tab2 = st.tabs(["Kurse auswählen", "Mein Stundenplan"])
            
            with tab1:
                all_course_objects = db_session.query(
                    Course.course_id, Course.meeting_code, Course.title, 
                    Course.description, Course.language_id
                ).all()
                
                user_course_ids_db = [uc.course_id for uc in db_session.query(
                    UserCourse.course_id).filter(UserCourse.user_id == user_id).all()
                ]
                
                df_courses_data = []
                for c_obj in all_course_objects:
                    df_courses_data.append({
                        'course_id': c_obj.course_id,
                        'meeting_code': c_obj.meeting_code,
                        'title': c_obj.title,
                        'description': c_obj.description,
                        'language_id': c_obj.language_id,
                        'language_name': local_lang_map.get(c_obj.language_id, f"Sprache {c_obj.language_id}"),
                        'selected': 1 if c_obj.course_id in user_course_ids_db else 0
                    })
                
                df_courses = pd.DataFrame(df_courses_data)
                
                search_term_val = st.text_input("Suche nach Kursen nach Titel oder Code:", key="search_courses")
                
                filtered_df = df_courses
                if search_term_val and not df_courses.empty:
                    filtered_df = df_courses[
                        df_courses['title'].str.contains(search_term_val, case=False, na=False) | 
                        df_courses['meeting_code'].str.contains(search_term_val, case=False, na=False)
                    ]
                
                unique_lang_names = sorted(filtered_df['language_name'].unique()) if not filtered_df.empty else []
                language_options = ["All"] + unique_lang_names
                selected_language_name = st.selectbox("Nach Sprache filtern:", language_options)
                
                if selected_language_name != "All" and not filtered_df.empty:
                    filtered_df = filtered_df[filtered_df['language_name'] == selected_language_name]
                
                st.write(f"Zeige {len(filtered_df)} Kurse")
                
                with st.form("course_selection_form"):
                    course_container = st.container()
                    submit_button_placeholder = st.empty()
                    
                    with course_container:
                        st.markdown("""
                        <style>
                        [data-testid="stVerticalBlock"] > div:nth-child(1) {
                            max-height: 400px;
                            overflow-y: auto;
                        }
                        </style>
                        """, unsafe_allow_html=True)
                        
                        selected_courses_ids = []
                        for _, row_data in filtered_df.iterrows():
                            course_id_val = row_data['course_id']
                            title_val = row_data['title']
                            code_val = row_data['meeting_code']
                            lang_name_val = row_data['language_name']
                            
                            is_selected = st.checkbox(
                                f"{code_val} - {title_val} ({lang_name_val})",
                                value=(row_data['selected'] == 1),
                                key=f"course_{course_id_val}"
                            )
                            
                            if is_selected:
                                selected_courses_ids.append(course_id_val)
                    
                    if submit_button_placeholder.form_submit_button("Kursauswahl speichern"):
                        if save_user_course_selections(user_id, selected_courses_ids):
                            st.success("Ihre Kursauswahl wurde gespeichert!!")
                            st.rerun()
            
            with tab2: # "Mein Stundenplan"
                user_selected_courses_details = get_user_courses(user_id)
                
                if not user_selected_courses_details:
                    st.info("Du hast noch keine Kurse ausgewählt. Gehe zum 'Kurse auswählen'-Tab, um Kurse hinzuzufügen.")
                else:
                    st.write(f"Du hast {len(user_selected_courses_details)} Kurse ausgewählt:")
                    # local_lang_map is already defined before tabs
                    for course_detail in user_selected_courses_details:
                        expander_label = f"{course_detail['meeting_code']} - {course_detail['title']}"
                        with st.expander(label=expander_label, expanded=False): # MODIFIED: Added expander, default collapsed
                            lang_name_display = local_lang_map.get(course_detail['language_id'], f"Sprache {course_detail['language_id']}")
                            # st.subheader(f"{course_detail['meeting_code']} - {course_detail['title']}") # Subheader is now expander label
                            st.write(f"**Sprache:** {lang_name_display}")
                            st.write(f"**Termin:** {course_detail['term_name']}")
                            st.write(f"**Beschreibung:** {course_detail['description']}")
                            if course_detail['link_course_info']:
                                st.markdown(f"[Weitere Informationen]({course_detail['link_course_info']})")
                            
                            course_schedule_entries = db_session.query(CourseSchedule).filter(CourseSchedule.course_id == course_detail['course_id']).all()
                            if course_schedule_entries:
                                st.write("**Zeitplan:**")
                                for entry in course_schedule_entries:
                                    st.write(f"- {entry.start_date} von {entry.start_time} bis {entry.end_time} in Raum {entry.room}")
                            else:
                                st.write("Kein Zeitplan für diesen Kurs hinterlegt.")
                        # st.divider() # Divider might be less necessary with expanders, or place outside
    except Exception as e:
        st.error(f"Ein Fehler ist aufgetreten: {e}")
    finally:
        db_session.close()

