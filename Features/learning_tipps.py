import streamlit as st
from utils import get_user_learning_type

# Tipps basierend auf VARK-Lernstrategien (vark-strategies.docx) citeturn0file0
def display_learning_tips(user_id):
    """
    Zeigt personalisierte Lerntipps basierend auf dem VARK-Lerntyp des Nutzers.
    Unterstützt Einzel- und Multimodal-Präferenzen.
    """
    st.title("Personalisierte Lern-Tipps")
    
    learning_type = get_user_learning_type(user_id)
    if not learning_type:
        st.warning("Du hast deinen Lerntyp noch nicht festgelegt. Gehe zum Abschnitt 'Lerntyp' und mache den Test.")
        return
    
    st.write(f"Basierend auf deinem **{learning_type}**-Lernstil, hier einige Tipps zur Optimierung deines Lernens:")

    # Zuordnung von Lerntypen zu Strategien
tip_mapping = {
    "Visuell": {
        "title": "Visuelle Strategien",
        "tips": [
            "Ersetze Stichwörter durch Symbole oder Diagramme.",
            "Rekonstruiere deine Notizen mit Bildern, Farben, Schriftarten und unterschiedlichen räumlichen Anordnungen.",
            "Überarbeite deine Notizen und suche nach Mustern.",
            "Reduziere 3 Seiten deiner Notizen auf 1.",
            "Zeichne deine Notizen aus dem Gedächtnis neu.",
            "Übersetze deine Visualisierungen zurück in Worte."
        ]
    },
    "Auditiv": {
        "title": "Auditive Strategien",
        "tips": [
            "Besuche Vorlesungen, Diskussionen und Tutorien.",
            "Lasse Lücken in deinen Notizen für spätere Erinnerungen und das Ergänzen fehlender Details.",
            "Erkläre deine Notizen und neuen Ideen einer anderen Person.",
            "Reduziere 3 Seiten deiner Notizen auf 1.",
            "Lies deine zusammengefassten Notizen laut vor; nimm sie auf und höre sie dir an.",
            "Stelle Fragen und diskutiere Themen mit Lehrenden und Kommilitonen.",
            "Hole dir Feedback zu deinem Verständnis, indem du Kommentare anderer anhörst.",
            "Nutze Reime und Eselsbrücken, um dir Konzepte zu merken.",
            "Übe mit alten Prüfungsaufgaben und sprich deine Antworten laut aus.",
            "Stelle dir vor, du würdest mit der Prüferin bzw. dem Prüfer sprechen."
        ]
    },
    "Lesen/Schreiben": {
        "title": "Lese-/Schreib-Strategien",
        "tips": [
            "Lies Lehrbücher, Handbücher und zugewiesene Texte.",
            "Nutze Listen, Glossare und Wörterbücher.",
            "Übersetze Ideen und Prinzipien in eigene Worte.",
            "Organisiere Diagramme, Tabellen und Grafiken in Worte.",
            "Schreibe Essays in strukturierten Absätzen mit Einleitung und Schlussfolgerung.",
            "Strukturiere deine Notizen in Punkte entsprechend einer Hierarchie.",
            "Reduziere 3 Seiten deiner Notizen auf 1, indem du unnötige Details entfernst.",
            "Schreibe deine Notizen mehrmals um.",
            "Lies deine Notizen still und wiederholt durch.",
            "Verfasse Übungsaufgaben schriftlich zur Vorbereitung."
        ]
    },
    "Kinästhetisch": {
        "title": "Kinästhetische Strategien",
        "tips": [
            "Ergänze deine Notizen um Details, die dir möglicherweise entgangen sind.",
            "Sprich über deine Notizen mit einem anderen kinästhetischen Lernenden.",
            "Reduziere 3 Seiten deiner Notizen auf 1.",
            "Nutze Fallstudien, Fotos und Anwendungsbeispiele zur Veranschaulichung abstrakter Konzepte.",
            "Nimm an Laboren und Exkursionen teil und reflektiere, was du gelernt hast.",
            "Rufe dir erfolgreiche Lernerfahrungen in Erinnerung.",
            "Übe Lösungen zu Aufgaben aus alten Prüfungsbögen."
        ]
    }
}

    # Bestimmen, welche Typen angezeigt werden (unterstützt Multimodal-Präferenzen)
types_to_display = []
if learning_type.startswith("Multimodal"):
    start = learning_type.find("(")
    end = learning_type.find(")")
    if start != -1 and end != -1:
        dominant = learning_type[start+1:end].split(",")
        types_to_display = [style.strip() for style in dominant]
else:
    types_to_display = [learning_type]

for lt in types_to_display:
    strategy = tip_mapping.get(lt)
    if strategy:
        st.subheader(strategy["title"])
        for tip in strategy["tips"]:
            st.markdown(f"- {tip}")
    else:
        st.warning(f"Keine Tipps verfügbar für den Lerntyp: {lt}")
