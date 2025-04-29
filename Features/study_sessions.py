import streamlit as st
from utils import get_user_sessions

def display_study_sessions(user_id):
    st.title("Your Study Sessions")
    
    sessions_df = get_user_sessions(user_id)
    if sessions_df.empty:
        st.info("You haven't recorded any study sessions yet.")
        st.write("Your sessions will be automatically tracked when you log in and out of StudyBuddy.")
    else:
        st.dataframe(sessions_df)
        st.write("Detailed session data displayed above.")
