import os
import json
import urllib.parse
import secrets
import bcrypt
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Optional, Tuple, List, Dict, Any
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.orm import relationship

# Mit der folgenden Zeile kann der Offline Modus aktiviert werden. 
# Statt einer Azure SQL-Datenbank wird eine lokale SQLite-Datenbank verwendet, die keine zusätzlichen Installationen benötigt.
# Auf False setzen, um mit Azure SQL zu arbeiten
OFFLINE_MODE = True

# Laden der Umgebungsvariablen aus der .env-Datei
load_dotenv()

# Funktion die für Offline- und Online-Modus die jeweils richtige Engine zurückgibt
def get_db_engine():
    if OFFLINE_MODE:
        # SQLite für Offline-Modus
        SQLALCHEMY_DATABASE_URL = "sqlite:///./local_database.db"
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL, 
            connect_args={"check_same_thread": False}
        )
        return engine
    else:
        # Azure SQL für Online-Modus
        return get_azure_db_engine()


# Funktion die eine SQLAlchemy-Engine für Azure SQL Database baut
def get_azure_db_engine():
    # laden der Umgebungsvariablen aus der .env-Datei
    server = os.getenv("DB_SERVER", "studybuddyhsg.database.windows.net")
    database = os.getenv("DB_DATABASE", "CS-Project-DB")
    username = os.getenv("DB_USERNAME", "CloudSA74f1c350")
    password = os.getenv("DB_PASSWORD")
    driver = os.getenv("DB_DRIVER", "{ODBC Driver 18 for SQL Server}")

    conn_str = (
        f"Driver={driver};"
        f"Server=tcp:{server},1433;"
        f"Database={database};"
        f"Uid={username};"
        f"Pwd={password};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=no;"
        f"Connection Timeout=30;"
    )

    params = urllib.parse.quote_plus(conn_str)
    engine_url = f"mssql+pyodbc:///?odbc_connect={params}"
    
    try:
        engine = create_engine(
            engine_url, 
            echo=False,
            pool_pre_ping=True,  # Prüfe Verbingung vor der Verwendung
            pool_recycle=3600, 
            pool_size=10,
            max_overflow=20
        )
        
        # Test der Verbindung und Ausgabe für Debugging
        with engine.connect():
            print("Erfolgreich mit der Azure SQL-Datenbank verbunden.")
        return engine
    except Exception as e:
        print(f"Fehler beim Verbinden mit der Azure SQL-Datenbank: {e}")
        raise

# Initialisierung der Engine und SessionLocal
engine = get_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Kontextmanager für Datenbanksitzungen, um eine ordnungsgemäße Bereinigung zu gewährleisten
@contextmanager
def get_db_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()

# Definition der einzlen Tabellen in unserer Datenbank
# Nutzer und seine Daten. Vor allem für die Authentifizierung wichtig
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    learning_type = Column(String(50), nullable=True)
    learning_type_completed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

# Logging der Nutzer-Sitzungen für Auswertungen der Lernzeit
class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    login_time = Column(DateTime, default=datetime.utcnow)
    logout_time = Column(DateTime, nullable=True)

# Tokens, damit auch bei Reloads die Authentifizierung nicht verloren geht
class AuthToken(Base):
    __tablename__ = "auth_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(100), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

# Tokens, damit auch bei Reloads die Authentifizierung nicht verloren geht
class SessionToken(Base):
    __tablename__ = "session_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(100), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

# Kurszeiten, damit die Kurse auch im Kalender angezeigt werden können ohne jedes mal von der API abgerufen werden zu müssen
class CourseSchedule(Base):
    __tablename__ = "course_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(String(100), ForeignKey("courses.course_id"), nullable=False)
    start_date = Column(String(10), nullable=False)  # Format: YYYY-MM-DD
    start_time = Column(String(5), nullable=False)   # Format: HH:MM
    end_time = Column(String(5), nullable=False)     # Format: HH:MM
    room = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Speicherung der Kurse, damit diese nicht jedes mal von der API abgerufen werden müssen
