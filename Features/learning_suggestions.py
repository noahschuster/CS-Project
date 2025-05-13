"""
Modul für die Anzeige und Generierung von Lernvorschlägen, überarbeitet mit KI-Funktionen.
"""
import streamlit as st
import random
import os
import re
import json
import requests
import fitz  # PyMuPDF
from datetime import datetime, timedelta, date as date_type, time as time_type # Renamed to avoid conflict with time module
from typing import List, Dict, Any, Optional, Union, Tuple

# Attempt to import OpenAI, make it a soft dependency for parts of the module
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    # Define a dummy client if openai is not available, so functions can check for it
    class DummyOpenAIClient:
        def __init__(self, api_key=None):
            pass # Does nothing
    OpenAI = DummyOpenAIClient # type: ignore

# Imports from other project modules (assumed to be in PYTHONPATH)
from database_manager import (
    get_calendar_events,
    save_calendar_event,
    get_learning_type_status,
    save_study_task,
    get_study_tasks,
    update_study_task_status,
    update_study_task,
    delete_study_task
)
from api_connection import get_user_courses # Fetches course_id, title, code, link_course_info

from dotenv import load_dotenv
import os

# Lade die .env-Datei
load_dotenv()

# Hole den API-Key
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# --- Constants --- 
MINUTES_PER_ECTS_PER_WEEK = 45
DEFAULT_SESSION_DURATION_MINUTES = 90
PDF_DOWNLOAD_DIR = "pdf_course_sheets/" # Ensure this directory is writable
if not os.path.exists(PDF_DOWNLOAD_DIR):
    try:
        os.makedirs(PDF_DOWNLOAD_DIR, exist_ok=True)
    except OSError as e:
        if "st" in globals() and hasattr(st, "error"):
            st.error(f"PDF-Download-Verzeichnis konnte nicht erstellt werden {PDF_DOWNLOAD_DIR}: {e}")
        else:
            print(f"ERROR: PDF-Download-Verzeichnis konnte nicht erstellt werden {PDF_DOWNLOAD_DIR}: {e}")


# --- PDF Processing Utilities ---
def download_pdf(pdf_url: str, course_code: str, download_dir: str = PDF_DOWNLOAD_DIR) -> Optional[str]:
    """Lädt eine PDF-Datei von einer URL herunter und speichert sie lokal."""
    try:
        if not os.path.exists(download_dir):
            try:
                os.makedirs(download_dir, exist_ok=True)
            except OSError as e:
                if "st" in globals() and hasattr(st, "error"):
                    st.error(f"PDF-Download-Verzeichnis konnte nicht erstellt werden {download_dir}: {e}")
                else:
                    print(f"ERROR: PDF-Download-Verzeichnis konnte nicht erstellt werden {download_dir}: {e}")
                return None

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(pdf_url, timeout=60, headers=headers)
        response.raise_for_status()
        safe_course_code = "".join(c if c.isalnum() else "_" for c in course_code)
        file_path = os.path.join(download_dir, f"{safe_course_code}_sheet_{random.randint(1000,9999)}.pdf")
        with open(file_path, "wb") as f:
            f.write(response.content)
        return file_path
    except requests.exceptions.RequestException as e:
        if "st" in globals() and hasattr(st, "error"):
            st.error(f"Error beim Herunterladen des PDFs für {course_code} von {pdf_url}: {e}")
        else:
            print(f"Error beim Herunterladen des PDFs für {course_code} von {pdf_url}: {e}")
        return None
    except Exception as e:
        if "st" in globals() and hasattr(st, "error"):
            st.error(f"Ein unerwarteter Fehler ist beim PDF-Download für {course_code}: {e}")
        else:
            print(f"ERROR: Ein unerwarteter Fehler ist beim PDF-Download für {course_code}: {e}")
        return None

