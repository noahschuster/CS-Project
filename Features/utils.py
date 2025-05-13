import pandas as pd
from datetime import datetime
import streamlit as st
from database_manager import get_db_session, User, UserSession

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

@st.cache_data(ttl=300)
def get_user_learning_type(user_id):
    """Ruft den Lerntyp des Benutzers aus der Datenbank ab."""
    with get_db_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        return user.learning_type if user else None

@st.cache_data(ttl=300)
def get_learning_type_completed(user_id):
    """Überprüft, ob der Benutzer seine Lerntypbewertung abgeschlossen hat."""
    with get_db_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        return bool(user.learning_type_completed) if user else False

def set_learning_type(user_id, learning_type):
    """Legt den Lerntyp des Benutzers fest und markiert ihn als abgeschlossen."""
    with get_db_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user.learning_type = learning_type
            user.learning_type_completed = 1
            session.commit()
            return True
        return False
