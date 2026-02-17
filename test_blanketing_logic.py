"""
Unit tests for blanketing logic module.

Ensures that blanketing decisions remain consistent and correct
across future modifications to the algorithm.
"""
import unittest
from blanketing_logic import BlanktetingLogic, HousingDecision, BlanktetingDecision, get_care_instructions_by_category


class TestHousingStatusDetermination(unittest.TestCase):
    """Test housing status determination logic"""
    
    def test_no_weather_data_returns_out_with_user_choice(self):
        """Test that missing weather data defaults to horses OUT with user choice"""
        decision = BlanktetingLogic.determine_housing_status(None, [])
        self.assertEqual(decision.status, "Horses OUT")
        self.assertTrue(decision.user_selectable)
        self.assertIn("No weather data", decision.reason)
    
    def test_rain_chance_above_threshold_forces_horses_in(self):
        """Test that rain chance > 10% forces horses IN"""
        weather_data = {'temperature': 70, 'humidity': 50}
        forecast_periods = [
            {'precipitation_chance': 15, 'short_forecast': 'Scattered Showers'}
        ]
        
        decision = BlanktetingLogic.determine_housing_status(weather_data, forecast_periods)
        self.assertEqual(decision.status, "Horses IN")
        self.assertFalse(decision.user_selectable)
        self.assertIn("Rain expected (15% chance)", decision.reason)
    
    def test_rain_chance_at_threshold_forces_horses_in(self):
        """Test edge case: rain chance exactly at 10% threshold"""
        weather_data = {'temperature': 70, 'humidity': 50}
        forecast_periods = [
            {'precipitation_chance': 10, 'short_forecast': 'Slight chance of rain'}
        ]
        
        decision = BlanktetingLogic.determine_housing_status(weather_data, forecast_periods)
        # Should NOT force horses in at exactly 10%
        self.assertEqual(decision.status, "Horses OUT")
        self.assertTrue(decision.user_selectable)
    
    def test_heat_index_not_applied_when_temp_below_75(self):
        """Test that heat index rules don't apply when temperature <= 75°F"""
        weather_data = {'temperature': 74, 'humidity': 80}  # Would be heat index 154
        forecast_periods = []
        
        decision = BlanktetingLogic.determine_housing_status(weather_data, forecast_periods)
        self.assertEqual(decision.status, "Horses OUT")
        self.assertTrue(decision.user_selectable)
    
    def test_heat_index_cloudy_weather_forces_horses_in(self):
        """Test heat index > 150 in cloudy weather forces horses IN"""
        weather_data = {'temperature': 80, 'humidity': 75}  # Heat index 155
        forecast_periods = [
            {'short_forecast': 'Mostly Cloudy'},
            {'short_forecast': 'Overcast'},
            {'short_forecast': 'Partly Cloudy'},
            {'short_forecast': 'Cloudy'}
        ]
        
        decision = BlanktetingLogic.determine_housing_status(weather_data, forecast_periods)
        self.assertEqual(decision.status, "Horses IN")
        self.assertFalse(decision.user_selectable)
        self.assertIn("High heat index (155) in cloudy weather", decision.reason)
    
    def test_heat_index_sunny_weather_forces_horses_in(self):
        """Test heat index > 120 in sunny weather forces horses IN"""
        weather_data = {'temperature': 76, 'humidity': 50}  # Heat index 126
        forecast_periods = [
            {'short_forecast': 'Sunny'},
            {'short_forecast': 'Clear'},
            {'short_forecast': 'Fair'},
            {'short_forecast': 'Sunny'}
        ]
        
        decision = BlanktetingLogic.determine_housing_status(weather_data, forecast_periods)
        self.assertEqual(decision.status, "Horses IN")
        self.assertFalse(decision.user_selectable)
        self.assertIn("High heat index (126) in sunny weather", decision.reason)
    
    def test_heat_index_edge_cases(self):
        """Test heat index edge cases at thresholds"""
        # Exactly at sunny threshold (should NOT trigger)
        weather_data = {'temperature': 76, 'humidity': 44}  # Heat index exactly 120
        forecast_periods = [{'short_forecast': 'Sunny'}]
        
        decision = BlanktetingLogic.determine_housing_status(weather_data, forecast_periods)
        self.assertEqual(decision.status, "Horses OUT")
        self.assertTrue(decision.user_selectable)
    
    def test_good_conditions_allows_user_choice(self):
        """Test that good conditions default to horses OUT with user choice"""
        weather_data = {'temperature': 70, 'humidity': 50}
        forecast_periods = [
            {'precipitation_chance': 5, 'short_forecast': 'Sunny'}
        ]
        
        decision = BlanktetingLogic.determine_housing_status(weather_data, forecast_periods)
        self.assertEqual(decision.status, "Horses OUT")
        self.assertTrue(decision.user_selectable)
        self.assertIn("Good conditions", decision.reason)


