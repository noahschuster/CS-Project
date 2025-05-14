import streamlit as st

# Import Module aus database_manager
from database_manager import get_db_session, User

# Speichert den Lerntyp des Benutzers in der Datenbank
def set_learning_type(user_id, learning_type):
    with get_db_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user.learning_type = learning_type
            user.learning_type_completed = 1
            session.commit()
            return True
        return False

# Ruft den Lerntyp des Benutzers aus der Datenbank ab
@st.cache_data(ttl=300)
def get_user_learning_type(user_id):
    with get_db_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        return user.learning_type if user else None
    
# VARK scoring chart - defined once outside function for efficiency
VARK_CHART = {
    1: {"a": "K", "b": "A", "c": "R", "d": "V"},
    2: {"a": "V", "b": "A", "c": "R", "d": "K"},
    3: {"a": "K", "b": "V", "c": "R", "d": "A"},
    4: {"a": "K", "b": "A", "c": "V", "d": "R"},
    5: {"a": "A", "b": "V", "c": "K", "d": "R"},
    6: {"a": "K", "b": "R", "c": "V", "d": "A"},
    7: {"a": "K", "b": "A", "c": "V", "d": "R"},
    8: {"a": "R", "b": "K", "c": "A", "d": "V"},
    9: {"a": "R", "b": "A", "c": "K", "d": "V"},
    10: {"a": "K", "b": "V", "c": "R", "d": "A"},
    11: {"a": "V", "b": "R", "c": "A", "d": "K"},
    12: {"a": "A", "b": "R", "c": "V", "d": "K"},
    13: {"a": "K", "b": "A", "c": "R", "d": "V"},
    14: {"a": "K", "b": "R", "c": "A", "d": "V"},
    15: {"a": "K", "b": "A", "c": "R", "d": "V"},
    16: {"a": "V", "b": "A", "c": "R", "d": "K"}
}

