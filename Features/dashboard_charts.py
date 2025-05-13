import plotly.graph_objects as go
from datetime import datetime, timedelta
# Assuming these functions exist in the user's environment and return data as expected
# from learning_suggestions import get_study_tasks 
# from database_manager import get_calendar_events 
import pandas as pd # Good practice, though not directly used in these specific modifications

# --- Mock data functions for testing purposes (if these are not available) ---
# It's better if the user has their actual data functions.
# If these are not defined, the script will fail when run standalone.
# For the purpose of this task, we assume they are provided elsewhere.

def get_study_tasks(user_id):
    # Mock data for create_pie_chart_learning_time_by_subject
    return [
        {"course_title": "Mathematics", "start_time": "09:00", "end_time": "11:00"},
        {"course_title": "Physics", "start_time": "13:00", "end_time": "14:30"},
        {"course_title": "History", "start_time": "15:00", "end_time": "16:00"},
        {"course_title": "Mathematics", "start_time": "10:00", "end_time": "12:00"},
        {"course_title": "Chemistry", "start_time": "08:00", "end_time": "09:30"},
    ]

def get_calendar_events(user_id):
    # Mock data for create_pie_chart_next_week_usage
    today = datetime.now()
    return [
        {"date": (today + timedelta(days=1)).strftime("%Y-%m-%d")},
        {"date": (today + timedelta(days=2)).strftime("%Y-%m-%d")},
        {"date": (today + timedelta(days=3)).strftime("%Y-%m-%d")},
        {"date": (today + timedelta(days=8)).strftime("%Y-%m-%d")} # This one is outside next 7 days
    ]
# --- End of Mock data functions ---


# Define new, more vibrant and modern color palettes
SUBJECT_PALETTE = ['#5E5CE6', '#007AFF', '#34C759', '#FF9500', '#FF3B30', '#AF52DE', '#5AC8FA', '#FFCC00']
USAGE_PALETTE = ['#FF9500', '#5E5CE6'] # Orange for used, Blue for free

# Define a base font family for a modern look
MODERN_FONT_FAMILY = "Inter, Arial, sans-serif"

def create_pie_chart_learning_time_by_subject(user_id):
    """Erstellt ein stark interaktives und hochwertiges Donut-Diagramm für die Lernzeiten nach Thema mit Plotly."""
    study_tasks = get_study_tasks(user_id)
    
    if not study_tasks:
        fig = go.Figure()
        fig.update_layout(
            title_text='Lernzeiten nach Thema',
            title_x=0.5, title_font_size=20, title_font_family=MODERN_FONT_FAMILY,
            annotations=[dict(text='Keine Lerndaten verfügbar.', showarrow=False, font_size=16, font_family=MODERN_FONT_FAMILY)],
            xaxis_visible=False, yaxis_visible=False,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig

    subject_times = {}
    total_duration_all_subjects = 0
    for task in study_tasks:
        subject = task.get('course_title', 'Unbekanntes Fach')
        try:
            start_time_obj = datetime.strptime(task['start_time'], "%H:%M")
            end_time_obj = datetime.strptime(task['end_time'], "%H:%M")
            duration = (end_time_obj - start_time_obj).seconds / 3600
            if duration < 0: duration += 24
        except (ValueError, KeyError):
            continue 
        subject_times[subject] = subject_times.get(subject, 0) + duration
        total_duration_all_subjects += duration

    if not subject_times:
        fig = go.Figure()
        fig.update_layout(
            title_text='Lernzeiten nach Thema',
            title_x=0.5, title_font_size=20, title_font_family=MODERN_FONT_FAMILY,
            annotations=[dict(text='Keine gültigen Lerndaten nach Aggregation.', showarrow=False, font_size=16, font_family=MODERN_FONT_FAMILY)],
            xaxis_visible=False, yaxis_visible=False,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig

    labels = list(subject_times.keys())
    values = list(subject_times.values())

    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=.45,  # Slightly larger hole for modern feel
        hoverinfo='label+percent+value',
        hovertemplate='<b>%{label}</b><br>Stunden: %{value:.1f}h<br>Anteil: %{percent}<extra></extra>', # Custom hover template
        textinfo='percent',
        textfont_size=14,
        textfont_family=MODERN_FONT_FAMILY,
        marker=dict(colors=SUBJECT_PALETTE, line=dict(color='#FFFFFF', width=2)), # White lines for separation
        pull=[0.02] * len(labels), # Slight pull for all slices for a subtle 3D/separated effect
        sort=False # Keep order as provided if meaningful
    )])

    fig.update_layout(
        title_text='Lernzeiten nach Thema',
        title_x=0.5, title_font_size=20, title_font_family=MODERN_FONT_FAMILY,
        legend_title_text='Themen',
        legend_title_font_family=MODERN_FONT_FAMILY,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, # Centered horizontal legend
            font=dict(family=MODERN_FONT_FAMILY, size=12, color="#555555"),
            bgcolor='rgba(255,255,255,0.6)', # Semi-transparent legend background
            bordercolor="#CCCCCC",
            borderwidth=1
        ),
        font=dict(family=MODERN_FONT_FAMILY, size=12, color="#333333"),
        margin=dict(t=80, b=50, l=50, r=50), # Adjusted margins for title/legend
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        transition_duration=500, # Animation for smooth transitions
        annotations=[
            dict(text=f'Total<br>{total_duration_all_subjects:.1f} Std.', 
                 x=0.5, y=0.5, font_size=18, font_family=MODERN_FONT_FAMILY, showarrow=False, font_color="#666666")
        ]
    )
    
    return fig

