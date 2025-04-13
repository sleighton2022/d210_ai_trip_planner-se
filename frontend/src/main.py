###########################################################################
## Integration between FastAPI and RtAiTripPlanner (crewAI) starts here ##
## TODO: 
## 1. issue where first item on activity plan is not rendered in map
## 2. Background and secondary background colors
## 3. Additional layout and formatting of titles, tabs, big header, etc.
## # TODO setup some splash page so that users can chill
    # Idea: have users explore the general map of area
    # Idea 2: Genaerate more itineraries
    # Idea 3: Display recommendations using Google API
###########################################################################

## this version of the app uses tabs to sepearate itineraries

import sys
import os
import streamlit as st
import pandas as pd
import requests
from datetime import date, timedelta
import json
from itertools import zip_longest
import asyncio
import aiohttp
import threading
import time
import random
import webbrowser
from PIL import Image
from io import BytesIO
from collections import defaultdict


import folium
from folium import plugins

# sys.path.append('./agents/src/rt_ai_trip_planner')
# sys.path.append('./agents/src')
# sys.path.append('./agents')
sys.path.append('./common')

from common.model import UserPreference as aitp_user_preference, Itinerary as aitp_itinerary, DayPlan, Activity
from common.utils.geocodes_utils import GeocodeUtils
from dotenv import load_dotenv, find_dotenv


backend_url = "http://127.0.0.1:8000/ai-trip-planner/v2/plan"
#backend_url = 'http://0.0.0.0:8000/ai-trip-planner/v2/plan'

dotenv_path = find_dotenv(usecwd=True)
load_dotenv(dotenv_path=dotenv_path)
places_api = os.getenv('GOOGLE_PLACES_API')

