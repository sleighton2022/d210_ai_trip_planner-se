
###########################################################################
## Integration between FastAPI and RtAiTripPlanner (crewAI) starts here ##
## TODO: 
###########################################################################
from fastapi import FastAPI
import os
import sys
app = FastAPI()

sys.path.append('./agents/src/rt_ai_trip_planner')
sys.path.append('./agents/src')
# sys.path.append('./agents')
sys.path.append('./common')

from model import UserPreference, Itinerary, OptimizationOptions
from agents.src.rt_ai_trip_planner.main import invoke_ai_agents

import json
import dotenv
from dotenv import load_dotenv
import time
import asyncio

load_dotenv(dotenv_path='./agents/.env')
for i in dotenv.dotenv_values():
    print(f"env: {i}")

# Generate Itinerary
@app.get("/ai-trip-planner/v2/plan", response_model=Itinerary)
def generate_itinerary_v2(request_payload: dict = None):
    # testing for UI improvements
    # ---------------------------
    # print('async call running')
    # time.sleep(20)
    # if (request_payload):
    #     with open("./common/sample-itinerary.json", "r") as file:
    #         itinerary = json.load(file)
    # return itinerary

    # ---------------------------
    #print("REQUEST PAYLOAD",request_payload)

    optimizations = request_payload["optimized_options"]

    if (request_payload):
        user_preference_request = UserPreference(
            destination=request_payload['destination_city'],
            start_date=request_payload["from_date"],
            end_date=request_payload["to_date"],
            interests=request_payload['interest_categories'],
            hotel_location=request_payload["departure_location"],
            optimization_options = OptimizationOptions(
                by_weather = "Weather" in optimizations,
                by_traffic = "Traffic" in optimizations,
                by_family_friendly = "Family Friendly" in optimizations,
                by_safety = "Safety" in optimizations,
                by_cost = "Cost" in optimizations,
                min_rating = request_payload["min_rating"]
            )
        )
    else:
        # For testing purpose.
        user_preference_request = UserPreference(
            destination='Los Angeles, CA',
            start_date='02-15-2025',
            end_date='02-20-2025',
            interests=['museum','tourist_attraction'],
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

    # print("Calling Agents...")
    output = invoke_ai_agents(user_preference_request)
    itinerary = Itinerary(**output.json_dict)
    # print(f"itinerary: {type(itinerary)}")

    return itinerary
