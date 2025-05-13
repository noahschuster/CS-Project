import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta

# --- Mock data functions for testing purposes ---
def get_study_tasks(user_id):
    return [
        {"course_title": "Mathematics", "start_time": "09:00", "end_time": "11:00"}, # 2h
        {"course_title": "Physics", "start_time": "13:00", "end_time": "14:30"},     # 1.5h
        {"course_title": "History", "start_time": "15:00", "end_time": "16:00"},     # 1h
        {"course_title": "Mathematics", "start_time": "10:00", "end_time": "12:00"}, # 2h (total Math: 4h)
        {"course_title": "Chemistry", "start_time": "08:00", "end_time": "09:30"},   # 1.5h
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

# Apple-inspired Aesthetics for Matplotlib
APPLE_FONT_FAMILY_MPL = "Arial" 
APPLE_TEXT_COLOR_MPL = "#1D1D1F" 
APPLE_SECONDARY_TEXT_COLOR_MPL = "#6E6E73" 

SUBJECT_PALETTE_APPLE_MPL = ["#0A84FF", "#30D158", "#FF9F0A", "#BF5AF2", "#64D2FF", "#FF453A", "#FFD60A"]
USAGE_PALETTE_APPLE_MPL = ["#FF9F0A", "#0A84FF"]

# Increased font sizes as per user request
TITLE_FONT_SIZE_MPL = 18
LABEL_FONT_SIZE_MPL = 11 # For percentages on slices and legend labels
SLICE_LABEL_FONT_SIZE_MPL = 11 # For labels if drawn outside by matplotlib (not currently used this way)
ANNOTATION_FONT_SIZE_MPL = 16 # For center annotation
FIG_DPI = 150

def create_donut_chart_lernzeiten_seaborn(user_id):
    study_tasks = get_study_tasks(user_id)
    plt.style.use("seaborn-v0_8-whitegrid") 
    plt.rcParams["font.family"] = APPLE_FONT_FAMILY_MPL
    plt.rcParams["text.color"] = APPLE_TEXT_COLOR_MPL
    plt.rcParams["axes.labelcolor"] = APPLE_TEXT_COLOR_MPL
    plt.rcParams["xtick.color"] = APPLE_SECONDARY_TEXT_COLOR_MPL
    plt.rcParams["ytick.color"] = APPLE_SECONDARY_TEXT_COLOR_MPL

    fig, ax = plt.subplots(figsize=(7, 5.25), dpi=FIG_DPI) # Slightly increased figsize for larger fonts
    fig.patch.set_alpha(0) 
    ax.patch.set_alpha(0)  

    if not study_tasks:
        ax.text(0.5, 0.5, "Keine Lerndaten verfügbar.", ha="center", va="center", fontsize=ANNOTATION_FONT_SIZE_MPL, color=APPLE_SECONDARY_TEXT_COLOR_MPL)
        ax.set_title("Lernzeiten nach Thema", fontsize=TITLE_FONT_SIZE_MPL, color=APPLE_TEXT_COLOR_MPL, pad=20)
        ax.axis("off")
        plt.tight_layout()
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
        ax.text(0.5, 0.5, "Keine gültigen Lerndaten.", ha="center", va="center", fontsize=ANNOTATION_FONT_SIZE_MPL, color=APPLE_SECONDARY_TEXT_COLOR_MPL)
        ax.set_title("Lernzeiten nach Thema", fontsize=TITLE_FONT_SIZE_MPL, color=APPLE_TEXT_COLOR_MPL, pad=20)
        ax.axis("off")
        plt.tight_layout()
        return fig

    labels = list(subject_times.keys())
    sizes = list(subject_times.values())
    
    explode = [0.03] * len(labels)

    wedges, texts, autotexts = ax.pie(sizes, explode=explode, labels=None, autopct="%1.1f%%", 
                                      startangle=90, colors=SUBJECT_PALETTE_APPLE_MPL,
                                      pctdistance=0.85, wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2.5)) # Slightly wider donut, thicker lines

    for autotext_obj in autotexts: # Percentages
        autotext_obj.set_color("white")
        autotext_obj.set_fontsize(LABEL_FONT_SIZE_MPL)
        autotext_obj.set_fontweight("bold")

    ax.set_title("Lernzeiten nach Thema", fontsize=TITLE_FONT_SIZE_MPL, color=APPLE_TEXT_COLOR_MPL, pad=30) # Increased pad for title
    
    ax.text(0, 0, f"Total\n{total_duration_all_subjects:.1f} Std.", ha="center", va="center", fontsize=ANNOTATION_FONT_SIZE_MPL, color=APPLE_TEXT_COLOR_MPL, fontweight="medium")
    
    # Legend outside, Apple style (simple, clean)
    # For better fitting with potentially larger fonts, adjust bbox_to_anchor or use a different loc if needed.
    ax.legend(wedges, labels, title=None, loc="center left", bbox_to_anchor=(1.0, 0.5), 
              fontsize=LABEL_FONT_SIZE_MPL, frameon=False, labelcolor=APPLE_TEXT_COLOR_MPL)

    ax.axis("equal") 
    plt.tight_layout(rect=[0, 0, 0.85, 1]) # Adjust rect to make space for legend on the right
    return fig

