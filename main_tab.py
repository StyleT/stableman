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