def create_pie_chart_next_week_usage(user_id):
    """Erstellt ein stark interaktives und hochwertiges Donut-Diagramm für die Zeitnutzung der nächsten Woche mit Plotly."""
    events = get_calendar_events(user_id)
    next_week_start = datetime.now()
    next_week_end = next_week_start + timedelta(days=7)
    
    total_hours_in_week = 40 
    used_hours = 0

    if events:
        for event in events:
            try:
                event_date_str = event.get('date')
                if not event_date_str: continue
                event_date = datetime.strptime(event_date_str, "%Y-%m-%d")
                if next_week_start.date() <= event_date.date() < next_week_end.date():
                    used_hours += 1 # Assuming 1 hour per event
            except (ValueError, KeyError):
                continue

    used_hours = min(used_hours, total_hours_in_week)
    free_hours = total_hours_in_week - used_hours

    labels = ['Belegte Zeit', 'Freie Zeit']
    values = [used_hours, free_hours]

    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=.45,
        hoverinfo='label+value+percent',
        hovertemplate='<b>%{label}</b><br>Stunden: %{value:.0f}h<br>Anteil: %{percent}<extra></extra>',
        textinfo='value+percent',
        texttemplate='%{value:.0f}h<br>(%{percent})', # Custom text on slices
        textposition='inside',
        textfont_size=14,
        textfont_family=MODERN_FONT_FAMILY,
        marker=dict(colors=USAGE_PALETTE, line=dict(color='#FFFFFF', width=2)),
        pull=[0.02, 0.02],
        sort=False
    )])

    fig.update_layout(
        title_text=f'Geplante Zeit: Nächste Woche ({total_hours_in_week} Std. Basis)',
        title_x=0.5, title_font_size=20, title_font_family=MODERN_FONT_FAMILY,
        legend_title_text='Status',
        legend_title_font_family=MODERN_FONT_FAMILY,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5,
            font=dict(family=MODERN_FONT_FAMILY, size=12, color="#555555"),
            bgcolor='rgba(255,255,255,0.6)',
            bordercolor="#CCCCCC",
            borderwidth=1
        ),
        font=dict(family=MODERN_FONT_FAMILY, size=12, color="#333333"),
        margin=dict(t=80, b=50, l=50, r=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        transition_duration=500,
        annotations=[
            dict(text=f'{used_hours:.0f}h<br>Belegt', 
                 x=0.5, y=0.5, font_size=18, font_family=MODERN_FONT_FAMILY, showarrow=False, font_color=USAGE_PALETTE[0])
        ]
    )

    return fig

# Example usage (for testing, if you run this script directly):
if __name__ == '__main__':
    # You would typically get user_id from your Streamlit app context
    sample_user_id = "test_user_123"

    fig1 = create_pie_chart_learning_time_by_subject(sample_user_id)
    # In a Streamlit app, you would use: st.plotly_chart(fig1)
    # For local testing, you can show the figure:
    # fig1.show() 
    print("Figure 1 (Learning Time by Subject) created. Call fig1.show() to display locally.")

    fig2 = create_pie_chart_next_week_usage(sample_user_id)
    # In a Streamlit app, you would use: st.plotly_chart(fig2)
    # For local testing, you can show the figure:
    # fig2.show()
    print("Figure 2 (Next Week Usage) created. Call fig2.show() to display locally.")

    # To save as HTML (which can be opened in a browser to see interactivity)
    # fig1.write_html("learning_time_chart.html")
    # fig2.write_html("next_week_usage_chart.html")
    # print("Charts saved as HTML files for review.")

