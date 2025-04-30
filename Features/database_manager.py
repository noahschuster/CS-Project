# database_manager.py

import os
import urllib
import secrets
import bcrypt
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, MetaData, Table, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy import Boolean

# Load environment variables from .env file
load_dotenv()

# Add these new functions to database_manager.py

def get_learning_type_status(user_id: int):
    """Gets the user's learning type and completion status."""
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            return user.learning_type, bool(user.learning_type_completed)
        return None, False
    except Exception as e:
        print(f"Error getting learning type status: {e}")
        return None, False
    finally:
        session.close()

def update_learning_type(user_id: int, learning_type: str):
    """Updates the user's learning type and marks it as completed."""
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user.learning_type = learning_type
            user.learning_type_completed = 1
            session.commit()
            print(f"Learning type updated for user ID: {user_id}")
            return True
        print(f"User not found for ID: {user_id}")
        return False
    except Exception as e:
        session.rollback()
        print(f"Error updating learning type: {e}")
        return False
    finally:
        session.close()


# --- Database Connection Configuration ---
def get_db_engine():
    """Creates and returns a SQLAlchemy engine for Azure SQL Database."""
    server = os.getenv("DB_SERVER", "studybuddyhsg.database.windows.net")
    database = os.getenv("DB_DATABASE", "CS-Project-DB")
    username = os.getenv("DB_USERNAME", "CloudSA74f1c350")
    password = os.getenv("DB_PASSWORD")
    driver = os.getenv("DB_DRIVER", "{ODBC Driver 18 for SQL Server}")

    if not password:
        raise ValueError("DB_PASSWORD environment variable not set.")

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
        engine = create_engine(engine_url, echo=False) # Set echo=True for debugging SQL
        # Test connection
        with engine.connect() as connection:
            print("Successfully connected to Azure SQL Database.")
        return engine
    except Exception as e:
        print(f"Error connecting to Azure SQL Database: {e}")
        raise

engine = get_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Add these functions to database_manager.py

def save_calendar_event(user_id, event_data):
    """Saves a calendar event to the database"""
    print("save_calendar_event")
    session = SessionLocal()
    try:
        # Check if event type is a deadline type
        is_deadline = event_data['type'] in ["Exam", "Assignment Due", "Project Due"]
        
        new_event = CalendarEvent(
            user_id=user_id,
            title=event_data['title'],
            date=event_data['date'],
            time=event_data['time'],
            event_type=event_data['type'],
            color=event_data['color'],
            is_deadline=is_deadline,
            priority=2  # Default medium priority
        )
        session.add(new_event)
        session.commit()
        session.refresh(new_event)
        print(f"Event saved successfully for user ID: {user_id}. Event ID: {new_event.id}")
        return new_event.id
    except Exception as e:
        session.rollback()
        print(f"Error saving calendar event: {e}")
        return None
    finally:
        session.close()

def get_calendar_events(user_id):
    """Gets all calendar events for a user"""
    session = SessionLocal()
    try:
        events = session.query(CalendarEvent).filter(CalendarEvent.user_id == user_id).all()
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
    except Exception as e:
        print(f"Error getting calendar events: {e}")
        return []
    finally:
        session.close()

def update_calendar_event(event_id, event_data):
    """Updates an existing calendar event"""
    session = SessionLocal()
    try:
        event = session.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
        if event:
            # Check if event type is a deadline type
            is_deadline = event_data['type'] in ["Exam", "Assignment Due", "Project Due"]
            
            event.title = event_data['title']
            event.date = event_data['date']
            event.time = event_data['time']
            event.event_type = event_data['type']
            event.color = event_data['color']
            event.is_deadline = is_deadline
            
            session.commit()
            print(f"Event updated successfully. Event ID: {event_id}")
            return True
        print(f"Event not found for ID: {event_id}")
        return False
    except Exception as e:
        session.rollback()
        print(f"Error updating calendar event: {e}")
        return False
    finally:
        session.close()

def delete_calendar_event(event_id):
    """Deletes a calendar event"""
    session = SessionLocal()
    try:
        event = session.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
        if event:
            session.delete(event)
            session.commit()
            print(f"Event deleted successfully. Event ID: {event_id}")
            return True
        print(f"Event not found for ID: {event_id}")
        return False
    except Exception as e:
        session.rollback()
        print(f"Error deleting calendar event: {e}")
        return False
    finally:
        session.close()

# Add these functions to database_manager.py

