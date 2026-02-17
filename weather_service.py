"""
Unified weather service with fallback mechanisms.
Tries AmbientWeather.net first, falls back to Weather.gov for current conditions.
"""
import logging
from typing import Dict, List, Optional, Tuple, Any
from ambient_weather import create_api_client
from weather_gov import create_weather_gov_client
from configuration import get_location_coordinates


def get_current_weather_data() -> Tuple[Optional[Dict], Optional[str]]:
    """
    Get current weather data with fallback mechanism.
    
    Primary: AmbientWeather.net API (real-time station data)
    Fallback: Weather.gov API (most recent forecast period as current conditions)
    
    Returns:
        Tuple of (weather_data_dict, error_message)
        weather_data_dict contains:
        - temperature: Temperature in Fahrenheit
        - feels_like: Feels-like temperature in Fahrenheit
        - humidity: Humidity percentage
        - station_name: Source description
        - last_update: Timestamp or time string
        - source: Data source ('ambient' or 'weather_gov')
    """
    logging.info("Attempting to fetch current weather data")
    
    # Try AmbientWeather.net first
    logging.debug("Trying AmbientWeather.net API")
    api_client, error = create_api_client()
    
    if not error:
        weather_data, ambient_error = api_client.get_latest_weather_data()
        
        if not ambient_error and weather_data:
            logging.info("Successfully retrieved weather data from AmbientWeather.net")
            weather_data['source'] = 'ambient'
            return weather_data, None
        else:
            logging.warning(f"AmbientWeather.net failed: {ambient_error}")
    else:
        logging.warning(f"AmbientWeather.net client creation failed: {error}")
    
    # Fallback to Weather.gov
    logging.info("Falling back to Weather.gov API for current conditions")
    try:
        latitude, longitude = get_location_coordinates()
        if not latitude or not longitude:
            error_msg = "Cannot fetch weather data: location coordinates not configured"
            logging.error(error_msg)
            return None, error_msg
        
        logging.debug(f"Using coordinates: {latitude}, {longitude}")
        weather_gov_client = create_weather_gov_client()
        forecast_data, gov_error = weather_gov_client.get_24_hour_forecast(latitude, longitude)
        
        if gov_error:
            error_msg = f"Both weather sources failed. Ambient: {ambient_error or error}. Weather.gov: {gov_error}"
            logging.error(error_msg)
            return None, error_msg
        
        if not forecast_data or not forecast_data.get('forecast'):
            error_msg = "Weather.gov returned no forecast data"
            logging.error(error_msg)
            return None, error_msg
        
        # Use the first forecast period as "current" conditions
        current_period = forecast_data['forecast'][0]
        location_info = forecast_data.get('location', {})
        
        # Convert to ambient weather format for consistency
        fallback_weather_data = {
            'temperature': current_period.get('temperature'),
            'feels_like': current_period.get('feels_like'),
            'humidity': current_period.get('humidity'),
            'station_name': f"NWS {location_info.get('city', 'Weather Station')} ({location_info.get('office', 'NWS')})",
            'last_update': current_period.get('time'),
            'source': 'weather_gov',
            'raw_data': current_period,
            'location_info': location_info
        }
        
        logging.info(f"Successfully retrieved fallback weather data from Weather.gov for {location_info.get('city', 'location')}")
        return fallback_weather_data, None
        
    except Exception as e:
        error_msg = f"Weather.gov fallback failed: {str(e)}"
        logging.error(error_msg)
        combined_error = f"All weather sources failed. Ambient: {ambient_error or error}. Weather.gov: {error_msg}"
        return None, combined_error


def get_weather_data_with_source_info() -> Tuple[Optional[Dict], Optional[str], str]:
    """
    Get weather data with detailed source information.
    
    Returns:
        Tuple of (weather_data_dict, error_message, source_description)
    """
    weather_data, error = get_current_weather_data()
    
    if error:
        return None, error, "No data source available"
    
    source = weather_data.get('source', 'unknown')
    if source == 'ambient':
        source_desc = "🏡 Personal Weather Station (AmbientWeather.net)"
    elif source == 'weather_gov':
        source_desc = "🏛️ National Weather Service (Weather.gov)"
    else:
        source_desc = "❓ Unknown Source"
    
    return weather_data, None, source_desc