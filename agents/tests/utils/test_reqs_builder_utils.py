
import json
import pytest

from rt_ai_trip_planner.model import OptimizationOptions, UserPreference
from rt_ai_trip_planner.utils.reqs_builder_utils import TripRequirementsBuilderUtils

@pytest.fixture
def builder() -> TripRequirementsBuilderUtils:
    user_preference = UserPreference(
        destination='Los Angeles, CA', # 'Los Angeles, CA', 
        start_date='02-17-2025',
        end_date='02-20-2025',
        interests=['Entertainment/Amusement Park', 'Zoo', 'Museum'], # ['zoo', 'museums', 'beaches'],
        hotel_location='West Covina, CA',
        optimization_options=OptimizationOptions(
            by_weather = True,
            by_traffic = True,
            by_family_friendly = True,
            by_safety = True,
            by_cost=False,
            min_rating=0.0
        )
    )
    return TripRequirementsBuilderUtils(user_preference)

def test_activity_requirements(builder: TripRequirementsBuilderUtils):
    req = builder.activity_requirements()
    print(f"[DEBUG] activity_requirements:\n{req}\n")
    assert req is not None

def test_traffic_requirements(builder: TripRequirementsBuilderUtils):
    req = builder.traffic_requirements() 
    print(f"[DEBUG] traffic_requirements:\n{req}\n")
    assert req is not None

def test_weather_requirements(builder: TripRequirementsBuilderUtils):
    req = builder.weather_requirements()
    print(f"[DEBUG] weather_requirements:\n{req}\n")
    assert req is not None    

def test_restaurant_requirements(builder: TripRequirementsBuilderUtils):
    req = builder.restaurant_requirements()
    print(f"[DEBUG] restaurant_requirements:\n{req}\n")
    assert req is not None
