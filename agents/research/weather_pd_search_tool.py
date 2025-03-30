import pandas as pd
import json
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field

# from rt_ai_trip_planner.model import Itinerary, RecommendedActivity, UserPreference, Activity
from typing import List


# Schema of the Input to the WeatherDataFrameSearchTool.
class WeatherDataFrameSearchToolInput(BaseModel):
    start_date: str = Field(..., description="Start date of the trip")
    end_date: str = Field(..., description="End date of the trip")

# This is a custom tool that search a DataFrame for the matching weather information.
class WeatherDataFrameSearchTool(BaseTool):
    name: str = "Search a Pandas DataFrame for weather forecasts."
    description: str = (
        "A tool that can be used to search a Pandas DataFrame for weather forecasts that fall between start_date and end_date."
    )
    args_schema: Type[BaseModel] = WeatherDataFrameSearchToolInput

    def _run(self, start_date: str, end_date: str) -> str:
        # Load the CSV file into a DataFrame
        # file_path = "../../../data/hourly-weather.csv"
        file_path = "./data/hourly-weather.csv"
        df = pd.read_csv(file_path)
        # Convert the 'date' column to datetime format
        df['date'] = pd.to_datetime(df['date'])
        result = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

        return result.to_json(orient='records', date_format='iso')


# Unit Test
if __name__ == "__main__":
    weather_search_tool = WeatherDataFrameSearchTool()
    result = weather_search_tool.run('02-18-2025', '02-19-2025')
    print(result)




# # Load the CSV file into a DataFrame
# file_path = "../../../data/hourly-weather.csv"
# weather_df = pd.read_csv(file_path)

# # Display the first few rows of the DataFrame
# print(weather_df.head())
# print(weather_df.dtypes)

# # def query_weather_by_location_and_date(df, location, date):
# #     result = df[(df['location'] == location) & (df['date'] == date)]
# #     return result

# # # Example usage
# # location = 'New York'
# # date = '2023-10-01'
# # queried_data = query_weather_by_location_and_date(weather_df, location, date)
# # print(queried_data)

# def query_weather_by_location_and_date_range(df, start_date, end_date):
#     result = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
#     return result

# # Convert the 'date' column to datetime format
# weather_df['date'] = pd.to_datetime(weather_df['date'])

# # Display the first few rows of the DataFrame to verify the change
# # print(weather_df.head())
# print(weather_df.dtypes)

# # Example usage
# start_date = '02-18-2025 00:00'
# end_date = '02-19-2025 23:59'
# queried_data_range = query_weather_by_location_and_date_range(weather_df, start_date, end_date)
# print(queried_data_range)

# print(queried_data_range.to_json(orient='records', date_format='iso'))