import json
import sys
from typing import List
import streamlit as st
import folium
from folium import plugins
from pydantic import BaseModel, Field
from ..model import Activity, DayPlan, RoutePlanningInput
from geocodes_utils import GeocodeUtils


class POIMapUtils:
    def plot_itinerary(self, itinerary: dict):
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
            self._show_itinerary_map(hotel_location, day_plan)            
    
    def _show_itinerary_map(self, hotel_location: Activity, day_plan: DayPlan):
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
            width="100%",
            height="75%",
        )

        folium.plugins.Fullscreen(
            position="topright",
            title="Expand",
            title_cancel="Collapse",
            force_separate_button=True,
        ).add_to(day_map)        

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
        target_parent = marker_cluster # Chose how to display the markers: marker_cluster, day_map

        for idx, activity_detail in enumerate(day_plan.activity_details):
            activity = activity_detail.activity
            lat_long = [activity.latitude, activity.longitude]
            return_driving_info = f"<br>Return to Hotel: {day_plan.return_to_hotel_driving_info}" if idx == len(day_plan.activity_details) - 1 else ""     
            
            icon_color = 'green' if activity.category == 'Restaurant' else 'blue'
            print(f"Activity: {activity.name}, category: {activity.category}, icon_color: {icon_color}")       

            folium.Marker(
                lat_long,
                icon=folium.Icon(icon=f'{idx+1}', prefix='fa', color=icon_color),
                popup=folium.Popup(
                    f"<b>{activity.name}</b><br>"
                    f"{activity_detail.date_time} | {activity_detail.weather_info} <br>"
                    f"{activity_detail.driving_info}{return_driving_info}",
                    max_width=450,
                ),
            ).add_to(target_parent)

        # Count activities and restaurants.
        total_activities = len([ad for ad in day_plan.activity_details if ad.activity.category != 'Restaurant'])
        total_restaurants = len([ad for ad in day_plan.activity_details if ad.activity.category == 'Restaurant'])

        st.subheader(title)
        st.write(f"**Total Activities: {total_activities} | Total Restaurents: {total_restaurants}**")

        # Show activity summary.
        for idx, activity_detail in enumerate(day_plan.activity_details):
            activity = activity_detail.activity
            st.write(f"{idx+1}. {activity_detail.date_time} ({activity_detail.weather_info}): {activity.name} | {activity.category} | {activity_detail.driving_info}")
        st.divider()

        # Render Map.
        st.components.v1.html(folium.Figure().add_child(day_map).render(), height=500)


    def plot_places(self, input: RoutePlanningInput):
        """
        Plot the places in the route planning input.
        """
        # Create the map title.
        user_preference = input.user_preference        
        title = f"Visiting Places: {user_preference.destination}"

        recommended_restaurants = []
        for assoc in input.activity_to_restaurant_assocs:
            restaurant = assoc.nearby_restaurant
            recommended_restaurants.append(restaurant)

        # Merge two activity lists.
        visiting_activities = input.recommended_activities + recommended_restaurants

        # Find the central latitude and longitude.
        central_lat_long = [0, 0]
        for activity in visiting_activities:
            central_lat_long[0] += activity.latitude
            central_lat_long[1] += activity.longitude
        central_lat_long[0] /= len(visiting_activities)
        central_lat_long[1] /= len(visiting_activities)

        # Create the map and center at the calculated latitude and longitude.
        init_lat_long = central_lat_long
        main_map = folium.Map(
            location=init_lat_long, 
            zoom_start=10,
            # width="100%", height="75%",
            width="100%", height="100%"
        )

        folium.plugins.Fullscreen(
            position="topright",
            title="Expand",
            title_cancel="Collapse",
            force_separate_button=True,
        ).add_to(main_map)

        # Create the hotel location.
        hotel_latitude, hotel_longitude = GeocodeUtils.get_lat_lon(user_preference.hotel_location)
        hotel_location = Activity(
            name="Hotel | Starting Point",
            location=user_preference.hotel_location,
            latitude=hotel_latitude,
            longitude=hotel_longitude,
            category="Hotel",
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
        ).add_to(main_map)

        # Define the layer (main map or marker cluster) to add the markers.
        marker_cluster = plugins.MarkerCluster(overlay=True, show=True, control=True).add_to(main_map)        
        target_parent = marker_cluster # marker_cluster, main_map
        
        # Add markers for the visiting activities.
        def _plot_marker(activity_list: List[Activity], icon: str, icon_color: str):
            for idx, activity in enumerate(activity_list):
                lat_long = [activity.latitude, activity.longitude]            
                icon = f'{idx+1}'

                folium.Marker(
                    lat_long,
                    icon=folium.Icon(icon=icon, prefix='fa', color=icon_color),
                    popup=folium.Popup(
                        f"<b>{activity.name}</b><br>"
                        f"{activity.location} | {activity.category} <br>",
                        max_width=450,
                    ),
                ).add_to(target_parent)

        _plot_marker(input.recommended_activities, 'star', 'blue')
        _plot_marker(recommended_restaurants, 'utensils', 'orange')
        
        st.subheader(title)
        st.write(f"* Travel Date: {user_preference.start_date} to {user_preference.end_date}")
        st.write(f"* Total places: {len(input.recommended_activities)}")
        st.write(f"* Total restaurents: {len(recommended_restaurants)}")
        st.divider()
        st.components.v1.html(folium.Figure().add_child(main_map).render(), height=500)


# Main method to run the app: $ streamlit run map_utils.py 
if __name__ == "__main__":
    run_option = 'itinerary' # input
    if len(sys.argv) > 1:        
        run_option = sys.argv[1]
        if run_option not in ['itinerary', 'input']:
            print("Invalid run option. Use 'itinerary' or 'input'.")
            sys.exit(1)
    print("Run Option:", run_option)

    # Initialize UI.
    st.set_page_config(
        page_title=None,
        page_icon=None,
        layout="centered",
        initial_sidebar_state="auto",
        menu_items=None,
    )    

    poi_map = POIMapUtils()
    if run_option == 'input':
    # Load the sample itinerary.
        with open('../../../data/route-planning-input.json', 'r') as file:
            route_planning_input_dict = json.load(file)

        # Create the POI map.        
        route_planning_input = RoutePlanningInput(**route_planning_input_dict)
        poi_map.plot_places(route_planning_input)    
    else:
        with open('../../../data/sample-itinerary.json', 'r') as file:
            itinerary = json.load(file)

        # Create the POI map.
        poi_map.plot_itinerary(itinerary)
