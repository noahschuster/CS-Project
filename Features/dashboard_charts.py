import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import pandas as pd # Added for DataFrame handling

# --- Import real data functions ---
# These functions are expected to be in files accessible in the same environment
# as this script, typically utils.py and database_manager.py in the same directory
# or a properly configured Python path.

# Attempt to import, with fallbacks to mock data if imports fail (for standalone testing)
# In a real deployment, these imports MUST succeed.
try:
    from utils import get_user_sessions # For study task data
    from database_manager import get_calendar_events # For calendar event data
    print("Successfully imported real data functions: get_user_sessions, get_calendar_events")
    USING_REAL_DATA = True
except ImportError as e:
    print(f"Warning: Could not import real data functions ({e}). Falling back to MOCK data.")
    USING_REAL_DATA = False
    # --- Mock data functions (fallback if real imports fail) ---
    def get_user_sessions(user_id):
        print("Using MOCK get_user_sessions")
        # Mocking a DataFrame similar to what get_user_sessions might return
        data = {
            "course_title": ["Mathematics", "Physics", "History", "Mathematics", "Chemistry"],
            "duration_hours": [2.0, 1.5, 1.0, 2.0, 1.5]
        }
        return pd.DataFrame(data)

    def get_calendar_events(user_id):
        print("Using MOCK get_calendar_events")
        today = datetime.now()
        return [
            {"date": (today + timedelta(days=1)).strftime("%Y-%m-%d"), "type": "Meeting", "is_deadline": False, "time": "10:00", "color": "blue"}, 
            {"date": (today + timedelta(days=2)).strftime("%Y-%m-%d"), "type": "Prüfung", "is_deadline": True, "time": "14:00", "color": "red"}, 
            {"date": (today + timedelta(days=3)).strftime("%Y-%m-%d"), "type": "Aufgabe fällig", "is_deadline": True, "time": "23:59", "color": "orange"}, 
            {"date": (today + timedelta(days=8)).strftime("%Y-%m-%d"), "type": "Projekt fällig", "is_deadline": True, "time": "17:00", "color": "green"}  
        ]
# --- End of Data functions ---

# Apple-inspired Aesthetics for Matplotlib
APPLE_FONT_FAMILY_MPL = "Arial" 
APPLE_TEXT_COLOR_MPL = "#1D1D1F" 
APPLE_SECONDARY_TEXT_COLOR_MPL = "#6E6E73" 

SUBJECT_PALETTE_APPLE_MPL = ["#0A84FF", "#30D158", "#FF9F0A", "#BF5AF2", "#64D2FF", "#FF453A", "#FFD60A"]
USAGE_PALETTE_APPLE_MPL = ["#FF9F0A", "#0A84FF"]

TITLE_FONT_SIZE_MPL = 18
LABEL_FONT_SIZE_MPL = 11 
SLICE_LABEL_FONT_SIZE_MPL = 11 
ANNOTATION_FONT_SIZE_MPL = 16 
FIG_DPI = 150
CHART_FIGSIZE = (7.5, 5.5) # Slightly larger figure size for better layout

