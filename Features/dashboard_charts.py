import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from learning_suggestions import get_study_tasks
from database_manager import get_calendar_events
import streamlit as st

# Charts für das Dashboard erstellen
def create_pie_chart_learning_time_by_subject(user_id):
    study_tasks = get_study_tasks(user_id)
    
    # Daten aggregieren
    subject_times = {}
    for task in study_tasks:
        subject = task['course_title']
        duration = (datetime.strptime(task['end_time'], "%H:%M") - datetime.strptime(task['start_time'], "%H:%M")).seconds / 3600
        subject_times[subject] = subject_times.get(subject, 0) + duration

    labels = list(subject_times.keys())
    sizes = list(subject_times.values())
    
    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, texts, autotexts = ax.pie(
        sizes, 
        autopct='%1.1f%%', 
        startangle=140,
        wedgeprops={'width': 0.85}  # Reduziert den Durchmesser für ein kompakteres Diagramm
    )
    
    # Legende unterhalb des Diagramms
    ax.legend(
        wedges, 
        labels, 
        title="Themen", 
        loc="center left", 
        bbox_to_anchor=(0.5, -0.1),
        fontsize=30  # Schriftgröße der Legende
    )
    st.pyplot(fig)

def create_pie_chart_next_week_usage(user_id):
    """Erstellt ein Tortendiagramm für die Zeitnutzung der nächsten Woche."""
    events = get_calendar_events(user_id)
    next_week = datetime.now() + timedelta(days=7)
    
    total_hours = 40
    used_hours = 0
    for event in events:
        event_date = datetime.strptime(event['date'], "%Y-%m-%d")
        if datetime.now() <= event_date <= next_week:
            used_hours += 1  # Annahme: 1 Stunde pro Event

    free_hours = total_hours - used_hours
    labels = ['Belegte Zeit', 'Freie Zeit']
    sizes = [used_hours, free_hours]
    
    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, texts, autotexts = ax.pie(
        sizes, 
        autopct='%1.1f%%', 
        startangle=140,
        wedgeprops={'width': 0.85}  # Reduziert den Durchmesser für ein kompakteres Diagramm
    )
    
    # Legende unterhalb des Diagramms
    ax.legend(
        wedges, 
        labels, 
        title="Zeitnutzung", 
        loc="center left", 
        bbox_to_anchor=(0.5, -0.1),
        fontsize=30  # Schriftgröße der Legende
    )
    st.pyplot(fig)
