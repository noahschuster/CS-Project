# login.py
# This file now acts as an interface to the database_manager module.

# Import the database functions from the centralized manager
from database_manager import (
    authenticate,
    add_user,
    log_session,
    generate_auth_token,
    validate_auth_token,
    init_db # Keep init_db import if you want to trigger it from here, though it's better called separately or on app startup
)

# Optional: Initialize the database if needed when this module is imported.
# Consider calling this explicitly at the start of your main application (main.py) instead.
# init_db()

# The functions below are now just wrappers calling the database_manager functions.
# This keeps login.py lean and focused on the logic flow rather than DB implementation.

# Note: The original file had os, secrets, hashlib, datetime, sqlite3 imports and 
# functions like make_hash, init_db (SQLite version), etc. These are removed 
# as their responsibilities are now handled by database_manager.py using 
# SQLAlchemy, pyodbc, bcrypt, etc. for Azure SQL.

# Example of how the functions are now just pass-throughs (no actual code needed here
# as the imports above make the functions directly available):

# def authenticate(username, password):
#     return db_manager_authenticate(username, password)

# def add_user(username, password, email):
#     return db_manager_add_user(username, password, email)

# ... and so on for log_session, generate_auth_token, validate_auth_token

print("login.py: Using database functions from database_manager")


