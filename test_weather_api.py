#!/usr/bin/env python3
"""
Test script for AmbientWeather.net API integration
Tests API connectivity and displays current weather data with blanketing recommendations
"""

import os
import requests
import time
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()

    api_key = os.getenv('AMBIENT_API_KEY')
    app_key = os.getenv('AMBIENT_APP_KEY')

    print(f"API Key loaded: {'✅' if api_key else '❌'}")
    print(f"App Key loaded: {'✅' if app_key else '❌'}")

    if api_key and app_key:
        print("\nTesting AmbientWeather API connection...")
        
        # Test API connection by fetching devices
        try:
            print("⏱️ Waiting 1 second between API calls to respect rate limits...")
            
            devices_url = "https://rt.ambientweather.net/v1/devices"
            params = {
                'apiKey': api_key,
                'applicationKey': app_key
            }
            
            response = requests.get(devices_url, params=params, timeout=10)
            print(f"API Response Status: {response.status_code}")
            
            if response.status_code == 429:
                print("❌ Rate limit exceeded (429). Wait and try again.")
                return
            
            if response.status_code == 200:
                devices = response.json()
                print(f"Found {len(devices)} weather station(s)")
                
                if devices:
                    device = devices[0]
                    print(f"Station Name: {device.get('info', {}).get('name', 'Unknown')}")
                    print(f"MAC Address: {device.get('macAddress')}")
                    
                    # Rate limit: wait before second API call
                    print("⏱️ Waiting 1 second before fetching weather data...")
                    time.sleep(1.1)
                    
                    # Get latest data
                    mac = device['macAddress']
                    data_url = f"https://rt.ambientweather.net/v1/devices/{mac}"
                    data_params = {
                        'apiKey': api_key,
                        'applicationKey': app_key,
                        'limit': 1
                    }
                    
                    data_response = requests.get(data_url, params=data_params, timeout=10)
                    
                    if data_response.status_code == 429:
                        print("❌ Rate limit exceeded (429) on weather data request.")
                        return
                        
                    if data_response.status_code == 200:
                        weather_data = data_response.json()
                        if weather_data:
                            latest = weather_data[0]
                            temp = latest.get('tempf')
                            humidity = latest.get('humidity')
                            print(f"\n🌡️ Current Temperature: {temp}°F")
                            print(f"💧 Current Humidity: {humidity}%")
                            print(f"📅 Last Updated: {latest.get('dateutc')}")
                            
                            # Test blanketing logic
                            if temp is not None:
                                if temp < 20:
                                    recommendation = "❄️ Heavy Blanket Required"
                                elif temp < 40:
                                    recommendation = "🧥 Medium Blanket Recommended"
                                elif temp < 60:
                                    recommendation = "🧣 Light Blanket Optional"
                                else:
                                    recommendation = "☀️ No Blanket Needed"
                                print(f"\n🐴 Blanketing Recommendation: {recommendation}")
                            
                        else:
                            print("No weather data available")
                    else:
                        print(f"Weather data API error: {data_response.status_code}")
                        print(data_response.text)
                else:
                    print("No weather stations found")
            else:
                print(f"API Error: {response.text}")
                
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("❌ Missing API keys in .env file")
        print("Make sure AMBIENT_API_KEY and AMBIENT_APP_KEY are set in .env")

if __name__ == "__main__":
    main()