import streamlit as st
import sqlite3
import pandas as pd
import json
from datetime import datetime

def app():
    st.title("StudyBuddy - Course Selection")
    
    # Check if user is logged in
    if not st.session_state.get('logged_in', False):
        st.warning("Please log in to view and select courses")
        st.stop()
    
    # Get user info
    user_id = st.session_state.get('user_id')
    username = st.session_state.get('username')
    
    st.write(f"Hello {username}! Let's set up your courses for this semester.")
    
    # Connect to database
    conn = sqlite3.connect('./data/studybuddy.db')
    
    # Check if courses exist in database
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM courses")
    course_count = cursor.fetchone()[0]
    
    if course_count == 0:
        st.warning("No courses available in the database. Please contact an administrator.")
        conn.close()
        st.stop()
    
    # Get term information
    cursor.execute("SELECT DISTINCT term_name, term_description FROM courses LIMIT 1")
    term_info = cursor.fetchone()
    term_name, term_description = term_info if term_info else ("Unknown", "Unknown")
    
    st.subheader(f"Course Selection for {term_description}")
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["Select Courses", "My Schedule"])
    
    with tab1:
        # Get all courses
        df_courses = pd.read_sql_query("""
        SELECT c.course_id, c.meeting_code, c.title, c.description, c.language_id,
               CASE WHEN uc.course_id IS NOT NULL THEN 1 ELSE 0 END as selected
        FROM courses c
        LEFT JOIN user_courses uc ON c.course_id = uc.course_id AND uc.user_id = ?
        ORDER BY c.title
        """, conn, params=(user_id,))
        
        # Add search functionality
        search_term = st.text_input("Search courses by title or code:", key="search_courses")
        
        # Filter courses based on search
        if search_term:
            filtered_df = df_courses[
                df_courses['title'].str.contains(search_term, case=False) | 
                df_courses['meeting_code'].str.contains(search_term, case=False)
            ]
        else:
            filtered_df = df_courses
        
        # Add language filter
        language_map = {2: "German", 21: "English"}
        languages = sorted(filtered_df['language_id'].unique())
        language_options = ["All"] + [language_map.get(lang, f"Language {lang}") for lang in languages]
        selected_language = st.selectbox("Filter by language:", language_options)
        
        if selected_language != "All":
            lang_id = [k for k, v in language_map.items() if v == selected_language][0]
            filtered_df = filtered_df[filtered_df['language_id'] == lang_id]
        
        # Display courses with checkboxes
        st.write(f"Showing {len(filtered_df)} courses")
        
        # Create a form for course selection
        with st.form("course_selection_form"):
            selected_courses = []
            
            for _, row in filtered_df.iterrows():
                course_id = row['course_id']
                title = row['title']
                code = row['meeting_code']
                lang = language_map.get(row['language_id'], f"Language {row['language_id']}")
                
                # Create a checkbox for each course
                is_selected = st.checkbox(
                    f"{code} - {title} ({lang})",
                    value=(row['selected'] == 1),
                    key=f"course_{course_id}"
                )
                
                if is_selected:
                    selected_courses.append(course_id)
            
            # Submit button
            submit_button = st.form_submit_button("Save Course Selection")
            
            if submit_button:
                # Clear previous selections
                cursor.execute('DELETE FROM user_courses WHERE user_id = ?', (user_id,))
                
                # Add new selections
                for course_id in selected_courses:
                    cursor.execute('''
                    INSERT INTO user_courses (user_id, course_id)
                    VALUES (?, ?)
                    ''', (user_id, course_id))
                
                conn.commit()
                st.success("Your course selection has been saved!")
                st.experimental_rerun()
    
    with tab2:
        # Get user's selected courses
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
            st.write(f"You have selected {len(user_courses)} courses for {term_description}:")
            
            # Display courses in a nice format
            for _, course in user_courses.iterrows():
                with st.expander(f"{course['meeting_code']} - {course['title']}"):
                    st.write(f"**Language:** {language_map.get(course['language_id'], 'Unknown')}")
                    if course['description']:
                        st.write(f"**Description:** {course['description']}")
                    if course['link_course_info']:
                        st.markdown(f"[Course Information Sheet]({course['link_course_info']})")
    
    conn.close()

if __name__ == "__main__":
    app()
