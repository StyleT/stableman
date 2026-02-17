# Stableman - Copilot Instructions 🐴

## Project Overview
Stableman is a Streamlit web application that provides horse blanketing instructions to stable hands based on weather conditions and established care guidelines. The app integrates with AmbientWeather.net API to deliver real-time, condition-specific blanketing recommendations with intelligent caching and rate limiting.

## Architecture & Structure
- **Single-file UI**: Main app logic in `streamlit_app.py`
- **Separate API Module**: Weather API client in `ambient_weather.py` for reusability
- **Weather Integration**: Real-time data from AmbientWeather.net with retry logic and rate limiting
- **Decision Logic**: Temperature-based horse blanketing guidelines (20°F/40°F/60°F thresholds)
- **Smart Caching**: 1-minute cache TTL to balance freshness with API rate limits
- **MAC Address Optimization**: Direct device access when configured, avoiding device enumeration

## Key Dependencies
```
streamlit>=1.30.0           # Core web framework
requests>=2.28.0            # HTTP client for weather API
python-dotenv>=0.19.0       # Environment variable management
pytz>=2021.1                # Timezone handling for timestamps
```

## Environment Configuration
Required environment variables in `.env` file:
```bash
AMBIENT_API_KEY=<your_api_key>          # Required: AmbientWeather.net API key
AMBIENT_APP_KEY=<your_application_key>   # Required: AmbientWeather.net app key
AMBIENT_MAC_ADDRESS=<device_mac>         # Optional but recommended for performance
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

## Streamlit App Patterns (`streamlit_app.py`)

### Page Configuration
```python
st.set_page_config(page_title="Stableman", page_icon="🐴")
```

### Caching Strategy
```python
@st.cache_data(ttl=60)  # 1-minute cache for weather data
```

### UI Layout
- **4-Column Metrics**: Temperature | Feels Like | Humidity | Station
- **Human-Readable Timestamps**: "February 16, 2026 at 02:30 PM UTC" + "5 minutes ago"
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

### Adding Weather Data Fields
1. Update `ambient_weather.py` data structure in `get_latest_weather_data()`
2. Add UI display in `streamlit_app.py` metrics section
3. Consider blanketing logic impact

### Modifying Cache Duration
Change `ttl=60` in `@st.cache_data(ttl=60)` decorator

### Adding Blanketing Rules
Update temperature threshold logic in blanketing instructions section

### API Rate Limit Tuning
Modify `rate_limit_delay` and `retry_delay` in `AmbientWeatherAPI` class

## External Integration
- **AmbientWeather.net API**: Real-time weather station data
- **Rate Limits**: 1 request/second per API key, 3 requests/second per developer key
- **Deployment**: Optimized for Streamlit Cloud with environment variable support

## File Structure
```
├── streamlit_app.py          # Main UI application
├── ambient_weather.py        # Reusable weather API client
├── test_weather_api.py       # Standalone API testing
├── requirements.txt          # Python dependencies
├── .env                      # API keys and configuration (gitignored)
└── .github/copilot-instructions.md  # This file
```