def save_calendar_event(user_id, event_data):
    """Saves a calendar event to the database"""
    session = SessionLocal()
    try:
        # Check if event type is a deadline type
        is_deadline = event_data['type'] in ["Exam", "Assignment Due", "Project Due"]
        
        new_event = CalendarEvent(
            user_id=user_id,
            title=event_data['title'],
            date=event_data['date'],
            time=event_data['time'],
            event_type=event_data['type'],
            color=event_data['color'],
            is_deadline=is_deadline,
            priority=2  # Default medium priority
        )
        session.add(new_event)
        session.commit()
        session.refresh(new_event)
        print(f"Event saved successfully for user ID: {user_id}. Event ID: {new_event.id}")
        return new_event.id
    except Exception as e:
        session.rollback()
        print(f"Error saving calendar event: {e}")
        return None
    finally:
        session.close()

def get_calendar_events(user_id):
    """Gets all calendar events for a user"""
    session = SessionLocal()
    try:
        events = session.query(CalendarEvent).filter(CalendarEvent.user_id == user_id).all()
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
    except Exception as e:
        print(f"Error getting calendar events: {e}")
        return []
    finally:
        session.close()

def update_calendar_event(event_id, event_data):
    """Updates an existing calendar event"""
    session = SessionLocal()
    try:
        event = session.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
        if event:
            # Check if event type is a deadline type
            is_deadline = event_data['type'] in ["Exam", "Assignment Due", "Project Due"]
            
            event.title = event_data['title']
            event.date = event_data['date']
            event.time = event_data['time']
            event.event_type = event_data['type']
            event.color = event_data['color']
            event.is_deadline = is_deadline
            
            session.commit()
            print(f"Event updated successfully. Event ID: {event_id}")
            return True
        print(f"Event not found for ID: {event_id}")
        return False
    except Exception as e:
        session.rollback()
        print(f"Error updating calendar event: {e}")
        return False
    finally:
        session.close()

def get_study_tasks(user_id):
    """Holt alle Lernaufgaben eines Benutzers aus der Datenbank"""
    session = SessionLocal()
    try:
        tasks = session.query(StudyTask).filter(StudyTask.user_id == user_id).all()
        
        return [
            {
                'id': task.id,
                'user_id': task.user_id,
                'course_id': task.course_id,
                'date': task.date,
                'start_time': task.start_time,
                'end_time': task.end_time,
                'topic': task.topic,
                'methods': json.loads(task.methods),
                'completed': task.completed,
                'created_at': task.created_at
            }
            for task in tasks
        ]
    except Exception as e:
        print(f"Fehler beim Abrufen der Lernaufgaben: {e}")
        return []
    finally:
        session.close()

import json  # Füge diesen Import am Anfang der Datei hinzu, falls noch nicht vorhanden

# Füge diese Klasse zu den ORM-Modellen in database_manager.py hinzu
class StudyTask(Base):
    __tablename__ = "study_tasks"
    __table_args__ = {'extend_existing': True}  # Diese Zeile hinzufügen
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(String(100), nullable=False)
    course_title = Column(String(255), nullable=False)
    course_code = Column(String(50), nullable=False)
    date = Column(String(10), nullable=False)  # Format: YYYY-MM-DD
    start_time = Column(String(5), nullable=False)  # Format: HH:MM
    end_time = Column(String(5), nullable=False)  # Format: HH:MM
    topic = Column(String(255), nullable=False)
    methods = Column(String(1000), nullable=False)  # JSON-String mit Lernmethoden
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

def save_study_task(user_id, task_data):
    """Speichert eine Lernaufgabe in der Datenbank"""
    session = SessionLocal()
    try:
        # Konvertiere methods-Liste zu JSON-String
        methods_json = json.dumps(task_data['methods'])
        
        new_task = StudyTask(
            user_id=user_id,
            course_id=task_data['course_id'],
            course_title=task_data.get('course_title', ''),  # Mit get und Fallback-Wert
            course_code=task_data.get('course_code', ''),    # Mit get und Fallback-Wert
            date=task_data['date'],
            start_time=task_data['start_time'],
            end_time=task_data['end_time'],
            topic=task_data['topic'],
            methods=methods_json,
            completed=False
        )
        
        session.add(new_task)
        session.commit()
        session.refresh(new_task)
        
        print(f"Lernaufgabe gespeichert für Benutzer ID: {user_id}. Aufgaben-ID: {new_task.id}")
        return new_task.id
    except Exception as e:
        session.rollback()
        print(f"Fehler beim Speichern der Lernaufgabe: {e}")
        return None
    finally:
        session.close()


