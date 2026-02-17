"""
Main Tab for Stableman application.
Contains blanketing instructions UI that uses separated business logic.
"""
import streamlit as st
from datetime import datetime, timedelta
from dateutil import parser
from configuration import get_location_coordinates
from blanketing_logic import BlanktetingLogic, get_care_instructions_by_category
from timezone_utils import get_user_timezone

# Configuration for phase-specific recommendation options
PHASE_RECOMMENDATION_CONFIG = {
    "Morning": {
        "options": [
            {
                "name": "Conservative (until Night phase)",
                "emoji": "🛡️",
                "target_phase": "Night",  # Get forecast through entire Night phase
                "description": "Covers until Night care",
                "priority": "primary"
            },
            {
                "name": "Normal (until Day phase)", 
                "emoji": "⚡",
                "target_phase": "Day",  # Get forecast until Day phase ends
                "description": "Covers until Day care",
                "priority": "alternative"
            }
        ]
    },
    "Day": {
        "options": [
            {
                "name": "Primary Recommendation",
                "emoji": "🎯", 
                "target_phase": "Night",  # Standard next phase lookup
                "description": "Until next care phase",
                "priority": "primary"
            }
        ]
    },
    "Night": {
        "options": [
            {
                "name": "Primary Recommendation",
                "emoji": "🎯",
                "target_phase": "Morning",  # Standard next phase lookup
                "description": "Until next care phase", 
                "priority": "primary"
            }
        ]
    }
}


def get_phase_ui_elements(phase_name):
    """
    Get UI elements (emoji and description) for a blanketing phase.
    
    Args:
        phase_name: Phase name ('Morning', 'Day', 'Night')
        
    Returns:
        tuple: (phase_emoji, phase_description)
    """
    phase_ui = {
        "Morning": ("🌅", "Early care period"),
        "Day": ("☀️", "Midday monitoring period"),
        "Night": ("🌙", "Night care period")
    }
    return phase_ui.get(phase_name, ("❓", "Unknown phase"))


def get_period_time_string(period, index, user_timezone):
    """Helper function to get a formatted time string for a forecast period"""
    time_str = period.get('name', '').strip()
    
    # If name is empty, try to format the actual time
    if not time_str and period.get('time'):
        try:
            period_time = parser.parse(period['time'])
            # Convert to user timezone if it's UTC
            if period_time.tzinfo:
                local_period_time = period_time.astimezone(user_timezone)
                time_str = local_period_time.strftime("%b %d, %I:%M %p")  # e.g., "Feb 16, 02:30 PM"
            else:
                time_str = period_time.strftime("%b %d, %I:%M %p")
        except:
            time_str = f"Period {index+1}"
    elif not time_str:  # If both name and time parsing failed
        time_str = f"Period {index+1}"
    
    return time_str


