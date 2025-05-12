import streamlit as st
import pandas as pd
import requests
import json
from database_manager import SessionLocal, Course, UserCourse

# HSG API Constants
API_APPLICATION_ID = "587acf1c-24d0-4801-afda-c98f081c4678"
API_VERSION = "1"
API_BASE_URL = "https://integration.preprod.unisg.ch"
LANGUAGE_MAP = {2: "German", 21: "English"}

def api_request(endpoint, headers=None):
    if headers is None:
        headers = {
            "X-ApplicationId": API_APPLICATION_ID,
            "API-Version": API_VERSION,
            "X-RequestedLanguage": "de"
        }
    
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", headers=headers)
        if response.ok:
            return response.json()

        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Connection Error: {str(e)}")
        return None

def fetch_current_term():
    return api_request("/eventapi/timeLines/currentTerm")

def fetch_courses_for_term(term_id):
    return api_request(f"/eventapi/Events/byTerm/{term_id}")

def get_user_courses(user_id):
    """
    Get courses a specific user is enrolled in.
    
    Args:
        user_id (int): The user ID to fetch courses for
        
    Returns:
        list: List of course information dictionaries for the user
    """
    session = SessionLocal()
    try:
        # Query courses joined with user_courses to get only user's selected courses
        user_courses = session.query(
            Course
        ).join(
            UserCourse, Course.course_id == UserCourse.course_id
        ).filter(
            UserCourse.user_id == user_id
        ).all()
        
        # Convert to list of dictionaries
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
    except Exception as e:
        st.error(f"Error fetching user courses: {str(e)}")
        return []
    finally:
        session.close()

def fetch_and_store_courses():
    status = st.empty()
    status.info("Fetching course data from HSG API...")
    
    current_term = fetch_current_term()
    if not current_term:
        status.error("Failed to fetch current term information.")
        return False
    
    term_id = current_term['id']
    term_name = current_term['shortName']
    term_description = current_term['description']
    
    courses_data = fetch_courses_for_term(term_id)
    if not courses_data:
        status.error("Failed to fetch courses.")
        return False
    
    session = SessionLocal()
    try:
        courses_added = 0
        
        for course in courses_data:
            try:
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
                
                courses_added += 1
            except Exception as e:
                session.rollback()
                st.error(f"Error adding course {course.get('id', '')}: {str(e)}")
        
        session.commit()
        status.success(f"Successfully imported {courses_added} courses for {term_description}")
        return True
    except Exception as e:
        session.rollback()
        st.error(f"Error storing courses: {str(e)}")
        return False
    finally:
        session.close()

def save_user_course_selections(user_id, course_ids):
    try:
        session = SessionLocal()
        session.query(UserCourse).filter(UserCourse.user_id == user_id).delete()
        
        for course_id in course_ids:
            session.add(UserCourse(user_id=user_id, course_id=course_id))
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        st.error(f"Error saving course selections: {str(e)}")
        return False
    finally:
        session.close()

def create_demo_courses_from_summary():
    status = st.empty()
    status.info("Creating demo courses...")
    
    from demo_courses import create_demo_courses
    try:
        courses_added = create_demo_courses()
        status.success(f"Successfully created {courses_added} demo courses!")
        return courses_added > 0
    except Exception as e:
        status.error(f"Error creating demo courses: {str(e)}")
        return False

def display_hsg_api_page():
    st.title("HSG Courses")
    
    if not st.session_state.get('logged_in', False):
        st.warning("Please log in to access this page")
        return

    user_id = st.session_state.get('user_id')
    username = st.session_state.get('username')
    
    st.write(f"Hello {username}! Here you can manage your courses from the University of St. Gallen.")
    
    session = SessionLocal()
    try:
        course_count = session.query(Course).count()
        
        with st.expander("Admin: Update Course Database"):
            if course_count > 0:
                st.info(f"Currently there are {course_count} courses in the database.")
            else:
                st.warning("No courses in the database yet.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Fetch Latest Courses from HSG API"):
                    fetch_and_store_courses()
            with col2:
                if st.button("Create Demo Courses"):
                    create_demo_courses_from_summary()
        
        if course_count > 0:
            tab1, tab2 = st.tabs(["Select Courses", "My Schedule"])
            
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

                search_term = st.text_input("Search courses by title or code:", key="search_courses")
                
                filtered_df = df_courses
                if search_term and not df_courses.empty:
                    filtered_df = df_courses[
                        df_courses['title'].str.contains(search_term, case=False) | 
                        df_courses['meeting_code'].str.contains(search_term, case=False)
                    ]
                
                languages = sorted(filtered_df['language_id'].unique()) if not filtered_df.empty else []
                language_options = ["All"] + [LANGUAGE_MAP.get(lang, f"Language {lang}") for lang in languages]
                selected_language = st.selectbox("Filter by language:", language_options)
                
                if selected_language != "All" and not filtered_df.empty:
                    lang_id = [k for k, v in LANGUAGE_MAP.items() if v == selected_language][0]
                    filtered_df = filtered_df[filtered_df['language_id'] == lang_id]
                
                st.write(f"Showing {len(filtered_df)} courses")
                
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
                    if submit_button_placeholder.form_submit_button("Save Course Selection"):
                        if save_user_course_selections(user_id, selected_courses):
                            st.success("Your course selection has been saved!")
                            st.rerun()
            
            with tab2:
                user_courses = session.query(
                    Course.meeting_code, Course.title, Course.description, 
                    Course.language_id, Course.link_course_info
                ).join(
                    UserCourse, Course.course_id == UserCourse.course_id
                ).filter(
                    UserCourse.user_id == user_id
                ).all()
                
                if len(user_courses) == 0:
                    st.info("You haven't selected any courses yet. Go to the 'Select Courses' tab to add courses.")
                else:
                    st.write(f"You have selected {len(user_courses)} courses:")
                    
                    for course in user_courses:
                        with st.expander(f"{course.meeting_code} - {course.title}"):
                            st.write(f"**Language:** {LANGUAGE_MAP.get(course.language_id, 'Unknown')}")
                            if course.description:
                                st.write(f"**Description:** {course.description}")
                            if course.link_course_info:
                                st.markdown(f"[Course Information Sheet]({course.link_course_info})")
        else:
            st.info("No courses available. Please use the admin section to fetch courses.")
    
    except Exception as e:
        st.error(f"Error accessing database: {str(e)}")
    finally:
        session.close()


if __name__ == "__main__":
    display_hsg_api_page()