# async call to call the backend and fetch the itinerary
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
# kickoff function to start async events          
def run_async_task(backend_url, request_payload):
    """Ensures the async task runs inside a proper event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(background_fetch(backend_url, request_payload))

# secondary function to start async call and display status updates on frontend
async def background_fetch(backend_url, request_payload):
    with st.status("Generating your personalized itinerary") as status:
        # print(status) #debugging
        task = asyncio.create_task(fetch_itinerary(backend_url, request_payload))
        messages = [
            "Generating your personalized itinerary .",
            "Generating your personalized itinerary ..",
            "Generating your personalized itinerary ...",
            "Finding attractions .",
            "Finding attractions ..",
            "Finding attractions ...",
            "Finding nearby restaurants .", 
            "Finding nearby restaurants ..", 
            "Finding nearby restaurants ...", 
            "Retrieving weather forecasts on the travel days .", 
            "Retrieving weather forecasts on the travel days ..", 
            "Retrieving weather forecasts on the travel days ...", 
            "Creating itineraries and optimizing routes .", 
            "Creating itineraries and optimizing routes ..", 
            "Creating itineraries and optimizing routes ...", 
            "Preparing itineraries report .",
            "Preparing itineraries report ..",
            "Preparing itineraries report ..."
            ]
        i = 0
        # while task is running in background, rotate through messages
        while not task.done():
            status.update(label = messages[i % len(messages)], state="running")
            i += 1
            await asyncio.sleep(3)
        
        # TODO track number of itineraries, set base case and limit of 3
        # if no itinerary
        if st.session_state['num_itin'] == 0:
            st.session_state['itineraries'] = await task
            st.session_state['num_itin'] += 1
        status.update(label="Itinerary complete!", state="complete")
        time.sleep(3) # wait 3 seconds so message can display
    st.rerun()

# for POI map, jitter coordinates slightly to the right so they don't overlap
def offset_coordinates(lat, long, offset=0.0008):
    """Apply a slight offset to coordinates to break overlap."""
    return lat + offset, long + offset

# set of marker types 
def get_activity_icon(activity_type):
    # https://github.com/python-visualization/folium/issues/617
    """Returns a Folium Icon based on the activity type."""
    activity_icons = {
        "Restaurant": folium.Icon(icon="cutlery", color="red", prefix='fa'),
        "Entertainment/Amusement Park": folium.Icon(icon="star", color="blue", prefix='fa'),
        "Park/Scenic Spots": folium.Icon(icon="tree", color="green", prefix='fa'),
        "Shopping": folium.Icon(icon="shop", color="purple", prefix='fa'),
        "Landmark": folium.Icon(icon="landmark", color="blue", prefix='fa'),
        "Museum": folium.Icon(icon="university", color="darkblue", prefix='fa'),
        "Zoo": folium.Icon(icon="paw", color="darkgreen", prefix='fa'),
    }
    
    return activity_icons.get(activity_type, folium.Icon(icon="circle-info", color="blue", prefix='fa'))  # Default icon

# generate map based on itinerary location
class POIMap:    
    def show_map(self, hotel_location: Activity, day_plan: DayPlan):
        # Create the map title.
        # title = f"{day_plan.date_of_the_day}: {day_plan.theme_of_the_day}"
        
        # Create the map with the first activity as the center.
        init_lat_long = [day_plan.activity_details[0].activity.latitude, day_plan.activity_details[0].activity.longitude]
        day_map = folium.Map(
            location=init_lat_long, 
            zoom_start=10,
            width="100%",
            height="90%",
        )
        # marker_cluster = plugins.MarkerCluster().add_to(day_map)
        marker_cluster = plugins.MarkerCluster(overlay=True, show=True, control=True).add_to(day_map)     
        target_parent = day_map

        # store coordinates
        placed_coordinates = []

        for i, activity_detail in enumerate(day_plan.activity_details, start=1):
            # plot location
            activity = activity_detail.activity
            lat_long = [activity.latitude, activity.longitude]
            
            # Add the new coordinates to the placed coordinates list
            if lat_long in placed_coordinates:
                # Apply offset if there's an overlap
                lat_long = offset_coordinates(activity.latitude, activity.longitude)
            placed_coordinates.append(lat_long)

            folium.Marker(
                location = lat_long,
                popup=folium.Popup(
                    f"<b>{i}. {activity.name}</b><br>"
                    f"{activity_detail.date_time} | {activity_detail.weather_info} <br>",
                    # f"{activity_detail.description}<br>",
                    max_width=450,
                ),
                icon=get_activity_icon(activity.category)
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

        folium.plugins.Fullscreen(
            position="topright",
            title="Expand me",
            title_cancel="Exit me",
            force_separate_button=True,
        ).add_to(day_map)

        st.components.v1.html(folium.Figure().add_child(day_map).render(), height=650)

# generate temporary splashpage on page load
def splash_page():
    with st.container(border=False):
        st.markdown(
            """
            <h2 style="text-align: center;">Love travel, hate planning?</h2>
            <p style="text-align: center;">Plan your next adventure through the power of AI</p>
            """,
            unsafe_allow_html=True
        )
    with st.container(height=600, border = False):
        st.markdown('<div class="non-scroll-container">', unsafe_allow_html=True)
        st.image("./common/la_image.jpg", use_container_width=True, output_format="JPEG")

st.set_page_config(
    layout="wide",
    page_icon=":airplane_departure:",
    page_title="SimplifAI Travel",
    initial_sidebar_state="expanded"
    )

# Load CSV data for recommendations
@st.cache_data
def load_recommendations(csv_path):
    return pd.read_csv(csv_path)

# Function to get top 4 recommendations per category for a given city
# def old_get_top_recommendations(df, categories, city):
    top_recs = []
    city_df = df[df['city'].str.lower() == city.lower()]
    for category in categories:
        filtered = city_df[city_df['overarching_category'] == category]
        top_10 = filtered.nlargest(10, 'normalized_value')  # Assuming 'normalized_value' is the ranking factor
        pick_3 = top_10.sample(min(len(filtered), 3), random_state=42)
        top_recs.append(pick_3)
    return pd.concat(top_recs) if top_recs else None

def get_top_recommendations_nearby(categories, city, api_key):
    """Fetch top 3 places per category near a city using Google Places API."""
    # lat, lng = get_lat_lng(city, api_key)
    lat, lng = GeocodeUtils.get_lat_lon(city)    
    print("[DEBUG] categories ",categories)
    print("[DEBUG] city ",city)
    print("[DEBUG] api_key",api_key)
    if lat is None:
        raise ValueError(f"Could not get coordinates for city: {city}")
    
    all_places = []
    for category in categories:
        # Google Nearby Places API
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            "location": f"{lat},{lng}",
            "radius": 18000,  # 20 km
            "type": category.lower(),  # must be a valid Google place type
            "key": api_key,
            "rankby": "prominence"  # could be "distance" as an alternative
        }
        
        response = requests.get(url, params=params)
        print("[DEBUG] params", params)
        print("[DEBUG] response", response)
        if response.status_code == 200:
            results = response.json().get("results", [])[:10]
            # Filter out places without a rating
            rated_results = [place for place in results if "rating" in place]

            # Sort by rating, then user_ratings_total as a tiebreaker
            sorted_by_rating = sorted(
                rated_results,
                key=lambda x: (x["rating"], x.get("user_ratings_total", 0)),
                reverse=True
            )
            # Sample 3 from top 10 
            top_n = sorted_by_rating[:10]
            sampled = random.sample(top_n, min(5, len(top_n)))

            for place in sampled:
                place_id = place.get("place_id")
                if place_id:
                    details = get_place_details(place_id, api_key)
                    if details:
                        details["overarching_category"] = category
                        all_places.append(details)
        else:
            print(f"Nearby API failed for '{category}' with status code {response.status_code}")


    print("[DEBUG] pd.Dataframe ", pd.DataFrame(all_places)) 
    return pd.DataFrame(all_places) if all_places else None

def get_place_details(place_id, api_key):
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    fields = ",".join([
        "name", "photos", "website", "formatted_phone_number", "url",
        "formatted_address", "rating", "user_ratings_total", "editorial_summary"
    ])
    params = {"place_id": place_id, "fields": fields, "key": api_key}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        result = response.json().get("result", {})

        photo_url = None
        if "photos" in result:
            photo_ref = result["photos"][0]["photo_reference"]
            photo_url = f"https://maps.googleapis.com/maps/api/place/photo?photo_reference={photo_ref}&maxwidth=400&maxheight=400&key={places_api}"
        
        return {
            "name": result.get("name"),
            "photo": photo_url,
            "website": result.get("website", "N/A"),
            "phone": result.get("formatted_phone_number", "N/A"),
            "map": result.get("url", "N/A"),
            "address": result.get("formatted_address", "N/A"),
            "rating": result.get("rating", "N/A"),
            "reviews": result.get("user_ratings_total", "N/A"),
            "description": result.get("editorial_summary", {}).get("overview", "No description available."),
        }
    return {}

# Function to get place details from Google Places API
# def old_get_place_details(place_name, city):
    search_url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={place_name}, {city}&inputtype=textquery&fields=place_id&key={places_api}"
    search_response = requests.get(search_url).json()

    if 'candidates' in search_response and search_response['candidates']:
        place_id = search_response['candidates'][0]['place_id']
        details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,photos,website,formatted_phone_number,url,formatted_address,rating,user_ratings_total,editorial_summary&key={places_api}"
        details_response = requests.get(details_url).json()
        result = details_response.get("result", {})
        
        photo_url = "./common/fallback-place-image.webp"
        if "photos" in result:
            photo_ref = result["photos"][0]["photo_reference"]
            photo_url = f"https://maps.googleapis.com/maps/api/place/photo?photo_reference={photo_ref}&maxwidth=400&maxheight=400&key={places_api}"
        
        return {
            "name": result.get("name", place_name),
            "photo": photo_url,
            "website": result.get("website", "N/A"),
            "phone": result.get("formatted_phone_number", "N/A"),
            "map": result.get("url", "N/A"),
            "address": result.get("formatted_address", "N/A"),
            "rating": result.get("rating", "N/A"),
            "reviews": result.get("user_ratings_total", "N/A"),
            "description": result.get("editorial_summary", {}).get("overview", "No description available."),
        }
    
    return {"name": place_name, "photo": photo_url, "website": "N/A", "phone": "N/A", "map": "N/A", "address": "N/A", "rating": "N/A", "reviews": "N/A", "description": "No description available."}

# Load recommendations CSV
csv_path = "./common/data/MVP_Data.csv"  # Ensure correct path
rec_df = load_recommendations(csv_path)
rec_categories = ['Entertainment/Amusement Park', 'Park/Scenic Spots', 'Shopping',
              'Landmark', 'Museum', 'Zoo']

# main website page code

# titles for sidebar
st.sidebar.title(":airplane: SimplifAI Travel")
st.sidebar.header("Your All-in-One Itinerary Planner", divider=True)

# inputs for sidebar
# destination_city = st.sidebar.text_input("What is your destination?", placeholder="Example: New York or Los Angeles") # custom input
available_cities = ["New York City, NY", "Los Angeles, CA", "Chicago, IL", "San Francisco, CA", "Boston, MA", "Seattle, WA", "Las Vegas, NV", "Austin, TX", "Miami, FL", "Orlando, FL"]
destination_city = st.sidebar.selectbox("What is your destination?", available_cities, index=None)
departure_location = st.sidebar.text_input("Where are you staying?", placeholder="Example: West Covina, CA")
sb_col1, sb_col2 = st.sidebar.columns(2)
from_date = sb_col1.date_input("Start Date", min_value=date.today())
to_date = sb_col2.date_input("End Date", min_value=from_date)

available_categories = ["Landmarks", "Entertainment", "History", "Nature", "Museums", "Shopping", "Nightlife"]
categories = st.sidebar.multiselect("Interests", available_categories)
optimized_options = st.sidebar.multiselect("Optimized By", ["Weather", "Family Friendly", "Safety", "Cost"])
restaurant_rating = st.sidebar.number_input(
    "Minimum Restaurant Rating",
    min_value = 1.0,
    max_value = 5.0, 
    step = 0.5,
    format = "%0.1f"
)

category_mapping = {
    "amusement_park": "Entertainment",
    "store": "Shopping",
    "museum": "Museums",
    "tourist_attraction": "Landmarks",
    "zoo": "Nature",
    "park": "Nature",
    "art_gallery": "Museums",
    "university": "History",
    "night_club": "Nightlife",
    "aquarium": "Nature"
}

reverse_mapping = defaultdict(list)
for k, v in category_mapping.items():
    reverse_mapping[v].append(k)

# button to generate itinerary
generate_itinerary = st.sidebar.button("Generate Itinerary")

# main page load area
# TODO track number of itineraries, set base case and limit of 3
if "itineraries" not in st.session_state:
    st.session_state["itineraries"] = None
    st.session_state["num_itin"] = 0
    st.session_state['itinerary_generated'] = False
    st.session_state['top_recommendations'] = None
    st.session_state['rec_details'] = {}

# generate itinerary when clicked
if generate_itinerary:
    selected_place_types = []
    for cat in categories:
        selected_place_types.extend(reverse_mapping[cat])

    interests = selected_place_types if len(selected_place_types) >= 4 else list(category_mapping.keys())[:5]
    destination = destination_city if destination_city else "Los Angeles" # default LA if non selected
    print(destination)
    print(categories)
    # reset for generating itinerary again after 1st use TODO: handle multiple itineraries
    if st.session_state['itinerary_generated']:
        st.session_state['itinerary_generated'] = False
        st.session_state["itineraries"] = None
        st.session_state["num_itin"] = 0
        with st.spinner("Generating your newly updated itinerary ..."):
            st.session_state['top_recommendations'] = get_top_recommendations_nearby(interests, destination, places_api)
    else:
        with st.spinner("Generating your itinerary ..."):
            st.session_state['top_recommendations'] = get_top_recommendations_nearby(interests, destination, places_api)

    request_payload = {
        "destination_city": destination,
        "departure_location": departure_location,
        "from_date": from_date.strftime('%m-%d-%Y'),#.isoformat()
        "to_date": to_date.strftime('%m-%d-%Y'),
        "interest_categories": categories,
        "optimized_options": optimized_options if optimized_options else ['None'], 
        "min_rating": restaurant_rating
    }
    st.session_state['itinerary_generated'] = True
    # load recommendations into the session state
    # city = 'Los-angeles' if destination_city == 'Los Angeles' else 'New-york-city'
    # st.session_state['top_recommendations'] = get_top_recommendations(rec_df, interests, destination_city)

# print(st.session_state['top_recommendations'])
# st.session_state['top_recommendations'].to_csv("places_sample.csv")

# when generate itinerary has been clicked
if st.session_state['itinerary_generated']:
    tab1, tab2 = st.tabs(['Places of Interest', 'Itinerary'])

    # this tab will generate recommend places in the area
    with tab1:
         # generates info at the top of the page
        if st.session_state['num_itin'] == 0:
            st.info("Generating your personalized itinerary, we'll let you know when it's finished! (See itinerary tab for updates...)", icon='ℹ️')
            # ping = st.info("See what new places are waiting for you on your next adventure!", icon='⬇️')
        else:
            st.success("Itinerary complete! Go to the Itinerary Tab!")

        # generates tiles for recommendations
        if not st.session_state['top_recommendations'].empty:
            st.markdown("<h2 style='text-align: center; font-weight: bold;'>Places of Interest</h2>", unsafe_allow_html=True)
            top_recs = st.session_state['top_recommendations'].sort_values(by="reviews", ascending=False).drop_duplicates(subset="name", keep="first")
            cols = st.columns(3)
            for idx, (_, details) in enumerate(top_recs.iterrows()):
                # rec_name = row['name']
                # rec_city = row['city']
                # if rec_name not in st.session_state['rec_details']:
                #     st.session_state['rec_details'][rec_name] = get_place_details(rec_name, rec_city)

                # details = st.session_state['rec_details'][rec_name]
                with cols[idx % 3]:
                    tile = st.container(border=True, height=470)
                    if details["photo"]:
                        # resize image to fit into the container
                        rec_image = requests.get(details["photo"])
                        if rec_image.status_code == 200:
                            image = Image.open(BytesIO(rec_image.content))
                            new_image = image.resize((330, 200))
                            tile.image(new_image, width=330)
                    else: 
                        tile.image( "./common/fallback-place-image.jpg", width=330)

                    # tile.markdown(f"**{details['name']}**", unsafe_allow_html=True)
                    tile.markdown(f"<h4 style='font-size:18px; font-weight:bold;'>{details['name']}</h4>", unsafe_allow_html=True)
                    tile.markdown(f"<p style='font-size:14px;'>{details['description']}</p>", unsafe_allow_html=True)
                    # tile.write(f"📝 {details['description']}")
                    if details["rating"] != "N/A":
                        rating_stars = "⭐" * int(float(details["rating"])) if details["rating"] != "N/A" else "N/A"
                        tile.markdown(f"<p style='font-size:14px;'>Rating: {rating_stars} ({int(details['reviews']):,} reviews)</p>", unsafe_allow_html=True)
                    # tile.write(f"Rating: {rating_stars} ({int(details['reviews']):,} reviews)")
                    
                    col1, col2, col3 = tile.columns(3)
                    with col1:
                        st.link_button(label="📞 Call", url=details['phone'], use_container_width=True) #, key=f"call_{idx}"
                    with col2:
                        st.link_button(label="📍 Map", url=details['map'], use_container_width=True) #, key=f"map_{idx}"
                    with col3:
                        st.link_button(label="🌐 Website", url= details['website'], use_container_width=True) #, key=f"website_{idx}"
        else:
            st.write("Trouble loading recommendations...")

    # this tab will generate the itinerary
    with tab2:
        # async call to run itinerary generation, will reset page once finished
        if st.session_state['num_itin'] == 0:
            asyncio.run(run_async_task(backend_url, request_payload))

        # if itinerary has been generated, display the itinerary in the tab
        response = st.session_state['itineraries']
        if response and response['status_code'] == 200:
            # itinerary:aitp_itinerary = aitp_itinerary(**response.json()) #entire itinerary json
            itinerary:aitp_itinerary = aitp_itinerary(**response['content'])
            st.subheader(f"{itinerary.name}", divider='gray') #set page header
            
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
                        # title for day plans (subheader version)
                        # st.subheader(f"Day {day_num} ({dp.date_of_the_day}): {dp.theme_of_the_day}", anchor=False)
                        # st.subheader(f"Itinerary:", divider="gray", anchor=False)

                        # title for day plans (markdown version)
                        st.markdown(f"<p style='font-size:20px;margin:0; padding:0;'><span style='font-weight:bold;'>Theme:</span> {dp.theme_of_the_day}</p>", unsafe_allow_html=True)
                        st.markdown(f"<p style='font-size:20px;margin:0; padding:0;'><span style='font-weight:bold;'>Date:</span> {dp.date_of_the_day}</p>", unsafe_allow_html=True)
                        st.markdown(f"<p style='font-size:20px;margin:0; padding:0;text-decoration:underline;'><span style='font-weight:bold;'>Activities:</span></p>", unsafe_allow_html=True)

                        # add detailed activities as expanding containers
                        for act_num, act_det in enumerate(dp.activity_details, start=1):
                            activity = act_det.activity
                            start_time = act_det.date_time.split(' - ')[0]
                            st.markdown(f"<p style='font-size:20px; margin:0; padding:0;'><span style='font-weight:bold;'>{act_num}. {activity.name}</span> ({act_det.date_time})</p>", unsafe_allow_html=True)
                            # st.markdown(f"##### {act_num}. {activity.name} ({act_det.date_time})", unsafe_allow_html=True)
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
                        # print(dp)
                        poi_map.show_map(hotel_location, dp)
                        # poi_map.show_map(dp)

        else:
            st.error("Failed to generate itinerary. Try again.")
else: 
    splash_page()

# if not generate_itinerary:
#     splash_page()

# else:

#     # format json request payload
#     request_payload = {
#         "destination_city": destination_city,
#         "departure_location": departure_location,
#         "from_date": from_date.strftime('%m-%d-%Y'),#.isoformat()
#         "to_date": to_date.strftime('%m-%d-%Y'),
#         "interest_categories": categories if categories else ["General Activities"],
#         "optimized_options": optimized_options if optimized_options else ['None'], 
#         "min_rating": restaurant_rating
#     }

#     workflow_steps = [
#         "Generating your personalized itinerary ...",
#         "Finding attractions ...",
#         "Finding nearby restaurants ...",
#         "Retrieving weather forecasts on the travel days ...",
#         "Creating itineraries and optimizing routes ...",
#         "Preparing itineraries report ..."
#     ]
#     ## TODO: redo, just have the
#     # start the task of fetching the itinerary
#     # start_background_fetch()
#     background_fetch()
#     with st.spinner(workflow_steps[i]):
#         while 'itinerary_response' not in st.session_state:
#             st.spinner(workflow_steps[i % 6])
#             i += 1
#             time.sleep(0.1)
#         # print('end while loop')
#         # request response
#         # response = requests.get(backend_url, json=request_payload) # sync request
#         # response = asyncio.run(async_request())
#         # st.success(f"Itinerary Ready!")
#     response = st.session_state['itinerary_response']

#     if response['status_code'] == 200:
#         # itinerary:aitp_itinerary = aitp_itinerary(**response.json()) #entire itinerary json
#         itinerary:aitp_itinerary = aitp_itinerary(**response['content'])
#         st.header(f"{itinerary.name}", divider='gray') #set page header
        
#         tabs = st.tabs([f"Day {day_num}: {dp.theme_of_the_day}" for day_num, dp in enumerate(itinerary.day_plans, start=1)])

#         # to plot hotel location
#         user_preference = itinerary.user_preference
#         hotel_latitude, hotel_longitude = GeocodeUtils.get_lat_lon(user_preference.hotel_location)
#         hotel_location = Activity(
#             name="Hotel | Starting Point",
#             location=user_preference.hotel_location,
#             latitude=hotel_latitude,
#             longitude=hotel_longitude,
#             category="Hotel",
#         )
#         # # loop through each day plan
#         for day_num, (dp, tab) in enumerate(zip(itinerary.day_plans, tabs), start=1):
#             # set container parameters
#             # with col.container(border=True, height=700):
#             with tab:
#                 col1, col2 = st.columns(2, vertical_alignment="top")
                
#                 # render itinerary in first column
#                 with col1:
#                     # title for day plans
#                     st.subheader(f"Day {day_num} ({dp.date_of_the_day}): {dp.theme_of_the_day}", anchor=False)
#                     # st.markdown(f"##### Date: {dp.date_of_the_day}", unsafe_allow_html=True)
#                     st.subheader(f"Itinerary:", divider="gray", anchor=False)

#                     # add detailed activities as expanding containers
#                     for act_num, act_det in enumerate(dp.activity_details, start=1):
#                         activity = act_det.activity
#                         start_time = act_det.date_time.split(' - ')[0]
#                         st.markdown(f"##### {act_num}. {act_det.date_time}: {activity.name}", unsafe_allow_html=True)
#                         # expanded = True if act_num == 1 else False
#                         expand = st.expander(f"More Details", icon="➡️")
                        
#                         expand.markdown(f"""
#                             - 📌 **Location:** {activity.location}
#                             - :sparkles: **Details:** {act_det.description}
#                             - ❓ **Why Suggest?** {act_det.why_its_suitable}
#                             - 🚗 **Transportation:** {act_det.driving_info}
#                             - ⭐ **Rating:** {act_det.rating}
#                             - 📝 **Reviews:**
#                                 - "{act_det.reviews[0]}"
#                                 - "{act_det.reviews[1]}"
#                             """, unsafe_allow_html=True)

#                     expand2 = st.expander(f"Additional Info", icon="ℹ️", expanded=True)
#                     expand2.write(f"🏨 **Returning Home:** {dp.return_to_hotel_driving_info}")
#                     expand2.write(f"🧳 **Packing List:** {', '.join(dp.packing_list)}")
                
#                 # render map in second column
#                 with col2:
#                     poi_map = POIMap()
#                     # day_plan = DayPlan(**dp)    
#                     poi_map.show_map(hotel_location, dp)
#                     # poi_map.show_map(dp)

#     else:
#         st.error("Failed to generate itinerary. Try again.")