def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    """Extrahiert Text aus einer PDF-Datei mit PyMuPDF (fitz)."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        if "st" in globals() and hasattr(st, "error"):
            st.error(f"Fehler beim Extrahieren von Text aus PDF {pdf_path} mit PyMuPDF: {e}")
        else:
            print(f"Fehler beim Extrahieren von Text aus PDF {pdf_path} mit PyMuPDF: {e}")
        return None

def parse_course_details_from_text(text: str, course_title: str) -> Dict[str, Any]:
    """Analysiert ECTS und Inhaltszusammenfassung aus extrahiertem PDF-Text."""
    details = {"ects": None, "content_summary": f"General information for {course_title}"}
    ects_patterns = [
        r"ECTS credits:?\s*(\d+([.,]\d+)?)" ,
        r"ECTS-Kreditpunkte:?\s*(\d+([.,]\d+)?)" ,
        r"Credits:?\s*(\d+([.,]\d+)?)\s*ECTS" ,
        r"(\d+([.,]\d+)?)\s*ECTS credits" ,
        r"(\d+([.,]\d+)?)\s*ECTS" ,
        r"Leistungspunkte(?:\s*\(ECTS\))?:\s*(\d+([.,]\d+)?)" ,
        r"Anzahl Credits ECTS:\s*(\d+([.,]\d+)?)"
    ]
    for pattern in ects_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                ects_str = match.group(1).replace(',', '.')
                details["ects"] = int(float(ects_str))
                break
            except ValueError:
                continue
    
    if details["ects"] is None: # Try a more general pattern if specific ones fail
        match_ects_general = re.search(r"(\d+([.,]\d+)?)\s*(?:Credit Points|CP|LP|ECTS)" , text, re.IGNORECASE)
        if match_ects_general:
             try:
                ects_str = match_ects_general.group(1).replace(',', '.')
                details["ects"] = int(float(ects_str))
             except ValueError:
                pass 

    content_keywords = [
        "Learning objectives", "Course content", "Course description", "Lernziele", 
        "Kursinhalte", "Beschreibung", "Modulinhalt", "Learning outcomes", "Inhalt", "Contents",
        "Kurzbeschreibung", "Detailed course description", "Ziele", "Inhalte der Lehrveranstaltung"
    ]
    extracted_sections_text = ""
    text_lower = text.lower() # For case-insensitive search
    found_keywords_indices = []

    for keyword in content_keywords:
        try:
            for match_iter in re.finditer(re.escape(keyword.lower()), text_lower):
                found_keywords_indices.append(match_iter.start())
        except Exception: 
            pass 
    
    found_keywords_indices = sorted(list(set(found_keywords_indices)))
    
    if found_keywords_indices:
        current_extracted_content = []
        for i, start_index in enumerate(found_keywords_indices):
            original_keyword_len = 0
            for kw_check in content_keywords:
                if text_lower[start_index:].startswith(kw_check.lower()):
                    original_keyword_len = len(kw_check)
                    break
            
            keyword_actual_end_index = start_index + original_keyword_len
            next_section_start_in_original_text = len(text) 
            if i + 1 < len(found_keywords_indices):
                next_section_start_in_original_text = found_keywords_indices[i+1]
            
            section_text_original = text[keyword_actual_end_index : min(keyword_actual_end_index + 2000, next_section_start_in_original_text)].strip()
            
            lines = section_text_original.split('\n')
            refined_section_lines = []
            for line_idx, line in enumerate(lines):
                if line.strip() == "" and line_idx > 5: 
                    break 
                if len(refined_section_lines) >= 15:
                    break
                if line.strip(): 
                    refined_section_lines.append(line.strip())
            
            if refined_section_lines:
                current_extracted_content.append("\n".join(refined_section_lines))
        
        if current_extracted_content:
             details["content_summary"] = "\n\n---\n".join(current_extracted_content)

    if not details["content_summary"].strip() or details["content_summary"] == f"General information for {course_title}":
        title_match = re.search(re.escape(course_title), text, re.IGNORECASE)
        if title_match:
            start_content_index = title_match.end()
            next_major_break = re.search(r"\n\s*\n", text[start_content_index:])
            end_content_index = start_content_index + (next_major_break.start() if next_major_break else 1500)
            details["content_summary"] = text[start_content_index : min(len(text), end_content_index)].strip()
        else:
            details["content_summary"] = text[:1500].strip()

    if len(details["content_summary"]) > 4000:
        details["content_summary"] = details["content_summary"][:4000] + "... (truncated)"
    
    if not details["content_summary"].strip():
        details["content_summary"] = f"General study for {course_title}. No specific content could be extracted."

    if details["ects"] is None:
        if "st" in globals() and hasattr(st, "warning"):
            st.warning(f"Konnte nicht automatisch ECTS ermitteln für '{course_title}'. Annahme von 3 ECTS als Standard.")
        else:
            print(f"WARNING: Konnte nicht automatisch die ECTS für '{course_title}'. Annahme von 3 ECTS als Standard.")
        details["ects"] = 3
    return details

# --- Scheduling Utilities (Integrated from scheduling_utils.py) ---
def get_busy_slots(calendar_events: List[Dict[str, Any]]) -> Dict[str, List[Tuple[time_type, time_type]]]:
    busy_slots: Dict[str, List[Tuple[time_type, time_type]]] = {}
    for event in calendar_events:
        try:
            event_date_str = event["date"]
            start_time_str = event["start_time"]
            end_time_str = event["end_time"]
            start_time_obj = datetime.strptime(start_time_str, "%H:%M").time()
            end_time_obj = datetime.strptime(end_time_str, "%H:%M").time()
            if end_time_obj == time_type(0, 0):
                end_time_obj = time_type(23, 59, 59)
            if event_date_str not in busy_slots:
                busy_slots[event_date_str] = []
            busy_slots[event_date_str].append((start_time_obj, end_time_obj))
        except KeyError as e:
            print(f"Ereignis fehlt erwarteter Schlüssel {e} in Veranstaltung: {event}")
            continue
        except ValueError as e:
            print(f"Fehler beim Parsen von Datum/Uhrzeit im Ereignis: {event} - {e}")
            continue
    for date_str in busy_slots:
        busy_slots[date_str].sort()
    return busy_slots

def is_slot_free(start_dt: datetime, duration_minutes: int, daily_busy_slots: List[Tuple[time_type, time_type]]) -> bool:
    new_session_start_time = start_dt.time()
    new_session_end_dt = start_dt + timedelta(minutes=duration_minutes)
    new_session_end_time = new_session_end_dt.time()
    if new_session_end_dt.date() != start_dt.date() and new_session_end_time != time_type(0,0):
         return False
    for busy_start, busy_end in daily_busy_slots:
        if new_session_start_time < busy_end and new_session_end_time > busy_start:
            return False
    return True

def find_available_slot_for_session(
    target_date: date_type, 
    session_duration_minutes: int, 
    daily_busy_slots: List[Tuple[time_type, time_type]], 
    preferred_start_hour: int = 8, 
    preferred_end_hour: int = 20,
    time_increment_minutes: int = 15
) -> Optional[time_type]:
    current_check_time = time_type(preferred_start_hour, 0)
    day_end_time = time_type(preferred_end_hour, 0)
    while True:
        potential_start_dt = datetime.combine(target_date, current_check_time)
        potential_end_dt = potential_start_dt + timedelta(minutes=session_duration_minutes)
        if potential_end_dt.time() > day_end_time:
            if potential_end_dt.date() > target_date or (potential_end_dt.date() == target_date and potential_end_dt.time() > day_end_time):
                 break
        if is_slot_free(potential_start_dt, session_duration_minutes, daily_busy_slots):
            return current_check_time
        next_check_dt = potential_start_dt + timedelta(minutes=time_increment_minutes)
        if next_check_dt.date() > target_date:
            break
        current_check_time = next_check_dt.time()
        if current_check_time >= day_end_time and current_check_time > time_type(preferred_start_hour,0):
             break
        if current_check_time < time_type(preferred_start_hour,0) and time_increment_minutes > 0 :
            break
    return None

# --- OpenAI API Interaction Logic (Integrated) ---
def generate_weekly_plan_with_openai(
    course_title: str, course_content_summary: str, learning_type: Optional[str],
    weekly_study_minutes: int, num_sessions: int, session_duration: int,
    week_number: int, total_weeks: int) -> Optional[List[Dict[str, Any]]]:
        
    if not client or not OPENAI_AVAILABLE:
        st.error("OpenAI Client ist nicht initialisiert oder die Bibliothek ist nicht verfügbar. KI-Plangenerierung nicht möglich.")
        return None
        
    prompt = f"""Du bist ein erfahrener Lerncoach und Didaktik-Experte, der Studierenden hilft, optimale Lernpläne zu erstellen.

