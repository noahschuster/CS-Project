import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from datetime import datetime, timedelta
from learning_suggestions import get_study_tasks
from database_manager import get_calendar_events

# Set Apple-inspired minimalist style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'font.family': 'SF Pro Display, Arial, sans-serif',
    'font.size': 12,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'axes.titleweight': 'bold',
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.edgecolor': '#EEEEEE',
    'axes.linewidth': 0.5,
    'figure.facecolor': 'white',
    'grid.color': '#F5F5F7',
    'grid.linewidth': 0.5
})

# Create pie chart for learning time by subject with Apple-inspired design
def create_pie_chart_learning_time_by_subject(user_id):
    """Creates a clean, Apple-style pie chart showing time spent per subject."""
    try:
        # Get study tasks data
        study_tasks = get_study_tasks(user_id)
        
        # Convert to pandas DataFrame for better processing
        df = pd.DataFrame(study_tasks)
        
        # Check if the required columns exist
        required_columns = ['start_time', 'end_time', 'course_title']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.warning(f"Missing columns in data: {', '.join(missing_columns)}. Using sample data instead.")
            # Create sample data
            sample_data = {
                'course_title': ['Mathematics', 'Computer Science', 'Physics', 'Biology'],
                'duration_hours': [8.5, 12.0, 6.5, 4.0]
            }
            subject_times = pd.DataFrame(sample_data)
        else:
            # Process time data
            df['start_time'] = pd.to_datetime(df['start_time'], format="%H:%M")
            df['end_time'] = pd.to_datetime(df['end_time'], format="%H:%M")
            df['duration_hours'] = (df['end_time'] - df['start_time']).dt.total_seconds() / 3600
            
            # Aggregate by subject
            subject_times = df.groupby('course_title')['duration_hours'].sum().reset_index()
        
        # Create Apple-style colors
        apple_colors = ['#5AC8FA', '#AF52DE', '#FF9500', '#FF2D55', '#34C759', '#007AFF']
        
        # Create interactive plotly pie chart with Apple aesthetic
        fig = go.Figure(data=[go.Pie(
            labels=subject_times['course_title'],
            values=subject_times['duration_hours'],
            hole=0.5,
            textinfo='percent',
            textfont_size=14,
            marker=dict(
                colors=apple_colors[:len(subject_times)],
                line=dict(color='#FFFFFF', width=2)
            ),
            insidetextorientation='radial'
        )])
        
        fig.update_layout(
            title={
                'text': 'Learning Time by Subject',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=20, family="SF Pro Display, Arial", color="#1D1D1F")
            },
            font=dict(family="SF Pro Display, Arial", size=14, color="#1D1D1F"),
            legend={
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': -0.2,
                'xanchor': 'center',
                'x': 0.5
            },
            paper_bgcolor='white',
            plot_bgcolor='white',
            height=500,
            width=700,
            margin=dict(t=80, b=80, l=40, r=40),
            showlegend=True
        )
        
        # Display interactive chart in Streamlit
        st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error creating learning time chart: {e}")
        st.info("Displaying a placeholder chart with sample data instead.")
        
        # Create sample data
        sample_data = {
            'course_title': ['Mathematics', 'Computer Science', 'Physics', 'Biology'],
            'duration_hours': [8.5, 12.0, 6.5, 4.0]
        }
        subject_times = pd.DataFrame(sample_data)
        
        apple_colors = ['#5AC8FA', '#AF52DE', '#FF9500', '#FF2D55']
        
        # Create a fallback chart with sample data
        fig = go.Figure(data=[go.Pie(
            labels=subject_times['course_title'],
            values=subject_times['duration_hours'],
            hole=0.5,
            textinfo='percent',
            textfont_size=14,
            marker=dict(
                colors=apple_colors,
                line=dict(color='#FFFFFF', width=2)
            )
        )])
        
        fig.update_layout(
            title="Learning Time by Subject (Sample Data)",
            font=dict(family="SF Pro Display, Arial", size=14, color="#1D1D1F"),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            height=500,
            width=700
        )
        
        st.plotly_chart(fig, use_container_width=True)

