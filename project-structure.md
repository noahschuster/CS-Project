# 1. Grundgerüst & Nutzerflow
## Login-System
- Nutzerauthentifizierung implementieren (z. B. mit Streamlit-Authenticator).

## Lerntyp-Erfassung
- Fragebogen zur Lernpräferenz erstellen (z. B. "Lernst du besser visuell oder auditiv?").
- ML-Algorithmus integrieren (z. B. Random Forest zur Lerntyp-Klassifizierung).

# 2. Datenbank (DB) & APIs
## Datenbankdesign
- Tabellen für:
  - **User** (Nutzername, Lerntyp, Kurse)
  - **Kalenderdaten** (Deadlines, Lernzeiten)
  - **Progress** (Fortschrittsdaten)
  - **Log-Daten** (Nutzeraktivitäten)

## Courses-API-Anbindung
- Prüfen, ob API verfügbar ist (z. B. Uni-Kursdaten abrufen).

# 3. Haupt-Dashboard
## Rückblick-Feature
- Zeigt vergangene Lernaktivitäten an (z. B. "Letzte Woche: 10h Mathe").

## Effizienz-Report
- Statistik zur Lernzeit vs. Zielerreichung (z. B. Balkendiagramme).

## Lerntipps
- Personalisierte Tipps basierend auf Lerntyp.

# 4. Kernlogik
## Benchmarking-System
- Vergleich der Lernfortschritte mit Kommilitonen (Likert-Skala: "Wie effizient war deine Session?").

## Session-Planung
- Algorithmus zur Vorbereitung der Lernsession (z. B. Priorisierung nach Prüfungsterminen).

# 5. Modifikation & Debugging
## Dynamische Anpassungen
- Nutzerfeedback einbauen (z. B. "War dieser Tipp hilfreich?").

## Log-Daten analysieren
- Fehlerbehebung und Verbesserungen ableiten.

# 6. Testing & Deployment
## Testfälle
- Login, API-Abfragen, ML-Modell validieren.

## Deployment
- Auf Streamlit Share/Heroku hosten.
