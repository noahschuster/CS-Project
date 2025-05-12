import streamlit as st
import pandas as pd
import joblib
import os
import numpy as np # Required for np.select if used, and general numeric ops

# Pfad zum Modell
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "procrastination_risk_model.joblib")

# Laden des Modells
try:
    model = joblib.load(MODEL_PATH)
except FileNotFoundError:
    st.error(f"Modell konnte nicht unter {MODEL_PATH} gefunden werden. Bitte stellen Sie sicher, dass die Modelldatei vorhanden ist.")
    model = None
except Exception as e:
    st.error(f"Ein Fehler ist beim Laden des Modells aufgetreten: {e}")
    model = None

# Deutsche UI-Optionen zu englischen Modellwerten
map_study_year_de_to_en = {
    "Erstes Studienjahr": "First Year",
    "Zweites Studienjahr": "Second Year",
    "Drittes Studienjahr": "Third Year",
    "Viertes Studienjahr": "Fourth Year"
}
map_socio_economic_de_to_en = {
    "Niedrig": "Low",
    "Untere Mittelschicht": "Lower-middle",
    "Mittelschicht": "Middle",
    "Obere Mittelschicht": "Upper-middle",
    "Hoch": "High"
}
map_assignment_submission_timing_de_to_en = {
    "Immer": "Always",
    "Oft": "Often",
    "Manchmal": "Sometimes",
    "Selten": "Occasionally",
    "Nie": "Never"
}
map_yes_no_de_to_en = {
    "Ja": "Yes",
    "Nein": "No"
}
map_study_hours_de_to_en = {
    "0-5 Stunden": "0-5 hours",
    "6-10 Stunden": "6-10 hours",
    "11-15 Stunden": "11-15 hours",
    "16+ Stunden": "16+ hours"
}
map_cgpa_de_to_en = {
    "Unter 2.50": "Below 2.50",
    "2.50 - 2.99": "2.50 - 2.99",
    "3.00 - 3.49": "3.00 - 3.49",
    "3.50 - 3.74": "3.50 - 3.74",
    "3.75 - 4.00": "3.75 - 4.00"
}
map_time_management_de_to_en = {
    "Immer": "Always",
    "Oft": "Often",
    "Manchmal": "Sometimes",
    "Selten": "Occasionally",
    "Nie": "Never"
}
map_mobile_hours_de_to_en = {
    "1-2 Stunden": "1-2 hours",
    "3-4 Stunden": "3-4 hours",
    "Mehr als 4 Stunden": "More than 4 hours"
}
map_distractions_de_to_en = {
    "Immer": "Always",
    "Oft": "Often",
    "Manchmal": "Sometimes",
    "Selten": "Occasionally",
    "Nie": "Never"
}

# Aktualisierte Liste der Features, die das NEUE Modell verwendet (vor One-Hot-Encoding)
actual_model_features_before_encoding = [
    "study_year",
    "socio-economic_background",
    "assignment_submission_timing",
    "last_minute_exam_preparation",
    "study_hours_per_week",
    "cgpa",
    "use_of_time_management",
    # "procrastination_management_training", # ENTFERNT
    # "procrastination_recovery_strategies", # ENTFERNT
    "hours_spent_on_mobile_non_academic",
    "study_session_distractions"
]

