"""
Blanketing Logic Module for Stableman Application

Contains all business logic for determining horse blanketing requirements
separate from UI components for easier testing and maintenance.
"""
from typing import Dict, List, Optional, Tuple, Any


class BlanktetingDecision:
    """Data class for blanketing recommendation results"""
    def __init__(
        self, 
        category: str, 
        housing_status: str, 
        effective_temp: float,
        current_temp: float,
        forecast_low: Optional[float] = None,
        has_temp_drop_alert: bool = False,
        temp_drop_amount: Optional[float] = None,
        step_down_applied: bool = False,
        reasoning: str = ""
    ):
        self.category = category  # 'none', 'light', 'medium', 'heavy'
        self.housing_status = housing_status  # 'Horses OUT', 'Horses IN'
        self.effective_temp = effective_temp
        self.current_temp = current_temp
        self.forecast_low = forecast_low
        self.has_temp_drop_alert = has_temp_drop_alert
        self.temp_drop_amount = temp_drop_amount
        self.step_down_applied = step_down_applied
        self.reasoning = reasoning


class HousingDecision:
    """Data class for housing status determination results"""
    def __init__(self, status: str, reason: str, user_selectable: bool):
        self.status = status  # 'Horses OUT', 'Horses IN'
        self.reason = reason
        self.user_selectable = user_selectable


class BlanktetingLogic:
    """Core blanketing business logic"""
    
    # Temperature thresholds for different housing situations
    THRESHOLDS_OUT = {'light': 50, 'medium': 40, 'heavy': 30}
    THRESHOLDS_IN = {'light': 45, 'medium': 35, 'heavy': 25}
    
    # Heat index thresholds
    HEAT_INDEX_CLOUDY_THRESHOLD = 150
    HEAT_INDEX_SUNNY_THRESHOLD = 120
    HEAT_INDEX_MIN_TEMP = 75  # Only apply heat index when temp > 75°F
    
    # Rain protection threshold
    RAIN_CHANCE_THRESHOLD = 10  # Percentage
    
    # Temperature drop alert threshold
    TEMP_DROP_ALERT_THRESHOLD = 10  # °F
    
    @classmethod
    def determine_housing_status(
        cls, 
        weather_data: Optional[Dict], 
        forecast_periods: List[Dict]
    ) -> HousingDecision:
        """
        Automatically determine housing status based on weather conditions.
        
        Rules:
        - If chance of rain > 10% - horses stay IN for duration + 12h if rained > 0.1in
        - Equine heat index = Temp °F + % Relative Humidity (only when temp > 75°F)
          - > 150 in consistently cloudy weather - horses stay IN for the day
          - > 120 in sunny weather - horses stay IN for the day
        - Otherwise - horses are OUT
        
        Args:
            weather_data: Current weather data
            forecast_periods: Forecast data periods
        
        Returns:
            HousingDecision object
        """
        if not weather_data:
            return HousingDecision("Horses OUT", "No weather data available", True)
        
        temp = weather_data.get('temperature')
        humidity = weather_data.get('humidity')
        
        # Calculate equine heat index if conditions are met
        if temp is not None and humidity is not None and temp > cls.HEAT_INDEX_MIN_TEMP:
            equine_heat_index = temp + humidity
            
            # Check forecast for cloudy conditions
            is_cloudy = cls._is_weather_cloudy(forecast_periods)
            
            # Apply heat index rules
            if is_cloudy and equine_heat_index > cls.HEAT_INDEX_CLOUDY_THRESHOLD:
                return HousingDecision(
                    "Horses IN", 
                    f"High heat index ({equine_heat_index:.0f}) in cloudy weather", 
                    False
                )
            elif not is_cloudy and equine_heat_index > cls.HEAT_INDEX_SUNNY_THRESHOLD:
                return HousingDecision(
                    "Horses IN", 
                    f"High heat index ({equine_heat_index:.0f}) in sunny weather", 
                    False
                )
        
        # Check for rain conditions in forecast
        rain_chance = cls._get_max_rain_chance(forecast_periods)
        if rain_chance > cls.RAIN_CHANCE_THRESHOLD:
            return HousingDecision(
                "Horses IN", 
                f"Rain expected ({rain_chance}% chance)", 
                False
            )
        
        # Default to horses OUT with user choice
        return HousingDecision("Horses OUT", "Good conditions for outdoor housing", True)
    
    @classmethod
    def get_blanket_category(cls, temp: float, housing_status: str) -> str:
        """
        Determine blanket category based on temperature and housing status.
        
        Args:
            temp: Feels-like temperature in Fahrenheit
            housing_status: 'Horses OUT' or 'Horses IN'
            
        Returns:
            Blanket category: 'none', 'light', 'medium', 'heavy'
        """
        thresholds = cls.THRESHOLDS_OUT if housing_status == "Horses OUT" else cls.THRESHOLDS_IN
        
        if temp >= thresholds['light']:
            return 'none'
        elif temp >= thresholds['medium']:
            return 'light'
        elif temp >= thresholds['heavy']:
            return 'medium'
        else:
            return 'heavy'
    
    @classmethod
    def make_blanketing_decision(
        cls,
        current_feels_like: float,
        min_forecast_feels_like: Optional[float],
        housing_status: str
    ) -> BlanktetingDecision:
        """
        Make comprehensive blanketing decision with anti-overheating logic.
        
        Args:
            current_feels_like: Current feels-like temperature
            min_forecast_feels_like: Minimum forecast feels-like temperature (can be None)
            housing_status: 'Horses OUT' or 'Horses IN'
            
        Returns:
            BlanktetingDecision object with complete recommendation
        """
        # Determine effective temperature for blanketing decision
        if min_forecast_feels_like is not None:
            effective_temp = min(current_feels_like, min_forecast_feels_like)
            forecast_available = True
        else:
            effective_temp = current_feels_like
            forecast_available = False
        
        # Get initial blanket categories
        current_category = cls.get_blanket_category(current_feels_like, housing_status)
        effective_category = cls.get_blanket_category(effective_temp, housing_status)
        
        # Initialize decision tracking
        has_temp_drop_alert = False
        temp_drop_amount = None
        step_down_applied = False
        reasoning = ""
        
        # Anti-overheating logic: if current is hot but forecast is cold, prefer lighter blanketing
        if forecast_available and current_feels_like > effective_temp:
            temp_drop_amount = current_feels_like - effective_temp
            if temp_drop_amount >= cls.TEMP_DROP_ALERT_THRESHOLD:
                has_temp_drop_alert = True
                reasoning = "Temperature drop detected"
                
                # Check if we should step down blanket category to prevent overheating
                if effective_category in ['medium', 'heavy'] and current_category in ['none', 'light']:
                    reasoning += " - stepped down blanket weight to prevent overheating"
                    step_down_applied = True
                    
                    # Step down one category to prevent overheating
                    if effective_category == 'heavy':
                        effective_category = 'medium'
                    elif effective_category == 'medium':
                        effective_category = 'light'
        
        return BlanktetingDecision(
            category=effective_category,
            housing_status=housing_status,
            effective_temp=effective_temp,
            current_temp=current_feels_like,
            forecast_low=min_forecast_feels_like,
            has_temp_drop_alert=has_temp_drop_alert,
            temp_drop_amount=temp_drop_amount,
            step_down_applied=step_down_applied,
            reasoning=reasoning
        )
    
    @classmethod
    def _is_weather_cloudy(cls, forecast_periods: List[Dict]) -> bool:
        """
        Determine if weather is consistently cloudy based on forecast periods.
        
        Args:
            forecast_periods: List of forecast period dictionaries
            
        Returns:
            True if weather is consistently cloudy, False if sunny
        """
        if not forecast_periods:
            return False  # Default to sunny if no forecast data
        
        cloudy_periods = 0
        total_periods = 0
        
        for period in forecast_periods[:4]:  # Check next 4 periods
            forecast = period.get('short_forecast', '').lower()
            if 'cloud' in forecast or 'overcast' in forecast or 'partly' in forecast:
                cloudy_periods += 1
            total_periods += 1
        
        if total_periods > 0:
            return cloudy_periods / total_periods > 0.5
        return False
    
    @classmethod
    def _get_max_rain_chance(cls, forecast_periods: List[Dict]) -> int:
        """
        Get the maximum rain chance from forecast periods.
        
        Args:
            forecast_periods: List of forecast period dictionaries
            
        Returns:
            Maximum precipitation chance percentage
        """
        max_rain_chance = 0
        for period in forecast_periods:
            rain_chance = period.get('precipitation_chance', 0)
            if rain_chance and rain_chance > max_rain_chance:
                max_rain_chance = rain_chance
        return max_rain_chance


