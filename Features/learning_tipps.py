import streamlit as st
from utils import get_user_learning_type

# 🌈 Fullscreen Lern-Tipps mit modernen Effekten (VARK-Strategien)
def display_learning_tips(user_id):
    """
    Zeigt motivierende, fullscreen Lerntipps mit Mikroanimationen
    basierend auf dem VARK-Lerntyp des Nutzers.
    """
    # --- CSS für Fullscreen, animierten Verlauf und Karten-Design ---
    st.markdown("""
    <style>
    /* Hauptbereich auf Full Width & Height strecken */
    .css-1lcbmhc.e1tzin5v1 {
        width: 100vw !important;
        padding: 0 !important;
    }
    .css-1lcbmhc.e1tzin5v1 > div {
        margin: 0 !important;
    }
    /* Hintergrund-Verlauf animiert */
    .streamlit-container {
        min-height: 100vh;
        background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
    }
    @keyframes gradientBG {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }
    /* Karten-Styling */
    .tip-card {
      background: rgba(255,255,255,0.85);
      backdrop-filter: blur(8px);
      padding: 2rem;
      border-radius: 1rem;
      margin: 2rem auto;
      max-width: 90vw;
      box-shadow: 0 6px 20px rgba(0,0,0,0.1);
      transition: transform 0.2s;
    }
    .tip-card:hover {
      transform: scale(1.02);
    }
    .tip-card h2 {
      font-size: 2rem;
      margin-bottom: 1rem;
      color: #0366d6;
    }
    .tip-card ul {
      list-style: none;
      padding-left: 0;
    }
    .tip-card li:before {
      content: "💡";
      margin-right: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- Konfetti & Vibrationseffekt ---
    st.components.v1.html("""
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js"></script>
    <script>
      setTimeout(() => confetti({ particleCount: 100, spread: 50 }), 500);
      if (navigator.vibrate) { navigator.vibrate([100,50,100]); }
    </script>
    """, height=0)

    st.title("✨ Personalisierte Lern-Tipps ✨")
    
    learning_type = get_user_learning_type(user_id)
    if not learning_type:
        st.warning("⚠️ Du hast deinen Lerntyp noch nicht festgelegt. Gehe zum Abschnitt 'Lerntyp' und mache den Test.")
        return

    # Mapping VARK-Lerntypen zu Titeln und Tipps
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

    # Unterstützung für Multimodal-Präferenzen
    if learning_type.startswith("Multimodal"):
        s,e = learning_type.find("("), learning_type.find(")")
        types_to_display = [lt.strip() for lt in learning_type[s+1:e].split(",")] if s!=-1 and e!=-1 else []
    else:
        types_to_display = [learning_type]

    # Tipps als Fullscreen-Karten anzeigen
    for lt in types_to_display:
        strategy = tip_mapping.get(lt)
        if not strategy:
            st.warning(f"Keine Tipps verfügbar für den Lerntyp: {lt}")
            continue
        st.markdown(f"""
        <div class='tip-card'>
          <h2>{strategy['title']}</h2>
          <ul>
            {''.join(f'<li>{t}</li>' for t in strategy['tips'])}
          </ul>
        </div>
        """, unsafe_allow_html=True)

    # Abschließendes Konfetti
    st.components.v1.html("""
    <script>
      setTimeout(() => confetti({ particleCount: 150, spread: 70 }), 1200);
    </script>
    """, height=0)
