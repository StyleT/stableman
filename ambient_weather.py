"""
AmbientWeather.net API client with rate limiting and retry logic
"""
import time
import requests
import logging
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
        logging.debug(f"Making API request to endpoint: {endpoint} with params: {params}")
        
        # Apply rate limiting
        logging.debug(f"Applying rate limit delay: {self.rate_limit_delay}s")
        time.sleep(self.rate_limit_delay)
        
        # Prepare request parameters
        request_params = {
            'apiKey': self.api_key,
            'applicationKey': self.app_key
        }
        if params:
            request_params.update(params)
        
        url = f"{self.base_url}/{endpoint}"
        logging.debug(f"Full URL: {url}")
        
        # Retry logic for 429 errors
        for attempt in range(self.max_retries):
            logging.debug(f"API request attempt {attempt + 1}/{self.max_retries}")
            try:
                response = requests.get(url, params=request_params, timeout=10)
                logging.debug(f"Response status: {response.status_code}")
                
                if response.status_code == 429:
                    logging.warning(f"Rate limit hit on attempt {attempt + 1}, status: 429")
                    if attempt < self.max_retries - 1:  # Don't wait on last attempt
                        logging.debug(f"Waiting {self.retry_delay}s before retry")
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        error_msg = "⏱️ API rate limit exceeded after retries. Please try again later."
                        logging.error(error_msg)
                        return None, error_msg
                
                response.raise_for_status()
                response_data = response.json()
                logging.debug(f"Successful API response received: {len(str(response_data))} characters")
                return response_data, None
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    error_msg = "⏱️ API rate limit exceeded. Please try again later."
                    logging.error(f"HTTP 429 error: {error_msg}")
                    return None, error_msg
                else:
                    error_msg = f"API HTTP error: {e.response.status_code}"
                    logging.error(f"HTTP error on attempt {attempt + 1}: {error_msg} - {str(e)}")
                    return None, error_msg
            except requests.exceptions.RequestException as e:
                error_msg = f"API request failed: {str(e)}"
                logging.error(f"Request exception on attempt {attempt + 1}: {error_msg}")
                return None, error_msg
            except Exception as e:
                error_msg = f"Error making API request: {str(e)}"
                logging.error(f"Unexpected exception on attempt {attempt + 1}: {error_msg}")
                return None, error_msg
        
        error_msg = "Request failed after all retry attempts"
        logging.error(f"All {self.max_retries} retry attempts failed")
        return None, error_msg
    
    def get_devices(self) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """
        Get list of weather stations for the account
        
        Returns:
            Tuple of (devices_list, error_message)
        """
        logging.info("Fetching device list from AmbientWeather API")
        devices_data, error = self._make_request("devices")
        
        if error:
            logging.error(f"Failed to get devices: {error}")
            return None, error
        
        if not devices_data:
            error_msg = "No weather stations found"
            logging.warning(error_msg)
            return None, error_msg
        
        logging.info(f"Successfully retrieved {len(devices_data)} weather station(s)")
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
        logging.info(f"Fetching weather data for device: {mac_address}, limit: {limit}")
        endpoint = f"devices/{mac_address}"
        params = {'limit': limit}
        
        data, error = self._make_request(endpoint, params)
        if error:
            logging.error(f"Failed to get device data for {mac_address}: {error}")
            return None, error
        else:
            logging.info(f"Successfully retrieved weather data for device {mac_address}")
        
        return data, error
    
    def get_latest_weather_data(self) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Get the latest weather data from preferred device (if MAC specified) or first available device
        
        Returns:
            Tuple of (weather_data_dict, error_message)
        """
        logging.info("Getting latest weather data")
        
        # If we have a preferred MAC address, use it directly
        if self.preferred_mac_address:
            logging.info(f"Using preferred MAC address: {self.preferred_mac_address}")
            weather_data_list, error = self.get_device_data(self.preferred_mac_address, limit=1)
            if error:
                logging.error(f"Error fetching data for preferred device {self.preferred_mac_address}: {error}")
                return None, error
            
            if not weather_data_list:
                error_msg = "No weather data available for specified device"
                logging.warning(f"No data returned for device {self.preferred_mac_address}")
                return None, error_msg
            
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
        logging.info("No preferred MAC address set, fetching device list for selection")
        devices, error = self.get_devices()
        if error:
            logging.error(f"Cannot proceed without device list: {error}")
            return None, error
        
        if not devices:
            error_msg = "No weather stations found"
            logging.error(error_msg)
            return None, error_msg
        
        # Return special response indicating device selection needed
        if len(devices) == 1:
            # Only one device, use it and suggest adding to env
            device = devices[0]
            mac_address = device.get('macAddress')
            device_name = device.get('info', {}).get('name', 'Weather Station')
            
            logging.info(f"Single device found: {device_name} ({mac_address})")
            return None, f"DEVICE_SELECTION_SINGLE|{mac_address}|{device_name}"
        else:
            # Multiple devices, need user to choose
            logging.info(f"Multiple devices found ({len(devices)}), user selection required")
            device_list = []
            for device in devices:
                mac = device.get('macAddress', 'Unknown')
                name = device.get('info', {}).get('name', 'Unnamed Station')
                device_list.append(f"{name}|{mac}")
                logging.debug(f"Available device: {name} ({mac})")
            
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
    
    logging.debug("Creating AmbientWeather API client")
    
    if not api_key:
        api_key = os.getenv('AMBIENT_API_KEY')
        logging.debug(f"API key from environment: {'***' if api_key else 'Not found'}")
    if not app_key:
        app_key = os.getenv('AMBIENT_APP_KEY')
        logging.debug(f"App key from environment: {'***' if app_key else 'Not found'}")
    if not mac_address:
        mac_address = os.getenv('AMBIENT_MAC_ADDRESS')
        logging.debug(f"MAC address from environment: {mac_address if mac_address else 'Not set'}")
    
    if not api_key or not app_key:
        error_msg = "Weather API keys not configured. Set AMBIENT_API_KEY and AMBIENT_APP_KEY environment variables."
        logging.error(error_msg)
        return None, error_msg
    
    client = AmbientWeatherAPI(api_key, app_key)
    client.preferred_mac_address = mac_address  # Store preferred MAC address
    logging.info(f"AmbientWeather API client created successfully{' with preferred MAC' if mac_address else ' (no preferred MAC)'}")
    return client, None