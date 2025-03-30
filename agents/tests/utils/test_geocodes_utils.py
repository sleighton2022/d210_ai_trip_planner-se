from rt_ai_trip_planner.utils.geocodes_utils import GeocodeUtils


def test_GeocodeUtils_get_lat_long_valid_city():
    place_name = "West Covina, CA"
    place_latitude, place_longitude = GeocodeUtils.get_lat_lon(place_name)
    print(f"[INFO] City Name: {place_name}, Latitude: {place_latitude}, Longitude: {place_longitude}")

    assert place_latitude != 0
    assert place_longitude != 0

def test_GeocodeUtils_reverse_geocode():
    place_latitude = 32.7767
    place_longitude = -96.7970
    
    place_name = GeocodeUtils.reverse_geocode(place_latitude, place_longitude)
    print(f"[INFO] City Name: {place_name}, Latitude: {place_latitude}, Longitude: {place_longitude}")

    assert place_name is not None
    assert "dallas" in place_name.lower()
