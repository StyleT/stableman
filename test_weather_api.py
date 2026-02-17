#!/usr/bin/env python3
"""
Test script for AmbientWeather.net API integration
Tests API connectivity and displays current weather data with blanketing recommendations
"""

import os
from dotenv import load_dotenv
from ambient_weather import create_api_client

def main():
    # Load environment variables
    load_dotenv()

    print("🌤️ AmbientWeather API Test Script")
    print("=" * 40)
    
    # Create API client
    api_client, error = create_api_client()
    
    if error:
        print(f"❌ {error}")
        print("\nMake sure AMBIENT_API_KEY and AMBIENT_APP_KEY are set in .env")
        return
    
    print("✅ API client created successfully")
    print("\nTesting API connection...")
    
    # Test getting devices
    print("\n1. Fetching weather stations...")
    devices, error = api_client.get_devices()
    
    if error:
        print(f"❌ {error}")
        return
    
    print(f"✅ Found {len(devices)} weather station(s)")
    
    for i, device in enumerate(devices):
        print(f"   Station {i+1}: {device.get('info', {}).get('name', 'Unknown')}")
        print(f"   MAC: {device.get('macAddress')}")
    
    # Test getting weather data
    print("\n2. Fetching latest weather data...")
    weather_data, error = api_client.get_latest_weather_data()
    
    if error:
        print(f"❌ {error}")
        return
    
    print("✅ Weather data retrieved successfully")
    print(f"\n🌡️ Current Temperature: {weather_data['temperature']}°F")
    print(f"💧 Current Humidity: {weather_data['humidity']}%")
    print(f"📍 Station: {weather_data['station_name']}")
    print(f"📅 Last Updated: {weather_data['last_update']} UTC")
    
    # Test blanketing logic
    temp = weather_data['temperature']
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
    
    print("\n✅ All tests completed successfully!")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()