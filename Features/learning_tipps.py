import streamlit as st
from learning_type import get_user_learning_type

# Frontend um Learning Tips anzuzeigen. Basiert auf dem mit VARK ermittelten Lerntyp des Benutzers
def display_learning_tips(user_id):
    st.title("Personalisierte Lerntipps")
    
    # Lerntyp mit Fehlerbehandlung abrufen
    learning_type = get_user_learning_type(user_id)

    # Kurze Erklärung zum Lerntyp anzeigen
    st.write(f"Ihr Lerntyp: **{learning_type}**")
    
    # VARK-Lernstrategien mit konkreten Tipps
    tip_mapping = {
        "Visuell": {
            "title": "Visuelle Strategien",
            "tips": [
                "Erstellen Sie Mind-Maps zu komplexen Themen und Zusammenhängen",
                "Verwenden Sie farbige Markierungen für verschiedene Konzepte und Kategorien",
                "Zeichnen Sie Diagramme oder Skizzen zu abstrakten Konzepten",
                "Nutzen Sie Video-Tutorials für schwierige Themen",
                "Verwenden Sie Symbole und Piktogramme in Ihren Notizen",
                "Organisieren Sie Informationen in visuellen Hierarchien oder Flussdiagrammen",
                "Erstellen Sie Infografiken zu wichtigen Themengebieten",
                "Arbeiten Sie mit Karteikarten, die visuelle Elemente enthalten"
            ]
        },
        "Auditiv": {
            "title": "Auditive Strategien",
            "tips": [
                "Nehmen Sie Vorlesungen auf und hören Sie sie mehrmals an",
                "Diskutieren Sie den Lernstoff in Gruppen oder mit Lernpartnern",
                "Erklären Sie komplexe Konzepte laut, als würden Sie sie jemandem beibringen",
                "Nehmen Sie sich selbst beim Erklären wichtiger Konzepte auf",
                "Verwenden Sie Podcasts oder Hörbücher zu Ihren Themen",
                "Erstellen Sie Merksätze oder Reime für wichtige Formeln oder Fakten",
                "Lesen Sie Ihre Notizen laut vor und nehmen Sie sie auf",
                "Setzen Sie Musik strategisch ein: Lernen Sie mit Hintergrundmusik und reproduzieren Sie diese Umgebung in Prüfungssituationen"
            ]
        },
        "Lesen/Schreiben": {
            "title": "Lese-/Schreibstrategien",
            "tips": [
                "Fassen Sie Vorlesungen in eigenen Worten schriftlich zusammen",
                "Erstellen Sie strukturierte Zusammenfassungen mit Überschriften und Unterpunkten",
                "Schreiben Sie Definitionen mehrmals auf und verfeinern Sie sie",
                "Verwenden Sie Fachbücher und wissenschaftliche Artikel zur Vertiefung",
                "Formulieren Sie potenzielle Prüfungsfragen und beantworten Sie diese schriftlich",
                "Führen Sie ein Lerntagebuch zu Ihren Fortschritten und offenen Fragen",
                "Wandeln Sie Diagramme und Grafiken in schriftliche Beschreibungen um",
                "Erstellen Sie Glossare mit wichtigen Begriffen und deren Definitionen"
            ]
        },
        "Kinästhetisch": {
            "title": "Kinästhetische Strategien",
            "tips": [
                "Wenden Sie theoretische Konzepte in praktischen Übungen an",
                "Bauen Sie physische Modelle zu komplexen Themen",
                "Nutzen Sie Rollenspiele oder Simulationen zum Verständnis von Prozessen",
                "Bewegen Sie sich beim Lernen - gehen Sie auf und ab während des Memorierens",
                "Verwenden Sie haptische Materialien wie Modelle oder interaktive Displays",
                "Führen Sie Experimente durch, um theoretische Konzepte zu veranschaulichen",
                "Erstellen Sie Lernspiele oder -aktivitäten zu Ihren Themen",
                "Planen Sie regelmäßige Pausen für Bewegung während längerer Lernphasen"
            ]
        }
    }
    
    # Informationen zu effektiven Lernmethoden für alle Typen
    allgemeine_tipps = [
        "Teilen Sie den Lernstoff in kleinere, überschaubare Einheiten auf",
        "Wenden Sie aktives Wiederholen an: Testen Sie sich selbst regelmäßig",
        "Nutzen Sie verteiltes Lernen statt Marathonsitzungen",
        "Erklären Sie anderen den Lernstoff (Feynman-Technik)",
        "Verbinden Sie neue Informationen mit bereits bekanntem Wissen",
        "Schaffen Sie eine ablenkungsfreie Lernumgebung",
        "Planen Sie regelmäßige Pausen mit der Pomodoro-Technik"
    ]

    # Prüfungsvorbereitungstipps
    pruefungstipps = [
        "Erstellen Sie einen realistischen Zeitplan mit konkreten Lernzielen",
        "Üben Sie mit früheren Prüfungen oder selbst erstellten Testfragen",
        "Identifizieren Sie Ihre Wissenslücken und konzentrieren Sie sich darauf",
        "Bilden Sie Lerngruppen mit Kommilitonen",
        "Reduzieren Sie den Lernstoff auf Kernkonzepte und wichtige Zusammenhänge"
    ]

    # Multimodale Lerntypen verarbeiten
    display_types = []
    if learning_type.startswith("Multimodal"):
        st.write("Als multimodaler Lerntyp profitieren Sie von einer Kombination verschiedener Lernstrategien.")
        start_idx = learning_type.find("(")
        end_idx = learning_type.find(")")
        if start_idx != -1 and end_idx != -1:
            display_types = [lt.strip() for lt in learning_type[start_idx+1:end_idx].split(",")]
    else:
        display_types = [learning_type]

    # Alle Tipps in einer Liste zusammenfassen
    all_tips = []
    
    # Lerntyp-spezifische Tipps hinzufügen
    for lt in display_types:
        strategy = tip_mapping.get(lt)
        if strategy:
            for tip in strategy['tips']:
                all_tips.append({
                    "icon": "💡",
                    "text": tip
                })
    
    # Allgemeine Tipps hinzufügen
    for tip in allgemeine_tipps:
        all_tips.append({
            "icon": "✅",
            "text": tip
        })
    
    # Prüfungstipps hinzufügen
    for tip in pruefungstipps:
        all_tips.append({
            "icon": "📝",
            "text": tip
        })
    
    # Session State für den aktuellen Tipp-Index initialisieren
    if 'tip_index' not in st.session_state:
        st.session_state['tip_index'] = 0
    
    # Aktuellen Tipp anzeigen
    if all_tips:
        current_tip = all_tips[st.session_state['tip_index']]
        
        # Container für den Tipp
        tip_container = st.container()
        with tip_container:
            st.markdown(f"### Tipp {st.session_state['tip_index']+1}/{len(all_tips)}")
            st.markdown(f"{current_tip['icon']} **{current_tip['text']}**")
        
        # Navigation für Tipps
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Vorheriger Tipp"):
                st.session_state['tip_index'] = (st.session_state['tip_index'] - 1) % len(all_tips)
                st.rerun()
        
        with col2:
            if st.button("Nächster Tipp"):
                st.session_state['tip_index'] = (st.session_state['tip_index'] + 1) % len(all_tips)
                st.rerun()
        
        # Fortschrittsbalken
        st.progress((st.session_state['tip_index'] + 1) / len(all_tips))
    else:
        st.warning("Keine Tipps verfügbar für Ihren Lerntyp.")
