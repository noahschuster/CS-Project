# database_manager.py

import os
import json
import urllib.parse
import secrets
import bcrypt
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Optional, Tuple, List, Dict, Any, Union

from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError, OperationalError


# Am Anfang der database_manager.py
OFFLINE_MODE = True  # Auf False setzen, wenn du wieder online gehen willst

# Load environment variables
load_dotenv()


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


# --- Database Connection Configuration ---
def get_azure_db_engine():
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
        engine = create_engine(
            engine_url, 
            echo=False,
            pool_pre_ping=True,  # Check connection validity before use
            pool_recycle=3600,   # Recycle connections every hour to avoid stale connections
            pool_size=10,        # Maintain a pool of connections
            max_overflow=20      # Allow up to 20 connections to be created beyond the pool_size
        )
        
        # Test connection
        with engine.connect():
            print("Successfully connected to Azure SQL Database.")
        return engine
    except Exception as e:
        print(f"Error connecting to Azure SQL Database: {e}")
        raise

# Initialize engine and session factory
engine = get_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Context manager for database sessions
@contextmanager
def get_db_session():
    """Context manager for database sessions to ensure proper cleanup."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()

# --- SQLAlchemy ORM Models ---
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    learning_type = Column(String(50), nullable=True)
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

class SessionToken(Base):
    __tablename__ = "session_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(100), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

class CourseSchedule(Base):
    __tablename__ = "course_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(String(100), ForeignKey("courses.course_id"), nullable=False)
    start_date = Column(String(10), nullable=False)  # Format: YYYY-MM-DD
    start_time = Column(String(5), nullable=False)   # Format: HH:MM
    end_time = Column(String(5), nullable=False)     # Format: HH:MM
    room = Column(String(255), nullable=True)
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

class CalendarEvent(Base):
    __tablename__ = "calendar_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(100), nullable=False)
    date = Column(String(10), nullable=False)  # Format: YYYY-MM-DD
    time = Column(String(5), nullable=False)   # Format: HH:MM
    event_type = Column(String(50), nullable=False)
    color = Column(String(7), nullable=False)  # Hex color code
    is_deadline = Column(Boolean, default=False)
    priority = Column(Integer, default=2)      # Priority: 1=High, 2=Medium, 3=Low
    created_at = Column(DateTime, default=datetime.utcnow)

class StudyTask(Base):
    __tablename__ = "study_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(String(100), nullable=False)
    course_title = Column(String(255), nullable=False)
    course_code = Column(String(50), nullable=False)
    date = Column(String(10), nullable=False)  # Format: YYYY-MM-DD
    start_time = Column(String(5), nullable=False)  # Format: HH:MM
    end_time = Column(String(5), nullable=False)    # Format: HH:MM
    topic = Column(String(255), nullable=False)
    methods = Column(String(1000), nullable=False)  # JSON-string of learning methods
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# --- Database Initialization ---
def init_db():
    """Creates database tables if they don't exist."""
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables checked/created successfully.")
    except OperationalError as e:
        print(f"Database connection error during init_db: {e}")
    except Exception as e:
        print(f"An error occurred during table creation: {e}")

# --- Password Utilities ---
def hash_password(password: str) -> str:
    """Hashes a password using bcrypt."""
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    try:
        password_bytes = plain_password.encode("utf-8")
        hashed_password_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_password_bytes)
    except Exception:
        return False

# --- User Management ---
def add_user(username: str, password: str, email: str) -> Optional[int]:
    """Adds a new user to the database."""
    with get_db_session() as session:
        try:
            # Check if username or email already exists
            existing_user = session.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            if existing_user:
                print(f"Username '{username}' or Email '{email}' already exists.")
                return None

            hashed_pw = hash_password(password)
            new_user = User(username=username, hashed_password=hashed_pw, email=email)
            session.add(new_user)
            session.flush()  # Flush to get the ID without committing
            print(f"User '{username}' added successfully with ID: {new_user.id}")
            return new_user.id
        except IntegrityError:
            print(f"Database integrity error adding user: {username}")
            return None

