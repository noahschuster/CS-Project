import streamlit as st
import pandas as pd
import datetime
import calendar
from datetime import datetime, timedelta
import random
from database_manager import get_calendar_events, save_calendar_event, delete_calendar_event
# Neuer Import für Google Calendar Synchronisation
from google_calendar_sync import display_google_calendar_sync, check_auto_sync


def display_calendar(user_id):
    st.title("Studienkalender")
    
    # Tab-System für Kalender und Google Sync
    cal_tab1, cal_tab2 = st.tabs(["Kalender", "Google Kalender Sync"])
    
    with cal_tab1:
        # Lade Ereignisse aus der Datenbank statt Demo-Events zu verwenden
        db_events = get_calendar_events(user_id)
        st.session_state.calendar_events = db_events if db_events else []
        
        # Prüfe auf automatische Synchronisation
        check_auto_sync(user_id)
        
        # Calendar navigation
        col1, col2, col3 = st.columns([2, 3, 2])
        
        with col1:
            # Get current month and year (default)
            if 'calendar_month' not in st.session_state:
                st.session_state.calendar_month = datetime.now().month
            if 'calendar_year' not in st.session_state:
                st.session_state.calendar_year = datetime.now().year
                
            if st.button("◀ Vorheriger Monat"):
                st.session_state.calendar_month -= 1
                if st.session_state.calendar_month < 1:
                    st.session_state.calendar_month = 12
                    st.session_state.calendar_year -= 1
        with col3:
            if st.button("Nächster Monat ▶"):
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
        weekdays = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
        cols = st.columns(7)
        for i, col in enumerate(cols):
            with col:
                st.markdown(f"<div style='text-align: center; font-weight: bold;'>{weekdays[i]}</div>", unsafe_allow_html=True)
        
        # Add global CSS for hover effect - UPDATED VERSION
        st.markdown("""
        <style>
        .day-cell {
            background-color: #f5f5f5;
            border-radius: 5px;
            padding: 5px;
            height: 80px;
            position: relative;
            overflow: hidden;
        }
        
        .day-cell-events {
            background-color: #e6f3ff;
        }
        
        .day-cell-events:hover {
            position: absolute;
            z-index: 1000;
            width: 250px;
            height: auto;
            min-height: 80px;
            max-height: 300px;
            overflow-y: auto;
            background-color: white !important;
            box-shadow: 0 0 10px rgba(0,0,0,0.2);
        }
        
        .day-number {
            font-weight: bold;
            text-align: center;
            margin-bottom: 3px;
        }
        
        .event-mini {
            font-size: 0.7em;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            margin-bottom: 1px;
            padding: 1px;
            border-radius: 2px;
        }
        
        .event-full {
            display: none;
            font-size: 0.8em;
            margin-bottom: 3px;
            padding: 3px;
            border-radius: 3px;
        }
        
        .day-cell-events:hover .event-mini {
            display: none;
        }
        
        .day-cell-events:hover .event-full {
            display: block;
        }
        
        .events-container {
            max-height: 55px;
            overflow: hidden;
        }
                
        </style>
        """, unsafe_allow_html=True)
        
        # Display calendar days with events - UPDATED VERSION
        for week_idx, week in enumerate(cal):
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
                        
                        # Build the HTML for this day
                        html = f'<div class="day-cell{" day-cell-events" if day_events else ""}">'
                        html += f'<div class="day-number">{day}</div>'
                        
                        # Container for events with overflow control
                        if day_events:
                            html += '<div class="events-container">'
                            
                            # Add mini event previews
                            for event in day_events:
                                html += f'<div class="event-mini" style="background-color: {event["color"]};">'
                                html += f'{event["time"]} {event["title"][:10]}...'
                                html += '</div>'
                            
                            html += '</div>'
                            
                            # Add full event details (hidden until hover)
                            html += '<hr style="margin: 3px 0;">'
                            for event in day_events:
                                html += f'<div class="event-full" style="background-color: {event["color"]};">'
                                html += f'<strong>{event["time"]}</strong> - {event["title"]} ({event["type"]})'
                                html += '</div>'
                            
                        html += '</div>'
                        
                        # Render the HTML
                        st.markdown(html, unsafe_allow_html=True)
            # Close the week container
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Event management section
        st.subheader("Ereignisse verwalten")
        
        tab1, tab2 = st.tabs(["Ereignis hinzufügen", "Ereignisse anzeigen/bearbeiten"])
        
        with tab1:
            with st.form("add_event_form"):
                event_date = st.date_input("Datum", datetime.now())
                event_title = st.text_input("Titel der Veranstaltung")
                # Speichere die ausgewählte Zeit in einer Session-Variable, um sie zu erhalten
                if 'selected_event_time' not in st.session_state:
                    st.session_state.selected_event_time = datetime.now().time()
                event_time = st.time_input("Time", st.session_state.selected_event_time)
                # Aktualisiere die gespeicherte Zeit
                st.session_state.selected_event_time = event_time
                
                event_type = st.selectbox(
                    "Titel der Veranstaltung",
                    ["Studiensitzung", "Vorlesung", "Prüfung", "Fällige Aufgabe", "Gruppenbesprechung", "Sonstiges"]
                )
                
                # Color mapping for event types
                color_map = {
                    "Studiensitzung": "#ffcccc",  # Light red
                    "Vorlesung": "#ccffcc",        # Light green
                    "Prüfung": "#ffaaaa",           # Darker red
                    "Fällige Aufgabe": "#ffffcc", # Light yellow
                    "Gruppenbesprechung": "#ccccff",  # Light blue
                    "Sonstiges": "#f0f0f0"           # Light grey
                }
                
                submit_button = st.form_submit_button("Event hinzufügen")
                
                if submit_button and event_title:
                    # Stelle sicher, dass die Zeit im richtigen Format ist
                    time_str = event_time.strftime("%H:%M")
                    
                    new_event = {
                        'date': event_date.strftime("%Y-%m-%d"),
                        'title': event_title,
                        'time': time_str,
                        'type': event_type,
                        'color': color_map[event_type],
                        'user_id': user_id
                    }
                    
                    # Speichere das Event in der Datenbank
                    event_id = save_calendar_event(user_id, new_event)
                    if event_id:
                        # Füge ID zum Event hinzu und speichere es im Session State
                        new_event['id'] = event_id
                        st.session_state.calendar_events.append(new_event)
                        st.success(f"Event '{event_title}' added on {event_date.strftime('%Y-%m-%d')} at {time_str}")
                        st.rerun()
                    else:
                        st.error("Ereignis konnte nicht in der Datenbank gespeichert werden.")
        
        with tab2:
            if not st.session_state.calendar_events:
                st.info("Noch keine Veranstaltungen geplant.")
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
                                if st.button("Löschen", key=f"del_{date}_{i}"):
                                    # Lösche das Event aus der Datenbank
                                    if 'id' in event and delete_calendar_event(event['id']):
                                        st.session_state.calendar_events.remove(event)
                                        st.success(f"Ereignis '{event['title']}' gelöscht.")
                                        st.rerun()
                                    else:
                                        st.error("Ereignis konnte nicht aus der Datenbank gelöscht werden.")
    
    # Google Calendar Sync Tab
    with cal_tab2:
        display_google_calendar_sync(user_id)


# Function to integrate with your database later
def save_events_to_db(user_id, events):
    """Speichern von Ereignissen in der Datenbank - Platzhalter für eine zukünftige Implementierung"""
    # This will be implemented when you're ready to connect to your database
    pass

# Function to load events from your database later
def load_events_from_db(user_id):
    """Laden von Ereignissen aus der Datenbank - Platzhalter für eine zukünftige Implementierung"""
    # This will be implemented when you're ready to connect to your database
    return []

# To integrate with your main app, you can add this to your dashboard.py navigation
# or create a new file called calendar.py with this code and import it in your main app
