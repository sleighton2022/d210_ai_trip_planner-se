###########################################################################
## Integration between FastAPI and RtAiTripPlanner (crewAI) starts here ##
## TODO: 
## 1. issue where first item on activity plan is not rendered in map
## 2. Background and secondary background colors
## 3. Additional layout and formatting of titles, tabs, big header, etc.
###########################################################################

## this version of the app uses tabs to sepearate itineraries

import sys
import os
import streamlit as st
import requests
from datetime import date
import json
from itertools import zip_longest
import time
import asyncio
import aiohttp

import folium
from folium import plugins

# sys.path.append('./agents/src/rt_ai_trip_planner')
# sys.path.append('./agents/src')
# sys.path.append('./agents')
#sys.path.append('../../common')


# Get the absolute path of the directory containing the current script (main.py)
script_dir = os.path.dirname(os.path.abspath(__file__))

# Go up two levels to get the project root directory
project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))

# Construct the absolute path to the 'common' directory
common_path = os.path.join(project_root, 'common')

# Add the 'common' directory to sys.path if it's not already there
if common_path not in sys.path:
    sys.path.append(common_path)


print(os.getcwd())
from model import UserPreference as aitp_user_preference, Itinerary as aitp_itinerary, DayPlan, Activity
from utils.geocodes_utils import GeocodeUtils


# Define the default URL
default_backend_url = "http://127.0.0.1:8000/ai-trip-planner/v2/plan"

# Get the value from the environment variable "BACKEND_URL",
# or use the default_backend_url if it's not set.
backend_url = os.getenv("BACKEND_URL", default_backend_url)

# async call to get itinerary
async def fetch_itinerary(backend_url, request_payload):
    async with aiohttp.ClientSession() as session:
        async with session.get(backend_url, json=request_payload) as response:
            # Get the status code
            status_code = response.status
            headers = response.headers
            content = await response.json()
            
            return {
                'status_code': status_code,
                'headers': dict(headers),
                'content': content
            }
            # return response
            
async def async_request():
    response = await fetch_itinerary(backend_url, request_payload)
    return response

class POIMap:    
    # def show_map(self, day_plan: DayPlan):
    def show_map(self, hotel_location: Activity, day_plan: DayPlan):
        # Create the map title.
        # title = f"{day_plan.date_of_the_day}: {day_plan.theme_of_the_day}"
        
        # Create the map with the first activity as the center.
        init_lat_long = [day_plan.activity_details[0].activity.latitude, day_plan.activity_details[0].activity.longitude]
        day_map = folium.Map(
            location=init_lat_long, 
            zoom_start=10,
            width="100%",
            height="100%",
        )
        # marker_cluster = plugins.MarkerCluster().add_to(day_map)
        marker_cluster = plugins.MarkerCluster(overlay=True, show=True, control=True).add_to(day_map)  
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

        for activity_detail in day_plan.activity_details:
            activity = activity_detail.activity
            lat_long = [activity.latitude, activity.longitude]
            folium.Marker(
                lat_long,
                popup=folium.Popup(
                    f"<b>{activity.name}</b><br>"
                    f"{activity_detail.date_time} | {activity_detail.weather_info} <br>",
                    # f"{activity_detail.description}<br>",
                    max_width=450,
                ),
            ).add_to(day_map)

        # st.subheader(title, divider=True)
        st.components.v1.html(folium.Figure().add_child(day_map).render(), height=650)


st.set_page_config(
    layout="wide",
    page_icon=":airplane_departure:",
    page_title="SimplifAI Travel",
    initial_sidebar_state="expanded"
    )

st.sidebar.title(":airplane: SimplifAI Travel")
st.sidebar.header("Your All-in-One Itinerary Planner", divider=True)

destination_city = st.sidebar.text_input("Where do you want to go?", placeholder="Search for destination city")
departure_location = st.sidebar.text_input("What is your starting point?", placeholder="Example: Hilton Midtown")
from_date = st.sidebar.date_input("From Date", min_value=date.today())
to_date = st.sidebar.date_input("To Date", min_value=from_date)
categories = st.sidebar.multiselect("Interests", ["Landmarks", "Entertainment", "History", "Nature", "Museums", "Food", "Shopping", "Nightlife"])
optimized_options = st.sidebar.multiselect("Optimized By", ["Weather", "Traffic", "Family Friendly", "Safety", "Cost"])
restaurant_rating = st.sidebar.number_input(
    "Minimum Restaurant Rating",
    min_value = 0.0,
    max_value = 5.0, 
    step = 0.5,
    format = "%0.1f"
)

# button to generate itinerary
generate_itinerary = st.sidebar.button("Generate Itinerary")