def render_phase_recommendations(phase_name, current_feels_like, housing_status, latitude, longitude, user_timezone):
    """
    Render blanketing recommendations for any phase using configuration.
    
    Args:
        phase_name: Current phase name
        current_feels_like: Current feels-like temperature
        housing_status: Current housing status
        latitude, longitude: Location coordinates
        user_timezone: User's timezone
    """
    phase_config = PHASE_RECOMMENDATION_CONFIG.get(phase_name)
    if not phase_config:
        st.error(f"No configuration found for phase: {phase_name}")
        return
    
    options = phase_config["options"]
    decisions = []
    forecast_data = []
    
    # Calculate decisions and forecast data for each option
    for option in options:
        try:
            if option["target_phase"] == "Morning":  # Standard next phase lookup
                min_forecast_feels_like, forecast_periods, next_phase_time = BlanktetingLogic.get_next_phase_forecast(
                    phase_name, latitude, longitude, user_timezone
                )
            else:  # Look ahead to specific target phase
                min_forecast_feels_like, forecast_periods, next_phase_time = BlanktetingLogic.get_next_phase_forecast(
                    option["target_phase"], latitude, longitude, user_timezone
                )
            
            blanketing_decision = BlanktetingLogic.make_blanketing_decision(
                current_feels_like, None, housing_status, forecast_periods
            )
            
            decisions.append((option, blanketing_decision, forecast_periods, next_phase_time))
            forecast_data.append((forecast_periods, next_phase_time, option))
            
        except Exception as e:
            st.error(f"Error calculating {option['name']}: {e}")
            continue
    
    if not decisions:
        return
    
    # Display recommendations
    if len(decisions) == 1:
        # Single option - show as primary recommendation
        option, decision, forecast_periods, next_phase_time = decisions[0]
        st.subheader(f"{option['emoji']} {option['name']}")
        if decision.forecast_low is not None:
            st.write(f"Based on current {current_feels_like}°F and forecast low {decision.forecast_low}°F {option['description'].lower()}:")
        else:
            st.write(f"Based on current temperature {current_feels_like}°F (forecast unavailable):")
        
        display_blanketing_recommendation_from_decision(decision)
        
        # Show forecast timeline
        if forecast_periods and len(forecast_periods) > 0:
            debug_info = f" (until {next_phase_time.strftime('%b %d, %I:%M %p')})" if next_phase_time else ""
            with st.expander(f"📊 Forecast Timeline{debug_info}"):
                for i, period in enumerate(forecast_periods):
                    if period.get('feels_like') is not None:
                        time_str = get_period_time_string(period, i, user_timezone)
                        st.write(f"• **{time_str}**: {period['feels_like']}°F feels like ({period.get('short_forecast', 'N/A')})")
    
    else:
        # Multiple options - show primary and alternatives
        st.subheader(f"🌅 {phase_name} Blanketing Options")
        
        primary_option = None
        alternative_options = []
        
        for option, decision, forecast_periods, next_phase_time in decisions:
            if option["priority"] == "primary":
                primary_option = (option, decision, forecast_periods, next_phase_time)
            else:
                alternative_options.append((option, decision, forecast_periods, next_phase_time))
        
        # Always show primary option
        if primary_option:
            option, decision, forecast_periods, next_phase_time = primary_option
            st.write(f"**{option['emoji']} {option['name']}**")
            col1, col2 = st.columns([1, 1])
            with col1:
                st.metric("Effective Temperature", f"{decision.effective_temp}°F")
            with col2:
                forecast_text = f"~{decision.forecast_low}°F expected" if decision.forecast_low else option['description']
                st.write(f"{forecast_text}")
            
            display_blanketing_recommendation_from_decision(decision)
        
        # Show alternatives only if they differ from primary
        shown_alternatives = []
        for option, decision, forecast_periods, next_phase_time in alternative_options:
            if primary_option and decision.category != primary_option[1].category:
                shown_alternatives.append((option, decision, forecast_periods, next_phase_time))
                st.write("---")  # Visual separator
                st.write(f"**{option['emoji']} Alternative: {option['name']}**")
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.metric("Effective Temperature", f"{decision.effective_temp}°F")
                with col2:
                    forecast_text = f"~{decision.forecast_low}°F expected" if decision.forecast_low else option['description']
                    st.write(f"{forecast_text}")
                
                display_blanketing_recommendation_from_decision(decision)
        
        # Show forecast timelines
        if shown_alternatives and primary_option:
            # Show timelines for both primary and alternatives
            option, decision, forecast_periods, next_phase_time = primary_option
            if forecast_periods and len(forecast_periods) > 0:
                debug_info = f" (until {next_phase_time.strftime('%b %d, %I:%M %p')})" if next_phase_time else ""
                with st.expander(f"📊 {option['name']} Timeline{debug_info}"):
                    for i, period in enumerate(forecast_periods):
                        if period.get('feels_like') is not None:
                            time_str = get_period_time_string(period, i, user_timezone)
                            st.write(f"• **{time_str}**: {period['feels_like']}°F feels like ({period.get('short_forecast', 'N/A')})")
            
            for option, decision, forecast_periods, next_phase_time in shown_alternatives:
                if forecast_periods and len(forecast_periods) > 0:
                    debug_info = f" (until {next_phase_time.strftime('%b %d, %I:%M %p')})" if next_phase_time else ""
                    with st.expander(f"📊 {option['name']} Timeline{debug_info}"):
                        for i, period in enumerate(forecast_periods):
                            if period.get('feels_like') is not None:
                                time_str = get_period_time_string(period, i, user_timezone)
                                st.write(f"• **{time_str}**: {period['feels_like']}°F feels like ({period.get('short_forecast', 'N/A')})")
        elif primary_option:
            # Show single timeline for primary option
            option, decision, forecast_periods, next_phase_time = primary_option
            if forecast_periods and len(forecast_periods) > 0:
                debug_info = f" (until {next_phase_time.strftime('%b %d, %I:%M %p')})" if next_phase_time else ""
                with st.expander(f"📊 Forecast Timeline{debug_info}"):
                    for i, period in enumerate(forecast_periods):
                        if period.get('feels_like') is not None:
                            time_str = get_period_time_string(period, i, user_timezone)
                            st.write(f"• **{time_str}**: {period['feels_like']}°F feels like ({period.get('short_forecast', 'N/A')})")


