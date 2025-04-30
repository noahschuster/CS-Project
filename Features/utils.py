# utils.py
import pandas as pd
from database_manager import SessionLocal, User, UserSession

def get_user_sessions(user_id):
    """Gets the user's study sessions from Azure SQL Database."""
    session = SessionLocal()
    try:
        # Query user sessions from Azure SQL
        query_result = session.query(
            UserSession.login_time,
            UserSession.logout_time
        ).filter(UserSession.user_id == user_id).order_by(UserSession.login_time.desc()).all()
        
        # Convert to DataFrame
        if query_result:
            # Create DataFrame from query results
            df = pd.DataFrame([(
                session.login_time,
                session.logout_time,
                # Calculate duration in hours if logout_time exists
                (session.logout_time - session.login_time).total_seconds() / 3600 
                if session.logout_time else 0
            ) for session in query_result], 
            columns=['login_time', 'logout_time', 'duration_hours'])
            return df
        else:
            return pd.DataFrame(columns=['login_time', 'logout_time', 'duration_hours'])
    except Exception as e:
        print(f"Error getting user sessions: {e}")
        return pd.DataFrame(columns=['login_time', 'logout_time', 'duration_hours'])
    finally:
        session.close()

def get_user_learning_type(user_id):
    """Gets the user's learning type from Azure SQL Database."""
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        return user.learning_type if user else None
    except Exception as e:
        print(f"Error getting user learning type: {e}")
        return None
    finally:
        session.close()

def get_learning_type_completed(user_id):
    """Gets whether the user has completed their learning type assessment."""
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        return bool(user.learning_type_completed) if user else False
    except Exception as e:
        print(f"Error getting learning type completion status: {e}")
        return False
    finally:
        session.close()

def set_learning_type(user_id, learning_type):
    """Sets the user's learning type and marks it as completed."""
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user.learning_type = learning_type
            user.learning_type_completed = 1
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        print(f"Error setting learning type: {e}")
        return False
    finally:
        session.close()
