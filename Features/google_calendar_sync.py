# google_calendar_sync.py
import streamlit as st
import os
import json
from datetime import datetime, timedelta
import pytz
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from database_manager import get_calendar_events, save_calendar_event, delete_calendar_event, update_calendar_event
from dotenv import load_dotenv
from pathlib import Path

# Lade Umgebungsvariablen
load_dotenv()

# Google Calendar API Konfiguration
SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = 'credentials.json'

# Client ID und Secret aus Umgebungsvariablen laden
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# Token-Informationen aus Umgebungsvariablen laden
GOOGLE_ACCESS_TOKEN = os.getenv("GOOGLE_ACCESS_TOKEN")
GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")
GOOGLE_TOKEN_URI = os.getenv("GOOGLE_TOKEN_URI", "https://oauth2.googleapis.com/token")
GOOGLE_EXPIRY = os.getenv("GOOGLE_EXPIRY")

# Farbzuordnung zwischen StudyBuddy und Google Calendar
EVENT_TYPE_COLOR_MAP = {
    "Study Session": "7",    # Hellgrün
    "Lecture": "2",          # Blau
    "Exam": "11",            # Rot
    "Assignment Due": "5",   # Gelb
    "Group Meeting": "9",    # Lila
    "Other": "8"             # Grau
}

# Google Calendar Farben zu StudyBuddy Farben
GOOGLE_TO_STUDYBUDDY_COLORS = {
    "7": "#ccffcc",  # Hellgrün - Study Session
    "2": "#ccccff",  # Blau - Lecture
    "11": "#ffaaaa", # Rot - Exam
    "5": "#ffffcc",  # Gelb - Assignment Due
    "9": "#ccccff",  # Lila - Group Meeting
    "8": "#f0f0f0"   # Grau - Other
}

# Google Calendar Farben zu StudyBuddy Event-Typen
GOOGLE_COLOR_TO_EVENT_TYPE = {
    "7": "Study Session",
    "2": "Lecture",
    "11": "Exam",
    "5": "Assignment Due",
    "9": "Group Meeting",
    "8": "Other"
}

def update_env_tokens(creds):
    """
    Aktualisiert die Token-Informationen in der .env-Datei.
    Dies ist eine einfache Implementierung - in der Praxis solltest du eine robustere Lösung verwenden.
    """
    try:
        # Lese die aktuelle .env-Datei
        with open('.env', 'r') as file:
            lines = file.readlines()
        
        # Aktualisierte Zeilen
        updated_lines = []
        token_updated = refresh_token_updated = expiry_updated = False
        
        for line in lines:
            if line.startswith('GOOGLE_ACCESS_TOKEN='):
                updated_lines.append(f'GOOGLE_ACCESS_TOKEN={creds.token}\n')
                token_updated = True
            elif line.startswith('GOOGLE_REFRESH_TOKEN=') and creds.refresh_token:
                updated_lines.append(f'GOOGLE_REFRESH_TOKEN={creds.refresh_token}\n')
                refresh_token_updated = True
            elif line.startswith('GOOGLE_EXPIRY='):
                updated_lines.append(f'GOOGLE_EXPIRY={creds.expiry.isoformat()}\n')
                expiry_updated = True
            else:
                updated_lines.append(line)
        
        # Füge fehlende Token-Informationen hinzu
        if not token_updated:
            updated_lines.append(f'GOOGLE_ACCESS_TOKEN={creds.token}\n')
        if not refresh_token_updated and creds.refresh_token:
            updated_lines.append(f'GOOGLE_REFRESH_TOKEN={creds.refresh_token}\n')
        if not expiry_updated and creds.expiry:
            updated_lines.append(f'GOOGLE_EXPIRY={creds.expiry.isoformat()}\n')
        
        # Schreibe die aktualisierte .env-Datei
        with open('.env', 'w') as file:
            file.writelines(updated_lines)
            
        return True
    except Exception as e:
        st.error(f"Fehler beim Aktualisieren der .env-Datei: {str(e)}")
        return False

def reset_env_tokens():
    """
    Entfernt die Token-Informationen aus der .env-Datei.
    """
    try:
        # Lese die aktuelle .env-Datei
        with open('.env', 'r') as file:
            lines = file.readlines()
        
        # Entferne Token-Zeilen
        updated_lines = [line for line in lines if not (
            line.startswith('GOOGLE_ACCESS_TOKEN=') or 
            line.startswith('GOOGLE_REFRESH_TOKEN=') or 
            line.startswith('GOOGLE_EXPIRY=')
        )]
        
        # Schreibe die aktualisierte .env-Datei
        with open('.env', 'w') as file:
            file.writelines(updated_lines)
            
        return True
    except Exception as e:
        st.error(f"Fehler beim Zurücksetzen der Token in der .env-Datei: {str(e)}")
        return False

