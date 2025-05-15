import streamlit as st
import os
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Es gab Probleme mit der Synchronisation von Events mit der Google Calendar API
# Hierfür wurde ChatGPT (OpenAI, 2025) verwendet, um Error-Handling und konsistentere Funktionen zu implementieren

# Importiere die benötigten Bibliotheken für Google Calendar API
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Importiere unsere Module aus dem Datenbankmanager
from database_manager import get_calendar_events, save_calendar_event, update_calendar_event

# Lade Umgebungsvariablen
load_dotenv()

# Google Calendar API Konfiguration
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Client ID und Secret aus Umgebungsvariablen laden
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# Farbzuordnung zwischen StudyBuddy und Google Calendar
EVENT_TYPE_COLOR_MAP = {
    "Lern-Session": "7",    # Hellgrün
    "Vorlesung": "2",          # Blau
    "Prüfung": "11",            # Rot
    "Aufgabe fällig": "5",   # Gelb
    "Gruppen-Meeting": "9",    # Lila
    "Andere": "8"             # Grau
}

# Google Calendar Farben zu StudyBuddy Farben
GOOGLE_TO_STUDYBUDDY_COLORS = {
    "7": "#ccffcc",  # Hellgrün - Lern-Session
    "2": "#ccccff",  # Blau - Vorlesung
    "11": "#ffaaaa", # Rot - Prüfung
    "5": "#ffffcc",  # Gelb - Abgabe fällig
    "9": "#ccccff",  # Lila - Gruppen-Meeting
    "8": "#f0f0f0"   # Grau - Andere
}

# Google Calendar Farben zu StudyBuddy Event-Typen
GOOGLE_COLOR_TO_EVENT_TYPE = {
    "7": "Lern-Session",
    "2": "Vorlesung",
    "11": "Prüfung",
    "5": "Aufgabe fällig",
    "9": "Gruppen-Meeting",
    "8": "Andere"
}

# Speichert die Google Credentials im Streamlit Session State.
def save_credentials_to_session(creds):
    # Speichere Credentials im Session State
    st.session_state.google_credentials = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
        "expiry": creds.expiry.isoformat() if creds.expiry else None
    }
    return True

#Entfernt die Google Credentials aus dem Session State.
def reset_credentials():
    if 'google_credentials' in st.session_state:
        del st.session_state.google_credentials
    return True
# Authentifiziert mit Google Calendar API und gibt Credentials zurück.
# Verwendet Credentials aus dem Streamlit Session State.
def get_google_credentials():
    creds = None
    
    # Versuche, Credentials aus dem Session State zu laden
    if 'google_credentials' in st.session_state:
        creds_data = st.session_state.google_credentials
    
        # Erstelle Credentials-Objekt aus den gespeicherten Daten
        creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
        
        # Prüfe, ob die Credentials gültig sind
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Aktualisiere die Credentials im Session State
            save_credentials_to_session(creds)
    
    # Wenn keine gültigen Credentials verfügbar sind, Benutzer anmelden lassen
    if not creds or not creds.valid:
        # Verwende Umgebungsvariablen für Client ID und Secret
        # Debugging: Prüfe ob Umgebungsvariablen gesetzt sind
        if not CLIENT_ID or not CLIENT_SECRET:
            st.error("Client ID oder Client Secret nicht in Umgebungsvariablen gefunden")
            return None
        
        # Konfiguration für den OAuth-Flow
        client_config = {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost:8502"]  # Anderer Port als Streamlit um Konflikete zu vermeiden
            }
        }
        
        try:
            # OAuth-Flow erstellen
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            
            # Authentifizierung über lokalen Server
            st.info("Ein Browser-Fenster wird geöffnet. Bitte melde dich bei Google an und erteile die Berechtigungen.")
            creds = flow.run_local_server(port=8502)
            
            # Speichere die neuen Credentials im Session State
            save_credentials_to_session(creds)
        except Exception as e:
            # Wenn ein Fehler auftritt, zeige eine Fehlermeldung an
            st.error(f"Fehler bei der Authentifizierung: {str(e)}")
            return None
    return creds

