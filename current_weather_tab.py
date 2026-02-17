"""
Current Weather Tab for Stableman application.
Displays real-time weather conditions with metrics and timestamps.
"""
import streamlit as st
from datetime import datetime
import pytz


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


def render_current_weather_tab(weather_data, error):
    """
    Render the current weather tab content.
    
    Args:
        weather_data (dict): Weather data from API
        error (str): Error message if any
    """
    st.header("🌤️ Current Weather Conditions")
    st.caption("⏱️ Data refreshed every 1 minute to respect API rate limits (1 req/sec)")

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