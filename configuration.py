"""
Configuration management for Stableman application.
Handles environment variable validation and configuration UI display.
"""
import os
import streamlit as st


def get_required_variables():
    """Get dictionary of required environment variables and their descriptions."""
    return {
        'AMBIENT_API_KEY': 'Your AmbientWeather.net API key',
        'AMBIENT_APP_KEY': 'Your AmbientWeather.net application key',
        'AMBIENT_MAC_ADDRESS': 'Your weather station MAC address',
        'LOCATION_LATITUDE': 'Stable location latitude',
        'LOCATION_LONGITUDE': 'Stable location longitude'
    }


def check_configuration():
    """
    Check which required environment variables are missing.
    
    Returns:
        list: List of tuples (variable_name, description) for missing variables
    """
    missing_config = []
    required_vars = get_required_variables()
    
    for var_name, description in required_vars.items():
        if not os.getenv(var_name):
            missing_config.append((var_name, description))
    
    return missing_config


def is_configuration_complete():
    """
    Check if all required configuration is present.
    
    Returns:
        bool: True if all required environment variables are set, False otherwise
    """
    return len(check_configuration()) == 0


def display_configuration_ui(missing_config):
    """
    Display configuration error UI with missing environment variables.
    
    Args:
        missing_config (list): List of tuples (variable_name, description) for missing variables
    """
    st.divider()
    st.error("🔧 **Configuration Required**")
    st.write("The following environment variables must be set for the app to function:")
    
    # Build configuration text with appropriate defaults
    config_text = ""
    for var_name, description in missing_config:
        if var_name == 'LOCATION_LATITUDE':
            config_text += f"{var_name}=40.7128  # {description}\n"
        elif var_name == 'LOCATION_LONGITUDE':
            config_text += f"{var_name}=-74.0060  # {description}\n"
        else:
            config_text += f"{var_name}=your_value_here  # {description}\n"
    
    st.code(config_text)
    
    # Display contextual help based on missing variables
    _display_contextual_help(missing_config)


def _display_contextual_help(missing_config):
    """
    Display contextual help messages based on which configuration is missing.
    
    Args:
        missing_config (list): List of tuples (variable_name, description) for missing variables
    """
    missing_var_names = [item[0] for item in missing_config]
    
    # API key help
    if any(var in missing_var_names for var in ['AMBIENT_API_KEY', 'AMBIENT_APP_KEY']):
        st.info("💡 Get your API keys from [AmbientWeather.net Developer Portal](https://ambientweather.docs.apiary.io/)")
    
    # MAC address help
    if 'AMBIENT_MAC_ADDRESS' in missing_var_names:
        st.warning("📍 Weather station MAC address is required for direct device access. The app will show available devices when you provide API keys.")
    
    # Location coordinates help
    if any(var in missing_var_names for var in ['LOCATION_LATITUDE', 'LOCATION_LONGITUDE']):
        st.warning("📍 Location coordinates are required for accurate weather forecasts at your stable.")


def get_location_coordinates():
    """
    Get location coordinates from environment variables with fallback defaults.
    
    Returns:
        tuple: (latitude, longitude) as float values
    """
    latitude = float(os.getenv('LOCATION_LATITUDE', '40.7128'))  # Default to NYC
    longitude = float(os.getenv('LOCATION_LONGITUDE', '-74.0060'))
    return latitude, longitude