def get_study_tasks(user_id):
    """Holt alle Lernaufgaben eines Benutzers aus der Datenbank"""
    session = SessionLocal()
    try:
        tasks = session.query(StudyTask).filter(StudyTask.user_id == user_id).all()
        
        return [
            {
                'id': task.id,
                'user_id': task.user_id,
                'course_id': task.course_id,
                'course_title': task.course_title,
                'course_code': task.course_code,
                'date': task.date,
                'start_time': task.start_time,
                'end_time': task.end_time,
                'topic': task.topic,
                'methods': json.loads(task.methods),
                'completed': task.completed,
                'created_at': task.created_at
            }
            for task in tasks
        ]
    except Exception as e:
        print(f"Fehler beim Abrufen der Lernaufgaben: {e}")
        return []
    finally:
        session.close()

def update_study_task_status(task_id, completed):
    """Aktualisiert den Status einer Lernaufgabe"""
    session = SessionLocal()
    try:
        task = session.query(StudyTask).filter(StudyTask.id == task_id).first()
        if task:
            task.completed = completed
            session.commit()
            print(f"Status der Lernaufgabe aktualisiert. Aufgaben-ID: {task_id}")
            return True
        
        print(f"Lernaufgabe nicht gefunden für ID: {task_id}")
        return False
    except Exception as e:
        session.rollback()
        print(f"Fehler beim Aktualisieren des Lernaufgabenstatus: {e}")
        return False
    finally:
        session.close()

def update_study_task_status(task_id, completed):
    """Aktualisiert den Status einer Lernaufgabe"""
    session = SessionLocal()
    try:
        task = session.query(StudyTask).filter(StudyTask.id == task_id).first()
        if task:
            task.completed = completed
            session.commit()
            print(f"Status der Lernaufgabe aktualisiert. Aufgaben-ID: {task_id}")
            return True
        
        print(f"Lernaufgabe nicht gefunden für ID: {task_id}")
        return False
    except Exception as e:
        session.rollback()
        print(f"Fehler beim Aktualisieren des Lernaufgabenstatus: {e}")
        return False
    finally:
        session.close()


def delete_calendar_event(event_id):
    """Deletes a calendar event"""
    session = SessionLocal()
    try:
        event = session.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
        if event:
            session.delete(event)
            session.commit()
            print(f"Event deleted successfully. Event ID: {event_id}")
            return True
        print(f"Event not found for ID: {event_id}")
        return False
    except Exception as e:
        session.rollback()
        print(f"Error deleting calendar event: {e}")
        return False
    finally:
        session.close()

# --- SQLAlchemy ORM Models ---

# Add to database_manager.py (when you implement the database integration)
class CalendarEvent(Base):
    __tablename__ = "calendar_events"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(100), nullable=False)
    date = Column(String(10), nullable=False)  # Format: YYYY-MM-DD
    time = Column(String(5), nullable=False)   # Format: HH:MM
    event_type = Column(String(50), nullable=False)
    color = Column(String(7), nullable=False)  # Hex color code
    is_deadline = Column(Boolean, default=False)  # New field to flag deadlines
    priority = Column(Integer, default=2)  # Priority: 1=High, 2=Medium, 3=Low
    created_at = Column(DateTime, default=datetime.utcnow)

class Course(Base):
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(String(100), unique=True, index=True)
    meeting_code = Column(String(50))
    title = Column(String(255))
    description = Column(String)
    language_id = Column(Integer)
    max_credits = Column(String)
    term_id = Column(String(50))
    term_name = Column(String(100))
    term_description = Column(String(255))
    link_course_info = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

class UserCourse(Base):
    __tablename__ = "user_courses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(String(100), nullable=False)
    selected_at = Column(DateTime, default=datetime.utcnow)
    
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    learning_type = Column(String(50), nullable=True) # Kept from original schema
    learning_type_completed = Column(Integer, default=0)  
    created_at = Column(DateTime, default=datetime.utcnow)

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    login_time = Column(DateTime, default=datetime.utcnow)
    logout_time = Column(DateTime, nullable=True)

class AuthToken(Base):
    __tablename__ = "auth_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(100), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

# --- Database Initialization ---

def init_db():
    """Creates database tables if they don't exist."""
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables checked/created successfully.")
    except OperationalError as e:
        print(f"Database connection error during init_db: {e}")
        # Depending on the error, you might want to retry or handle differently
    except Exception as e:
        print(f"An error occurred during table creation: {e}")

# --- Password Hashing ---

