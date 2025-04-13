from pydantic import BaseModel, Field
from typing import List, Optional

####################################################################################################
# Define classes related to user input.
####################################################################################################
class OptimizationOptions(BaseModel):
    by_weather: Optional[bool] = Field(..., description="Optimize by weather")
    by_traffic: Optional[bool] = Field(..., description="Optimize by traffic")
    by_family_friendly: Optional[bool] = Field(..., description="Optimize by family friendly")
    by_safety: Optional[bool] = Field(..., description="Optimize by safety")
    by_cost: Optional[bool] = Field(..., description="Optimize by cost")    
    min_rating: Optional[float] = Field(..., description="Minimum rating of the activity")

class UserPreference(BaseModel):
    destination: str = Field(..., description="Destination of the trip")
    start_date: str = Field(..., description="Start date of the trip")
    end_date: str = Field(..., description="End date of the trip")
    interests: List[str] = Field(..., description="List of interests")
    hotel_location: str = Field(..., description="Preferred hotel location")
    optimization_options: OptimizationOptions = Field(..., description="Optimization options")


####################################################################################################
# Define classes related to activity.
####################################################################################################
class Activity(BaseModel):
    name: str = Field(..., description="Name of the activity")
    location: str = Field(..., description="Location of the activity")
    latitude: float = Field(..., description="Latitude of the location")
    longitude: float = Field(..., description="Longitude of the location")
    category: str = Field(..., description="Category of the activity")
    rating: Optional[float] = Field(description="Rating of the activity", default=0.0)
    regular_opening_hours: Optional[str] = Field(description="Regular opening hours of the activity", default="N/A")
    business_status: Optional[str] = Field(description="Business status of the activity", default="N/A")
    description: Optional[str] = Field(description="Description of the activity including editorial summary", default="N/A")

class ActivityDetail(BaseModel):
    activity: Activity = Field(..., description="Details of the activity including activity, date and time, weather and driving information")
    date_time: str = Field(..., description="Date and time of the activity")
    weather_info: str = Field(..., description="Weather information on the activity location")
    driving_info: str = Field(..., description="Driving information to the activity location")
    description: str = Field(..., description="Description of the activity")
    category: str = Field(..., description="Category of the activity")
    why_its_suitable: str = Field(..., description="Why it's suitable for the traveler")
    reviews: Optional[List[str]] = Field(..., description="List of reviews")
    rating: Optional[float] = Field(..., description="Rating of the activity")
    cost: Optional[float] = Field(..., description="Cost of the activity")
    average_duration: Optional[float] = Field(..., description="Average duration of the activity")    

class ActivityContainer(BaseModel):
    '''A container for user preference and recommended activities based on the user preference.'''
    name: str = "User Preference and Activities Container"
    description: str = "This class contains the user's preferences for the trip and the list of activities recommended based on these preferences."
    user_preference: UserPreference = Field(..., description="User preference")
    activities: List[Activity] = Field(..., description="List of recommended activities based on user preference")

class Restaurant(Activity):
    name: str = Field(..., description="Name of the restaurant")
    location: str = Field(..., description="Location of the restaurant")
    latitude: float = Field(..., description="Latitude of the restaurant")
    longitude: float = Field(..., description="Longitude of the restaurant")    
    category: str = "Dining"
    cuisine: str = Field(..., description="Cuisine of the restaurant")

class ActivityNearbyRestaurantAssocs(BaseModel):
    activity_name: str = Field(..., description="Name of the activity")
    nearby_restaurant: Restaurant = Field(..., description="Details of the nearby restaurant")


####################################################################################################
# Define classes related to weather.
####################################################################################################
class WeatherDetails(BaseModel):
    date: str = Field(..., description="Date and time of the weather forecast")
    temp: int = Field(..., description="Temperature")
    code: int = Field(..., description="WMO weather code")
    desc: str = Field(..., description="Description of the weather")


####################################################################################################
# Define the itinerary and weather classes.
####################################################################################################
class DayPlan(BaseModel):
    date_of_the_day: str = Field(..., description="Date of the day")
    theme_of_the_day: str = Field(..., description="Theme of the day")
    activity_details: List[ActivityDetail] = Field(..., description="List of activity details for the day")
    return_to_hotel_driving_info: str = Field(..., description="Driving information to return to the hotel")
    packing_list: List[str] = Field(..., description="List of items to pack for the day")

class Itinerary(BaseModel):
  name: str = Field(..., description="Name of the itinerary, something funny")
  user_preference: UserPreference = Field(..., description="User preference")
  day_plans: List[DayPlan] = Field(..., description="List of day plans")


####################################################################################################
# Define the route planning input class.
####################################################################################################
class RoutePlanningInput(BaseModel):
    user_preference: UserPreference = Field(..., description="User preference")
    recommended_activities: List[Activity] = Field(..., description="List of recommended activities")
    activity_to_restaurant_assocs: List[ActivityNearbyRestaurantAssocs] = Field(..., description="List of associations between activities and nearby restaurants")
    weather_forecasts: List[WeatherDetails] = Field(..., description="List of weather forecasts")

class RecommendedActivitiesContainer(BaseModel):
    user_preference: UserPreference = Field(..., description="User preference")
    recommended_activities: List[Activity] = Field(..., description="List of recommended activities")

class ActivityToRestaurantAssocsContainer(BaseModel):
    activity_to_restaurant_assocs: List[ActivityNearbyRestaurantAssocs] = Field(..., description="List of associations between activities and nearby restaurants")

class WeatherForecastsContainer(BaseModel):
    weather_forecasts: List[WeatherDetails] = Field(..., description="List of weather forecasts")