# Create pie chart for next week time usage with Apple-inspired design
def create_pie_chart_next_week_usage(user_id):
    """Creates Apple-style chart for time allocation."""
    try:
        # Get calendar events
        events = get_calendar_events(user_id)
        
        # Convert to pandas DataFrame
        df = pd.DataFrame(events)
        
        # Check if the required columns exist
        if 'date' not in df.columns:
            st.warning("Missing 'date' column in calendar data. Using sample data instead.")
            # Create fallback data
            total_hours = 40
            used_hours = 3
            free_hours = 37
        else:
            # Calculate date range for next week
            today = datetime.now()
            next_week = today + timedelta(days=7)
            
            # Process dates
            df['date'] = pd.to_datetime(df['date'], format="%Y-%m-%d")
            
            # Filter events for next week
            next_week_events = df[(df['date'] >= today) & (df['date'] <= next_week)]
            
            # Total hours in a week (assuming 40-hour work week)
            total_hours = 40
            used_hours = next_week_events.shape[0]  # Assuming 1 hour per event
            free_hours = total_hours - used_hours
        
        # Apple-style colors
        colors = ['#FF9500', '#34C759']
        
        # Create interactive donut chart with Apple design
        fig = go.Figure(data=[go.Pie(
            labels=['Allocated Time', 'Free Time'],
            values=[used_hours, free_hours],
            hole=0.65,
            textinfo='percent',
            textfont_size=14,
            marker=dict(
                colors=colors,
                line=dict(color='#FFFFFF', width=2)
            )
        )])
        
        # Add center text showing available hours
        fig.update_layout(
            annotations=[dict(
                text=f"{free_hours}h<br>Available", 
                x=0.5, 
                y=0.5, 
                font_size=18, 
                font_family="SF Pro Display, Arial", 
                font_color="#1D1D1F",
                showarrow=False
            )]
        )
        
        fig.update_layout(
            title={
                'text': 'Next Week Time Allocation',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=20, family="SF Pro Display, Arial", color="#1D1D1F")
            },
            font=dict(family="SF Pro Display, Arial", size=14, color="#1D1D1F"),
            legend={
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': -0.2,
                'xanchor': 'center',
                'x': 0.5
            },
            paper_bgcolor='white',
            plot_bgcolor='white',
            height=500,
            width=700,
            margin=dict(t=80, b=80, l=40, r=40),
            showlegend=True
        )
        
        # Display the interactive chart in Streamlit
        st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error creating time allocation chart: {e}")
        st.info("Displaying a placeholder chart with sample data instead.")
        
        # Create sample data for fallback
        total_hours = 40
        used_hours = 3
        free_hours = 37
        colors = ['#FF9500', '#34C759']
        
        # Create a fallback chart with sample data
        fig = go.Figure(data=[go.Pie(
            labels=['Allocated Time', 'Free Time'],
            values=[used_hours, free_hours],
            hole=0.65,
            textinfo='percent',
            textfont_size=14,
            marker=dict(
                colors=colors,
                line=dict(color='#FFFFFF', width=2)
            )
        )])
        
        fig.update_layout(
            title="Next Week Time Allocation (Sample Data)",
            annotations=[dict(text=f"{free_hours}h<br>Available", x=0.5, y=0.5, font_size=18, showarrow=False)],
            font=dict(family="SF Pro Display, Arial", size=14),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            height=500,
            width=700
        )
        
        st.plotly_chart(fig, use_container_width=True)

# Main dashboard section
def display_learning_dashboard(user_id):
    st.set_page_config(layout="wide", page_title="Learning Dashboard")
    
    # Apply custom CSS for Apple-like styling
    st.markdown("""
        <style>
        .main {
            background-color: #FFFFFF;
            padding: 2rem;
        }
        h1, h2, h3 {
            font-family: 'SF Pro Display', 'Helvetica Neue', sans-serif;
            font-weight: 600;
            color: #1D1D1F;
        }
        h1 {
            font-size: 32px;
            margin-bottom: 30px;
        }
        h2 {
            font-size: 24px;
            margin-top: 40px;
            margin-bottom: 20px;
        }
        .stPlotlyChart {
            background-color: #FFFFFF;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            padding: 10px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("Learning Dashboard")
    
    # Add some spacing
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
    st.header("Learning Time Distribution")
    create_pie_chart_learning_time_by_subject(user_id)
    
    # Add some spacing
    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
    
    st.header("Next Week Time Allocation")
    create_pie_chart_next_week_usage(user_id)
        
if __name__ == "__main__":
    # For testing purposes
    user_id = "test_user_123"
    display_learning_dashboard(user_id)