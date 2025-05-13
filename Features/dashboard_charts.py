import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd

# --- Mock data functions for testing purposes ---
def get_study_tasks(user_id):
    return [
        {"course_title": "Mathematics", "start_time": "09:00", "end_time": "11:00"},
        {"course_title": "Physics", "start_time": "13:00", "end_time": "14:30"},
        {"course_title": "History", "start_time": "15:00", "end_time": "16:00"},
        {"course_title": "Mathematics", "start_time": "10:00", "end_time": "12:00"},
        {"course_title": "Chemistry", "start_time": "08:00", "end_time": "09:30"},
    ]

def get_calendar_events(user_id):
    today = datetime.now()
    return [
        {"date": (today + timedelta(days=1)).strftime("%Y-%m-%d")},
        {"date": (today + timedelta(days=2)).strftime("%Y-%m-%d")},
        {"date": (today + timedelta(days=3)).strftime("%Y-%m-%d")},
        {"date": (today + timedelta(days=8)).strftime("%Y-%m-%d")}
    ]
# --- End of Mock data functions ---

SUBJECT_PALETTE = ["#6C63FF", "#00B8A9", "#FFC300", "#FF5733", "#C70039", "#900C3F", "#581845"]
USAGE_PALETTE = ["#FFB300", "#6C63FF"]
MODERN_FONT_FAMILY = "Inter, Arial, Helvetica, sans-serif"
BASE_FONT_COLOR = "#333333"
TITLE_FONT_SIZE = 16
LEGEND_FONT_SIZE = 11
ANNOTATION_FONT_SIZE = 16
CHART_HEIGHT = 380

