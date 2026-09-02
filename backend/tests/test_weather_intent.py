import os
import sys
import unittest

# Add backend root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.routes.ai import detect_weather_intent

class TestWeatherIntent(unittest.TestCase):
    
    def test_detect_weather_intent_with_today(self):
        # Queries with today/now/tomorrow/yesterday/live should trigger weather intent
        has_weather, has_rainfall_only = detect_weather_intent("what is the rain fall in konaseema today")
        self.assertTrue(has_weather)
        self.assertFalse(has_rainfall_only)

        has_weather_tomorrow, has_rainfall_only_tomorrow = detect_weather_intent("will there be rain in guntur tomorrow")
        self.assertTrue(has_weather_tomorrow)
        self.assertFalse(has_rainfall_only_tomorrow)

        has_weather_yesterday, has_rainfall_only_yesterday = detect_weather_intent("what was the precipitation in hapur yesterday")
        self.assertTrue(has_weather_yesterday)
        self.assertFalse(has_rainfall_only_yesterday)

    def test_detect_weather_intent_historical_only(self):
        # Plain rainfall query (no live indicators) should be historical only
        has_weather, has_rainfall_only = detect_weather_intent("what is the rain fall in konaseema")
        self.assertFalse(has_weather)
        self.assertTrue(has_rainfall_only)

        has_weather_dist, has_rainfall_only_dist = detect_weather_intent("annual rainfall in nellore")
        self.assertFalse(has_weather_dist)
        self.assertTrue(has_rainfall_only_dist)

    def test_combined_query_keyword_exclusion(self):
        # Simulate combined query logic to ensure rainfall/rain alone doesn't trigger combined groundwater view
        groundwater_terms = [
            "groundwater", "water level", "depth", "recharge", "extraction", "stage",
            "status", "assessment", "category"
        ]
        
        def mock_is_combined_query(query_lower: str, is_weather_query: bool) -> bool:
            return is_weather_query and any(x in query_lower for x in groundwater_terms)

        # 1. Pure weather rainfall queries should not be combined
        self.assertFalse(mock_is_combined_query("what is the rain fall in konaseema today", is_weather_query=True))
        self.assertFalse(mock_is_combined_query("is it raining tomorrow in guntur", is_weather_query=True))

        # 2. Queries mixing weather with groundwater terms should be combined
        self.assertTrue(mock_is_combined_query("what is the groundwater level and rain fall today in guntur", is_weather_query=True))
        self.assertTrue(mock_is_combined_query("what is the depth to water level and weather in nellore tomorrow", is_weather_query=True))

if __name__ == "__main__":
    unittest.main()
