import streamlit as st
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv
from ambient_weather import create_api_client
from weather_gov import create_weather_gov_client

# Load environment variables from .env file
load_dotenv()

st.set_page_config(page_title="Stableman", page_icon="🐴")

@st.cache_data(ttl=60)  # Cache for 1 minute to reduce API calls
def get_weather_data():
    """Fetch current weather data from AmbientWeather.net API"""
    api_client, error = create_api_client()
    
    if error:
        return None, error
    
    weather_data, error = api_client.get_latest_weather_data()
    
    if error:
        return None, error
    
    return weather_data, None

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

def handle_device_selection_error(error_msg):
    """Handle device selection errors and display appropriate UI"""
    if error_msg.startswith("DEVICE_SELECTION_SINGLE|"):
        parts = error_msg.split("|")
        mac_address = parts[1]
        device_name = parts[2]
        
        st.warning("🔧 **Device Configuration Needed**")
        st.write(f"Found one weather station: **{device_name}**")
        st.write(f"MAC Address: `{mac_address}`")
        
        st.info("💡 **To improve performance, add this to your .env file:**")
        st.code(f"AMBIENT_MAC_ADDRESS={mac_address}")
        st.write("This will avoid listing devices on each request and speed up the app.")
        
        return None
        
    elif error_msg.startswith("DEVICE_SELECTION_MULTIPLE|"):
        device_list_str = error_msg.split("|", 1)[1]
        devices = []
        
        for device_str in device_list_str.split(";"):
            if "|" in device_str:
                name, mac = device_str.split("|", 1)
                devices.append({"name": name, "mac": mac})
        
        st.warning("🔧 **Multiple Weather Stations Found**")
        st.write("Please select which weather station to use:")
        
        for i, device in enumerate(devices, 1):
            st.write(f"**{i}. {device['name']}**")
            st.write(f"   MAC Address: `{device['mac']}`")
        
        st.info("💡 **To configure your preferred station, add this to your .env file:**")
        st.code("AMBIENT_MAC_ADDRESS=<mac_address_from_above>")
        st.write("Replace `<mac_address_from_above>` with the MAC address of your preferred station.")
        
        return None
        
    return error_msg

st.title("🐴 Stableman")
st.write("Horse blanketing instructions based on current weather conditions")

# Weather Information Section
st.header("🌤️ Current Weather Conditions")
st.caption("⏱️ Data refreshed every 1 minute to respect API rate limits (1 req/sec)")

weather_data, error = get_weather_data()

if error:
    # Check if this is a device selection error
    if error.startswith("DEVICE_SELECTION_"):
        handle_device_selection_error(error)
    else:
        # Regular error handling
        if "rate limit" in error.lower():
            st.warning(f"⚠️ {error}")
            st.info("💡 Try refreshing in a few seconds. Weather data is automatically cached to prevent rate limiting.")
        else:
            st.error(f"⚠️ {error}")
            st.info("💡 Set AMBIENT_API_KEY and AMBIENT_APP_KEY environment variables to enable weather data")
