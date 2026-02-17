# Stableman - Copilot Instructions 🐴

## Project Overview
Stableman is a Streamlit web application that provides horse blanketing instructions to stable hands based on weather conditions and established care guidelines. The app integrates with AmbientWeather.net API for real-time station data and falls back to Weather.gov for reliable current conditions, delivering condition-specific blanketing recommendations with intelligent caching and rate limiting.

## ⚠️ CRITICAL: Blanketing Rules Synchronization
**ALWAYS** keep [`blanketing_rules.md`](./blanketing_rules.md) synchronized with the implementation in `blanketing_logic.py`. Any changes to:
- Temperature thresholds
- Blanketing categories  
- Care instructions
- Phase timing
- Forecast logic
- Animal-specific rules
- Housing determination rules

**MUST** be immediately reflected in both the code AND the documentation. This ensures stable hands have accurate guidance and developers understand the business logic.

## Architecture & Structure
- **Four-Tab Modular Design**: Complete separation of concerns across focused UI modules
- **Main Orchestration**: Core application logic in `streamlit_app.py`
- **Business Logic Separation**: Pure logic in `blanketing_logic.py` separate from UI
- **Comprehensive Testing**: Unit tests in `test_blanketing_logic.py` with 35 test cases
- **Configuration Management**: Environment variable validation and UI in `configuration.py`
- **Weather Service Module**: Unified weather service with automatic fallback in `weather_service.py`
- **Weather API Modules**: AmbientWeather.net client in `ambient_weather.py`, Weather.gov client in `weather_gov.py`
- **Tab Modules**: Dedicated files for each UI tab
  - `main_tab.py` - Blanketing instructions interface (uses `blanketing_logic.py`)
  - `current_weather_tab.py` - Real-time conditions display with source indicators
  - `forecast_tab.py` - 24-hour planning and strategy
  - `about_tab.py` - App information and documentation
- **Smart Configuration**: Dynamic UI that shows only missing configuration items
- **Weather Integration**: Robust fallback system (AmbientWeather.net → Weather.gov) for current conditions
- **Decision Logic**: Feels-like temperature based blanketing with forecast integration
- **Smart Caching**: 1-minute cache for current weather, 30-minute for forecasts
- **Timezone Handling**: Browser-aware timestamp display with pytz integration

## Key Dependencies
```
streamlit>=1.30.0           # Core web framework
requests>=2.28.0            # HTTP client for weather API
python-dotenv>=0.19.0       # Environment variable management
pytz>=2021.1                # Timezone handling for timestamps
python-dateutil>=2.8.0      # Date parsing for forecast data
```

## Core Business Logic (`blanketing_logic.py`)

### Key Classes & Architecture:
- **`BlanktetingLogic`**: Main business logic class with static methods
- **`BlanktetingDecision`**: Data class for blanketing recommendation results
- **`HousingDecision`**: Data class for housing status determination results
- **`get_care_instructions_by_category()`**: Care instruction generation helper

### Critical Business Rules:
```python
# Temperature thresholds
THRESHOLDS_OUT = {'light': 50, 'medium': 40, 'heavy': 30}  # Horses OUT
THRESHOLDS_IN = {'light': 45, 'medium': 35, 'heavy': 25}   # Horses IN

# Heat index protection (only when temp > 75°F)
HEAT_INDEX_CLOUDY_THRESHOLD = 150
HEAT_INDEX_SUNNY_THRESHOLD = 120

# Rain protection
RAIN_CHANCE_THRESHOLD = 10  # Percentage

# Anti-overheating
TEMP_DROP_ALERT_THRESHOLD = 10  # °F
```

### Unit Testing (`test_blanketing_logic.py`):
- **20+ comprehensive test cases** covering all business logic
- **Housing status determination** tests (heat index, rain, edge cases)
- **Temperature threshold** boundary testing for OUT/IN scenarios
- **Anti-overheating logic** validation and step-down rules
- **Care instruction generation** testing
- **Edge cases and error conditions** coverage
- Run tests: `python3 test_blanketing_logic.py` or `./run_tests.sh`

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

## Unified Weather Service (`weather_service.py`)

### Core Functionality:
- **`get_current_weather_data()`**: Main function with automatic fallback mechanism
- **`get_weather_data_with_source_info()`**: Enhanced version with source descriptions
- **Fallback Logic**: AmbientWeather.net (primary) → Weather.gov (fallback)
- **Unified Data Format**: Consistent weather data structure regardless of source
- **Comprehensive Logging**: Detailed logging for troubleshooting weather service issues

