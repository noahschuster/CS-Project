import streamlit as st
import api_connection

def display_courses(user_id):
    st.title("Courses")
    st.write("Manage your courses here.")
    api_connection.display_hsg_api_page()