def get_google_credentials():
    """
    Authentifiziert mit Google Calendar API und gibt Credentials zurück.
    Verwendet Token-Informationen aus .env-Datei statt token.json
    """
    creds = None
    
    # Versuche, Token aus Umgebungsvariablen zu laden
    if GOOGLE_ACCESS_TOKEN and GOOGLE_REFRESH_TOKEN:
        token_data = {
            "token": GOOGLE_ACCESS_TOKEN,
            "refresh_token": GOOGLE_REFRESH_TOKEN,
            "token_uri": GOOGLE_TOKEN_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scopes": SCOPES,
            "expiry": GOOGLE_EXPIRY
        }
        
        try:
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        except Exception as e:
            st.error(f"Fehler beim Laden der Token-Informationen aus .env: {str(e)}")
            creds = None
    
    # Wenn keine gültigen Anmeldeinformationen verfügbar sind, Benutzer anmelden lassen
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Aktualisierte Token in .env speichern
                update_env_tokens(creds)
            except Exception as e:
                st.error(f"Fehler beim Aktualisieren des Tokens: {str(e)}")
                creds = None
        else:
            # Verwende Umgebungsvariablen statt credentials.json
            if not CLIENT_ID or not CLIENT_SECRET:
                st.error("Client ID oder Client Secret nicht in .env-Datei gefunden")
                return None
                
            flow = InstalledAppFlow.from_client(
                {"web": {
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost:8501/"]
                }},
                SCOPES
            )
            creds = flow.run_local_server(port=8501)
            
            # Neue Token in .env speichern
            update_env_tokens(creds)
    
    return creds

def get_google_calendar_service():
    """
    Erstellt einen Google Calendar API Service.
    """
    creds = get_google_credentials()
    if not creds:
        return None
        
    try:
        service = build('calendar', 'v3', credentials=creds)
        return service
    except Exception as e:
        st.error(f"Fehler beim Erstellen des Google Calendar Service: {str(e)}")
        return None

def get_google_calendars():
    """
    Ruft alle verfügbaren Google Kalender des Benutzers ab.
    """
    service = get_google_calendar_service()
    if not service:
        return []
        
    try:
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])
        return calendars
    except HttpError as error:
        st.error(f"Fehler beim Abrufen der Google Kalender: {error}")
        return []

def create_google_event(service, calendar_id, event_data):
    """
    Erstellt ein neues Ereignis im Google Kalender.
    """
    # Datum und Uhrzeit formatieren
    date_str = event_data['date']
    time_str = event_data['time']
    
    # Start- und Endzeit (Standarddauer: 1 Stunde)
    start_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    end_datetime = start_datetime + timedelta(hours=1)
    
    # Zeitzone des Benutzers
    timezone = pytz.timezone('Europe/Berlin')
    
    # Event-Typ bestimmen und entsprechende Farbe zuweisen
    event_type = event_data.get('type', 'Other')
    color_id = EVENT_TYPE_COLOR_MAP.get(event_type, "8")
    
    # Google Calendar Event erstellen
    event = {
        'summary': event_data['title'],
        'description': f"StudyBuddy Event - Typ: {event_type}",
        'start': {
            'dateTime': start_datetime.isoformat(),
            'timeZone': timezone.zone,
        },
        'end': {
            'dateTime': end_datetime.isoformat(),
            'timeZone': timezone.zone,
        },
        'colorId': color_id,
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': 30},
            ],
        },
        # Metadaten hinzufügen, um StudyBuddy-Events zu identifizieren
        'extendedProperties': {
            'private': {
                'studybuddy_id': str(event_data.get('id', '')),
                'studybuddy_type': event_type
            }
        }
    }
    
    try:
        event = service.events().insert(calendarId=calendar_id, body=event).execute()
        return event['id']
    except HttpError as error:
        st.error(f"Fehler beim Erstellen des Google Calendar Events: {error}")
        return None

