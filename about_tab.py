"""
About Tab for Stableman application.
Contains app information, features, configuration details, and data sources.
"""
import streamlit as st


def render_about_tab():
    """
    Render the about tab content with app information and technical details.
    """
    st.header("About Stableman")
    st.write("""
    Stableman provides real-time horse blanketing instructions based on current weather conditions and 24-hour forecasts.
    The app uses AmbientWeather.net API for current conditions and Weather.gov for detailed forecasts, then provides
    comprehensive care recommendations and strategic planning for stable hands.
    """)
    
    st.subheader("🌟 Features")
    st.write("""
    - **Real-time Weather Data**: Live conditions from your weather station
    - **24-Hour Forecasts**: Detailed planning with Weather.gov integration
    - **Smart Blanketing Logic**: Temperature-based recommendations (20°F/40°F/60°F thresholds)
    - **Location-Aware**: Accurate forecasts for your stable's coordinates
    - **Rate-Limited**: Respectful API usage with intelligent caching
    """)
    
    st.subheader("🔧 Configuration")
    st.write("""
    The app requires environment variables for API access and location:
    - **AmbientWeather.net API Keys**: For real-time weather station data
    - **Weather Station MAC Address**: For direct device access
    - **Location Coordinates**: For accurate forecast data from Weather.gov
    """)
    
    st.subheader("📊 Data Sources")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Current Weather**")
        st.write("• 🏡 AmbientWeather.net API (Primary)")
        st.write("• 🏛️ Weather.gov API (Fallback)")
        st.write("• 1-minute cache refresh")
        st.write("• Automatic fallback if station unavailable")
        st.write("• Temperature, humidity, feels-like")
    
    with col2:
        st.write("**24-Hour Forecast**")
        st.write("• Weather.gov API")
        st.write("• 30-minute cache refresh")
        st.write("• NWS grid point resolution")
        st.write("• Hourly conditions & planning")

    st.subheader("️ Blanketing Guidelines")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Temperature Thresholds**")
        st.write("• Below 20°F: Heavy blankets required")
        st.write("• 20-40°F: Medium blankets recommended") 
        st.write("• 40-60°F: Light blankets optional")
        st.write("• Above 60°F: No blankets needed")
    
    with col2:
        st.write("**Additional Factors**")
        st.write("• Wind speed considerations")
        st.write("• Precipitation forecasts")
        st.write("• Horse body condition")
        st.write("• Shelter availability")

    st.subheader("🔗 External Services")
    st.write("""
    - **[AmbientWeather.net](https://ambientweather.net)**: Personal weather station data
    - **[Weather.gov API](https://weather.gov/documentation/services-web-api)**: National Weather Service forecasts
    - **[Streamlit](https://streamlit.io)**: Web application framework
    """)