class Course(Base):
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(String(100), unique=True, index=True, nullable=False)
    meeting_code = Column(String(50))
    title = Column(String(255))
    description = Column(String)
    language_id = Column(Integer, ForeignKey("languages.id"))
    max_credits = Column(String)
    term_id = Column(String(50), ForeignKey("terms.term_id"))
    link_course_info = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    language = relationship("Language", back_populates="courses")
    term = relationship("Term", back_populates="courses")
    study_tasks = relationship("StudyTask", back_populates="course")

# Languages als relationship (separate table) damit 3NF form eingehalten wird
class Language(Base):
    __tablename__ = "languages"
    
    id = Column(Integer, primary_key=True, index=True)
    language_name = Column(String(100))
    language_code = Column(String(20))
    
    # Relationship
    courses = relationship("Course", back_populates="language")

# Terms als relationship (separate table) damit 3NF form eingehalten wird
class Term(Base):
    __tablename__ = "terms"
    
    term_id = Column(String(50), primary_key=True, index=True)
    term_name = Column(String(100))
    term_description = Column(String(255))
    
    # Relationship
    courses = relationship("Course", back_populates="term")

# Speicherung der Kurse, die ein Nutzer ausgewählt hat
class UserCourse(Base):
    __tablename__ = "user_courses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(String(100), nullable=False)
    selected_at = Column(DateTime, default=datetime.utcnow)

# Speicherung der Kalendereinträge
class CalendarEvent(Base):
    __tablename__ = "calendar_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(100), nullable=False)
    date = Column(String(10), nullable=False)  # Format: YYYY-MM-DD
    time = Column(String(5), nullable=False)   # Format: HH:MM
    event_type = Column(String(50), nullable=False)
    color = Column(String(7), nullable=False)  # Hex Farbcode
    is_deadline = Column(Boolean, default=False)
    priority = Column(Integer, default=2)      # Priorität: 1=High, 2=Medium, 3=Low
    created_at = Column(DateTime, default=datetime.utcnow)

# Speicherung der Studienaufgaben
class StudyTask(Base):
    __tablename__ = "study_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(String(100), ForeignKey("courses.course_id"), nullable=False)
    date = Column(String(10), nullable=False)  # Format: YYYY-MM-DD
    start_time = Column(String(5), nullable=False)  # Format: HH:MM
    end_time = Column(String(5), nullable=False)    # Format: HH:MM
    topic = Column(String(255), nullable=False)
    methods = Column(String(1000), nullable=False)  # JSON-string für Lernmethoden
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to Course table to fetch title and code
    course = relationship("Course", back_populates="study_tasks")
# Funktion zum Initialisieren der Datenbanktabellen
def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        print("Datenbanktabellen erfolgreich geprüft/erstellt.")
    except Exception as e:
        print(f"Bei der Erstellung der Tabelle ist ein Fehler aufgetreten: {e}")

# Verschlüsselung der Passwörter
def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode("utf-8")

#Überprüft ein einfaches Passwort mit einem gehashten Passwort.
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        password_bytes = plain_password.encode("utf-8")
        hashed_password_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_password_bytes)
    except Exception:
        return False

# Nutzerverwaltung: Fügt bei Registrierung einen neuen Nutzer hinzu
def add_user(username: str, password: str, email: str) -> Optional[int]:
    with get_db_session() as session:
        # prüfen, ob der Nutzer bereits existiert
        existing_user = session.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing_user:
            print(f"Username '{username}' oder Email '{email}' existiert bereits.")
            return None
        # Nutzer hinzufügen
        hashed_pw = hash_password(password)
        new_user = User(username=username, hashed_password=hashed_pw, email=email)
        session.add(new_user)
        session.flush()  # Flush um die ID des neuen Nutzers zu erhalten
        # Controll Statement für Debugging
        print(f"User '{username}' erfolgreich hinzugefügt mit ID: {new_user.id}")
        return new_user.id