# generate itinerary when clicked, else display cover
if not generate_itinerary:
    image_file_path = os.path.join(common_path, "ny_image.jpg")
    st.markdown(
        """
        <h1 style="text-align: center;">Love travel, hate planning?</h1>
        <p style="text-align: center;">Plan your next adventure in seconds through the power of AI</p>
        """,
        unsafe_allow_html=True
    )
    st.markdown(
        f"""
        <style>
        .bg-container {{
            position: relative;
            width: 70%;
            height: 200px;  /* Set the height of the container */
            background-image: url(data:image/jpeg;base64,{st.image(image_file_path, use_column_width=True, output_format="JPEG")._image_data_url});
            background-size: contain;
            background-position: center;
        }}
        .text-overlay {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: black;
            font-size: 30px;
            font-weight: bold;
            text-align: center;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

else:

    # generate json payload
    request_payload = {
        "destination_city": destination_city,
        "departure_location": departure_location,
        "from_date": from_date.strftime('%m-%d-%Y'),#.isoformat()
        "to_date": to_date.strftime('%m-%d-%Y'),
        "interest_categories": categories if categories else ["General Activities"],
        "optimized_options": optimized_options if optimized_options else ['None'], 
        "min_rating": restaurant_rating
    }

    with st.spinner("Generating Itinerary..."):
        # request response
        # response = requests.get(backend_url, json=request_payload) # sync request
        response = asyncio.run(async_request())
        st.success(f"Itinerary Ready!")
        # TODO Asynchronous calling, setup some splash page so that users can chill
        
        if response['status_code'] == 200:
            # itinerary:aitp_itinerary = aitp_itinerary(**response.json()) #entire itinerary json
            itinerary:aitp_itinerary = aitp_itinerary(**response['content'])
            st.header(f"{itinerary.name}", divider='gray') #set page header
            
            tabs = st.tabs([f"Day {day_num}: {dp.theme_of_the_day}" for day_num, dp in enumerate(itinerary.day_plans, start=1)])

            # to plot hotel location
            user_preference = itinerary.user_preference
            hotel_latitude, hotel_longitude = GeocodeUtils.get_lat_lon(user_preference.hotel_location)
            hotel_location = Activity(
                name="Hotel | Starting Point",
                location=user_preference.hotel_location,
                latitude=hotel_latitude,
                longitude=hotel_longitude,
                category="Hotel",
            )
            # # loop through each day plan
            for day_num, (dp, tab) in enumerate(zip(itinerary.day_plans, tabs), start=1):
                # set container parameters
                # with col.container(border=True, height=700):
                with tab:
                    col1, col2 = st.columns(2, vertical_alignment="top")
                    
                    # render itinerary in first column
                    with col1:
                        # title for day plans
                        st.subheader(f"Day {day_num} ({dp.date_of_the_day}): {dp.theme_of_the_day}", anchor=False)
                        # st.markdown(f"##### Date: {dp.date_of_the_day}", unsafe_allow_html=True)
                        st.subheader(f"Itinerary:", divider="gray", anchor=False)

                        # add detailed activities as expanding containers
                        for act_num, act_det in enumerate(dp.activity_details, start=1):
                            activity = act_det.activity
                            start_time = act_det.date_time.split(' - ')[0]
                            st.markdown(f"##### {act_num}. {act_det.date_time}: {activity.name}", unsafe_allow_html=True)
                            # expanded = True if act_num == 1 else False
                            expand = st.expander(f"More Details", icon="➡️")
                            
                            expand.markdown(f"""
                                - 📌 **Location:** {activity.location}
                                - :sparkles: **Details:** {act_det.description}
                                - ❓ **Why Suggest?** {act_det.why_its_suitable}
                                - 🚗 **Transportation:** {act_det.driving_info}
                                - ⭐ **Rating:** {act_det.rating}
                                - 📝 **Reviews:**
                                    - "{act_det.reviews[0]}"
                                    - "{act_det.reviews[1]}"
                                """, unsafe_allow_html=True)

                        expand2 = st.expander(f"Additional Info", icon="ℹ️", expanded=True)
                        expand2.write(f"🏨 **Returning Home:** {dp.return_to_hotel_driving_info}")
                        expand2.write(f"🧳 **Packing List:** {', '.join(dp.packing_list)}")
                    
                    # render map in second column
                    with col2:
                        poi_map = POIMap()
                        # day_plan = DayPlan(**dp)    
                        poi_map.show_map(hotel_location, dp)
                        # poi_map.show_map(dp)

        else:
            st.error("Failed to generate itinerary. Try again.")

