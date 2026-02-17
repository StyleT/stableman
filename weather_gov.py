"""
Weather.gov (National Weather Service) API client for weather forecasts
"""
import requests
import time
from typing import Dict, List, Optional, Tuple, Any
import math


def calculate_feels_like(temp_f: float, humidity: float, wind_mph: float = 0) -> float:
    """
    Calculate feels-like temperature using heat index and wind chill
    
    Args:
        temp_f: Temperature in Fahrenheit
        humidity: Relative humidity percentage (0-100)
        wind_mph: Wind speed in mph
        
    Returns:
        Feels-like temperature in Fahrenheit
    """
    if temp_f >= 80:
        # Use heat index for hot weather
        # Simplified Steadman's formula
        hi = (
            -42.379 +
            2.04901523 * temp_f +
            10.14333127 * humidity -
            0.22475541 * temp_f * humidity -
            6.83783e-3 * temp_f * temp_f -
            5.481717e-2 * humidity * humidity +
            1.22874e-3 * temp_f * temp_f * humidity +
            8.5282e-4 * temp_f * humidity * humidity -
            1.99e-6 * temp_f * temp_f * humidity * humidity
        )
        return round(hi, 1)
    elif temp_f <= 50 and wind_mph > 3:
        # Use wind chill for cold weather
        wc = (
            35.74 +
            0.6215 * temp_f -
            35.75 * (wind_mph ** 0.16) +
            0.4275 * temp_f * (wind_mph ** 0.16)
        )
        return round(wc, 1)
    else:
        # No significant heat index or wind chill
        return temp_f


class WeatherGovAPI:
    """Client for interacting with Weather.gov API for forecasts"""
    
    def __init__(self, user_agent: str = "StablemanApp/1.0"):
        self.base_url = "https://api.weather.gov"
        self.user_agent = user_agent
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})
    
    def _make_request(self, url: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Make a request to the Weather.gov API
        
        Args:
            url: Full URL to request
            
        Returns:
            Tuple of (response_data, error_message)
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json(), None
            
        except requests.exceptions.RequestException as e:
            return None, f"Weather.gov API request failed: {str(e)}"
        except Exception as e:
            return None, f"Error making Weather.gov API request: {str(e)}"
    
    def get_grid_point(self, latitude: float, longitude: float) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Get grid point information for coordinates
        
        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            
        Returns:
            Tuple of (grid_info, error_message)
        """
        url = f"{self.base_url}/points/{latitude},{longitude}"
        return self._make_request(url)
    
    def get_hourly_forecast(self, grid_x: int, grid_y: int, office: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Get hourly forecast for grid coordinates
        
        Args:
            grid_x: Grid X coordinate
            grid_y: Grid Y coordinate
            office: Weather office identifier
            
        Returns:
            Tuple of (forecast_periods, error_message)
        """
        url = f"{self.base_url}/gridpoints/{office}/{grid_x},{grid_y}/forecast/hourly"
        data, error = self._make_request(url)
        
        if error:
            return None, error
        
        if not data or 'properties' not in data or 'periods' not in data['properties']:
            return None, "Invalid forecast data format"
        
        return data['properties']['periods'], None
    
    def get_24_hour_forecast(self, latitude: float, longitude: float) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Get detailed 24-hour forecast for coordinates with location info
        
        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            
        Returns:
            Tuple of (forecast_response_dict, error_message)
            forecast_response_dict contains:
            - 'location': location information
            - 'forecast': list of forecast periods
        """
        # Step 1: Get grid point
        grid_info, error = self.get_grid_point(latitude, longitude)
        if error:
            return None, error
        
        if not grid_info or 'properties' not in grid_info:
            return None, "Invalid grid point data"
        
        props = grid_info['properties']
        grid_x = props.get('gridX')
        grid_y = props.get('gridY')
        office = props.get('gridId')
        
        # Extract location information from grid point response
        location_info = {
            'city': props.get('relativeLocation', {}).get('properties', {}).get('city', ''),
            'state': props.get('relativeLocation', {}).get('properties', {}).get('state', ''),
            'office': office,
            'timezone': props.get('timeZone', ''),
            'coordinates': f"{latitude}, {longitude}"
        }
        
        if not all([grid_x, grid_y, office]):
            return None, "Missing grid coordinates"
        
        # Step 2: Get hourly forecast
        forecast_periods, error = self.get_hourly_forecast(grid_x, grid_y, office)
        if error:
            return None, error
        
        # Process and enhance forecast data
        enhanced_forecast = []
        for period in forecast_periods[:24]:  # Get 24 hours
            temp_f = period.get('temperature')
            humidity = period.get('relativeHumidity', {}).get('value', 50) if period.get('relativeHumidity') else 50
            wind_speed = period.get('windSpeed', '0 mph')
            
            # Extract wind speed number
            wind_mph = 0
            if isinstance(wind_speed, str):
                import re
                wind_match = re.search(r'(\d+)', wind_speed)
                if wind_match:
                    wind_mph = int(wind_match.group(1))
            
            # Calculate feels-like if we have temperature
            feels_like = None
            if temp_f is not None:
                feels_like = calculate_feels_like(temp_f, humidity, wind_mph)
            
            enhanced_period = {
                'time': period.get('startTime'),
                'name': period.get('name', ''),
                'temperature': temp_f,
                'feels_like': feels_like,
                'humidity': humidity,
                'wind_speed': wind_speed,
                'wind_mph': wind_mph,
                'precipitation_chance': period.get('probabilityOfPrecipitation', {}).get('value', 0) if period.get('probabilityOfPrecipitation') else 0,
                'short_forecast': period.get('shortForecast', ''),
                'detailed_forecast': period.get('detailedForecast', ''),
                'raw_data': period
            }
            enhanced_forecast.append(enhanced_period)
        
        return {
            'location': location_info,
            'forecast': enhanced_forecast
        }, None


def create_weather_gov_client(user_agent: str = "StablemanApp/1.0") -> WeatherGovAPI:
    """
    Factory function to create a Weather.gov API client
    
    Args:
        user_agent: User agent string for API requests
        
    Returns:
        WeatherGovAPI client instance
    """
    return WeatherGovAPI(user_agent)