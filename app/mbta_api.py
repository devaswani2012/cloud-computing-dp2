import requests

from app.config import (
    MBTA_API_KEY,
    MBTA_BASE_URL,
    ROUTE_ID,
    STOP_ID,
    DIRECTION_ID,
    TIMEOUT,
)
from app.utils import parse_mbta_time, minutes_difference


def _get_headers():
    headers = {}
    if MBTA_API_KEY:
        headers["x-api-key"] = MBTA_API_KEY
    return headers


def fetch_predictions_payload():
    """
    Fetch full MBTA predictions payload for the configured route/stop/direction.
    """
    url = f"{MBTA_BASE_URL}/predictions"
    params = {
        "filter[route]": ROUTE_ID,
        "filter[stop]": STOP_ID,
        "filter[direction_id]": DIRECTION_ID,
        "sort": "arrival_time",
        "include": "schedule",
    }

    response = requests.get(
        url,
        params=params,
        headers=_get_headers(),
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def get_next_prediction():
    """
    Return the next usable prediction record with:
    - predicted_arrival
    - scheduled_arrival
    - delay_minutes
    - num_predictions

    If no usable prediction exists, return None-valued fields.
    """
    payload = fetch_predictions_payload()
    predictions = payload.get("data", [])
    included = payload.get("included", [])

    schedule_lookup = {}
    for obj in included:
        if obj.get("type") == "schedule":
            schedule_lookup[obj.get("id")] = obj

    for item in predictions:
        attributes = item.get("attributes", {})
        predicted_str = attributes.get("arrival_time")
        if not predicted_str:
            continue

        relationships = item.get("relationships", {})
        schedule_rel = relationships.get("schedule", {})
        schedule_data = schedule_rel.get("data")

        scheduled_str = None
        if schedule_data:
            schedule_id = schedule_data.get("id")
            schedule_obj = schedule_lookup.get(schedule_id)
            if schedule_obj:
                scheduled_str = schedule_obj.get("attributes", {}).get("arrival_time")

        predicted_dt = parse_mbta_time(predicted_str)
        scheduled_dt = parse_mbta_time(scheduled_str)
        delay_minutes = minutes_difference(predicted_dt, scheduled_dt)

        return {
            "predicted_arrival": predicted_str,
            "scheduled_arrival": scheduled_str,
            "delay_minutes": delay_minutes,
            "num_predictions": len(predictions),
        }

    return {
        "predicted_arrival": None,
        "scheduled_arrival": None,
        "delay_minutes": None,
        "num_predictions": len(predictions),
    }
