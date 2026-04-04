import math
import numpy as np
from typing import List, Tuple, Dict, Optional


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
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
    
    K_NEIGHBORS = 8
    MAX_DISTANCE_KM = 5.0
    
    def __init__(self, area_features: Optional[List[Dict]] = None):
        self.area_features = area_features or []
        
    def set_area_features(self, area_features: List[Dict]):
        self.area_features = area_features
    
    def extract(self, lat: float, lon: float, segment_length_m: float = 100.0) -> np.ndarray:
        neighbors = self._find_nearest_neighbors(lat, lon, self.K_NEIGHBORS)
        
        if not neighbors:
            return self._get_default_features()
        
        crime_density = self._interpolate_idw(neighbors, "crime_score")
        population_density = self._interpolate_idw(neighbors, "population_density")
        road_density = self._interpolate_idw(neighbors, "road_density")
        visibility_score = self._interpolate_idw(neighbors, "night_light_intensity")
        
        crime_density = self._normalize(crime_density, 0.0, 1.0)
        population_density = self._normalize(population_density, 0.0, 1.0)
        road_density = self._normalize(road_density, 0.0, 1.0)
        visibility_score = self._normalize(visibility_score, 0.0, 1.0)
        
        features = np.array([
            crime_density,
            population_density,
            road_density,
            visibility_score,
        ], dtype=np.float32)
        
        features = np.clip(features, 0.0, 1.0)
        
        # Validate
        assert len(features) == 4, \
            f"Feature vector length {len(features)} != expected 4"
        assert np.all(features >= 0) and np.all(features <= 1), \
            f"Feature values out of range [0,1]: {features}"
        
        return features
    
    def _find_nearest_neighbors(self, lat: float, lon: float, k: int) -> List[Tuple[int, float, Dict]]:
        if not self.area_features:
            return []
        
        distances = []
        for i, record in enumerate(self.area_features):
            dist = haversine_distance(
                lat, lon,
                record["latitude"], record["longitude"]
            )
            
            if dist <= self.MAX_DISTANCE_KM:
                distances.append((i, dist, record))
        
        distances.sort(key=lambda x: x[1])
        return distances[:k]
    
    def _interpolate_idw(self, neighbors: List[Tuple[int, float, Dict]], 
                         field: str) -> float:
        if not neighbors:
            return 0.5
        
        numerator = 0.0
        denominator = 0.0
        
        for idx, dist, record in neighbors:
            if dist < 0.01:
                return record.get(field, 0.5)
            
            weight = 1.0 / dist
            value = record.get(field, 0.5)
            
            numerator += value * weight
            denominator += weight
        
        if denominator == 0:
            return 0.5
        
        return numerator / denominator
    
    def _normalize(self, value: float, min_val: float, max_val: float) -> float:
        if max_val <= min_val:
            return 0.5
        
        normalized = (value - min_val) / (max_val - min_val)
        return np.clip(normalized, 0.0, 1.0)
    
    def _get_default_features(self) -> np.ndarray:
        return np.array([0.5, 0.5, 0.5, 0.5], dtype=np.float32)
    
    @staticmethod
    def create_from_database(db_records: List[Dict]) -> "FeatureExtractor":
        return FeatureExtractor(area_features=db_records)
