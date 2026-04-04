import math
import datetime
import numpy as np
from typing import Optional
from risk_model import FEATURE_NAMES


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in kilometers."""
    R = 6371.0
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


class FeatureExtractor:
    def __init__(self):
        pass

    def extract(
        self,
        lat: float,
        lon: float,
        timestamp: Optional[datetime.datetime] = None,
        segment_length_m: float = 100.0,
        crime_density_norm: float = 0.0,
    ) -> np.ndarray:
        """Extract feature vector for a location."""
        if timestamp is None:
            timestamp = datetime.datetime.now()

        hour = timestamp.hour + timestamp.minute / 60.0
        hour_rad = 2 * math.pi * hour / 24

        features = {
            "hour_sin": math.sin(hour_rad),
            "hour_cos": math.cos(hour_rad),
            "is_night": 1.0 if (hour >= 20 or hour <= 5) else 0.0,
            "is_rush_hour": 1.0 if (7 <= hour <= 9 or 17 <= hour <= 19) else 0.0,
        }

        env = self._get_environment(hour, lat=lat, lon=lon)
        features.update(env)

        features["isolation_score"] = 1.0 - features["poi_density_norm"]
        features["segment_length_norm"] = min(1.0, segment_length_m / 2000.0)
        
        assert 0.0 <= crime_density_norm <= 1.0, \
            f"crime_density_norm {crime_density_norm} not in valid range [0, 1]"
        features["crime_density_norm"] = max(0.0, min(1.0, crime_density_norm))

        vector = np.array(
            [features.get(name, 0.5) for name in FEATURE_NAMES],
            dtype=np.float32
        )

        return np.clip(vector, 0.0, 1.0)

    def _get_environment(self, hour: float, lat: float = 0.0, lon: float = 0.0) -> dict:
        """Get environmental features based on time and location."""
        is_night = hour >= 20 or hour <= 5
        
        seed = int(abs(lat * 1000 + lon * 1000)) % 100
        spatial_factor = seed / 100.0
        
        if is_night:
            return {
                "is_lit": max(0.0, min(1.0, 0.3 + spatial_factor * 0.15)),
                "poi_density_norm": max(0.0, min(1.0, 0.2 + spatial_factor * 0.2)),
                "crowd_estimate": max(0.0, min(1.0, 0.15 + spatial_factor * 0.1)),
                "police_proximity": max(0.0, min(1.0, 0.35 - spatial_factor * 0.1)),
            }
        else:
            return {
                "is_lit": max(0.0, min(1.0, 0.75 + spatial_factor * 0.15)),
                "poi_density_norm": max(0.0, min(1.0, 0.55 + spatial_factor * 0.25)),
                "crowd_estimate": max(0.0, min(1.0, 0.65 + spatial_factor * 0.2)),
                "police_proximity": max(0.0, min(1.0, 0.45 - spatial_factor * 0.15)),
            }
