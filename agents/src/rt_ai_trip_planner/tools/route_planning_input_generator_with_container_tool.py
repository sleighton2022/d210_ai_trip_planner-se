from datetime import datetime
import json
import os
import time
from crewai.tools import BaseTool
from typing import List, Type
from pydantic import BaseModel, Field

from ..model import Activity, ActivityNearbyRestaurantAssocs, ActivityToRestaurantAssocsContainer, OptimizationOptions, ActivityContainer, RecommendedActivitiesContainer, Restaurant, RoutePlanningInput, UserPreference, WeatherDetails, WeatherForecastsContainer
from ..utils.crew_io_utils import CrewInputOutputUtils

# Schema of the Input to the RoutePlanningInputGeneratorTooler details.
class RoutePlanningInputGeneratorWithContainerToolInput(BaseModel):
    recommended_activities_container: RecommendedActivitiesContainer = Field(..., description="Container for recommended activities")
    activity_to_restaurant_assocs_container: ActivityToRestaurantAssocsContainer = Field(..., description="Container for activity-to-restaurant associations")
    weather_forecasts_container: WeatherForecastsContainer = Field(..., description="Container for weather forecasts")


# This is a custom tool that packs all the input required for route planning.
class RoutePlanningInputGeneratorWithContainerTool(BaseTool):
    name: str = "Report Generation Tool"
    description: str = (
        "A tool that packs all the research information such as activity recommendations, restaurant recommendations, and weather forecasts into a single RoutePlanningInput object."
    )
    args_schema: Type[BaseModel] = RoutePlanningInputGeneratorWithContainerToolInput

    def _run(self, recommended_activities_container: RecommendedActivitiesContainer, 
             activity_to_restaurant_assocs_container: ActivityToRestaurantAssocsContainer,
             weather_forecasts_container: WeatherForecastsContainer,) -> str:
        """
        This method is called by the BaseTool.run() method. It is responsible for executing the tool's functionality.
        """ 
        # --- DEBUGGING START ---
        print("-" * 80)
        print(f"[DEBUG TOOL] Entering {self.name} _run method.")
        print(f"[DEBUG TOOL] Type of recommended_activities_container: {type(recommended_activities_container)}")
        print(f"[DEBUG TOOL] Value of recommended_activities_container:\n{recommended_activities_container}")
        print("-" * 30)
        print(f"[DEBUG TOOL] Type of activity_to_restaurant_assocs_container: {type(activity_to_restaurant_assocs_container)}")
        print(f"[DEBUG TOOL] Value of activity_to_restaurant_assocs_container:\n{activity_to_restaurant_assocs_container}")
        print("-" * 30)
        print(f"[DEBUG TOOL] Type of weather_forecasts_container: {type(weather_forecasts_container)}")
        print(f"[DEBUG TOOL] Value of weather_forecasts_container:\n{weather_forecasts_container}")
        print("-" * 80)
        # --- DEBUGGING END ---

        # Create the RoutePlanningInput object.
        obj = RoutePlanningInput(
            user_preference=recommended_activities_container.user_preference, 
            recommended_activities=recommended_activities_container.recommended_activities,
            activity_to_restaurant_assocs=activity_to_restaurant_assocs_container.activity_to_restaurant_assocs,
            weather_forecasts=weather_forecasts_container.weather_forecasts)
        
        # Convert the object to a json string and return.
        json_str = json.dumps(obj.model_dump(), indent=2, default=lambda o: getattr(o, '__dict__', str(o)))

        # Save the JSON string to a file.
        write_crew_io_to_file = os.getenv("APP_WRITE_CREW_IO_TO_FILE", "false")
        if write_crew_io_to_file.lower() == "true":
            start_time = time.time()
            CrewInputOutputUtils.write_to_file(folder_name='data', file_name='route-planning-input.json', data=json_str)

        return json_str