# Dictionary of questions and options for easier maintenance
QUESTIONS = {
    1: {
        "text": "Du hilfst jemandem, der zum Flughafen, ins Stadtzentrum oder zum Bahnhof möchte. Du würdest:",
        "options": [
            "mit ihr mitgehen.",
            "ihr den Weg erklären.",
            "die Wegbeschreibung aufschreiben.",
            "eine Karte zeichnen, zeigen oder ihr eine Karte geben."
        ]
    },
    2: {
        "text": "Eine Website zeigt ein Video, wie man ein spezielles Diagramm erstellt. Es gibt eine Person, die spricht, einige Listen und Wörter, die beschreiben, was zu tun ist, und einige Diagramme. Du würdest am meisten lernen durch:",
        "options": [
            "das Betrachten der Diagramme.",
            "das Zuhören.",
            "das Lesen der Wörter.",
            "das Beobachten der Handlungen."
        ]
    },
    3: {
        "text": "Du planst einen Urlaub für eine Gruppe. Du möchtest Feedback zu deinem Plan. Du würdest:",
        "options": [
            "einige der Höhepunkte beschreiben, die sie erleben werden.",
            "eine Karte verwenden, um ihnen die Orte zu zeigen.",
            "ihnen eine Kopie des gedruckten Reiseplans geben.",
            "sie anrufen, ihnen eine Textnachricht oder E-Mail schicken."
        ]
    },
    4: {
        "text": "Du möchtest etwas Besonderes kochen. Du würdest:",
        "options": [
            "etwas kochen, das du kennst, ohne Anleitung zu benötigen.",
            "Freunde um Vorschläge bitten.",
            "im Internet oder in Kochbüchern nach Ideen anhand von Bildern suchen.",
            "ein gutes Rezept verwenden."
        ]
    },
    5: {
        "text": "Eine Gruppe von Touristen möchte etwas über die Parks oder Naturschutzgebiete in deiner Region erfahren. Du würdest:",
        "options": [
            "über Parks oder Naturschutzgebiete sprechen oder einen Vortrag für sie organisieren.",
            "ihnen Karten und Internetbilder zeigen.",
            "sie zu einem Park oder Naturschutzgebiet mitnehmen und mit ihnen wandern.",
            "ihnen ein Buch oder Broschüren über die Parks oder Naturschutzgebiete geben."
        ]
    },
    6: {
        "text": "Du bist dabei, eine Digitalkamera oder ein Mobiltelefon zu kaufen. Abgesehen vom Preis, was würde deine Entscheidung am meisten beeinflussen?",
        "options": [
            "Es auszuprobieren oder zu testen.",
            "Die Details zu lesen oder die Funktionen online zu überprüfen.",
            "Es hat ein modernes Design und sieht gut aus.",
            "Der Verkäufer erzählt mir von seinen Funktionen."
        ]
    },
    7: {
        "text": "Erinnere dich an eine Zeit, als du etwas Neues gelernt hast. Vermeide es, eine körperliche Fähigkeit zu wählen, z.B. Fahrradfahren. Du hast am besten gelernt durch:",
        "options": [
            "das Beobachten einer Demonstration.",
            "das Zuhören, während jemand es erklärt, und das Stellen von Fragen.",
            "Diagramme, Karten und Schaubilder - visuelle Hinweise.",
            "schriftliche Anweisungen - z.B. ein Handbuch oder Buch."
        ]
    },
    8: {
        "text": "Du hast ein Problem mit deinem Herzen. Du würdest es vorziehen, dass der Arzt:",
        "options": [
            "dir etwas zum Lesen gibt, um zu erklären, was falsch ist.",
            "ein Plastikmodell verwendet, um zu zeigen, was falsch ist.",
            "beschreibt, was falsch ist.",
            "dir ein Diagramm zeigt, was falsch ist."
        ]
    },
    9: {
        "text": "Du möchtest ein neues Programm, eine Fertigkeit oder ein Spiel auf einem Computer lernen. Du würdest:",
        "options": [
            "die schriftlichen Anweisungen lesen, die mit dem Programm geliefert wurden.",
            "mit Leuten sprechen, die das Programm kennen.",
            "die Steuerelemente oder die Tastatur benutzen.",
            "den Diagrammen im Buch folgen, das mitgeliefert wurde."
        ]
    },
    10: {
        "text": "Ich mag Websites, die:",
        "options": [
            "Dinge haben, auf die ich klicken, verschieben oder ausprobieren kann.",
            "ein interessantes Design und visuelle Elemente haben.",
            "interessante schriftliche Beschreibungen, Listen und Erklärungen haben.",
            "Audiokanäle haben, wo ich Musik, Radioprogramme oder Interviews hören kann."
        ]
    },
    11: {
        "text": "Abgesehen vom Preis, was würde deine Entscheidung, ein neues Sachbuch zu kaufen, am meisten beeinflussen?",
        "options": [
            "Sein Aussehen ist ansprechend.",
            "Schnelles Durchlesen von Teilen davon.",
            "Ein Freund spricht darüber und empfiehlt es.",
            "Es enthält reale Geschichten, Erfahrungen und Beispiele."
        ]
    },
    12: {
        "text": "Du benutzt ein Buch, eine CD oder eine Website, um zu lernen, wie man mit deiner neuen Digitalkamera Fotos macht. Du möchtest gerne haben:",
        "options": [
            "die Möglichkeit, Fragen zu stellen und über die Kamera und ihre Funktionen zu sprechen.",
            "klare schriftliche Anweisungen mit Listen und Aufzählungspunkten darüber, was zu tun ist.",
            "Diagramme, die die Kamera und die Funktion jedes Teils zeigen.",
            "viele Beispiele für gute und schlechte Fotos und wie man sie verbessern kann."
        ]
    },
    13: {
        "text": "Bevorzugst du einen Lehrer oder Vortragenden, der:",
        "options": [
            "Demonstrationen, Modelle oder praktische Übungen verwendet.",
            "Fragen und Antworten, Gespräche, Gruppendiskussionen oder Gastredner einsetzt.",
            "Handouts, Bücher oder Texte zum Lesen verwendet.",
            "Diagramme, Schaubilder oder Grafiken einsetzt."
        ]
    },
    14: {
        "text": "Du hast einen Wettbewerb oder Test abgeschlossen und möchtest Feedback. Du hättest gerne Feedback:",
        "options": [
            "anhand von Beispielen aus dem, was du getan hast.",
            "mit einer schriftlichen Beschreibung deiner Ergebnisse.",
            "von jemandem, der es mit dir durchspricht.",
            "anhand von Grafiken, die zeigen, was du erreicht hast."
        ]
    },
    15: {
        "text": "Du wirst in einem Restaurant oder Café Essen auswählen. Du würdest:",
        "options": [
            "etwas wählen, das du dort schon einmal hattest.",
            "dem Kellner zuhören oder Freunde um Empfehlungen bitten.",
            "aus den Beschreibungen im Menü wählen.",
            "anschauen, was andere essen oder dir Bilder von jedem Gericht ansehen."
        ]
    },
    16: {
        "text": "Du musst eine wichtige Rede auf einer Konferenz oder zu einem besonderen Anlass halten. Du würdest:",
        "options": [
            "Diagramme erstellen oder Grafiken verwenden, um Dinge zu erklären.",
            "einige Schlüsselwörter aufschreiben und das Halten deiner Rede immer wieder üben.",
            "deine Rede aufschreiben und sie durch mehrmaliges Durchlesen lernen.",
            "viele Beispiele und Geschichten sammeln, um den Vortrag realistisch und praktisch zu machen."
        ]
    }
}

