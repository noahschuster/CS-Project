import os
import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship

# Definiere den Pfad für die SQLite-Datenbank
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'local_database.db')
print(f"Erstelle Datenbank unter: {DB_PATH}")

# Erstelle SQLite-Verbindungsstring
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# Erstelle Engine mit SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Nur für SQLite notwendig
)

# Erstelle Base für Modelle
Base = declarative_base()

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

# Speicherung der Kurse, damit diese nicht jedes mal von der API abgerufen werden müssen
class Course(Base):
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(String(100), unique=True, index=True)
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

# Erstelle alle Tabellen in der Datenbank
Base.metadata.create_all(bind=engine)

# Erstelle SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

print("Datenbank wurde erfolgreich erstellt!")
print("Alle Tabellen wurden angelegt. Die Datenbank ist bereit zur Verwendung.")
print(f"Speicherort: {DB_PATH}")

# Aktualisiere die database_manager.py Datei, um die lokale Datenbank zu verwenden
print("\nWichtig: Stelle sicher, dass in deiner database_manager.py die Variable OFFLINE_MODE auf True gesetzt ist.")
