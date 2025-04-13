import json
import os
import re
import time
from typing import Any, List, Type
import googlemaps
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import requests
from ..model import Activity, OptimizationOptions, RecommendedActivitiesContainer, Restaurant, UserPreference
from ..utils.geocodes_utils import GeocodeUtils

# References: 
#   https://developers.google.com/maps/documentation/places/web-service/nearby-search
#   https://developers.google.com/maps/documentation/places/web-service/supported_types
#   https://developers.google.com/maps/documentation/places/web-service/choose-fields
#   https://console.cloud.google.com/google/maps-apis/api-list?project=my-lab-projects-387418

INTEREST_TO_PLACE_TYPES = {
    "amusement park": ["amusement_park"],
    "zoo": ["zoo"],
    "aquarium": ["aquarium"],
    "tourist_attraction": ["tourist_attraction"],
    "landmarks": ["local_government_office", "city_hall", "courthouse", "library", "university"],
    "entertainment/amusement park": ["amusement_park", "tourist_attraction", "aquarium"],
    "history": ["museum", "tourist_attraction"],
    "nature": ["park", "zoo"],
    "museum": ["museum"],
    "food": ["restaurant", "cafe", "bakery", "bar"],
    "shopping": ["shopping_mall", "shoe_store", "store", "clothing_store"],
    "nightlife": ["night_club"],
}


# Schema of the Input to the AttractionsSearchTool.
class AttractionsSearchToolInput(BaseModel):
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

# This is a custom tool that access Google Map Places API to search places.
class AttractionsSearchTool(BaseTool):
    name: str = "Search attractions nearby a location"
    description: str = (
        "A tool that can be used to find the nearby attractions with the latitude and longitude of a location."
    )
    args_schema: Type[BaseModel] = AttractionsSearchToolInput

    def _run(self, destination: str, start_date: str, end_date: str, interests: List[str], hotel_location: str, 
             by_weather: bool, by_traffic: bool, by_family_friendly: bool, by_safety: bool, by_cost: bool, min_rating: float) -> str:
        """
        This method is called by the BaseTool.run() method. It is responsible for executing the tool's functionality.
        Call searchNearby API to get the nearby restaurants.
        """
        # Resolve the destination to latitude and longitude. Convert interests to place types.
        start_time = time.time()
        latitude, longitude = GeocodeUtils.get_lat_lon(destination)        
        place_types = self._to_place_types(interests) # ['amusement_park', 'museum', 'zoo']        
        print(f"[DEBUG] Searching for attractions near '{destination}' at latitude: {latitude}, longitude: {longitude}, place types: {place_types}")

        # Get attraction data.
        url = "https://places.googleapis.com/v1/places:searchNearby"
        data = {
            "includedTypes": place_types,
            "maxResultCount": 15,
            "rankPreference": "POPULARITY", # POPULARITY, DISTANCE
            "regionCode": "US",
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": latitude,  # Example: 37.7749
                        "longitude": longitude # Example: -122.4194
                    },
                    "radius": 50000.0  # In meters, 50000 meters is ~30 miles
                }
            }
        }
        
        headers = {
            "Content-Type": "application/json", "X-Goog-Api-Key": os.getenv('GOOGLE_MAPS_API_KEY'),
            "X-Goog-FieldMask": "places.displayName.text,places.types,places.formattedAddress,places.location,places.rating,places.regularOpeningHours.weekdayDescriptions,places.businessStatus,places.primaryType,places.editorialSummary.text,places.goodForChildren"
        }
        json_data = json.dumps(data)
        response = requests.post(url, data=json_data, headers=headers)        
        activities = self._to_activity(response.json())

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

        print(f"[INFO] Time taken for AttractionsSearchTool.run() to retrieve {len(activities)} attractions: {time.time()-start_time} seconds")
        container = RecommendedActivitiesContainer(
            user_preference=user_preference,
            recommended_activities=activities
        )
        return json.dumps(container, indent=2, default=lambda o: getattr(o, '__dict__', str(o)))        

    def _to_activity(self, response: str) -> list[Activity]:
        """
        Convert the response from the API to a list of Activity objects.
        """
        activities = []
        for place in response['places']:

            # Need to decode the unicode characters in the string.
            regular_opening_hours_str=str(place.get('regularOpeningHours', {}).get('weekdayDescriptions', 'N/A'))
            if regular_opening_hours_str != 'N/A':
                regular_opening_hours_str=regular_opening_hours_str.encode('utf-8').decode('unicode_escape')
                regular_opening_hours_str=regular_opening_hours_str.replace("\u202f", " - ")
                regular_opening_hours_str=re.sub(r'[^\x00-\x7F]+', ' ', regular_opening_hours_str)

            activity = Activity(
                name=place.get('displayName', {}).get('text', 'N/A'),
                location=place.get('formattedAddress', 'N/A'),
                latitude=place.get('location', {}).get('latitude', 0.0),
                longitude=place.get('location', {}).get('longitude', 0.0),
                category=place.get('primaryType', 'N/A'),
                rating=place.get('rating', 0.0),
                regular_opening_hours=regular_opening_hours_str,
                business_status=place.get('businessStatus', 'N/A'),
                description=place.get('editorialSummary', {}).get('text', 'N/A'),
            )
            activities.append(activity)

        print(f"[DEBUG] AttractionsSearchTool len(activities): {len(activities)}")    
        return activities

    def _to_place_types(self, interest: list[str]) -> list[str]:
        """
        Convert the interest to a list of place types.
        """
        place_types = set()
        for i in interest:
            i = i.lower()
            if i in INTEREST_TO_PLACE_TYPES:
                # Add the place types to the set.
                for j in INTEREST_TO_PLACE_TYPES[i]:
                    place_types.add(j)
            else:
                print(f"[WARNING] Unknown Interest '{i}' not found in INTEREST_TO_PLACE_TYPES. Defaulting to 'tourist_attraction'.")
                place_types.add("tourist_attraction")

        # Convert the set to a list and return.
        return list(place_types)


# Quick Unit Test. TODO: Move this to a separate test file.
if __name__ == "__main__":
    placesSearchTool = AttractionsSearchTool()

    response = placesSearchTool._run(
        destination="Los Angeles, CA", 
        start_date="2025-02-17", end_date="2025-02-20", 
        interests=["aquarium", "museum", "amusement_park"], 
        hotel_location="West Covina, CA", 
        optimization_options={"by_weather": True, "by_traffic": True, "by_family_friendly": True, "by_safety": True, "by_cost": False, "min_rating": 3.0}
    )
    print(response)
