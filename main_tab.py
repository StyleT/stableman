"""
Main Tab for Stableman application.
Contains blanketing instructions based on current weather and app information.
"""
import streamlit as st


def render_main_tab(weather_data):
    """
    Render the main tab content with blanketing instructions and about section.
    
    Args:
        weather_data (dict): Weather data from API for blanketing logic
    """
    # Blanketing Instructions (based on current weather data)
    st.header("🐴 Blanketing Instructions")
    st.write("""
    Based on current weather conditions, here are the recommended blanketing instructions for stable hands:
    """)

    # Simple blanketing logic based on temperature
    if weather_data and weather_data['temperature'] is not None:
        temp = weather_data['temperature']
        
        if temp < 20:
            st.error("🥶 **Heavy Blanket Required** - Temperature below 20°F")
            st.write("• Use heavy winter blankets (300g+ fill)")
            st.write("• Check horses hourly for signs of cold stress")
            st.write("• Ensure adequate shelter and windbreak")
        elif temp < 40:
            st.warning("🧥 **Medium Blanket Recommended** - Temperature 20-40°F")
            st.write("• Use medium weight blankets (150-250g fill)")
            st.write("• Monitor horses for comfort")
            st.write("• Check blanket fit and security")
        elif temp < 60:
            st.info("🧸 **Light Blanket Optional** - Temperature 40-60°F")
            st.write("• Light blankets may be used for sensitive horses")
            st.write("• Consider horse's body condition and coat")
            st.write("• Monitor for overheating")
        else:
            st.success("☀️ **No Blanket Needed** - Temperature above 60°F")
            st.write("• Horses should be comfortable without blankets")
            st.write("• Ensure adequate shade and water")
            st.write("• Remove any existing blankets")
    else:
        st.info("Connect weather data to see personalized blanketing recommendations")

    st.divider()

    # About section
    st.header("About")
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
        st.write("• AmbientWeather.net API")
        st.write("• 1-minute cache refresh")
        st.write("• Direct weather station access")
        st.write("• Temperature, humidity, feels-like")
    
    with col2:
        st.write("**24-Hour Forecast**")
        st.write("• Weather.gov API")
        st.write("• 30-minute cache refresh")
        st.write("• NWS grid point resolution")
        st.write("• Hourly conditions & planning")