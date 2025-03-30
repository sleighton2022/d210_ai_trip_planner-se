
from datetime import datetime
import json

from rt_ai_trip_planner.model import OptimizationOptions, UserPreference
from rt_ai_trip_planner.utils.reqs_builder_utils import TripRequirementsBuilderUtils


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
            interests=['Entertainment/Amusement Park', 'Zoo', 'Museum'], # ['zoo', 'museums', 'beaches'],
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

        # Prepare the builder instance to construct trip requirements.
        builder = TripRequirementsBuilderUtils(user_preference)

        # Convert the user preference to a dictionary.
        inputs = json.loads(
            json.dumps(user_preference, default=lambda o: getattr(o, '__dict__', str(o)))
        )

        # Decorate the inputs with additional information.
        inputs.update({
            'trip_duration': trip_duration,
            'activity_requirements': builder.activity_requirements(),
            'traffic_requirements': builder.traffic_requirements(), 
            'weather_requirements': builder.weather_requirements(),
            'restaurant_requirements': builder.restaurant_requirements(),
            'activity_names': [],
            'activities': []
        })

        print("-" * 30)
        print(f"[INFO] Inputs to Crew:\n{inputs}")
        print("-" * 30)
        return inputs
    
    @staticmethod
    def inspect_crew_output(crew_output, verbose=False):
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