import json
import streamlit as st
import folium
from folium import plugins
from pydantic import BaseModel, Field
from model import Activity, DayPlan
from rt_ai_trip_planner.utils.geocodes_utils import GeocodeUtils


class POIMapUtils:
    def plot_itinerary(self, itinerar: dict):
        """
        Plot a list of maps for the itinerary where each map contains the visiting places in a day plan.
        """
        # Create the hotel location.
        user_preference = itinerary['user_preference']
        hotel_latitude, hotel_longitude = GeocodeUtils.get_lat_lon(user_preference['hotel_location'])
        hotel_location = Activity(
            name="Hotel | Starting Point",
            location=user_preference['hotel_location'],
            latitude=hotel_latitude,
            longitude=hotel_longitude,
            category="Hotel",
        ) 

        # Plot a map for each day plan.
        for dp_dict in itinerary['day_plans']:
            day_plan = DayPlan(**dp_dict)    
            self._show_map(hotel_location, day_plan)            
    
    def _show_map(self, hotel_location: Activity, day_plan: DayPlan):
        """
        Show a map with the hotel and activities for a given day plan.
        """
        # Create the map title.
        title = f"{day_plan.date_of_the_day}: {day_plan.theme_of_the_day}"
        
        # Create the map with the first activity as the center.
        init_lat_long = [day_plan.activity_details[0].activity.latitude, day_plan.activity_details[0].activity.longitude]
        day_map = folium.Map(
            location=init_lat_long, 
            zoom_start=10,
            width="90%",
            height="75%",
        )

        # Add a marker for the hotel.
        folium.Marker(
            location=[hotel_location.latitude, hotel_location.longitude], 
            icon=folium.Icon(icon='hotel', prefix='fa', color='purple'),
            popup=folium.Popup(
                f"<b>{hotel_location.name}</b><br>"
                f"{hotel_location.location}<br>",
                max_width=450,
            ),
        ).add_to(day_map)

        marker_cluster = plugins.MarkerCluster(overlay=True, show=True, control=True).add_to(day_map)        
        target_parent = day_map

        for idx, activity_detail in enumerate(day_plan.activity_details):
            activity = activity_detail.activity
            lat_long = [activity.latitude, activity.longitude]
            return_driving_info = day_plan.return_to_hotel_driving_info if idx == len(day_plan.activity_details) - 1 else ""            

            folium.Marker(
                lat_long,
                icon=folium.Icon(icon=f'{idx+1}', prefix='fa'),
                popup=folium.Popup(
                    f"<b>{activity.name}</b><br>"
                    f"{activity_detail.date_time} | {activity_detail.weather_info} <br>"
                    f"{activity_detail.driving_info}<br>{return_driving_info}",
                    max_width=450,
                ),
            ).add_to(target_parent)

        st.subheader(title, divider=True)
        st.components.v1.html(folium.Figure().add_child(day_map).render(), height=500)


# Main method to run the app: $ streamlit run map_utils.py 
if __name__ == "__main__":
    # Initialize UI.
    st.set_page_config(
        page_title=None,
        page_icon=None,
        layout="centered",
        initial_sidebar_state="auto",
        menu_items=None,
    )

    # Load the sample itinerary.
    with open('../../../data/sample-itinerary.json', 'r') as file:
        itinerary = json.load(file)

    # Create the POI map.
    poi_map = POIMapUtils()
    poi_map.plot_itinerary(itinerary)
