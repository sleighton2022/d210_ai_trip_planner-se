import json
import openmeteo_requests

from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from typing import Type

import requests
import requests_cache
import pandas as pd
from retry_requests import retry

from ..model import WeatherDetails
import time


# Define api-related constants:
#   * Make sure all required weather variables are listed here
#   * The order of variables in hourly or daily is important to assign them correctly below.
#   * Variables: lat/long, timezone: "America/New_York", "America/Los_Angeles"
#   * Use this API to find lat/long and timezone by city name: https://geocoding-api.open-meteo.com/v1/search?name=los+angeles&count=1&language=en&format=json
#
OPEN_METRO_FORECAST_API_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METRO_FORECAST_API_PARAMS = {
    "hourly": ["temperature_2m", "precipitation_probability", "precipitation", "rain", "showers", "snowfall", "weather_code", "wind_speed_10m", "wind_gusts_10m"],
    "temperature_unit": "fahrenheit",
    "wind_speed_unit": "mph",
    "precipitation_unit": "inch",
}
OPEN_METRO_GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
OPEN_METRO_GEOCODING_API_PARAMS = {
    "count": 1,
    "language": "en",
    "format": "json"
}

# Cache Latitude and longitude of popular cities in the US avoid extra lookup.
POPULAR_CITIES_LAT_LONG = {
    "Los Angeles, CA": (34.0522, -118.2437),
    "New York, NY": (40.7128, -74.0060),
    "Chicago, IL": (41.8781, -87.6298),
    "Houston, TX": (29.7604, -95.3698),
    "Phoenix, AZ": (33.4484, -112.0740),
    "Philadelphia, PA": (39.9526, -75.1652),
    "San Antonio, TX": (29.4241, -98.4936),
    "San Diego, CA": (32.7157, -117.1611),
    "Dallas, TX": (32.7767, -96.7970),
    "San Jose, CA": (37.3382, -121.8863),
    "Austin, TX": (30.2672, -97.7431),
    "Jacksonville, FL": (30.3322, -81.6557),
    "San Francisco, CA": (37.7749, -122.4194),    
}

# Load WMO weather codes from a json file from the first available path.
# These codes are used to get the weather description from the weather code.
WMO_WEATHER_CODES = {}
LOOKUP_PATHS = [
    ".",
    "../..",
    "../../..",
]
for p in LOOKUP_PATHS:
    try:
        file_path = f"{p}/data/wmo-weather-codes.json"
        print(f"[INFO] Loading json file from: {file_path}...")
        with open(file_path, 'r') as file:
            WMO_WEATHER_CODES = json.load(file)
        print(f"[INFO] Loaded json file from: {file_path}")
        break
    except FileNotFoundError:
        pass
assert WMO_WEATHER_CODES is not None, "Failed to load the json file from any of the specified paths."


# Schema of the Input to the WeatherDataFrameSearchTool.
class MockedWeatherSearchToolInput(BaseModel):
    location: str = Field(..., description="Location of interest")
    start_date: str = Field(..., description="Start date of the weather forecast")
    end_date: str = Field(..., description="End date of the weather forecast")


# This is a custom tool that access the Open-Meteo API for weather forecasts.
class MockedWeatherSearchTool(BaseTool):
    name: str = "Retrieve weather forecasts."
    description: str = (
        "A tool to retrieve Weather Forecast."
    )
    args_schema: Type[BaseModel] = MockedWeatherSearchToolInput
    
    def _run(self, location: str, start_date: str, end_date: str) -> list[WeatherDetails]:
        """
        This method is called by the BaseTool.run() method. It is responsible for executing the tool's functionality.
        It gets weather forecast by latitude, longitude, start date, and end date.
        """
        weather_forecasts = [
            WeatherDetails(date="2025-02-17T00:00", temp=70, code=800, desc="Clear sky, 70 °F"),
            WeatherDetails(date="2025-02-18T01:00", temp=70, code=800, desc="Clear sky, 71 °F"),
            WeatherDetails(date="2025-02-19T02:00", temp=70, code=800, desc="Clear sky, 72 °F"),
        ]
        return weather_forecasts
