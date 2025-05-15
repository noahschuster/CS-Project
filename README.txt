StudyBuddy

Überblick

StudyBuddy ist eine umfassende Lernmanagement-Anwendung, entwickelt zur Unterstützung von Studierenden bei der Organisation ihres Lernalltags. Die Anwendung nutzt moderne Technologien wie maschinelles Lernen und KI, um personalisierte Lernempfehlungen zu generieren und Prokrastinationsrisiken zu identifizieren.

Funktionen

    Personalisiertes Dashboard: Visualisierung von Lernaktivitäten und kommenden Fristen

    Lerntyp-Analyse: Bestimmung des individuellen Lerntyps für optimierte Lernstrategien

    Kalender-Integration: Synchronisation mit Google Calendar für effizientes Zeitmanagement

    Kursverwaltung: Übersichtliche Verwaltung von Kursen

    KI-gestützte Lernempfehlungen: Massgeschneiderte Lernpläne basierend auf Kursinhalten und Lerntyp

    Prokrastinations-Risiko-Analyse: ML-basierte Einschätzung des persönlichen Prokrastinationsrisikos mit individuellen Gegenmassnahmen

Technische Architektur

Frontend

    Streamlit: Interaktive Benutzeroberfläche mit reaktiven Komponenten

Backend

    Python 3.8+: Hauptprogrammiersprache

    SQLite/Azure SQL: Datenbankmanagement (lokal/cloud-basiert)

    scikit-learn: Framework für maschinelles Lernen

    OpenAI API: KI-gestützte Inhaltsgeneration für Lernempfehlungen

Externe APIs

    Google Calendar API: Kalender-Synchronisation

    OpenAI API: Generierung von personalisierten Lernplänen

    HSG API: Kursinformationen und -materialien

Datenbank

Die Anwendung verwendet standardmässig eine lokale SQLite-Datenbank. Ursprünglich war eine Azure SQL-Datenbank für die Produktionsumgebung vorgesehen, jedoch werden die Azure-Dienste aufgrund aufgebrauchter Free Credits nicht mehr genutzt. Die Anwendung ist so konfiguriert, dass sie nahtlos zwischen lokaler und Cloud-Datenbank wechseln kann.

Ordnerstruktur

CS-Project/
├── .streamlit/ Streamlit-Konfiguration
├── Features/ Kernfunktionalitäten
│ ├── .env Umgebungsvariablen und API-Schlüssel
│ ├── calendar_study.py Kalender-Funktionalität
│ ├── courses.py Kursverwaltung
│ ├── dashboard.py Dashboard-Hauptansicht
│ ├── dashboard_charts.py Diagramme und Visualisierungen
│ ├── database_manager.py Datenbankoperationen
│ ├── db.py Datenbankinitialisierung
│ ├── google_calendar_sync.py Google Kalender-Integration
│ ├── learning_suggestions.py KI-gestützte Lernempfehlungen
│ ├── learning_tipps.py Lernstrategien nach Lerntyp
│ ├── learning_type.py Lerntyp-Analyse
│ ├── local_database.db Lokale SQLite-Datenbank
│ ├── procrastination_data.csv Trainingsdaten für ML-Modell
│ ├── procrastination_risk.py Prokrastinations-Analyse
│ ├── procrastination_risk_model.joblib Trainiertes ML-Modell
├── main.py Anwendungseinstiegspunkt
├── Procrastination_ML_Notebook_Realistic_App_Features.ipynb ML-Modellentwicklung
└── requirements.txt Abhängigkeiten

Installation und Ausführung

Installation

    Entpacken Sie die ZIP-Datei in ein Verzeichnis Ihrer Wahl

    Navigieren Sie zum Projektverzeichnis

    Installieren Sie die Abhängigkeiten:
    pip install -r requirements.txt

Ausführung
Starten Sie die Anwendung mit:
streamlit run main.py

Die Anwendung ist anschliessend unter http://localhost:8501 erreichbar.

Prokrastinations-Risiko-Modell

Das integrierte maschinelle Lernmodell zur Prokrastinations-Risikoanalyse basiert auf einem Random Forest Classifier und berücksichtigt folgende Faktoren:

    Studienjahr

    Sozioökonomischer Hintergrund

    Prüfungsvorbereitungsgewohnheiten

    Wöchentliche Lernstunden

    Akademische Leistung (Notendurchschnitt)

    Zeitmanagement-Praktiken

    Digitale Ablenkungen (Smartphone-Nutzung)

    Konzentrationsfähigkeit während des Lernens

Das Modell klassifiziert das Prokrastinationsrisiko in drei Kategorien:

    Niedriges Risiko (0): Effektives Zeitmanagement, geringe Prokrastinationsneigung

    Mittleres Risiko (1): Gelegentliche Prokrastination mit moderaten Auswirkungen

    Hohes Risiko (2): Häufige Prokrastination mit signifikanten Auswirkungen auf die Leistung

Die Modellentwicklung und -validierung ist im Jupyter Notebook "Procrastination_ML_Notebook_Realistic_App_Features.ipynb" dokumentiert.

Hinweis zu Azure

Die Anwendung wurde ursprünglich mit Azure SQL Database als Cloud-Datenbanklösung konzipiert. Aufgrund aufgebrauchter Azure Free Credits wurde die Anwendung auf lokale SQLite-Datenbanken umgestellt. Die Azure-Funktionalität bleibt im Code erhalten und kann bei Bedarf durch Konfiguration der entsprechenden Umgebungsvariablen in der ".env"-Datei reaktiviert werden.

Technologie

    Frontend: Streamlit

    Backend: Python

    Datenbank: SQLite (lokal), Azure SQL (cloud)

    ML/KI:

        scikit-learn (Random Forest Classifier)

        OpenAI API (GPT-Modelle für Lernplangeneration)

    Externe APIs:

        Google OAuth 2.0

        Google Calendar API

        OpenAI API

    Datenvisualisierung:

        Matplotlib

        Plotly

Hinweis

Die Anwendung speichert Benutzerdaten lokal und überträgt bei aktivierten externen Diensten nur die notwendigen Informationen. API-Schlüssel und Zugangsdaten werden in der ".env"-Datei gespeichert und nicht im Code hartcodiert.