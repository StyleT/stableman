"""
Forecast Graph Module for Stableman application.
Contains dual-axis chart creation for temperature and blanketing score visualization.
"""
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
from blanketing_logic import BlanktetingLogic


def render_forecast_graph(forecast_periods, housing_status):
    """
    Render a dual-axis forecast graph showing temperature and blanketing score.
    
    Args:
        forecast_periods: List of forecast period dictionaries with 'feels_like' values
        housing_status: Housing status ('OUT' or 'IN') for blanketing score calculation
    """
    if not forecast_periods:
        st.write("No forecast data available")
        return
        
    st.write("**Forecast Overview**")
    
    # Prepare data for visualization
    forecast_data = []
    current_time = datetime.now()
    for i, period in enumerate(forecast_periods[:12]):  # Show max 12 hours for readability
        feels_like = period.get('feels_like', 0)
        score = BlanktetingLogic.temperature_to_blanketing_score(feels_like, housing_status)
        
        # Calculate the actual time for this forecast period
        forecast_time = current_time + timedelta(hours=i)
        time_label = forecast_time.strftime("%H:%M")
        
        forecast_data.append({
            'Hour': time_label,
            'Feels Like (°F)': feels_like,
            'Blanketing Score': score
        })
    
    if forecast_data:
        df = pd.DataFrame(forecast_data)
        
        # Create dual-axis chart with Altair
        base = alt.Chart(df).encode(x=alt.X('Hour:O', title=None))  # Use ordinal, not temporal
        
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
        
        st.altair_chart(chart, use_container_width=True)
        st.caption(f"{len(forecast_periods)} hours available • {len(forecast_data)} shown")
