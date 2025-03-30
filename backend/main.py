
###########################################################################
## Integration between FastAPI and RtAiTripPlanner (crewAI) starts here ##
## TODO: 
## 1. Create a common directory
## 2. Move agents/src/rt_ai_trip_planner/model.py to common directory
## 3. Update imports reference to common directory
## 4. Refactor to keep only one generate_itinerary function
###########################################################################
from fastapi import FastAPI
app = FastAPI()
import os
print(f"Current directory: {os.getcwd()}")

import sys
# sys.path.append('/home/cng/labs/ucb/d210_ai_trip_planner-main/agents/src/rt_ai_trip_planner')
# sys.path.append('/home/cng/labs/ucb/d210_ai_trip_planner-main/agents/src')
# sys.path.append('/home/cng/labs/ucb/d210_ai_trip_planner-main/agents')
#sys.path.append('./agents/src/rt_ai_trip_planner')
#sys.path.append('./agents/src')
# sys.path.append('./agents')
#sys.path.append('./common')


# --- Start of Robust Path Calculation ---

# Get the absolute path of the directory containing the current script (main.py)
# Example: /home/sleighton/ds210/d210_ai_trip_planner/backend
script_dir = os.path.dirname(os.path.abspath(__file__))

# Navigate up one level from the script's directory to find the project root.
# Example: /home/sleighton/ds210/d210_ai_trip_planner
project_root = os.path.abspath(os.path.join(script_dir, '..'))

# Construct the absolute path to the 'common' directory under the project root.
# Example: /home/sleighton/ds210/d210_ai_trip_planner/common
common_path = os.path.join(project_root, 'common')
agent_path = os.path.join(project_root, 'agents')


# Add the 'common' directory to the Python path if it's not already there.
if common_path not in sys.path:
    sys.path.append(common_path)

if agent_path not in sys.path:
    agent_src_path = agent_path + "/src"
    agent_src_rt_path = agent_src_path + "rt_ai_trip_planner"
    sys.path.append(agent_src_path)
    sys.path.append(agent_src_rt_path)


from model import UserPreference, Itinerary, OptimizationOptions
from agents.src.rt_ai_trip_planner.main import invoke_ai_agents

import json
import dotenv
from dotenv import load_dotenv

load_dotenv(dotenv_path='./agents/.env')
for i in dotenv.dotenv_values():
    print(f"env: {i}")

# Generate Itinerary
@app.get("/ai-trip-planner/v2/plan", response_model=Itinerary)
def generate_itinerary_v2(request_payload: dict = None):
    # testing for UI improvements
    # ---------------------------
    # print("Backend Payload", request_payload)
    # if (request_payload):
    #     with open("./common/sample-itinerary.json", "r") as file:
    #         itinerary = json.load(file)
    # return itinerary
    # ---------------------------
    # print(request_payload)
    
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
            interests=['museums', 'beaches'],
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
