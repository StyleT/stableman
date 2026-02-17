# Stableman - Copilot Instructions 🐴

## Project Overview
Stableman is a Streamlit web application that provides horse blanketing instructions to stable hands based on weather conditions and established care guidelines. The app integrates with AmbientWeather.net API to deliver real-time, condition-specific blanketing recommendations with intelligent caching and rate limiting.

## Architecture & Structure
- **Modular Design**: Separated concerns across multiple focused modules
- **Main UI**: Core weather application logic in `streamlit_app.py`
- **Configuration Management**: Environment variable validation and UI in `configuration.py`
- **Weather API Module**: AmbientWeather.net client in `ambient_weather.py`
- **Forecast API Module**: Weather.gov client in `weather_gov.py`
- **Smart Configuration**: Dynamic UI that shows only missing configuration items
- **Weather Integration**: Dual APIs for current conditions and 24-hour forecasts
- **Decision Logic**: Temperature-based horse blanketing guidelines (20°F/40°F/60°F thresholds)
- **Smart Caching**: 1-minute cache for current weather, 30-minute for forecasts
- **Timezone Handling**: Browser-aware timestamp display with pytz integration

## Key Dependencies
```
streamlit>=1.30.0           # Core web framework
requests>=2.28.0            # HTTP client for weather API
python-dotenv>=0.19.0       # Environment variable management
pytz>=2021.1                # Timezone handling for timestamps
```

## Environment Configuration
All required environment variables in `.env` file:
```bash
AMBIENT_API_KEY=<your_api_key>          # Required: AmbientWeather.net API key
AMBIENT_APP_KEY=<your_application_key>   # Required: AmbientWeather.net app key
AMBIENT_MAC_ADDRESS=<device_mac>         # Required: Weather station MAC address
LOCATION_LATITUDE=40.7128               # Required: Stable location latitude
LOCATION_LONGITUDE=-74.0060             # Required: Stable location longitude
```

**Configuration Management** (`configuration.py`):
- **`check_configuration()`**: Returns list of missing environment variables
- **`is_configuration_complete()`**: Boolean check for complete setup
- **`display_configuration_ui()`**: Smart UI showing only missing items
- **`get_location_coordinates()`**: Safe coordinate retrieval with fallbacks
- **Dynamic Display**: Configuration UI only shows when setup is incomplete

## Weather.gov Forecast Integration (`weather_gov.py`)

### Key Classes & Methods:
- **`WeatherGovClient`**: National Weather Service API client with location resolution
- **`get_24_hour_forecast()`**: Fetches detailed 24-hour forecast with feels-like calculations
- **`_resolve_location()`**: Converts lat/lng to NWS grid points for forecast data
- **`calculate_feels_like()`**: Computes heat index and wind chill from temperature/humidity/wind
- **Location Metadata**: Returns city, state, timezone, and NWS office information

### Forecast Features:
- **Grid Point Resolution**: Automatic conversion from coordinates to NWS forecast grids
- **Enhanced Data**: Adds feels-like temperature calculations not provided by API
- **Location Context**: Rich location display with city, state, and NWS office
- **Error Handling**: Graceful degradation for API failures with coordinate fallbacks

## Weather API Integration (`ambient_weather.py`)

### Key Classes & Methods:
- **`AmbientWeatherAPI`**: Main client class with rate limiting (1.1s delays between calls)
- **`get_latest_weather_data()`**: Returns formatted weather data with temperature, feels-like, humidity
- **`create_api_client()`**: Factory function that loads environment variables
- **Rate Limiting**: Automatic 1-second waits + 3-retry logic for 429 errors
- **MAC Address Optimization**: Skips device listing when `AMBIENT_MAC_ADDRESS` is set

### Device Selection Logic:
- **MAC Provided**: Direct API call to specific device (1 API call)
- **Single Device Found**: Shows device info, suggests adding MAC to `.env`
- **Multiple Devices**: Lists all devices, prompts user to select via environment config

## Streamlit App Patterns (`streamlit_app.py`)