### Fallback Behavior:
- **Primary Source**: AmbientWeather.net - Real-time personal weather station data
- **Fallback Source**: Weather.gov - Uses first forecast period as current conditions
- **Automatic Switching**: Seamless fallback when primary source fails
- **Source Indication**: Data includes 'source' field ('ambient' or 'weather_gov')
- **Error Aggregation**: Combined error messages when both sources fail

### Data Format:
```python
{
    'temperature': 72.5,           # Temperature in Fahrenheit
    'feels_like': 68.2,            # Feels-like temperature  
    'humidity': 65,                # Humidity percentage
    'station_name': 'Weather Station (MAC)', # Source description
    'last_update': '2026-02-17T...',  # ISO string (weather.gov) or ms (ambient)
    'source': 'weather_gov',       # Data source indicator
    'raw_data': {...},             # Original API response
    'location_info': {...}         # Location metadata (weather.gov only)
}
```

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

## Tab Module Architecture

### Main Tab (`main_tab.py`)
- **`render_main_tab(weather_data)`**: Primary blanketing instructions interface
- **Business Logic Integration**: Uses `BlanktetingLogic` class for all decisions
- **Housing Determination**: Automatic status based on weather conditions
- **Forecast Integration**: Phase-aware recommendations with timeline display
- **UI Components**: Metrics, alerts, recommendations using separated logic
- **User-Focused**: Core stable hand guidance without technical details
- **Weather-Dependent**: Real-time instructions based on current conditions

### Current Weather Tab (`current_weather_tab.py`)
- **`render_current_weather_tab(weather_data, error)`**: Live conditions display
- **`handle_device_selection_error()`**: Device configuration UI  
- **Source Indicators**: Shows data source (🏡 Personal Station vs 🏛️ NWS)
- **Metrics Display**: 4-column weather data with timestamps
- **Flexible Timestamp Handling**: Supports both millisecond (ambient) and ISO string (weather.gov) formats
- **Error Handling**: Rate limits, API failures, device selection
- **Timezone Display**: Browser-aware timestamp formatting

### Forecast Tab (`forecast_tab.py`)
- **`render_forecast_tab(latitude, longitude, get_forecast_data_func)`**: 24-hour planning
- **`display_forecast_period()`**: Helper for forecast period rendering
- **Location Resolution**: NWS grid point conversion and location display
- **Strategic Planning**: 24-hour blanketing recommendations
- **Time-Based Tabs**: 8-hour periods for detailed planning

### About Tab (`about_tab.py`)
- **`render_about_tab()`**: App information and documentation
- **Feature Overview**: Capabilities and technical specifications
- **Configuration Guide**: Environment variable requirements
- **Data Sources**: API details and refresh rates
- **Blanketing Guidelines**: Temperature thresholds and decision factors

## Streamlit App Patterns (`streamlit_app.py`)

### Page Configuration
```python
st.set_page_config(page_title="Stableman", page_icon="🐴")
```

### Configuration Integration
```python
from configuration import check_configuration, display_configuration_ui, get_location_coordinates
from weather_service import get_current_weather_data
from main_tab import render_main_tab
from current_weather_tab import render_current_weather_tab
from forecast_tab import render_forecast_tab
from about_tab import render_about_tab

missing_config = check_configuration()
if missing_config:
    display_configuration_ui(missing_config)  # Smart configuration UI
else:
    # Create four-tab interface
    tab1, tab2, tab3, tab4 = st.tabs(["🐴 Main", "🌤️ Current Weather", "📊 24-Hour Forecast", "ℹ️ About"])
    
    with tab1:
        render_main_tab(weather_data)
    with tab2:
        render_current_weather_tab(weather_data, error)
    with tab3:
        latitude, longitude = get_location_coordinates()
        render_forecast_tab(latitude, longitude, get_forecast_data)
    with tab4:
        render_about_tab()
```

### Weather Data Fetching
```python
@st.cache_data(ttl=60)  # 1-minute cache for weather data
def get_weather_data():
    """Fetch current weather data with automatic fallback"""
    return get_current_weather_data()  # Handles ambient → weather.gov fallback
```

### UI Layout
- **Four-Tab Structure**: Main | Current Weather | 24-Hour Forecast | About
- **Main Tab**: Blanketing instructions based on current temperature
- **Current Weather Tab**: 4-column metrics (Temperature | Feels Like | Humidity | Station)
- **Forecast Tab**: 3 sub-tabs for time periods (Next 8 Hours | 8-16 Hours | 16-24 Hours)
- **About Tab**: App features, configuration, data sources, and guidelines
- **6-Column Forecast Details**: Time | Temperature | Humidity | Wind | Rain | Conditions
- **Location Context**: City, state, coordinates with NWS office information
- **Human-Readable Timestamps**: "February 16, 2026 at 02:30 PM EST" + "5 minutes ago"
- **Dynamic Configuration UI**: Only shows missing required variables
- **Error Handling**: Specific UI for device selection, rate limits, and API errors

