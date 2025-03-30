import json
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field

from rt_ai_trip_planner.model import Itinerary, ActivityContainer, UserPreference, Activity
from typing import List


# It takes a UserPreference object and returns a list of activities that match the argument.
class ActivitySearchToolInput_v1(BaseModel):
    """Input schema for ActivityDatabaseSearchTool."""
    # user_preference: dict = Field(..., description="An instance of a UserPreference class.")
    destination: str = Field(..., description="Destination of the trip")
    start_date: str = Field(..., description="Start date of the trip")
    end_date: str = Field(..., description="End date of the trip")
    interests: List[str] = Field(..., description="List of interests")
    hotel_location: str = Field(..., description="Preferred hotel location")


class MockedActivitySearchTool(BaseTool):
    name: str = "JSON Activity Search Tool"
    description: str = (
        "This tool returns activities defined in a JSON file."
    )
    args_schema: Type[BaseModel] = ActivitySearchToolInput_v1

    def _run(self, destination: str, start_date: str, end_date: str, interests: List[str], hotel_location: str) -> ActivityContainer:
        # Convert input arguments to UserPreference object.
        user_preference = UserPreference(
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            interests=interests,
            hotel_location=hotel_location
        )

        # Create mocked activities from a json file.
        with open('./data/sample-activity.json', 'r') as file:
            data = json.load(file)
            recommended_activity = ActivityContainer(**data)
            recommended_activity.user_preference = user_preference        

        print("\n===============================================\n")
        print(f"[DEBUG] Calling MockedActivitySearchTool...     \n")
        print(f"[DEBUG] * Input(user_preference): \n{user_preference}\n")
        print(f"[DEBUG] * Output(recommended_activity): \n{recommended_activity}\n")
        print("\n===============================================\n")

        return recommended_activity


# This is a custom tool that search a local database for matching activities.
class ActivityDatabaseSearchTool_v1(BaseTool):
    name: str = "Local Database Search Tool"
    description: str = (
        "This tool searches a local database for activities that match the destination, start_date, end_date, interests and hotel_location."
    )
    args_schema: Type[BaseModel] = ActivitySearchToolInput_v1

    def _run(self, destination: str, start_date: str, end_date: str, interests: List[str], hotel_location: str) -> ActivityContainer:
        # Convert input arguments to UserPreference object.
        user_preference = UserPreference(
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            interests=interests,
            hotel_location=hotel_location
        )

        # Search Database for activities that match the user_preference
        # TODO: Implement the search logic here

        return ActivityContainer(user_preference=user_preference, activities=[])


class ItineraryGeneratorToolInput(BaseModel):
    """Input schema for ActivityDatabaseSearchTool."""
    # user_preference: dict = Field(..., description="An instance of a UserPreference class.")
    destination: str = Field(..., description="Destination of the trip")
    start_date: str = Field(..., description="Start date of the trip")
    end_date: str = Field(..., description="End date of the trip")
    interests: List[str] = Field(..., description="List of interests")
    hotel_location: str = Field(..., description="Preferred hotel location")
    activities: List[Activity] = Field(..., description="List of activities to plan for the itinerary")


class MockedItineraryGeneratorTool(BaseTool):
    name: str = "JSON Route Optimization Tool"
    description: str = (
        "This tool returns itinerary defined in a JSON file."
    )
    args_schema: Type[BaseModel] = ItineraryGeneratorToolInput

    def _run(self, destination: str, start_date: str, end_date: str, interests: List[str], hotel_location: str, activities: List[Activity]) -> Itinerary:
        # Convert input arguments to UserPreference object.
        user_preference = UserPreference(
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            interests=interests,
            hotel_location=hotel_location
        )

        # Create mocked activities from a json file.
        with open('./data/sample-itinerary.json', 'r') as file:
            data = json.load(file)
            itinerary = Itinerary(**data)
            itinerary.user_preference = user_preference        

        print("\n===============================================\n")
        print(f"[DEBUG] Calling MockedActivitySearchTool...     \n")
        print(f"[DEBUG] * Input(user_preference, activities): \n{user_preference}\n{activities}\n")
        print(f"[DEBUG] * Output(itinerary): \n{itinerary}\n")
        print("\n===============================================\n")

        return itinerary



# class MyCustomToolInput(BaseModel):
#     """Input schema for MyCustomTool."""
#     argument: str = Field(..., description="Description of the argument.")

# class MyCustomTool(BaseTool):
#     name: str = "Name of my tool"
#     description: str = (
#         "Clear description for what this tool is useful for, your agent will need this information to use it."
#     )
#     args_schema: Type[BaseModel] = MyCustomToolInput

#     def _run(self, argument: str) -> str:
#         # Implementation goes here
#         return "this is an example of a tool output, ignore it and move along."