def calculate_learning_type(all_answers):
    """Calculate VARK scores from submitted answers."""
    scores = {"V": 0, "A": 0, "R": 0, "K": 0}
    
    for question_num, answers in all_answers.items():
        for answer in answers:
            if answer in VARK_CHART[question_num]:
                scores[VARK_CHART[question_num][answer]] += 1
    
    # Map scores to full names
    score_mapping = {
        "V": ("Visuell", scores["V"]),
        "A": ("Auditiv", scores["A"]),
        "R": ("Lesen/Schreiben", scores["R"]),
        "K": ("Kinästhetisch", scores["K"])
    }
    
    # Find dominant style(s)
    max_score = max(scores.values())
    dominant_styles = [name for key, (name, score) in score_mapping.items() if score == max_score]
    
    # Format result string
    if len(dominant_styles) == 1:
        learning_type = dominant_styles[0]
    else:
        learning_type = f"Multimodal ({', '.join(dominant_styles)})"
    
    return {
        "scores": {name: score for name, score in score_mapping.values()},
        "learning_type": learning_type
    }

def display_learning_type(user_id):
    """Display the VARK learning type questionnaire and process results."""
    st.title("Entdecke deinen Lerntyp - VARK Fragebogen")
    
    # Check for existing learning type
    current_type = get_user_learning_type(user_id)
    if current_type:
        st.success(f"Dein aktueller Lerntyp: {current_type}")
        st.write("Möchtest du den Test noch einmal machen? Benutze das Formular unten.")
    
    st.subheader("Der VARK Fragebogen (Version 7.8)")
    st.write("Wie lerne ich am besten?")
    
    # Clear instructions
    st.info("""
    Anleitung:
    - Wähle die Antwort(en), die deine Präferenz für jede Frage am besten erklären.
    - Du kannst mehrere Optionen pro Frage auswählen.
    - Es gibt keine Begrenzung, wie viele Optionen du pro Frage auswählen kannst.
    """)
    
    with st.form("vark_questionnaire"):
        all_answers = {}
        
        # Generate form questions dynamically
        for q_num, q_data in QUESTIONS.items():
            st.write(f"{q_num}. {q_data['text']}")
            
            # Create selection options
            q_selections = []
            for i, option in enumerate(q_data['options']):
                if st.checkbox(option, key=f"q{q_num}_{i}"):
                    q_selections.append(chr(97 + i))  # Convert to a, b, c, d
            
            all_answers[q_num] = q_selections
        
        submitted = st.form_submit_button("Fragebogen abschicken")
        
        if submitted:
            # Calculate results
            results = calculate_learning_type(all_answers)
            scores = results["scores"]
            learning_type = results["learning_type"]
            
            # Display results
            st.subheader("Deine VARK Lernstil-Ergebnisse")
            
            # Create bar chart
            st.bar_chart(scores)
            
            # Display scores
            for style, score in scores.items():
                st.write(f"{style}: {score}")
            
            # Display learning type
            st.success(f"Dein Lernstil ist: {learning_type}")
            
            # Save learning type
            if set_learning_type(user_id, learning_type):
                st.session_state.learning_type_completed = True
                st.info("Basierend auf deinem Lerntyp werden wir deine Lernerfahrung anpassen.")
            else:
                st.error("Es gab einen Fehler beim Speichern deines Lerntyps. Bitte versuche es erneut.")
    
    # Navigation button outside the form
    if st.session_state.get("learning_type_completed", False):
        if st.button("Weiter zum Dashboard"):
            st.rerun()  # Trigger app rerun to navigate to dashboard