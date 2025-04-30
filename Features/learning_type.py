import streamlit as st
from utils import get_user_learning_type, set_learning_type

def display_learning_type(user_id):
    st.title("Entdecke deinen Lerntyp - VARK Fragebogen")
    
    current_type = get_user_learning_type(user_id)
    if current_type:
        st.success(f"Dein aktueller Lerntyp: {current_type}")
        st.write("Möchtest du den Test noch einmal machen? Benutze das Formular unten.")
    
    st.subheader("Der VARK Fragebogen (Version 7.8)")
    st.write("Wie lerne ich am besten?")
    
    # Klarere Anweisungen zur Mehrfachauswahl
    st.info("""
    Anleitung:
    - Wähle die Antwort(en), die deine Präferenz für jede Frage am besten erklären.
    - Du kannst mehr als eine Option auswählen, wenn eine einzelne Antwort nicht zu deiner Wahrnehmung passt.
    - Wähle alle zutreffenden Optionen - es gibt keine Begrenzung, wie viele du pro Frage auswählen kannst.
    """)
    
    with st.form("vark_questionnaire"):
        all_answers = {}
        
        # Frage 1
        st.write("1. Du hilfst jemandem, der zum Flughafen, ins Stadtzentrum oder zum Bahnhof möchte. Du würdest:")
        q1_options = [
            "mit ihr mitgehen.",
            "ihr den Weg erklären.",
            "die Wegbeschreibung aufschreiben.",
            "eine Karte zeichnen, zeigen oder ihr eine Karte geben."
        ]
        q1_selections = []
        for i, option in enumerate(q1_options):
            if st.checkbox(option, key=f"q1_{i}"):
                q1_selections.append(chr(97 + i))  # Umwandlung in a, b, c, d
        all_answers[1] = q1_selections
        
        # Frage 2
        st.write("2. Eine Website zeigt ein Video, wie man ein spezielles Diagramm erstellt. Es gibt eine Person, die spricht, einige Listen und Wörter, die beschreiben, was zu tun ist, und einige Diagramme. Du würdest am meisten lernen durch:")
        q2_options = [
            "das Betrachten der Diagramme.",
            "das Zuhören.",
            "das Lesen der Wörter.",
            "das Beobachten der Handlungen."
        ]
        q2_selections = []
        for i, option in enumerate(q2_options):
            if st.checkbox(option, key=f"q2_{i}"):
                q2_selections.append(chr(97 + i))
        all_answers[2] = q2_selections
        
        # Frage 3
        st.write("3. Du planst einen Urlaub für eine Gruppe. Du möchtest Feedback zu deinem Plan. Du würdest:")
        q3_options = [
            "einige der Höhepunkte beschreiben, die sie erleben werden.",
            "eine Karte verwenden, um ihnen die Orte zu zeigen.",
            "ihnen eine Kopie des gedruckten Reiseplans geben.",
            "sie anrufen, ihnen eine Textnachricht oder E-Mail schicken."
        ]
        q3_selections = []
        for i, option in enumerate(q3_options):
            if st.checkbox(option, key=f"q3_{i}"):
                q3_selections.append(chr(97 + i))
        all_answers[3] = q3_selections
        
        # Frage 4
        st.write("4. Du möchtest etwas Besonderes kochen. Du würdest:")
        q4_options = [
            "etwas kochen, das du kennst, ohne Anleitung zu benötigen.",
            "Freunde um Vorschläge bitten.",
            "im Internet oder in Kochbüchern nach Ideen anhand von Bildern suchen.",
            "ein gutes Rezept verwenden."
        ]
        q4_selections = []
        for i, option in enumerate(q4_options):
            if st.checkbox(option, key=f"q4_{i}"):
                q4_selections.append(chr(97 + i))
        all_answers[4] = q4_selections
        
        # Frage 5
        st.write("5. Eine Gruppe von Touristen möchte etwas über die Parks oder Naturschutzgebiete in deiner Region erfahren. Du würdest:")
        q5_options = [
            "über Parks oder Naturschutzgebiete sprechen oder einen Vortrag für sie organisieren.",
            "ihnen Karten und Internetbilder zeigen.",
            "sie zu einem Park oder Naturschutzgebiet mitnehmen und mit ihnen wandern.",
            "ihnen ein Buch oder Broschüren über die Parks oder Naturschutzgebiete geben."
        ]
        q5_selections = []
        for i, option in enumerate(q5_options):
            if st.checkbox(option, key=f"q5_{i}"):
                q5_selections.append(chr(97 + i))
        all_answers[5] = q5_selections
        
        # Frage 6
        st.write("6. Du bist dabei, eine Digitalkamera oder ein Mobiltelefon zu kaufen. Abgesehen vom Preis, was würde deine Entscheidung am meisten beeinflussen?")
        q6_options = [
            "Es auszuprobieren oder zu testen.",
            "Die Details zu lesen oder die Funktionen online zu überprüfen.",
            "Es hat ein modernes Design und sieht gut aus.",
            "Der Verkäufer erzählt mir von seinen Funktionen."
        ]
        q6_selections = []
        for i, option in enumerate(q6_options):
            if st.checkbox(option, key=f"q6_{i}"):
                q6_selections.append(chr(97 + i))
        all_answers[6] = q6_selections
        
        # Frage 7
        st.write("7. Erinnere dich an eine Zeit, als du etwas Neues gelernt hast. Vermeide es, eine körperliche Fähigkeit zu wählen, z.B. Fahrradfahren. Du hast am besten gelernt durch:")
        q7_options = [
            "das Beobachten einer Demonstration.",
            "das Zuhören, während jemand es erklärt, und das Stellen von Fragen.",
            "Diagramme, Karten und Schaubilder - visuelle Hinweise.",
            "schriftliche Anweisungen - z.B. ein Handbuch oder Buch."
        ]
        q7_selections = []
        for i, option in enumerate(q7_options):
            if st.checkbox(option, key=f"q7_{i}"):
                q7_selections.append(chr(97 + i))
        all_answers[7] = q7_selections
        
        # Frage 8
        st.write("8. Du hast ein Problem mit deinem Herzen. Du würdest es vorziehen, dass der Arzt:")
        q8_options = [
            "dir etwas zum Lesen gibt, um zu erklären, was falsch ist.",
            "ein Plastikmodell verwendet, um zu zeigen, was falsch ist.",
            "beschreibt, was falsch ist.",
            "dir ein Diagramm zeigt, was falsch ist."
        ]
        q8_selections = []
        for i, option in enumerate(q8_options):
            if st.checkbox(option, key=f"q8_{i}"):
                q8_selections.append(chr(97 + i))
        all_answers[8] = q8_selections
        
        # Frage 9
        st.write("9. Du möchtest ein neues Programm, eine Fertigkeit oder ein Spiel auf einem Computer lernen. Du würdest:")
        q9_options = [
            "die schriftlichen Anweisungen lesen, die mit dem Programm geliefert wurden.",
            "mit Leuten sprechen, die das Programm kennen.",
            "die Steuerelemente oder die Tastatur benutzen.",
            "den Diagrammen im Buch folgen, das mitgeliefert wurde."
        ]
        q9_selections = []
        for i, option in enumerate(q9_options):
            if st.checkbox(option, key=f"q9_{i}"):
                q9_selections.append(chr(97 + i))
        all_answers[9] = q9_selections
        
        # Frage 10
        st.write("10. Ich mag Websites, die:")
        q10_options = [
            "Dinge haben, auf die ich klicken, verschieben oder ausprobieren kann.",
            "ein interessantes Design und visuelle Elemente haben.",
            "interessante schriftliche Beschreibungen, Listen und Erklärungen haben.",
            "Audiokanäle haben, wo ich Musik, Radioprogramme oder Interviews hören kann."
        ]
        q10_selections = []
        for i, option in enumerate(q10_options):
            if st.checkbox(option, key=f"q10_{i}"):
                q10_selections.append(chr(97 + i))
        all_answers[10] = q10_selections
        
        # Frage 11
        st.write("11. Abgesehen vom Preis, was würde deine Entscheidung, ein neues Sachbuch zu kaufen, am meisten beeinflussen?")
        q11_options = [
            "Sein Aussehen ist ansprechend.",
            "Schnelles Durchlesen von Teilen davon.",
            "Ein Freund spricht darüber und empfiehlt es.",
            "Es enthält reale Geschichten, Erfahrungen und Beispiele."
        ]
        q11_selections = []
        for i, option in enumerate(q11_options):
            if st.checkbox(option, key=f"q11_{i}"):
                q11_selections.append(chr(97 + i))
        all_answers[11] = q11_selections
        
        # Frage 12
        st.write("12. Du benutzt ein Buch, eine CD oder eine Website, um zu lernen, wie man mit deiner neuen Digitalkamera Fotos macht. Du möchtest gerne haben:")
        q12_options = [
            "die Möglichkeit, Fragen zu stellen und über die Kamera und ihre Funktionen zu sprechen.",
            "klare schriftliche Anweisungen mit Listen und Aufzählungspunkten darüber, was zu tun ist.",
            "Diagramme, die die Kamera und die Funktion jedes Teils zeigen.",
            "viele Beispiele für gute und schlechte Fotos und wie man sie verbessern kann."
        ]
        q12_selections = []
        for i, option in enumerate(q12_options):
            if st.checkbox(option, key=f"q12_{i}"):
                q12_selections.append(chr(97 + i))
        all_answers[12] = q12_selections
        
        # Frage 13
        st.write("13. Bevorzugst du einen Lehrer oder Vortragenden, der:")
        q13_options = [
            "Demonstrationen, Modelle oder praktische Übungen verwendet.",
            "Fragen und Antworten, Gespräche, Gruppendiskussionen oder Gastredner einsetzt.",
            "Handouts, Bücher oder Texte zum Lesen verwendet.",
            "Diagramme, Schaubilder oder Grafiken einsetzt."
        ]
        q13_selections = []
        for i, option in enumerate(q13_options):
            if st.checkbox(option, key=f"q13_{i}"):
                q13_selections.append(chr(97 + i))
        all_answers[13] = q13_selections
        
        # Frage 14
        st.write("14. Du hast einen Wettbewerb oder Test abgeschlossen und möchtest Feedback. Du hättest gerne Feedback:")
        q14_options = [
            "anhand von Beispielen aus dem, was du getan hast.",
            "mit einer schriftlichen Beschreibung deiner Ergebnisse.",
            "von jemandem, der es mit dir durchspricht.",
            "anhand von Grafiken, die zeigen, was du erreicht hast."
        ]
        q14_selections = []
        for i, option in enumerate(q14_options):
            if st.checkbox(option, key=f"q14_{i}"):
                q14_selections.append(chr(97 + i))
        all_answers[14] = q14_selections
        
        # Frage 15
        st.write("15. Du wirst in einem Restaurant oder Café Essen auswählen. Du würdest:")
        q15_options = [
            "etwas wählen, das du dort schon einmal hattest.",
            "dem Kellner zuhören oder Freunde um Empfehlungen bitten.",
            "aus den Beschreibungen im Menü wählen.",
            "anschauen, was andere essen oder dir Bilder von jedem Gericht ansehen."
        ]
        q15_selections = []
        for i, option in enumerate(q15_options):
            if st.checkbox(option, key=f"q15_{i}"):
                q15_selections.append(chr(97 + i))
        all_answers[15] = q15_selections
        
        # Frage 16
        st.write("16. Du musst eine wichtige Rede auf einer Konferenz oder zu einem besonderen Anlass halten. Du würdest:")
        q16_options = [
            "Diagramme erstellen oder Grafiken verwenden, um Dinge zu erklären.",
            "einige Schlüsselwörter aufschreiben und das Halten deiner Rede immer wieder üben.",
            "deine Rede aufschreiben und sie durch mehrmaliges Durchlesen lernen.",
            "viele Beispiele und Geschichten sammeln, um den Vortrag realistisch und praktisch zu machen."
        ]
        q16_selections = []
        for i, option in enumerate(q16_options):
            if st.checkbox(option, key=f"q16_{i}"):
                q16_selections.append(chr(97 + i))
        all_answers[16] = q16_selections
        
        submitted = st.form_submit_button("Fragebogen abschicken")
        
        if submitted:
            # VARK Bewertungstabelle
            vark_chart = {
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
            
            # Berechne VARK-Punkte
            v_score = 0
            a_score = 0
            r_score = 0
            k_score = 0
            
            # Zähle die VARK-Punkte basierend auf den Antworten
            for question_num, answers in all_answers.items():
                for answer in answers:
                    if answer in vark_chart[question_num]:
                        vark_type = vark_chart[question_num][answer]
                        if vark_type == "V":
                            v_score += 1
                        elif vark_type == "A":
                            a_score += 1
                        elif vark_type == "R":
                            r_score += 1
                        elif vark_type == "K":
                            k_score += 1
            
            # Ergebnisse anzeigen
            st.subheader("Deine VARK Lernstil-Ergebnisse")
            
            scores_df = {
                "Visuell": v_score,
                "Auditiv": a_score,
                "Lesen/Schreiben": r_score,
                "Kinästhetisch": k_score
            }
            
            # Balkendiagramm erstellen
            st.bar_chart(scores_df)
            
            # Dominanten Lernstil(e) finden
            max_score = max(v_score, a_score, r_score, k_score)
            dominant_styles = []
            
            if v_score == max_score:
                dominant_styles.append("Visuell")
            if a_score == max_score:
                dominant_styles.append("Auditiv")
            if r_score == max_score:
                dominant_styles.append("Lesen/Schreiben")
            if k_score == max_score:
                dominant_styles.append("Kinästhetisch")
            
            # Ergebnisse anzeigen
            st.write(f"Visuell (V): {v_score}")
            st.write(f"Auditiv (A): {a_score}")
            st.write(f"Lesen/Schreiben (R): {r_score}")
            st.write(f"Kinästhetisch (K): {k_score}")
            
            # Bestimmen, ob es eine einzelne oder multimodale Präferenz ist
            learning_type = ""
            if len(dominant_styles) == 1:
                learning_type = dominant_styles[0]
                st.success(f"Dein dominanter Lernstil ist: {learning_type}")
            else:
                learning_type = "Multimodal (" + ", ".join(dominant_styles) + ")"
                st.success(f"Du hast eine multimodale Lernpräferenz: {learning_type}")
            
            # Lerntyp speichern
            if set_learning_type(user_id, learning_type):
                st.session_state.learning_type_completed = True
                st.info("Basierend auf deinem Lerntyp werden wir deine Lernerfahrung anpassen.")
            else:
                st.error("Es gab einen Fehler beim Speichern deines Lerntyps. Bitte versuche es erneut.")
    
    # Platziere den Button außerhalb des Formulars
    if st.session_state.get("learning_type_completed", False):
        if st.button("Weiter zum Dashboard"):
            st.rerun()  # Dies wird einen Neustart auslösen und zum Dashboard führen