import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Importiere die Basisklasse für die Datenbankmodelle
from database_manager import Base

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

# Erstelle alle Tabellen in der Datenbank
Base.metadata.create_all(bind=engine)

# Erstelle SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

print("Datenbank wurde erfolgreich erstellt!")
print("Alle Tabellen wurden angelegt. Die Datenbank ist bereit zur Verwendung.")
print(f"Speicherort: {DB_PATH}")
