# 1. Grundgerüst & Nutzerflow

## Login-System
- Nutzerauthentifizierung implementieren (z. B. mit Streamlit-Authenticator).
  
## Lerntyp-Erfassung
- Fragebogen zur Lernpräferenz erstellen (z. B. "Lernst du besser visuell oder auditiv?").
- ML-Algorithmus integrieren (z. B. Random Forest zur Lerntyp-Klassifizierung).

**Ordner:** `Login`

---

# 2. Datenbank (DB) & APIs

## Datenbankdesign
Tabellen für:
- User (Nutzername, Lerntyp, Kurse)
- Kalenderdaten (Deadlines, Lernzeiten)
- Progress (Fortschrittsdaten)
- Log-Daten (Nutzeraktivitäten)

## Courses-API-Anbindung
- Prüfen, ob API verfügbar ist (z. B. Uni-Kursdaten abrufen)

**Ordner:** `UserInit_StudyPreferences`

---

# 3. Haupt-Dashboard

## Rückblick-Feature
- Zeigt vergangene Lernaktivitäten an (z. B. "Letzte Woche: 10h Mathe").

## Effizienz-Report
- Statistik zur Lernzeit vs. Zielerreichung (z. B. Balkendiagramme).

## Lerntipps
- Personalisierte Tipps basierend auf Lerntyp.

**Ordner:** `Dashboard`

---

# 4. Kernlogik

## Benchmarking-System
- Vergleich der Lernfortschritte mit Kommilitonen (Likert-Skala: "Wie effizient war deine Session?").

## Session-Planung
- Algorithmus zur Vorbereitung der Lernsession (z. B. Priorisierung nach Prüfungsterminen).

**Ordner:** `CourseOrg`

---

# 5. Modifikation & Debugging

## Dynamische Anpassungen
- Nutzerfeedback einbauen (z. B. "War dieser Tipp hilfreich?").

## Log-Daten analysieren
- Fehlerbehebung und Verbesserungen ableiten.

**Ordner:** *(noch offen)*

---

# 6. Testing & Deployment

## Testfälle
- Login, API-Abfragen, ML-Modell validieren.

## Deployment
- Auf Streamlit Share/Heroku hosten.

**Ordner:** *(noch offen)*

---

# Detaillierte Dateistruktur

## 1. Login
**Inhalt:**
- Nutzerauthentifizierung (Benutzername/Passwort oder Uni-Login).
- Prüfung, ob die Courses-API verfügbar ist ("Anmeldung, dass courses API funktioniert").

**Datei:** `login`

---

## 2. Lerntyp und Präferenzen
**Inhalt:**
- Fragebogen zur Ermittlung des Lerntyps (z. B. "Lernst du besser mit Videos oder Texten?").
- Algorithmus zur Lerntyp-Identifikation ("nutzen wir einen Algorithmus um Lerntyp zu identifizieren").

**Datei:** `UserInit_StudyPreferences`

---

## 3. Dashboard-Hauptseite
**Inhalt:**
- Übersicht über aktuelle Lernpläne und Fortschritt ("Fläche").
- Verlinkung zu allen anderen Seiten.

**Datei:** `dashboard`

---

## 4. SHSG Bib-Plätze belegt
**Inhalt:**
- Sitzplätze in der Uni anzeigen.

**Datei:** `shsg_planner`

---

## 5. Kursverwaltung
**Inhalt:**
- Organisatorische Kursübersicht ("Kurs ist organisatorisch abgebildet").
- Kernlogik: Automatische Lernvorschläge ("Logik gibt Lernvorschläge in welcher Session was zu lernen ist").
- Benchmarking mit Likert-Skala ("Benchmarking nach Lernsession – Likert-Skala").

**Datei:** `CourseOrg`

---

## 6. Lerntipps
**Inhalt:**
- Personalisierte Tipps basierend auf Lerntyp ("Lerntipps").
- Option zur manuellen Anpassung ("Möglichkeit der Modifikation").

**Datei:** `lerntipps`
