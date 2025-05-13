import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd

# --- Mock data functions for testing purposes ---
# These are included so the script can be run standalone and to ensure consistent data for chart appearance.
# In a real application, these would be replaced by actual data fetching logic.
def get_study_tasks(user_id):
    # Mock data for create_pie_chart_learning_time_by_subject
    return [
        {"course_title": "Mathematics", "start_time": "09:00", "end_time": "11:00"}, # 2h
        {"course_title": "Physics", "start_time": "13:00", "end_time": "14:30"},     # 1.5h
        {"course_title": "History", "start_time": "15:00", "end_time": "16:00"},     # 1h
        {"course_title": "Mathematics", "start_time": "10:00", "end_time": "12:00"}, # 2h (total Math: 4h)
        {"course_title": "Chemistry", "start_time": "08:00", "end_time": "09:30"},   # 1.5h
        # Total 8.0 hours: Math 50%, Physics 18.75%, History 12.5%, Chemistry 18.75%
    ]

def get_calendar_events(user_id):
    # Mock data for create_pie_chart_next_week_usage
    today = datetime.now()
    return [
        {"date": (today + timedelta(days=1)).strftime("%Y-%m-%d")}, # Event 1
        {"date": (today + timedelta(days=2)).strftime("%Y-%m-%d")}, # Event 2
        {"date": (today + timedelta(days=3)).strftime("%Y-%m-%d")}, # Event 3 (used_hours = 3)
        {"date": (today + timedelta(days=8)).strftime("%Y-%m-%d")}  # This one is outside next 7 days
    ]
# --- End of Mock data functions ---

# Define new, more vibrant and modern color palettes and fonts
SUBJECT_PALETTE = ["#6C63FF", "#00B8A9", "#FFC300", "#FF5733", "#C70039", "#900C3F", "#581845"]
USAGE_PALETTE = ["#FFB300", "#6C63FF"] # Vibrant Orange for used, Purple for free
MODERN_FONT_FAMILY = "Inter, Arial, Helvetica, sans-serif"
BASE_FONT_COLOR = "#333333" # Darker grey for better readability
TITLE_FONT_SIZE = 16
LEGEND_FONT_SIZE = 11 # Increased slightly for readability
ANNOTATION_FONT_SIZE = 16
CHART_HEIGHT = 380 # Standard height for charts

