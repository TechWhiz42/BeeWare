from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class LocationInput:
    latitude: float
    longitude: float
    timestamp: object
    crime_density_norm: float


@dataclass
class WaypointInput:
    latitude: float
    longitude: float
    timestamp: object
    crime_density_norm: float
    name: Optional[str] = None


class ValidationError(ValueError):
    pass


def validate_latitude(lat: float) -> float:
    if not isinstance(lat, (int, float)):
        raise ValidationError("Latitude must be numeric")
    if lat < -90 or lat > 90:
        raise ValidationError(f"Latitude must be between -90 and 90, got {lat}")
    return lat


def validate_longitude(lon: float) -> float:
    if not isinstance(lon, (int, float)):
        raise ValidationError("Longitude must be numeric")
    if lon < -180 or lon > 180:
        raise ValidationError(f"Longitude must be between -180 and 180, got {lon}")
    return lon


def validate_crime_density(crime: float) -> float:
    if not isinstance(crime, (int, float)):
        raise ValidationError("Crime density must be numeric")
    if crime < 0 or crime > 1:
        raise ValidationError(f"Crime density must be between 0 and 1, got {crime}")
    return crime


def get_crime_density(lat: float, lon: float) -> float:
    """Get crime density for location from database.
    
    Queries the crime database to find the nearest area and
    returns normalized crime density [0, 1].
    
    Args:
        lat: Latitude [-90, 90]
        lon: Longitude [-180, 180]
    
    Returns:
        Crime density normalized to [0, 1]
    """
    from database import get_crime_density_from_db
    
    try:
        crime_density = get_crime_density_from_db(lat, lon)
        return validate_crime_density(crime_density)
    except Exception as e:
        logger.error(f"Error getting crime density for ({lat}, {lon}): {e}")
        return 0.0
