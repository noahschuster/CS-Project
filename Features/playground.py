# test_course_schedule.py
import requests
import json
import time
from datetime import datetime

# HSG API Constants
API_APPLICATION_ID = "587acf1c-24d0-4801-afda-c98f081c4678"
API_VERSION = "1"
API_BASE_URL = "https://integration.preprod.unisg.ch"

def api_request(endpoint, headers=None, timeout=10):
    """Führt eine API-Anfrage durch und gibt das Ergebnis zurück"""
    if headers is None:
        headers = {
            "X-ApplicationId": API_APPLICATION_ID,
            "API-Version": API_VERSION,
            "X-RequestedLanguage": "de"
        }
    
    print(f"API-Anfrage an: {API_BASE_URL}{endpoint}")
    start_time = time.time()
    
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", headers=headers, timeout=timeout)
        elapsed_time = time.time() - start_time
        print(f"Antwort erhalten in {elapsed_time:.2f} Sekunden, Status: {response.status_code}")
        
        if response.ok:
            return response.json()
        else:
            print(f"API-Fehler: {response.status_code} - {response.reason}")
            return None
    except requests.exceptions.Timeout:
        print(f"Timeout bei API-Anfrage nach {timeout} Sekunden")
        return None
    except Exception as e:
        print(f"Fehler bei API-Anfrage: {str(e)}")
        return None

def test_course_schedule():
    """Testet das Abrufen und Speichern von Kurszeiten"""
    # 1. Hole das aktuelle Semester
    print("\n1. Hole das aktuelle Semester...")
    current_term = api_request("/eventapi/timeLines/currentTerm")
    
    if not current_term:
        print("Fehler: Konnte das aktuelle Semester nicht abrufen.")
        return
    
    term_id = current_term.get('id')
    term_name = current_term.get('description')
    print(f"Aktuelles Semester: {term_name} (ID: {term_id})")
    
    # 2. Hole Kurse für das aktuelle Semester
    print("\n2. Hole Kurse für das aktuelle Semester...")
    courses = api_request(f"/eventapi/Events/byTerm/{term_id}")
    
    if not courses or not isinstance(courses, list) or len(courses) == 0:
        print("Fehler: Keine Kurse gefunden.")
        return
    
    print(f"Anzahl gefundener Kurse: {len(courses)}")
    
    # 3. Wähle den ersten Kurs
    first_course = courses[0]
    course_id = first_course.get('id')
    course_title = first_course.get('title')
    course_code = first_course.get('meetingCode', 'N/A')
    
    print(f"\n3. Ausgewählter Kurs: {course_title} ({course_code}) - ID: {course_id}")
    
    # 4. Hole Kurszeiten für den ersten Kurs
    print("\n4. Hole Kurszeiten für den ausgewählten Kurs...")
    course_dates = api_request(f"/eventapi/EventDates/byEvent/{course_id}")
    
    if not course_dates:
        print("Fehler: Keine Kurszeiten gefunden.")
        return
    
    print(f"Anzahl gefundener Termine: {len(course_dates)}")
    
    # 5. Analysiere die Struktur der Kurszeiten
    print("\n5. Analysiere die Struktur der Kurszeiten...")
    if course_dates and len(course_dates) > 0:
        first_date = course_dates[0]
        print("\nErster Termin (Rohdaten):")
        print(json.dumps(first_date, indent=2))
        
        # Überprüfe die Datums- und Zeitfelder
        print("\nDatei- und Zeitfelder:")
        for field in ['startDate', 'endDate', 'date', 'start', 'end']:
            if field in first_date:
                print(f"  {field}: {first_date[field]}")
        
        # Versuche, die Datums- und Zeitfelder zu parsen
        print("\nParsing-Versuche:")
        for field in ['startDate', 'endDate']:
            if field in first_date and first_date[field]:
                value = first_date[field]
                print(f"  {field}: {value}")
                
                # Versuche ISO-Format
                if 'T' in value:
                    parts = value.split('T')
                    print(f"    ISO-Format: Datum = {parts[0]}, Zeit = {parts[1][:5]}")
                
                # Versuche datetime.fromisoformat
                try:
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    print(f"    datetime.fromisoformat: {dt.strftime('%Y-%m-%d %H:%M')}")
                except Exception as e:
                    print(f"    datetime.fromisoformat Fehler: {e}")
    
    # 6. Speichere die Kurszeiten als JSON
    print("\n6. Speichere die Kurszeiten als JSON...")
    try:
        with open('course_dates.json', 'w') as f:
            json.dump(course_dates, f, indent=2)
        print("Kurszeiten erfolgreich als 'course_dates.json' gespeichert.")
    except Exception as e:
        print(f"Fehler beim Speichern der Kurszeiten: {e}")
    
    print("\n=== Test abgeschlossen ===")

if __name__ == "__main__":
    test_course_schedule()
