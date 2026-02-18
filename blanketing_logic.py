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
    
    @staticmethod
    def temperature_to_blanketing_score(feels_like_temp: float, housing_status: str) -> int:
        """
        Convert a temperature to a blanketing score (0-3).
        
        Args:
            feels_like_temp: Feels-like temperature in Fahrenheit
            housing_status: 'Horses OUT' or 'Horses IN'
            
        Returns:
            int: Blanketing score (0=none, 1=light, 2=medium, 3=heavy)
        """
        # Use appropriate thresholds based on housing status
        if 'OUT' in housing_status:
            thresholds = BlanktetingLogic.THRESHOLDS_OUT
        else:
            thresholds = BlanktetingLogic.THRESHOLDS_IN
        
        if feels_like_temp >= thresholds['light']:
            return 0  # No blanket
        elif feels_like_temp >= thresholds['medium']:
            return 1  # Light
        elif feels_like_temp >= thresholds['heavy']:
            return 2  # Medium
        else:
            return 3  # Heavy
    
    @staticmethod
    def blanketing_score_to_category(score: float) -> str:
        """
        Convert an averaged blanketing score to a category.
        
        Args:
            score: Averaged blanketing score (0.0-3.0)
            
        Returns:
            str: Blanketing category ('none', 'light', 'medium', 'heavy')
        """
        if score < 0.5:
            return 'none'
        elif score < 1.5:
            return 'light'
        elif score < 2.5:
            return 'medium'
        else:
            return 'heavy'
    
    @staticmethod
    def analyze_forecast_temperatures(forecast_periods: List[Dict], housing_status: str) -> Tuple[float, str, List[Dict]]:
        """
        Analyze forecast temperatures using hourly averaging approach.
        
        Args:
            forecast_periods: List of forecast period dictionaries
            housing_status: Current housing status
            
        Returns:
            tuple: (average_score, recommended_category, period_analysis)
        """
        if not forecast_periods:
            return 0.0, 'none', []
        
        period_analysis = []
        scores = []
        
        for period in forecast_periods:
            feels_like = period.get('feels_like')
            if feels_like is not None:
                score = BlanktetingLogic.temperature_to_blanketing_score(feels_like, housing_status)
                category = BlanktetingLogic.blanketing_score_to_category(score)
                
                period_analysis.append({
                    'time': period.get('time', 'Unknown'),
                    'name': period.get('name', ''),
                    'feels_like': feels_like,
                    'score': score,
                    'category': category,
                    'short_forecast': period.get('short_forecast', '')
                })
                
                scores.append(score)
        
        # Calculate average score
        if scores:
            average_score = sum(scores) / len(scores)
            recommended_category = BlanktetingLogic.blanketing_score_to_category(average_score)
        else:
            average_score = 0.0
            recommended_category = 'none'
        
        return average_score, recommended_category, period_analysis
    
    @classmethod
    def make_blanketing_decision(
        cls,
        current_feels_like: float,
        min_forecast_feels_like: Optional[float],
        housing_status: str,
        forecast_periods: Optional[List[Dict]] = None
    ) -> BlanktetingDecision:
        """
        Make a blanketing decision based on current temperature and forecast analysis.
        
        Args:
            current_feels_like: Current feels-like temperature
            min_forecast_feels_like: Minimum forecast feels-like (for backward compatibility)
            housing_status: Housing status ('Horses OUT' or 'Horses IN')
            forecast_periods: Optional list of forecast periods for improved analysis
            
        Returns:
            BlanktetingDecision object with recommendation details
        """
        # Use improved forecast analysis if periods are available
        if forecast_periods and len(forecast_periods) > 0:
            # Get current temperature recommendation
            current_score = cls.temperature_to_blanketing_score(
                current_feels_like, housing_status
            )
            current_category = cls.blanketing_score_to_category(current_score)
            
            # Analyze forecast temperatures
            avg_forecast_score, forecast_category, period_analysis = cls.analyze_forecast_temperatures(
                forecast_periods, housing_status
            )
            
            # Combine current and forecast analysis
            # Weight current conditions at 30% and forecast at 70%
            combined_score = ((current_score * 0.3) + (avg_forecast_score * 0.7)) / 2  # Normalize to 0-3 scale
            recommended_category = cls.blanketing_score_to_category(combined_score)
            
            # Check for temperature drop alert (significant change from current to forecast)
            temp_drop_alert = False
            step_down_applied = False
            temp_drop_amount = None
            
            if min_forecast_feels_like is not None:
                temp_drop_amount = current_feels_like - min_forecast_feels_like
                if temp_drop_amount >= cls.TEMP_DROP_ALERT_THRESHOLD:
                    temp_drop_alert = True
                    
                    # Apply step-down logic for anti-overheating
                    if recommended_category == 'heavy':
                        recommended_category = 'medium'
                        step_down_applied = True
                    elif recommended_category == 'medium':
                        recommended_category = 'light'
                        step_down_applied = True
            
            # Calculate effective temperature (for display purposes)
            if avg_forecast_score > 0:
                # Use a weighted average for effective temperature display
                effective_temp = min(current_feels_like, min_forecast_feels_like or current_feels_like)
            else:
                effective_temp = current_feels_like
            
            reasoning = f"Hourly analysis: Current {current_category} ({current_score}), Forecast avg {forecast_category} ({avg_forecast_score:.1f}), Combined {recommended_category} ({combined_score:.1f})"
            
            return BlanktetingDecision(
                category=recommended_category,
                housing_status=housing_status,
                effective_temp=effective_temp,
                current_temp=current_feels_like,
                forecast_low=min_forecast_feels_like,
                has_temp_drop_alert=temp_drop_alert,
                temp_drop_amount=temp_drop_amount,
                step_down_applied=step_down_applied,
                reasoning=reasoning
            )
        
        # Fallback to original logic if no forecast periods available
        else:
            return cls._make_legacy_blanketing_decision(
                current_feels_like, min_forecast_feels_like, housing_status
            )
    
    @classmethod
    def _make_legacy_blanketing_decision(
        cls,
        current_feels_like: float,
        min_forecast_feels_like: Optional[float],
        housing_status: str
    ) -> BlanktetingDecision:
        """
        Legacy blanketing decision logic (minimum temperature approach).
        
        Args:
            current_feels_like: Current feels-like temperature
            min_forecast_feels_like: Minimum forecast feels-like temperature
            housing_status: Housing status ('Horses OUT' or 'Horses IN')
            
        Returns:
            BlanktetingDecision object with recommendation details
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
    
    @staticmethod
    def get_current_phase(user_timezone=None):
        """
        Determine the current blanketing phase based on time of day in user's timezone.
        
        Args:
            user_timezone: pytz timezone object for user's timezone. If None, uses server timezone.
            
        Returns:
            str: Phase name ('Morning', 'Day', 'Night')
        """
        from datetime import datetime
        import pytz
        
        if user_timezone:
            # Get current time in user's timezone
            utc_now = datetime.now(pytz.UTC)
            now = utc_now.astimezone(user_timezone)
        else:
            # Fallback to server timezone
            now = datetime.now()
            
        current_hour = now.hour
        current_minute = now.minute
        
        # Convert current time to minutes since midnight for easier comparison
        current_time_minutes = current_hour * 60 + current_minute
        
        # Phase boundaries in minutes since midnight
        morning_start = 4 * 60 + 30  # 4:30 AM
        day_start = 11 * 60  # 11:00 AM
        evening_start = 15 * 60 + 50  # 3:50 PM
        
        if current_time_minutes < morning_start:
            return "Night"  # Midnight to 4:30 AM
        elif current_time_minutes < day_start:
            return "Morning"  # 4:30 AM to 11:00 AM
        elif current_time_minutes < evening_start:
            return "Day"  # 11:00 AM to 3:50 PM
        else:
            return "Night"  # 3:50 PM to midnight
    
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
            # Defensive programming: ensure period is a dictionary
            if not isinstance(period, dict):
                continue
            rain_chance = period.get('precipitation_chance', 0)
            if rain_chance and rain_chance > max_rain_chance:
                max_rain_chance = rain_chance
        return max_rain_chance


    @staticmethod
    def get_next_phase_forecast(target_phase, latitude, longitude, user_timezone=None):
        """
        Get forecast data until the end of a specific target phase.
        
        Args:
            target_phase: Target phase name ('Morning', 'Day', 'Night') to get forecast until
            latitude: Location latitude
            longitude: Location longitude
            user_timezone: User's timezone object for accurate time calculations
        
        Returns:
            tuple: (forecast_periods, next_phase_time)
        """
        try:
            from weather_gov import create_weather_gov_client
            from datetime import datetime, timedelta
            from dateutil import parser
            
            weather_client = create_weather_gov_client()
            forecast_data, error = weather_client.get_24_hour_forecast(latitude, longitude)
            
            if error or not forecast_data:
                return [], None
            
            forecast_periods = forecast_data.get('forecast', [])
            
            # Use user timezone for time calculations
            if user_timezone:
                import pytz
                utc_now = datetime.now(pytz.UTC)
                now = utc_now.astimezone(user_timezone)
            else:
                now = datetime.now()
            
            # Determine target phase end timing
            if target_phase == 'Morning':
                # Morning phase ends at 11:00 AM
                next_phase_time = now.replace(hour=11, minute=0, second=0, microsecond=0)
                if now.hour >= 11:
                    next_phase_time += timedelta(days=1)  # Next day if already past 11 AM
            elif target_phase == 'Day':
                # Day phase ends at 3:50 PM
                next_phase_time = now.replace(hour=15, minute=50, second=0, microsecond=0)
                if now.hour >= 15 and now.minute >= 50:
                    next_phase_time += timedelta(days=1)  # Next day if already past 3:50 PM
            elif target_phase == 'Night':
                # For Night phase targeting: go until midnight (stable hands re-blanket late, not early morning)
                next_phase_time = now.replace(hour=23, minute=59, second=59, microsecond=0)
            else:
                # Default behavior for unknown phases
                next_phase_time = now.replace(hour=11, minute=0, second=0, microsecond=0) + timedelta(days=1)
            
            # Filter forecast periods until next phase
            relevant_periods = []
            min_feels_like = float('inf')
            
            # Make next_phase_time naive for comparison with forecast periods
            comparison_time = next_phase_time.replace(tzinfo=None) if next_phase_time.tzinfo else next_phase_time
            
            for period in forecast_periods:
                if not period.get('time'):
                    continue
                    
                try:
                    period_time = parser.parse(period['time'])
                    # Convert to naive datetime for comparison
                    if period_time.tzinfo:
                        period_time = period_time.replace(tzinfo=None)
                    
                    if period_time <= comparison_time:
                        relevant_periods.append(period)
                        if period.get('feels_like') is not None:
                            min_feels_like = min(min_feels_like, period['feels_like'])
                except:
                    continue
            
            return relevant_periods, next_phase_time
            
        except Exception as e:
            # Don't use streamlit here since this is pure business logic
            return [], None

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