def create_donut_chart_lernzeiten_seaborn(user_id):
    # Get data using the (potentially real) function
    sessions_df = get_user_sessions(user_id)

    plt.style.use("seaborn-v0_8-whitegrid") 
    plt.rcParams["font.family"] = APPLE_FONT_FAMILY_MPL
    plt.rcParams["text.color"] = APPLE_TEXT_COLOR_MPL
    plt.rcParams["axes.labelcolor"] = APPLE_TEXT_COLOR_MPL
    plt.rcParams["xtick.color"] = APPLE_SECONDARY_TEXT_COLOR_MPL
    plt.rcParams["ytick.color"] = APPLE_SECONDARY_TEXT_COLOR_MPL

    fig, ax = plt.subplots(figsize=CHART_FIGSIZE, dpi=FIG_DPI)
    fig.patch.set_alpha(0) 
    ax.patch.set_alpha(0)  

    if sessions_df is None or sessions_df.empty or "duration_hours" not in sessions_df.columns or "course_title" not in sessions_df.columns:
        ax.text(0.5, 0.5, "Keine Lerndaten verfügbar.", ha="center", va="center", fontsize=ANNOTATION_FONT_SIZE_MPL, color=APPLE_SECONDARY_TEXT_COLOR_MPL)
        ax.set_title("Lernzeiten nach Thema", fontsize=TITLE_FONT_SIZE_MPL, color=APPLE_TEXT_COLOR_MPL, pad=25, loc="center")
        ax.axis("off")
        plt.tight_layout(pad=1.0)
        return fig

    # Aggregate time by subject from the DataFrame
    subject_times_series = sessions_df.groupby("course_title")["duration_hours"].sum()
    subject_times = subject_times_series.to_dict()
    total_duration_all_subjects = subject_times_series.sum()

    if not subject_times or total_duration_all_subjects == 0:
        ax.text(0.5, 0.5, "Keine gültigen Lerndaten.", ha="center", va="center", fontsize=ANNOTATION_FONT_SIZE_MPL, color=APPLE_SECONDARY_TEXT_COLOR_MPL)
        ax.set_title("Lernzeiten nach Thema", fontsize=TITLE_FONT_SIZE_MPL, color=APPLE_TEXT_COLOR_MPL, pad=25, loc="center")
        ax.axis("off")
        plt.tight_layout(pad=1.0)
        return fig

    labels = list(subject_times.keys())
    sizes = list(subject_times.values())
    explode = [0.02] * len(labels) # Reduced explode for a tighter look

    # --- Direct Labeling Attempt ---
    # Instead of legend, try to label slices directly if possible, or use legend more effectively.
    # For now, keeping legend but ensuring it doesn't overlap.

    wedges, texts_pie, autotexts = ax.pie(sizes, explode=explode, labels=None, autopct="%1.1f%%", 
                                      startangle=90, colors=SUBJECT_PALETTE_APPLE_MPL,
                                      pctdistance=0.85, wedgeprops=dict(width=0.40, edgecolor="white", linewidth=3))

    for autotext_obj in autotexts: 
        autotext_obj.set_color("white")
        autotext_obj.set_fontsize(LABEL_FONT_SIZE_MPL)
        autotext_obj.set_fontweight("bold")

    ax.set_title("Lernzeiten nach Thema", fontsize=TITLE_FONT_SIZE_MPL, color=APPLE_TEXT_COLOR_MPL, pad=35, loc="center")
    
    ax.text(0, 0, f"Total\n{total_duration_all_subjects:.1f} Std.", ha="center", va="center", fontsize=ANNOTATION_FONT_SIZE_MPL, color=APPLE_TEXT_COLOR_MPL, fontweight="medium")
    
    # Improved Legend: Positioned below the chart, horizontal
    if len(labels) > 0:
        ax.legend(wedges, labels, title=None, loc="upper center", bbox_to_anchor=(0.5, -0.05), 
                  fontsize=LABEL_FONT_SIZE_MPL, frameon=False, labelcolor=APPLE_TEXT_COLOR_MPL, ncol=min(len(labels), 3))

    ax.axis("equal") 
    plt.tight_layout(pad=1.0, rect=[0, 0.05, 1, 0.95]) # Adjust rect to make space for legend below and title above
    return fig

