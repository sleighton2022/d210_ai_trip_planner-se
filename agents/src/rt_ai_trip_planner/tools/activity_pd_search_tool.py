import pandas as pd
from crewai.tools import BaseTool
from typing import List, Tuple, Type
from pydantic import BaseModel, Field

from rt_ai_trip_planner.model import Activity, OptimizationOptions, ActivityContainer, UserPreference

import os
# name,main_category,overarching_category,rating,reviews,normalized_value,city,latitude,longitude
# destination='Los Angeles, CA', interests=['Theme park', 'zoo', 'museums']

# Load data from the CSV file into a DataFrame from the first available path.
ACTIVITY_DF: pd.DataFrame = None
LOOKUP_PATHS = [
    ".",
    "..",
    "../..",
    "../../..",
]
for p in LOOKUP_PATHS:
    try:
        print("Current Working Directory:", os.getcwd())
        file_path = f"{p}/agents/data/MVP_Data.csv"
        print(f"[INFO] Loading DataFrame from: {file_path}...")
        ACTIVITY_DF = pd.read_csv(file_path)
        print(f"[INFO] Loaded DataFrame from: {file_path}")
        break
    except FileNotFoundError:
        pass
assert ACTIVITY_DF is not None, "Failed to load the DataFrame from any of the specified paths."


# Schema of the Input to the ActivityDataFrameSearchTool.
class ActivityDataFrameSearchToolInput(BaseModel):
    destination: str = Field(..., description="Destination of the trip")
    start_date: str = Field(..., description="Start date of the trip")
    end_date: str = Field(..., description="End date of the trip")
    interests: List[str] = Field(..., description="List of interests")
    hotel_location: str = Field(..., description="Preferred hotel location")    
    optimization_options: dict = Field(..., description="Optimization options")


# This is a custom tool that search a DataFrame for the matching Activity information.
class ActivityDataFrameSearchTool(BaseTool):
    name: str = "Search a Pandas DataFrame for activities."
    description: str = (
        "A tool that can be used to search a Pandas DataFrame for activities."
    )
    args_schema: Type[BaseModel] = ActivityDataFrameSearchToolInput

    def _run(self, destination: str, start_date: str, end_date: str, interests: List[str], hotel_location: str, optimization_options: dict) -> ActivityContainer:
        """
        This method is called by the BaseTool.run() method. It is responsible for executing the tool's functionality.
        Search a Pandas DataFrame for activities that match the user preferences.
        """
        # Convert input arguments to UserPreference object.
        user_preference = UserPreference(
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            interests=interests,
            hotel_location=hotel_location,
            optimization_options=OptimizationOptions(
                by_weather = optimization_options['by_weather'],
                by_traffic = optimization_options['by_traffic'],
                by_family_friendly = optimization_options['by_family_friendly'],
                by_safety = optimization_options['by_safety'],
                by_cost = optimization_options['by_cost'],
                min_rating = optimization_options['min_rating']
            )
        )

        # Search Database for activities that match the user_preference.
        activities = self._search(destination, interests)

        # Create a list of activity names.
        activity_names = [activity.name for activity in activities]

        return ActivityContainer(user_preference=user_preference, activity_names=activity_names, activities=activities)    

    def _search(self, location: str, interest: List[str]) -> list[Activity]:
        """Search the DataFrame for activities that match the location and interest."""

        # Convert the search keys to values that match the DataFrame columns.
        city, categories = self._map_search_keys(location, interest)
        print(f"[DEBUG] Searching activities that match city: {city}, categories: {categories}")

        # Find records that match the location (ignore case) and interest.
        df = ACTIVITY_DF
        result = df[(df['city'].str.contains(city, case=False)) & (df['overarching_category'].isin(categories))]

        # Convert the results to a list of Activity objects.
        activities = []
        for index, row in result.iterrows():
            activity = Activity(
                name=row['name'],
                location=row['address'],      
                latitude=row['latitude'],
                longitude=row['longitude'],          
                category=row['overarching_category'],
                # rating=row['rating'],
                # description='',
                # why_its_suitable='',
                # reviews=None,                
                # cost=None,
                # average_duration=None
            )
            activities.append(activity)

        return activities
    
    def _map_search_keys(self, location: str, interest: List[str]) -> Tuple[str, List[str]]:
        """Convert search keys to a format that is comply to the dataset."""

        # Map the search keys to the DataFrame columns        
        if 'los angeles' in location.lower():
            city = 'Los-angeles'
        elif 'new york' in location.lower():
            city = 'New-york-city'
        else:
            city = location

        categories = interest

        return city, categories
