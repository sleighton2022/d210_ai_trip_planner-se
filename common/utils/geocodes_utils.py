import pandas as pd
from geopy.geocoders import Nominatim
from geopy.point import Point


geolocator = Nominatim(user_agent="rt-trip-planner")


class GeocodeUtils:
    @staticmethod
    def reverse_geocode(lat, lon):
        try:
            location = geolocator.reverse(Point(lat, lon))
            print(f"[INFO] Reverse geocoding for {lat}, {lon} returned: {location.address}")
            return location.address
        except:
            return None
        
    @staticmethod
    def populate_address(file_path: str):
        # Load the data
        df = pd.read_csv("../../data/MVP_Data.csv")

        # Apply reverse geocoding only to rows where 'address' is missing
        df['address'] = df.apply(
            lambda row: GeocodeUtils.reverse_geocode(row['latitude'], row['longitude']) if pd.isna(row['address']) else row['address'],
            axis=1
        )

        # save the data
        df.to_csv("../data/MVP_Data.csv", index=False)

    @staticmethod
    def get_lat_lon(address: str) -> tuple:
        code = geolocator.geocode(address)
        return code.latitude, code.longitude