else:
    if weather_data:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            temp = weather_data['temperature']
            if temp is not None:
                st.metric(
                    label="🌡️ Temperature",
                    value=f"{temp}°F"
                )
            else:
                st.metric("🌡️ Temperature", "--°F")
        
        with col2:
            feels_like = weather_data.get('feels_like')
            if feels_like is not None:
                st.metric(
                    label="🌡️ Feels Like",
                    value=f"{feels_like}°F"
                )
            else:
                st.metric("🌡️ Feels Like", "--°F")
        
        with col3:
            humidity = weather_data['humidity']
            if humidity is not None:
                st.metric(
                    label="💧 Humidity",
                    value=f"{humidity}%"
                )
            else:
                st.metric("💧 Humidity", "--%")
        
        with col4:
            st.metric(
                label="📍 Station",
                value=weather_data['station_name']
            )
        
        # Show last update time if available
        if weather_data.get('last_update'):
            try:
                last_update = weather_data['last_update']
                
                # Get browser timezone
                browser_tz = st.context.timezone
                if browser_tz:
                    local_tz = pytz.timezone(browser_tz)
                else:
                    local_tz = pytz.UTC  # Fallback to UTC if no timezone detected
                
                # Handle different timestamp formats
                if isinstance(last_update, (int, float)) or (isinstance(last_update, str) and last_update.isdigit()):
                    # Unix timestamp in milliseconds
                    timestamp_ms = int(last_update)
                    utc_time = datetime.fromtimestamp(timestamp_ms / 1000, tz=pytz.UTC)
                else:
                    # ISO format string (fallback)
                    utc_time = datetime.fromisoformat(str(last_update).replace('Z', '+00:00'))
                    if utc_time.tzinfo is None:
                        utc_time = utc_time.replace(tzinfo=pytz.UTC)
                
                # Convert to local timezone
                local_time = utc_time.astimezone(local_tz)
                
                # Convert to a more readable format in local time
                tz_name = browser_tz or "UTC"
                readable_time = local_time.strftime(f"%B %d, %Y at %I:%M %p {tz_name}")
                st.caption(f"📅 Last updated: {readable_time}")
                
                # Display time ago (using UTC for calculation)
                now_utc = datetime.now(pytz.UTC)
                time_diff = now_utc - utc_time
                
                if time_diff.total_seconds() < 60:
                    time_ago = f"{int(time_diff.total_seconds())} seconds ago"
                elif time_diff.total_seconds() < 3600:
                    time_ago = f"{int(time_diff.total_seconds() / 60)} minutes ago"
                elif time_diff.total_seconds() < 86400:
                    time_ago = f"{int(time_diff.total_seconds() / 3600)} hours ago"
                else:
                    time_ago = f"{int(time_diff.total_seconds() / 86400)} days ago"
                
                st.caption(f"⏰ {time_ago}")
                
            except (ValueError, AttributeError, TypeError) as e:
                # Fallback to raw timestamp if parsing fails
                st.caption(f"📅 Last updated: {weather_data['last_update']} UTC")
    else:
        st.warning("No weather data available")

st.divider()

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

# 24-Hour Forecast Section
st.header("📊 24-Hour Weather Forecast")
st.caption("⏱️ Forecast updated every 30 minutes from Weather.gov")

# Get coordinates from environment variables
latitude = float(os.getenv('LOCATION_LATITUDE', '40.7128'))  # Default to NYC
longitude = float(os.getenv('LOCATION_LONGITUDE', '-74.0060'))

forecast_data, location_info, forecast_error = get_forecast_data(latitude, longitude)

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
                    
                    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 3])
                    
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
                        rain_chance = period.get('precipitation_chance', 0)
                        st.metric("💨 Wind", wind)
                        if rain_chance > 0:
                            st.caption(f"🌧️ {rain_chance}% rain")
                    
                    with col5:
                        forecast = period.get('short_forecast', '')
                        st.write(f"*{forecast}*")
                    
                    if i < len(periods) - 1:  # Don't add divider after last item
                        st.divider()
                        
                except Exception as e:
                    st.error(f"Error displaying period {i}: {e}")
        
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

st.divider()

st.header("About")
st.write("""
Stableman provides real-time horse blanketing instructions based on current weather conditions and 24-hour forecasts.
The app uses AmbientWeather.net API for current conditions and Weather.gov for detailed forecasts, then provides
comprehensive care recommendations and strategic planning for stable hands.
""")

st.divider()

st.header("🔧 Configuration")
st.write("Set these environment variables to enable weather data:")
st.code("""
AMBIENT_API_KEY=your_api_key_here
AMBIENT_APP_KEY=your_application_key_here
AMBIENT_MAC_ADDRESS=your_weather_station_mac_address (optional)
LOCATION_LATITUDE=40.7128 (optional, defaults to NYC)
LOCATION_LONGITUDE=-74.0060 (optional, defaults to NYC)
""")

st.info("💡 Get your API keys from [AmbientWeather.net Developer Portal](https://ambientweather.docs.apiary.io/)")
st.write("**Note:** AMBIENT_MAC_ADDRESS is optional but recommended for better performance. The app will help you find it if not provided.")
st.write("**Location:** Set LOCATION_LATITUDE and LOCATION_LONGITUDE for accurate forecasts at your stable's location.")