# Nutzerverwaltung: Authentifizierung eines Nutzers beim Login
def authenticate(username: str, password: str) -> Optional[Tuple[int, str]]:
    with get_db_session() as session:
        user = session.query(User).filter(User.username == username).first()
        # Überprüfen, ob der Nutzer existiert und das Passwort korrekt ist
        if user and verify_password(password, user.hashed_password):
            # Debugging
            print(f"User '{username}' erfolgreich authentifiziert.")
            # Rückgabe der Nutzer-ID und des Nutzernamens
            return user.id, user.username
        # Debugging
        print(f"Authentifizierung für Benutzer fehlgeschlagen'{username}'.")
        return None

# Prüfe ob VARK Fragebogen bereits ausgefüllt wurde
def get_learning_type_status(user_id: int) -> Tuple[Optional[str], bool]:
    with get_db_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            return user.learning_type, bool(user.learning_type_completed)
        return None, False

# Protokolliert eine neue Benutzersitzung.
def log_session(user_id: int) -> Optional[int]:
    with get_db_session() as session:
        new_session = UserSession(user_id=user_id, login_time=datetime.utcnow())
        session.add(new_session)
        session.flush()
        # Debugging
        print(f"Für die Benutzer-ID protokollierte Sitzung: {user_id}. Session ID: {new_session.id}")
        return new_session.id

# --- Token Management ---
def generate_auth_token(user_id: int) -> Optional[str]:
    with get_db_session() as session:
        token = secrets.token_hex(32)
        expiry = datetime.utcnow() + timedelta(days=7)
        
        new_token = AuthToken(user_id=user_id, token=token, expires_at=expiry)
        session.add(new_token)
        print(f"Für die Benutzer-ID generiertes Auth-Token: {user_id}")
        return token

def validate_auth_token(token: str) -> Optional[Tuple[int, str]]:
    """Validiert ein Authentifizierungs-Token und gibt bei Gültigkeit Benutzerinformationen zurück."""
    with get_db_session() as session:
        auth_token = session.query(AuthToken).filter(AuthToken.token == token).first()
        if not auth_token or auth_token.expires_at <= datetime.utcnow():
            print(f"Auth-Token ungültig oder abgelaufen")
            return None
            
        user = session.query(User).filter(User.id == auth_token.user_id).first()
        if not user:
            print(f"Benutzer für Token nicht gefunden")
            return None
            
        print(f"Auth-Token für Benutzer-ID validiert: {user.id}")
        return user.id, user.username

def generate_session_token(user_id: int, days_valid: int = 30) -> Optional[str]:
    """Erzeugt und speichert ein neues persistentes Sitzungs-Token für einen Benutzer."""
    with get_db_session() as session:
        # Clean up expired tokens for this user
        session.query(SessionToken).filter(
            SessionToken.user_id == user_id,
            SessionToken.expires_at <= datetime.utcnow()
        ).delete(synchronize_session=False)
        
        token = secrets.token_hex(32)
        expiry = datetime.utcnow() + timedelta(days=days_valid)
        
        new_token = SessionToken(user_id=user_id, token=token, expires_at=expiry)
        session.add(new_token)
        print(f"Für die Benutzer-ID generiertes Session-Token: {user_id}")
        return token

def validate_session_token(token: str) -> Optional[Tuple[int, str]]:
    """Validiert ein Sitzungs-Token und gibt bei Gültigkeit Benutzerinformationen zurück."""
    with get_db_session() as session:
        session_token = session.query(SessionToken).filter(SessionToken.token == token).first()
        if not session_token or session_token.expires_at <= datetime.utcnow():
            if session_token:
                # Clean up expired token
                session.delete(session_token)
            print(f"Session-Token ungültig oder abgelaufen")
            return None
            
        user = session.query(User).filter(User.id == session_token.user_id).first()
        if not user:
            print(f"Benutzer für Sitzungs-Token nicht gefunden")
            return None
            
        # Extend token validity (sliding session)
        session_token.expires_at = datetime.utcnow() + timedelta(days=30)
        print(f"Session-Token für Benutzer-ID validiert: {user.id}")
        return user.id, user.username

def delete_session_token(token: str) -> bool:
    """Löscht ein bestimmtes Sitzungs-Token aus der Datenbank."""
    with get_db_session() as session:
        deleted_count = session.query(SessionToken).filter(
            SessionToken.token == token
        ).delete(synchronize_session=False)
        
        if deleted_count > 0:
            print(f"Session token {token[:8]}... erfolgreich gelöscht.")
            return True
        print(f"Session token {token[:8]}... zur Löschung nicht gefunden.")
        return False

