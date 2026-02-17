"""
Main Tab for Stableman application.
Contains blanketing instructions based on current weather and app information.
"""
import streamlit as st
from datetime import datetime, timedelta
from dateutil import parser
import pytz
from weather_gov import create_weather_gov_client
from configuration import get_location_coordinates


def get_next_phase_forecast(current_phase, latitude, longitude):
    """
    Get forecast data until the next blanketing phase.
    
    Args:
        current_phase: Current phase name ('Morning', 'Day', 'Evening')
        latitude: Location latitude
        longitude: Location longitude
    
    Returns:
        tuple: (min_feels_like, forecast_periods, next_phase_time)
    """
    try:
        weather_client = create_weather_gov_client()
        forecast_data, error = weather_client.get_24_hour_forecast(latitude, longitude)
        
        if error or not forecast_data:
            return None, [], None
        
        forecast_periods = forecast_data.get('forecast', [])
        now = datetime.now()
        
        # Determine next phase timing
        if current_phase == 'Morning':
            # Next phase is Day at 11:00 AM
            next_phase_time = now.replace(hour=11, minute=0, second=0, microsecond=0)
            if now.hour >= 11:
                next_phase_time += timedelta(days=1)  # Next day if already past 11 AM
        elif current_phase == 'Day':
            # Next phase is Night at 3:50 PM
            next_phase_time = now.replace(hour=15, minute=50, second=0, microsecond=0)
            if now.hour >= 15 and now.minute >= 50:
                next_phase_time += timedelta(days=1)  # Next day if already past 3:50 PM
        else:  # Night
            # Night phase extends until morning phase ends at 11:00 AM next day
            next_phase_time = now.replace(hour=11, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        # Filter forecast periods until next phase
        relevant_periods = []
        min_feels_like = float('inf')
        
        for period in forecast_periods:
            if not period.get('time'):
                continue
                
            try:
                period_time = parser.parse(period['time'])
                # Convert to naive datetime for comparison
                if period_time.tzinfo:
                    period_time = period_time.replace(tzinfo=None)
                
                if period_time <= next_phase_time:
                    relevant_periods.append(period)
                    if period.get('feels_like') is not None:
                        min_feels_like = min(min_feels_like, period['feels_like'])
            except:
                continue
        
        return min_feels_like if min_feels_like != float('inf') else None, relevant_periods, next_phase_time
        
    except Exception as e:
        st.error(f"Error fetching forecast data: {e}")
        return None, [], None


def determine_housing_status(weather_data, forecast_periods):
    """
    Automatically determine housing status based on weather conditions.
    
    Rules:
    - If chance of rain > 10% - horses stay IN for duration + 12h if rained > 0.1in
    - Equine heat index = Temp °F + % Relative Humidity
      - > 150 in consistently cloudy weather - horses stay IN for the day
      - > 120 in sunny weather - horses stay IN for the day
    - Otherwise - horses are OUT
    
    Args:
        weather_data: Current weather data
        forecast_periods: Forecast data periods
    
    Returns:
        tuple: (housing_status, reason, user_selectable)
    """
    if not weather_data:
        return "Horses OUT", "No weather data available", True
    
    temp = weather_data.get('temperature')
    humidity = weather_data.get('humidity')
    
    # Calculate equine heat index if we have both temperature and humidity
    if temp is not None and humidity is not None and temp > 75:
        equine_heat_index = temp + humidity
        
        # Check for high heat conditions
        # Note: We'll need to determine if weather is sunny/cloudy from forecast data
        # For now, assume sunny unless we can detect cloudy conditions
        is_cloudy = False
        
        # Check forecast for cloudy conditions
        if forecast_periods:
            cloudy_periods = 0
            total_periods = 0
            for period in forecast_periods[:4]:  # Check next 4 periods
                forecast = period.get('short_forecast', '').lower()
                if 'cloud' in forecast or 'overcast' in forecast or 'partly' in forecast:
                    cloudy_periods += 1
                total_periods += 1
            
            if total_periods > 0 and cloudy_periods / total_periods > 0.5:
                is_cloudy = True
        
        # Apply heat index rules
        if is_cloudy and equine_heat_index > 150:
            return "Horses IN", f"High heat index ({equine_heat_index:.0f}) in cloudy weather", False
        elif not is_cloudy and equine_heat_index > 120:
            return "Horses IN", f"High heat index ({equine_heat_index:.0f}) in sunny weather", False
    
    # Check for rain conditions in forecast
    if forecast_periods:
        for period in forecast_periods:
            rain_chance = period.get('precipitation_chance', 0)
            if rain_chance > 10:
                return "Horses IN", f"Rain expected ({rain_chance}% chance)", False
    
    # Default to horses OUT with user choice
    return "Horses OUT", "Good conditions for outdoor housing", True


def get_current_phase():
    """
    Determine the current blanketing phase based on time of day.
    
    Returns:
        tuple: (phase_name, phase_emoji, phase_description)
    """
    now = datetime.now()
    current_hour = now.hour
    current_minute = now.minute
    
    # Convert current time to minutes since midnight for easier comparison
    current_time_minutes = current_hour * 60 + current_minute
    
    # Phase boundaries in minutes since midnight
    day_start = 11 * 60  # 11:00 AM
    evening_start = 15 * 60 + 50  # 3:50 PM
    
    if current_time_minutes < day_start:
        return "Morning", "🌅", "Early care period"
    elif current_time_minutes < evening_start:
        return "Day", "☀️", "Midday monitoring period"
    else:
        return "Night", "🌙", "Night care period"


def render_main_tab(weather_data):
    """
    Render the main tab content with blanketing instructions and about section.
    
    Args:
        weather_data (dict): Weather data from API for blanketing logic
    """    # Display current blanketing phase
    phase_name, phase_emoji, phase_description = get_current_phase()
    current_time = datetime.now().strftime("%I:%M %p")
    
    st.info(f"{phase_emoji} **{phase_name}** ({phase_description}) - {current_time}")
    
    # Blanketing Instructions
    st.header("🐴 Blanketing Instructions")
    st.write(f"""
    Based on current weather conditions and the **{phase_name}** care phase, here are the recommended blanketing instructions for stable hands:
    
    **Daily Care Schedule:**
    - 🌅 **Morning** (until 11:00 AM): Initial assessment and blanketing
    - ☀️ **Day** (11:00 AM - 3:50 PM): Midday monitoring and adjustments  
    - 🌙 **Night** (3:50 PM onwards): Final check and overnight preparation
    """)

    # Advanced blanketing logic with forecast integration
    if weather_data and weather_data['feels_like'] is not None:
        current_feels_like = weather_data['feels_like']
        
        st.subheader("🌡️ Advanced Blanketing Recommendations")
        
        # Get forecast data for next phase
        try:
            latitude, longitude = get_location_coordinates()
            min_forecast_feels_like, forecast_periods, next_phase_time = get_next_phase_forecast(
                phase_name, latitude, longitude
            )
        except:
            min_forecast_feels_like = None
            forecast_periods = []
            next_phase_time = None
        
        # Display current and forecast temperatures
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.metric("Current Feels Like", f"{current_feels_like}°F")
        
        with col2:
            if min_forecast_feels_like is not None:
                st.metric("Forecast Low", f"{min_forecast_feels_like}°F", 
                         delta=f"{min_forecast_feels_like - current_feels_like}°F")
            else:
                st.metric("Forecast Low", "Loading...")
        
        with col3:
            # Determine housing status automatically or allow user selection
            auto_housing_status, housing_reason, user_selectable = determine_housing_status(
                weather_data, forecast_periods
            )
            
            if user_selectable:
                # Show selector when conditions allow user choice
                housing_status = st.selectbox(
                    "Housing Status", 
                    ["Horses OUT", "Horses IN"], 
                    index=0 if auto_housing_status == "Horses OUT" else 1,
                    key="housing_status"
                )
                if housing_reason:
                    st.caption(f"💡 {housing_reason}")
            else:
                # Auto-determined housing with explanation
                st.metric("Housing Status", auto_housing_status.split()[-1])  # Show just "OUT" or "IN"
                st.caption(f"🔒 {housing_reason}")
                housing_status = auto_housing_status
        
        # Determine blanketing thresholds based on housing
        if housing_status == "Horses OUT":
            thresholds = {'light': 50, 'medium': 40, 'heavy': 30}
            temp_ranges = {"50-40°F": "light", "40-30°F": "medium", "Below 30°F": "heavy"}
        else:  # Horses IN
            thresholds = {'light': 45, 'medium': 35, 'heavy': 25}
            temp_ranges = {"45-35°F": "light", "35-25°F": "medium", "Below 25°F": "heavy"}
        
        # Determine effective temperature for blanketing decision
        if min_forecast_feels_like is not None:
            # Use the lower of current and forecast minimum
            effective_temp = min(current_feels_like, min_forecast_feels_like)
            forecast_available = True
        else:
            effective_temp = current_feels_like
            forecast_available = False
        
        # Apply blanketing logic with overheating prevention
        def get_blanket_category(temp):
            if temp >= thresholds['light']:
                return 'none'
            elif temp >= thresholds['medium']:
                return 'light'
            elif temp >= thresholds['heavy']:
                return 'medium'
            else:
                return 'heavy'
        
        current_category = get_blanket_category(current_feels_like)
        effective_category = get_blanket_category(effective_temp)
        
        # Special logic: if current is hot but forecast is cold, prefer lighter blanketing
        # Horses can tolerate 1-2 hours of cold better than overblanketing
        if forecast_available and current_feels_like > effective_temp:
            temp_diff = current_feels_like - effective_temp
            if temp_diff >= 10:  # Significant temperature drop expected
                st.warning(f"⚠️ **Temperature Drop Alert**: Current {current_feels_like}°F → Forecast Low {min_forecast_feels_like}°F")
                if effective_category in ['medium', 'heavy'] and current_category in ['none', 'light']:
                    st.info("🧠 **Smart Blanketing**: Reducing blanket weight to prevent overheating. Horses tolerate brief cold better than overblanketing.")
                    # Step down one category to prevent overheating
                    if effective_category == 'heavy':
                        effective_category = 'medium'
                    elif effective_category == 'medium':
                        effective_category = 'light'
        
        # Special morning options if current phase is Morning
        if phase_name == "Morning":
            st.subheader("🌅 Morning Blanketing Options")
            
            # Option 1: Conservative (blanket for whole day until evening)
            try:
                evening_forecast_low, _, _ = get_next_phase_forecast("Day", latitude, longitude)
                if evening_forecast_low is not None:
                    conservative_temp = min(current_feels_like, evening_forecast_low)
                    conservative_category = get_blanket_category(conservative_temp)
                    
                    st.write("**Option 1: Conservative (until Night phase)**")
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.metric("Effective Temperature", f"{conservative_temp}°F")
                    with col2:
                        st.write(f"Covers until Night care (~{evening_forecast_low}°F expected)")
                    
                    display_blanketing_recommendation(conservative_category, housing_status, "conservative")
                    
                    st.write("**Option 2: Normal (until Day phase)**")
            except:
                pass
        
        # Display main recommendation
        st.subheader("🎯 Primary Recommendation")
        if forecast_available:
            st.write(f"Based on current {current_feels_like}°F and forecast low {min_forecast_feels_like}°F until next care phase:")
        else:
            st.write(f"Based on current temperature {current_feels_like}°F (forecast unavailable):")
        
        display_blanketing_recommendation(effective_category, housing_status, "primary")
        
        # Show forecast timeline if available
        if forecast_periods and len(forecast_periods) > 0:
            # Add debug info for Night phase
            debug_info = ""
            if next_phase_time:
                debug_info = f" (targeting {next_phase_time.strftime('%b %d, %I:%M %p')})"
            
            with st.expander(f"📊 Forecast Timeline Until Next Care Phase{debug_info}"):
                for i, period in enumerate(forecast_periods):
                    if period.get('feels_like') is not None:
                        # Get a meaningful time string, try to parse the actual time first
                        time_str = period.get('name', '').strip()
                        
                        # If name is empty, try to format the actual time
                        if not time_str and period.get('time'):
                            try:
                                period_time = parser.parse(period['time'])
                                time_str = period_time.strftime("%b %d, %I:%M %p")  # e.g., "Feb 16, 02:30 PM"
                            except:
                                time_str = f"Period {i+1}"
                        elif not time_str:  # If both name and time parsing failed
                            time_str = f"Period {i+1}"
                            
                        st.write(f"• **{time_str}**: {period['feels_like']}°F feels like ({period.get('short_forecast', 'N/A')})")
    else:
        st.info("Connect weather data to see personalized blanketing recommendations")


def display_blanketing_recommendation(category, housing_status, option_type="primary"):
    """Display blanketing recommendation based on category"""
    if category == 'none':
        st.success("☀️ **No Blanket Needed**")
        st.write("**Horses:** No blanketing required")
        st.write("**Donkeys:** No blanketing required")
        if housing_status == "Horses OUT":
            st.write("• Ensure adequate shade and water")
        else:
            st.write("• Ensure adequate ventilation in barn")
    elif category == 'light':
        st.info("🧸 **Light Blanketing**")
        st.write("**Horses:** Turnout sheet without neck piece")
        st.write("**Donkeys:** No blanketing required")
        st.write("• Monitor for comfort and proper fit")
    elif category == 'medium':
        st.warning("🧥 **Medium Blanketing**")
        st.write("**Horses:** Fleece sheet + turnout sheet with neck piece over it")
        st.write("**Donkeys:** No blanketing required")
        st.write("• Check layering is secure and comfortable")
    else:  # heavy
        st.error("🥶 **Heavy Blanketing**")
        st.write("**Horses:** Weighted blanket with neck piece + turnout sheet without neck piece over it")
        st.write("**Donkeys:** Weighted blanket")
        st.write("• Check animals hourly for signs of cold stress")
        if housing_status == "Horses OUT":
            st.write("• Ensure adequate shelter and windbreak")
        else:
            st.write("• Monitor closely even in barn environment")