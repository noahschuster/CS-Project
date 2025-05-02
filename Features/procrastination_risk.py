# procrastination_risk.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random
from database_manager import get_db_session, User

def display_procrastination_assessment(user_id):
    """
    Displays the procrastination risk assessment page and handles the questionnaire.
    This function allows users to evaluate their procrastination risk level
    and provides personalized recommendations based on their answers.
    """
    st.title("Prokrastinations-Risiko Assessment")
    
    # Check if assessment already completed
    if 'procrastination_assessment_completed' in st.session_state:
        display_procrastination_results(user_id)
        return
    
    st.write("Beantworte die folgenden Fragen, damit wir dein persönliches Prokrastinations-Risiko einschätzen können.")
    st.write("Deine ehrlichen Antworten helfen uns, dir personalisierte Empfehlungen zu geben.")
    
    # Create the assessment form
    with st.form("procrastination_assessment_form"):
        # Study year
        study_year = st.selectbox(
            "In welchem Studienjahr befindest du dich?",
            options=["1. Jahr", "2. Jahr", "3. Jahr", "4. Jahr", "5+ Jahre"]
        )
        
        # Assignment delay frequency
        assignment_delay = st.select_slider(
            "Wie oft verschiebst du die Bearbeitung von Aufgaben auf später?",
            options=["Nie", "Selten", "Manchmal", "Oft", "Sehr oft"]
        )
        
        # Procrastination reasons
        procrastination_reasons = st.multiselect(
            "Aus welchen Gründen schiebst du Aufgaben auf? (Mehrfachauswahl möglich)",
            options=[
                "Perfektionismus",
                "Angst vor Misserfolg",
                "Mangelnde Motivation",
                "Ablenkung durch soziale Medien",
                "Überforderung",
                "Langeweile",
                "Andere Prioritäten"
            ]
        )
        
        # Last-minute exam preparation
        last_minute_prep = st.select_slider(
            "Wie oft lernst du erst kurz vor Prüfungen?",
            options=["Nie", "Selten", "Manchmal", "Oft", "Immer"]
        )
        
        # Study hours per week
        study_hours = st.slider(
            "Wie viele Stunden pro Woche lernst du durchschnittlich?",
            min_value=0, max_value=60, value=15, step=5
        )
        
        # Use of time management
        time_management = st.select_slider(
            "Wie konsequent nutzt du Zeitmanagement-Techniken?",
            options=["Gar nicht", "Kaum", "Gelegentlich", "Regelmäßig", "Sehr konsequent"]
        )
        
        # Procrastination management training
        procrastination_training = st.radio(
            "Hast du bereits an Trainings zur Prokrastinationsbewältigung teilgenommen?",
            options=["Nein", "Ja, aber nicht hilfreich", "Ja, teilweise hilfreich", "Ja, sehr hilfreich"]
        )
        
        # Procrastination recovery strategies
        recovery_strategies = st.multiselect(
            "Welche Strategien nutzt du, um Prokrastination zu überwinden? (Mehrfachauswahl möglich)",
            options=[
                "To-Do-Listen",
                "Pomodoro-Technik",
                "Belohnungssystem",
                "Lerngruppen",
                "Fristen setzen",
                "Ablenkungen eliminieren",
                "Keine spezifische Strategie"
            ]
        )
        
        # Hours spent on mobile non-academic
        mobile_hours = st.slider(
            "Wie viele Stunden verbringst du täglich mit nicht-akademischen Aktivitäten auf dem Smartphone?",
            min_value=0, max_value=12, value=3, step=1
        )
        
        # Study session distractions
        distractions = st.multiselect(
            "Was lenkt dich während des Lernens am häufigsten ab? (Mehrfachauswahl möglich)",
            options=[
                "Soziale Medien",
                "Nachrichten/Messenger",
                "Streaming-Dienste",
                "Videospiele",
                "Freunde/Familie",
                "Haushaltsaufgaben",
                "Gedanken/Tagträume"
            ]
        )
        
        # Submit button
        submitted = st.form_submit_button("Auswertung starten")
        
        if submitted:
            # Calculate risk score (this would be replaced by ML model prediction)
            risk_score = calculate_risk_score(
                study_year, assignment_delay, procrastination_reasons,
                last_minute_prep, study_hours, time_management,
                procrastination_training, recovery_strategies,
                mobile_hours, distractions
            )
            
            # Store results in session state
            st.session_state.procrastination_assessment_completed = True
            st.session_state.procrastination_risk_score = risk_score
            st.session_state.procrastination_data = {
                'study_year': study_year,
                'assignment_delay': assignment_delay,
                'procrastination_reasons': procrastination_reasons,
                'last_minute_prep': last_minute_prep,
                'study_hours': study_hours,
                'time_management': time_management,
                'procrastination_training': procrastination_training,
                'recovery_strategies': recovery_strategies,
                'mobile_hours': mobile_hours,
                'distractions': distractions
            }
            
            # Save to database (would be implemented when database schema is updated)
            # save_procrastination_assessment(user_id, st.session_state.procrastination_data, risk_score)
            
            # Refresh page to show results
            st.rerun()

