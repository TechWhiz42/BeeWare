"""
Production-Ready Feature Extractor

Implements realistic spatial interpolation using k-NN and inverse distance weighting.
No synthetic features, no time dependency.

Feature Vector (4 features, all normalized [0,1]):
1. crime_density - weighted spatial interpolation from area_features
2. population_density - weighted spatial interpolation from area_features
3. road_density - weighted spatial interpolation from area_features
4. visibility_score - night_light_intensity from area_features
"""

import math
import numpy as np
from typing import List, Tuple, Dict, Optional


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
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
    """
    Extract normalized features from geographic data using spatial interpolation.
    """
    
    K_NEIGHBORS = 8  # Use k=8 nearest neighbors for interpolation
    MAX_DISTANCE_KM = 5.0  # Max distance to consider for interpolation
    
    def __init__(self, area_features: Optional[List[Dict]] = None):
        """
        Args:
            area_features: List of dicts with keys: latitude, longitude, crime_score, 
                          population_density, night_light_intensity, road_density
        """
        self.area_features = area_features or []
        
    def set_area_features(self, area_features: List[Dict]):
        """Update area features data."""
        self.area_features = area_features
    
    def extract(self, lat: float, lon: float, segment_length_m: float = 100.0) -> np.ndarray:
        """
        Extract feature vector for a location using spatial interpolation.
        
        Args:
            lat: Latitude
            lon: Longitude
            segment_length_m: Segment length (for context, not used in features)
        
        Returns:
            Feature vector of shape (7,) with all values in [0, 1]
        """
        
        # Get k nearest neighbors and their distances
        neighbors = self._find_nearest_neighbors(lat, lon, self.K_NEIGHBORS)
        
        if not neighbors:
            # Fallback if no data available
            return self._get_default_features()
        
        # Spatial interpolation (inverse distance weighting)
        crime_density = self._interpolate_idw(neighbors, "crime_score")
        population_density = self._interpolate_idw(neighbors, "population_density")
        road_density = self._interpolate_idw(neighbors, "road_density")
        visibility_score = self._interpolate_idw(neighbors, "night_light_intensity")
        
        # Normalize to [0,1]
        crime_density = self._normalize(crime_density, 0.0, 1.0)
        population_density = self._normalize(population_density, 0.0, 1.0)
        road_density = self._normalize(road_density, 0.0, 1.0)
        visibility_score = self._normalize(visibility_score, 0.0, 1.0)
        
        # Build feature vector [crime_density, population_density, road_density, visibility_score]
        features = np.array([
            crime_density,
            population_density,
            road_density,
            visibility_score,
        ], dtype=np.float32)
        
        # Ensure all values in [0,1]
        features = np.clip(features, 0.0, 1.0)
        
        # Validate
        assert len(features) == 4, \
            f"Feature vector length {len(features)} != expected 4"
        assert np.all(features >= 0) and np.all(features <= 1), \
            f"Feature values out of range [0,1]: {features}"
        
        return features
    
    def _find_nearest_neighbors(self, lat: float, lon: float, k: int) -> List[Tuple[int, float, Dict]]:
        """
        Find k nearest neighbors with distances.
        
        Returns:
            List of (index, distance_km, record) tuples, sorted by distance
        """
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
        
        # Sort by distance and take top k
        distances.sort(key=lambda x: x[1])
        return distances[:k]
    
    def _interpolate_idw(self, neighbors: List[Tuple[int, float, Dict]], 
                         field: str) -> float:
        """
        Inverse distance weighting interpolation.
        
        Formula: value = Σ(value_i / distance_i) / Σ(1 / distance_i)
        """
        if not neighbors:
            return 0.5  # Default midpoint
        
        numerator = 0.0
        denominator = 0.0
        
        for idx, dist, record in neighbors:
            # Avoid division by zero for very close points
            if dist < 0.01:
                # If extremely close, use the value directly
                return record.get(field, 0.5)
            
            weight = 1.0 / dist
            value = record.get(field, 0.5)
            
            numerator += value * weight
            denominator += weight
        
        if denominator == 0:
            return 0.5
        
        return numerator / denominator
    
    def _normalize(self, value: float, min_val: float, max_val: float) -> float:
        """Normalize value to [0,1] range."""
        if max_val <= min_val:
            return 0.5
        
        normalized = (value - min_val) / (max_val - min_val)
        return np.clip(normalized, 0.0, 1.0)
    
    def _get_default_features(self) -> np.ndarray:
        """Return default feature vector when no area data available."""
        return np.array([0.5, 0.5, 0.5, 0.5], dtype=np.float32)
    
    @staticmethod
    def create_from_database(db_records: List[Dict]) -> "FeatureExtractor":
        """Factory method to create extractor from database records."""
        return FeatureExtractor(area_features=db_records)
