import streamlit as st
import pandas as pd
import datetime
import calendar
import sqlite3
from datetime import datetime, timedelta
import random

def display_calendar(user_id):
    st.title("Study Calendar")
    
    # Initialize session state for events if not already done
    if 'calendar_events' not in st.session_state:
        st.session_state.calendar_events = generate_demo_events()
    
    # Calendar navigation
    col1, col2, col3 = st.columns([2, 3, 2])
    
    with col1:
        # Get current month and year (default)
        if 'calendar_month' not in st.session_state:
            st.session_state.calendar_month = datetime.now().month
        if 'calendar_year' not in st.session_state:
            st.session_state.calendar_year = datetime.now().year
            
        if st.button("◀ Previous Month"):
            st.session_state.calendar_month -= 1
            if st.session_state.calendar_month < 1:
                st.session_state.calendar_month = 12
                st.session_state.calendar_year -= 1
    
    with col3:
        if st.button("Next Month ▶"):
            st.session_state.calendar_month += 1
            if st.session_state.calendar_month > 12:
                st.session_state.calendar_month = 1
                st.session_state.calendar_year += 1
    
    with col2:
        month_name = calendar.month_name[st.session_state.calendar_month]
        st.subheader(f"{month_name} {st.session_state.calendar_year}")
    
    # Create calendar grid
    cal = calendar.monthcalendar(st.session_state.calendar_year, st.session_state.calendar_month)
    
    # Display weekday headers with custom styling
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    cols = st.columns(7)
    for i, col in enumerate(cols):
        with col:
            st.markdown(f"<div style='text-align: center; font-weight: bold;'>{weekdays[i]}</div>", unsafe_allow_html=True)
    
    # Display calendar days with events
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day == 0:
                    # Empty cell for days not in this month
                    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
                else:
                    # Create a date object for this day
                    current_date = datetime(st.session_state.calendar_year, st.session_state.calendar_month, day)
                    date_str = current_date.strftime("%Y-%m-%d")
                    
                    # Check if we have events for this day
                    day_events = [e for e in st.session_state.calendar_events if e['date'] == date_str]
                    
                    # Style differently if there are events
                    if day_events:
                        st.markdown(
                            f"""
                            <div style='background-color: #e6f3ff; border-radius: 5px; padding: 5px; height: 80px; overflow-y: auto;'>
                                <div style='font-weight: bold; text-align: center;'>{day}</div>
                                <hr style='margin: 2px;'>
                            """, 
                            unsafe_allow_html=True
                        )
                        
                        for event in day_events:
                            st.markdown(
                                f"""<div style='font-size: 0.8em; margin-bottom: 2px; background-color: {event['color']}; 
                                padding: 2px; border-radius: 3px;'>{event['time']} - {event['title']}</div>""", 
                                unsafe_allow_html=True
                            )
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(
                            f"""
                            <div style='background-color: #f5f5f5; border-radius: 5px; padding: 5px; height: 80px;'>
                                <div style='font-weight: bold; text-align: center;'>{day}</div>
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )
    
    # Event management section
    st.subheader("Manage Events")
    
    tab1, tab2 = st.tabs(["Add Event", "View/Edit Events"])
    
    with tab1:
        with st.form("add_event_form"):
            event_date = st.date_input("Date", datetime.now())
            event_title = st.text_input("Event Title")
            event_time = st.time_input("Time", datetime.now().time())
            
            event_type = st.selectbox(
                "Event Type", 
                ["Study Session", "Lecture", "Exam", "Assignment Due", "Group Meeting", "Other"]
            )
            
            # Color mapping for event types
            color_map = {
                "Study Session": "#ffcccc",  # Light red
                "Lecture": "#ccffcc",        # Light green
                "Exam": "#ffaaaa",           # Darker red
                "Assignment Due": "#ffffcc", # Light yellow
                "Group Meeting": "#ccccff",  # Light blue
                "Other": "#f0f0f0"           # Light grey
            }
            
            submit_button = st.form_submit_button("Add Event")
            
            if submit_button and event_title:
                new_event = {
                    'date': event_date.strftime("%Y-%m-%d"),
                    'title': event_title,
                    'time': event_time.strftime("%H:%M"),
                    'type': event_type,
                    'color': color_map[event_type],
                    'user_id': user_id
                }
                
                st.session_state.calendar_events.append(new_event)
                st.success(f"Event '{event_title}' added on {event_date.strftime('%Y-%m-%d')}")
                st.rerun()
    
    with tab2:
        if not st.session_state.calendar_events:
            st.info("No events scheduled yet.")
        else:
            # Group events by date for better organization
            from collections import defaultdict
            events_by_date = defaultdict(list)
            
            for event in st.session_state.calendar_events:
                date_obj = datetime.strptime(event['date'], "%Y-%m-%d")
                formatted_date = date_obj.strftime("%A, %B %d, %Y")
                events_by_date[formatted_date].append(event)
            
            # Sort dates chronologically
            sorted_dates = sorted(events_by_date.keys(), 
                                 key=lambda x: datetime.strptime(x, "%A, %B %d, %Y"))
            
            # Display events by date
            for date in sorted_dates:
                with st.expander(date):
                    for i, event in enumerate(events_by_date[date]):
                        col1, col2 = st.columns([5, 1])
                        with col1:
                            st.markdown(
                                f"""<div style='background-color: {event['color']}; padding: 10px; 
                                border-radius: 5px; margin-bottom: 5px;'>
                                <strong>{event['time']}</strong> - {event['title']} ({event['type']})
                                </div>""", 
                                unsafe_allow_html=True
                            )
                        with col2:
                            if st.button("Delete", key=f"del_{date}_{i}"):
                                st.session_state.calendar_events.remove(event)
                                st.rerun()

def generate_demo_events():
    """Generate demo events for the calendar"""
    events = []
    
    # Event types with their colors
    event_types = [
        {"type": "Study Session", "color": "#ffcccc"},
        {"type": "Lecture", "color": "#ccffcc"},
        {"type": "Exam", "color": "#ffaaaa"},
        {"type": "Assignment Due", "color": "#ffffcc"},
        {"type": "Group Meeting", "color": "#ccccff"}
    ]
    
    # Course names for demo events
    course_names = [
        "Introduction to Programming",
        "Data Structures and Algorithms",
        "Machine Learning Fundamentals",
        "Business Analytics",
        "Marketing Research",
        "Financial Accounting"
    ]
    
    # Generate events for the current month and next month
    today = datetime.now()
    
    # Add some events in the past
    for _ in range(5):
        past_date = today - timedelta(days=random.randint(1, 15))
        event_type = random.choice(event_types)
        course = random.choice(course_names)
        
        events.append({
            'date': past_date.strftime("%Y-%m-%d"),
            'title': f"{course}",
            'time': f"{random.randint(8, 18):02d}:{random.choice(['00', '30'])}",
            'type': event_type["type"],
            'color': event_type["color"],
            'user_id': 1  # Demo user ID
        })
    
    # Add some events in the future
    for _ in range(10):
        future_date = today + timedelta(days=random.randint(0, 30))
        event_type = random.choice(event_types)
        course = random.choice(course_names)
        
        events.append({
            'date': future_date.strftime("%Y-%m-%d"),
            'title': f"{course}",
            'time': f"{random.randint(8, 18):02d}:{random.choice(['00', '30'])}",
            'type': event_type["type"],
            'color': event_type["color"],
            'user_id': 1  # Demo user ID
        })
    
    return events

# Function to integrate with your database later
def save_events_to_db(user_id, events):
    """Save events to the database - placeholder for future implementation"""
    # This will be implemented when you're ready to connect to your database
    pass

# Function to load events from your database later
def load_events_from_db(user_id):
    """Load events from the database - placeholder for future implementation"""
    # This will be implemented when you're ready to connect to your database
    return []

# To integrate with your main app, you can add this to your dashboard.py navigation
# or create a new file called calendar.py with this code and import it in your main app
