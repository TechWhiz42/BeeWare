import sqlite3
import math
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

DB_PATH = "../Database/crime.sqlite"

CRIME_STATS = {
    3: 12456,
    9: 12227,
    13: 13151,
    6: 12593,
    5: 12644,
    1: 12006,
    4: 12707,
    2: 12497,
    10: 13289,
    12: 12237,
    7: 11626,
    15: 12062,
    8: 12751,
    14: 11798,
    11: 12681,
}

AREA_COORDINATES = {
    1: (26.8, 80.85),
    2: (26.71, 80.97),
    3: (26.63, 80.90),
    4: (26.75, 80.75),
    5: (26.85, 80.85),
    6: (26.85, 81.15),
    7: (26.87, 80.90),
    8: (26.95, 80.72),
    9: (27.05, 80.80),
    10: (27.15, 80.68),
    11: (26.85, 80.65),
    12: (26.75, 81.05),
    13: (26.65, 81.10),
    14: (26.55, 81.15),
    15: (26.95, 80.55),
}

MAX_CRIME_COUNT = max(CRIME_STATS.values())
MIN_DISTANCE_KM = 5.0


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in kilometers."""
    R = 6371.0
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def find_nearest_area(latitude: float, longitude: float) -> Optional[int]:
    """Find nearest area to given coordinates."""
    min_distance = float('inf')
    nearest_area_id = None
    
    for area_id, (area_lat, area_lon) in AREA_COORDINATES.items():
        distance = haversine_distance(latitude, longitude, area_lat, area_lon)
        if distance < min_distance:
            min_distance = distance
            nearest_area_id = area_id
    
    if min_distance > 50:
        logger.warning(f"Nearest area {nearest_area_id} is {min_distance:.1f}km away")
    
    return nearest_area_id


def get_crime_for_area(area_id: int) -> int:
    """Get total crimes for an area."""
    return CRIME_STATS.get(area_id, 0)


def normalize_crime_density(crime_count: int, max_crimes: int = MAX_CRIME_COUNT) -> float:
    """Normalize crime count to [0, 1] range."""
    if max_crimes == 0:
        return 0.0
    
    normalized = min(1.0, max(0.0, crime_count / max_crimes))
    return float(normalized)


def get_crime_density_from_db(latitude: float, longitude: float) -> float:
    """
    Get crime density for a location.
    
    Process:
    1. Find nearest area to lat/lon
    2. Get total crimes for that area
    3. Normalize to [0, 1] range
    4. Return normalized crime density
    """
    try:
        nearest_area_id = find_nearest_area(latitude, longitude)
        
        if nearest_area_id is None:
            logger.warning(f"Could not find area for ({latitude}, {longitude})")
            return 0.0
        
        crime_count = get_crime_for_area(nearest_area_id)
        crime_density_norm = normalize_crime_density(crime_count)
        
        logger.debug(
            f"Crime for ({latitude}, {longitude}): "
            f"Area {nearest_area_id}, crimes={crime_count}, normalized={crime_density_norm:.3f}"
        )
        
        return crime_density_norm
    
    except Exception as e:
        logger.error(f"Error fetching crime density: {e}")
        return 0.0


def get_area_info(latitude: float, longitude: float) -> Dict[str, Any]:
    """Get area information for a location."""
    try:
        area_id = find_nearest_area(latitude, longitude)
        
        if area_id is None:
            return {"area_id": None, "crime_count": 0, "crime_density_norm": 0.0}
        
        crime_count = get_crime_for_area(area_id)
        crime_density = normalize_crime_density(crime_count)
        
        return {
            "area_id": area_id,
            "crime_count": crime_count,
            "crime_density_norm": crime_density
        }
    
    except Exception as e:
        logger.error(f"Error fetching area info: {e}")
        return {"area_id": None, "crime_count": 0, "crime_density_norm": 0.0}
