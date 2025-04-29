import sqlite3
import pandas as pd

def get_user_sessions(user_id):
    with sqlite3.connect('./data/users.db') as conn:
        try:
            df = pd.read_sql_query("""
                SELECT login_time, logout_time,
                       (julianday(logout_time) - julianday(login_time)) * 24 AS duration_hours
                FROM user_sessions
                WHERE user_id = ?
                ORDER BY login_time DESC
            """, conn, params=(user_id,))
            return df
        except Exception as e:
            return pd.DataFrame()

def get_user_learning_type(user_id):
    with sqlite3.connect('./data/users.db') as conn:
        c = conn.cursor()
        c.execute('SELECT learning_type FROM users WHERE id = ?', (user_id,))
        result = c.fetchone()
        return result[0] if result else None
