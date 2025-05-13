import streamlit as st
import datetime
import calendar
from datetime import datetime, timedelta
import random
from database_manager import get_calendar_events, save_calendar_event, delete_calendar_event
from google_calendar_sync import display_google_calendar_sync, check_auto_sync

# Streamlit Frontend
def display_calendar(user_id):
    st.title("Studienkalender")
    
    # Tab-System für Kalender und Google Sync
    cal_tab1, cal_tab2 = st.tabs(["Kalender", "Google Kalender Sync"])
    
    with cal_tab1:
        # Lade Ereignisse aus der Datenbank
        db_events = get_calendar_events(user_id)
        st.session_state.calendar_events = db_events if db_events else []
        
        # Prüfe auf automatische Synchronisation
        check_auto_sync(user_id)
        
        # Calendar navigation
        col1, col2, col3 = st.columns([2, 3, 2])
        
        with col1:
            # Aktuelle DAtum bestimmen
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
        
        # Kalender erstellen
        cal = calendar.monthcalendar(st.session_state.calendar_year, st.session_state.calendar_month)
        
        # Custom CSS Styling für Kalender. Übernommen aus ChatGPT
        weekdays = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
        cols = st.columns(7)
        for i, col in enumerate(cols):
            with col:
                st.markdown(f"<div style='text-align: center; font-weight: bold;'>{weekdays[i]}</div>", unsafe_allow_html=True)
        
        # Design Elemente und Hover Effekte für unseren Kalender von ChatGPT kopiert
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
        
        # Kalender anzeigen
        for week_idx, week in enumerate(cal):
            cols = st.columns(7)
            for i, day in enumerate(week):
                with cols[i]:
                    if day == 0:
                        # Leere Zeile für Tage, die nicht im Monat sind. Übernommen von ChatGPT
                        st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
                    else:
                        # Datum erstellen
                        current_date = datetime(st.session_state.calendar_year, st.session_state.calendar_month, day)
                        date_str = current_date.strftime("%Y-%m-%d")
                        
                        # Prüfen ob es Einträge für diesen Tag gibt
                        day_events = [e for e in st.session_state.calendar_events if e['date'] == date_str]
                        
                        # HTML für den Tag erstellen, übernommen von ChatGPT
                        html = f'<div class="day-cell{" day-cell-events" if day_events else ""}">'
                        html += f'<div class="day-number">{day}</div>'
                        
                        # Container für jedes Event und Overflow verhidnern, übernommen von ChatGPT
                        if day_events:
                            html += '<div class="events-container">'
                            
                            # Preview hinzufügen, aus ChatGPT übernommen
                            for event in day_events:
                                html += f'<div class="event-mini" style="background-color: {event["color"]};">'
                                html += f'{event["time"]} {event["title"][:10]}...'
                                html += '</div>'
                            
                            html += '</div>'
                            
                            # Inhalt hinzufügen, der beim Hover angezeigt wird, aus ChatGPT übernommen
                            html += '<hr style="margin: 3px 0;">'
                            for event in day_events:
                                html += f'<div class="event-full" style="background-color: {event["color"]};">'
                                html += f'<strong>{event["time"]}</strong> - {event["title"]} ({event["type"]})'
                                html += '</div>'
                            
                        html += '</div>'
                        
                        # Rendern vom HTML
                        st.markdown(html, unsafe_allow_html=True)
            # Wochen Container schließen
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Verwaltung der einzelnen Events
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
                
                # VErschiedene Farben für die Events, damit der Nutzer die auseinadnerhalten kann
                color_map = {
                    "Studiensitzung": "#ffcccc",
                    "Vorlesung": "#ccffcc", 
                    "Prüfung": "#ffaaaa",      
                    "Fällige Aufgabe": "#ffffcc", 
                    "Gruppenbesprechung": "#ccccff", 
                    "Sonstiges": "#f0f0f0"     
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
                # Events nach Datum gruppieren
                from collections import defaultdict
                events_by_date = defaultdict(list)
                
                for event in st.session_state.calendar_events:
                    date_obj = datetime.strptime(event['date'], "%Y-%m-%d")
                    formatted_date = date_obj.strftime("%A, %B %d, %Y")
                    events_by_date[formatted_date].append(event)
                
                # DAtums chronologisch sortieren
                sorted_dates = sorted(events_by_date.keys(),
                                      key=lambda x: datetime.strptime(x, "%A, %B %d, %Y"))
                
                # Einträge nach DAtum sortiert anzeigen
                for date in sorted_dates:
                    with st.expander(date):
                        for i, event in enumerate(events_by_date[date]):
                            col1, col2 = st.columns([5, 1])
                            with col1:
                                # styling von Chatgpt empfohlen
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
    
    # Google Calendar Sync Tab. Import aus dem google_calendar_sync.py Modul
    with cal_tab2:
        display_google_calendar_sync(user_id)