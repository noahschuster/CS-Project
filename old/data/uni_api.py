import streamlit as st
import pandas as pd
import requests
import sqlite3
from datetime import datetime
import json
import os

# Create a function to fetch and store course data
def fetch_and_store_courses():
    # Create a status message
    status = st.empty()
    status.info("Fetching course data from HSG API...")
    
    # First, get the current semester
    url = "https://integration.preprod.unisg.ch/eventapi/timeLines/currentTerm"
    
    headers = {
        "X-ApplicationId": "587acf1c-24d0-4801-afda-c98f081c4678",
        "API-Version": "1",
        "X-RequestedLanguage": "de"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.ok:
            current_term = response.json()
            term_id = current_term['id']
            term_name = current_term['shortName']
            term_description = current_term['description']
            
            # Display term info
            st.write(f"Current Term: {term_description} ({term_name})")
            
            # Now fetch all courses for this term
            courses_url = f"https://integration.preprod.unisg.ch/eventapi/Events/byTerm/{term_id}"
            
            courses_response = requests.get(courses_url, headers=headers)
            
            if courses_response.ok:
                courses_data = courses_response.json()
                
                # Convert to DataFrame for easier handling
                df = pd.DataFrame(courses_data)
                
                # Create database directory if it doesn't exist
                if not os.path.exists("./data"):
                    os.makedirs("./data")
                
                # Connect to SQLite database
                conn = sqlite3.connect('./data/studybuddy.db')
                c = conn.cursor()
                
                # Create courses table if it doesn't exist
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
                
                # Create user_courses table for storing user selections
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
                
                # Insert courses into database
                courses_added = 0
                
                for _, course in df.iterrows():
                    try:
                        # Convert maxCredits list to string
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
                conn.close()
                
                status.success(f"Successfully imported {courses_added} courses for {term_description}")
                return True
            else:
                status.error(f"Error fetching courses: {courses_response.status_code}")
                return False
        else:
            status.error(f"Error fetching current term: {response.status_code}")
            return False
    except Exception as e:
        status.error(f"Error: {str(e)}")
        return False

# Create a page for course selection
def course_selection_page():
    st.title("Course Selection")
    st.subheader("Select your courses for the current semester")
    
    # Check if user is logged in
    if not st.session_state.get('logged_in', False):
        st.warning("Please log in to select courses")
        return
    
    # Connect to database
    conn = sqlite3.connect('./data/studybuddy.db')
    c = conn.cursor()
    
    # Get current user ID
    user_id = st.session_state.get('user_id')
    
    # Get courses from database
    c.execute('SELECT course_id, meeting_code, title, language_id FROM courses ORDER BY title')
    courses = c.fetchall()
    
    # Get user's selected courses
    c.execute('SELECT course_id FROM user_courses WHERE user_id = ?', (user_id,))
    selected_courses = [row[0] for row in c.fetchall()]
    
    # Display courses in a searchable format
    st.subheader("Available Courses")
    
    # Add search functionality
    search_term = st.text_input("Search courses by title or code:", "")
    
    # Filter courses based on search term
    filtered_courses = courses
    if search_term:
        filtered_courses = [course for course in courses 
                           if search_term.lower() in course[2].lower() 
                           or search_term.lower() in course[1].lower()]
    
    # Display courses in a multi-select box
    course_options = {f"{course[1]} - {course[2]}": course[0] for course in filtered_courses}
    
    if course_options:
        selected = st.multiselect(
            "Select your courses:",
            options=list(course_options.keys()),
            default=[key for key, value in course_options.items() if value in selected_courses]
        )
        
        # Convert selected course names back to IDs
        selected_ids = [course_options[course_name] for course_name in selected]
        
        # Save button
        if st.button("Save Course Selection"):
            # Clear previous selections
            c.execute('DELETE FROM user_courses WHERE user_id = ?', (user_id,))
            
            # Add new selections
            for course_id in selected_ids:
                c.execute('''
                INSERT INTO user_courses (user_id, course_id)
                VALUES (?, ?)
                ''', (user_id, course_id))
            
            conn.commit()
            st.success("Your course selection has been saved!")
    else:
        st.info("No courses match your search criteria.")
    
    conn.close()

# Admin page to fetch and update courses
def admin_course_management():
    st.title("Course Management (Admin)")
    
    # Check if user is admin (you would need to add admin flag to your users table)
    if not st.session_state.get('is_admin', True):  # Default to True for testing
        st.warning("You need admin privileges to access this page")
        return
    
    st.subheader("Update Course Database")
    
    if st.button("Fetch Latest Courses from HSG API"):
        fetch_and_store_courses()
    
    # Display existing courses
    conn = sqlite3.connect('./data/studybuddy.db')
    try:
        df = pd.read_sql_query("SELECT meeting_code, title, language_id, term_name FROM courses", conn)
        st.subheader("Current Courses in Database")
        st.write(f"Total courses: {len(df)}")
        st.dataframe(df)
    except:
        st.info("No courses in database yet. Click 'Fetch Latest Courses' to import them.")
    
    conn.close()

# Main app
def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Login", "Course Selection", "Admin: Course Management"])
    
    if page == "Login":
        # Your existing login code here
        pass
    elif page == "Course Selection":
        course_selection_page()
    elif page == "Admin: Course Management":
        admin_course_management()

if __name__ == "__main__":
    main()
