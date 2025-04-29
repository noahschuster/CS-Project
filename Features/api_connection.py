import streamlit as st
import pandas as pd
import requests
import sqlite3
from datetime import datetime
import json
import os

# HSG API Constants
API_APPLICATION_ID = "587acf1c-24d0-4801-afda-c98f081c4678"
API_VERSION = "1"
API_BASE_URL = "https://integration.preprod.unisg.ch"
LANGUAGE_MAP = {2: "German", 21: "English"}

def fetch_current_term():
    url = f"{API_BASE_URL}/eventapi/timeLines/currentTerm"
    
    headers = {
        "X-ApplicationId": API_APPLICATION_ID,
        "API-Version": API_VERSION,
        "X-RequestedLanguage": "de"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.ok:
            return response.json()
        else:
            st.error(f"Error fetching current term: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error connecting to HSG API: {str(e)}")
        return None

def fetch_courses_for_term(term_id):
    url = f"{API_BASE_URL}/eventapi/Events/byTerm/{term_id}"
    
    headers = {
        "X-ApplicationId": API_APPLICATION_ID,
        "API-Version": API_VERSION,
        "X-RequestedLanguage": "de"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.ok:
            return response.json()
        else:
            st.error(f"Error fetching courses: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error connecting to HSG API: {str(e)}")
        return None

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
    
    st.write(f"Current Term: {term_description} ({term_name})")
    
    courses_data = fetch_courses_for_term(term_id)
    
    if not courses_data:
        status.error("Failed to fetch courses.")
        return False
    
    os.makedirs("./data", exist_ok=True)
    
    with sqlite3.connect('./data/studybuddy.db') as conn:
        c = conn.cursor()
        
        c.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY,
            course_id TEXT UNIQUE,
            meeting_code TEXT,
            title TEXT,
            description TEXT,
            language_id INTEGER,
            max_credits TEXT,
            term_id TEXT,
            term_name TEXT,
            term_description TEXT,
            link_course_info TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        c.execute('''
        CREATE TABLE IF NOT EXISTS user_courses (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            course_id TEXT,
            selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (course_id) REFERENCES courses (course_id)
        )
        ''')
        
        courses_added = 0
        
        for course in courses_data:
            try:
                max_credits = json.dumps(course.get('maxCredits', []))
                
                c.execute('''
                INSERT OR REPLACE INTO courses
                (course_id, meeting_code, title, description, language_id, max_credits, 
                term_id, term_name, term_description, link_course_info)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(course.get('id', '')), 
                    course.get('meetingCode', ''),
                    course.get('title', ''),
                    course.get('remark', ''),
                    course.get('languageId', 0),
                    max_credits,
                    term_id,
                    term_name,
                    term_description,
                    course.get('linkCourseInformationSheet', '')
                ))
                courses_added += 1
            except Exception as e:
                st.error(f"Error adding course {course.get('id', '')}: {str(e)}")
        
        conn.commit()
    
    status.success(f"Successfully imported {courses_added} courses for {term_description}")
    return True

def get_all_courses():
    try:
        with sqlite3.connect('./data/studybuddy.db') as conn:
            df = pd.read_sql_query("SELECT * FROM courses", conn)
            return df
    except Exception as e:
        st.error(f"Error fetching courses: {str(e)}")
        return pd.DataFrame()

def get_user_courses(user_id):
    try:
        with sqlite3.connect('./data/studybuddy.db') as conn:
            df = pd.read_sql_query("""
            SELECT c.*
            FROM courses c
            JOIN user_courses uc ON c.course_id = uc.course_id
            WHERE uc.user_id = ?
            """, conn, params=(user_id,))
            return df
    except Exception as e:
        st.error(f"Error fetching user courses: {str(e)}")
        return pd.DataFrame()

def save_user_course_selections(user_id, course_ids):
    try:
        with sqlite3.connect('./data/studybuddy.db') as conn:
            c = conn.cursor()
            c.execute('DELETE FROM user_courses WHERE user_id = ?', (user_id,))
            
            for course_id in course_ids:
                c.execute('''
                INSERT INTO user_courses (user_id, course_id)
                VALUES (?, ?)
                ''', (user_id, course_id))
            
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Error saving course selections: {str(e)}")
        return False

def display_hsg_api_page():
    st.title("HSG Courses")
    
    if not st.session_state.get('logged_in', False):
        st.warning("Please log in to access this page")
        return
    
    user_id = st.session_state.get('user_id')
    username = st.session_state.get('username')
    
    st.write(f"Hello {username}! Here you can manage your courses from the University of St. Gallen.")
    
    with sqlite3.connect('./data/studybuddy.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='courses'")
        table_exists = cursor.fetchone()[0] > 0
        
        course_count = 0
        if table_exists:
            cursor.execute("SELECT COUNT(*) FROM courses")
            course_count = cursor.fetchone()[0]
    
    with st.expander("Admin: Update Course Database"):
        st.write("Use this section to update the course database from the HSG API.")
        if course_count > 0:
            st.info(f"Currently there are {course_count} courses in the database.")
        else:
            st.warning("No courses in the database yet.")
        
        if st.button("Fetch Latest Courses from HSG API"):
            fetch_and_store_courses()
    
    if course_count > 0:
        tab1, tab2 = st.tabs(["Select Courses", "My Schedule"])
        
        with tab1:
            with sqlite3.connect('./data/studybuddy.db') as conn:
                df_courses = pd.read_sql_query("""
                SELECT c.course_id, c.meeting_code, c.title, c.description, c.language_id,
                       CASE WHEN uc.course_id IS NOT NULL THEN 1 ELSE 0 END as selected
                FROM courses c
                LEFT JOIN user_courses uc ON c.course_id = uc.course_id AND uc.user_id = ?
                ORDER BY c.title
                """, conn, params=(user_id,))
            
            search_term = st.text_input("Search courses by title or code:", key="search_courses")
            
            filtered_df = df_courses
            if search_term:
                filtered_df = df_courses[
                    df_courses['title'].str.contains(search_term, case=False) | 
                    df_courses['meeting_code'].str.contains(search_term, case=False)
                ]
            
            languages = sorted(filtered_df['language_id'].unique())
            language_options = ["All"] + [LANGUAGE_MAP.get(lang, f"Language {lang}") for lang in languages]
            selected_language = st.selectbox("Filter by language:", language_options)
            
            if selected_language != "All":
                lang_id = [k for k, v in LANGUAGE_MAP.items() if v == selected_language][0]
                filtered_df = filtered_df[filtered_df['language_id'] == lang_id]
            
            st.write(f"Showing {len(filtered_df)} courses")
            
            with st.form("course_selection_form"):
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
                
                submit_button = st.form_submit_button("Save Course Selection")
                
                if submit_button:
                    if save_user_course_selections(user_id, selected_courses):
                        st.success("Your course selection has been saved!")
                        st.rerun()
        
        with tab2:
            with sqlite3.connect('./data/studybuddy.db') as conn:
                user_courses = pd.read_sql_query("""
                SELECT c.meeting_code, c.title, c.description, c.language_id, c.link_course_info
                FROM courses c
                JOIN user_courses uc ON c.course_id = uc.course_id
                WHERE uc.user_id = ?
                ORDER BY c.title
                """, conn, params=(user_id,))
            
            if len(user_courses) == 0:
                st.info("You haven't selected any courses yet. Go to the 'Select Courses' tab to add courses to your schedule.")
            else:
                st.write(f"You have selected {len(user_courses)} courses:")
                
                for _, course in user_courses.iterrows():
                    with st.expander(f"{course['meeting_code']} - {course['title']}"):
                        st.write(f"**Language:** {LANGUAGE_MAP.get(course['language_id'], 'Unknown')}")
                        if course['description']:
                            st.write(f"**Description:** {course['description']}")
                        if course['link_course_info']:
                            st.markdown(f"[Course Information Sheet]({course['link_course_info']})")
    else:
        st.info("No courses available. Please use the admin section to fetch courses from the HSG API.")

if __name__ == "__main__":
    display_hsg_api_page()
