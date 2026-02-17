"""
24-Hour Forecast Tab for Stableman application.
Displays weather forecast with location information and strategic planning.
"""
import streamlit as st
from datetime import datetime
import pytz


def display_forecast_period(periods, start_idx, end_idx):
    """Helper function to display forecast periods"""
    # Get browser timezone for consistent time display
    browser_tz = st.context.timezone
    if browser_tz:
        local_tz = pytz.timezone(browser_tz)
    else:
        local_tz = pytz.UTC  # Fallback to UTC if no timezone detected
        
    for i, period in enumerate(periods[start_idx:end_idx], start_idx):
        try:
            # Parse time
            time_str = period.get('time', '')
            if time_str:
                dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                # Convert to local timezone
                local_dt = dt.astimezone(local_tz)
                time_display = local_dt.strftime("%I:%M %p")
                date_display = local_dt.strftime("%a %m/%d")
            else:
                time_display = f"Hour {i+1}"
                date_display = ""
            
            col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 1.5, 2.5])
            
            with col1:
                st.write(f"**{time_display}**")
                if date_display:
                    st.caption(date_display)
            
            with col2:
                temp = period.get('temperature')
                feels_like = period.get('feels_like')
                if temp is not None:
                    st.metric("🌡️ Temp", f"{temp}°F")
                if feels_like is not None and feels_like != temp:
                    st.caption(f"Feels {feels_like}°F")
            
            with col3:
                humidity = period.get('humidity', 0)
                st.metric("💧 Humidity", f"{humidity}%")
            
            with col4:
                wind = period.get('wind_speed', 'Calm')
                st.metric("💨 Wind", wind)
            
            with col5:
                rain_chance = period.get('precipitation_chance', 0)
                st.metric("🌧️ Rain", f"{rain_chance}%")
            
            with col6:
                forecast = period.get('short_forecast', '')
                st.write(f"*{forecast}*")
            
            if i < len(periods) - 1:  # Don't add divider after last item
                st.divider()
                
        except Exception as e:
            st.error(f"Error displaying period {i}: {e}")


def render_forecast_tab(latitude, longitude, get_forecast_data_func):
    """
    Render the 24-hour forecast tab content.
    
    Args:
        latitude (float): Location latitude
        longitude (float): Location longitude
        get_forecast_data_func (callable): Function to get forecast data
    """
    st.header("📊 24-Hour Weather Forecast")
    st.caption("⏱️ Forecast updated every 30 minutes from Weather.gov")
    
    forecast_data, location_info, forecast_error = get_forecast_data_func(latitude, longitude)

    if forecast_error:
        st.error(f"⚠️ Forecast Error: {forecast_error}")
        st.info("💡 Set LOCATION_LATITUDE and LOCATION_LONGITUDE environment variables for your location")
        
        # Show basic coordinate info even on error
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📍 Latitude", f"{latitude}°")
        with col2:
            st.metric("📍 Longitude", f"{longitude}°")
    else:
        # Display enhanced location information
        if location_info:
            city = location_info.get('city', '')
            state = location_info.get('state', '')
            office = location_info.get('office', '')
            
            # Create location display
            if city and state:
                location_display = f"{city}, {state}"
            elif city:
                location_display = city
            else:
                location_display = f"Coordinates: {latitude}°, {longitude}°"
            
            if office:
                location_display += f" (NWS {office})"
            
            st.subheader(f"📍 {location_display}")
            
            # Show detailed coordinates
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📍 Latitude", f"{latitude}°")
            with col2:
                st.metric("📍 Longitude", f"{longitude}°")
            with col3:
                if location_info.get('timezone'):
                    st.metric("🕐 Timezone", location_info['timezone'])
        else:
            # Fallback to basic coordinate display
            col1, col2 = st.columns(2)
            with col1:
                st.metric("📍 Latitude", f"{latitude}°")
            with col2:
                st.metric("📍 Longitude", f"{longitude}°")
            st.caption(f"📍 Forecast Location: {latitude}°, {longitude}°")

        # Display forecast data if available
        if forecast_data:
            # Display forecast overview
            st.subheader("🌡️ Temperature & Conditions Forecast")
            
            # Create tabs for different time periods
            tab1, tab2, tab3 = st.tabs(["🌅 Next 8 Hours", "🌙 8-16 Hours", "🌅 16-24 Hours"])
            
            with tab1:
                st.caption("🌅 Early periods (next 8 hours)")
                display_forecast_period(forecast_data, 0, 8)
            
            with tab2:
                st.caption("🌙 Mid periods (8-16 hours ahead)")
                display_forecast_period(forecast_data, 8, 16)
            
            with tab3:
                st.caption("🌅 Later periods (16-24 hours ahead)")
                display_forecast_period(forecast_data, 16, 24)
            
            # Forecast-based blanketing recommendations
            st.subheader("🐴 24-Hour Blanketing Strategy")
            
            # Analyze forecast for blanketing recommendations
            min_temp = min([p.get('temperature', 100) for p in forecast_data if p.get('temperature') is not None], default=None)
            max_temp = max([p.get('temperature', -100) for p in forecast_data if p.get('temperature') is not None], default=None)
            max_wind = max([p.get('wind_mph', 0) for p in forecast_data], default=0)
            max_rain_chance = max([p.get('precipitation_chance', 0) for p in forecast_data], default=0)
        
            if min_temp is not None and max_temp is not None:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("🌡️ Low/High", f"{min_temp}°F / {max_temp}°F")
                
                with col2:
                    st.metric("💨 Max Wind", f"{max_wind} mph")
                
                with col3:
                    st.metric("🌧️ Rain Chance", f"{max_rain_chance}%")
                
                # Strategic blanketing recommendation
                if min_temp < 20 or max_wind > 25:
                    st.error("❄️ **Heavy Blanket Strategy Recommended**")
                    st.write("• Expect very cold conditions or high winds")
                    st.write("• Use heavy winter blankets (300g+ fill)")
                    st.write("• Consider waterproof blankets if rain expected")
                elif min_temp < 40 or max_wind > 15:
                    st.warning("🧥 **Medium Blanket Strategy Recommended**")
                    st.write("• Moderate cold expected")
                    st.write("• Use medium weight blankets (150-250g)")
                    st.write("• Monitor for weather changes")
                elif min_temp < 60:
                    st.info("🧸 **Light Blanket Strategy**")
                    st.write("• Mild conditions expected")
                    st.write("• Light blankets for sensitive horses only")
                    st.write("• Easy to adjust as needed")
                else:
                    st.success("☀️ **No Blankets Needed**")
                    st.write("• Warm conditions expected")
                    st.write("• Ensure adequate shade and water")
                
                if max_rain_chance > 50:
                    st.info("🌧️ **Weather Protection Note**: High chance of precipitation - consider waterproof blankets")