def create_donut_chart_next_week_seaborn(user_id):
    # Get data using the (potentially real) function
    events = get_calendar_events(user_id)
    
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams["font.family"] = APPLE_FONT_FAMILY_MPL
    plt.rcParams["text.color"] = APPLE_TEXT_COLOR_MPL
    plt.rcParams["axes.labelcolor"] = APPLE_TEXT_COLOR_MPL
    plt.rcParams["xtick.color"] = APPLE_SECONDARY_TEXT_COLOR_MPL
    plt.rcParams["ytick.color"] = APPLE_SECONDARY_TEXT_COLOR_MPL

    fig, ax = plt.subplots(figsize=CHART_FIGSIZE, dpi=FIG_DPI)
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)

    total_hours_in_week = 40 # As per original script logic
    used_hours = 0

    if events:
        # Logic from original dashboard_charts.py (Plotly) for calculating used_hours
        # Assuming events are for the *current* week, and we need to find *next* week's usage.
        # The original logic for next_week_usage in Plotly version was based on calendar_events for the *next* 7 days.
        # Let's replicate that logic more closely.
        
        # This part needs to align with how your `get_calendar_events` and `dashboard.py` determine "next week usage"
        # The mock data was simple. The real data processing from your original Plotly script for this chart needs to be used.
        # For now, I will assume `get_calendar_events` returns events and we need to filter for next week.
        # And that each relevant event contributes a fixed amount of hours (e.g., 3 hours as in mock, or needs to be derived)
        
        # --- This is a placeholder for the actual logic from your system ---
        # Based on your dashboard.py, it seems `get_calendar_events` gets all events.
        # The original Plotly `create_pie_chart_next_week_usage` had its own logic to sum up hours.
        # Let's assume `get_calendar_events` gives all events, and we filter for next 7 days.
        # And assume each event implies some duration (e.g., 3 hours, or needs to be in event data)
        
        now = datetime.now()
        next_seven_days_start = now # Or now + timedelta(days=1) depending on definition
        next_seven_days_end = next_seven_days_start + timedelta(days=7)
        
        # Example: if your events have 'start_time' and 'end_time' or a 'duration_hours' field:
        for event in events:
            try:
                event_date_str = event.get("date")
                if not event_date_str: continue
                event_date = datetime.strptime(event_date_str, "%Y-%m-%d")

                if next_seven_days_start.date() <= event_date.date() < next_seven_days_end.date():
                    # Assuming a default duration if not specified, or you might have it in event data
                    # This is a critical part that needs to match your actual data structure and intent
                    # The original Plotly chart script might have had more specific logic here.
                    # For now, using a placeholder of 3 hours per event in the next 7 days.
                    event_duration = event.get("duration_hours", 3) # Defaulting to 3 if not present
                    used_hours += event_duration
            except (ValueError, KeyError):
                continue
        # --- End of placeholder logic ---

    used_hours = min(used_hours, total_hours_in_week)
    free_hours = total_hours_in_week - used_hours
    
    chart_labels = ["Belegte Zeit", "Freie Zeit"]
    sizes = [used_hours, free_hours]
    current_palette = [USAGE_PALETTE_APPLE_MPL[0] if used_hours > 0 else "#E9E9EA", 
                       USAGE_PALETTE_APPLE_MPL[1] if free_hours > 0 else "#E9E9EA"]
    explode = [0.02, 0.02]

    def make_autopct(values):
        def my_autopct(pct):
            total = sum(values)
            if total == 0: # Avoid division by zero if total is 0
                return "0h\n(0.0%)" if pct == 0 else ""
            val = int(round(pct*total/100.0))
            if pct > 0 or (val == 0 and total == 0): # Show 0h if total is 0
                return f"{val}h\n({pct:.1f}%)"
            return ""
        return my_autopct

    wedges, texts_pie, autotexts = ax.pie(sizes, explode=explode, labels=None, autopct=make_autopct(sizes),
                                      startangle=90, colors=current_palette,
                                      pctdistance=0.80, 
                                      wedgeprops=dict(width=0.40, edgecolor="white", linewidth=3))
    for autotext_obj in autotexts:
        autotext_obj.set_color("white")
        autotext_obj.set_fontsize(LABEL_FONT_SIZE_MPL)
        autotext_obj.set_fontweight("bold")

    ax.set_title(f"Geplante Zeit: Nächste Woche", fontsize=TITLE_FONT_SIZE_MPL, color=APPLE_TEXT_COLOR_MPL, pad=35, loc="center")
    ax.text(0, 0, f"{used_hours:.0f}h / {total_hours_in_week}h\nBelegt", ha="center", va="center", fontsize=ANNOTATION_FONT_SIZE_MPL, 
            color=USAGE_PALETTE_APPLE_MPL[0] if used_hours > 0 else APPLE_SECONDARY_TEXT_COLOR_MPL, fontweight="medium")
    
    ax.axis("equal")
    plt.tight_layout(pad=1.0, rect=[0, 0.05, 1, 0.95])
    return fig

if __name__ == "__main__":
    # This section is for local testing. 
    # It will use MOCK data if real imports fail, or REAL data if they succeed.
    sample_user_id = "test_user_123"
    
    print(f"Running with USING_REAL_DATA = {USING_REAL_DATA}")

    print("Generating Lernzeiten chart (Seaborn/Matplotlib Apple Style with real data integration attempt)...")
    fig1 = create_donut_chart_lernzeiten_seaborn(sample_user_id)
    if fig1:
        plt.show() 
    else:
        print("Failed to generate Lernzeiten chart.")

    print("Generating Geplante Zeit chart (Seaborn/Matplotlib Apple Style with real data integration attempt)...")
    fig2 = create_donut_chart_next_week_seaborn(sample_user_id)
    if fig2:
        plt.show() 
    else:
        print("Failed to generate Geplante Zeit chart.")
    
    print("Charts generated. In Streamlit, use st.pyplot(fig1) and st.pyplot(fig2).")

