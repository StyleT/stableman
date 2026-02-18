"""
Forecast Graph Module for Stableman application.
Contains dual-axis chart creation for temperature and blanketing score visualization.
"""
import streamlit as st
import pandas as pd
import altair as alt
from blanketing_logic import BlanktetingLogic
from dateutil import parser


def render_forecast_graph(forecast_periods, housing_status, user_timezone=None):
    """
    Render a dual-axis forecast graph showing temperature and blanketing score.
    
    Args:
        forecast_periods: List of forecast period dictionaries with 'feels_like' values
        housing_status: Housing status ('OUT' or 'IN') for blanketing score calculation
        user_timezone: User's timezone for proper time display
    """
    if not forecast_periods:
        st.write("No forecast data available")
        return
        
    st.write("**Forecast Overview**")
    
    # Prepare data for visualization
    forecast_data = []
        
    for i, period in enumerate(forecast_periods):
        feels_like = period.get('feels_like', 0)
        score = BlanktetingLogic.temperature_to_blanketing_score(feels_like, housing_status)
        
        # Use the actual forecast period time
        if period.get('time'):
                period_time = parser.parse(period['time'])
                time_label = period_time.strftime("%H:%M")
                # Keep the datetime object for proper chronological ordering
                datetime_obj = period_time
        else:
            # Fallback if no time field
            time_label = f"Hour {i+1}"
            datetime_obj = None
        
        forecast_data.append({
            'Hour': time_label,
            'DateTime': datetime_obj,
            'Feels Like (°F)': feels_like,
            'Blanketing Score': score
        })
    
    if forecast_data:
        df = pd.DataFrame(forecast_data)
        
        # Use datetime for proper chronological ordering, fallback to hour labels
        x_field = 'DateTime:T' if df['DateTime'].notna().all() else 'Hour:O'
        
        # Create dual-axis chart with Altair
        base = alt.Chart(df).encode(
            x=alt.X(x_field, 
                   title=None,
                   axis=alt.Axis(format='%H:%M') if x_field == 'DateTime:T' else None)
        )
        
        # Left Y-axis (Temperature)
        temp_line = base.mark_line(color='#1f77b4', strokeWidth=2).encode(
            y=alt.Y('Feels Like (°F):Q', 
                   axis=alt.Axis(title='Temperature (°F)', titleColor='#1f77b4', labelColor='#1f77b4'))
        )
        
        # Right Y-axis (Blanketing Score)
        score_line = base.mark_line(color='#ff7f0e', strokeWidth=2).encode(
            y=alt.Y('Blanketing Score:Q', 
                   axis=alt.Axis(title='Blanketing Score', titleColor='#ff7f0e', labelColor='#ff7f0e'),
                   scale=alt.Scale(domain=[0, 3]))
        )
        
        # Layer and resolve scales for dual-axis
        chart = alt.layer(temp_line, score_line).resolve_scale(y='independent').properties(
            height=150
        )
        
        st.altair_chart(chart, width='stretch')
