import math
import json
from datetime import datetime, timezone

def haversine_distance(lat1, lon1, lat2, lon2, unit="km"):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees).
    """
    try:
        lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
    except (TypeError, ValueError):
        return None

    # Radius of earth in kilometers or miles
    r = 6371.0 if unit == "km" else 3958.8

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    distance = r * c
    return round(distance, 2)

def format_distance(distance_km):
    if distance_km is None:
        return "Distance unavailable"
    if distance_km < 1.0:
        meters = int(distance_km * 1000)
        return f"{meters} m away"
    return f"{distance_km:.1f} km away"

def get_shop_open_status(opening_hours_json):
    """
    Parse opening hours JSON and determine if store is open right now.
    Format of opening_hours_json:
    {
      "mon": {"open": "08:00", "close": "20:00", "closed": false},
      "tue": ...,
      ...
    }
    """
    if not opening_hours_json:
        return {"is_open": None, "badge": "Hours Not Listed", "details": "Contact shop for current hours"}

    try:
        if isinstance(opening_hours_json, str):
            schedule = json.loads(opening_hours_json)
        else:
            schedule = opening_hours_json
    except Exception:
        return {"is_open": None, "badge": "Hours Not Listed", "details": "Contact shop for current hours"}

    now = datetime.now()
    day_key = now.strftime("%a").lower()[:3] # 'mon', 'tue', etc.
    current_time_str = now.strftime("%H:%M")

    today_hours = schedule.get(day_key)
    if not today_hours or today_hours.get("closed", False):
        return {
            "is_open": False,
            "badge": "Closed Today",
            "details": "Closed today"
        }

    open_time = today_hours.get("open", "09:00")
    close_time = today_hours.get("close", "18:00")

    if open_time <= current_time_str <= close_time:
        return {
            "is_open": True,
            "badge": "Open Now",
            "details": f"Open today until {format_time_12h(close_time)}"
        }
    elif current_time_str < open_time:
        return {
            "is_open": False,
            "badge": "Closed",
            "details": f"Opens today at {format_time_12h(open_time)}"
        }
    else:
        return {
            "is_open": False,
            "badge": "Closed",
            "details": f"Closed for today at {format_time_12h(close_time)}"
        }

def format_time_12h(time_str):
    try:
        t = datetime.strptime(time_str, "%H:%M")
        return t.strftime("%I:%M %p").lstrip("0")
    except Exception:
        return time_str

def format_relative_time(dt_str_or_obj):
    """
    Convert datetime string or object into readable relative format
    e.g. '10 minutes ago', '2 hours ago', 'Yesterday', '3 days ago'
    """
    if not dt_str_or_obj:
        return "Unknown"

    try:
        if isinstance(dt_str_or_obj, str):
            # SQLite format: YYYY-MM-DD HH:MM:SS or ISO
            clean_str = dt_str_or_obj.split(".")[0].replace("T", " ")
            dt = datetime.strptime(clean_str, "%Y-%m-%d %H:%M:%S")
        else:
            dt = dt_str_or_obj

        now = datetime.now()
        diff = now - dt

        seconds = diff.total_seconds()
        if seconds < 0:
            return "Just now"
        if seconds < 60:
            return "Just now"
        if seconds < 3600:
            mins = int(seconds // 60)
            return f"{mins} min{'s' if mins != 1 else ''} ago"
        if seconds < 86400:
            hours = int(seconds // 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        days = int(seconds // 86400)
        if days == 1:
            return "Yesterday"
        if days < 30:
            return f"{days} days ago"
        return dt.strftime("%b %d, %Y")
    except Exception:
        return str(dt_str_or_obj)

def is_inventory_stale(dt_str_or_obj, stale_days=14):
    """Returns True if last update was more than stale_days ago."""
    if not dt_str_or_obj:
        return True
    try:
        if isinstance(dt_str_or_obj, str):
            clean_str = dt_str_or_obj.split(".")[0].replace("T", " ")
            dt = datetime.strptime(clean_str, "%Y-%m-%d %H:%M:%S")
        else:
            dt = dt_str_or_obj
        now = datetime.now()
        return (now - dt).days >= stale_days
    except Exception:
        return False
