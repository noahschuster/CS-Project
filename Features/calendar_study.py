import streamlit as st
import calendar
from datetime import datetime
from database_manager import get_calendar_events, save_calendar_event, delete_calendar_event

def display_calendar(user_id):
    st.title("Study Calendar")
    
    # Load events from database
    if 'calendar_events' not in st.session_state:
        st.session_state.calendar_events = get_calendar_events(user_id) or []
    
    # Calendar navigation - simplified layout
    col1, col2, col3 = st.columns([1, 2, 1])
    
    # Initialize month/year if not in session state
    if 'calendar_month' not in st.session_state:
        st.session_state.calendar_month = datetime.now().month
    if 'calendar_year' not in st.session_state:
        st.session_state.calendar_year = datetime.now().year
            
    # Navigation buttons and header
    with col1:
        if st.button("◀"):
            st.session_state.calendar_month -= 1
            if st.session_state.calendar_month < 1:
                st.session_state.calendar_month = 12
                st.session_state.calendar_year -= 1
    with col3:
        if st.button("▶"):
            st.session_state.calendar_month += 1
            if st.session_state.calendar_month > 12:
                st.session_state.calendar_month = 1
                st.session_state.calendar_year += 1
    with col2:
        st.subheader(f"{calendar.month_name[st.session_state.calendar_month]} {st.session_state.calendar_year}")
    
    # Create calendar grid
    cal = calendar.monthcalendar(st.session_state.calendar_year, st.session_state.calendar_month)
    
    # CSS for calendar styling
    st.markdown("""
    <style>
    .day-cell {background-color:#f5f5f5; border-radius:5px; padding:5px; height:80px; position:relative; overflow:hidden;}
    .day-cell-events {background-color:#e6f3ff;}
    .day-cell-events:hover {position:absolute; z-index:1000; width:250px; height:auto; min-height:80px; 
                           max-height:300px; overflow-y:auto; background-color:white; box-shadow:0 0 10px rgba(0,0,0,0.2);}
    .day-number {font-weight:bold; text-align:center; margin-bottom:3px;}
    .event-mini {font-size:0.7em; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; 
                margin-bottom:1px; padding:1px; border-radius:2px;}
    .event-full {display:none; font-size:0.8em; margin-bottom:3px; padding:3px; border-radius:3px;}
    .day-cell-events:hover .event-mini {display:none;}
    .day-cell-events:hover .event-full {display:block;}
    .events-container {max-height:55px; overflow:hidden;}
    </style>
    """, unsafe_allow_html=True)
    
    # Display weekday headers
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    cols = st.columns(7)
    for i, col in enumerate(cols):
        with col:
            st.markdown(f"<div style='text-align:center; font-weight:bold;'>{weekdays[i]}</div>", unsafe_allow_html=True)

    # Display calendar days
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day == 0:
                    st.markdown("<div style='height:80px;'></div>", unsafe_allow_html=True)
                else:
                    # Create date string for this day
                    current_date = datetime(st.session_state.calendar_year, st.session_state.calendar_month, day)
                    date_str = current_date.strftime("%Y-%m-%d")
                    
                    # Find events for this day
                    day_events = [e for e in st.session_state.calendar_events if e['date'] == date_str]
                    
                    # Build HTML for this day
                    has_events = " day-cell-events" if day_events else ""
                    html = f'<div class="day-cell{has_events}"><div class="day-number">{day}</div>'
                    
                    if day_events:
                        html += '<div class="events-container">'
                        for event in day_events:
                            html += f'<div class="event-mini" style="background-color:{event["color"]};">'
                            html += f'{event["time"]} {event["title"][:10]}...</div>'
                        html += '</div><hr style="margin:3px 0;">'
                        
                        for event in day_events:
                            html += f'<div class="event-full" style="background-color:{event["color"]};">'
                            html += f'<strong>{event["time"]}</strong> - {event["title"]} ({event["type"]})</div>'
                    
                    html += '</div>'
                    st.markdown(html, unsafe_allow_html=True)
    
    # Event management - tabs
    st.subheader("Manage Events")
    tab1, tab2 = st.tabs(["Add Event", "View/Edit Events"])
    
    # Color mapping for event types
    color_map = {
        "Study Session": "#ffcccc", "Lecture": "#ccffcc", "Exam": "#ffaaaa",
        "Assignment Due": "#ffffcc", "Group Meeting": "#ccccff", "Other": "#f0f0f0"
    }
    
    # Add Event tab
    with tab1:
        with st.form("add_event_form"):
            event_date = st.date_input("Date", datetime.now())
            event_title = st.text_input("Event Title")
            event_time = st.time_input("Time", datetime.now().time())
            event_type = st.selectbox("Event Type", list(color_map.keys()))
            
            if st.form_submit_button("Add Event") and event_title:
                new_event = {
                    'date': event_date.strftime("%Y-%m-%d"),
                    'title': event_title,
                    'time': event_time.strftime("%H:%M"),
                    'type': event_type,
                    'color': color_map[event_type],
                    'user_id': user_id
                }
                
                # Save to database
                event_id = save_calendar_event(user_id, new_event)
                if event_id:
                    new_event['id'] = event_id
                    st.session_state.calendar_events.append(new_event)
                    st.success(f"Event '{event_title}' added")
                    st.rerun()
                else:
                    st.error("Failed to save event")
    
    # View/Edit Events tab
    with tab2:
        if not st.session_state.calendar_events:
            st.info("No events scheduled yet.")
        else:
            # Group events by date
            from collections import defaultdict
            events_by_date = defaultdict(list)
            
            for event in st.session_state.calendar_events:
                date_obj = datetime.strptime(event['date'], "%Y-%m-%d")
                formatted_date = date_obj.strftime("%A, %B %d, %Y")
                events_by_date[formatted_date].append(event)
            
            # Sort dates and display events
            for date in sorted(events_by_date.keys(), 
                             key=lambda x: datetime.strptime(x, "%A, %B %d, %Y")):
                with st.expander(date):
                    for i, event in enumerate(events_by_date[date]):
                        col1, col2 = st.columns([5, 1])
                        with col1:
                            st.markdown(
                                f"""<div style='background-color:{event['color']}; padding:10px; 
                                border-radius:5px; margin-bottom:5px;'>
                                <strong>{event['time']}</strong> - {event['title']} ({event['type']})
                                </div>""", 
                                unsafe_allow_html=True
                            )
                        with col2:
                            if st.button("Delete", key=f"del_{date}_{i}"):
                                if 'id' in event and delete_calendar_event(event['id']):
                                    st.session_state.calendar_events.remove(event)
                                    st.success(f"Event deleted")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete event")
