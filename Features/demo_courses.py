"""
Demo courses generator for database population.
Creates structured academic courses based on predefined subject categories.
"""
import random
import json
from typing import Dict, List, Optional
from contextlib import contextmanager

from sqlalchemy import text
from database_manager import SessionLocal, Course, UserCourse, User, hash_password


CURRENT_TERM = {
    "id": "FS2025",
    "name": "Frühjahrssemester 2025",
    "description": "Frühjahrssemester 2025 (Februar - Juni)"
}

# Subject category definitions with associated topics
SUBJECTS = {
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

DEMO_COURSE_PREFIX = "DEMO_"
DEMO_USER = {"username": "demo", "password": "demo123", "email": "demo@example.com"}
LANGUAGE_ID_GERMAN = 2


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def generate_course_code(subject: str) -> str:
    """Generate a random course code based on subject."""
    prefix = ''.join(c for c in subject if c.isupper()) or subject[:3].upper()
    return f"{prefix}{random.randint(1000, 9999)}"


def create_course_description(subject: str, topics: List[str]) -> str:
    """Create a concise course description."""
    sample_size = min(3, len(topics))
    return f"Dieser Kurs behandelt {subject} mit Fokus auf: {', '.join(random.sample(topics, sample_size))}."


def get_or_create_demo_user(session) -> int:
    """Get existing demo user or create if not exists."""
    demo_user = session.query(User).filter(User.username == DEMO_USER["username"]).first()
    
    if not demo_user:
        demo_user = User(
            username=DEMO_USER["username"],
            email=DEMO_USER["email"],
            hashed_password=hash_password(DEMO_USER["password"]),
            learning_type='Visual',
            learning_type_completed=1
        )
        session.add(demo_user)
        session.flush()
        print(f"Demo-Benutzer erstellt mit ID: {demo_user.id}")
    else:
        print(f"Bestehender Demo-Benutzer gefunden mit ID: {demo_user.id}")
        
    return demo_user.id


def clean_existing_demo_data(session):
    """Remove existing demo data from database."""
    session.execute(text("DELETE FROM user_courses WHERE course_id LIKE :prefix"), 
                   {"prefix": f"{DEMO_COURSE_PREFIX}%"})
    session.execute(text("DELETE FROM courses WHERE course_id LIKE :prefix"), 
                   {"prefix": f"{DEMO_COURSE_PREFIX}%"})


def create_course(session, course_id: str, title: str, description: str, meeting_code: str) -> None:
    """Create a course with consistent parameters."""
    course = Course(
        course_id=course_id,
        meeting_code=meeting_code,
        title=title,
        description=description,
        language_id=LANGUAGE_ID_GERMAN,
        max_credits=json.dumps([{"value": random.randint(2, 6), "creditSystemId": 1}]),
        term_id=CURRENT_TERM["id"],
        term_name=CURRENT_TERM["name"],
        term_description=CURRENT_TERM["description"],
        link_course_info=f"https://example.com/course/{meeting_code}"
    )
    session.add(course)


def create_demo_courses() -> int:
    """Create demo courses and assign them to demo user."""
    with session_scope() as session:
        # Clean existing demo data
        clean_existing_demo_data(session)
        
        print("Erstelle Demo-Kurse aus der Fächerzusammenfassung...")
        courses_added = 0
        course_ids = []
        
        # Create courses for each subject
        for subject, topics in SUBJECTS.items():
            # Create main course for subject
            subject_key = subject.replace(' ', '')
            main_course_id = f"{DEMO_COURSE_PREFIX}{subject_key}_MAIN"
            meeting_code = generate_course_code(subject)
            
            create_course(
                session=session,
                course_id=main_course_id,
                title=f"{subject} - Grundlagen",
                description=create_course_description(subject, topics),
                meeting_code=meeting_code
            )
            
            courses_added += 1
            course_ids.append(main_course_id)
            
            # Create specialized courses for each topic group
            for i, topic_subset in enumerate([topics[i:i+3] for i in range(0, len(topics), 3)]):
                if not topic_subset:
                    continue
                    
                specialized_id = f"{DEMO_COURSE_PREFIX}{subject_key}_{i+1}"
                specialized_code = f"{meeting_code}.{i+1}"
                
                create_course(
                    session=session,
                    course_id=specialized_id,
                    title=f"{subject} - {topic_subset[0]}",
                    description=f"Vertiefungskurs zu {subject} mit Fokus auf: {', '.join(topic_subset)}.",
                    meeting_code=specialized_code
                )
                
                courses_added += 1
                course_ids.append(specialized_id)
        
        # Get or create demo user
        demo_user_id = get_or_create_demo_user(session)
        
        # Delete existing course assignments for demo user
        session.query(UserCourse).filter(
            UserCourse.user_id == demo_user_id,
            text("course_id LIKE :prefix")
        ).params(prefix=f"{DEMO_COURSE_PREFIX}%").delete(synchronize_session=False)
        
        # Assign random courses to demo user
        selected_courses = random.sample(course_ids, min(5, len(course_ids)))
        
        for course_id in selected_courses:
            session.add(UserCourse(user_id=demo_user_id, course_id=course_id))
            
        print(f"Erfolgreich {courses_added} Demo-Kurse erstellt!")
        print(f"{len(selected_courses)} Kurse wurden dem Demo-Benutzer zugewiesen.")
        print("\nDie Demo-Kurse wurden erfolgreich erstellt und können jetzt in der App verwendet werden.")
        
        return courses_added


if __name__ == "__main__":
    create_demo_courses()