def calculate_risk_score(study_year, assignment_delay, procrastination_reasons,
                         last_minute_prep, study_hours, time_management,
                         procrastination_training, recovery_strategies,
                         mobile_hours, distractions):
    """
    Placeholder for ML model that would calculate procrastination risk score.
    This function will be replaced by the actual ML model implementation.
    
    Returns a risk score between 0-100.
    """
    # This is a simplified scoring algorithm - would be replaced by ML model
    score = 0
    
    # Assignment delay frequency impact
    delay_map = {"Nie": 0, "Selten": 5, "Manchmal": 10, "Oft": 15, "Sehr oft": 20}
    score += delay_map.get(assignment_delay, 10)
    
    # Number of procrastination reasons impact
    score += min(len(procrastination_reasons) * 5, 20)
    
    # Last-minute exam preparation impact
    prep_map = {"Nie": 0, "Selten": 5, "Manchmal": 10, "Oft": 15, "Immer": 20}
    score += prep_map.get(last_minute_prep, 10)
    
    # Study hours impact (inverse relationship)
    score += max(0, 20 - (study_hours / 3))
    
    # Time management impact (inverse relationship)
    time_map = {"Gar nicht": 20, "Kaum": 15, "Gelegentlich": 10, "Regelmäßig": 5, "Sehr konsequent": 0}
    score += time_map.get(time_management, 10)
    
    # Mobile hours impact
    score += min(mobile_hours * 2, 20)
    
    # Recovery strategies impact (inverse relationship)
    if "Keine spezifische Strategie" in recovery_strategies:
        score += 10
    else:
        score -= min(len(recovery_strategies) * 2, 10)
    
    # Normalize to 0-100 scale
    normalized_score = min(max(int(score * 2.5), 0), 100)
    
    return normalized_score

def display_procrastination_results(user_id):
    """Displays the results of the procrastination risk assessment."""
    risk_score = st.session_state.procrastination_risk_score
    
    st.subheader("Dein Prokrastinations-Risiko Ergebnis")
    
    # Display risk score with color-coded gauge
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if risk_score < 30:
            st.markdown(f"<h1 style='color:green;text-align:center;'>{risk_score}%</h1>", unsafe_allow_html=True)
        elif risk_score < 70:
            st.markdown(f"<h1 style='color:orange;text-align:center;'>{risk_score}%</h1>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h1 style='color:red;text-align:center;'>{risk_score}%</h1>", unsafe_allow_html=True)
    
    with col2:
        # Risk level determination
        if risk_score < 30:
            risk_level = "Niedrig"
            color = "green"
            message = "Du hast ein niedriges Prokrastinations-Risiko. Weiter so!"
        elif risk_score < 70:
            risk_level = "Mittel"
            color = "orange"
            message = "Du hast ein mittleres Prokrastinations-Risiko. Mit einigen Änderungen kannst du deine Produktivität steigern."
        else:
            risk_level = "Hoch"
            color = "red"
            message = "Du hast ein hohes Prokrastinations-Risiko. Dies könnte negative Auswirkungen auf deine Noten haben."
        
        st.markdown(f"<h3 style='color:{color};'>Risiko-Level: {risk_level}</h3>", unsafe_allow_html=True)
        st.write(message)
    
    # Display impact on grades
    st.subheader("Mögliche Auswirkungen auf deine Noten")
    
    if risk_score >= 70:
        st.warning("⚠️ Hohes Prokrastinations-Risiko kann zu signifikant schlechteren Noten führen (durchschnittlich 0.7-1.0 Notenpunkte niedriger).")
        st.write("Studierende mit hohem Prokrastinations-Risiko haben eine 3-mal höhere Wahrscheinlichkeit, Prüfungen nicht zu bestehen.")
    elif risk_score >= 30:
        st.info("⚠️ Mittleres Prokrastinations-Risiko kann zu leicht schlechteren Noten führen (durchschnittlich 0.3-0.5 Notenpunkte niedriger).")
        st.write("Studierende mit mittlerem Prokrastinations-Risiko haben eine 1.5-mal höhere Wahrscheinlichkeit, Abgabefristen zu verpassen.")
    else:
        st.success("✅ Dein niedriges Prokrastinations-Risiko wirkt sich positiv auf deine akademischen Leistungen aus.")
        st.write("Studierende mit niedrigem Prokrastinations-Risiko erzielen im Durchschnitt 0.5 Notenpunkte bessere Ergebnisse.")
    
    # Personalized recommendations
    st.subheader("Personalisierte Empfehlungen")
    
    data = st.session_state.procrastination_data
    
    # Generate recommendations based on assessment data
    recommendations = generate_recommendations(data, risk_score)
    
    for i, (title, desc) in enumerate(recommendations):
        with st.expander(f"{i+1}. {title}"):
            st.write(desc)
    
    # Reset button
    if st.button("Neuen Test starten"):
        if 'procrastination_assessment_completed' in st.session_state:
            del st.session_state.procrastination_assessment_completed
        if 'procrastination_risk_score' in st.session_state:
            del st.session_state.procrastination_risk_score
        if 'procrastination_data' in st.session_state:
            del st.session_state.procrastination_data
        st.rerun()

