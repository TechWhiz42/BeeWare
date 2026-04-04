import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from risk_model import BeeWareRiskModel
from feature_extractor import FeatureExtractor
from route_analyzer import RouteAnalyzer, RouteSegment
from validators import ValidationError
from time_utils import extract_time_features, get_time_risk_multiplier, format_timestamp

logger = logging.getLogger(__name__)


def _get_fallback_result(latitude: float, longitude: float, crime: float) -> Dict[str, Any]:
    """
    Generate a fallback result when model/db fails.
    Approximates safety based on crime alone (graceful degradation).
    """
    # Simple approximation: safety = 100 - (crime * 100)
    # With some stability bounds
    approx_safety = max(0.0, min(100.0, 100 - (crime * 70)))
    
    # Determine category
    if approx_safety >= 70:
        label, color = "Safe", "#22c55e"
    elif approx_safety >= 45:
        label, color = "Caution", "#f59e0b"
    else:
        label, color = "High Risk", "#ef4444"
    
    return {
        "latitude": latitude,
        "longitude": longitude,
        "safety_score": round(approx_safety, 1),
        "label": label,
        "color": color,
        "probability_safe": max(0.0, approx_safety / 100),
        "probability_caution": 0.3,
        "probability_high_risk": max(0.0, (100 - approx_safety) / 100),
        "crime_density_norm": crime,
        "confidence": 0.5,  # Low confidence for fallback
        "explanation": ["Fallback calculation: model unavailable"],
        "timestamp": datetime.now().isoformat(),
        "is_fallback": True,
    }


class SafetyAnalysisService:
    def __init__(self, model: BeeWareRiskModel, extractor: FeatureExtractor, 
                 analyzer: RouteAnalyzer):
        self.model = model
        self.extractor = extractor
        self.analyzer = analyzer
    
    def analyze_location(self, latitude: float, longitude: float,
                        timestamp: Optional[datetime] = None,
                        crime_density_norm: float = 0.5) -> Dict[str, Any]:
        """
        Analyze safety of a single location with time-based risk adjustment.
        Includes graceful fallback if model is unavailable.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            timestamp: Optional datetime for time-based risk adjustment
            crime_density_norm: Crime density (kept for API compatibility)
        """
        try:
            if not self.model.is_trained:
                logger.warning("Model not trained, using fallback")
                return _get_fallback_result(latitude, longitude, crime_density_norm)
            
            # Extract features using spatial interpolation
            features = self.extractor.extract(
                lat=latitude,
                lon=longitude,
                segment_length_m=100.0,
            )
            
            prediction = self.model.predict_segment(features)
            
            # Apply time-based risk adjustment if timestamp provided
            adjusted_safety_score = prediction["safety_score"]
            time_features = {}
            time_label = ""
            
            if timestamp:
                time_features = extract_time_features(timestamp)
                time_multiplier = get_time_risk_multiplier(timestamp)
                # Apply time multiplier to adjust safety score
                # Lower score = higher risk, so multiply by multiplier
                adjusted_safety_score = prediction["safety_score"] / time_multiplier
                adjusted_safety_score = max(0.0, min(100.0, adjusted_safety_score))
                
                # Adjust label if time makes it significantly riskier
                if adjusted_safety_score < 45 and prediction["safety_score"] >= 45:
                    prediction["label"] = "Caution"
                    prediction["color"] = "#f59e0b"
                elif adjusted_safety_score < 25 and prediction["safety_score"] >= 25:
                    prediction["label"] = "High Risk"
                    prediction["color"] = "#ef4444"
            
            result = {
                "latitude": latitude,
                "longitude": longitude,
                "safety_score": adjusted_safety_score,
                "label": prediction["label"],
                "color": prediction["color"],
                "confidence": prediction["confidence"],
                "explanation": prediction["explanation"],
                "probability_safe": prediction["probability_safe"],
                "probability_caution": prediction["probability_caution"],
                "probability_high_risk": prediction["probability_high_risk"],
                "crime_density": prediction["crime_density"],
                "timestamp": format_timestamp(timestamp) if timestamp else None,
                "time_features": time_features,
                "is_fallback": False,
            }
            
            return result
        except Exception as e:
            logger.error(f"Error in analyze_location: {str(e)}")
            # Return fallback
            return _get_fallback_result(latitude, longitude, crime_density_norm)
    
    def analyze_route(self, waypoints: List[Dict[str, Any]], 
                     route_name: str, timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Analyze safety of a route with time-based risk adjustment.
        Uses spatial interpolation to compute features, not pre-computed crime values.
        """
        try:
            if not self.model.is_trained:
                raise ValueError("Model not trained")
            
            if len(waypoints) < 2:
                raise ValueError("Route must have at least 2 waypoints")
            
            segments = []
            for i, wp in enumerate(waypoints):
                segment = RouteSegment(
                    lat=wp["latitude"],
                    lon=wp["longitude"],
                    length_m=100.0,
                    name=wp.get("name", f"Point {i+1}"),
                    crime_density_norm=0.0,  # Not used with new extractor
                    timestamp=wp.get("timestamp", timestamp),  # Use waypoint timestamp or route timestamp
                )
                segments.append(segment)
            
            # Analyze route with timestamp for time-based adjustments
            analysis = self.analyzer.analyze_route(segments, timestamp=timestamp)
            
            return {
                "route_name": route_name,
                "safety_score": analysis.safety_score,
                "category": analysis.category,
                "color": analysis.color,
                "summary": analysis.summary,
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
                        "length_m": seg["length_m"],
                        "safety_score": seg["safety_score"],
                        "label": seg["label"],
                        "color": seg["color"],
                        "explanation": seg["explanation"],
                    }
                    for i, seg in enumerate(analysis.segments)
                ],
                "recommendations": analysis.recommendations,
                "processing_time_ms": analysis.processing_time_ms,
                "is_fallback": False,
            }
        except Exception as e:
            logger.error(f"Error in analyze_route: {str(e)}")
            # Return fallback with approximation
            approx_safety = 50.0  # Safe default
            
            category, color = "Caution", "#f59e0b"
            
            return {
                "route_name": route_name,
                "safety_score": round(approx_safety, 1),
                "category": category,
                "color": color,
                "summary": f"{category} - Fallback calculation",
                "total_segments": len(waypoints),
                "recommendations": ["Route analysis failed, use fallback estimate"],
                "is_fallback": True,
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
            )
            results.append(result)
            
            if result["label"] == "High Risk":
                high_risk_count += 1
        
        return {
            "count": len(results),
            "results": results,
            "high_risk_count": high_risk_count,
        }