WICHTIG: Deine Antwort MUSS ein valides JSON-Array sein, das exakt diese Struktur für jede Lerneinheit hat und ALLE Antworten MÜSSEN auf DEUTSCH sein:
{{
  "session_number": (eine Ganzzahl, beginnend bei 1),
  "topic_focus": (ein präziser, spezifischer String mit dem Hauptthema, maximal 100 Zeichen),
  "suggested_activities": (ein Array mit 3-4 KURZEN aber SPEZIFISCHEN Lernaktivitäten, jede maximal 100 Zeichen),
  "estimated_duration_minutes": (eine Ganzzahl, sollte {session_duration} sein)
}}

Kurs: {course_title}
Zusammenfassung der Kursinhalte/Lernziele:
{course_content_summary}

Lerntyp des Studierenden: {learning_type if learning_type else 'Nicht spezifiziert'}
Wöchentlicher Lernaufwand für diesen Kurs: {weekly_study_minutes} Minuten.
Dieser Plan ist für Woche {week_number} von {total_weeks}.
Der Lernaufwand soll auf {num_sessions} Lerneinheiten von jeweils ca. {session_duration} Minuten aufgeteilt werden.

ANLEITUNG FÜR HOCHWERTIGE LERNAKTIVITÄTEN:

1. KÜRZE: Jede Aktivität MUSS kurz und prägnant sein (maximal 100 Zeichen). Verwende klare, direkte Sprache.

2. SPEZIFITÄT: Trotz Kürze muss jede Aktivität präzise und konkret sein. Vermeide allgemeine Formulierungen.

3. METHODENVIELFALT: Integriere verschiedene Lernmethoden, die zum Thema und Lerntyp passen.

4. HANDLUNGSORIENTIERUNG: Formuliere jede Aktivität als konkrete Handlungsanweisung mit Verb.

5. ANWENDUNGSBEZUG: Verbinde theoretische Konzepte mit praktischen Anwendungen.

Hier ist ein Beispiel für ein korrektes Objekt im Array mit KURZEN, PRÄGNANTEN Aktivitäten:
{{
  "session_number": 1,
  "topic_focus": "Einführung in die Makroökonomie",
  "suggested_activities": [
    "Mindmap zu BIP-Komponenten erstellen (20 Min.)",
    "5 Übungsaufgaben zur BIP-Berechnung lösen (30 Min.)",
    "Karteikarten mit 10 Fachbegriffen anlegen (20 Min.)",
    "TED-Talk zu Wirtschaftswachstum ansehen (20 Min.)"
  ],
  "estimated_duration_minutes": {session_duration}
}}

