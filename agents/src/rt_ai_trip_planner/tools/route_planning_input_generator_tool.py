from datetime import datetime
import json
import os
import time
from crewai.tools import BaseTool
from typing import List, Type
from pydantic import BaseModel, Field

from ..model import Activity, ActivityNearbyRestaurantAssocs, OptimizationOptions, ActivityContainer, Restaurant, RoutePlanningInput, UserPreference, WeatherDetails
from ..utils.crew_io_utils import CrewInputOutputUtils

# Schema of the Input to the RoutePlanningInputGeneratorTooler details.
class RoutePlanningInputGeneratorToolInput(BaseModel):
    destination: str = Field(..., description="Destination of the trip")
    start_date: str = Field(..., description="Start date of the trip")
    end_date: str = Field(..., description="End date of the trip")
    interests: List[str] = Field(..., description="List of interests")
    hotel_location: str = Field(..., description="Preferred hotel location")
    by_weather: bool = Field(..., description="Optimize by weather")
    by_traffic: bool = Field(..., description="Optimize by traffic")
    by_family_friendly: bool = Field(..., description="Optimize by family friendly")
    by_safety: bool = Field(..., description="Optimize by safety")
    by_cost: bool = Field(..., description="Optimize by cost")    
    min_rating: float = Field(..., description="Minimum rating of the activity")
    recommended_activities: List[Activity] = Field(..., description="List of activities")
    activity_to_restaurant_assocs: List[ActivityNearbyRestaurantAssocs] = Field(..., description="List of activity-to-nearby restaurant associations")
    weather_forecasts: List[WeatherDetails] = Field(..., description="List of weather forecasts")


# This is a custom tool that packs all the input required for route planning.
class RoutePlanningInputGeneratorTool(BaseTool):
    name: str = "Report Generation Tool"
    description: str = (
        "A tool that packs all the research information such as activity recommendations, restaurant recommendations, and weather forecasts into a single RoutePlanningInput object."
    )
    args_schema: Type[BaseModel] = RoutePlanningInputGeneratorToolInput

    def _run(self, destination: str, start_date: str, end_date: str, interests: List[str], hotel_location: str, 
            by_weather: bool, by_traffic: bool, by_family_friendly: bool, by_safety: bool, by_cost: bool, min_rating: float,
            recommended_activities: List[Activity], 
            activity_to_restaurant_assocs: List[ActivityNearbyRestaurantAssocs],
            weather_forecasts: List[WeatherDetails]) -> str:
        """
        This method is called by the BaseTool.run() method. It is responsible for executing the tool's functionality.
        """        
        # Convert input arguments to UserPreference object.
        user_preference = UserPreference(
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            interests=interests,
            hotel_location=hotel_location,
            optimization_options=OptimizationOptions(
                by_weather = by_weather,
                by_traffic = by_traffic,
                by_family_friendly = by_family_friendly,
                by_safety = by_safety,
                by_cost = by_cost,
                min_rating = min_rating
            )
        )

        global_start_time = time.time()
        start_time = time.time()        
        print(f'[DEBUG] RoutePlanningInputGeneratorTooler details STARTED at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.')
        print(f"[DEBUG] Start preparing RoutePlanningInput objects...")
        print(f"[DEBUG]   - user_preference: {str(user_preference)[:50]}")
        print(f"[DEBUG]   - recommended_activities: {len(recommended_activities)}")
        print(f"[DEBUG]   - activity_to_restaurant_assocs: {len(activity_to_restaurant_assocs)}")
        print(f"[DEBUG]   - weather_forecasts: {len(weather_forecasts)}")

        # Create the RoutePlanningInput object.
        obj = RoutePlanningInput(
            user_preference=user_preference, 
            recommended_activities=recommended_activities,
            activity_to_restaurant_assocs=activity_to_restaurant_assocs,
            weather_forecasts=weather_forecasts)
        print(f"[DEBUG] RoutePlanningInput object created in {time.time() - start_time:.4f} seconds.")
        
        # Convert the object to a json string and return.
        start_time = time.time()
        print(f"[DEBUG] Start creating Json string for the RoutePlanningInput objects...")
        json_str = json.dumps(obj.model_dump(), indent=2, default=lambda o: getattr(o, '__dict__', str(o)))
        print(f"[DEBUG] Json string created in {time.time() - start_time:.4f} seconds.")

        # Save the JSON string to a file.
        write_crew_io_to_file = os.getenv("APP_WRITE_CREW_IO_TO_FILE", "false")
        if write_crew_io_to_file.lower() == "true":
            start_time = time.time()
            print(f"[DEBUG] Start writing Json string to file...")
            CrewInputOutputUtils.write_to_file(folder_name='data', file_name='route-planning-input.json', data=json_str)
            print(f"[DEBUG] Json string written to file in {time.time() - start_time:.4f} seconds.")

        print(f"[DEBUG] RoutePlanningInputGeneratorTooler details completed in {time.time() - global_start_time:.4f} seconds.")
        print(f'[DEBUG] RoutePlanningInputGeneratorTooler details ENDED at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.')
        return json_str
