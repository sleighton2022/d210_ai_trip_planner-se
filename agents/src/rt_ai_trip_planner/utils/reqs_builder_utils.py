from textwrap import dedent

from ..model import UserPreference


class TripRequirementsBuilderUtils:
    def __init__(self, user_preference: UserPreference):
        self.user_preference = user_preference

    def activity_requirements(self):
        requirements = []
        self._interests(requirements)
        self._by_family_friendly(requirements)
        self._by_safety(requirements)
        self._by_cost(requirements)
        self._min_rating(requirements)
        return ('\n'.join(map(str, requirements)))
    
    def restaurant_requirements(self):
        requirements = []
        self._by_family_friendly(requirements)
        self._by_safety(requirements)
        self._by_cost(requirements)
        self._min_rating(requirements)
        return ('\n'.join(map(str, requirements)))    
    
    def traffic_requirements(self):
        requirements = []
        self._by_traffic(requirements)
        return ('\n'.join(map(str, requirements)))
    
    def weather_requirements(self):
        requirements = []
        self._by_weather(requirements)        
        return ('\n'.join(map(str, requirements)))
    
    def _interests(self, requirements: list):
        if self.user_preference.interests:
            requirements.append(
                dedent(f"""
                    - Choose only activities that align with the traveler's interests: {', '.join(self.user_preference.interests)}.
                """).strip())

    def _by_family_friendly(self, requirements: list):
        if self.user_preference.optimization_options.by_family_friendly:
            requirements.append(
                dedent(f"""
                    - Ensure all activities are family-friendly.
                """).strip())

    def _by_safety(self, requirements: list):
        if self.user_preference.optimization_options.by_safety:
            requirements.append(
                dedent(f"""
                    - Ensure all activities are safe.
                """).strip())

    def _by_cost(self, requirements: list):
        if self.user_preference.optimization_options.by_cost:
            requirements.append(
                dedent(f"""
                    - Ensure all activities are cost-friendly.
                """).strip())

    def _min_rating(self, requirements: list):
        if self.user_preference.optimization_options.min_rating:
            requirements.append(
                dedent(f"""
                    - Ensure all activities are above {self.user_preference.optimization_options.min_rating} stars.
                """).strip())
    
    def _by_traffic(self, requirements: list):
        if self.user_preference.optimization_options.by_traffic:
            requirements.append(
                dedent(f"""
                    - When making recommendations, consider real-time traffic conditions. 
                    - Prioritize routes and locations that minimize travel disruptions by avoiding traffic congestion, especially during peak hours. 
                    - Arrange locations logically to prevent backtracking.
                    - Optimize routes to minimize travel time, traffic delays, and distance.
                """).strip())

    def _by_weather(self, requirements: list):
        if self.user_preference.optimization_options.by_weather:
            requirements.append(
                dedent(f"""
                    - Use the provided weather_forecasts to make recommendations.
                    - Take into account potential delays, seasonal activities, and indoor alternatives in case of bad weather. 
                    - Avoid outdoor activities if rain or snow is forecast.
                """).strip())
