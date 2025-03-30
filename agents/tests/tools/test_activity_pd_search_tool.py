from rt_ai_trip_planner.model import ActivityContainer, OptimizationOptions
from rt_ai_trip_planner.tools.activity_pd_search_tool import ActivityDataFrameSearchTool


def test_ActivityDataFrameSearchTool_run_not_null():
    # Prepare inputs.
    destination='Los Angeles, CA'
    start_date='02-17-2025'
    end_date='02-20-2025'
    interests=['Entertainment/Amusement Park', 'Zoo', 'Museum']
    hotel_location='West Covina, CA'
    optimization_options=OptimizationOptions(
        by_weather = True,
        by_traffic = True,
        by_family_friendly = True,
        by_safety = True,
        by_cost=False,
        min_rating=0.0
    )
    optimization_options_dict = optimization_options.__dict__

    # Verify the search tool return a valid result.
    activity_search_tool = ActivityDataFrameSearchTool()
    result: ActivityContainer = activity_search_tool.run(destination, start_date, end_date, interests, hotel_location, optimization_options_dict)

    assert result is not None
    assert len(result.activities) > 0

def test_ActivityDataFrameSearchTool_run_invalid_city():
    # Prepare invalid inputs.
    destination='NOT_A_CITY'
    start_date='02-17-2025'
    end_date='02-20-2025'
    interests=['Entertainment/Amusement Park', 'Zoo', 'Museum']
    hotel_location='West Covina, CA'
    optimization_options=OptimizationOptions(
        by_weather = True,
        by_traffic = True,
        by_family_friendly = True,
        by_safety = True,
        by_cost=False,
        min_rating=0.0
    )
    optimization_options_dict = optimization_options.__dict__

    # Verify the search tool return a blank activity list.
    activity_search_tool = ActivityDataFrameSearchTool()
    result: ActivityContainer = activity_search_tool.run(destination, start_date, end_date, interests, hotel_location, optimization_options_dict)

    assert len(result.activities) == 0
