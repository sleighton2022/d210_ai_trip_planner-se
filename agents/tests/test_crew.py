import json
import pytest

from rt_ai_trip_planner.model import OptimizationOptions, UserPreference
from rt_ai_trip_planner.crew import RtAiTripPlanner
from rt_ai_trip_planner.utils.crew_io_utils import CrewInputOutputUtils


@pytest.fixture
def crew_inputs() -> dict:
    user_preference = UserPreference(
        destination='Los Angeles, CA',
        start_date='02-17-2025',
        end_date='02-18-2025',
        interests=['Entertainment/Amusement Park', 'Zoo', 'Museum'],
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
    return CrewInputOutputUtils.prepare_crew_inputs(user_preference)

def test_find_activity_task(crew_inputs):
    # Configure crew.
    planner = RtAiTripPlanner(
        run_find_activity_task=True,
        run_find_nearby_restaurant_task=False,
        run_find_weather_forecast_task=False,
        run_plan_activity_task=False
    )
    crew_output = planner.crew().kickoff(inputs=crew_inputs)

    assert crew_output is not None
    assert len(crew_output.json_dict['activities']) > 3
    CrewInputOutputUtils.inspect_crew_output(crew_output)

def test_find_nearby_restaurant_task(crew_inputs):
    # Set the activity names as it is required for the restaurant finder task.
    crew_inputs['activity_names'] = [
        "Universal Studios Hollywood",
        "Los Angeles Zoo",
        "California Science Center",
        "The Getty",
        "Los Angeles County Museum of Art",
        "Griffith Observatory",
        "La Brea Tar Pits and Museum",
        "The Broad",
        "Natural History Museum of Los Angeles County",
        "Hollywood Wax Museum"
    ]        

    # Configure crew.
    planner = RtAiTripPlanner(
        run_find_activity_task=False,
        run_find_nearby_restaurant_task=True,
        run_find_weather_forecast_task=False,
        run_plan_activity_task=False
    )
    crew_output = planner.crew().kickoff(inputs=crew_inputs)
    
    assert crew_output is not None
    assert len(json.loads(crew_output.raw)) > 3
    CrewInputOutputUtils.inspect_crew_output(crew_output)
    
    # Reset shared inputs.
    crew_inputs['activity_names'] = []

def test_find_weather_forecast_task(crew_inputs):
    # Configure crew.
    planner = RtAiTripPlanner(
        run_find_activity_task=False,
        run_find_nearby_restaurant_task=False,
        run_find_weather_forecast_task=True,
        run_plan_activity_task=False
    )
    crew_output = planner.crew().kickoff(inputs=crew_inputs)

    assert crew_output is not None
    assert len(json.loads(crew_output.raw)) > 3
    CrewInputOutputUtils.inspect_crew_output(crew_output)
