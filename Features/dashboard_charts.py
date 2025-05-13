import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd

# --- Mock data functions for testing purposes ---
def get_study_tasks(user_id):
    return [
        {"course_title": "Mathematics", "start_time": "09:00", "end_time": "11:00"}, # 2h
        {"course_title": "Physics", "start_time": "13:00", "end_time": "14:30"},     # 1.5h
        {"course_title": "History", "start_time": "15:00", "end_time": "16:00"},     # 1h
        {"course_title": "Mathematics", "start_time": "10:00", "end_time": "12:00"}, # 2h (total Math: 4h)
        {"course_title": "Chemistry", "start_time": "08:00", "end_time": "09:30"},   # 1.5h
        # Total 8.0 hours: Math 50%, Physics 18.75%, History 12.5%, Chemistry 18.75%
    ]

def get_calendar_events(user_id):
    today = datetime.now()
    return [
        {"date": (today + timedelta(days=1)).strftime("%Y-%m-%d")}, # Event 1
        {"date": (today + timedelta(days=2)).strftime("%Y-%m-%d")}, # Event 2
        {"date": (today + timedelta(days=3)).strftime("%Y-%m-%d")}, # Event 3 (used_hours = 3)
        {"date": (today + timedelta(days=8)).strftime("%Y-%m-%d")}  # This one is outside next 7 days
    ]
# --- End of Mock data functions ---

# Apple-inspired Aesthetics
APPLE_FONT_FAMILY = "-apple-system, BlinkMacSystemFont, San Francisco, Inter, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
APPLE_TEXT_COLOR = "#1d1d1f" # Near black for primary text
APPLE_SECONDARY_TEXT_COLOR = "#6e6e73" # Grey for secondary text
APPLE_BACKGROUND_COLOR = "rgba(0,0,0,0)" # Transparent for Streamlit integration

# Refined Palettes (inspired by Apple's softer, clearer tones)
SUBJECT_PALETTE_APPLE = ["#007AFF", "#34C759", "#FF9500", "#AF52DE", "#5AC8FA", "#FF3B30", "#FFCC00"] # Blue, Green, Orange, Purple, Teal, Red, Yellow
USAGE_PALETTE_APPLE = ["#FF9500", "#007AFF"] # Orange for used, Blue for free

TITLE_FONT_SIZE_APPLE = 20
LEGEND_FONT_SIZE_APPLE = 13
ANNOTATION_FONT_SIZE_APPLE = 18
SLICE_TEXT_FONT_SIZE_APPLE = 12
CHART_HEIGHT_APPLE = 450 # Increased for more vertical space