class TestBlankeetingDecisions(unittest.TestCase):
    """Test blanketing category determination logic"""
    
    def test_horses_out_temperature_thresholds(self):
        """Test temperature thresholds for horses OUT"""
        # Above light threshold
        self.assertEqual(BlanktetingLogic.get_blanket_category(55, "Horses OUT"), 'none')
        
        # At light threshold
        self.assertEqual(BlanktetingLogic.get_blanket_category(50, "Horses OUT"), 'none')
        
        # Light range
        self.assertEqual(BlanktetingLogic.get_blanket_category(45, "Horses OUT"), 'light')
        self.assertEqual(BlanktetingLogic.get_blanket_category(40, "Horses OUT"), 'light')
        
        # Medium range
        self.assertEqual(BlanktetingLogic.get_blanket_category(35, "Horses OUT"), 'medium')
        self.assertEqual(BlanktetingLogic.get_blanket_category(30, "Horses OUT"), 'medium')
        
        # Heavy (below 30)
        self.assertEqual(BlanktetingLogic.get_blanket_category(25, "Horses OUT"), 'heavy')
        self.assertEqual(BlanktetingLogic.get_blanket_category(15, "Horses OUT"), 'heavy')
    
    def test_horses_in_temperature_thresholds(self):
        """Test temperature thresholds for horses IN"""
        # Above light threshold
        self.assertEqual(BlanktetingLogic.get_blanket_category(50, "Horses IN"), 'none')
        self.assertEqual(BlanktetingLogic.get_blanket_category(45, "Horses IN"), 'none')
        
        # Light range
        self.assertEqual(BlanktetingLogic.get_blanket_category(40, "Horses IN"), 'light')
        self.assertEqual(BlanktetingLogic.get_blanket_category(35, "Horses IN"), 'light')
        
        # Medium range
        self.assertEqual(BlanktetingLogic.get_blanket_category(30, "Horses IN"), 'medium')
        self.assertEqual(BlanktetingLogic.get_blanket_category(25, "Horses IN"), 'medium')
        
        # Heavy (below 25)
        self.assertEqual(BlanktetingLogic.get_blanket_category(20, "Horses IN"), 'heavy')
        self.assertEqual(BlanktetingLogic.get_blanket_category(10, "Horses IN"), 'heavy')
    
    def test_blanketing_decision_without_forecast(self):
        """Test blanketing decision when forecast is unavailable"""
        decision = BlanktetingLogic.make_blanketing_decision(35, None, "Horses OUT")
        
        self.assertEqual(decision.category, 'medium')
        self.assertEqual(decision.housing_status, "Horses OUT")
        self.assertEqual(decision.effective_temp, 35)
        self.assertEqual(decision.current_temp, 35)
        self.assertIsNone(decision.forecast_low)
        self.assertFalse(decision.has_temp_drop_alert)
    
    def test_blanketing_decision_with_forecast_no_drop(self):
        """Test blanketing decision when forecast doesn't drop significantly"""
        decision = BlanktetingLogic.make_blanketing_decision(40, 38, "Horses OUT")
        
        self.assertEqual(decision.category, 'medium')  # Based on forecast low (38)
        self.assertEqual(decision.effective_temp, 38)
        self.assertEqual(decision.forecast_low, 38)
        self.assertFalse(decision.has_temp_drop_alert)  # Drop is only 2 degrees
    
    def test_anti_overheating_logic_with_significant_drop(self):
        """Test anti-overheating logic when temperature drop >= 10°F"""
        # Current is warm (light blanket), forecast is cold (would need heavy)
        decision = BlanktetingLogic.make_blanketing_decision(48, 25, "Horses OUT")
        
        self.assertTrue(decision.has_temp_drop_alert)
        self.assertEqual(decision.temp_drop_amount, 23)  # 48 - 25
        self.assertTrue(decision.step_down_applied)
        self.assertEqual(decision.category, 'medium')  # Stepped down from heavy
        self.assertIn("stepped down blanket weight", decision.reasoning)
    
    def test_anti_overheating_step_down_medium_to_light(self):
        """Test stepping down from medium to light category"""
        # Current needs light, forecast would need medium, but step down applied
        decision = BlanktetingLogic.make_blanketing_decision(45, 32, "Horses OUT")
        
        self.assertTrue(decision.step_down_applied)
        self.assertEqual(decision.category, 'light')  # Stepped down from medium
    
    def test_no_step_down_when_not_needed(self):
        """Test that step-down logic doesn't apply when not needed"""
        # Both current and forecast need heavy blanketing
        decision = BlanktetingLogic.make_blanketing_decision(25, 15, "Horses OUT")
        
        self.assertTrue(decision.has_temp_drop_alert)  # Drop is 10°F
        self.assertFalse(decision.step_down_applied)  # Both current and forecast need heavy
        self.assertEqual(decision.category, 'heavy')