def generate_recommendations(data, risk_score):
    """Generates personalized recommendations based on assessment data."""
    recommendations = []
    
    # High mobile usage recommendation
    if data['mobile_hours'] > 3:
        recommendations.append((
            "Reduziere deine Smartphone-Nutzung",
            "Deine tägliche Smartphone-Nutzung von mehr als 3 Stunden für nicht-akademische Zwecke ist ein bedeutender Ablenkungsfaktor. "
            "Versuche Apps wie Forest oder Focus Mode zu nutzen, um deine Nutzung zu reduzieren. "
            "Lege feste Zeiten fest, in denen du dein Smartphone nicht nutzt."
        ))
    
    # Poor time management recommendation
    if data['time_management'] in ["Gar nicht", "Kaum"]:
        recommendations.append((
            "Verbessere dein Zeitmanagement",
            "Effektives Zeitmanagement ist entscheidend, um Prokrastination zu bekämpfen. "
            "Beginne mit einfachen Techniken wie der Pomodoro-Methode (25 Minuten Arbeit, 5 Minuten Pause) oder "
            "dem Eisenhower-Prinzip zur Priorisierung von Aufgaben."
        ))
    
    # Last-minute preparation recommendation
    if data['last_minute_prep'] in ["Oft", "Immer"]:
        recommendations.append((
            "Vermeide Last-Minute-Lernen",
            "Last-Minute-Lernen führt zu Stress und schlechteren Ergebnissen. Erstelle einen Lernplan, der den Stoff "
            "über mehrere Wochen verteilt. Nutze aktive Lernmethoden wie Selbsttests und Zusammenfassungen schreiben, "
            "anstatt nur passiv zu lesen."
        ))
    
    # Distraction management
    if "Soziale Medien" in data['distractions'] or "Nachrichten/Messenger" in data['distractions']:
        recommendations.append((
            "Minimiere digitale Ablenkungen",
            "Digitale Ablenkungen sind ein Hauptgrund für Prokrastination. Installiere Browser-Erweiterungen wie StayFocusd "
            "oder Cold Turkey, um ablenkende Websites zu blockieren. Deaktiviere Benachrichtigungen während deiner Lernzeiten."
        ))
    
    # Study environment
    if risk_score > 50:
        recommendations.append((
            "Optimiere deine Lernumgebung",
            "Eine optimale Lernumgebung kann Prokrastination reduzieren. Finde einen ruhigen, aufgeräumten Ort zum Lernen. "
            "Informiere Mitbewohner oder Familie über deine Lernzeiten, um Unterbrechungen zu minimieren."
        ))
    
    # Add general recommendations if we don't have enough specific ones
    if len(recommendations) < 3:
        general_recommendations = [
            (
                "Setze dir klare Ziele",
                "Definiere klare, spezifische und erreichbare Ziele für jede Lerneinheit. "
                "Teile große Aufgaben in kleinere, überschaubare Teilaufgaben auf. "
                "Das Erreichen kleiner Ziele gibt dir ein Erfolgserlebnis und motiviert dich weiterzumachen."
            ),
            (
                "Nutze die 2-Minuten-Regel",
                "Wenn eine Aufgabe weniger als 2 Minuten dauert, erledige sie sofort. "
                "Für größere Aufgaben, starte mit nur 2 Minuten Arbeit - oft wirst du danach weitermachen wollen. "
                "Diese Technik hilft, die anfängliche Hürde zu überwinden."
            ),
            (
                "Belohne dich selbst",
                "Etabliere ein Belohnungssystem für erledigte Aufgaben. Nach erfolgreichen Lerneinheiten "
                "gönn dir etwas, das dir Freude bereitet. Dies stärkt die positive Assoziation mit dem Lernen "
                "und motiviert dich, regelmäßig zu arbeiten."
            ),
            (
                "Finde einen Lernpartner",
                "Suche dir einen Kommilitonen als Lernpartner. Gegenseitige Verantwortlichkeit erhöht die Motivation. "
                "Vereinbart regelmäßige Treffen und setzt euch gemeinsame Ziele. "
                "Erklärt euch gegenseitig den Lernstoff, um euer Verständnis zu vertiefen."
            ),
            (
                "Visualisiere deinen Fortschritt",
                "Führe ein Lerntagebuch oder nutze eine App, um deinen Fortschritt zu verfolgen. "
                "Die visuelle Darstellung deiner Erfolge kann sehr motivierend sein und dir helfen, "
                "deine Produktivitätsmuster zu erkennen."
            )
        ]
        
        # Add needed number of general recommendations
        needed = 3 - len(recommendations)
        recommendations.extend(random.sample(general_recommendations, needed))
    
    return recommendations