@st.cache_data(ttl=300)
def get_user_sessions(user_id):
    """Ruft alle Sitzungen für einen Benutzer ab und berechnet die Dauer."""
    with get_db_session() as session:
        user_sessions = session.query(UserSession).filter(
            UserSession.user_id == user_id
        ).order_by(UserSession.login_time.desc()).all()

        sessions_data = []
        for sess in user_sessions:
            login_time = sess.login_time
            logout_time = sess.logout_time or datetime.utcnow()
            duration_hours = (logout_time - login_time).total_seconds() / 3600
            
            sessions_data.append({
                "login_time": login_time,
                "logout_time": logout_time,
                "duration_hours": round(duration_hours, 2)
            })

        return pd.DataFrame(sessions_data)

# --- Calendar Event Management ---
def save_calendar_event(user_id: int, event_data: Dict[str, Any]) -> Optional[int]:
    """Speichert ein Kalenderevent in der Datenbank."""
    with get_db_session() as session:
        # Check if event type is a deadline type
        is_deadline = event_data.get('type') in ["Prüfung", "Aufgabe fällig", "Projekt fällig"]
        
        new_event = CalendarEvent(
            user_id=user_id,
            title=event_data.get('title'),
            date=event_data.get('date'),
            time=event_data.get('time'),
            event_type=event_data.get('type'),
            color=event_data.get('color'),
            is_deadline=is_deadline,
            priority=event_data.get('priority', 2)  # Default medium priority
        )
        session.add(new_event)
        session.flush()
        print(f"Ereignis für Benutzer-ID gespeichert: {user_id}. Event ID: {new_event.id}")
        return new_event.id

def get_calendar_events(user_id: int) -> List[Dict[str, Any]]:
    """Ruft alle Kalenderereignisse für einen Benutzer ab."""
    with get_db_session() as session:
        events = session.query(CalendarEvent).filter(
            CalendarEvent.user_id == user_id
        ).all()
        
        return [
            {
                'id': event.id,
                'date': event.date,
                'title': event.title,
                'time': event.time,
                'type': event.event_type,
                'color': event.color,
                'user_id': event.user_id,
                'is_deadline': event.is_deadline,
                'priority': event.priority
            }
            for event in events
        ]

def update_calendar_event(event_id: int, event_data: Dict[str, Any]) -> bool:
    """Ruft alle Kalenderereignisse für einen Benutzer ab."""
    with get_db_session() as session:
        event = session.query(CalendarEvent).filter(
            CalendarEvent.id == event_id
        ).first()
        
        if not event:
            print(f"Ereignis für ID nicht gefunden: {event_id}")
            return False
            
        # Check if event type is a deadline type
        is_deadline = event_data.get('type') in ["Prüfung", "Aufgabe fällig", "Projekt fällig"]
        
        event.title = event_data.get('title', event.title)
        event.date = event_data.get('date', event.date)
        event.time = event_data.get('time', event.time)
        event.event_type = event_data.get('type', event.event_type)
        event.color = event_data.get('color', event.color)
        event.is_deadline = is_deadline
        event.priority = event_data.get('priority', event.priority)
        
        print(f"Ereignis erfolgreich aktualisiert. Ereignis-ID:  {event_id}")
        return True

def delete_calendar_event(event_id: int) -> bool:
    """Löscht ein Kalenderereignis."""
    with get_db_session() as session:
        deleted_count = session.query(CalendarEvent).filter(
            CalendarEvent.id == event_id
        ).delete(synchronize_session=False)
        
        if deleted_count > 0:
            print(f"Ereignis erfolgreich gelöscht. Ereignis-ID: {event_id}")
            return True
        print(f"Ereignis für ID nicht gefunden: {event_id}")
        return False

