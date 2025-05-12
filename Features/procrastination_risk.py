import streamlit as st
import pandas as pd
import joblib
import os

# Pfad zum Modell (angenommen, es befindet sich im Upload-Verzeichnis)
# Im echten Deployment muss dieser Pfad angepasst werden oder das Modell anders geladen werden.
# Für die Entwicklung gehen wir davon aus, dass die Datei im übergeordneten Verzeichnis des Features-Ordners liegt.
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "procrastination_risk_model.joblib")

# Laden des Modells (mit Fehlerbehandlung)
try:
    model = joblib.load(MODEL_PATH)
except FileNotFoundError:
    st.error(f"Modell konnte nicht unter {MODEL_PATH} gefunden werden. Bitte stellen Sie sicher, dass die Modelldatei vorhanden ist.")
    model = None
except Exception as e:
    st.error(f"Ein Fehler ist beim Laden des Modells aufgetreten: {e}")
    model = None

# Mapping von deutschen UI-Optionen zu den englischen Werten, die das Modell erwartet
# Basierend auf feature_options.txt und questionnaire_design_german.md
map_study_year_de_to_en = {
    'Erstes Studienjahr': 'First Year',
    'Zweites Studienjahr': 'Second Year',
    'Drittes Studienjahr': 'Third Year',
    'Viertes Studienjahr': 'Fourth Year'
}

map_socio_economic_de_to_en = {
    'Niedrig': 'Low',
    'Untere Mittelschicht': 'Lower-middle',
    'Mittelschicht': 'Middle',
    'Obere Mittelschicht': 'Upper-middle',
    'Hoch': 'High'
}

map_assignment_submission_timing_de_to_en = {
    'Immer': 'Always',
    'Oft': 'Often',
    'Manchmal': 'Sometimes',
    'Selten': 'Occasionally', # 'Selten' wurde als Mapping für 'Occasionally' im Design festgelegt
    'Nie': 'Never'
}

map_yes_no_de_to_en = {
    'Ja': 'Yes',
    'Nein': 'No'
}

map_effect_procrastination_grades_de_to_en = {
    'Erheblich': 'Significantly',
    'Mäßig': 'Moderately',
    'Leicht': 'Slightly',
    'Überhaupt nicht': 'Not at all'
}

map_stress_procrastination_de_to_en = {
    'Erheblich': 'Significantly',
    'Mäßig': 'Moderately',
    'Leicht': 'Slightly',
    'Überhaupt nicht': 'Not at all'
}

map_study_hours_de_to_en = {
    '0-5 Stunden': '0-5 hours',
    '6-10 Stunden': '6-10 hours',
    '11-15 Stunden': '11-15 hours',
    '16+ Stunden': '16+ hours'
}

map_cgpa_de_to_en = {
    'Unter 2.50': 'Below 2.50',
    '2.50 - 2.99': '2.50 - 2.99',
    '3.00 - 3.49': '3.00 - 3.49',
    '3.50 - 3.74': '3.50 - 3.74',
    '3.75 - 4.00': '3.75 - 4.00'
}

map_time_management_de_to_en = {
    'Immer': 'Always',
    'Oft': 'Often',
    'Manchmal': 'Sometimes',
    'Selten': 'Occasionally',
    'Nie': 'Never'
}

map_mobile_hours_de_to_en = {
    '1-2 Stunden': '1-2 hours',
    '3-4 Stunden': '3-4 hours',
    'Mehr als 4 Stunden': 'More than 4 hours'
}

map_distractions_de_to_en = {
    'Immer': 'Always',
    'Oft': 'Often',
    'Manchmal': 'Sometimes',
    'Selten': 'Occasionally',
    'Nie': 'Never'
}