### Blanketing Logic
**See [`blanketing_rules.md`](./blanketing_rules.md) for complete, up-to-date blanketing guidelines.**

Key features:
- **Feels-like temperature** based decisions (not air temperature)
- **Forecast-aware logic** considering weather until next care phase
- **Anti-overheating priority** with smart category step-down
- **Phase-based timing**: Morning/Day/Night care cycles
- **Housing-aware thresholds**: Different rules for horses OUT vs IN
- **Animal-specific rules**: Horses vs donkeys

## Development Workflow

### Local Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
streamlit run streamlit_app.py
```

### Testing Business Logic
```bash
python3 test_blanketing_logic.py  # Unit tests for business logic
./run_tests.sh                    # Comprehensive test runner with coverage report
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
- **Business Logic Separation**: Pure logic in dedicated modules with comprehensive testing

## Common Tasks

### Modifying Blanketing Logic
1. **Update business logic**: Modify `blanketing_logic.py` functions
2. **Run tests**: Execute `./run_tests.sh` to ensure no regressions
3. **Update documentation**: Sync changes with `blanketing_rules.md`
4. **Test integration**: Verify UI integration in `main_tab.py`

### Adding New Unit Tests
1. Add test methods to `test_blanketing_logic.py`
2. Follow naming convention: `test_[functionality]_[scenario]`
3. Cover edge cases and boundary conditions
4. Run tests to verify they pass

### Adding New Tab Modules
1. Create new tab file (e.g., `new_tab.py`) with `render_new_tab()` function
2. Import module in `streamlit_app.py`
3. Add tab to `st.tabs()` list
4. Add `with tabN:` block calling render function

### Modifying Tab Content
1. Update specific tab module file (e.g., `main_tab.py`)
2. Modify render function within the module
3. No changes needed to main application file

### Adding New Configuration Variables
1. Update `get_required_variables()` in `configuration.py`
2. Add contextual help in `_display_contextual_help()`
3. Update environment variable documentation

### Adding Weather Data Fields
1. Update `ambient_weather.py` data structure in `get_latest_weather_data()`
2. Add UI display in `current_weather_tab.py` metrics section
3. Consider blanketing logic impact in `blanketing_logic.py`

### Adding Forecast Data Fields
1. Update `weather_gov.py` data parsing in `get_24_hour_forecast()`
2. Add display columns in `display_forecast_period()` function in `forecast_tab.py`
3. Consider strategic blanketing recommendations

### Modifying Cache Duration
- Current weather: Change `ttl=60` in `@st.cache_data(ttl=60)` decorator
- Forecast data: Change `ttl=1800` in forecast cache decorator

### API Rate Limit Tuning
Modify `rate_limit_delay` and `retry_delay` in `AmbientWeatherAPI` class

## External Integration
- **AmbientWeather.net API**: Real-time weather station data with device management (primary source)
- **Weather.gov API**: 24-hour forecasts with location resolution and current conditions fallback
- **Rate Limits**: 
  - AmbientWeather: 1 request/second per API key, 3 requests/second per developer key
  - Weather.gov: No explicit rate limits but respectful usage recommended
- **Fallback Strategy**: Automatic switching from personal station to NWS data when needed
- **Timezone Handling**: Always use Browser timezone detection via `timezone_utils.py`
- **Deployment**: Optimized for Streamlit Cloud with environment variable support

## File Structure
```
├── streamlit_app.py          # Main application orchestration with tab management
├── configuration.py          # Environment variable validation and configuration UI
├── weather_service.py        # Unified weather service with automatic fallback
├── ambient_weather.py        # AmbientWeather.net API client for current conditions
├── weather_gov.py            # Weather.gov API client for 24-hour forecasts
├── blanketing_logic.py       # Pure business logic for blanketing decisions
├── timezone_utils.py         # Browser timezone detection and formatting utilities
├── main_tab.py               # Blanketing instructions interface
├── current_weather_tab.py    # Real-time conditions display with source indicators
├── forecast_tab.py           # 24-hour planning and strategic recommendations
├── about_tab.py              # App information and documentation
├── test_blanketing_logic.py  # Unit tests for business logic (35 test cases)
├── test_weather_api.py       # Standalone API testing script
├── run_tests.sh              # Convenient test runner script
├── requirements.txt          # Python dependencies
├── .env                      # API keys and configuration (gitignored)
└── .github/copilot-instructions.md  # This file
└── .github/blanketing_rules.md      # Business rules documentation
```