def authenticate(username: str, password: str) -> Optional[Tuple[int, str]]:
    """Authenticates a user by username and password."""
    with get_db_session() as session:
        user = session.query(User).filter(User.username == username).first()
        if user and verify_password(password, user.hashed_password):
            print(f"User '{username}' authenticated successfully.")
            return user.id, user.username
        print(f"Authentication failed for user '{username}'.")
        return None

# --- Learning Type Management ---
def get_learning_type_status(user_id: int) -> Tuple[Optional[str], bool]:
    """Gets the user's learning type and completion status."""
    with get_db_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            return user.learning_type, bool(user.learning_type_completed)
        return None, False

def update_learning_type(user_id: int, learning_type: str) -> bool:
    """Updates the user's learning type and marks it as completed."""
    with get_db_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"User not found for ID: {user_id}")
            return False
        
        user.learning_type = learning_type
        user.learning_type_completed = 1
        print(f"Learning type updated for user ID: {user_id}")
        return True

# --- Session Management ---
def log_session(user_id: int) -> Optional[int]:
    """Logs a new user session."""
    with get_db_session() as session:
        new_session = UserSession(user_id=user_id, login_time=datetime.utcnow())
        session.add(new_session)
        session.flush()
        print(f"Session logged for user ID: {user_id}. Session ID: {new_session.id}")
        return new_session.id

# --- Token Management ---
def generate_auth_token(user_id: int) -> Optional[str]:
    """Generates and stores a new authentication token for a user."""
    with get_db_session() as session:
        token = secrets.token_hex(32)
        expiry = datetime.utcnow() + timedelta(days=7)
        
        new_token = AuthToken(user_id=user_id, token=token, expires_at=expiry)
        session.add(new_token)
        print(f"Auth token generated for user ID: {user_id}")
        return token

def validate_auth_token(token: str) -> Optional[Tuple[int, str]]:
    """Validates an authentication token and returns user info if valid."""
    with get_db_session() as session:
        auth_token = session.query(AuthToken).filter(AuthToken.token == token).first()
        if not auth_token or auth_token.expires_at <= datetime.utcnow():
            print(f"Auth token invalid or expired")
            return None
            
        user = session.query(User).filter(User.id == auth_token.user_id).first()
        if not user:
            print(f"User not found for token")
            return None
            
        print(f"Auth token validated for user ID: {user.id}")
        return user.id, user.username

def generate_session_token(user_id: int, days_valid: int = 30) -> Optional[str]:
    """Generates and stores a new persistent session token for a user."""
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
        print(f"Session token generated for user ID: {user_id}")
        return token

def validate_session_token(token: str) -> Optional[Tuple[int, str]]:
    """Validates a session token and returns user info if valid."""
    with get_db_session() as session:
        session_token = session.query(SessionToken).filter(SessionToken.token == token).first()
        if not session_token or session_token.expires_at <= datetime.utcnow():
            if session_token:
                # Clean up expired token
                session.delete(session_token)
            print(f"Session token invalid or expired")
            return None
            
        user = session.query(User).filter(User.id == session_token.user_id).first()
        if not user:
            print(f"User not found for session token")
            return None
            
        # Extend token validity (sliding session)
        session_token.expires_at = datetime.utcnow() + timedelta(days=30)
        print(f"Session token validated for user ID: {user.id}")
        return user.id, user.username

def delete_session_token(token: str) -> bool:
    """Deletes a specific session token from the database."""
    with get_db_session() as session:
        deleted_count = session.query(SessionToken).filter(
            SessionToken.token == token
        ).delete(synchronize_session=False)
        
        if deleted_count > 0:
            print(f"Session token {token[:8]}... deleted successfully.")
            return True
        print(f"Session token {token[:8]}... not found for deletion.")
        return False

# --- Calendar Event Management ---
def save_calendar_event(user_id: int, event_data: Dict[str, Any]) -> Optional[int]:
    """Saves a calendar event to the database."""
    with get_db_session() as session:
        # Check if event type is a deadline type
        is_deadline = event_data.get('type') in ["Exam", "Assignment Due", "Project Due"]
        
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
        print(f"Event saved for user ID: {user_id}. Event ID: {new_event.id}")
        return new_event.id