def create_pie_chart_learning_time_by_subject(user_id):
    study_tasks = get_study_tasks(user_id)
    fig = go.Figure()

    if not study_tasks:
        fig.update_layout(
            title_text="Lernzeiten nach Thema",
            title_x=0.5, title_y=0.97, title_font=dict(size=TITLE_FONT_SIZE_APPLE, family=APPLE_FONT_FAMILY, color=APPLE_TEXT_COLOR),
            annotations=[dict(text="Keine Lerndaten verfügbar.", showarrow=False, font=dict(size=16, family=APPLE_FONT_FAMILY, color=APPLE_SECONDARY_TEXT_COLOR))],
            xaxis_visible=False, yaxis_visible=False, paper_bgcolor=APPLE_BACKGROUND_COLOR, plot_bgcolor=APPLE_BACKGROUND_COLOR, height=CHART_HEIGHT_APPLE
        )
        return fig

    subject_times = {}
    total_duration_all_subjects = 0
    for task in study_tasks:
        subject = task.get("course_title", "Unbekanntes Fach")
        try:
            start_time_obj = datetime.strptime(task["start_time"], "%H:%M")
            end_time_obj = datetime.strptime(task["end_time"], "%H:%M")
            duration = (end_time_obj - start_time_obj).seconds / 3600
            if duration < 0: duration += 24
        except (ValueError, KeyError):
            continue 
        subject_times[subject] = subject_times.get(subject, 0) + duration
        total_duration_all_subjects += duration

    if not subject_times:
        fig.update_layout(
            title_text="Lernzeiten nach Thema",
            title_x=0.5, title_y=0.97, title_font=dict(size=TITLE_FONT_SIZE_APPLE, family=APPLE_FONT_FAMILY, color=APPLE_TEXT_COLOR),
            annotations=[dict(text="Keine gültigen Lerndaten.", showarrow=False, font=dict(size=16, family=APPLE_FONT_FAMILY, color=APPLE_SECONDARY_TEXT_COLOR))],
            xaxis_visible=False, yaxis_visible=False, paper_bgcolor=APPLE_BACKGROUND_COLOR, plot_bgcolor=APPLE_BACKGROUND_COLOR, height=CHART_HEIGHT_APPLE
        )
        return fig

    labels = list(subject_times.keys())
    values = list(subject_times.values())

    fig.add_trace(go.Pie(
        labels=labels, 
        values=values, 
        hole=.60, # Larger hole for a cleaner, modern Apple-like look
        hoverinfo="label+percent+value",
        hovertemplate="<b>%{label}</b><br>Stunden: %{value:.1f}h<br>Anteil: %{percent}<extra></extra>", 
        textinfo="label+percent", # Show label and percent outside
        textposition="outside",
        textfont=dict(size=SLICE_TEXT_FONT_SIZE_APPLE, family=APPLE_FONT_FAMILY, color=APPLE_TEXT_COLOR),
        outsidetextfont=dict(size=SLICE_TEXT_FONT_SIZE_APPLE, family=APPLE_FONT_FAMILY, color=APPLE_TEXT_COLOR),
        marker=dict(colors=SUBJECT_PALETTE_APPLE, line=dict(color=
"#FFFFFF"
, width=3)), # Slightly thicker white lines for better separation
        pull=0.01, # Very subtle pull, or can be removed
        sort=True, direction="clockwise"
    ))

    fig.update_layout(
        title_text="Lernzeiten nach Thema",
        title_x=0.5, title_y=0.95, title_font=dict(size=TITLE_FONT_SIZE_APPLE, family=APPLE_FONT_FAMILY, color=APPLE_TEXT_COLOR),
        showlegend=False, # Legend removed as textposition="outside" with labels should suffice
        font=dict(family=APPLE_FONT_FAMILY, color=APPLE_TEXT_COLOR),
        margin=dict(t=80, b=60, l=60, r=60), # Generous margins for outside text
        paper_bgcolor=APPLE_BACKGROUND_COLOR, plot_bgcolor=APPLE_BACKGROUND_COLOR,
        transition_duration=350,
        height=CHART_HEIGHT_APPLE,
        autosize=False,
        width=None,
        annotations=[
            dict(text=f"Total<br><b>{total_duration_all_subjects:.1f} Std.</b>",
                 x=0.5, y=0.5, font=dict(size=ANNOTATION_FONT_SIZE_APPLE, family=APPLE_FONT_FAMILY, color=APPLE_TEXT_COLOR), showarrow=False)
        ],
        hoverlabel=dict(bgcolor="#FFFFFF", font=dict(size=14, family=APPLE_FONT_FAMILY, color=APPLE_TEXT_COLOR), bordercolor="#EAEAEA")
    )
    return fig