### Page Configuration
```python
st.set_page_config(page_title="Stableman", page_icon="🐴")
```

### Configuration Integration
```python
from configuration import check_configuration, display_configuration_ui, get_location_coordinates

missing_config = check_configuration()
if missing_config:
    display_configuration_ui(missing_config)  # Smart configuration UI
else:
    # Show full weather application
    latitude, longitude = get_location_coordinates()
```

### Caching Strategy
```python
@st.cache_data(ttl=60)  # 1-minute cache for weather data
```

### UI Layout
- **4-Column Current Weather**: Temperature | Feels Like | Humidity | Station
- **3-Tab Forecast Display**: Next 8 Hours | 8-16 Hours | 16-24 Hours
- **6-Column Forecast Details**: Time | Temperature | Humidity | Wind | Rain | Conditions
- **Location Context**: City, state, coordinates with NWS office information
- **Human-Readable Timestamps**: "February 16, 2026 at 02:30 PM EST" + "5 minutes ago"
- **Dynamic Configuration UI**: Only shows missing required variables
- **Error Handling**: Specific UI for device selection, rate limits, and API errors

### Blanketing Logic
Temperature-based recommendations:
```python
if temp < 20: "Heavy Blanket Required" (300g+ fill)
elif temp < 40: "Medium Blanket Recommended" (150-250g)
elif temp < 60: "Light Blanket Optional"
else: "No Blanket Needed"
```

## Development Workflow

### Local Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
streamlit run streamlit_app.py
```

### Testing Weather API
```bash
python test_weather_api.py  # Standalone API test script
```

## Project-Specific Conventions
- **Emoji Usage**: Extensive use for visual clarity (🐴🌡️💧📍⏰)
- **Error Messages**: User-friendly with actionable guidance
- **API Efficiency**: Prefer cached data over fresh API calls
- **Configuration Guidance**: Auto-generated `.env` suggestions for device setup
- **Timestamp Handling**: Unix milliseconds → human-readable + relative time

## Common Tasks

### Adding New Configuration Variables
1. Update `get_required_variables()` in `configuration.py`
2. Add contextual help in `_display_contextual_help()`
3. Update environment variable documentation

### Adding Weather Data Fields
1. Update `ambient_weather.py` data structure in `get_latest_weather_data()`
2. Add UI display in `streamlit_app.py` metrics section
3. Consider blanketing logic impact

### Adding Forecast Data Fields
1. Update `weather_gov.py` data parsing in `get_24_hour_forecast()`
2. Add display columns in `display_forecast_period()` function
3. Consider strategic blanketing recommendations

### Modifying Cache Duration
- Current weather: Change `ttl=60` in `@st.cache_data(ttl=60)` decorator
- Forecast data: Change `ttl=1800` in forecast cache decorator

### Adding Blanketing Rules
Update temperature threshold logic in blanketing instructions section

### API Rate Limit Tuning
Modify `rate_limit_delay` and `retry_delay` in `AmbientWeatherAPI` class

## External Integration
- **AmbientWeather.net API**: Real-time weather station data with device management
- **Weather.gov API**: 24-hour forecasts with location resolution and grid point mapping
- **Rate Limits**: 
  - AmbientWeather: 1 request/second per API key, 3 requests/second per developer key
  - Weather.gov: No explicit rate limits but respectful usage recommended
- **Timezone Handling**: Browser timezone detection via `st.context.timezone`
- **Deployment**: Optimized for Streamlit Cloud with environment variable support

## File Structure
```
├── streamlit_app.py          # Main UI application with weather display
├── configuration.py          # Environment variable validation and configuration UI
├── ambient_weather.py        # AmbientWeather.net API client for current conditions
├── weather_gov.py            # Weather.gov API client for 24-hour forecasts
├── test_weather_api.py       # Standalone API testing script
├── requirements.txt          # Python dependencies
├── .env                      # API keys and configuration (gitignored)
└── .github/copilot-instructions.md  # This file
```