import streamlit as st
import os
from streamlit_cookies_manager import EncryptedCookieManager
import sys
import subprocess

# Import unserer Module
from database_manager import (
    authenticate,
    add_user,
    log_session,
    generate_session_token,
    validate_session_token,
    init_db,
    SessionLocal,
    User
)
import dashboard


# Konfiguration der Streamlit-Seite
st.set_page_config(
    page_title="StudyBuddy",
    page_icon="📚",
    layout="centered")

# Pfad zur Datenbankdatei
db_path = 'local_database.db'

# Prüfe ob eine lokale Datenbankdatei existiert
if not os.path.exists(db_path):
    print(f"Database Datei {db_path} nicht gefunden. Erstelle neue...")
    
    # Erstelle die Datenbankdatei, wenn sie nicht existiert
    # Nutze db.py, um die Datenbank zu zu erstellen
    subprocess.run([sys.executable, 'db.py'], check=True)
    print(f"Database Datei {db_path} erfolgreich erstellt.")

else:
    print(f"Database Datei {db_path} existiert bereits.")


# Definiere Passwort für Cookie Encryption
COOKIE_PASSWORD = "dfsakdfakd876/)(ghjfewakjFGH)" 
SESSION_COOKIE_NAME = "kjjkl-687khkhkhj9870dsfHJJHbn"
SESSION_EXPIRY_DAYS = 30

# Initialisiere die Datenbank
try:
    init_db()
except Exception as e:
    # Error Handling für Datenbankinitialisierung
    st.error(f"Datenbankverbindung fehlgeschlagen: {e}. Bitte überprüfen Sie die Konfiguration und stellen Sie sicher, dass die Datenbank läuft.")
    st.stop()

# Initialisiere den Cookie-Manager
cookies = EncryptedCookieManager(
    prefix="sb/sess/",
    password=COOKIE_PASSWORD,
)

# Warte auf die Cookies, um sicherzustellen, dass sie geladen sind
if not cookies.ready():
    st.stop()

# Initialisiere Session-State Variblen
def initialize_session_state():
    defaults = {
        'logged_in': False,
        'username': None,
        'user_id': None,
        'session_id': None,
        'login_attempted': False,
        'learning_type_completed': False
    }
    # Setze Standardwerte für Session-State Variablen
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Initialisiere den Session-State mit der definierten Funktion
initialize_session_state()

# Authentifizierungslogik
# Prüft, ob ein Session-Cookie vorhanden ist und versucht, den Benutzer ohne Passwort anzumelden
def attempt_login_from_cookie():
    if not st.session_state.logged_in:
        session_token = cookies.get(SESSION_COOKIE_NAME)
        if session_token:
            # Debugging-Ausgabe
            print(f"Sitzungscookie gefunden: {session_token[:8]}...")
            user_info = validate_session_token(session_token)
            if user_info:
                user_id, username = user_info
                # Debugging-Ausgabe
                print(f"Session-Cookie für den Benutzer validiert: {username} (ID: {user_id})")
                st.session_state.logged_in = True
                st.session_state.user_id = user_id
                st.session_state.username = username
                
                # Prüfe ob VARK Fragen bereits beantwortet wurden
                session = SessionLocal()
                user = session.query(User).filter(User.id == user_id).first()
                st.session_state.learning_type_completed = bool(user.learning_type_completed)
                
                # Lade die Dashboard-Seite
                st.rerun()
            else:
                # Debugging-Ausgabe
                print("Session-Cookie ungültig oder abgelaufen, löschen.")
                # Gefunden aber ungültigen Cookie löschen
                del cookies[SESSION_COOKIE_NAME]
                # Cookies speichern
                cookies.save()
        else:
            # Debugging-Ausgabe
            print("Kein Session-Cookie gefunden.")