# Google Kalender Service erstellen
def get_google_calendar_service():
    creds = get_google_credentials()
    service = build('calendar', 'v3', credentials=creds)
    return service

# Ruft alle verfügbaren Google Kalender des Benutzers ab
def get_google_calendars():
    service = get_google_calendar_service()
    try:
        # Liste der Kalender abrufen
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])
        return calendars
    except HttpError as error:
        # Fehler beim Abrufen der Kalender (zb Verbindung abgebrochen)
        st.error(f"Fehler beim Abrufen der Google Kalender: {error}")
        return []

# Erstellt ein neues Ereignis im Google Kalender
def create_google_event(service, calendar_id, event_data):
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
    
    # Google Calendar Event erstellen im Format wie es die API erwartet
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
        # Metadaten hinzufügen, um StudyBuddy-Events zu identifizieren, wichtig bei der Synchronisation
        'extendedProperties': {
            'private': {
                'studybuddy_id': str(event_data.get('id', '')),
                'studybuddy_type': event_type
            }
        }
    }
    
    try:
        # Event in den Google Kalender einfügen
        event = service.events().insert(calendarId=calendar_id, body=event).execute()
        return event['id']
    except HttpError as error:
        # Fehler beim Erstellen des Events (zb Verbindung abgebrochen)
        st.error(f"Fehler beim Erstellen des Google Calendar Events: {error}")
        return None

# Aktualisiert ein bestehendes Ereignis im Google Kalender.
def update_google_event(service, calendar_id, google_event_id, event_data):
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
        
        # Event aktualisieren, im Format wie es die API erwartet
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
        # Fehler beim Aktualisieren des Events (zb Verbindung abgebrochen)
        st.error(f"Fehler beim Aktualisieren des Google Calendar Events: {error}")
        return None

# Löscht ein Ereignis aus dem Google Kalender
def delete_google_event(service, calendar_id, google_event_id):
    try:
        service.events().delete(calendarId=calendar_id, eventId=google_event_id).execute()
        return True
    except HttpError as error:
        # Fehler beim Löschen des Events (zb Verbindung abgebrochen)
        st.error(f"Fehler beim Löschen des Google Calendar Events: {error}")
        return False

# Synchronisiert StudyBuddy-Events zu Google Calendar.
def sync_to_google(user_id, calendar_id):
    service = get_google_calendar_service()
    
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
        # Fehler beim Synchronisieren (zb Verbindung abgebrochen)
        return False, f"Fehler bei der Synchronisation: {error}"

# Importiert Google Calendar-Events zu StudyBuddy
def sync_from_google(user_id, calendar_id):
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
        # Damit der Kalender aktualisiert wird, wird die Seite neu geladen
        st.rerun()
        return True, message
    
    except HttpError as error:
        # Fehler beim Importieren (zb Verbindung abgebrochen)
        return False, f"Fehler beim Import: {error}"

# Prüft, ob automatische Synchronisation aktiviert ist und führt sie bei Bedarf aus
def check_auto_sync(user_id):
    if st.session_state.get('auto_sync', False) and st.session_state.get('selected_calendar_id'):
        # Führe die Synchronisation in beide Richtungen durch
        sync_to_google(user_id, st.session_state.selected_calendar_id)
        sync_from_google(user_id, st.session_state.selected_calendar_id)
        
# Frontend für Google Calendar Synchronisation
def display_google_calendar_sync(user_id):
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
    is_authenticated = 'google_credentials' in st.session_state
    
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
            reset_credentials()
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
        # sync von StudyBuddy zu Google
        if st.button("StudyBuddy → Google", use_container_width=True):
            with st.spinner("Synchronisiere Events zu Google Calendar..."):
                success, message = sync_to_google(user_id, calendar_id)
                if success:
                    st.success(message)
                else:
                    st.error(message)
    
    with col2:
        # Import von Google zu StudyBuddy
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
        # Aufruf der Funktion zum Zurücksetzen der Verbindung
        reset_credentials()
        st.success("Verbindung zurückgesetzt. Bitte verbinde dich erneut.")
        # Wenn die Verbindung zurückgesetzt wird, wird die Seite neu geladen um Fehler zu vermeiden
        st.rerun()