def hash_password(password: str) -> str:
    """Hashes a password using bcrypt."""
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    password_byte_enc = plain_password.encode("utf-8")
    hashed_password_byte_enc = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_byte_enc, hashed_password_byte_enc)

def update_study_task(task_id, task_data):
    """Aktualisiert eine bestehende Lernaufgabe"""
    session = SessionLocal()
    try:
        task = session.query(StudyTask).filter(StudyTask.id == task_id).first()
        if task:
            # Aktualisiere die Felder
            if 'date' in task_data:
                task.date = task_data['date']
            if 'start_time' in task_data:
                task.start_time = task_data['start_time']
            if 'end_time' in task_data:
                task.end_time = task_data['end_time']
            if 'topic' in task_data:
                task.topic = task_data['topic']
            if 'methods' in task_data:
                task.methods = json.dumps(task_data['methods'])
            if 'completed' in task_data:
                task.completed = task_data['completed']
            
            session.commit()
            print(f"Lernaufgabe aktualisiert. Aufgaben-ID: {task_id}")
            return True
        
        print(f"Lernaufgabe nicht gefunden für ID: {task_id}")
        return False
    except Exception as e:
        session.rollback()
        print(f"Fehler beim Aktualisieren der Lernaufgabe: {e}")
        return False
    finally:
        session.close()


# --- Core Database Functions ---

def add_user(username: str, password: str, email: str):
    """Adds a new user to the database."""
    session = SessionLocal()
    try:
        # Check if username or email already exists
        existing_user = session.query(User).filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            print(f"Username '{username}' or Email '{email}' already exists.")
            return None

        hashed_pw = hash_password(password)
        new_user = User(username=username, hashed_password=hashed_pw, email=email)
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        print(f"User '{username}' added successfully with ID: {new_user.id}")
        return new_user.id
    except IntegrityError as e:
        session.rollback()
        print(f"Database integrity error adding user: {e}")
        return None
    except Exception as e:
        session.rollback()
        print(f"An unexpected error occurred adding user: {e}")
        return None
    finally:
        session.close()

def update_study_task(task_id, update_data):
    """Aktualisiert eine bestehende Lernaufgabe"""
    session = SessionLocal()
    try:
        task = session.query(StudyTask).filter(StudyTask.id == task_id).first()
        if task:
            # Aktualisiere die Felder
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
            
            session.commit()
            print(f"Lernaufgabe aktualisiert. Aufgaben-ID: {task_id}")
            return True
        
        print(f"Lernaufgabe nicht gefunden für ID: {task_id}")
        return False
    except Exception as e:
        session.rollback()
        print(f"Fehler beim Aktualisieren der Lernaufgabe: {e}")
        return False
    finally:
        session.close()


def delete_study_task(task_id):
    """Löscht eine Lernaufgabe aus der Datenbank"""
    session = SessionLocal()
    try:
        task = session.query(StudyTask).filter(StudyTask.id == task_id).first()
        if task:
            session.delete(task)
            session.commit()
            print(f"Lernaufgabe erfolgreich gelöscht. Aufgaben-ID: {task_id}")
            return True
        
        print(f"Lernaufgabe nicht gefunden für ID: {task_id}")
        return False
    except Exception as e:
        session.rollback()
        print(f"Fehler beim Löschen der Lernaufgabe: {e}")
        return False
    finally:
        session.close()


def authenticate(username: str, password: str):
    """Authenticates a user by username and password."""
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.username == username).first()
        if user and verify_password(password, user.hashed_password):
            print(f"User '{username}' authenticated successfully.")
            return user.id, user.username # Return ID and username tuple
        else:
            print(f"Authentication failed for user '{username}'.")
            return None
    except Exception as e:
        print(f"An error occurred during authentication: {e}")
        return None
    finally:
        session.close()

def log_session(user_id: int):
    """Logs a new user session."""
    session = SessionLocal()
    try:
        new_session = UserSession(user_id=user_id, login_time=datetime.utcnow())
        session.add(new_session)
        session.commit()
        session.refresh(new_session)
        print(f"Session logged successfully for user ID: {user_id}. Session ID: {new_session.id}")
        return new_session.id
    except Exception as e:
        session.rollback()
        print(f"An error occurred logging session: {e}")
        return None
    finally:
        session.close()