def create_pie_chart_learning_time_by_subject(user_id):
    study_tasks = get_study_tasks(user_id)
    fig = go.Figure()

    if not study_tasks:
        fig.update_layout(
            title_text=\'Lernzeiten nach Thema\',
            title_x=0.5, title_y=0.95, title_font=dict(size=TITLE_FONT_SIZE, family=MODERN_FONT_FAMILY, color=BASE_FONT_COLOR),
            annotations=[dict(text=\'Keine Lerndaten verfügbar.\
(Mock-Daten aktiv)\
', showarrow=False, font=dict(size=14, family=MODERN_FONT_FAMILY, color=BASE_FONT_COLOR))],
            xaxis_visible=False, yaxis_visible=False, paper_bgcolor=\'rgba(0,0,0,0)\
', plot_bgcolor=\'rgba(0,0,0,0)\
', height=CHART_HEIGHT
        )
        return fig

    subject_times = {}
    total_duration_all_subjects = 0
    for task in study_tasks:
        subject = task.get(\'course_title\
', \'Unbekanntes Fach\
')
        try:
            start_time_obj = datetime.strptime(task[\"start_time\"], "%H:%M")
            end_time_obj = datetime.strptime(task[\"end_time\"], "%H:%M")
            duration = (end_time_obj - start_time_obj).seconds / 3600
            if duration < 0: duration += 24
        except (ValueError, KeyError):
            continue 
        subject_times[subject] = subject_times.get(subject, 0) + duration
        total_duration_all_subjects += duration

    if not subject_times:
        fig.update_layout(
            title_text=\'Lernzeiten nach Thema\',
            title_x=0.5, title_y=0.95, title_font=dict(size=TITLE_FONT_SIZE, family=MODERN_FONT_FAMILY, color=BASE_FONT_COLOR),
            annotations=[dict(text=\'Keine gültigen Lerndaten nach Aggregation.\
(Mock-Daten aktiv)\
', showarrow=False, font=dict(size=14, family=MODERN_FONT_FAMILY, color=BASE_FONT_COLOR))],
            xaxis_visible=False, yaxis_visible=False, paper_bgcolor=\'rgba(0,0,0,0)\
', plot_bgcolor=\'rgba(0,0,0,0)\
', height=CHART_HEIGHT
        )
        return fig

    labels = list(subject_times.keys())
    values = list(subject_times.values())

    fig.add_trace(go.Pie(
        labels=labels, 
        values=values, 
        hole=.55,
        hoverinfo=\'label+percent+value\
',
        hovertemplate=\'<b>%{label}</b><br>Stunden: %{value:.1f}h<br>Anteil: %{percent}<extra></extra>\
', 
        textinfo=\'percent\
',
        textfont=dict(size=11, family=MODERN_FONT_FAMILY, color=\'#FFFFFF\
'), # White text on slices for contrast
        marker=dict(colors=SUBJECT_PALETTE, line=dict(color=\'#FFFFFF\
', width=2.5)),
        pull=[0.04 if v > 0 else 0 for v in values],
        sort=True, direction=\'clockwise\
', insidetextorientation=\'radial\
'
    ))

    fig.update_layout(
        title_text=\'Lernzeiten nach Thema\
',
        title_x=0.5, title_y=0.96, title_font=dict(size=TITLE_FONT_SIZE, family=MODERN_FONT_FAMILY, color=BASE_FONT_COLOR),
        legend_title_text=\'\
', # No title for legend, items are self-explanatory
        legend=dict(
            orientation="h", yanchor="top", y=0.90, xanchor="center", x=0.5, # Legend below title
            font=dict(family=MODERN_FONT_FAMILY, size=LEGEND_FONT_SIZE, color=BASE_FONT_COLOR),
            bgcolor=\'rgba(255,255,255,0.0)\
', bordercolor=\'rgba(0,0,0,0)\
', traceorder="normal"
        ),
        font=dict(family=MODERN_FONT_FAMILY, color=BASE_FONT_COLOR),
        margin=dict(t=60, b=30, l=20, r=20, autoexpand=True), # autoexpand True to help with fitting
        paper_bgcolor=\'rgba(0,0,0,0)\
', plot_bgcolor=\'rgba(0,0,0,0)\
',
        transition_duration=250,
        height=CHART_HEIGHT,
        autosize=False, # Important with explicit height/width for Streamlit
        width=None,     # Let Streamlit handle width with use_container_width
        annotations=[
            dict(text=f"Total<br><b>{total_duration_all_subjects:.1f} Std.</b>", 
                 x=0.5, y=0.5, font=dict(size=ANNOTATION_FONT_SIZE, family=MODERN_FONT_FAMILY, color=BASE_FONT_COLOR), showarrow=False)
        ],
        hoverlabel=dict(bgcolor="#FFFFFF", font=dict(size=13, family=MODERN_FONT_FAMILY, color=BASE_FONT_COLOR), bordercolor="#DDDDDD")
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
                event_date_str = event.get(\'date\
')
                if not event_date_str: continue
                event_date = datetime.strptime(event_date_str, "%Y-%m-%d")
                if next_week_start.date() <= event_date.date() < next_week_end.date():
                    used_hours += 1 
            except (ValueError, KeyError):
                continue

    used_hours = min(used_hours, total_hours_in_week)
    free_hours = total_hours_in_week - used_hours
    labels = [\'Belegte Zeit\
', \'Freie Zeit\
']
    values = [used_hours, free_hours]
    current_palette = [USAGE_PALETTE[0] if used_hours > 0 else \'#E0E0E0\
', USAGE_PALETTE[1] if free_hours > 0 else \'#E0E0E0\
']

    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=labels, values=values, hole=.55,
        hoverinfo=\'label+value+percent\
',
        hovertemplate=\'<b>%{label}</b><br>Stunden: %{value:.0f}h<br>Anteil: %{percent}<extra></extra>\
',
        textinfo=\'value+percent\
', 
        texttemplate=[f"%{value:.0f}h<br>(%{percent})" if values[0] > 0 else "", f"%{value:.0f}h<br>(%{percent})" if values[1] > 0 else ""],
        textposition=\'inside\
', textfont=dict(size=11, family=MODERN_FONT_FAMILY, color=\'#FFFFFF\
'),
        marker=dict(colors=current_palette, line=dict(color=\'#FFFFFF\
', width=2.5)),
        pull=[0.04 if v > 0 else 0 for v in values], sort=False, insidetextorientation=\'radial\
'
    ))

    fig.update_layout(
        title_text=f\"Geplante Zeit: Nächste Woche ({total_hours_in_week} Std. Basis)\
",
        title_x=0.5, title_y=0.96, title_font=dict(size=TITLE_FONT_SIZE, family=MODERN_FONT_FAMILY, color=BASE_FONT_COLOR),
        legend_title_text=\'\
',
        legend=dict(
            orientation="h", yanchor="top", y=0.90, xanchor="center", x=0.5,
            font=dict(family=MODERN_FONT_FAMILY, size=LEGEND_FONT_SIZE, color=BASE_FONT_COLOR),
            bgcolor=\'rgba(255,255,255,0.0)\
', bordercolor=\'rgba(0,0,0,0)\
', traceorder="normal"
        ),
        font=dict(family=MODERN_FONT_FAMILY, color=BASE_FONT_COLOR),
        margin=dict(t=60, b=30, l=20, r=20, autoexpand=True),
        paper_bgcolor=\'rgba(0,0,0,0)\
', plot_bgcolor=\'rgba(0,0,0,0)\
',
        transition_duration=250,
        height=CHART_HEIGHT,
        autosize=False,
        width=None,
        annotations=[
            dict(text=f"<b>{used_hours:.0f}h</b><br>Belegt", 
                 x=0.5, y=0.5, font=dict(size=ANNOTATION_FONT_SIZE, family=MODERN_FONT_FAMILY, color=USAGE_PALETTE[0] if used_hours > 0 else BASE_FONT_COLOR), showarrow=False)
        ],
        hoverlabel=dict(bgcolor="#FFFFFF", font=dict(size=13, family=MODERN_FONT_FAMILY, color=BASE_FONT_COLOR), bordercolor="#DDDDDD"),
        uniformtext_minsize=9, uniformtext_mode=\'hide\'
    )
    return fig

# Example usage for direct testing (e.g., python dashboard_charts.py)
if __name__ == \'__main__\
':
    sample_user_id = "test_user_123"
    print("Generating chart for Lernzeiten nach Thema...")
    fig1 = create_pie_chart_learning_time_by_subject(sample_user_id)
    fig1.show()
    # fig1.write_html("learning_time_chart_v3.html")

    print("Generating chart for Geplante Zeit nächste Woche...")
    fig2 = create_pie_chart_next_week_usage(sample_user_id)
    fig2.show()
    # fig2.write_html("next_week_usage_chart_v3.html")
    # print("Charts saved as HTML files for review (v3).")

