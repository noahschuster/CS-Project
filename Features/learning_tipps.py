import streamlit as st
from utils import get_user_learning_type

def display_learning_tips(user_id):
    """
    Displays personalized learning tips based on the user's VARK learning type.
    Optimized for performance with minimal, purposeful animations.
    """
    # Apply essential CSS only - reduced animations and simplified styling
    st.markdown("""
    <style>
    .tip-card {
      background: rgba(255,255,255,0.9);
      padding: 1.5rem;
      border-radius: 0.75rem;
      margin: 1.5rem auto;
      max-width: 800px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .tip-card h2 {
      font-size: 1.5rem;
      margin-bottom: 0.75rem;
      color: #0366d6;
    }
    .tip-card ul {
      list-style-type: none;
      padding-left: 0.5rem;
    }
    .tip-card li {
      margin-bottom: 0.5rem;
      position: relative;
      padding-left: 1.5rem;
    }
    .tip-card li:before {
      content: "💡";
      position: absolute;
      left: 0;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("Personalized Learning Tips")
    
    # Get learning type with error handling
    learning_type = get_user_learning_type(user_id)
    if not learning_type:
        st.warning("Please complete the learning style assessment first.")
        return

    # VARK learning strategies data - separated from display logic
    tip_mapping = {
        "Visuell": {
            "title": "Visual Strategies",
            "tips": [
                "Replace keywords with symbols or diagrams",
                "Use colors, images and spatial arrangements in your notes",
                "Look for patterns in your materials",
                "Condense notes into one-page visual summaries",
                "Redraw notes from memory",
                "Translate visualizations back into words"
            ]
        },
        "Auditiv": {
            "title": "Auditory Strategies",
            "tips": [
                "Attend lectures, discussions and tutorials",
                "Leave gaps in notes for later recall and filling in",
                "Explain concepts aloud to others",
                "Summarize key points verbally",
                "Record and replay important content",
                "Discuss topics with instructors and peers",
                "Use rhythms and mnemonics for memorization",
                "Practice by speaking answers aloud"
            ]
        },
        "Lesen/Schreiben": {
            "title": "Reading/Writing Strategies",
            "tips": [
                "Study textbooks and assigned readings",
                "Use lists, glossaries and dictionaries",
                "Rewrite ideas in your own words",
                "Convert diagrams to written descriptions",
                "Write structured essays with clear sections",
                "Organize notes hierarchically",
                "Rewrite notes multiple times for retention",
                "Practice writing answers to test questions"
            ]
        },
        "Kinästhetisch": {
            "title": "Kinesthetic Strategies",
            "tips": [
                "Add real-world details to your notes",
                "Discuss notes with fellow hands-on learners",
                "Use case studies and practical examples",
                "Participate in labs and field trips",
                "Recall successful learning experiences",
                "Practice solutions using previous exams",
                "Apply concepts to real-life situations"
            ]
        }
    }

    # Process multimodal learning types efficiently
    display_types = []
    if learning_type.startswith("Multimodal"):
        start_idx = learning_type.find("(")
        end_idx = learning_type.find(")")
        if start_idx != -1 and end_idx != -1:
            display_types = [lt.strip() for lt in learning_type[start_idx+1:end_idx].split(",")]
    else:
        display_types = [learning_type]

    # Display tips for each learning type
    for lt in display_types:
        strategy = tip_mapping.get(lt)
        if not strategy:
            st.warning(f"No tips available for learning type: {lt}")
            continue
            
        st.markdown(f"""
        <div class='tip-card'>
          <h2>{strategy['title']}</h2>
          <ul>
            {''.join(f'<li>{t}</li>' for t in strategy['tips'])}
          </ul>
        </div>
        """, unsafe_allow_html=True)