def run_procrastination_questionnaire():
    st.title("Fragebogen zum Prokrastinationsrisiko")
    st.markdown("""
    **Haftungsausschluss:** Dieser Fragebogen dient zur Einschätzung Ihres Prokrastinationsrisikos.
    Die Ergebnisse sind indikativ und ersetzen keine professionelle Beratung.
    Bitte beantworten Sie die Fragen ehrlich, um eine möglichst genaue Einschätzung zu erhalten.
    """)
    st.markdown("---")

    with st.form(key="procrastination_form"):
        st.subheader("Allgemeine Informationen")
        q_study_year = st.selectbox("In welchem Studienjahr befinden Sie sich?", options=list(map_study_year_de_to_en.keys()), key="study_year")
        q_socio_economic = st.selectbox("Wie würden Sie Ihren sozioökonomischen Hintergrund beschreiben?", options=list(map_socio_economic_de_to_en.keys()), key="socio_economic")
        q_cgpa = st.selectbox("Was ist Ihr aktueller Notendurchschnitt (z.B. CGPA)?", options=list(map_cgpa_de_to_en.keys()), key="cgpa")

        st.subheader("Lerngewohnheiten und Zeitmanagement")
        q_study_hours = st.selectbox("Wie viele Stunden lernen Sie durchschnittlich pro Woche?", options=list(map_study_hours_de_to_en.keys()), key="study_hours")
        q_time_management = st.radio("Wie oft nutzen Sie Zeitmanagement-Techniken?", options=list(map_time_management_de_to_en.keys()), key="time_management")
        q_assignment_submission = st.radio("Wie oft geben Sie Aufgaben pünktlich ab?", options=list(map_assignment_submission_timing_de_to_en.keys()), key="assignment_submission")
        q_last_minute_exam = st.radio("Bereiten Sie sich oft in letzter Minute auf Prüfungen vor?", options=list(map_yes_no_de_to_en.keys()), key="last_minute_exam")
        q_distractions = st.radio("Wie oft werden Sie während Lernsitzungen abgelenkt?", options=list(map_distractions_de_to_en.keys()), key="distractions")
        q_mobile_hours = st.selectbox("Wie viele Stunden verbringen Sie täglich mit nicht-akademischen Aktivitäten auf Ihrem Mobiltelefon?", options=list(map_mobile_hours_de_to_en.keys()), key="mobile_hours")

        # Die Fragen zu "procrastination_management_training" und "procrastination_recovery_strategies" wurden entfernt.

        submit_button = st.form_submit_button(label="Risiko einschätzen")

    if submit_button and model:
        input_data_dict = {
            "study_year": map_study_year_de_to_en[q_study_year],
            "socio-economic_background": map_socio_economic_de_to_en[q_socio_economic],
            "assignment_submission_timing": map_assignment_submission_timing_de_to_en[q_assignment_submission],
            "last_minute_exam_preparation": map_yes_no_de_to_en[q_last_minute_exam],
            "study_hours_per_week": map_study_hours_de_to_en[q_study_hours],
            "cgpa": map_cgpa_de_to_en[q_cgpa],
            "use_of_time_management": map_time_management_de_to_en[q_time_management],
            "hours_spent_on_mobile_non_academic": map_mobile_hours_de_to_en[q_mobile_hours],
            "study_session_distractions": map_distractions_de_to_en[q_distractions]
        }

        input_df = pd.DataFrame([input_data_dict])
        
        input_df_encoded = pd.get_dummies(input_df, columns=actual_model_features_before_encoding, prefix_sep="_")

        try:
            model_feature_names = model.feature_names_in_
        except AttributeError:
            st.error("Das geladene Modell hat kein `feature_names_in_` Attribut. Spaltenreihenfolge/Namen können nicht verifiziert werden.")
            model_feature_names = None

        if model_feature_names is not None:
            final_input_df = pd.DataFrame(columns=model_feature_names)
            final_input_df = pd.concat([final_input_df, input_df_encoded], ignore_index=True).fillna(0)
            final_input_df = final_input_df[model_feature_names]
        else:
            st.warning("Modell-Feature-Namen konnten nicht geladen werden. Vorhersage basiert auf den generierten Spalten.")
            # Fallback: Sicherstellen, dass alle Spalten aus input_df_encoded im finalen DataFrame sind
            # und potenziell fehlende Spalten (die das Modell erwartet, aber nicht generiert wurden) hinzugefügt werden.
            # Dies ist weniger robust als die Verwendung von model.feature_names_in_.
            # Eine bessere Fallback-Strategie wäre, eine explizite Liste der erwarteten Spaltennamen zu haben.
            final_input_df = input_df_encoded 
            # Um sicherzustellen, dass alle Spalten, die das Modell erwartet (falls bekannt), vorhanden sind:
            # known_model_cols = ["col1", "col2", ...] # Diese Liste müsste man pflegen
            # for col in known_model_cols:
            #     if col not in final_input_df.columns:
            #         final_input_df[col] = 0
            # final_input_df = final_input_df[known_model_cols] # Reihenfolge sicherstellen

        try:
            prediction = model.predict(final_input_df)
            probabilities = model.predict_proba(final_input_df)
            risk_map = {0: "Niedrig", 1: "Mittel", 2: "Hoch"}
            predicted_risk_level = risk_map.get(prediction[0], "Unbekannt")

            st.subheader("Ergebnis Ihrer Einschätzung")
            st.write(f"Ihr geschätztes Prokrastinationsrisiko ist: **{predicted_risk_level}**")
            
            st.write("Wahrscheinlichkeiten für jede Risikostufe:")
            # Visualisierung der Wahrscheinlichkeiten
            prob_data = {
                "Risikostufe": ["Niedrig", "Mittel", "Hoch"],
                "Wahrscheinlichkeit": probabilities[0]
            }
            prob_df = pd.DataFrame(prob_data)
            
            # Verwenden von st.bar_chart für eine einfache Visualisierung
            st.bar_chart(prob_df.set_index("Risikostufe"))

            # Alternative Textdarstellung (falls gewünscht)
            # st.write(f"- Niedriges Risiko: {probabilities[0][0]:.2%}")
            # st.write(f"- Mittleres Risiko: {probabilities[0][1]:.2%}")
            # st.write(f"- Hohes Risiko: {probabilities[0][2]:.2%}")

        except Exception as e:
            st.error(f"Fehler bei der Vorhersage: {e}")
            st.error(f"Stellen Sie sicher, dass das hochgeladene Modell mit den aktuellen Features trainiert wurde.")
            if model_feature_names:
                 st.error(f"Vom Modell erwartete Spalten: {model_feature_names}")
            st.error(f"Tatsächliche Spalten im Input-DataFrame vor der Vorhersage: {list(final_input_df.columns)}")

    elif submit_button and not model:
        st.error("Das Modell ist nicht geladen. Die Vorhersage kann nicht durchgeführt werden.")

if __name__ == "__main__":
    st.set_page_config(layout="wide")
    run_procrastination_questionnaire()

