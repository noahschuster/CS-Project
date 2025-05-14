import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from learning_suggestions import get_study_tasks
from database_manager import get_calendar_events
import streamlit as st

# Modern Material/Tailwind Inspired Colors
PREMIUM_COLORS = [
    "#0EA5E9",  # Sky Blue
    "#10B981",  # Emerald
    "#F59E0B",  # Amber
    "#F43F5E",  # Rose
    "#64748B",  # Slate
    "#78716C",  # Stone
]

def style_autotexts(autotexts):
    for autotext in autotexts:
        autotext.set_fontsize(20)  # Large readable labels
        autotext.set_color('white')
        autotext.set_weight('bold')

def create_pie_chart_learning_time_by_subject(user_id):
    study_tasks = get_study_tasks(user_id)

    subject_times = {}
    for task in study_tasks:
        subject = task['course_title']
        duration = (datetime.strptime(task['end_time'], "%H:%M") - datetime.strptime(task['start_time'], "%H:%M")).seconds / 3600
        subject_times[subject] = subject_times.get(subject, 0) + duration

    labels = list(subject_times.keys())
    sizes = list(subject_times.values())

    fig, ax = plt.subplots(figsize=(9, 9))
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=None,
        autopct='%1.1f%%',
        startangle=140,
        wedgeprops={'width': 0.85},
        colors=PREMIUM_COLORS[:len(sizes)]
    )

    style_autotexts(autotexts)

    ax.legend(
        wedges,
        labels,
        title="Themen",
        loc="lower center",
        bbox_to_anchor=(0.5, -0.40),  # Push legend lower
        fontsize=24,                  # Large legend text
        title_fontsize=26,            # Large title
        ncol=1,                       # Stack items vertically
        frameon=False
    )

    plt.tight_layout()
    st.pyplot(fig)


def create_pie_chart_next_week_usage(user_id):
    events = get_calendar_events(user_id)
    next_week = datetime.now() + timedelta(days=7)

    total_hours = 40
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
        colors=[PREMIUM_COLORS[0], PREMIUM_COLORS[2]]
    )

    style_autotexts(autotexts)

    ax.legend(
        wedges,
        labels,
        title="Zeitnutzung",
        loc="lower center",
        bbox_to_anchor=(0.5, -0.40),  # Push legend lower
        fontsize=24,                  # Large legend text
        title_fontsize=26,            # Large title
        ncol=1,                       # Stack items vertically
        frameon=False
    )

    plt.tight_layout()
    st.pyplot(fig)
