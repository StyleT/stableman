"""
AmbientWeather.net API client with rate limiting and retry logic
"""
import time
import requests
from typing import Dict, List, Optional, Tuple, Any


class AmbientWeatherAPI:
    """Client for interacting with AmbientWeather.net API with rate limiting and retry logic"""
    
    def __init__(self, api_key: str, app_key: str):
        self.api_key = api_key
        self.app_key = app_key
        self.base_url = "https://rt.ambientweather.net/v1"
        self.max_retries = 3
        self.retry_delay = 1.0
        self.rate_limit_delay = 1.1  # Slightly over 1 second to be safe
        self.preferred_mac_address = None  # Will be set by factory function
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Make a rate-limited API request with retry logic for 429 errors
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Additional query parameters
            
        Returns:
            Tuple of (response_data, error_message)
        """
        # Apply rate limiting
        time.sleep(self.rate_limit_delay)
        
        # Prepare request parameters
        request_params = {
            'apiKey': self.api_key,
            'applicationKey': self.app_key
        }
        if params:
            request_params.update(params)
        
        url = f"{self.base_url}/{endpoint}"
        
        # Retry logic for 429 errors
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, params=request_params, timeout=10)
                
                if response.status_code == 429:
                    if attempt < self.max_retries - 1:  # Don't wait on last attempt
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        return None, "⏱️ API rate limit exceeded after retries. Please try again later."
                
                response.raise_for_status()
                return response.json(), None
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    return None, "⏱️ API rate limit exceeded. Please try again later."
                else:
                    return None, f"API HTTP error: {e.response.status_code}"
            except requests.exceptions.RequestException as e:
                return None, f"API request failed: {str(e)}"
            except Exception as e:
                return None, f"Error making API request: {str(e)}"
        
        return None, "Request failed after all retry attempts"
    
    def get_devices(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Get list of weather stations for the account
        
        Returns:
            Tuple of (devices_list, error_message)
        """
        devices_data, error = self._make_request("devices")
        
        if error:
            return None, error
        
        if not devices_data:
            return None, "No weather stations found"
        
        return devices_data, None
    
    def get_device_data(self, mac_address: str, limit: int = 1) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Get weather data from a specific device
        
        Args:
            mac_address: MAC address of the weather station
            limit: Number of recent records to retrieve
            
        Returns:
            Tuple of (weather_data_list, error_message)
        """
        endpoint = f"devices/{mac_address}"
        params = {'limit': limit}
        
        return self._make_request(endpoint, params)
    
    def get_latest_weather_data(self) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Get the latest weather data from preferred device (if MAC specified) or first available device
        
        Returns:
            Tuple of (weather_data_dict, error_message)
        """
        # If we have a preferred MAC address, use it directly
        if self.preferred_mac_address:
            weather_data_list, error = self.get_device_data(self.preferred_mac_address, limit=1)
            if error:
                return None, error
            
            if not weather_data_list:
                return None, "No weather data available for specified device"
            
            latest_reading = weather_data_list[0]
            
            # Format the response
            return {
                'temperature': latest_reading.get('tempf'),
                'feels_like': latest_reading.get('feelsLike') or latest_reading.get('feelslikef'),
                'humidity': latest_reading.get('humidity'),
                'station_name': f"Weather Station ({self.preferred_mac_address})",
                'last_update': latest_reading.get('dateutc'),
                'mac_address': self.preferred_mac_address,
                'raw_data': latest_reading
            }, None
        
        # No preferred MAC address - need to list devices first
        devices, error = self.get_devices()
        if error:
            return None, error
        
        if not devices:
            return None, "No weather stations found"
        
        # Return special response indicating device selection needed
        if len(devices) == 1:
            # Only one device, use it and suggest adding to env
            device = devices[0]
            mac_address = device.get('macAddress')
            device_name = device.get('info', {}).get('name', 'Weather Station')
            
            return None, f"DEVICE_SELECTION_SINGLE|{mac_address}|{device_name}"
        else:
            # Multiple devices, need user to choose
            device_list = []
            for device in devices:
                mac = device.get('macAddress', 'Unknown')
                name = device.get('info', {}).get('name', 'Unnamed Station')
                device_list.append(f"{name}|{mac}")
            
            return None, f"DEVICE_SELECTION_MULTIPLE|{';'.join(device_list)}"


def create_api_client(api_key: Optional[str] = None, app_key: Optional[str] = None, mac_address: Optional[str] = None) -> Tuple[Optional[AmbientWeatherAPI], Optional[str]]:
    """
    Factory function to create an AmbientWeather API client
    
    Args:
        api_key: API key (if None, will try to get from environment)
        app_key: Application key (if None, will try to get from environment)
        mac_address: MAC address of weather station (if None, will try to get from environment)
        
    Returns:
        Tuple of (api_client, error_message)
    """
    import os
    
    if not api_key:
        api_key = os.getenv('AMBIENT_API_KEY')
    if not app_key:
        app_key = os.getenv('AMBIENT_APP_KEY')
    if not mac_address:
        mac_address = os.getenv('AMBIENT_MAC_ADDRESS')
    
    if not api_key or not app_key:
        return None, "Weather API keys not configured. Set AMBIENT_API_KEY and AMBIENT_APP_KEY environment variables."
    
    client = AmbientWeatherAPI(api_key, app_key)
    client.preferred_mac_address = mac_address  # Store preferred MAC address
    return client, None