# --- Study Task Management ---
def save_study_task(user_id: int, task_data: Dict[str, Any]) -> Optional[int]:
    """Speichert eine Studienaufgabe in der Datenbank."""
    with get_db_session() as session:
        # Convert methods list to JSON string
        methods_json = json.dumps(task_data.get("methods", []))
        
        new_task = StudyTask(
            user_id=user_id,
            course_id=task_data.get("course_id"),
            # course_title and course_code are removed, will be fetched via relationship
            date=task_data.get("date"),
            start_time=task_data.get("start_time"),
            end_time=task_data.get("end_time"),
            topic=task_data.get("topic"),
            methods=methods_json,
            completed=task_data.get("completed", False) # Retain completed field if passed
        )
        
        session.add(new_task)
        session.flush()
        print(f"Studienaufgabe für User-ID gespeichert: {user_id}. Task ID: {new_task.id}")
        return new_task.id

def get_study_tasks(user_id: int) -> List[Dict[str, Any]]:
    """Ruft alle Lernaufgaben für einen Benutzer ab, inklusive Kursdetails."""
    with get_db_session() as session:
        tasks_with_course_info = session.query(
            StudyTask,
            Course.title.label("course_title"),
            Course.meeting_code.label("course_code")
        ).join(
            Course, StudyTask.course_id == Course.course_id
        ).filter(
            StudyTask.user_id == user_id
        ).all()
        
        result_list = []
        for task, course_title, course_code in tasks_with_course_info:
            result_list.append({
                "id": task.id,
                "user_id": task.user_id,
                "course_id": task.course_id,
                "course_title": course_title,  # Fetched via join
                "course_code": course_code,    # Fetched via join
                "date": task.date,
                "start_time": task.start_time,
                "end_time": task.end_time,
                "topic": task.topic,
                "methods": json.loads(task.methods) if task.methods else [], # Ensure methods is a list
                "completed": task.completed,
                "created_at": task.created_at
            })
        return result_list

def update_study_task(task_id: int, update_data: Dict[str, Any]) -> bool:
    """Aktualisiert eine bestehende Studienaufgabe."""
    with get_db_session() as session:
        task = session.query(StudyTask).filter(
            StudyTask.id == task_id
        ).first()
        
        if not task:
            print(f"Studienaufgabe für ID nicht gefunden: {task_id}")
            return False
            
        # Update fields if provided
        if 'date' in update_data:
            task.date = update_data['date']
        if 'start_time' in update_data:
            task.start_time = update_data['start_time']
        if 'end_time' in update_data:
            task.end_time = update_data['end_time']
        if 'topic' in update_data:
            task.topic = update_data['topic']
        if 'methods' in update_data and isinstance(update_data['methods'], list):
            task.methods = json.dumps(update_data['methods'])
        if 'completed' in update_data:
            task.completed = update_data['completed']
        
        print(f"Studienaufgabe aktualisiert. Task ID: {task_id}")
        return True

def update_study_task_status(task_id: int, completed: bool) -> bool:
    """Aktualisiert den Abschlussstatus einer Studienaufgabe."""
    with get_db_session() as session:
        task = session.query(StudyTask).filter(
            StudyTask.id == task_id
        ).first()
        
        if not task:
            print(f"Study task für ID nicht gefunden: {task_id}")
            return False
            
        task.completed = completed
        print(f"Status der Studienaufgaben aktualisiert. Task ID: {task_id}")
        return True

def delete_study_task(task_id: int) -> bool:
    """Löscht eine Studienaufgabe."""
    with get_db_session() as session:
        deleted_count = session.query(StudyTask).filter(
            StudyTask.id == task_id
        ).delete(synchronize_session=False)
        
        if deleted_count > 0:
            print(f"Studienaufgabe erfolgreich gelöscht. Task ID: {task_id}")
            return True
        print(f"Studienaufgabe für ID nicht gefunden: {task_id}")
        return False

# Initialisierung der Datenbanktabellen wenn die Datei direkt ausgeführt wird
if __name__ == "__main__":
    # Debugging Statement
    print("Initialisiere Datenbank...")
    try:
        init_db()
    except Exception as e:
        # Fehlermeldung, wenn die Datenbank nicht initialisiert werden kann
        print(f"Error beim Initialisieren der Datenbank: {e}")