def display_dashboard_warning(user_id):
    """
    Displays a warning on the dashboard if the user has a high procrastination risk.
    This function can be called from the dashboard.py file.
    """
    # Check if risk assessment has been completed
    if 'procrastination_risk_score' in st.session_state:
        risk_score = st.session_state.procrastination_risk_score
        
        # Only show warning for high risk
        if risk_score >= 70:
            st.warning(
                "⚠️ **Achtung: Hohes Prokrastinations-Risiko erkannt!** "
                "Deine Lerngewohnheiten könnten negative Auswirkungen auf deine Noten haben. "
                "Schau dir die personalisierten Empfehlungen in der Prokrastinations-Risiko Sektion an."
            )
        elif risk_score >= 50:
            st.info(
                "ℹ️ **Mittleres Prokrastinations-Risiko erkannt.** "
                "Mit einigen Änderungen könntest du deine Produktivität und Noten verbessern. "
                "Schau dir die Empfehlungen in der Prokrastinations-Risiko Sektion an."
            )
    else:
        # If no assessment done yet, show gentle reminder
        if random.random() < 0.3:  # Show only sometimes to avoid being annoying
            st.info(
                "💡 **Tipp:** Mache das Prokrastinations-Risiko Assessment, um zu erfahren, "
                "wie deine Lerngewohnheiten deine Noten beeinflussen könnten und erhalte "
                "personalisierte Empfehlungen zur Verbesserung deiner Produktivität."
            )

# Database schema would need to be updated to store procrastination assessment results
# This function would be implemented when the database schema is updated
def save_procrastination_assessment(user_id, assessment_data, risk_score):
    """
    Saves the procrastination assessment results to the database.
    This is a placeholder function that would be implemented when the database schema is updated.
    """
    # Example implementation (commented out until database schema is updated)
    """
    with get_db_session() as session:
        # Check if assessment already exists for this user
        existing_assessment = session.query(ProcrastinationAssessment).filter(
            ProcrastinationAssessment.user_id == user_id
        ).first()
        
        if existing_assessment:
            # Update existing assessment
            existing_assessment.risk_score = risk_score
            existing_assessment.study_year = assessment_data['study_year']
            existing_assessment.assignment_delay = assessment_data['assignment_delay']
            # ... update other fields
            existing_assessment.updated_at = datetime.utcnow()
        else:
            # Create new assessment
            new_assessment = ProcrastinationAssessment(
                user_id=user_id,
                risk_score=risk_score,
                study_year=assessment_data['study_year'],
                assignment_delay=assessment_data['assignment_delay'],
                # ... other fields
                created_at=datetime.utcnow()
            )
            session.add(new_assessment)
        
        return True
    """
    return True  # Placeholder return until implementation
