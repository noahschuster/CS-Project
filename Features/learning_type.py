import streamlit as st
from utils import get_user_learning_type, set_learning_type

def display_learning_type(user_id):
    st.title("Discover Your Learning Type")
    
    current_type = get_user_learning_type(user_id)
    if current_type:
        st.success(f"Your current learning type: {current_type}")
        st.write("Want to retake the quiz? Use the form below.")
    
    st.subheader("Learning Type Quiz")
    st.write("Answer these questions to help us identify your optimal learning style.")
    
    # Simple quiz implementation
    with st.form("learning_type_quiz"):
        st.write("1. How do you prefer to learn new information?")
        q1 = st.radio(
            "Select one:",
            ["Reading and writing notes", "Listening to explanations", "Hands-on activities", "Visual aids and diagrams"],
            key="q1"
        )
        
        st.write("2. When trying to remember something, you typically:")
        q2 = st.radio(
            "Select one:",
            ["Write it down multiple times", "Repeat it out loud", "Act it out or use physical movement", "Create a mental image"],
            key="q2"
        )
        
        st.write("3. When learning a new skill, you prefer to:")
        q3 = st.radio(
            "Select one:",
            ["Read instructions", "Listen to verbal directions", "Jump in and try it", "Watch someone demonstrate"],
            key="q3"
        )
        
        submitted = st.form_submit_button("Submit Quiz")
        
        if submitted:
            # Simple algorithm to determine learning type
            responses = [q1, q2, q3]
            
            reading_writing_count = sum(1 for r in responses if "read" in r.lower() or "writ" in r.lower())
            auditory_count = sum(1 for r in responses if "listen" in r.lower() or "verbal" in r.lower() or "repeat" in r.lower())
            kinesthetic_count = sum(1 for r in responses if "hands-on" in r.lower() or "physical" in r.lower() or "try" in r.lower())
            visual_count = sum(1 for r in responses if "visual" in r.lower() or "image" in r.lower() or "watch" in r.lower() or "diagram" in r.lower())
            
            counts = {
                "Reading/Writing": reading_writing_count,
                "Auditory": auditory_count,
                "Kinesthetic": kinesthetic_count,
                "Visual": visual_count
            }
            
            # Find the learning type with the highest count
            learning_type = max(counts, key=counts.get)
            
            # Update the database using the utils function
            if set_learning_type(user_id, learning_type):
                st.session_state.learning_type_completed = True
                st.success(f"Your learning type has been identified as: {learning_type}")
                st.info("Based on your learning type, we'll customize your study experience.")
                
                # The button needs to be OUTSIDE the form
                st.write("Click below to continue to your dashboard.")
            else:
                st.error("There was an error saving your learning type. Please try again.")
    
    # Place the button outside the form
    if st.session_state.get("learning_type_completed", False):
        if st.button("Continue to Dashboard"):
            st.rerun()  # This will trigger a rerun and go to dashboard