def create_donut_chart_next_week_seaborn(user_id):
    events = get_calendar_events(user_id)
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams["font.family"] = APPLE_FONT_FAMILY_MPL
    plt.rcParams["text.color"] = APPLE_TEXT_COLOR_MPL
    plt.rcParams["axes.labelcolor"] = APPLE_TEXT_COLOR_MPL
    plt.rcParams["xtick.color"] = APPLE_SECONDARY_TEXT_COLOR_MPL
    plt.rcParams["ytick.color"] = APPLE_SECONDARY_TEXT_COLOR_MPL

    fig, ax = plt.subplots(figsize=(7, 5.25), dpi=FIG_DPI)
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)

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
                    used_hours += 3 
            except (ValueError, KeyError):
                continue

    used_hours = min(used_hours, total_hours_in_week)
    free_hours = total_hours_in_week - used_hours
    
    chart_labels = ["Belegte Zeit", "Freie Zeit"]
    sizes = [used_hours, free_hours]
    current_palette = [USAGE_PALETTE_APPLE_MPL[0] if used_hours > 0 else "#E9E9EA", # Lighter grey for unused
                       USAGE_PALETTE_APPLE_MPL[1] if free_hours > 0 else "#E9E9EA"]
    explode = [0.03, 0.03]

    # Custom autopct function for better label formatting
    def make_autopct(values):
        def my_autopct(pct):
            total = sum(values)
            val = int(round(pct*total/100.0))
            if pct > 0:
                return f"{val}h\n({pct:.1f}%)"
            return ""
        return my_autopct

    wedges, texts_pie, autotexts = ax.pie(sizes, explode=explode, labels=None, autopct=make_autopct(sizes),
                                      startangle=90, colors=current_palette,
                                      pctdistance=0.80, 
                                      wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2.5))
    for autotext_obj in autotexts:
        autotext_obj.set_color("white")
        autotext_obj.set_fontsize(LABEL_FONT_SIZE_MPL)
        autotext_obj.set_fontweight("bold")

    ax.set_title(f"Geplante Zeit: Nächste Woche", fontsize=TITLE_FONT_SIZE_MPL, color=APPLE_TEXT_COLOR_MPL, pad=30)
    ax.text(0, 0, f"{used_hours:.0f}h / {total_hours_in_week}h\nBelegt", ha="center", va="center", fontsize=ANNOTATION_FONT_SIZE_MPL, 
            color=USAGE_PALETTE_APPLE_MPL[0] if used_hours > 0 else APPLE_SECONDARY_TEXT_COLOR_MPL, fontweight="medium")
    
    # For only two items, legend might be redundant if labels are clear on slices.
    # If needed, can add a simple legend similarly to the first chart.
    # ax.legend(wedges, chart_labels, title=None, loc="center left", bbox_to_anchor=(1.0, 0.5), fontsize=LABEL_FONT_SIZE_MPL, frameon=False, labelcolor=APPLE_TEXT_COLOR_MPL)

    ax.axis("equal")
    plt.tight_layout(rect=[0, 0, 0.9, 1]) # Adjust rect to ensure title and chart fit well
    return fig

if __name__ == "__main__":
    sample_user_id = "test_user_123"
    
    print("Generating Lernzeiten chart (Seaborn/Matplotlib Apple Style with larger fonts)...")
    fig1 = create_donut_chart_lernzeiten_seaborn(sample_user_id)
    plt.show() 

    print("Generating Geplante Zeit chart (Seaborn/Matplotlib Apple Style with larger fonts)...")
    fig2 = create_donut_chart_next_week_seaborn(sample_user_id)
    plt.show() 
    print("Charts generated. In Streamlit, use st.pyplot(fig1) and st.pyplot(fig2).")

