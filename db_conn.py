from dotenv import load_dotenv
import os
import urllib
from sqlalchemy import create_engine
import pandas as pd
import pyodbc

load_dotenv()

# Adjust the database settings to your Azure database 
server = 'studybuddyhsg.database.windows.net'
database = 'CS-Project-DB'
username = 'CloudSA74f1c350'
password = os.getenv("DB_PASSWORD")
driver= '{ODBC Driver 18 for SQL Server}'

conn = f"""Driver={driver};Server=tcp:{server},1433;Database={database};
Uid={username};Pwd={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"""

params = urllib.parse.quote_plus(conn)
conn_str = 'mssql+pyodbc:///?autocommit=true&odbc_connect={}'.format(params)
DB = create_engine(conn_str, echo=False)

print(pd.read_sql('SELECT * FROM TestTable', DB))