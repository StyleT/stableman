import streamlit as st
import requests
import os
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

st.set_page_config(page_title="Stableman", page_icon="🐴")

@st.cache_data(ttl=600)  # Cache for 10 minutes to reduce API calls
def get_weather_data():
    """Fetch current weather data from AmbientWeather.net API with rate limiting"""
    api_key = os.getenv('AMBIENT_API_KEY')
    app_key = os.getenv('AMBIENT_APP_KEY')
    
    if not api_key or not app_key:
        return None, "Weather API keys not configured"
    
    try:
        # Rate limiting: Wait to respect 1 request per second limit
        time.sleep(1.1)  # Slightly over 1 second to be safe
        
        # Get user devices first
        devices_url = "https://rt.ambientweather.net/v1/devices"
        devices_params = {
            'apiKey': api_key,
            'applicationKey': app_key
        }
        
        devices_response = requests.get(devices_url, params=devices_params, timeout=10)
        
        if devices_response.status_code == 429:
            return None, "⏱️ API rate limit exceeded. Please wait a moment and refresh."
        
        devices_response.raise_for_status()
        devices = devices_response.json()
        
        if not devices:
            return None, "No weather stations found"
        
        # Rate limiting: Wait before second API call
        time.sleep(1.1)
        
        # Get data from first device
        device_mac = devices[0]['macAddress']
        data_url = f"https://rt.ambientweather.net/v1/devices/{device_mac}"
        data_params = {
            'apiKey': api_key,
            'applicationKey': app_key,
            'limit': 1
        }
        
        data_response = requests.get(data_url, params=data_params, timeout=10)
        
        if data_response.status_code == 429:
            return None, "⏱️ API rate limit exceeded. Data is cached for 10 minutes to prevent this."
        
        data_response.raise_for_status()
        weather_data = data_response.json()
        
        if weather_data:
            latest_reading = weather_data[0]
            return {
                'temperature': latest_reading.get('tempf'),
                'humidity': latest_reading.get('humidity'),
                'station_name': devices[0].get('info', {}).get('name', 'Weather Station'),
                'last_update': latest_reading.get('dateutc')
            }, None
        else:
            return None, "No weather data available"
            
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            return None, "⏱️ API rate limit exceeded. Weather data is cached to minimize requests."
        else:
            return None, f"API HTTP error: {e.response.status_code}"
    except requests.exceptions.RequestException as e:
        return None, f"API request failed: {str(e)}"
    except Exception as e:
        return None, f"Error fetching weather data: {str(e)}"

st.title("🐴 Stableman")
st.write("Horse blanketing instructions based on current weather conditions")

# Weather Information Section
st.header("🌤️ Current Weather Conditions")
st.caption("⏱️ Data refreshed every 10 minutes to respect API rate limits (1 req/sec)")

weather_data, error = get_weather_data()

if error:
    if "rate limit" in error.lower():
        st.warning(f"⚠️ {error}")
        st.info("💡 Try refreshing in a few seconds. Weather data is automatically cached to prevent rate limiting.")
    else:
        st.error(f"⚠️ {error}")
        st.info("💡 Set AMBIENT_API_KEY and AMBIENT_APP_KEY environment variables to enable weather data")
else:
    if weather_data:
        col1, col2, col3 = st.columns(3)
        
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
            humidity = weather_data['humidity']
            if humidity is not None:
                st.metric(
                    label="💧 Humidity",
                    value=f"{humidity}%"
                )
            else:
                st.metric("💧 Humidity", "--%")
        
        with col3:
            st.metric(
                label="📍 Station",
                value=weather_data['station_name']
            )
        
        # Show last update time if available
        if weather_data.get('last_update'):
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
""")

st.info("💡 Get your API keys from [AmbientWeather.net Developer Portal](https://ambientweather.docs.apiary.io/)")
