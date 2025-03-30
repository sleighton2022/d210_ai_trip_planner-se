import json

from rt_ai_trip_planner.model import Itinerary


def test_deserialize():
    itinerary_dict: dict = _load_iter()
    itinerary = Itinerary(**itinerary_dict)
    assert itinerary is not None
    assert type(itinerary) == Itinerary
    print(itinerary)

def _load_iter() -> dict:
    itinerary = {}
    LOOKUP_PATHS = [
        ".",
        "..",
        "../..",
        "../../..",
    ]
    for p in LOOKUP_PATHS:
        try:
            file_path = f"{p}/data/sample-itinerary.json"
            print(f"[INFO] Loading json file from: {file_path}...")
            with open(file_path, 'r') as file:
                itinerary = json.load(file)
            print(f"[INFO] Loaded json file from: {file_path}")
            break
        except FileNotFoundError:
            pass

    assert itinerary is not None
    return itinerary