# Streamlit Frontend Seite für manuelles Login und Registrierung
def show_login_page():
    st.title("StudyBuddy")
    st.subheader("Optimieren Sie Ihre Lernreise")
    
    tab1, tab2 = st.tabs(["Login", "Registrieren"])
    
    with tab1:
        st.header("Willkommen zurück!")
        
        # Hier Streamlit Keys definieren, um Fehler zu vermeiden
        # Passwort und Benutzername Eingabefelder
        username = st.text_input("Username", key="login_username_input")
        password = st.text_input("Passwort", type="password", key="login_password_input")
        
        # Login Button für den Nutzer
        login_button = st.button("Login", key="login_button")
            
        if login_button and not st.session_state.login_attempted:
            # Verhindere dass man Mehrmals auf den Button klicken kann um Fehler zu vermeiden
            st.session_state.login_attempted = True
            if username and password:
                user_info = authenticate(username, password)
                if user_info:
                    user_id, retrieved_username = user_info
                    # Debugging-Ausgabe
                    print(f"Passwortanmeldung für Benutzer erfolgreich: {retrieved_username} (ID: {user_id})")
                    st.session_state.logged_in = True
                    st.session_state.username = retrieved_username
                    st.session_state.user_id = user_id
                    # Log Session um später Trcking und Statistiken zu ermöglichen
                    st.session_state.session_id = log_session(user_id)
                    
                    # Prüfe ob VARK Fragen bereits beantwortet wurden
                    session = SessionLocal()
                    user = session.query(User).filter(User.id == user_id).first()
                    st.session_state.learning_type_completed = bool(user.learning_type_completed)
                    
                    # Erstelle ein neues Session-Token und speichere es im Cookie
                    # um bei neuer Anmeldung nicht erneut nach dem Passwort fragen zu müssen
                    session_token = generate_session_token(user_id, days_valid=SESSION_EXPIRY_DAYS)
                    if session_token:
                        # Nutze oben definiertes Dictonary um den Cookie zu speichern
                        cookies[SESSION_COOKIE_NAME] = session_token
                        cookies.save()
                        # Debugging-Ausgabe
                        print("Persistentes Sitzungscookie, das nach der Passwortanmeldung gesetzt wird.")
                    else:
                        # Debugging-Ausgabe
                        st.warning("Konnte nach der Anmeldung kein dauerhaftes Sitzungs-Token erzeugen.")
                    
                    # Lade neu um auf die Dashboard-Seite zu gelangen
                    st.rerun()
                else:
                    # Bei falschen Anmeldedaten
                    st.error("Ungültiger Benutzername oder Passwort")
                    # Erlaube unbegrenzte Versuche
                    st.session_state.login_attempted = False
            else:
                # Wenn die Eingabefelder leer sind
                st.warning("Bitte geben Sie Ihren Benutzernamen und Ihr Passwort ein")
                st.session_state.login_attempted = False
        elif not login_button: 
            # Wenn der Button nicht gedrückt wurde, setze den Status zurück, damit der Benutzer erneut versuchen kann
            st.session_state.login_attempted = False

    # Tab zur Registrierung eines neuen Benutzers
    with tab2:
        st.header("Account erstellen")
        
        # Eingabefelder für die Registrierung mit uniquen Keys um Fehler zu vermeiden
        new_username = st.text_input("Username", key="signup_username_input")
        new_email = st.text_input("E-Mail", key="signup_email_input")
        new_password = st.text_input("Passwort", type="password", key="signup_password_input")
        confirm_password = st.text_input("Passwort bestätigen", type="password", key="confirm_password_input")
        
        # Registrierungsbutton
        signup_button = st.button("Registrieren", key="signup_button")
        
        if signup_button:
            # Prüfe Nutzer Eingaben auf Validität
            if new_username and new_email and new_password:
                if new_password == confirm_password:
                    if '@' in new_email and '.' in new_email.split('@')[-1]:
                        user_id = add_user(new_username, new_password, new_email)
                        if user_id:
                            st.success("Konto erfolgreich erstellt! Bitte fahren Sie mit der Registerkarte Login fort.")
                        else:
                            st.error("Usename oder E-Mail existiert bereits. Bitte versuchen Sie einen anderen.")
                    else:
                        st.error("Bitte geben Sie eine gültige E-Mail Adresse ein.")
                else:
                    st.error("Die Passwörter stimmen nicht überein.")
            else:
                st.warning("Bitte füllen Sie alle erforderlichen Felder aus.")

#  Main-Funktion, die den gesamten Ablauf steuert
def main():
    # Versuche mit dem Cookie anzumelden
    attempt_login_from_cookie()
    
    # Prüfe ob der Login via Cookie erfolgreich war
    if st.session_state.logged_in:
        # Stelle sicher, auth_token Parameter zu löschen, wenn vorhanden
        if 'auth_token' in st.query_params:
             try:
                 st.query_params["auth_token"] = ""
             except Exception as e:
                 # Debugging-Ausgabe
                 print(f"Fehler beim Löschen von Abfrageparametern: {e}")
        # Starte die Dashboard-Seite und übergebe die Cookies
        dashboard.main(cookies=cookies)
        # Stoppe die Ausführung, wenn der Benutzer eingeloggt ist
        return
    
    # Wenn der Benutzer nicht eingeloggt ist, zeige die Login-Seite an
    if not st.session_state.logged_in:
        show_login_page()

if __name__ == "__main__":
    main()