def generate_auth_token(user_id: int):
    """Generates and stores a new authentication token for a user."""
    session = SessionLocal()
    try:
        token = secrets.token_hex(32) # Longer token
        expiry = datetime.utcnow() + timedelta(days=7) # Token valid for 7 days
        
        new_token = AuthToken(user_id=user_id, token=token, expires_at=expiry)
        session.add(new_token)
        session.commit()
        print(f"Auth token generated successfully for user ID: {user_id}")
        return token
    except Exception as e:
        session.rollback()
        print(f"An error occurred generating auth token: {e}")
        return None
    finally:
        session.close()

def validate_auth_token(token: str):
    """Validates an authentication token and returns user info if valid."""
    session = SessionLocal()
    try:
        auth_token = session.query(AuthToken).filter(AuthToken.token == token).first()
        if auth_token and auth_token.expires_at > datetime.utcnow():
            user = session.query(User).filter(User.id == auth_token.user_id).first()
            if user:
                print(f"Auth token validated successfully for user ID: {user.id}")
                return user.id, user.username # Return ID and username tuple
            else:
                 print(f"User associated with valid token not found (ID: {auth_token.user_id}).")
                 return None # Should not happen if DB is consistent
        else:
            if auth_token:
                 print(f"Auth token found but expired for user ID: {auth_token.user_id}")
            else:
                 print(f"Auth token not found: {token}")
            return None
    except Exception as e:
        print(f"An error occurred validating auth token: {e}")
        return None
    finally:
        session.close()

# --- Main execution block for initialization ---
if __name__ == "__main__":
    print("Initializing database...")
    # This will attempt to connect and create tables if they don't exist.
    # Ensure DB_PASSWORD environment variable is set before running this directly.
    try:
        init_db()
    except ValueError as e:
        print(f"Configuration Error: {e}")
    except Exception as e:
        print(f"Failed to initialize database: {e}")



# --- New Session Token Model and Functions ---

class SessionToken(Base):
    __tablename__ = "session_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(100), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    # Session tokens might have a longer expiry, e.g., 30 days
    expires_at = Column(DateTime, nullable=False)

# --- Update init_db to include SessionToken ---
# (No code change needed here, Base.metadata.create_all handles it)

# --- Session Token Functions ---

def generate_session_token(user_id: int, days_valid: int = 30):
    """Generates and stores a new persistent session token for a user."""
    session = SessionLocal()
    try:
        # Clean up any expired tokens for this user first (optional but good practice)
        session.query(SessionToken).filter(
            SessionToken.user_id == user_id,
            SessionToken.expires_at <= datetime.utcnow()
        ).delete(synchronize_session=False)
        
        token = secrets.token_hex(32)
        expiry = datetime.utcnow() + timedelta(days=days_valid)
        
        new_token = SessionToken(user_id=user_id, token=token, expires_at=expiry)
        session.add(new_token)
        session.commit()
        print(f"Session token generated successfully for user ID: {user_id}")
        return token
    except Exception as e:
        session.rollback()
        print(f"An error occurred generating session token: {e}")
        return None
    finally:
        session.close()

def validate_session_token(token: str):
    """Validates a session token and returns user info if valid."""
    session = SessionLocal()
    try:
        session_token = session.query(SessionToken).filter(SessionToken.token == token).first()
        if session_token and session_token.expires_at > datetime.utcnow():
            user = session.query(User).filter(User.id == session_token.user_id).first()
            if user:
                print(f"Session token validated successfully for user ID: {user.id}")
                # Optionally update expiry on successful validation (sliding session)
                # session_token.expires_at = datetime.utcnow() + timedelta(days=30) 
                # session.commit()
                return user.id, user.username # Return ID and username tuple
            else:
                 print(f"User associated with valid session token not found (ID: {session_token.user_id}).")
                 return None
        else:
            if session_token:
                 print(f"Session token found but expired for user ID: {session_token.user_id}")
                 # Clean up expired token
                 session.delete(session_token)
                 session.commit()
            else:
                 print(f"Session token not found: {token}")
            return None
    except Exception as e:
        session.rollback() # Rollback potential expiry update if error occurs
        print(f"An error occurred validating session token: {e}")
        return None
    finally:
        session.close()

def delete_session_token(token: str):
    """Deletes a specific session token from the database."""
    session = SessionLocal()
    try:
        deleted_count = session.query(SessionToken).filter(SessionToken.token == token).delete(synchronize_session=False)
        session.commit()
        if deleted_count > 0:
            print(f"Session token {token[:8]}... deleted successfully.")
            return True
        else:
            print(f"Session token {token[:8]}... not found for deletion.")
            return False
    except Exception as e:
        session.rollback()
        print(f"An error occurred deleting session token: {e}")
        return False
    finally:
        session.close()