# Die Original-Features für `procrastination_reasons` aus feature_options.txt
# ['Distractions (e.g.', 'Health issues', 'Lack of interest', 'Overconfidence', 'Personal family problems', 'Poor time management', 'Procrastination due to lack of resources', 'Stress and anxiety', 'Unclear instructions from professors', 'social media)']
# Konsolidierte deutsche Optionen aus questionnaire_design_german.md:
# ['Ablenkungen (z.B. soziale Medien)', 'Gesundheitliche Probleme', 'Interessenmangel', 'Selbstüberschätzung', 'Persönliche/familiäre Probleme', 'Schlechtes Zeitmanagement', 'Mangel an Ressourcen', 'Stress und Angst', 'Unklare Anweisungen von Professoren']
# Wichtig: Das Modell erwartet die Gründe als separate Features (one-hot encoded). Die Verarbeitung muss dies berücksichtigen.
# Die Spaltennamen im Trainingsdatensatz für die Gründe sind: 'procrastination_reasons_Distractions (e.g. social media)', 'procrastination_reasons_Health issues', etc.
# Wir müssen die deutschen Multiselect-Optionen auf diese englischen Spaltennamen mappen.

# Original-Englisch-Optionen für `procrastination_reasons` (aus feature_options.txt, leicht bereinigt)
# Die genauen Spaltennamen im trainierten Modell sind entscheidend!
# Laut Notebook: df_encoded = pd.get_dummies(df, columns=categorical_cols_to_encode, prefix=categorical_cols_to_encode, prefix_sep='_')
# Also wird 'procrastination_reasons' zu 'procrastination_reasons_Lack of interest', etc.
# Die Optionen aus feature_options.txt waren:
# ['Distractions (e.g.', 'Health issues', 'Lack of interest', 'Overconfidence', 'Personal family problems', 'Poor time management', 'Procrastination due to lack of resources', 'Stress and anxiety', 'Unclear instructions from professors', 'social media)']
# Die konsolidierten deutschen Optionen aus dem Design:
# ['Ablenkungen (z.B. soziale Medien)', 'Gesundheitliche Probleme', 'Interessenmangel', 'Selbstüberschätzung', 'Persönliche/familiäre Probleme', 'Schlechtes Zeitmanagement', 'Mangel an Ressourcen', 'Stress und Angst', 'Unklare Anweisungen von Professoren']

# Wir definieren die deutschen Optionen für die Multiselect-Box
procrastination_reasons_options_de = [
    'Ablenkungen (z.B. soziale Medien)',
    'Gesundheitliche Probleme',
    'Interessenmangel',
    'Selbstüberschätzung',
    'Persönliche/familiäre Probleme',
    'Schlechtes Zeitmanagement',
    'Mangel an Ressourcen',
    'Stress und Angst',
    'Unklare Anweisungen von Professoren'
]

# Mapping von deutschen Multiselect-Optionen zu den englischen Basis-Phrasen, die für die One-Hot-Kodierung verwendet wurden.
# Dies muss GENAU den Werten entsprechen, die in der `procrastination_reasons` Spalte VOR der One-Hot-Kodierung waren.
# Aus dem Notebook: `df['procrastination_reasons'].dropna().astype(str).apply(lambda x: [all_reasons.add(reason.strip()) for reason in x.split(',')])`
# Die `feature_options.txt` hat die bereinigten, einzelnen Gründe gezeigt.
# Die Spaltennamen im Modell werden `procrastination_reasons_THE_REASON` sein.
# Wir brauchen die *exakten* englischen Strings, die zu den Spaltennamen führten.
# Die `feature_options.txt` hatte: 'Distractions (e.g.', 'social media)' getrennt. Im Design wurde es zu 'Ablenkungen (z.B. soziale Medien)'.
# Das Notebook hat die Spalte 'procrastination_reasons' direkt für get_dummies verwendet, nachdem die Gründe gesplittet und bereinigt wurden.
# Die Spaltennamen im Modell sind entscheidend. Wir nehmen an, dass die Spaltennamen im Modell den bereinigten englischen Gründen entsprechen.
# Die `feature_options.txt` hatte: ['Distractions (e.g.', 'Health issues', ..., 'social media)']
# Das Notebook-Skript `extract_features.py` hat diese bereits kombiniert/bereinigt.
# Die `feature_options.txt` zeigt die *einzelnen* Gründe nach dem Splitten und `set.add`.
# Die relevanten englischen Gründe (die zu Spaltennamen wie `procrastination_reasons_Lack of interest` führen):
map_procrastination_reasons_de_to_en_keys = {
    'Ablenkungen (z.B. soziale Medien)': ['Distractions (e.g. social media)', 'Distractions (e.g.', 'social media)'], # Mapping auf die möglichen Original-Strings
    'Gesundheitliche Probleme': ['Health issues'],
    'Interessenmangel': ['Lack of interest'],
    'Selbstüberschätzung': ['Overconfidence'],
    'Persönliche/familiäre Probleme': ['Personal family problems'],
    'Schlechtes Zeitmanagement': ['Poor time management'],
    'Mangel an Ressourcen': ['Procrastination due to lack of resources'],
    'Stress und Angst': ['Stress and anxiety'],
    'Unklare Anweisungen von Professoren': ['Unclear instructions from professors']
}

