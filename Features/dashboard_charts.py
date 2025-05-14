import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from learning_suggestions import get_study_tasks
from database_manager import get_calendar_events
import streamlit as st

# Moderne Farben auswählen für die Charts auf dem Dashboard
MY_COLORS = [
    "#0EA5E9",  
    "#10B981",  
    "#F59E0B",  
    "#F43F5E",  
    "#64748B",
    "#78716C",
]

# autotexts definieren
def style_autotexts(autotexts):
    for autotext in autotexts:
        autotext.set_fontsize(20)  # Grosse Schriftgrösse bei den Beschriftungen 
        autotext.set_color('white')
        autotext.set_weight('bold')

# kuchendiagramm definieren via funktion für Zeit je nach Fach gelernt
def create_pie_chart_learning_time_by_subject(user_id):
    study_tasks = get_study_tasks(user_id)

    subject_times = {}
    for task in study_tasks:
        subject = task['course_title']
        duration = (datetime.strptime(task['end_time'], "%H:%M") - datetime.strptime(task['start_time'], "%H:%M")).seconds / 3600
        subject_times[subject] = subject_times.get(subject, 0) + duration

    labels = list(subject_times.keys())
    sizes = list(subject_times.values())

    # Create figure with larger square aspect ratio
    fig, ax = plt.subplots(figsize=(14, 14))
    
    # Center the pie chart and make it even larger
    ax.set_position([0.1, 0.2, 0.8, 0.8])
    
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=None,
        autopct='%1.1f%%',
        startangle=140,
        wedgeprops={'width': 0.7},
        colors=MY_COLORS[:len(sizes)],
        textprops={'fontsize': 24, 'color': 'white', 'weight': 'bold'}  # Increased font size
    )

    # Style the percentage text
    for autotext in autotexts:
        autotext.set_fontsize(24)
        autotext.set_color('white')
        autotext.set_weight('bold')

    # Place legend below the pie chart with more space
    ax.legend(
        wedges,
        labels,
        title="Themen",
        loc="lower center",
        bbox_to_anchor=(0.5, -0.35),  # Moved legend further down
        fontsize=24,
        title_fontsize=26,
        ncol=1,
        frameon=False
    )

    plt.tight_layout(pad=2.0)  # Added padding
    st.pyplot(fig)

# kuchendiagramm definieren via funktion für Zeit nächste Woche
def create_pie_chart_next_week_usage(user_id):
    events = get_calendar_events(user_id)
    next_week = datetime.now() + timedelta(days=7)

    total_hours = 40 # Annahme 40 Stunden pro Woche verfügbar
    used_hours = 0
    for event in events:
        event_date = datetime.strptime(event['date'], "%Y-%m-%d")
        if datetime.now() <= event_date <= next_week:
            used_hours += 1

    free_hours = total_hours - used_hours
    labels = ['Belegte Zeit', 'Freie Zeit']
    sizes = [used_hours, free_hours]

    fig, ax = plt.subplots(figsize=(9, 9))
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=None,
        autopct='%1.1f%%',
        startangle=140,
        wedgeprops={'width': 0.85},
        colors=[MY_COLORS[0], MY_COLORS[2]]
    )

    style_autotexts(autotexts)

    ax.legend(
        wedges,
        labels,
        title="Zeitnutzung",
        loc="lower center",
        bbox_to_anchor=(0.5, -0.15),  # Legende weiter nach unten
        fontsize=24,                  # Grosser Legendentext
        title_fontsize=26,            # Grosser Titel
        ncol=1,                       # Items vertikal anordnen
        frameon=False
    )

    plt.tight_layout()
    st.pyplot(fig)