def get_calendar_events(user_id: int) -> List[Dict[str, Any]]:
    """Gets all calendar events for a user."""
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
    """Updates an existing calendar event."""
    with get_db_session() as session:
        event = session.query(CalendarEvent).filter(
            CalendarEvent.id == event_id
        ).first()
        
        if not event:
            print(f"Event not found for ID: {event_id}")
            return False
            
        # Check if event type is a deadline type
        is_deadline = event_data.get('type') in ["Exam", "Assignment Due", "Project Due"]
        
        event.title = event_data.get('title', event.title)
        event.date = event_data.get('date', event.date)
        event.time = event_data.get('time', event.time)
        event.event_type = event_data.get('type', event.event_type)
        event.color = event_data.get('color', event.color)
        event.is_deadline = is_deadline
        event.priority = event_data.get('priority', event.priority)
        
        print(f"Event updated successfully. Event ID: {event_id}")
        return True

def delete_calendar_event(event_id: int) -> bool:
    """Deletes a calendar event."""
    with get_db_session() as session:
        deleted_count = session.query(CalendarEvent).filter(
            CalendarEvent.id == event_id
        ).delete(synchronize_session=False)
        
        if deleted_count > 0:
            print(f"Event deleted successfully. Event ID: {event_id}")
            return True
        print(f"Event not found for ID: {event_id}")
        return False

# --- Study Task Management ---
def save_study_task(user_id: int, task_data: Dict[str, Any]) -> Optional[int]:
    """Saves a study task to the database."""
    with get_db_session() as session:
        # Convert methods list to JSON string
        methods_json = json.dumps(task_data.get('methods', []))
        
        new_task = StudyTask(
            user_id=user_id,
            course_id=task_data.get('course_id'),
            course_title=task_data.get('course_title', ''),
            course_code=task_data.get('course_code', ''),
            date=task_data.get('date'),
            start_time=task_data.get('start_time'),
            end_time=task_data.get('end_time'),
            topic=task_data.get('topic'),
            methods=methods_json,
            completed=False
        )
        
        session.add(new_task)
        session.flush()
        print(f"Study task saved for user ID: {user_id}. Task ID: {new_task.id}")
        return new_task.id

def get_study_tasks(user_id: int) -> List[Dict[str, Any]]:
    """Gets all study tasks for a user."""
    with get_db_session() as session:
        tasks = session.query(StudyTask).filter(
            StudyTask.user_id == user_id
        ).all()
        
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

def update_study_task(task_id: int, update_data: Dict[str, Any]) -> bool:
    """Updates an existing study task."""
    with get_db_session() as session:
        task = session.query(StudyTask).filter(
            StudyTask.id == task_id
        ).first()
        
        if not task:
            print(f"Study task not found for ID: {task_id}")
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
        
        print(f"Study task updated. Task ID: {task_id}")
        return True

def update_study_task_status(task_id: int, completed: bool) -> bool:
    """Updates the completion status of a study task."""
    with get_db_session() as session:
        task = session.query(StudyTask).filter(
            StudyTask.id == task_id
        ).first()
        
        if not task:
            print(f"Study task not found for ID: {task_id}")
            return False
            
        task.completed = completed
        print(f"Study task status updated. Task ID: {task_id}")
        return True

def delete_study_task(task_id: int) -> bool:
    """Deletes a study task."""
    with get_db_session() as session:
        deleted_count = session.query(StudyTask).filter(
            StudyTask.id == task_id
        ).delete(synchronize_session=False)
        
        if deleted_count > 0:
            print(f"Study task deleted successfully. Task ID: {task_id}")
            return True
        print(f"Study task not found for ID: {task_id}")
        return False

# Initialize database tables if running as main script
if __name__ == "__main__":
    print("Initializing database...")
    try:
        init_db()
    except ValueError as e:
        print(f"Configuration Error: {e}")
    except Exception as e:
        print(f"Failed to initialize database: {e}")