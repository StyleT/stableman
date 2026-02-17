"""
Main Tab for Stableman application.
Contains blanketing instructions UI that uses separated business logic.
"""
import streamlit as st
from datetime import datetime, timedelta
from dateutil import parser
import pytz
from weather_gov import create_weather_gov_client
from configuration import get_location_coordinates
from blanketing_logic import BlanktetingLogic, get_care_instructions_by_category


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
            # Determine housing status using business logic
            housing_decision = BlanktetingLogic.determine_housing_status(
                weather_data, forecast_periods
            )
            
            if housing_decision.user_selectable:
                # Show selector when conditions allow user choice
                housing_status = st.selectbox(
                    "Housing Status", 
                    ["Horses OUT", "Horses IN"], 
                    index=0 if housing_decision.status == "Horses OUT" else 1,
                    key="housing_status"
                )
                if housing_decision.reason:
                    st.caption(f"💡 {housing_decision.reason}")
            else:
                # Auto-determined housing with explanation
                st.metric("Housing Status", housing_decision.status.split()[-1])  # Show just "OUT" or "IN"
                st.caption(f"🔒 {housing_decision.reason}")
                housing_status = housing_decision.status
        
        # Make blanketing decision using business logic
        blanketing_decision = BlanktetingLogic.make_blanketing_decision(
            current_feels_like, min_forecast_feels_like, housing_status
        )
        
        # Show temperature drop alert if applicable
        if blanketing_decision.has_temp_drop_alert:
            st.warning(f"⚠️ **Temperature Drop Alert**: Current {current_feels_like}°F → Forecast Low {min_forecast_feels_like}°F")
            if blanketing_decision.step_down_applied:
                st.info("🧠 **Smart Blanketing**: Reducing blanket weight to prevent overheating. Horses tolerate brief cold better than overblanketing.")
        
        # Special morning options if current phase is Morning
        if phase_name == "Morning":
            st.subheader("🌅 Morning Blanketing Options")
            
            # Option 1: Conservative (blanket for whole day until night)
            try:
                evening_forecast_low, _, _ = get_next_phase_forecast("Day", latitude, longitude)
                if evening_forecast_low is not None:
                    conservative_decision = BlanktetingLogic.make_blanketing_decision(
                        current_feels_like, evening_forecast_low, housing_status
                    )
                    
                    st.write("**Option 1: Conservative (until Night phase)**")
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.metric("Effective Temperature", f"{conservative_decision.effective_temp}°F")
                    with col2:
                        st.write(f"Covers until Night care (~{evening_forecast_low}°F expected)")
                    
                    display_blanketing_recommendation_from_decision(conservative_decision)
                    
                    st.write("**Option 2: Normal (until Day phase)**")
            except:
                pass
        
        # Display main recommendation
        st.subheader("🎯 Primary Recommendation")
        if blanketing_decision.forecast_low is not None:
            st.write(f"Based on current {current_feels_like}°F and forecast low {blanketing_decision.forecast_low}°F until next care phase:")
        else:
            st.write(f"Based on current temperature {current_feels_like}°F (forecast unavailable):")
        
        display_blanketing_recommendation_from_decision(blanketing_decision)
        
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


def display_blanketing_recommendation_from_decision(blanketing_decision):
    """Display blanketing recommendation from BlanktetingDecision object"""
    instructions = get_care_instructions_by_category(
        blanketing_decision.category, 
        blanketing_decision.housing_status
    )
    
    # Display with appropriate Streamlit styling
    if instructions['color'] == 'success':
        st.success(f"{instructions['emoji']} **{instructions['title']}**")
    elif instructions['color'] == 'info':
        st.info(f"{instructions['emoji']} **{instructions['title']}**")
    elif instructions['color'] == 'warning':
        st.warning(f"{instructions['emoji']} **{instructions['title']}**")
    else:  # error
        st.error(f"{instructions['emoji']} **{instructions['title']}**")
    
    # Display care instructions
    st.write(f"**Horses:** {instructions['horses']}")
    st.write(f"**Donkeys:** {instructions['donkeys']}")
    
    for note in instructions['care_notes']:
        st.write(f"• {note}")


# Backwards compatibility function (can be removed later)
def display_blanketing_recommendation(category, housing_status, option_type="primary"):
    """Display blanketing recommendation based on category (legacy function)"""
    instructions = get_care_instructions_by_category(category, housing_status)
    
    # Display with appropriate Streamlit styling
    if instructions['color'] == 'success':
        st.success(f"{instructions['emoji']} **{instructions['title']}**")
    elif instructions['color'] == 'info':
        st.info(f"{instructions['emoji']} **{instructions['title']}**")
    elif instructions['color'] == 'warning':
        st.warning(f"{instructions['emoji']} **{instructions['title']}**")
    else:  # error
        st.error(f"{instructions['emoji']} **{instructions['title']}**")
    
    # Display care instructions
    st.write(f"**Horses:** {instructions['horses']}")
    st.write(f"**Donkeys:** {instructions['donkeys']}")
    
    for note in instructions['care_notes']:
        st.write(f"• {note}")