WICHTIG: Halte jede Aktivität KURZ (maximal 100 Zeichen), aber dennoch spezifisch und handlungsorientiert. Deine Antwort darf NUR das JSON-Array enthalten und keine Erklärungen oder zusätzlichen Text.
"""
        
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Du bist ein erfahrener Lerncoach. Erstelle kurze, prägnante und spezifische Lernaktivitäten auf Deutsch. Jede Aktivität darf maximal 100 Zeichen haben."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        response_content = response.choices[0].message.content
        
        if response_content:
            try:
                parsed_json = json.loads(response_content)
                plan_data = None
                
                if isinstance(parsed_json, list):
                    # Fallback für String-Items in der Liste
                    for i, item in enumerate(parsed_json):
                        if isinstance(item, str):
                            parsed_json[i] = {
                                "session_number": i + 1,
                                "topic_focus": item[:100] if len(item) > 100 else item,
                                "suggested_activities": [
                                    f"Mindmap zu '{item[:30]}' erstellen (25 Min.)",
                                    f"Wichtige Konzepte recherchieren (20 Min.)",
                                    f"5 Übungsfragen formulieren (25 Min.)",
                                    f"Zusammenfassung schreiben (20 Min.)"
                                ],
                                "estimated_duration_minutes": session_duration
                            }
                    plan_data = parsed_json
                elif isinstance(parsed_json, dict):
                    for key in parsed_json:
                        if isinstance(parsed_json[key], list):
                            # Fallback für String-Items in verschachtelten Listen
                            for i, item in enumerate(parsed_json[key]):
                                if isinstance(item, str):
                                    parsed_json[key][i] = {
                                        "session_number": i + 1,
                                        "topic_focus": item[:100] if len(item) > 100 else item,
                                        "suggested_activities": [
                                            f"Mindmap zu '{item[:30]}' erstellen (25 Min.)",
                                            f"Wichtige Konzepte recherchieren (20 Min.)",
                                            f"5 Übungsfragen formulieren (25 Min.)",
                                            f"Zusammenfassung schreiben (20 Min.)"
                                        ],
                                        "estimated_duration_minutes": session_duration
                                    }
                            plan_data = parsed_json[key]
                            break
                    if plan_data is None:
                        st.error(f"OpenAI API hat JSON zurückgegeben, aber keine Liste von Lerneinheiten gefunden: {response_content}")
                        return None
                else:
                    st.error(f"OpenAI API hat eine unerwartete JSON-Struktur zurückgegeben: {response_content}")
                    return None
                
                validated_plan = []
                for session in plan_data:
                    if not all(k in session for k in ["session_number", "topic_focus", "suggested_activities", "estimated_duration_minutes"]):
                        st.warning(f"Lerneinheit wird übersprungen wegen fehlender Felder: {session}")
                        continue
                    
                    # Stelle sicher, dass topic_focus nicht zu lang ist
                    if len(session["topic_focus"]) > 100:
                        session["topic_focus"] = session["topic_focus"][:97] + "..."
                    
                    # Stelle sicher, dass suggested_activities eine Liste ist und nicht zu lang
                    if not isinstance(session["suggested_activities"], list):
                        if isinstance(session["suggested_activities"], str):
                            session["suggested_activities"] = [
                                f"Mindmap erstellen (25 Min.)",
                                f"Konzepte recherchieren (20 Min.)",
                                f"Übungsfragen lösen (25 Min.)",
                                f"Zusammenfassung schreiben (20 Min.)"
                            ]
                        else:
                            st.warning(f"Lerneinheit wird übersprungen wegen ungültiger 'suggested_activities': {session}")
                            continue
                    else:
                        # Kürze zu lange Aktivitäten
                        for i, activity in enumerate(session["suggested_activities"]):
                            if len(activity) > 100:
                                session["suggested_activities"][i] = activity[:97] + "..."
                    
                    validated_plan.append(session)
                return validated_plan
            except json.JSONDecodeError as e:
                st.error(f"Fehler beim Dekodieren des JSON von der OpenAI API: {e}\nAntwort war: {response_content}")
                return None
        else:
            st.error("OpenAI API hat eine leere Antwort zurückgegeben.")
            return None
    except Exception as e:
        st.error(f"Fehler beim Aufruf der OpenAI API: {e}")
        return None

# --- Main Logic for Generating and Displaying Study Plan (Integrated) ---
def _generate_complete_study_plan(
    user_id: str,
    selected_courses_info: List[Dict[str, Any]],
    start_date_dt: date_type,
    weeks: int,
    learning_type: Optional[str],
    existing_calendar_events: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    full_study_plan = []
    all_busy_slots = get_busy_slots(existing_calendar_events)
    progress_bar = st.progress(0.0)
    total_steps = len(selected_courses_info) * weeks if weeks > 0 else 1 # Avoid division by zero if weeks is 0
    current_step = 0

    for course_info in selected_courses_info:
        st.write(f"Verarbeite Kurs: {course_info['title']} ({course_info['code']})...")
        if not course_info.get("link_course_info"):
            st.warning(f"Übersprüinge {course_info['title']} weil Kursmerkblatt-Link fehlt.")
            current_step += weeks
            progress_bar.progress(min(1.0, current_step / total_steps if total_steps > 0 else 0.0))
            continue
            
        pdf_path = download_pdf(course_info["link_course_info"], course_info["code"])
        if not pdf_path:
            st.warning(f"Überspringe {course_info['title']} weil das PDF nicht heruntergeladen werden konnte.")
            current_step += weeks
            progress_bar.progress(min(1.0, current_step / total_steps if total_steps > 0 else 0.0))
            continue

        pdf_text = extract_text_from_pdf(pdf_path)
        if os.path.exists(pdf_path): os.remove(pdf_path)

        if not pdf_text:
            st.warning(f"Überspringe {course_info['title']} weil der Text nicht aus dem PDF extrahiert werden konnte.")
            current_step += weeks
            progress_bar.progress(min(1.0, current_step / total_steps if total_steps > 0 else 0.0))
            continue
        
        parsed_details = parse_course_details_from_text(pdf_text, course_info["title"])
        ects = parsed_details["ects"]
        content_summary = parsed_details["content_summary"]
        
        weekly_study_minutes_for_course = ects * MINUTES_PER_ECTS_PER_WEEK
        if weekly_study_minutes_for_course <= 0:
            st.info(f"Kurs {course_info['title']} hat 0 ECTS oder 0 Lernminuten. Überspringe Planung.")
            current_step += weeks
            progress_bar.progress(min(1.0, current_step / total_steps if total_steps > 0 else 0.0))
            continue
            
        num_sessions_per_week = max(1, round(weekly_study_minutes_for_course / DEFAULT_SESSION_DURATION_MINUTES))
        actual_session_duration = round(weekly_study_minutes_for_course / num_sessions_per_week)

        st.write(f"  ECTS: {ects}, Wöchentliche Minuten: {weekly_study_minutes_for_course}, Sessions/Woche: {num_sessions_per_week} x {actual_session_duration}min")

        for week_idx in range(weeks):
            current_step += 1
            progress_bar.progress(min(1.0, current_step / total_steps if total_steps > 0 else 0.0))
            st.write(f"  Plane Woche {week_idx + 1} für {course_info['title']}...")
            
            weekly_ai_plan = generate_weekly_plan_with_openai(
                course_title=course_info["title"],
                course_content_summary=content_summary,
                learning_type=learning_type,
                weekly_study_minutes=weekly_study_minutes_for_course,
                num_sessions=num_sessions_per_week,
                session_duration=actual_session_duration,
                week_number=week_idx + 1,
                total_weeks=weeks
            )

            if not weekly_ai_plan:
                st.warning(f"Konnte keinen KI Lernplan generieren für {course_info['title']} für Woche {week_idx + 1}.")
                for _ in range(num_sessions_per_week):
                    full_study_plan.append({
                        "course_id": course_info["id"], "course_title": course_info["title"], "course_code": course_info["code"],
                        "date": "UNSCHEDULED", "start_time": "N/A", "end_time": "N/A",
                        "content": {"topic_focus": "Manual planning needed - AI generation failed", "suggested_activities": ["Review course materials."], "estimated_duration_minutes": actual_session_duration},
                        "completed": False, "status": "ai_failed"
                    })
                continue

            current_week_start_date = start_date_dt + timedelta(days=week_idx * 7)
            day_of_week_preference = list(range(7))
            random.shuffle(day_of_week_preference)

            sessions_scheduled_this_week = 0
            for session_content in weekly_ai_plan:
                if sessions_scheduled_this_week >= num_sessions_per_week: break
                scheduled_this_session = False
                for day_offset in day_of_week_preference:
                    target_schedule_date = current_week_start_date + timedelta(days=day_offset)
                    busy_slots_for_day = all_busy_slots.get(target_schedule_date.strftime("%Y-%m-%d"), [])
                    
                    available_start_time_obj = find_available_slot_for_session(
                        target_date=target_schedule_date,
                        session_duration_minutes=session_content.get("estimated_duration_minutes", actual_session_duration),
                        daily_busy_slots=busy_slots_for_day,
                        preferred_start_hour=8, preferred_end_hour=22
                    )

                    if available_start_time_obj:
                        start_dt_obj = datetime.combine(target_schedule_date, available_start_time_obj)
                        end_dt_obj = start_dt_obj + timedelta(minutes=session_content.get("estimated_duration_minutes", actual_session_duration))
                        full_study_plan.append({
                            "course_id": course_info["id"], "course_title": course_info["title"], "course_code": course_info["code"],
                            "date": start_dt_obj.strftime("%Y-%m-%d"), "start_time": start_dt_obj.strftime("%H:%M"), "end_time": end_dt_obj.strftime("%H:%M"),
                            "content": session_content, "completed": False, "status": "scheduled"
                        })
                        date_str = start_dt_obj.strftime("%Y-%m-%d")
                        if date_str not in all_busy_slots: all_busy_slots[date_str] = []
                        all_busy_slots[date_str].append((start_dt_obj.time(), end_dt_obj.time()))
                        all_busy_slots[date_str].sort()
                        scheduled_this_session = True
                        sessions_scheduled_this_week += 1
                        break
                if not scheduled_this_session:
                    full_study_plan.append({
                        "course_id": course_info["id"], "course_title": course_info["title"], "course_code": course_info["code"],
                        "date": "UNSCHEDULED", "start_time": "N/A", "end_time": "N/A",
                        "content": session_content, "completed": False, "status": "unscheduled_conflict"
                    })
                    st.warning(f"Konnte keinen freien Platz für eine Sitzung von {course_info['title']} in Woche {week_idx + 1}.")
    
    progress_bar.progress(1.0)
    st.success("Prozess der Studienplanerstellung abgeschlossen.")
    full_study_plan.sort(key=lambda x: (x.get("date", "zzzz"), x.get("start_time", "zz:zz")))
    return full_study_plan

# --- Streamlit UI Functions (New Version) ---
def _display_generated_study_plan(study_plan: List[Dict[str, Any]]) -> None:
    if not study_plan:
        st.info("Kein Lernplan zum Anzeigen vorhanden.")
        return
    for session in study_plan:
        status_emoji = "✅" if session.get("completed") else ("🗓️" if session.get("status") == "scheduled" else ("⚠️" if session.get("status") == "unscheduled_conflict" else ("🤖" if session.get("status") == "ai_failed" else "📝")))
        header_text = f"{status_emoji} {session['date']} | {session['start_time']} - {session['end_time']} | {session['course_code']}"
        if session.get("status") == "unscheduled_conflict": header_text += " (KONFLIKT/UNGEPLANT)"
        elif session.get("status") == "ai_failed": header_text += " (KI-FEHLER)"
        with st.expander(header_text):
            st.markdown(f"**Kurs:** {session['course_title']}")
            content = session.get("content", {})
            st.markdown(f"**Thema/Fokus:** {content.get('topic_focus', 'N/A')}")
            st.markdown("**Vorgeschlagene Aktivitäten:**")
            activities = content.get("suggested_activities", [])
            if activities and isinstance(activities, list):
                for activity in activities:
                    st.markdown(f"- {activity}")
            else:
                st.markdown("- Keine spezifischen Aktivitäten generiert.")
            st.markdown(f"**Geschätzte Dauer:** {content.get('estimated_duration_minutes', 'N/A')} Minuten")
            if session.get("status") != "scheduled": st.caption(f"Status: {session['status']}")

def _handle_new_study_plan_saving(user_id: str) -> None:
    if 'new_study_plan' in st.session_state and st.session_state.new_study_plan:
        plan_to_save = [s for s in st.session_state.new_study_plan if s.get("status") == "scheduled"]
        if not plan_to_save:
            st.warning("Keine planbaren Lerneinheiten zum Speichern vorhanden.")
            return
        num_saved, num_failed = 0, 0
        for session in plan_to_save:
            try:
                # Wichtig: Verwende 'type' statt 'event_type', da die save_calendar_event Funktion
                # event_data.get('type') verwendet, um den Wert für event_type in der Datenbank zu setzen
                event_data = {
                    'title': f"Lernen (KI): {session['course_code']} - {session['content'].get('topic_focus', 'Allgemein')[:30]}",
                    'date': session['date'], 
                    'time': session['start_time'],
                    'end_time': session['end_time'],
                    'type': "Study Session (AI)",  # WICHTIG: Verwende 'type' statt 'event_type'
                    'color': "#A0E7E5", 
                    'user_id': user_id,
                    'priority': 2  # Medium priority
                }
                save_calendar_event(user_id, event_data)
                
                task_data = {
                    'course_id': session['course_id'], 
                    'course_title': session['course_title'], 
                    'course_code': session['course_code'],
                    'date': session['date'], 
                    'start_time': session['start_time'], 
                    'end_time': session['end_time'],
                    'topic': session['content'].get('topic_focus', 'N/A'),
                    'methods': json.dumps(session['content'].get('suggested_activities', [])),
                    'status': 'Pending', 
                    'is_ai_generated': True
                }
                save_study_task(user_id, task_data)
                num_saved += 1
            except Exception as e:
                st.error(f"Fehler beim Speichern der Session für {session['course_code']} am {session['date']}: {e}")
                num_failed += 1
        
        if num_saved > 0: 
            st.success(f"{num_saved} Lerneinheiten gespeichert!")
        if num_failed > 0: 
            st.error(f"{num_failed} Lerneinheiten konnten nicht gespeichert werden.")
        
        # Nur wenn mindestens eine Einheit gespeichert wurde, Plan löschen und Seite neu laden
        if num_saved > 0:
            del st.session_state.new_study_plan
            st.rerun()
    else:
        st.error("Kein Lernplan zum Speichern vorhanden.")


def _display_ai_learning_plan_generator(user_id: str, learning_type: Optional[str]) -> None:
    st.subheader("Dein intelligenter Lernplan")
    if learning_type: 
        st.write(f"Dein Lerntyp: **{learning_type}** (wird berücksichtigt)")
    else: 
        st.write("Lerntyp nicht festgelegt. Plan wird allgemeiner generiert.")
    
    # Prüfe zuerst, ob bereits ein Plan in der Session existiert
    if "new_study_plan" in st.session_state and st.session_state.new_study_plan:
        st.success("Ein generierter Lernplan ist verfügbar!")
        st.subheader("Generierter Lernplan")
        _display_generated_study_plan(st.session_state.new_study_plan)
        
        # Speichern-Button - WICHTIG: Dieser Teil muss auf jeden Fall ausgeführt werden
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("✅ LERNPLAN JETZT SPEICHERN", key="save_new_plan_button", type="primary", use_container_width=True):
                _handle_new_study_plan_saving(user_id)
        
        # Optionaler Button zum Löschen des Plans aus der Session
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🗑️ Lernplan verwerfen und neuen erstellen", key="discard_plan_button"):
                del st.session_state.new_study_plan
                st.rerun()
        
        # Wichtig: Return hier, um den Rest der Funktion zu überspringen
        return
    
    # Nur wenn kein Plan in der Session ist, zeige das Formular zur Plangenerierung an
    user_courses = get_user_courses(user_id)
    if not user_courses:
        st.info("Keine Kurse ausgewählt. Bitte zuerst Kurse in den Einstellungen auswählen.")
        return
    
    with st.form("generate_new_study_plan_form"):
        st.write("Wähle Kurse für den Lernplan:")
        selected_courses_data = []
        for course in user_courses:
            if st.checkbox(f"{course['meeting_code']} - {course['title']}", value=True, key=f"course_select_{course['course_id']}"):
                if not course.get("link_course_info"):
                    st.warning(f"Kursmerkblatt-Link für {course['title']} fehlt. Kann nicht automatisch beplant werden.")
                    continue
                selected_courses_data.append({
                    "id": course["course_id"], 
                    "title": course["title"], 
                    "code": course["meeting_code"], 
                    "link_course_info": course["link_course_info"]
                })
        
        today = datetime.now().date()
        default_start = today + timedelta(days=(7 - today.weekday())) if today.weekday() >= 5 else today
        start_date_input = st.date_input("Startdatum", default_start)
        weeks_input = st.slider("Anzahl Wochen", 1, 12, 4)
        submit_button = st.form_submit_button("Lernplan mit KI generieren")
    
    if submit_button:
        if not selected_courses_data:
            st.warning("Bitte wähle mindestens einen Kurs mit gültigem Merkblatt-Link aus.")
            return
            
        if not client or not OPENAI_AVAILABLE:
            st.error("OpenAI Client nicht initialisiert/verfügbar. Plangenerierung nicht möglich.")
            return
        
        # Temporärer Container für die Info-Meldung
        info_container = st.empty()
        info_container.info("Lernplan wird generiert... Dies kann einige Minuten dauern.")
        
        calendar_events = get_calendar_events(user_id)
        valid_calendar_events = []
        
        if isinstance(calendar_events, list):
            for evt in calendar_events:
                if isinstance(evt, dict) and all(k in evt for k in ["date", "start_time", "end_time"]):
                    valid_calendar_events.append(evt)
                elif isinstance(evt, dict) and "date" in evt and "time" in evt and "end_time" not in evt:
                    try:
                        start_t = datetime.strptime(evt["time"], "%H:%M").time()
                        end_t = (datetime.combine(date_type.min, start_t) + timedelta(hours=1)).time()
                        evt["start_time"] = evt["time"]
                        evt["end_time"] = end_t.strftime("%H:%M")
                        valid_calendar_events.append(evt)
                    except Exception:
                        st.warning(f"Kalenderereignis ignoriert/konnte nicht angepasst werden: {evt}")
        else:
            st.error("Fehler beim Abrufen der Kalenderereignisse.")
        
        generated_plan = _generate_complete_study_plan(
            user_id=user_id, 
            selected_courses_info=selected_courses_data,
            start_date_dt=start_date_input, 
            weeks=weeks_input, 
            learning_type=learning_type,
            existing_calendar_events=valid_calendar_events
        )
        
        # Info-Meldung entfernen
        info_container.empty()
        
        if generated_plan:
            st.session_state.new_study_plan = generated_plan
            st.success(f"KI-Lernplan für {len(selected_courses_data)} Kurse über {weeks_input} Wochen erstellt!")
            st.rerun()  # Wichtig: Seite neu laden, um den neuen UI-Fluss zu starten
        else:
            st.error("Lernplan konnte nicht generiert werden.")


# --- Main Entry Point --- (Replaces original display_learning_suggestions)
def display_learning_suggestions(user_id: str) -> None:
    st.title("KI-gestützte Lernplanerstellung")
    learning_type, completed = get_learning_type_status(user_id)
    if not completed:
        st.warning("Dein Lerntyp ist noch nicht festgelegt. Für optimale Vorschläge, beantworte bitte zuerst die Fragen zum Lerntyp. Du kannst den Plan aber auch ohne Lerntyp erstellen.")

    tab1, tab2 = st.tabs(["Neuen Lernplan generieren", "Meine Lernaufgaben"])
    with tab1:
        _display_ai_learning_plan_generator(user_id, learning_type if completed else None)
    with tab2:
        display_study_tasks(user_id) # Assuming this is the updated/kept version

# --- Study Tasks Display (Adapted from new_suggestions, kept for completeness) ---

# Note: The original learning_suggestions.py had functions like:
# _display_learning_plan_generator, _handle_study_plan_generation, 
# _handle_study_plan_saving, generate_study_plan, _get_busy_time_slots (old version),
# get_course_content, generate_study_content, display_study_plan, save_study_plan_to_calendar
# These have been effectively replaced by the new AI-driven workflow and helper functions above.
# They are not included in this merged version to avoid redundancy and use the new system.
def display_study_tasks(user_id: str) -> None:
    st.subheader("Meine Lernaufgaben")
    
    user_tasks = get_study_tasks(user_id)
    if not user_tasks:
        st.info("Du hast noch keine Lernaufgaben.")
        return
    
    # Aktuelles Datum für die Kategorisierung
    today = datetime.now().date()
    today_str = today.strftime("%Y-%m-%d")
    
    # Aufgaben nach Datum kategorisieren
    overdue_tasks = []
    today_tasks = []
    future_tasks = []
    
    for task in user_tasks:
        task_date_str = task.get('date', '')
        try:
            task_date = datetime.strptime(task_date_str, "%Y-%m-%d").date()
            if task_date < today:
                overdue_tasks.append(task)
            elif task_date == today:
                today_tasks.append(task)
            else:
                future_tasks.append(task)
        except (ValueError, TypeError):
            # Bei ungültigem Datum, Aufgabe zu "Heute" hinzufügen
            today_tasks.append(task)
    
    # Sortieren nach Datum und Zeit
    overdue_tasks.sort(key=lambda x: (x.get('date', 'zzzz'), x.get('start_time', 'zz:zz')))
    today_tasks.sort(key=lambda x: x.get('start_time', 'zz:zz'))
    future_tasks.sort(key=lambda x: (x.get('date', 'zzzz'), x.get('start_time', 'zz:zz')))
    
    # Tab-System für die verschiedenen Kategorien
    tab1, tab2, tab3 = st.tabs(["Heute", "Überfällig", "Zukünftig"])
    
    # Funktion zum Anzeigen einer Aufgabenliste mit einheitlichem Format
    def display_task_list(tasks, category):
        if not tasks:
            st.info(f"Keine {category} Lernaufgaben vorhanden.")
            return
        
        for task in tasks:
            task_id = task.get('id', random.randint(10000, 99999))
            is_ai = task.get('is_ai_generated', False)
            ai_marker = "🤖" if is_ai else ""
            
            # Status bestimmen für die Checkbox
            current_status = task.get('status', 'Pending')
            is_completed = task.get('completed', False)  # Verwende den tatsächlichen completed-Wert
            
            # Aufgabencontainer mit Checkbox
            col1, col2 = st.columns([0.05, 0.95])
            with col1:
                # Checkbox zum Abhaken
                if st.checkbox("", value=is_completed, key=f"checkbox_{task_id}", 
                               help="Aufgabe als erledigt markieren"):
                    if not is_completed:
                        # Übergebe booleschen Wert True statt String
                        if update_study_task_status(task_id, True):
                            st.success(f"Aufgabe '{task.get('topic')}' als erledigt markiert!")
                            st.rerun()
                else:
                    if is_completed:
                        # Übergebe booleschen Wert False statt String
                        if update_study_task_status(task_id, False):
                            st.info(f"Aufgabe '{task.get('topic')}' wieder als ausstehend markiert.")
                            st.rerun()
            
            # Aufgabendetails
            with col2:
                task_header = f"{ai_marker} {task.get('date', 'Kein Datum')} | {task.get('start_time', '')} - {task.get('end_time', '')} | {task.get('course_code', 'N/A')}"
                
                # Stil für erledigte Aufgaben
                if is_completed:
                    task_header = f"~~{task_header}~~"
                
                with st.expander(task_header):
                    st.markdown(f"**Kurs:** {task.get('course_title', 'N/A')} ({task.get('course_code', 'N/A')})")
                    
                    # Thema mit Durchstreichung, wenn erledigt
                    topic_text = task.get('topic', 'N/A')
                    if is_completed:
                        st.markdown(f"**Thema:** ~~{topic_text}~~")
                    else:
                        st.markdown(f"**Thema:** {topic_text}")
                    
                    st.markdown(f"**Dauer:** {task.get('start_time', 'N/A')} - {task.get('end_time', 'N/A')}")
                    
                    # Aktivitäten anzeigen
                    st.markdown("**Aktivitäten:**")
                    methods = task.get('methods', [])
                    if isinstance(methods, str):
                        try: 
                            methods = json.loads(methods)
                        except: 
                            methods = [methods]
                    
                    if isinstance(methods, list) and methods:
                        for method in methods:
                            # Durchstreichen, wenn erledigt
                            if is_completed:
                                st.markdown(f"- ~~{method}~~")
                            else:
                                st.markdown(f"- {method}")
                    else:
                        st.write("Keine spezifischen Aktivitäten.")
                    
                    # Status-Dropdown und Löschen-Button
                    col_status, col_delete = st.columns(2)
                    
                    with col_status:
                        status_options = ["Pending", "In Progress", "Completed", "Cancelled"]
                        status_labels = {
                            "Pending": "Ausstehend",
                            "In Progress": "In Bearbeitung",
                            "Completed": "Abgeschlossen",
                            "Cancelled": "Abgebrochen"
                        }
                        status_values = {
                            "Pending": False,
                            "In Progress": False,
                            "Completed": True,
                            "Cancelled": False
                        }
                        
                        try:
                            current_status_index = status_options.index(current_status)
                        except ValueError:
                            current_status_index = 0
                        
                        new_status = st.selectbox(
                            "Status", 
                            options=status_options,
                            format_func=lambda x: status_labels.get(x, x),
                            index=current_status_index, 
                            key=f"status_{task_id}"
                        )
                        
                        if new_status != current_status:
                            # Konvertiere Status-String in booleschen Wert für completed
                            new_completed = status_values.get(new_status, False)
                            if update_study_task_status(task_id, new_completed):
                                st.success(f"Status für Aufgabe '{task.get('topic')}' aktualisiert!")
                                st.rerun()
                            else:
                                st.error("Fehler beim Aktualisieren des Status.")
                    
                    with col_delete:
                        if st.button("Löschen", key=f"delete_{task_id}"):
                            if delete_study_task(task_id):
                                st.success(f"Aufgabe '{task.get('topic')}' gelöscht!")
                                st.rerun()
                            else:
                                st.error("Fehler beim Löschen der Aufgabe.")
    
    # Anzeigen der Aufgaben in den entsprechenden Tabs
    with tab1:
        st.header("Heutige Aufgaben")
        st.markdown(f"**Datum: {today.strftime('%d.%m.%Y')}**")
        display_task_list(today_tasks, "heutige")
    
    with tab2:
        st.header("Überfällige Aufgaben")
        st.markdown("**Aufgaben, die vor dem heutigen Tag geplant waren**")
        display_task_list(overdue_tasks, "überfällige")
    
    with tab3:
        st.header("Zukünftige Aufgaben")
        st.markdown("**Aufgaben für die kommenden Tage**")
        display_task_list(future_tasks, "zukünftige")
    
    # Zusammenfassung anzeigen
    st.markdown("---")
    st.markdown(f"""
    **Zusammenfassung:**
    - Heutige Aufgaben: {len(today_tasks)}
    - Überfällige Aufgaben: {len(overdue_tasks)}
    - Zukünftige Aufgaben: {len(future_tasks)}
    - Gesamt: {len(user_tasks)}
    """)

# If this file is run directly for testing (streamlit run learning_suggestions.py):
if __name__ == "__main__":
    # Mock user_id for testing. In a real app, this comes from session state after login.
    mock_user_id = st.session_state.get("user_id", "test_user_standalone")
    if "user_id" not in st.session_state:
        st.session_state.user_id = mock_user_id

    # Minimal setup for standalone run if needed, or rely on main.py to set up session_state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = True # Assume logged in for standalone test
    
    # Check if learning type is already set, if not, provide a mock
    if 'learning_type_status_completed' not in st.session_state:
        st.session_state.learning_type_status_completed = True
        st.session_state.learning_type_status_type = "Visual"

    # Override database/API calls with mocks for standalone testing if desired
    # This part is complex to maintain here. For robust testing, use a proper test framework.
    # For simplicity, we'll assume the actual DB functions are available or will fail gracefully.
    
    # Example: Mock get_learning_type_status if it's not fully set up
    _original_get_learning_type_status = get_learning_type_status
    def _mock_get_learning_type_status(uid):
        completed = st.session_state.get('learning_type_status_completed', False)
        ltype = st.session_state.get('learning_type_status_type', None)
        if not completed:
            # Simulate going through learning type questionnaire
            # from learning_type import display_learning_type # This would be complex here
            # For now, just return a default if not completed
            return "Visual", True # Mock as completed for testing flow
        return ltype, completed
    # get_learning_type_status = _mock_get_learning_type_status

    display_learning_suggestions(mock_user_id)

    # get_learning_type_status = _original_get_learning_type_status # Restore if needed