class TestCareInstructions(unittest.TestCase):
    """Test care instruction generation"""
    
    def test_care_instructions_structure(self):
        """Test that care instructions have proper structure"""
        instructions = get_care_instructions_by_category('medium', 'Horses OUT')
        
        required_keys = ['title', 'emoji', 'color', 'horses', 'donkeys', 'care_notes']
        for key in required_keys:
            self.assertIn(key, instructions)
        
        self.assertIsInstance(instructions['care_notes'], list)
    
    def test_different_care_notes_for_housing_status(self):
        """Test that care notes differ based on housing status"""
        heavy_out = get_care_instructions_by_category('heavy', 'Horses OUT')
        heavy_in = get_care_instructions_by_category('heavy', 'Horses IN')
        
        # Should have different care notes for OUT vs IN
        self.assertNotEqual(heavy_out['care_notes'], heavy_in['care_notes'])
        
        # OUT should mention shelter and windbreak
        out_text = ' '.join(heavy_out['care_notes'])
        self.assertIn('shelter', out_text.lower())
        
        # IN should mention barn monitoring
        in_text = ' '.join(heavy_in['care_notes'])
        self.assertIn('barn', in_text.lower())
    
    def test_invalid_category_defaults_to_none(self):
        """Test that invalid category defaults to 'none' instructions"""
        invalid = get_care_instructions_by_category('invalid', 'Horses OUT')
        valid_none = get_care_instructions_by_category('none', 'Horses OUT')
        
        self.assertEqual(invalid, valid_none)


class TestHelperMethods(unittest.TestCase):
    """Test internal helper methods"""
    
    def test_is_weather_cloudy_detection(self):
        """Test cloudy weather detection logic"""
        cloudy_periods = [
            {'short_forecast': 'Mostly Cloudy'},
            {'short_forecast': 'Overcast'},
            {'short_forecast': 'Partly Sunny'},
            {'short_forecast': 'Cloudy'}
        ]
        
        self.assertTrue(BlanktetingLogic._is_weather_cloudy(cloudy_periods))
        
        sunny_periods = [
            {'short_forecast': 'Sunny'},
            {'short_forecast': 'Clear'},
            {'short_forecast': 'Fair'},
            {'short_forecast': 'Sunny'}
        ]
        
        self.assertFalse(BlanktetingLogic._is_weather_cloudy(sunny_periods))
        
        # Mixed weather - should be False since < 50% cloudy
        mixed_periods = [
            {'short_forecast': 'Sunny'},
            {'short_forecast': 'Cloudy'},
            {'short_forecast': 'Clear'},
            {'short_forecast': 'Fair'}
        ]
        
        self.assertFalse(BlanktetingLogic._is_weather_cloudy(mixed_periods))
    
    def test_get_max_rain_chance(self):
        """Test maximum rain chance extraction"""
        forecast_periods = [
            {'precipitation_chance': 5},
            {'precipitation_chance': 15},
            {'precipitation_chance': 8},
            {'precipitation_chance': 22}
        ]
        
        max_chance = BlanktetingLogic._get_max_rain_chance(forecast_periods)
        self.assertEqual(max_chance, 22)
        
        # Test with no precipitation data
        no_rain_periods = [
            {'short_forecast': 'Sunny'},
            {'other_field': 'value'}
        ]
        
        max_chance = BlanktetingLogic._get_max_rain_chance(no_rain_periods)
        self.assertEqual(max_chance, 0)


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)