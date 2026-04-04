"""
Time Utility Functions

Extracts temporal features from timestamps for safety analysis.
Provides time-based risk adjustment for deterministic safety formula.
"""

from datetime import datetime
from typing import Dict, Optional


def extract_time_features(timestamp: Optional[datetime]) -> Dict[str, float]:
    """
    Extract all time-based features from a timestamp.
    
    Args:
        timestamp: datetime object (or None, will use current time)
        
    Returns:
        Dictionary with time features
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    hour = timestamp.hour
    day_of_week = timestamp.weekday()  # 0=Monday, 6=Sunday
    
    return {
        "hour": hour,
        "day_of_week": day_of_week,
        "is_night": 1.0 if (hour >= 22 or hour < 6) else 0.0,  # Less safe
        "is_rush_hour": 1.0 if (7 <= hour <= 10 or 18 <= hour <= 21) else 0.0,  # More safe (crowded)
        "is_weekend": 1.0 if day_of_week >= 4 else 0.0,
    }


def get_time_risk_multiplier(timestamp: Optional[datetime]) -> float:
    """
    Get time-based risk adjustment for safety score.
    
    Formula:
    - Base: 1.0 (multiplier = divide, so no change)
    - If night (22:00-06:00): +0.25 (multiply by 1.25, less safe)
    - If rush hour (07:00-10:00, 18:00-21:00): -0.05 (multiply by 0.95, more safe)
    - Result clamped to [0.95, 1.35] (safer at rush hour, less safe at night)
    
    Args:
        timestamp: datetime object (or None, will use current time)
        
    Returns:
        Risk multiplier [0.95, 1.35]
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    hour = timestamp.hour
    
    time_risk = 0.0
    
    # Night time (22:00 to 06:00): HIGHER RISK
    is_night = (hour >= 22 or hour < 6)
    if is_night:
        time_risk += 0.25
    
    # Rush hour (7-10, 18-21): LOWER RISK (crowded = safer)
    is_rush_hour = (7 <= hour <= 10 or 18 <= hour <= 21)
    if is_rush_hour:
        time_risk -= 0.05  # NEGATIVE: reduces risk multiplier
    
    time_multiplier = 1.0 + time_risk
    return max(0.95, min(1.35, time_multiplier))


def format_timestamp(timestamp: Optional[datetime]) -> str:
    """
    Format timestamp to ISO format string.
    
    Args:
        timestamp: datetime object (or None, will use current time)
        
    Returns:
        ISO format string (YYYY-MM-DDTHH:MM:SS)
    """
    if timestamp is None:
        timestamp = datetime.now()
    return timestamp.isoformat()


def get_time_of_day_label(timestamp: Optional[datetime]) -> str:
    """
    Get a human-readable label for time of day.
    
    Args:
        timestamp: datetime object (or None, will use current time)
        
    Returns:
        String describing time of day
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    hour = timestamp.hour
    
    if 5 <= hour < 12:
        return "Morning"
    elif 12 <= hour < 17:
        return "Afternoon"
    elif 17 <= hour < 20:
        return "Evening"
    else:
        return "Night"
