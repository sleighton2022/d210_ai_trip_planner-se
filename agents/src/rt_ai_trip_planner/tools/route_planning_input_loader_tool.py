import json
from crewai.tools import BaseTool
from typing import List, Type
from pydantic import BaseModel, Field

from ..utils.crew_io_utils import CrewInputOutputUtils
from ..model import Activity, ActivityNearbyRestaurantAssocs, OptimizationOptions, ActivityContainer, Restaurant, RoutePlanningInput, UserPreference, WeatherDetails

# This is a custom tool that packs all the input required for route planning.
class RoutePlanningInputLoaderTool(BaseTool):
    name: str = "Route Planning Input Loader Tool"
    description: str = (
        "A tool that loads required data to create route plan."
    )

    def _run(self) -> str:
        """
        This method is called by the BaseTool.run() method. It is responsible for executing the tool's functionality.
        """
        # Load a json file and convert it into a RoutePlanningInput object.
        data_folder_path = CrewInputOutputUtils.find_folder_path('data')
        print(f"[DEBUG] Loading input from data_folder_path: {data_folder_path}...")
        with open(f'{data_folder_path}/route-planning-input.json', 'r') as file:
            data = file.read()
        data = json.loads(data)
        print(f"[DEBUG] Loaded data: {str(data)[:50]}...")

        user_preference = UserPreference(**data['user_preference'])
        recommended_activities = [Activity(**activity) for activity in data['recommended_activities']]
        activity_to_restaurant_assocs = [ActivityNearbyRestaurantAssocs(**assoc) for assoc in data['activity_to_restaurant_assocs']]
        weather_forecasts = [WeatherDetails(**forecast) for forecast in data['weather_forecasts']]

        print(f"[INFO] Loaded user_preference: {user_preference}")
        print(f"[INFO] recommended_activities: {len(recommended_activities)}")
        print(f"[INFO] activityNearbyRestaurantAssocs: {len(activity_to_restaurant_assocs)}")
        print(f"[INFO] weather_forecasts: {len(weather_forecasts)}")

        obj = RoutePlanningInput(
            user_preference=user_preference, 
            recommended_activities=recommended_activities,
            activity_to_restaurant_assocs=activity_to_restaurant_assocs,
            weather_forecasts=weather_forecasts
        )
        
        # Convert the object to a json string and return.
        return json.dumps(obj.model_dump(), indent=2, default=lambda o: getattr(o, '__dict__', str(o)))
        
