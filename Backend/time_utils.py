"""
Time Utility Functions

Extracts temporal features from timestamps for safety analysis.
"""

from datetime import datetime
from typing import Dict, Tuple


def extract_time_features(timestamp: datetime) -> Dict[str, float]:
    """
    Extract all time-based features from a timestamp.
    
    Args:
        timestamp: datetime object
        
    Returns:
        Dictionary with normalized time features [0, 1]:
        - hour_normalized: Hour of day [0-23] normalized to [0, 1]
        - is_night: Binary (1 if night, 0 if day) - night is 20:00-06:00
        - is_weekend: Binary (1 if Fri-Sun, 0 otherwise)
        - day_of_week_normalized: Day of week [0-6] normalized to [0, 1]
    """
    hour = timestamp.hour
    day_of_week = timestamp.weekday()  # 0=Monday, 6=Sunday
    
    # Hour normalized: 0-23 -> 0-1
    hour_normalized = hour / 23.0
    
    # Night time: 20:00 (20) to 06:00 (6) is considered night
    is_night = 1.0 if (hour >= 20 or hour < 6) else 0.0
    
    # Weekend: Friday (4), Saturday (5), Sunday (6)
    is_weekend = 1.0 if day_of_week >= 4 else 0.0
    
    # Day of week normalized: 0-6 -> 0-1
    day_of_week_normalized = day_of_week / 6.0
    
    return {
        "hour_normalized": hour_normalized,
        "is_night": is_night,
        "is_weekend": is_weekend,
        "day_of_week_normalized": day_of_week_normalized,
    }


def get_peak_crime_hours() -> Tuple[int, int]:
    """
    Get peak crime hours (typical for most urban areas).
    Returns tuple of (start_hour, end_hour) - typically night hours and early morning.
    
    Returns:
        Tuple of (start_hour, end_hour) representing peak crime window
    """
    return (20, 6)  # 20:00 to 06:00


def is_peak_crime_time(timestamp: datetime) -> bool:
    """
    Check if a given timestamp falls within peak crime hours.
    
    Args:
        timestamp: datetime object
        
    Returns:
        True if time is during peak crime hours (20:00-06:00)
    """
    hour = timestamp.hour
    start, end = get_peak_crime_hours()
    if start > end:  # Wrap around midnight
        return hour >= start or hour < end
    return start <= hour < end


def get_time_risk_multiplier(timestamp: datetime) -> float:
    """
    Get a risk multiplier based on time of day.
    Peak hours get higher multipliers.
    
    Args:
        timestamp: datetime object
        
    Returns:
        Risk multiplier [0.8, 1.5]:
        - 1.5 during peak hours (20:00-06:00)
        - 1.0 during moderate hours (06:00-20:00)
    """
    if is_peak_crime_time(timestamp):
        return 1.5
    return 1.0


def format_timestamp(timestamp: datetime) -> str:
    """
    Format timestamp to ISO format string.
    
    Args:
        timestamp: datetime object
        
    Returns:
        ISO format string (YYYY-MM-DDTHH:MM:SS)
    """
    return timestamp.isoformat()


def get_time_of_day_label(timestamp: datetime) -> str:
    """
    Get a human-readable label for time of day.
    
    Args:
        timestamp: datetime object
        
    Returns:
        String describing time of day
    """
    hour = timestamp.hour
    
    if 5 <= hour < 12:
        return "Morning"
    elif 12 <= hour < 17:
        return "Afternoon"
    elif 17 <= hour < 20:
        return "Evening"
    else:
        return "Night"
