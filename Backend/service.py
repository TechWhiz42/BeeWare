import logging
from datetime import datetime
from typing import List, Dict, Any

from risk_model import BeeWareRiskModel
from feature_extractor import FeatureExtractor
from route_analyzer import RouteAnalyzer, RouteSegment
from validators import ValidationError

logger = logging.getLogger(__name__)


class SafetyAnalysisService:
    def __init__(self, model: BeeWareRiskModel, extractor: FeatureExtractor, 
                 analyzer: RouteAnalyzer):
        self.model = model
        self.extractor = extractor
        self.analyzer = analyzer
    
    def analyze_location(self, latitude: float, longitude: float, 
                        timestamp: datetime, crime_density_norm: float) -> Dict[str, Any]:
        """Analyze safety of a single location."""
        if not self.model.is_trained:
            raise ValueError("Model not trained")
        
        features = self.extractor.extract(
            lat=latitude,
            lon=longitude,
            timestamp=timestamp,
            segment_length_m=100.0,
            crime_density_norm=crime_density_norm,
        )
        
        prediction = self.model.predict_segment(features)
        
        return {
            "latitude": latitude,
            "longitude": longitude,
            "safety_score": prediction["safety_score"],
            "label": prediction["label"],
            "color": prediction["color"],
            "probability_safe": prediction["probability_safe"],
            "probability_caution": prediction["probability_caution"],
            "probability_high_risk": prediction["probability_high_risk"],
            "crime_density_norm": crime_density_norm,
            "timestamp": timestamp.isoformat(),
        }
    
    def analyze_route(self, waypoints: List[Dict[str, Any]], 
                     route_name: str) -> Dict[str, Any]:
        """Analyze safety of a route with per-waypoint crime values."""
        if not self.model.is_trained:
            raise ValueError("Model not trained")
        
        if len(waypoints) < 2:
            raise ValueError("Route must have at least 2 waypoints")
        
        timestamp = waypoints[0]["timestamp"]
        
        segments = []
        for i, wp in enumerate(waypoints):
            segment = RouteSegment(
                lat=wp["latitude"],
                lon=wp["longitude"],
                length_m=100.0,
                name=wp.get("name", f"Point {i+1}"),
                crime_density_norm=wp["crime_density_norm"],
            )
            segments.append(segment)
        
        analysis = self.analyzer.analyze_route(segments, timestamp=timestamp)
        
        return {
            "route_name": route_name,
            "safety_score": analysis.safety_score,
            "category": analysis.category,
            "color": analysis.color,
            "summary": analysis.summary,
            "timestamp": timestamp.isoformat(),
            "total_segments": len(analysis.segments),
            "high_risk_segments": len(analysis.high_risk_segments),
            "high_risk_percentage": (
                100 * len(analysis.high_risk_segments) / len(analysis.segments)
                if analysis.segments else 0
            ),
            "segment_details": [
                {
                    "index": i,
                    "name": seg["name"],
                    "latitude": seg["lat"],
                    "longitude": seg["lon"],
                    "safety_score": seg["safety_score"],
                    "label": seg["label"],
                    "color": seg["color"],
                    "explanation": seg["explanation"],
                }
                for i, seg in enumerate(analysis.segments)
            ],
            "recommendations": analysis.recommendations,
            "processing_time_ms": analysis.processing_time_ms,
        }
    
    def analyze_multiple_locations(self, locations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze safety of multiple locations."""
        if not self.model.is_trained:
            raise ValueError("Model not trained")
        
        results = []
        high_risk_count = 0
        
        for location in locations:
            result = self.analyze_location(
                latitude=location["latitude"],
                longitude=location["longitude"],
                timestamp=location["timestamp"],
                crime_density_norm=location["crime_density_norm"],
            )
            results.append(result)
            
            if result["label"] == "High Risk":
                high_risk_count += 1
        
        return {
            "count": len(results),
            "results": results,
            "high_risk_count": high_risk_count,
        }