def update_google_event(service, calendar_id, google_event_id, event_data):
    """
    Aktualisiert ein bestehendes Ereignis im Google Kalender.
    """
    try:
        # Zuerst das bestehende Event abrufen
        event = service.events().get(calendarId=calendar_id, eventId=google_event_id).execute()
        
        # Datum und Uhrzeit formatieren
        date_str = event_data['date']
        time_str = event_data['time']
        
        # Start- und Endzeit (Standarddauer: 1 Stunde)
        start_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        end_datetime = start_datetime + timedelta(hours=1)
        
        # Zeitzone des Benutzers
        timezone = pytz.timezone('Europe/Berlin')
        
        # Event-Typ bestimmen und entsprechende Farbe zuweisen
        event_type = event_data.get('type', 'Other')
        color_id = EVENT_TYPE_COLOR_MAP.get(event_type, "8")
        
        # Event aktualisieren
        event['summary'] = event_data['title']
        event['description'] = f"StudyBuddy Event - Typ: {event_type}"
        event['start'] = {
            'dateTime': start_datetime.isoformat(),
            'timeZone': timezone.zone,
        }
        event['end'] = {
            'dateTime': end_datetime.isoformat(),
            'timeZone': timezone.zone,
        }
        event['colorId'] = color_id
        
        # Wenn extendedProperties nicht existiert, erstellen
        if 'extendedProperties' not in event:
            event['extendedProperties'] = {'private': {}}
        elif 'private' not in event['extendedProperties']:
            event['extendedProperties']['private'] = {}
            
        # StudyBuddy-Metadaten aktualisieren
        event['extendedProperties']['private']['studybuddy_id'] = str(event_data.get('id', ''))
        event['extendedProperties']['private']['studybuddy_type'] = event_type
        
        updated_event = service.events().update(
            calendarId=calendar_id,
            eventId=google_event_id,
            body=event
        ).execute()
        
        return updated_event['id']
    except HttpError as error:
        st.error(f"Fehler beim Aktualisieren des Google Calendar Events: {error}")
        return None

def delete_google_event(service, calendar_id, google_event_id):
    """
    Löscht ein Ereignis aus dem Google Kalender.
    """
    try:
        service.events().delete(calendarId=calendar_id, eventId=google_event_id).execute()
        return True
    except HttpError as error:
        st.error(f"Fehler beim Löschen des Google Calendar Events: {error}")
        return False

def sync_to_google(user_id, calendar_id):
    """
    Synchronisiert StudyBuddy-Events zu Google Calendar.
    """
    service = get_google_calendar_service()
    if not service:
        return False, "Keine Verbindung zu Google Calendar möglich."
    
    # Alle StudyBuddy-Events abrufen
    studybuddy_events = get_calendar_events(user_id)
    if not studybuddy_events:
        return True, "Keine Events zum Synchronisieren vorhanden."
    
    # Alle Google Calendar Events abrufen
    try:
        # Zeitraum für Abfrage (z.B. 1 Jahr zurück und 1 Jahr voraus)
        now = datetime.utcnow()
        time_min = (now - timedelta(days=365)).isoformat() + 'Z'
        time_max = (now + timedelta(days=365)).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        google_events = events_result.get('items', [])
        
        # Map erstellen, um Google Events mit StudyBuddy-ID zu finden
        google_events_map = {}
        for event in google_events:
            if 'extendedProperties' in event and 'private' in event['extendedProperties']:
                studybuddy_id = event['extendedProperties']['private'].get('studybuddy_id')
                if studybuddy_id:
                    google_events_map[studybuddy_id] = event['id']
        
        # Zähler für Statistik
        created = 0
        updated = 0
        skipped = 0
        
        # Für jedes StudyBuddy-Event
        for event in studybuddy_events:
            # Prüfen, ob das Event bereits in Google Calendar existiert
            google_event_id = google_events_map.get(str(event['id']))
            
            if google_event_id:
                # Event aktualisieren
                result = update_google_event(service, calendar_id, google_event_id, event)
                if result:
                    updated += 1
            else:
                # Neues Event erstellen
                result = create_google_event(service, calendar_id, event)
                if result:
                    created += 1
                else:
                    skipped += 1
        
        message = f"Synchronisation abgeschlossen: {created} erstellt, {updated} aktualisiert, {skipped} übersprungen."
        return True, message
    
    except HttpError as error:
        return False, f"Fehler bei der Synchronisation: {error}"

