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

# Load environment variables from .env file
load_dotenv()

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

# --- SQLAlchemy ORM Models ---

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    learning_type = Column(String(50), nullable=True) # Kept from original schema
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