def get_care_instructions_by_category(category: str, housing_status: str) -> Dict[str, Any]:
    """
    Get care instructions for a specific blanket category.
    
    Args:
        category: Blanket category ('none', 'light', 'medium', 'heavy')
        housing_status: Housing status ('Horses OUT', 'Horses IN')
        
    Returns:
        Dictionary with care instructions
    """
    instructions = {
        'none': {
            'title': 'No Blanket Needed',
            'emoji': '☀️',
            'color': 'success',
            'horses': 'No blanketing required',
            'donkeys': 'No blanketing required',
            'care_notes': [
                'Ensure adequate shade and water' if housing_status == "Horses OUT" 
                else 'Ensure adequate ventilation in barn'
            ]
        },
        'light': {
            'title': 'Light Blanketing',
            'emoji': '🧸',
            'color': 'info',
            'horses': 'Turnout sheet without neck piece',
            'donkeys': 'No blanketing required',
            'care_notes': ['Monitor for comfort and proper fit']
        },
        'medium': {
            'title': 'Medium Blanketing',
            'emoji': '🧥',
            'color': 'warning',
            'horses': 'Fleece sheet + turnout sheet with neck piece over it',
            'donkeys': 'No blanketing required',
            'care_notes': ['Check layering is secure and comfortable']
        },
        'heavy': {
            'title': 'Heavy Blanketing',
            'emoji': '🥶',
            'color': 'error',
            'horses': 'Weighted blanket with neck piece + turnout sheet without neck piece over it',
            'donkeys': 'Weighted blanket',
            'care_notes': [
                'Check animals hourly for signs of cold stress',
                'Ensure adequate shelter and windbreak' if housing_status == "Horses OUT" 
                else 'Monitor closely even in barn environment'
            ]
        }
    }
    
    return instructions.get(category, instructions['none'])