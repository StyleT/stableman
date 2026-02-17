import streamlit as st
import os
from datetime import datetime
import pytz
from dotenv import load_dotenv
from ambient_weather import create_api_client

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
                
                # Convert to a more readable format
                readable_time = utc_time.strftime("%B %d, %Y at %I:%M %p UTC")
                st.caption(f"📅 Last updated: {readable_time}")
                
                # Display time ago
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

st.header("About")
st.write("""
Stableman provides real-time horse blanketing instructions based on current weather conditions.
The app uses AmbientWeather.net API to fetch temperature and humidity data, then provides
appropriate care recommendations for stable hands.
""")

st.divider()

st.header("🔧 Configuration")
st.write("Set these environment variables to enable weather data:")
st.code("""
AMBIENT_API_KEY=your_api_key_here
AMBIENT_APP_KEY=your_application_key_here
AMBIENT_MAC_ADDRESS=your_weather_station_mac_address (optional)
""")

st.info("💡 Get your API keys from [AmbientWeather.net Developer Portal](https://ambientweather.docs.apiary.io/)")
st.write("**Note:** AMBIENT_MAC_ADDRESS is optional but recommended for better performance. The app will help you find it if not provided.")
