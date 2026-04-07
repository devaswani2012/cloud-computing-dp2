from datetime import datetime, timezone


def parse_mbta_time(timestr: str):
    """Convert MBTA ISO timestamp string to a Python datetime."""
    if not timestr:
        return None
    return datetime.fromisoformat(timestr.replace("Z", "+00:00"))


def minutes_difference(predicted_dt, scheduled_dt):
    """Return predicted - scheduled in minutes."""
    if not predicted_dt or not scheduled_dt:
        return None
    return round((predicted_dt - scheduled_dt).total_seconds() / 60.0, 2)


def classify_status(delay_minutes, threshold=2):
    """Classify train status based on delay."""
    if delay_minutes is None:
        return "NO_SERVICE"
    if abs(delay_minutes) <= threshold:
        return "ON_TIME"
    if delay_minutes > threshold:
        return "DELAYED"
    return "EARLY"


def utc_now_iso():
    """Current UTC timestamp as ISO string."""
    return datetime.now(timezone.utc).isoformat()