def render_main_tab(weather_data):
    """
    Render the main tab content with blanketing instructions and about section.
    
    Args:
        weather_data (dict): Weather data from API for blanketing logic
    """    # Display current blanketing phase
    user_timezone = get_user_timezone()
    phase_name = BlanktetingLogic.get_current_phase(user_timezone)
    phase_emoji, phase_description = get_phase_ui_elements(phase_name)
    
    # Display current time in user's timezone
    import pytz
    utc_now = datetime.now(pytz.UTC)
    local_now = utc_now.astimezone(user_timezone)
    current_time = local_now.strftime("%I:%M %p")
    
    st.info(f"{phase_emoji} **{phase_name}** ({phase_description}) - {current_time}")
    
    # Advanced blanketing logic with forecast integration
    if weather_data and weather_data['feels_like'] is not None:
        current_feels_like = weather_data['feels_like']
        
        st.header("🌡️ Blanketing Recommendations")
        
        # Get forecast data for next phase
        try:
            latitude, longitude = get_location_coordinates()
            min_forecast_feels_like, forecast_periods, next_phase_time = BlanktetingLogic.get_next_phase_forecast(
                phase_name, latitude, longitude, user_timezone
            )
        except Exception as e:
            st.error(f"Error loading forecast: {str(e)}")
            forecast_periods = []
            next_phase_time = None
        
        # Display current temperature and forecast summary
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.metric("Current Feels Like", f"{current_feels_like}°F")
        
        with col2:
            if forecast_periods:
                # Show forecast period count and time range
                st.metric("Forecast Periods", f"{len(forecast_periods)} hours", 
                         help="Hours of forecast data analyzed for blanketing decision")
            else:
                st.metric("Forecast Data", "Loading...")
        
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
        
        # Make blanketing decision using improved temperature analysis
        blanketing_decision = BlanktetingLogic.make_blanketing_decision(
            current_feels_like, None, housing_status, forecast_periods
        )
        
        # Show temperature drop alert if applicable
        if blanketing_decision.has_temp_drop_alert:
            st.warning(f"⚠️ **Temperature Drop Alert**: Current {current_feels_like}°F → Forecast Low {blanketing_decision.forecast_low}°F")
            if blanketing_decision.step_down_applied:
                st.info("🧠 **Smart Blanketing**: Reducing blanket weight to prevent overheating. Horses tolerate brief cold better than overblanketing.")
        
        # Use generalized recommendation rendering for all phases
        render_phase_recommendations(
            phase_name, current_feels_like, housing_status, 
            latitude, longitude, user_timezone
        )
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