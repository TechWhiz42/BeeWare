import math
import datetime
import numpy as np
from typing import Optional


class FeatureExtractor:
    def __init__(self, db=None):
        self.db = db

    def extract(
        self,
        lat: float,
        lon: float,
        timestamp: Optional[datetime.datetime] = None,
        segment_length_m: float = 100.0,
    ) -> np.ndarray:

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

        env = self._get_environment(lat, lon, hour)
        features.update(env)

        features["isolation_score"] = 1.0 - features["poi_density_norm"]
        features["segment_length_norm"] = min(1.0, segment_length_m / 2000.0)

        from risk_model import FEATURE_NAMES

        vector = np.array(
            [features.get(name, 0.5) for name in FEATURE_NAMES],
            dtype=np.float32
        )

        return np.clip(vector, 0.0, 1.0)

    def _get_environment(self, lat, lon, hour):
        if self.db:
            data = self._fetch_from_db(lat, lon)
            if data:
                return data
        return self._estimate_environment(hour)

    def _fetch_from_db(self, lat, lon):
        return None

    def _estimate_environment(self, hour):
        is_night = hour >= 20 or hour <= 5

        if is_night:
            return {
                "is_lit": 0.4,
                "poi_density_norm": 0.3,
                "crowd_estimate": 0.2,
                "police_proximity": 0.3,
            }
        else:
            return {
                "is_lit": 0.8,
                "poi_density_norm": 0.6,
                "crowd_estimate": 0.7,
                "police_proximity": 0.4,
            }