def sync_from_google(user_id, calendar_id):
    """
    Synchronisiert Google Calendar-Events zu StudyBuddy.
    """
    service = get_google_calendar_service()
    if not service:
        return False, "Keine Verbindung zu Google Calendar möglich."
    
    # Alle StudyBuddy-Events abrufen und in Map speichern
    studybuddy_events = get_calendar_events(user_id)
    studybuddy_events_map = {str(event['id']): event for event in studybuddy_events}
    
    # Alle Google Calendar Events abrufen
    try:
        # Zeitraum für Abfrage (z.B. 1 Jahr zurück und 1 Jahr voraus)
        now = datetime.utcnow()
        time_min = (now - timedelta(days=365)).isoformat() + 'Z'
        time_max = (now + timedelta(days=365)).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        google_events = events_result.get('items', [])
        
        # Zähler für Statistik
        created = 0
        updated = 0
        skipped = 0
        
        # Für jedes Google Calendar Event
        for google_event in google_events:
            # StudyBuddy-ID aus den erweiterten Eigenschaften extrahieren
            studybuddy_id = None
            if 'extendedProperties' in google_event and 'private' in google_event['extendedProperties']:
                studybuddy_id = google_event['extendedProperties']['private'].get('studybuddy_id')
            
            # Wenn es ein gelöschtes Event ist, überspringen
            if google_event.get('status') == 'cancelled':
                continue
                
            # Wenn es kein Start-Datum/Zeit hat, überspringen
            if 'start' not in google_event or 'dateTime' not in google_event['start']:
                skipped += 1
                continue
                
            # Datum und Zeit extrahieren
            start_datetime = datetime.fromisoformat(google_event['start']['dateTime'].replace('Z', '+00:00'))
            date_str = start_datetime.strftime("%Y-%m-%d")
            time_str = start_datetime.strftime("%H:%M")
                
            # Event-Typ und Farbe bestimmen
            color_id = google_event.get('colorId', '8')
            event_type = GOOGLE_COLOR_TO_EVENT_TYPE.get(color_id, 'Other')
            color = GOOGLE_TO_STUDYBUDDY_COLORS.get(color_id, '#f0f0f0')
                
            # Event-Daten vorbereiten
            event_data = {
                'title': google_event.get('summary', 'Untitled Event'),
                'date': date_str,
                'time': time_str,
                'type': event_type,
                'color': color,
                'user_id': user_id
            }
                
            if studybuddy_id and studybuddy_id in studybuddy_events_map:
                # Event existiert bereits in StudyBuddy -> aktualisieren
                result = update_calendar_event(int(studybuddy_id), event_data)
                if result:
                    updated += 1
            else:
                # Neues Event in StudyBuddy erstellen
                # Nur Events importieren, die nicht aus StudyBuddy stammen und keine studybuddy_id haben
                if not studybuddy_id:
                    new_id = save_calendar_event(user_id, event_data)
                    if new_id:
                        created += 1
                                        
                        # Aktualisiere das Google-Event mit der neuen StudyBuddy-ID
                        if 'extendedProperties' not in google_event:
                            google_event['extendedProperties'] = {'private': {}}
                        elif 'private' not in google_event['extendedProperties']:
                            google_event['extendedProperties']['private'] = {}
                            
                        google_event['extendedProperties']['private']['studybuddy_id'] = str(new_id)
                        
                        service.events().update(
                            calendarId=calendar_id,
                            eventId=google_event['id'],
                            body=google_event
                        ).execute()
        
        message = f"Import abgeschlossen: {created} erstellt, {updated} aktualisiert, {skipped} übersprungen."
        return True, message
    
    except HttpError as error:
        return False, f"Fehler beim Import: {error}"

def delete_event_both(user_id, event_id, calendar_id):
    """
    Löscht ein Event sowohl aus StudyBuddy als auch aus Google Calendar.
    """
    # Zuerst aus StudyBuddy löschen
    if not delete_calendar_event(event_id):
        return False, "Fehler beim Löschen des Events aus StudyBuddy."
    
    # Dann aus Google Calendar löschen
    service = get_google_calendar_service()
    if not service:
        return True, "Event aus StudyBuddy gelöscht, aber keine Verbindung zu Google Calendar möglich."
    
    # Alle Google Calendar Events abrufen
    try:
        # Zeitraum für Abfrage (z.B. 1 Jahr zurück und 1 Jahr voraus)
        now = datetime.utcnow()
        time_min = (now - timedelta(days=365)).isoformat() + 'Z'
        time_max = (now + timedelta(days=365)).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        google_events = events_result.get('items', [])
        
        # Suche nach dem Event mit der entsprechenden StudyBuddy-ID
        for google_event in google_events:
            if 'extendedProperties' in google_event and 'private' in google_event['extendedProperties']:
                studybuddy_id = google_event['extendedProperties']['private'].get('studybuddy_id')
                if studybuddy_id == str(event_id):
                    # Event in Google Calendar löschen
                    if delete_google_event(service, calendar_id, google_event['id']):
                        return True, "Event erfolgreich aus StudyBuddy und Google Calendar gelöscht."
                    else:
                        return True, "Event aus StudyBuddy gelöscht, aber Fehler beim Löschen aus Google Calendar."
        
        return True, "Event aus StudyBuddy gelöscht, aber nicht in Google Calendar gefunden."
    
    except HttpError as error:
        return True, f"Event aus StudyBuddy gelöscht, aber Fehler beim Zugriff auf Google Calendar: {error}"

