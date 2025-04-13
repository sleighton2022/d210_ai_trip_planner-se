import json
import os
from typing import Any, Type
import googlemaps
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import requests
from ..model import Restaurant

# References: 
#   https://developers.google.com/maps/documentation/places/web-service/nearby-search
#   https://developers.google.com/maps/documentation/places/web-service/supported_types
#   https://developers.google.com/maps/documentation/places/web-service/choose-fields
#   https://console.cloud.google.com/google/maps-apis/api-list?project=my-lab-projects-387418

# Schema of the Input to the NearbyRestaurantsSearchTool.
class NearbyRestaurantsSearchToolInput(BaseModel):
    latitude: float = Field(..., description="The latitude value for which you wish to obtain the closest restaurants.")
    longitude: float = Field(..., description="The longitude value for which you wish to obtain the closest restaurants.")

# This is a custom tool that access Google Map Places API to search nearby restaurants.
class NearbyRestaurantsSearchTool(BaseTool):
    name: str = "Search Nearby Restaurants"
    description: str = (
        "A tool that can be used to find the nearby restaurants with the latitude and longitude of a location."
    )
    args_schema: Type[BaseModel] = NearbyRestaurantsSearchToolInput

    def _run(self, latitude: float, longitude: float) -> str:
        """
        This method is called by the BaseTool.run() method. It is responsible for executing the tool's functionality.
        Call searchNearby API to get the nearby restaurants.
        """
        print(f"[DEBUG] Searching for nearby restaurants at latitude: {latitude}, longitude: {longitude}")

        # Get the restaurants data.
        url = "https://places.googleapis.com/v1/places:searchNearby"
        data = {
            "includedTypes": ["restaurant", "diner", "deli", "food_court", "sandwich_shop", "steak_house"],
            "maxResultCount": 5,
            "rankPreference": "DISTANCE", # POPULARITY, DISTANCE
            "regionCode": "US",
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": latitude,  # Example: 37.7749
                        "longitude": longitude # Example: -122.4194
                    },
                    "radius": 12000.0  # Assume 5 - 10 miles as nearby. Take the median value = 8 mile (~12000 meters)
                }
            }
        }
        
        headers = {
            "Content-Type": "application/json", "X-Goog-Api-Key": os.getenv('GOOGLE_MAPS_API_KEY'),
            "X-Goog-FieldMask": "places.displayName.text,places.types,places.formattedAddress,places.location,places.rating,places.regularOpeningHours.weekdayDescriptions,places.businessStatus,places.priceLevel,places.servesBreakfast,places.servesLunch,places.servesDinner,places.primaryType,places.editorialSummary.text,places.goodForChildren,places.priceRange"
        }
        json_data = json.dumps(data)
        response = requests.post(url, data=json_data, headers=headers)
        return response.json()


    def _run_places_nearby(self, location: tuple, keyword: str, rank_by: str) -> any:
        """
        This method is called by the BaseTool.run() method. It is responsible for executing the tool's functionality.
        It gets weather forecast by latitude, longitude, start date, and end date.
        https://developers.google.com/maps/documentation/places/web-service/supported_types
        """                
        
        # Default values
        radius = 5000
        type = "restaurant, cafe"
        language = "en-US"
        if rank_by is None:
            rank_by = "prominence" # Optional: Sort by prominence, distance, or rating       

        try:
            gmaps = googlemaps.Client(key=os.getenv('GOOGLE_MAPS_API_KEY'))
            results = gmaps.places_nearby(
                location=location,
                radius=radius,
                type=type,
                keyword=keyword,
                rank_by=rank_by,
                language=language,
            )
        except googlemaps.exceptions.HTTPError as e:
            print(f"Error: {e}")
        
        return results    

    def get_place_info(self, address, api_key):
        # Base URL
        base_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"

        # Parameters in a dictionary
        params = {
            "input": address,
            "inputtype": "textquery",
            "fields": "formatted_address,name,business_status,place_id",
            "key": api_key,
        }

        # Send request and capture response
        response = requests.get(base_url, params=params)

        # Check if the request was successful
        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    def to_restaurant(self, result: dict) -> Restaurant:
        """
        Convert the result (in dictionary) from the Google Map Places API to a Restaurant object.
        """
        return Restaurant(
            name=result["name"],
            location=result["vicinity"],
            latitude=result["geometry"]["location"]["lat"],
            longitude=result["geometry"]["location"]["lng"],
            cuisine=result["types"][0],
        )
    