# Liste aller möglichen englischen Gründe, die als Spalten im Modell existieren könnten (basierend auf feature_options.txt)
# Diese Liste muss mit den Spaltennamen übereinstimmen, die das Modell erwartet (nach One-Hot-Encoding von 'procrastination_reasons')
# Die Spaltennamen im Modell sind `procrastination_reasons_` + der jeweilige Grund.
# Wir nehmen die bereinigten Gründe aus `feature_options.txt` als Basis für die Spaltennamen.
expected_reason_model_columns_stems = [
    'Distractions (e.g. social media)', # Angenommen, dies ist der konsolidierte Name
    'Health issues',
    'Lack of interest',
    'Overconfidence',
    'Personal family problems',
    'Poor time management',
    'Procrastination due to lack of resources',
    'Stress and anxiety',
    'Unclear instructions from professors'
]
# Es ist sicherer, die tatsächlichen Spaltennamen aus dem trainierten Modell zu verwenden, falls verfügbar.
# Im Notebook werden die Spalten `X.columns` nach dem Encoding verwendet.
# Die Spaltennamen im Notebook nach Encoding sind: Index(['study_year_First Year', 'study_year_Fourth Year', ... , 'procrastination_reasons_Distractions (e.g. social media)', ...])

def run_procrastination_questionnaire():
    st.title("Fragebogen zum Prokrastinationsrisiko")

    st.markdown("""
    **Haftungsausschluss:** Dieser Fragebogen dient zur Einschätzung Ihres Prokrastinationsrisikos.
    Die Ergebnisse sind indikativ und ersetzen keine professionelle Beratung.
    Bitte beantworten Sie die Fragen ehrlich, um eine möglichst genaue Einschätzung zu erhalten.
    """)
    st.markdown("---")

    # Eingabeformular
    with st.form(key='procrastination_form'):
        st.subheader("Allgemeine Informationen")
        q_study_year = st.selectbox(
            "In welchem Studienjahr befinden Sie sich?",
            options=list(map_study_year_de_to_en.keys()),
            key='study_year'
        )
        q_socio_economic = st.selectbox(
            "Wie würden Sie Ihren sozioökonomischen Hintergrund beschreiben?",
            options=list(map_socio_economic_de_to_en.keys()),
            key='socio_economic'
        )
        q_cgpa = st.selectbox(
            "Was ist Ihr aktueller Notendurchschnitt (z.B. CGPA)?",
            options=list(map_cgpa_de_to_en.keys()),
            key='cgpa'
        )

        st.subheader("Lerngewohnheiten und Zeitmanagement")
        q_study_hours = st.selectbox(
            "Wie viele Stunden lernen Sie durchschnittlich pro Woche?",
            options=list(map_study_hours_de_to_en.keys()),
            key='study_hours'
        )
        q_time_management = st.radio(
            "Wie oft nutzen Sie Zeitmanagement-Techniken?",
            options=list(map_time_management_de_to_en.keys()),
            key='time_management'
        )
        q_assignment_submission = st.radio(
            "Wie oft geben Sie Aufgaben pünktlich ab?",
            options=list(map_assignment_submission_timing_de_to_en.keys()),
            key='assignment_submission'
        )
        q_last_minute_exam = st.radio(
            "Bereiten Sie sich oft in letzter Minute auf Prüfungen vor?",
            options=list(map_yes_no_de_to_en.keys()),
            key='last_minute_exam'
        )
        q_distractions = st.radio(
            "Wie oft werden Sie während Lernsitzungen abgelenkt?",
            options=list(map_distractions_de_to_en.keys()),
            key='distractions'
        )
        q_mobile_hours = st.selectbox(
            "Wie viele Stunden verbringen Sie täglich mit nicht-akademischen Aktivitäten auf Ihrem Mobiltelefon?",
            options=list(map_mobile_hours_de_to_en.keys()),
            key='mobile_hours'
        )

        st.subheader("Auswirkungen und Umgang mit Prokrastination")
        q_effect_on_grades = st.radio(
            "Wie stark wirkt sich Prokrastination Ihrer Meinung nach auf Ihre Noten aus?",
            options=list(map_effect_procrastination_grades_de_to_en.keys()),
            key='effect_on_grades'
        )
        q_procrastination_grade_outcome = st.radio(
            "Glauben Sie, dass Prokrastination Ihre Notenergebnisse negativ beeinflusst hat?",
            options=list(map_yes_no_de_to_en.keys()),
            key='procrastination_grade_outcome'
        )
        q_stress = st.radio(
            "Wie gestresst fühlen Sie sich aufgrund von Prokrastination?",
            options=list(map_stress_procrastination_de_to_en.keys()),
            key='stress'
        )
        q_training = st.radio(
            "Haben Sie jemals an einem Training zum Prokrastinationsmanagement teilgenommen?",
            options=list(map_yes_no_de_to_en.keys()),
            key='training'
        )
        q_recovery_strategies = st.radio(
            "Nutzen Sie Strategien, um sich von Prokrastination zu erholen?",
            options=list(map_yes_no_de_to_en.keys()),
            key='recovery_strategies'
        )
        q_procrastination_reasons = st.multiselect(
            "Was sind die Hauptgründe für Ihre Prokrastination? (Mehrfachauswahl möglich)",
            options=procrastination_reasons_options_de,
            key='procrastination_reasons'
        )

        submit_button = st.form_submit_button(label='Risiko einschätzen')

    if submit_button and model:
        # Daten für das Modell vorbereiten
        # Die Reihenfolge der Features muss exakt der Trainingsreihenfolge entsprechen!
        # Aus dem Notebook: features_to_use (nachdem 'Timestamp' und 'assignment_delay_frequency' entfernt wurden)
        # Und dann one-hot encoded.
        # Die Spaltennamen im trainierten Modell sind der Schlüssel.
        # Wir erstellen ein Dictionary mit den englischen Werten
        
        input_data_dict = {
            'study_year': map_study_year_de_to_en[q_study_year],
            'socio-economic_background': map_socio_economic_de_to_en[q_socio_economic],
            'assignment_submission_timing': map_assignment_submission_timing_de_to_en[q_assignment_submission],
            'last_minute_exam_preparation': map_yes_no_de_to_en[q_last_minute_exam],
            'effect_of_procrastination_on_grades': map_effect_procrastination_grades_de_to_en[q_effect_on_grades],
            'procrastination_and_grade_outcome': map_yes_no_de_to_en[q_procrastination_grade_outcome],
            'stress_due_to_procrastination': map_stress_procrastination_de_to_en[q_stress],
            'study_hours_per_week': map_study_hours_de_to_en[q_study_hours],
            'cgpa': map_cgpa_de_to_en[q_cgpa],
            'use_of_time_management': map_time_management_de_to_en[q_time_management],
            'procrastination_management_training': map_yes_no_de_to_en[q_training],
            'procrastination_recovery_strategies': map_yes_no_de_to_en[q_recovery_strategies],
            'hours_spent_on_mobile_non_academic': map_mobile_hours_de_to_en[q_mobile_hours],
            'study_session_distractions': map_distractions_de_to_en[q_distractions]
            # 'procrastination_reasons' wird speziell behandelt
        }

        # DataFrame für die Eingabe erstellen (eine Zeile)
        input_df_non_reasons = pd.DataFrame([input_data_dict])

        # One-Hot-Encoding für 'procrastination_reasons'
        # Erstelle Spalten für alle möglichen Gründe, initialisiert mit 0
        for reason_stem in expected_reason_model_columns_stems:
            col_name = f"procrastination_reasons_{reason_stem}" # So sind die Spalten im Modell benannt
            input_df_non_reasons[col_name] = 0

        # Setze 1 für ausgewählte Gründe
        for de_reason in q_procrastination_reasons:
            # Finde die entsprechenden englischen Stems
            english_stems_for_de_reason = map_procrastination_reasons_de_to_en_keys.get(de_reason, [])
            for en_stem in english_stems_for_de_reason:
                # Finde die passende Spalte im DataFrame (muss exakt übereinstimmen)
                # Es ist möglich, dass ein deutscher Grund auf mehrere englische Original-Gründe gemappt wurde (z.B. 'Distractions (e.g.' und 'social media)')
                # Wir müssen sicherstellen, dass wir die richtigen Spalten setzen.
                # Die `expected_reason_model_columns_stems` sollten die genauen Stems sein, die zu Spaltennamen führen.
                if en_stem in expected_reason_model_columns_stems:
                    col_name_to_set = f"procrastination_reasons_{en_stem}"
                    if col_name_to_set in input_df_non_reasons.columns:
                         input_df_non_reasons[col_name_to_set] = 1
                    # else: st.warning(f"Spalte {col_name_to_set} nicht im Input DataFrame für Gründe gefunden. Überprüfen Sie das Mapping.")
                # else: st.warning(f"Englischer Stamm '{en_stem}' für Grund '{de_reason}' nicht in erwarteten Modellspaltenstämmen. Überprüfen Sie das Mapping.")

        # Die Spalten, die das Modell erwartet (aus dem Notebook, nach dem Encoding)
        # Dies ist der kritischste Teil: Die Spalten des input_df müssen *exakt* denen des Trainingsdatensatzes entsprechen
        # in Reihenfolge und Benennung.
        # model.feature_names_in_ enthält die Namen der Features, wie sie das Modell erwartet.
        try:
            model_feature_names = model.feature_names_in_
        except AttributeError:
            st.error("Das geladene Modell hat kein `feature_names_in_` Attribut. Die Spaltenreihenfolge kann nicht überprüft werden. Die Vorhersage könnte fehlerhaft sein.")
            # Fallback: Versuche, die Spalten aus dem Notebook zu rekonstruieren (sehr fehleranfällig)
            # Diese Liste muss manuell erstellt werden, basierend auf dem Notebook-Output von X_train.columns
            # Beispiel: model_feature_names = ['study_year_First Year', 'study_year_Fourth Year', ...]
            # Für jetzt lassen wir es so, aber das ist ein großes Risiko.
            model_feature_names = None 

        # One-Hot-Encoding für die anderen kategorischen Features
        # Die Spalten, die one-hot encoded werden müssen (außer 'procrastination_reasons', das schon behandelt wurde)
        categorical_cols_to_encode_for_model = [
            'study_year', 'socio-economic_background', 'assignment_submission_timing',
            'last_minute_exam_preparation', 'effect_of_procrastination_on_grades',
            'procrastination_and_grade_outcome', 'stress_due_to_procrastination',
            'study_hours_per_week', 'cgpa', 'use_of_time_management',
            'procrastination_management_training', 'procrastination_recovery_strategies',
            'hours_spent_on_mobile_non_academic', 'study_session_distractions'
        ]
        
        input_df_encoded = pd.get_dummies(input_df_non_reasons, columns=categorical_cols_to_encode_for_model, prefix_sep='_')

        # Sicherstellen, dass alle vom Modell erwarteten Spalten vorhanden sind und in der richtigen Reihenfolge
        if model_feature_names is not None:
            final_input_df = pd.DataFrame(columns=model_feature_names)
            final_input_df = final_input_df.append(input_df_encoded, ignore_index=True).fillna(0)
            # Nur die Spalten behalten, die das Modell erwartet, und in der richtigen Reihenfolge
            final_input_df = final_input_df[model_feature_names]
        else:
            # Ohne model_feature_names ist dies ein Schuss ins Blaue
            # Wir müssen annehmen, dass pd.get_dummies die Spalten in einer konsistenten (aber nicht unbedingt korrekten) Reihenfolge erzeugt.
            # Es ist besser, die Spaltennamen explizit aus dem Training zu haben.
            st.warning("Die Spaltennamen und -reihenfolge für das Modell konnten nicht verifiziert werden. Die Vorhersage könnte ungenau sein.")
            final_input_df = input_df_encoded
            # Versuch, fehlende Spalten (die im Training da waren, aber nicht in dieser Eingabe) mit 0 aufzufüllen
            # Dies ist immer noch riskant, wenn die Reihenfolge nicht stimmt.
            # Man bräuchte eine Referenzliste aller Spalten aus dem Training.

        # Vorhersage
        try:
            prediction = model.predict(final_input_df)
            probabilities = model.predict_proba(final_input_df)
            
            # Mapping der numerischen Vorhersage zu Risikostufen
            # Aus dem Notebook: 0 -> Low, 1 -> Medium, 2 -> High (nachdem assignment_delay_frequency gemappt wurde)
            # Die Zielvariable 'procrastination_risk_level' wurde so erstellt:
            # conditions = [
            #    (df['assignment_delay_frequency'] == 'Never') | (df['assignment_delay_frequency'] == 'Occasionally'), # Low
            #    (df['assignment_delay_frequency'] == 'Sometimes'),                                                  # Medium
            #    (df['assignment_delay_frequency'] == 'Often') | (df['assignment_delay_frequency'] == 'Always')        # High
            # ]
            # choices = [0, 1, 2] # Low, Medium, High
            # df['procrastination_risk_level'] = np.select(conditions, choices, default=1) # Default zu Medium, falls Logik nicht greift
            # Also: 0 = Niedrig, 1 = Mittel, 2 = Hoch

            risk_map = {0: "Niedrig", 1: "Mittel", 2: "Hoch"}
            predicted_risk_level = risk_map.get(prediction[0], "Unbekannt")

            st.subheader("Ergebnis Ihrer Einschätzung")
            st.write(f"Ihr geschätztes Prokrastinationsrisiko ist: **{predicted_risk_level}**")
            
            st.write("Wahrscheinlichkeiten für jede Risikostufe:")
            st.write(f"- Niedriges Risiko: {probabilities[0][0]:.2%}")
            st.write(f"- Mittleres Risiko: {probabilities[0][1]:.2%}")
            st.write(f"- Hohes Risiko: {probabilities[0][2]:.2%}")

        except Exception as e:
            st.error(f"Fehler bei der Vorhersage: {e}")
            st.error("Mögliche Ursache: Die eingegebenen Daten passen nicht zu dem, was das Modell erwartet. Überprüfen Sie die Spaltennamen und Datentypen, insbesondere nach dem One-Hot-Encoding.")
            st.error(f"Erwartete Spalten (falls verfügbar): {model_feature_names}")
            st.error(f"Tatsächliche Spalten im Input-DataFrame vor der Vorhersage: {list(final_input_df.columns)}")

    elif submit_button and not model:
        st.error("Das Modell ist nicht geladen. Die Vorhersage kann nicht durchgeführt werden.")

# Diese Funktion wird von main.py oder einer anderen Haupt-Streamlit-Datei aufgerufen
if __name__ == '__main__':
    # Dies ermöglicht das direkte Ausführen dieser Datei für Tests
    # In der App wird `run_procrastination_questionnaire()` von woanders importiert und aufgerufen.
    st.set_page_config(layout="wide")
    run_procrastination_questionnaire()

