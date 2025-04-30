# demo_courses.py
import os
import random
import json
from datetime import datetime
from database_manager import SessionLocal, Course, UserCourse
from sqlalchemy import text

def create_demo_courses():
    """Erstellt Demo-Kurse aus der Fächerzusammenfassung und fügt sie in die Datenbank ein."""
    
    session = SessionLocal()
    try:
        # Fächer aus der Fächerzusammenfassung
        subjects = {
            "BWL": [
                "Geschäftsprozesse und Marketingkonzept",
                "Marktanalyse",
                "Marketingstrategie",
                "Marktleistungsgestaltung",
                "Preisgestaltung, Kommunikation, Distribution",
                "Controlling und Innovation",
                "Management und Managementmodelle",
                "Entscheidungen und Kommunikation",
                "Strategie und Entwicklungsmodi",
                "Struktur und Kultur",
                "Führung und Governance",
                "Umwelt und Interaktionsthemen"
            ],
            "VWL": [
                "Grundlagen der ökonomischen Denkweise",
                "Spezialisierung und Tausch",
                "Angebot und Nachfrage",
                "Externe Effekte und die Grenzen des Marktes",
                "Kosten & Unternehmen auf Märkten mit Vollständiger Konkurrenz",
                "Unternehmensverhalten auf Monopolmärkten",
                "Grundlagen der Spieltheorie",
                "Unternehmensverhalten auf Oligopolmärkten"
            ],
            "Buchhaltung": [
                "Zweck der Buchhaltung, Inventar und Bilanz",
                "Bilanzkonten und Buchungssatz",
                "Erfolgsrechnung",
                "Einzelunternehmen, Warenhandel",
                "Zahlungsverkehr, Produktionsbetrieb",
                "Abschreibungen, Wertberichtigungen, Forderungsverluste",
                "Immobilien, Rechnungsabgrenzung und Rückstellungen",
                "Wertschriften",
                "Aktiengesellschaft",
                "Stille Reserven"
            ],
            "Mathe": [
                "Mathematische Logik Folgen & Reihen",
                "Folgen & Reihen",
                "Funktionen",
                "Differenzierbarkeit I",
                "Differenzierbarkeit II Extremstellen",
                "Taylorpolynome",
                "Funktionen zweier reeller Variablen",
                "Der Satz über die implizite Funktion",
                "Extrema von Funktionen zweier Variablen mit & ohne Nebenbedingungen",
                "Funktionen zweier reeller Variablen",
                "Deskriptive Statistik und Wahrscheinlichkeitstheorie",
                "Optimierungsprobleme in Wirtschaft und Statistik"
            ],
            "Recht": [
                "Einführung ins Privatrecht",
                "Einführung in das Vertragsrecht und Willensbildung",
                "Vertragsgestaltung und -erfüllung",
                "Vertragsänderung, -durchführung und -verletzung",
                "Haftung",
                "Schlechterfüllung und Gewährleistung",
                "Produkthaftung und vertragliche Sanktionen",
                "Erlöschen vertraglicher Pflichten"
            ]
        }
        
        # Funktion zum Erstellen einer Demo-Kursbeschreibung
        def create_demo_description(subject, topics):
            return f"Dieser Kurs behandelt {subject} mit Fokus auf: {', '.join(random.sample(topics, min(3, len(topics))))}."
        
        # Funktion zum Generieren einer zufälligen Kursnummer
        def generate_course_code(subject):
            prefix = ''.join([c for c in subject if c.isupper()])
            if not prefix:
                prefix = subject[:3].upper()
            return f"{prefix}{random.randint(1000, 9999)}"
        
        # Aktuelles Semester und Jahr
        current_term_id = "FS2025"
        current_term_name = "Frühjahrssemester 2025"
        current_term_description = "Frühjahrssemester 2025 (Februar - Juni)"
        
        # Vorhandene Demo-Kurse löschen
        session.execute(text("DELETE FROM user_courses WHERE course_id LIKE 'DEMO%'"))
        session.execute(text("DELETE FROM courses WHERE course_id LIKE 'DEMO%'"))
        session.commit()
        
        # Kurse in die Datenbank einfügen
        courses_added = 0
        course_ids = []
        
        print("Erstelle Demo-Kurse aus der Fächerzusammenfassung...")
        
        for subject, topics in subjects.items():
            # Erstelle einen Hauptkurs für das Fach
            course_id = f"DEMO_{subject.replace(' ', '')}_MAIN"
            meeting_code = generate_course_code(subject)
            title = f"{subject} - Grundlagen"
            description = create_demo_description(subject, topics)
            language_id = 2  # Deutsch
            max_credits = json.dumps([{"value": random.randint(3, 6), "creditSystemId": 1}])
            
            try:
                # Erstelle den Hauptkurs
                new_course = Course(
                    course_id=course_id,
                    meeting_code=meeting_code,
                    title=title,
                    description=description,
                    language_id=language_id,
                    max_credits=max_credits,
                    term_id=current_term_id,
                    term_name=current_term_name,
                    term_description=current_term_description,
                    link_course_info=f"https://example.com/course/{meeting_code}"
                )
                
                session.add(new_course)
                session.commit()
                
                courses_added += 1
                course_ids.append(course_id)
                
                # Erstelle zusätzliche spezialisierte Kurse für jedes Fach
                for i, topic_group in enumerate([topics[i:i+3] for i in range(0, len(topics), 3)]):
                    if not topic_group:
                        continue
                        
                    specialized_id = f"DEMO_{subject.replace(' ', '')}_{i+1}"
                    specialized_code = f"{meeting_code}.{i+1}"
                    specialized_title = f"{subject} - {topic_group[0]}"
                    specialized_desc = f"Vertiefungskurs zu {subject} mit Fokus auf: {', '.join(topic_group)}."
                    
                    # Erstelle den spezialisierten Kurs
                    specialized_course = Course(
                        course_id=specialized_id,
                        meeting_code=specialized_code,
                        title=specialized_title,
                        description=specialized_desc,
                        language_id=language_id,
                        max_credits=json.dumps([{"value": random.randint(2, 4), "creditSystemId": 1}]),
                        term_id=current_term_id,
                        term_name=current_term_name,
                        term_description=current_term_description,
                        link_course_info=f"https://example.com/course/{specialized_code}"
                    )
                    
                    session.add(specialized_course)
                    session.commit()
                    
                    courses_added += 1
                    course_ids.append(specialized_id)
                    
            except Exception as e:
                session.rollback()
                print(f"Fehler beim Hinzufügen des Kurses {title}: {str(e)}")
        
        # Ausgabe der Ergebnisse
        print(f"Erfolgreich {courses_added} Demo-Kurse erstellt!")
        
        # Prüfe, ob Demo-Benutzer existiert
        from database_manager import User, hash_password
        
        demo_user = session.query(User).filter(User.username == 'demo').first()
        
        if not demo_user:
            # Erstelle Demo-Benutzer
            hashed_pw = hash_password('demo123')
            
            demo_user = User(
                username='demo',
                email='demo@example.com',
                hashed_password=hashed_pw,
                learning_type='Visual',
                learning_type_completed=1
            )
            
            session.add(demo_user)
            session.commit()
            
            demo_user_id = demo_user.id
            print(f"\nDemo-Benutzer erstellt mit ID: {demo_user_id}")
        else:
            demo_user_id = demo_user.id
            print(f"\nBestehender Demo-Benutzer gefunden mit ID: {demo_user_id}")
        
        # Bestehende Demo-Kurszuweisungen für diesen Benutzer löschen
        session.query(UserCourse).filter(
            UserCourse.user_id == demo_user_id,
            text("course_id LIKE 'DEMO%'")
        ).delete(synchronize_session=False)
        session.commit()
        
        # Zufällig Kurse auswählen und dem Benutzer zuweisen
        selected_courses = random.sample(course_ids, min(5, len(course_ids)))
        assigned = 0
        
        for course_id in selected_courses:
            try:
                user_course = UserCourse(
                    user_id=demo_user_id,
                    course_id=course_id
                )
                
                session.add(user_course)
                session.commit()
                
                assigned += 1
            except Exception as e:
                session.rollback()
                print(f"Fehler beim Zuweisen des Kurses {course_id} zu Benutzer {demo_user_id}: {str(e)}")
        
        print(f"{assigned} Kurse wurden dem Demo-Benutzer zugewiesen.")
        print("\nDie Demo-Kurse wurden erfolgreich erstellt und können jetzt in der App verwendet werden.")
        
        return courses_added
        
    except Exception as e:
        print(f"Fehler bei der Erstellung der Demo-Kurse: {str(e)}")
        raise
    finally:
        session.close()

# Funktion aufrufen, wenn dieses Skript direkt ausgeführt wird
if __name__ == "__main__":
    create_demo_courses()