def create_pie_chart_learning_time_by_subject(user_id):
    study_tasks = get_study_tasks(user_id)
    fig = go.Figure()

    if not study_tasks:
        fig.update_layout(
            title_text=
"Lernzeiten nach Thema"
,
            title_x=0.5, title_y=0.95, title_font=dict(size=TITLE_FONT_SIZE, family=MODERN_FONT_FAMILY, color=BASE_FONT_COLOR),
            annotations=[dict(text=
"Keine Lerndaten verfügbar.\n(Mock-Daten aktiv)"

, showarrow=False, font=dict(size=14, family=MODERN_FONT_FAMILY, color=BASE_FONT_COLOR))],
            xaxis_visible=False, yaxis_visible=False, paper_bgcolor=
"rgba(0,0,0,0)"
, plot_bgcolor=
"rgba(0,0,0,0)"
, height=CHART_HEIGHT
        )
        return fig

    subject_times = {}
    total_duration_all_subjects = 0
    for task in study_tasks:
        subject = task.get(
"course_title"
, 
"Unbekanntes Fach"

)
        try:
            start_time_obj = datetime.strptime(task[
"start_time"
], "%H:%M")
            end_time_obj = datetime.strptime(task[
"end_time"
], "%H:%M")
            duration = (end_time_obj - start_time_obj).seconds / 3600
            if duration < 0: duration += 24
        except (ValueError, KeyError):
            continue 
        subject_times[subject] = subject_times.get(subject, 0) + duration
        total_duration_all_subjects += duration

    if not subject_times:
        fig.update_layout(
            title_text=
"Lernzeiten nach Thema"
,
            title_x=0.5, title_y=0.95, title_font=dict(size=TITLE_FONT_SIZE, family=MODERN_FONT_FAMILY, color=BASE_FONT_COLOR),
            annotations=[dict(text=
"Keine gültigen Lerndaten nach Aggregation.\n(Mock-Daten aktiv)"

, showarrow=False, font=dict(size=14, family=MODERN_FONT_FAMILY, color=BASE_FONT_COLOR))],
            xaxis_visible=False, yaxis_visible=False, paper_bgcolor=
"rgba(0,0,0,0)"
, plot_bgcolor=
"rgba(0,0,0,0)"
, height=CHART_HEIGHT
        )
        return fig

    labels = list(subject_times.keys())
    values = list(subject_times.values())

    fig.add_trace(go.Pie(
        labels=labels, 
        values=values, 
        hole=.55,
        hoverinfo=
"label+percent+value"
,
        hovertemplate=
"<b>%{label}</b><br>Stunden: %{value:.1f}h<br>Anteil: %{percent}<extra></extra>"
, 
        textinfo=
"percent"
,
        textfont=dict(size=11, family=MODERN_FONT_FAMILY, color=
"#FFFFFF"
),
        marker=dict(colors=SUBJECT_PALETTE, line=dict(color=
"#FFFFFF"
, width=2.5)),
        pull=[0.04 if v > 0 else 0 for v in values],
        sort=True, direction=
"clockwise"
, insidetextorientation=
"radial"

    ))

    fig.update_layout(
        title_text=
"Lernzeiten nach Thema"
,
        title_x=0.5, title_y=0.96, title_font=dict(size=TITLE_FONT_SIZE, family=MODERN_FONT_FAMILY, color=BASE_FONT_COLOR),
        legend_title_text=
""
,
        legend=dict(
            orientation="h", yanchor="top", y=0.90, xanchor="center", x=0.5,
            font=dict(family=MODERN_FONT_FAMILY, size=LEGEND_FONT_SIZE, color=BASE_FONT_COLOR),
            bgcolor=
"rgba(255,255,255,0.0)"
, bordercolor=
"rgba(0,0,0,0)"
, traceorder="normal"
        ),
        font=dict(family=MODERN_FONT_FAMILY, color=BASE_FONT_COLOR),
        margin=dict(t=60, b=30, l=20, r=20, autoexpand=True),
        paper_bgcolor=
"rgba(0,0,0,0)"
, plot_bgcolor=
"rgba(0,0,0,0)"
,
        transition_duration=250,
        height=CHART_HEIGHT,
        autosize=False,
        width=None,
        annotations=[
            dict(text=f
"Total<br><b>{total_duration_all_subjects:.1f} Std.</b>"
, 
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
                event_date_str = event.get(
"date"
)
                if not event_date_str: continue
                event_date = datetime.strptime(event_date_str, "%Y-%m-%d")
                if next_week_start.date() <= event_date.date() < next_week_end.date():
                    used_hours += 1 
            except (ValueError, KeyError):
                continue

    used_hours = min(used_hours, total_hours_in_week)
    free_hours = total_hours_in_week - used_hours
    labels = [
"Belegte Zeit"
, 
"Freie Zeit"
]
    values = [used_hours, free_hours]
    current_palette = [USAGE_PALETTE[0] if used_hours > 0 else 
"#E0E0E0"
, USAGE_PALETTE[1] if free_hours > 0 else 
"#E0E0E0"
]

    # Prepare texttemplate list based on values
    texttemplate_list = []
    if values[0] > 0:
        texttemplate_list.append("%{value:.0f}h<br>(%{percent})") # Corrected: No f-string
    else:
        texttemplate_list.append("")
    
    if values[1] > 0:
        texttemplate_list.append("%{value:.0f}h<br>(%{percent})") # Corrected: No f-string
    else:
        texttemplate_list.append("")

    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=labels, values=values, hole=.55,
        hoverinfo=
"label+value+percent"
,
        hovertemplate=
"<b>%{label}</b><br>Stunden: %{value:.0f}h<br>Anteil: %{percent}<extra></extra>"
,
        textinfo=
"value+percent"
, 
        texttemplate=texttemplate_list,
        textposition=
"inside"
, textfont=dict(size=11, family=MODERN_FONT_FAMILY, color=
"#FFFFFF"
),
        marker=dict(colors=current_palette, line=dict(color=
"#FFFFFF"
, width=2.5)),
        pull=[0.04 if v > 0 else 0 for v in values], sort=False, insidetextorientation=
"radial"

    ))

    fig.update_layout(
        title_text=f
"Geplante Zeit: Nächste Woche ({total_hours_in_week} Std. Basis)"
,
        title_x=0.5, title_y=0.96, title_font=dict(size=TITLE_FONT_SIZE, family=MODERN_FONT_FAMILY, color=BASE_FONT_COLOR),
        legend_title_text=
""
,
        legend=dict(
            orientation="h", yanchor="top", y=0.90, xanchor="center", x=0.5,
            font=dict(family=MODERN_FONT_FAMILY, size=LEGEND_FONT_SIZE, color=BASE_FONT_COLOR),
            bgcolor=
"rgba(255,255,255,0.0)"
, bordercolor=
"rgba(0,0,0,0)"
, traceorder="normal"
        ),
        font=dict(family=MODERN_FONT_FAMILY, color=BASE_FONT_COLOR),
        margin=dict(t=60, b=30, l=20, r=20, autoexpand=True),
        paper_bgcolor=
"rgba(0,0,0,0)"
, plot_bgcolor=
"rgba(0,0,0,0)"
,
        transition_duration=250,
        height=CHART_HEIGHT,
        autosize=False,
        width=None,
        annotations=[
            dict(text=f
"<b>{used_hours:.0f}h</b><br>Belegt"
, 
                 x=0.5, y=0.5, font=dict(size=ANNOTATION_FONT_SIZE, family=MODERN_FONT_FAMILY, color=USAGE_PALETTE[0] if used_hours > 0 else BASE_FONT_COLOR), showarrow=False)
        ],
        hoverlabel=dict(bgcolor="#FFFFFF", font=dict(size=13, family=MODERN_FONT_FAMILY, color=BASE_FONT_COLOR), bordercolor="#DDDDDD"),
        uniformtext_minsize=9, uniformtext_mode=
"hide"

    )
    return fig

if __name__ == 
"__main__"
:
    sample_user_id = "test_user_123"
    print("Generating chart for Lernzeiten nach Thema...")
    fig1 = create_pie_chart_learning_time_by_subject(sample_user_id)
    fig1.show()

    print("Generating chart for Geplante Zeit nächste Woche...")
    fig2 = create_pie_chart_next_week_usage(sample_user_id)
    fig2.show()