def create_pie_chart_next_week_usage(user_id):
    events = get_calendar_events(user_id)
    next_week_start = datetime.now()
    next_week_end = next_week_start + timedelta(days=7)
    total_hours_in_week = 40 
    used_hours = 0

    if events:
        for event in events:
            try:
                event_date_str = event.get("date")
                if not event_date_str: continue
                event_date = datetime.strptime(event_date_str, "%Y-%m-%d")
                if next_week_start.date() <= event_date.date() < next_week_end.date():
                    used_hours += 1 
            except (ValueError, KeyError):
                continue

    used_hours = min(used_hours, total_hours_in_week)
    free_hours = total_hours_in_week - used_hours
    labels = ["Belegte Zeit", "Freie Zeit"]
    values = [used_hours, free_hours]
    current_palette = [USAGE_PALETTE_APPLE[0] if used_hours > 0 else "#EAEAEA", USAGE_PALETTE_APPLE[1] if free_hours > 0 else "#EAEAEA"]

    texttemplate_list = []
    # Only show text for slices with value > 0 to avoid clutter
    if values[0] > 0:
        texttemplate_list.append("%{label}<br>%{value:.0f}h (%{percent})")
    else:
        texttemplate_list.append("") # No text for zero value slice
    
    if values[1] > 0:
        texttemplate_list.append("%{label}<br>%{value:.0f}h (%{percent})")
    else:
        texttemplate_list.append("") # No text for zero value slice

    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=labels, values=values, hole=.60,
        hoverinfo="label+value+percent",
        hovertemplate="<b>%{label}</b><br>Stunden: %{value:.0f}h<br>Anteil: %{percent}<extra></extra>",
        textinfo="none", # Text will be handled by texttemplate or outside labels if preferred
        texttemplate=texttemplate_list, 
        textposition="outside", # Try outside to avoid overlap
        textfont=dict(size=SLICE_TEXT_FONT_SIZE_APPLE, family=APPLE_FONT_FAMILY, color=APPLE_TEXT_COLOR),
        outsidetextfont=dict(size=SLICE_TEXT_FONT_SIZE_APPLE, family=APPLE_FONT_FAMILY, color=APPLE_TEXT_COLOR),
        marker=dict(colors=current_palette, line=dict(color="#FFFFFF", width=3)),
        pull=0.01, sort=False
    ))

    fig.update_layout(
        title_text=f"Geplante Zeit: Nächste Woche", # Simplified title
        title_x=0.5, title_y=0.95, title_font=dict(size=TITLE_FONT_SIZE_APPLE, family=APPLE_FONT_FAMILY, color=APPLE_TEXT_COLOR),
        showlegend=False, # With only two items and outside text, legend might be redundant
        font=dict(family=APPLE_FONT_FAMILY, color=APPLE_TEXT_COLOR),
        margin=dict(t=80, b=60, l=60, r=60),
        paper_bgcolor=APPLE_BACKGROUND_COLOR, plot_bgcolor=APPLE_BACKGROUND_COLOR,
        transition_duration=350,
        height=CHART_HEIGHT_APPLE,
        autosize=False,
        width=None,
        annotations=[
            dict(text=f"<b>{used_hours:.0f}h / {total_hours_in_week}h</b><br>Belegt", 
                 x=0.5, y=0.5, font=dict(size=ANNOTATION_FONT_SIZE_APPLE, family=APPLE_FONT_FAMILY, color=USAGE_PALETTE_APPLE[0] if used_hours > 0 else APPLE_SECONDARY_TEXT_COLOR), showarrow=False)
        ],
        hoverlabel=dict(bgcolor="#FFFFFF", font=dict(size=14, family=APPLE_FONT_FAMILY, color=APPLE_TEXT_COLOR), bordercolor="#EAEAEA")
    )
    return fig

if __name__ == "__main__":
    sample_user_id = "test_user_123"
    print("Generating chart for Lernzeiten nach Thema (Apple Style)...")
    fig1 = create_pie_chart_learning_time_by_subject(sample_user_id)
    fig1.show()
    # fig1.write_html("learning_time_chart_apple.html")

    print("Generating chart for Geplante Zeit nächste Woche (Apple Style)...")
    fig2 = create_pie_chart_next_week_usage(sample_user_id)
    fig2.show()
    # fig2.write_html("next_week_usage_chart_apple.html")
    # print("Charts saved as HTML files for review (Apple Style).")

