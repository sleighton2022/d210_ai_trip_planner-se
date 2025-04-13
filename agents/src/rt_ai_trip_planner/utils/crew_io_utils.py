
from datetime import datetime
import json
import os

from ..model import OptimizationOptions, UserPreference
from .reqs_builder_utils import TripRequirementsBuilderUtils


class CrewInputOutputUtils:
    @staticmethod
    def create_sample_inputs() -> dict:
        """
        Create the crew inputs for the trip planner.
        """
        user_preference = CrewInputOutputUtils.create_sample_user_preference()
        return CrewInputOutputUtils.prepare_crew_inputs(user_preference)
                                              
    @staticmethod
    def create_sample_user_preference() -> UserPreference:
        """
        Simulate a http request received from FE.
        """
        user_preference = UserPreference(
            destination='Los Angeles, CA', # 'Los Angeles, CA', 
            start_date='02-17-2025',
            end_date='02-20-2025',
            interests=['tourist_attraction', 'zoo', 'museums'], # ['zoo', 'museums', 'beaches'],
            hotel_location='West Covina, CA',
            optimization_options=OptimizationOptions(
                by_weather = True,
                by_traffic = True,
                by_family_friendly = True,
                by_safety = True,
                by_cost=False,
                min_rating=3.0
            )
        )
        return user_preference

    @staticmethod
    def prepare_crew_inputs(user_preference: UserPreference) -> dict:
        """
        Prepare the crew inputs from the user preference.
        """
        # Calculate the day difference between start and end date.
        start_date = datetime.strptime(user_preference.start_date, "%m-%d-%Y")
        end_date = datetime.strptime(user_preference.end_date, "%m-%d-%Y")
        trip_duration = (end_date - start_date).days

        # Number of activities to be selected from - assume 4 activities per day.
        num_activities = 4 * trip_duration

        # Prepare the builder instance to construct trip requirements.
        builder = TripRequirementsBuilderUtils(user_preference)

        # Convert the user preference to a dictionary.
        inputs = json.loads(
            json.dumps(user_preference, default=lambda o: getattr(o, '__dict__', str(o)))
        )

        # Flatten the optimization_options dictionary.
        inputs = {**inputs, **inputs['optimization_options']}
        del inputs['optimization_options']

        # Decorate the inputs with additional information.
        inputs.update({
            'trip_duration': trip_duration,
            'num_activities': num_activities,
            'activity_requirements': builder.activity_requirements(),
            'traffic_requirements': builder.traffic_requirements(), 
            'weather_requirements': builder.weather_requirements(),
            'restaurant_requirements': builder.restaurant_requirements(),
            'activities': []
        })

        print("-" * 30)
        print(f"[INFO] Inputs to Crew:\n{inputs}")
        print("-" * 30)
        return inputs
    
    @staticmethod
    def inspect_crew_output(crew_output, verbose=False, output_file_name=None):
        """
        Inspect the crew output.
        """
        print("-" * 30)

        if verbose:
            print(f"Raw Output: {crew_output.raw}")
            if crew_output.json_dict:
                print(f"JSON Output: {json.dumps(crew_output.json_dict, indent=2)}")
            if crew_output.pydantic:
                print(f"Pydantic Output: {crew_output.pydantic}")
            print(f"Tasks Output: {crew_output.tasks_output}")
        print(f"Token Usage: {crew_output.token_usage}")    

        print("-" * 30)

        # Write the output to a file.
        if output_file_name:
            output_file_path = os.path.join(os.getcwd(), output_file_name)
            print(f"\n[INFO] Writing the crew output to {output_file_path}...\n")
            with open(output_file_path, 'w') as file:
                json.dump(crew_output.json_dict, file, indent=2)
        
    @staticmethod
    def find_folder_path(folder_name: str) -> str:
        LOOKUP_PATHS = [
            ".",
            "..",
            "../..",
            "../../..",
        ]
        for p in LOOKUP_PATHS:
            file_path = f"{p}/{folder_name}"
            print(f"[INFO] Checking path at: {file_path}...")

            # Check if the directory exists.
            if os.path.exists(file_path):
                print(f"[INFO] Found directory at: {file_path}")
                return file_path
            
        # If we reach here, it is an error. Raise an assert error.
        assert False, "Directory not found!"

    @staticmethod
    def write_to_file(folder_name: str, file_name: str, data: dict):
        """
        Write the data to a file.
        """
        target_folder_path = CrewInputOutputUtils.find_folder_path(folder_name)
        file_path = f'{target_folder_path}/{file_name}'
        with open(f'{file_path}', 'w') as file:
            file.write(data)

        print(f"[DEBUG] Contents '{data[:50]}...' saved to {file_path}")
