#!/usr/bin/env python
import sys
import os
import json
from datetime import datetime, timedelta
import time

# --- Robust Path Setup ---
# Add necessary directories to sys.path assuming this script runs from 'evaluation'

script_dir = os.path.dirname(os.path.abspath(__file__))
# Go up one level from 'evaluation' to get the project root
project_root = os.path.abspath(os.path.join(script_dir, '..'))
# Construct paths relative to the project root
common_path = os.path.join(project_root, 'common')
agents_src_path = os.path.join(project_root, 'agents', 'src')

# Add paths needed for imports
if common_path not in sys.path:
    sys.path.append(common_path)
# Add agents/src so 'from rt_ai_trip_planner...' works
if agents_src_path not in sys.path:
    sys.path.append(agents_src_path)
# Optional: Add project root itself if needed by any imports
# if project_root not in sys.path:
#     sys.path.append(project_root)

print(f"Script Directory: {script_dir}")
print(f"Project Root: {project_root}")
print(f"Common Path Added: {common_path}")
print(f"Agents Src Path Added: {agents_src_path}")


# --- Imports from your project ---
try:
    # Import the function that runs the agents
    from rt_ai_trip_planner.main import invoke_ai_agents
    # Import the necessary data models to create inputs
    # Assuming model.py is in the 'common' directory based on previous fixes
    from model import OptimizationOptions, UserPreference
except ModuleNotFoundError as e:
    print(f"Error importing project modules: {e}")
    print("Please ensure:")
    print("1. This script is run from the 'evaluation' directory.") # Updated message
    print("2. The project structure (common/, agents/src/) is correct relative to 'evaluation/'.")
    print("3. You have __init__.py files in 'common', 'agents', 'agents/src', and 'agents/src/rt_ai_trip_planner'.")
    sys.exit(1)

# --- Environment Setup ---
from dotenv import load_dotenv, find_dotenv
# Search for .env in current dir (evaluation) and parent dirs (finds it in project root)
dotenv_path = find_dotenv(usecwd=True)
print(f"Loading .env file from: {dotenv_path}")
load_dotenv(dotenv_path=dotenv_path)


# --- Define Example Inputs ---

# Get dates for examples (e.g., starting next month)
today = datetime.now().date()
# Use hardcoded future dates if running frequently to avoid month rollovers during testing
# Or keep dynamic like this:
start_date_default = today.replace(day=1, month=today.month % 12 + 1) + timedelta(days=14) # Approx middle of next month
if today.month == 12: # Handle year change
     start_date_default = start_date_default.replace(year=today.year+1)

start_date_str = start_date_default.strftime('%m-%d-%Y')
end_date_default = start_date_default + timedelta(days=2) # 3 day trip
end_date_str = end_date_default.strftime('%m-%d-%Y')
weekend_end_date_str = (start_date_default + timedelta(days=1)).strftime('%m-%d-%Y') # 2 day weekend trip

# Default optimization options
default_opts = OptimizationOptions(
    by_weather=True,
    by_traffic=True,
    by_family_friendly=False,
    by_safety=True,
    by_cost=False,
    min_rating=4.0 # Example: only higher rated places
)

# List of different UserPreference scenarios
# (Consider moving this list to a shared config file/module)
EXAMPLE_INPUTS = [ 

#    {
#        "filename_suffix": "la_museums_beach",
#        "prefs": UserPreference(
#            destination='Los Angeles, CA',
#            start_date=start_date_str,
#            end_date=end_date_str,
#            interests=['museums', 'beaches', 'good local food'],
#            hotel_location='Santa Monica, CA',
#            optimization_options=default_opts
#        )
#    },
    {
        "filename_suffix": "sf_history_parks_family",
        "prefs": UserPreference(
            destination='San Francisco, CA',
            start_date=start_date_str,
            end_date=weekend_end_date_str, # Shorter trip
            interests=['historical landmarks', 'parks', 'views'],
            hotel_location='Fisherman\'s Wharf, San Francisco, CA',
            optimization_options=default_opts.model_copy(update={"by_family_friendly": True, "min_rating": 0.0}) # Family friendly override
        )
    }

#    {
#        "filename_suffix": "sd_zoo_gaslamp_cost_conscious",
#        "prefs": UserPreference(
#            destination='San Diego, CA',
#            start_date=start_date_str,
#            end_date=end_date_str,
#            interests=['zoo', 'nightlife', 'breweries'],
#            hotel_location='Gaslamp Quarter, San Diego, CA',
#            optimization_options=default_opts.model_copy(update={"by_cost": True}) # Cost conscious override
#        )
#    },
#   # Add more scenarios as needed
]

# --- Output Directory ---
# Define output dir relative to project root for consistency
OUTPUT_DIR = os.path.join(project_root, "evaluation/example_outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Main Execution Logic ---
if __name__ == "__main__":
    print(f"\nStarting generation of example outputs...")
    print(f"Using default start date: {start_date_str}")
    print(f"Outputs will be saved in: {OUTPUT_DIR}")

    # Check if OPENAI_API_KEY is set (often needed by agents)
    if not os.getenv("OPENAI_API_KEY"):
         print("Warning: OPENAI_API_KEY environment variable not set. Agent execution may fail.")

    for i, example in enumerate(EXAMPLE_INPUTS):
        suffix = example["filename_suffix"]
        prefs = example["prefs"]
        output_filename = os.path.join(OUTPUT_DIR, f"itinerary_{suffix}.json")

        print(f"\n--- Running Scenario {i+1}: {suffix} ---")
        print(f"Destination: {prefs.destination}, Interests: {prefs.interests}")
        print(f"Saving output to: {output_filename}")

        start_time = time.time()
        try:
            # Call the function from your original main.py
            # Modify this call if invoke_ai_agents now returns more than just the answer dict/model
            result = invoke_ai_agents(prefs) # Assume returns dict or pydantic model for answer

            # --- Extract only the answer part if needed ---
            # If invoke_ai_agents returns {'answer': ..., 'context':...} use:
            # answer_data = result['answer'] if isinstance(result, dict) and 'answer' in result else result
            # If invoke_ai_agents just returns the itinerary dict/model directly:
            answer_data = result
            # ---

            # Save the successful output
            with open(output_filename, 'w') as f:
                # If answer_data is a pydantic model, use .model_dump_json()
                if hasattr(answer_data, 'model_dump_json'):
                    f.write(answer_data.model_dump_json(indent=2))
                # Otherwise assume it's already a dict or compatible
                else:
                    json.dump(answer_data, f, indent=2)

            elapsed_time = time.time() - start_time
            print(f"✅ Scenario '{suffix}' completed successfully in {elapsed_time:.2f} seconds.")

        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"❌ Scenario '{suffix}' failed after {elapsed_time:.2f} seconds: {e}")
            # Optionally write error to a file
            with open(output_filename + ".error", 'w') as f:
                f.write(f"Error running scenario '{suffix}':\n{e}\n")
                import traceback
                traceback.print_exc(file=f)

    print("\n--- Example generation complete ---")