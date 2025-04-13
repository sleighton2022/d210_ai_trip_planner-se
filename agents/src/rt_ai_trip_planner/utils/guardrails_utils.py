
import json
import os
from typing import Tuple, Any
from crewai.tasks import TaskOutput


class GuardrailsUtils:
    @staticmethod
    def validate_activities(task_output: TaskOutput) -> Tuple[bool, Any]:
        """Validate blog content meets requirements."""
        try:
            print(f"\n[DEBUG] Validating activities: {task_output.name}...")

            # Remove "```" from the raw output.
            data = task_output.raw.replace("```", "")

            # Convert json string to a python object.            
            raw_obj = json.loads(data)

            # Verify if the activities list is not empty.
            print(f"[DEBUG] validate_activities: raw_obj.len (Total Activities): {len(raw_obj)}")
            if not raw_obj or len(raw_obj) == 0:
                print(f"[WARNING] No activities found in the itinerary.")
                return GuardrailsUtils.create_respond(task_output, False, {
                    "error": "No activities found in the itinerary",
                    "code": "NO_ACTIVITIES"
                })

            print(f"[DEBUG] Validation completed for the activities: {task_output.name}")
            return (True, task_output)
        except Exception as e:
            print(f"[ERROR] validate_activities: Unexpected error during validation: {e}")
            return GuardrailsUtils.create_respond(task_output, False, {
                "error": "Unexpected error during validate_activities",
                "code": "SYSTEM_ERROR"
            })

    @staticmethod
    def validate_itinerary(task_output: TaskOutput) -> Tuple[bool, Any]:
        """Validate blog content meets requirements."""
        try:
            print(f"\n[DEBUG] Validating Itinerary: {task_output.name}...")

            # Convert json to Itinerary object.
            itinerary = task_output.json_dict

            # Keep track of unique activities.
            unique_activities = set()
            total_activities = 0

            # Validate each day has the correct activities.
            print(f"[DEBUG] Validating each day has the correct activities...")
            for day_plan in itinerary['day_plans']:
                print(f"[DEBUG] Validating day plan: {day_plan['theme_of_the_day']}...")
                # Collect count for activities type.
                regular_activity_count = 0
                restaurant_count = 0
                for activity_detail in day_plan['activity_details']:
                    activity = activity_detail['activity']
                    unique_activities.add(activity['name'])
                    total_activities += 1

                    if GuardrailsUtils.is_restaurant_activity(activity):
                        print(f"[DEBUG]   - Found restaurant ({activity['category']}) activity: {activity['name']}")
                        restaurant_count += 1
                    else:
                        print(f"[DEBUG]   - Found ({activity['category']}) activity: {activity['name']}")
                        regular_activity_count += 1
                
                # Check if each day at least has two 'restaurant' activities (lunch and dinner)
                if restaurant_count < 2:
                    print(f"[WARNING] Each day must have at least two restaurant activities: {day_plan['theme_of_the_day']} found {restaurant_count} restaurant activities")
                    return GuardrailsUtils.create_respond(task_output, False, {
                        "error": "Each day must have at least two restaurant activities",
                        "code": "TOO_FEW_RESTAURANT"
                    })
                # Check if there is too few activity.
                if regular_activity_count < 2:
                    print(f"[WARNING] Each day must have at least more than one activity: {day_plan['theme_of_the_day']} found {regular_activity_count} activities")
                    return GuardrailsUtils.create_respond(task_output, False, {
                        "error": "Each day must have at least more than one activity",
                        "code": "TOO_FEW_ACTIVITY"
                    })
            
            # Check if there are any duplicate activities.
            print(f"[DEBUG] Checking for duplicate activities (Total activities: {total_activities}, Unique activities: {len(unique_activities)})...")
            if len(unique_activities) != total_activities:
                print(f"[WARNING] Found duplicate activities in the itinerary. Total activities: {total_activities}, Unique activities: {len(unique_activities)}")
                return GuardrailsUtils.create_respond(task_output, False, {
                    "error": "Found duplicate activities in the itinerary",
                    "code": "DUPLICATE_ACTIVITY"
                })            

            # Additional validation logic here
            print(f"[DEBUG] Validation completed for the itinerary: {task_output.name}")
            return (True, task_output)
        except Exception as e:
            print(f"[ERROR] validate_itinerary: Unexpected error during validation: {e}")
            return GuardrailsUtils.create_respond(task_output, False, {
                "error": "Unexpected error during validate_itinerary",
                "code": "SYSTEM_ERROR"
            })
        
    @staticmethod
    def is_restaurant_activity(activity: dict) -> bool:
        """
        Check if the activity is a restaurant.
        """
        
        # Check if the activity name contains the keyword 'lunch' or 'dinner'
        activity_name = activity['name'].lower()
        if 'lunch' in activity_name or 'dinner' in activity_name:
            return True

        # Return True if category contains part of the restaurant keywords
        category = activity['category'].lower()
        restaurant_keywords = [
            "restaurant", "food", "dining", 
            "eatery", "meal", 
            "bar", "cafe", "Café", "cafeteria", "coffee", "chocolate",
            "deli", "dessert", "doughnut",
            "pub", "snack",
            "supper", "takeout", "tavern", "diner", 
            "spanish", "mexican", "italian", "chinese", "japanese", "korean", "indian", "thai", "french", "greek",
            "seafood", "vegetarian", "vegan", "steakhouse", "sushi",
            "breakfast", "brunch", "lunch", "dinner",
            "ice cream", "juice", "pancake", "tea", 
            "acai_shop"
        ]
        for keyword in restaurant_keywords:
            if keyword in category:
                return True
        
        return False
    
    @staticmethod
    def create_respond(task_output: TaskOutput, is_success: bool, error_msg: Any = None) -> tuple[bool, Any]:
        """
        Create a response for the task.
        """
        observe_guardrails_error = os.getenv("APP_OBSERVE_GUARDRAILS_ERROR", "false")
        print(f"[DEBUG] write_crew_io_to_file: {observe_guardrails_error}")
        if observe_guardrails_error.lower() == "true":
            returned_obj = task_output if is_success else error_msg
            return (is_success, returned_obj)
        
        # Default is to return the success status and task output.
        return (True, task_output)