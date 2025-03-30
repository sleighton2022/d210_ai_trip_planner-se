from rt_ai_trip_planner.model import WeatherDetails
from rt_ai_trip_planner.tools.weather_tool import WeatherOpenMeteoSearchTool


def test_WeatherOpenMeteoSearchTool_get_lat_long_valid_city():
    # Get lat/long of a valid location.
    weather_search_tool = WeatherOpenMeteoSearchTool()    
    result = weather_search_tool._get_lat_long("Los Angeles, CA")
    assert result is not None

def test_WeatherOpenMeteoSearchTool_get_lat_long_invalid_city():
    # Get lat/long of a valid location.
    weather_search_tool = WeatherOpenMeteoSearchTool()    
    result = weather_search_tool._get_lat_long("NOT_A_CITY")
    assert result[0] == 0
    assert result[1] == 0

def test_WeatherOpenMeteoSearchTool_run_valid_city():
    # Get weather of a valid location.
    weather_search_tool = WeatherOpenMeteoSearchTool()
    weather_details_list: list[WeatherDetails] = weather_search_tool.run('Los Angeles, CA', '2025-02-17', '2025-02-18')
    assert weather_details_list is not None
    assert len(weather_details_list) > 0
