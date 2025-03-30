import json
import openmeteo_requests

from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from typing import Type

import requests
import requests_cache
import pandas as pd
from retry_requests import retry

from rt_ai_trip_planner.model import WeatherDetails
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
class WeatherOpenMeteoSearchToolInput(BaseModel):
    location: str = Field(..., description="Location of interest")
    start_date: str = Field(..., description="Start date of the weather forecast")
    end_date: str = Field(..., description="End date of the weather forecast")


# This is a custom tool that access the Open-Meteo API for weather forecasts.
class WeatherOpenMeteoSearchTool(BaseTool):
    name: str = "Call the Open-Meteo API for weather forecasts."
    description: str = (
        "A tool for accessing the Open-Meteo Weather Forecast API for weather forecasts that fall between start_date and end_date for a specified location. Note that the 'date' field in the result is in ISO format."
    )
    args_schema: Type[BaseModel] = WeatherOpenMeteoSearchToolInput
    
    def _run(self, location: str, start_date: str, end_date: str) -> list[WeatherDetails]:
        """
        This method is called by the BaseTool.run() method. It is responsible for executing the tool's functionality.
        It gets weather forecast by latitude, longitude, start date, and end date.
        """
        start_time = time.time()

        # Resolve the location to latitude and longitude.
        latitude, longitude = self._get_lat_long(location)

        # Get weather forecast data.
        weather_details = self.get_weather_forecast_as_list(latitude, longitude, start_date, end_date)

        end_time = time.time()
        print(f"[INFO] Time taken for WeatherOpenMeteoSearchTool.run(): {end_time - start_time} seconds")
        return weather_details

    def get_weather_forecast_as_list(self, latitude: float, longitude: float, start_date: str, end_date: str) -> list[WeatherDetails]:
        """
        Get weather forecast by latitude, longitude, start date, and end date, and return the data as a list of WeatherDetails objects.        
        """
        # Get weather forecast data
        hourly_data = self._get_weather_forecast(latitude, longitude, start_date, end_date)

        # Convert the data to a list of WeatherDetails objects.
        weather_details_list = []
        for i in range(len(hourly_data["date"])):
            # Skip the data if the time is between 10:00 PM and 6:00 AM (outside of active hours).
            datetime = hourly_data["date"][i]
            if (datetime.hour < 6) or (datetime.hour > 22):
                continue

            weather_details = WeatherDetails(
                date = (hourly_data["date"][i]).isoformat(timespec='minutes'),
                temp = int(hourly_data["temperature_2m"][i]), # Convert temperature to int - Does not have to be very precise.                
                code = hourly_data["weather_code"][i],
                desc = self._get_weather_description(hourly_data["weather_code"][i], hourly_data["date"][i])
            )

            # Enrich the weather description by appending the temperature and temperature unit.
            weather_details.desc += f", {weather_details.temp} °F"
            weather_details_list.append(weather_details)

        return weather_details_list
    
    def get_weather_forecast_as_dataframe(self, latitude: float, longitude: float, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Get weather forecast by latitude, longitude, start date, and end date, and return the data as a pandas DataFrame.
        """
        # Get weather forecast data
        hourly_data = self._get_weather_forecast(latitude, longitude, start_date, end_date)

        # Convert the data to a pandas DataFrame.
        hourly_dataframe = pd.DataFrame(data = hourly_data)

        # Rename column names to make them more understandable.
        hourly_dataframe.rename(columns={
            "temperature_2m": "Temperature (°F)",
            "precipitation_probability": "Precipitation Probability (%)",
            "precipitation": "Precipitation (in)",
            "rain": "Rain (in)",
            "showers": "Showers (in)",
            "snowfall": "Snowfall (in)",
            "weather_code": "WMO Weather Code",
            "wind_speed_10m": "Wind Speed (mph)",
            "wind_gusts_10m": "Wind Gusts (mph)"
        }, inplace=True)

        return hourly_dataframe
    
    def _get_weather_forecast(self, latitude: float, longitude: float, start_date: str, end_date: str) -> dict:
        """
        Get weather forecast by latitude, longitude, start date, and end date.
        """
        # Setup the Open-Meteo API client with cache and retry on error
        cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
        retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
        openmeteo = openmeteo_requests.Client(session = retry_session)

        # Set up the query parameters specific to the request.
        query_params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date
        }
        params = OPEN_METRO_FORECAST_API_PARAMS | query_params
        responses = openmeteo.weather_api(OPEN_METRO_FORECAST_API_URL, params=params)

        # Process first location. Add a for-loop for multiple locations or weather models
        response = responses[0]
        print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
        print(f"Elevation {response.Elevation()} m asl")
        print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
        print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

        # Process hourly data. The order of variables needs to be the same as requested.
        hourly = response.Hourly()
        hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
        hourly_precipitation_probability = hourly.Variables(1).ValuesAsNumpy()
        hourly_precipitation = hourly.Variables(2).ValuesAsNumpy()
        hourly_rain = hourly.Variables(3).ValuesAsNumpy()
        hourly_showers = hourly.Variables(4).ValuesAsNumpy()
        hourly_snowfall = hourly.Variables(5).ValuesAsNumpy()
        hourly_weather_code = hourly.Variables(6).ValuesAsNumpy()
        hourly_wind_speed_10m = hourly.Variables(7).ValuesAsNumpy()
        hourly_wind_gusts_10m = hourly.Variables(8).ValuesAsNumpy()

        hourly_data = {"date": pd.date_range(
            start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
            end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
            freq = pd.Timedelta(seconds = hourly.Interval()),
            inclusive = "left"
        )}

        hourly_data["temperature_2m"] = hourly_temperature_2m
        hourly_data["precipitation_probability"] = hourly_precipitation_probability
        hourly_data["precipitation"] = hourly_precipitation
        hourly_data["rain"] = hourly_rain
        hourly_data["showers"] = hourly_showers
        hourly_data["snowfall"] = hourly_snowfall
        hourly_data["weather_code"] = hourly_weather_code
        hourly_data["wind_speed_10m"] = hourly_wind_speed_10m
        hourly_data["wind_gusts_10m"] = hourly_wind_gusts_10m

        return hourly_data
    
    def _get_lat_long(self, location: str, verbose=False) -> tuple[float, float]:
        """
        Get the latitude and longitude of a location using the Open-Meteo API.
        """
        # Check if the location is a popular city in the US.
        if location in POPULAR_CITIES_LAT_LONG:
            latitude, longitude = POPULAR_CITIES_LAT_LONG[location]
            return latitude, longitude

        # If the location string contains a comma, remove the comma and any string after it.
        if "," in location:
            location = location.split(",")[0].strip()        

        # Use the Open-Meteo API to get the latitude and longitude of the location.
        params = OPEN_METRO_GEOCODING_API_PARAMS | { "name": location }
        response = requests.get(OPEN_METRO_GEOCODING_API_URL, params=params)
        response_json = response.json()

        if (verbose):
            print(f"Location: [{location}]")
            print(f"Response: {response}")
            print(f"Response JSON: {response_json}")
            print(f"Response JSON (type): {type(response_json)}")

        latitude = longitude = 0
        results = response.json().get('results')
        if results:
            latitude = results[0]["latitude"]
            longitude = results[0]["longitude"]        

        return latitude, longitude
    
    def _get_weather_description(self, wmo_weather_code: int, datetime: pd.Timestamp) -> str:        
        """
        Get the weather description from the WMO weather code.
        """
        code = WMO_WEATHER_CODES.get(str(int(wmo_weather_code)))
        # print(f"wmo_weather_code: {wmo_weather_code}...code: {code}...datetime: {datetime}")

        if code:
            # if datetime is day time, set is_day to True, else False.
            is_day = (datetime.hour >= 6) and (datetime.hour < 18)
            if is_day:
                code_day_night = code.get("day")
            else:
                code_day_night = code.get("night")
            
            # print(f"is_day: {is_day}...code_day_night: {code_day_night}")
            desc = code_day_night.get("description") if code_day_night else "Unknown"
        else:
            desc = "Unknown"

        return desc
