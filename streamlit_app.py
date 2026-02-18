import streamlit as st
import os
from datetime import datetime
from dotenv import load_dotenv
from weather_service import get_current_weather_data
from weather_gov import create_weather_gov_client
from configuration import check_configuration, is_configuration_complete, display_configuration_ui, get_location_coordinates
from current_weather_tab import render_current_weather_tab
from forecast_tab import render_forecast_tab
from main_tab import render_main_tab
from about_tab import render_about_tab

# Load environment variables from .env file
load_dotenv()

st.set_page_config(page_title="Stableman", page_icon="🐴")

@st.cache_data(ttl=60)  # Cache for 1 minute to reduce API calls
def get_weather_data():
    """Fetch current weather data with fallback mechanism (AmbientWeather.net → Weather.gov)"""
    return get_current_weather_data()

@st.cache_data(ttl=1800)  # Cache for 30 minutes for forecast data
def get_forecast_data(latitude: float, longitude: float):
    """Fetch 24-hour forecast from Weather.gov API"""
    weather_gov = create_weather_gov_client()
    forecast_response, error = weather_gov.get_24_hour_forecast(latitude, longitude)
    
    if error:
        return None, None, error
    
    if forecast_response:
        return forecast_response.get('forecast'), forecast_response.get('location'), None
    
    return None, None, "No forecast data available"

st.title("🐴 Stableman")

# Check configuration using the configuration module
missing_config = check_configuration()

if missing_config:
    # Display configuration UI for missing variables
    display_configuration_ui(missing_config)
else:
    # All configuration is complete - show main weather UI
    
    # Get weather data first for use in blanketing instructions and tabs
    weather_data, error = get_weather_data()

    # Create main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🐴 Main", "🌤️ Current Weather", "📊 24-Hour Forecast", "ℹ️ About"])

    with tab1:
        # Main tab with blanketing instructions
        if error:
            st.error(f"Weather data unavailable: {error}")
            st.info("Check your internet connection or API configuration.")
        render_main_tab(weather_data)

    with tab2:
        # Current Weather Conditions Tab
        render_current_weather_tab(weather_data, error)

    with tab3:
        # 24-Hour Forecast Tab
        latitude, longitude = get_location_coordinates()
        render_forecast_tab(latitude, longitude, get_forecast_data)

    with tab4:
        # About Tab
        render_about_tab()