def display_google_calendar_sync(user_id):
    """
    Zeigt die Google Calendar Synchronisations-Oberfläche an.
    """
    st.subheader("Google Calendar Synchronisation")
    
    # Prüfen, ob Client ID und Secret vorhanden sind
    if not CLIENT_ID or not CLIENT_SECRET:
        st.error("""
        Um Google Calendar zu nutzen, benötigst du eine .env Datei mit den entsprechenden Zugangsdaten. 
        Bitte erstelle eine .env Datei mit folgenden Einträgen:
        
        GOOGLE_CLIENT_ID=deine_client_id
        GOOGLE_CLIENT_SECRET=dein_client_secret
        """)
        return
    
    # Prüfen, ob bereits authentifiziert
    is_authenticated = GOOGLE_ACCESS_TOKEN and GOOGLE_REFRESH_TOKEN
    
    if not is_authenticated:
        st.warning("Du bist noch nicht mit Google Calendar verbunden.")
        if st.button("Mit Google Calendar verbinden"):
            with st.spinner("Verbindung zu Google wird hergestellt..."):
                creds = get_google_credentials()
                if creds:
                    st.success("Erfolgreich mit Google Calendar verbunden!")
                    st.rerun()
                else:
                    st.error("Verbindung fehlgeschlagen. Bitte versuche es erneut.")
        return
    
    # Google Kalender abrufen
    calendars = get_google_calendars()
    
    if not calendars:
        st.warning("Keine Google Kalender gefunden oder Fehler beim Abrufen der Kalender.")
        if st.button("Verbindung zurücksetzen"):
            reset_env_tokens()
            st.success("Verbindung zurückgesetzt. Bitte verbinde dich erneut.")
            st.rerun()
        return
    
    # Kalender-Auswahl
    calendar_options = {cal['summary']: cal['id'] for cal in calendars}
    selected_calendar = st.selectbox(
        "Wähle einen Google Kalender für die Synchronisation:",
        options=list(calendar_options.keys())
    )
    
    calendar_id = calendar_options[selected_calendar]
    
    # Speichere die ausgewählte Kalender-ID in der Session
    if 'selected_calendar_id' not in st.session_state:
        st.session_state.selected_calendar_id = calendar_id
    else:
        st.session_state.selected_calendar_id = calendar_id
    
    # Synchronisationsoptionen
    st.write("### Synchronisationsoptionen")
    
    # Automatische Synchronisation
    auto_sync = st.checkbox("Automatische Synchronisation aktivieren", 
                           value=st.session_state.get('auto_sync', False))
    
    if auto_sync != st.session_state.get('auto_sync', False):
        st.session_state.auto_sync = auto_sync
        st.success(f"Automatische Synchronisation {'aktiviert' if auto_sync else 'deaktiviert'}.")
    
    # Manuelle Synchronisation
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("StudyBuddy → Google", use_container_width=True):
            with st.spinner("Synchronisiere Events zu Google Calendar..."):
                success, message = sync_to_google(user_id, calendar_id)
                if success:
                    st.success(message)
                else:
                    st.error(message)
    
    with col2:
        if st.button("Google → StudyBuddy", use_container_width=True):
            with st.spinner("Importiere Events von Google Calendar..."):
                success, message = sync_from_google(user_id, calendar_id)
                if success:
                    st.success(message)
                else:
                    st.error(message)
    
    # Verbindung zurücksetzen
    st.write("### Verbindungseinstellungen")
    if st.button("Verbindung zu Google Calendar zurücksetzen"):
        reset_env_tokens()
        st.success("Verbindung zurückgesetzt. Bitte verbinde dich erneut.")
        st.rerun()

def check_auto_sync(user_id):
    """
    Prüft, ob automatische Synchronisation aktiviert ist und führt sie bei Bedarf aus.
    """
    if st.session_state.get('auto_sync', False) and st.session_state.get('selected_calendar_id'):
        # Führe die Synchronisation in beide Richtungen durch
        sync_to_google(user_id, st.session_state.selected_calendar_id)
        sync_from_google(user_id, st.session_state.selected_calendar_id)
