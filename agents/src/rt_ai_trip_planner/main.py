#!/usr/bin/env python
import json
import os
import sys
import time
import warnings
from dotenv import load_dotenv
load_dotenv()

from datetime import datetime

# Uncomment the following lines to enable langtrace.
# Must precede any llm module imports
# from langtrace_python_sdk import langtrace
# langtrace.init(api_key = '991ac5f7cd887e2a2c74f851962e37dc8b64cd8276d1de94114318c5689f8ae9')

from .crew import RtAiTripPlanner
from .model import OptimizationOptions, UserPreference
from .utils.crew_io_utils import CrewInputOutputUtils
from .utils.reqs_builder_utils import TripRequirementsBuilderUtils

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    load_dotenv()
    try:
        crew_output = RtAiTripPlanner().crew().kickoff(inputs=CrewInputOutputUtils.create_sample_inputs())

        # Write the output to a file.
        # output_file_path = os.path.join(os.getcwd(), 'data/sample-itinerary.json')
        # print(f"\n[INFO] Writing the crew output to {output_file_path}...\n")
        # with open(output_file_path, 'w') as file:
        #     json.dump(crew_output.json_dict, file, indent=2)

        # Save the JSON string to a file.
        write_crew_io_to_file = os.getenv("APP_WRITE_CREW_IO_TO_FILE", "false")
        if write_crew_io_to_file.lower() == "true":
            json_str = json.dumps(crew_output.json_dict, indent=2)
            CrewInputOutputUtils.write_to_file(folder_name='data', file_name='sample-itinerary.json', data=json_str)        

        # Report crew metrics.
        print(f"\n[INFO] Token Usage: \n{crew_output.token_usage}\n")
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")

def train():
    """
    Train the crew for a given number of iterations.
    """
    try:
        RtAiTripPlanner().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=CrewInputOutputUtils.create_sample_inputs())

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        RtAiTripPlanner().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    try:
        RtAiTripPlanner().crew().test(n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=CrewInputOutputUtils.create_sample_inputs())

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def invoke_ai_agents(user_preference_request: UserPreference) -> dict:
    """
    Call this function from web controller to invoke the AI agents to plan the trip.
    """
    print(f'[DEBUG] invoke_ai_agents STARTED at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.')
    print(f"[DEBUG] user_preference_request:\n{user_preference_request}")
    start_time = time.time()
    inputs = CrewInputOutputUtils.prepare_crew_inputs(user_preference_request)
    output = RtAiTripPlanner().crew().kickoff(inputs=inputs)
    print(f'\n[DEBUG] invoke_ai_agents ENDED at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.')
    print(f"[DEBUG] Crew execution time: {(time.time() - start_time)/60:.2f} minutes\n")
    return output

# Quick unit test/POC.
if __name__ == "__main__":
    # Simulate a http request received from FE.
    user_preference_request = UserPreference(
        destination='Los Angeles, CA',
        start_date='04-03-2025',
        end_date='04-05-2025',
        interests=['museum', 'tourist_attraction'],
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

    output = invoke_ai_agents(user_preference_request)
    print(f"\n[DEBUG] Output: \n{output}\n")
