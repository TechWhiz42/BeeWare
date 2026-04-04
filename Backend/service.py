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
        "crime_density": crime,
        "confidence": 0.5,
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
            # Ensure timestamp is not None
            if timestamp is None:
                timestamp = datetime.now()
            
            # Extract features using spatial interpolation
            features = self.extractor.extract(
                lat=latitude,
                lon=longitude,
                segment_length_m=100.0,
            )
            
            # Get base safety score from deterministic formula
            try:
                prediction = self.model.predict_segment(features)
            except Exception as e:
                logger.error(f"Model prediction failed: {str(e)}")
                return _get_fallback_result(latitude, longitude, crime_density_norm)
            
            # Apply time-based risk adjustment
            base_score = prediction["safety_score"]
            time_multiplier = get_time_risk_multiplier(timestamp)
            
            # Time multiplier > 1 means higher risk (night time)
            # So we reduce the safety score
            adjusted_safety_score = base_score / time_multiplier
            adjusted_safety_score = max(0.0, min(100.0, adjusted_safety_score))
            
            # Extract time features for response
            time_features = extract_time_features(timestamp)
            
            # Update label if time significantly affects risk
            label = prediction["label"]
            color = prediction["color"]
            
            if adjusted_safety_score < 45 and base_score >= 45:
                # Time made it risky
                label = "Caution"
                color = "#f59e0b"
            elif adjusted_safety_score < 25 and base_score >= 25:
                label = "High Risk"
                color = "#ef4444"
            
            # Build explanation with time context
            explanation = prediction["explanation"][:]
            hour = timestamp.hour
            if hour >= 22 or hour < 6:
                explanation.append("Night time increases risk")
            if 7 <= hour <= 10 or 18 <= hour <= 21:
                explanation.append("Rush hour crowd impact")
            
            result = {
                "latitude": latitude,
                "longitude": longitude,
                "safety_score": round(adjusted_safety_score, 1),
                "label": label,
                "color": color,
                "confidence": prediction["confidence"],
                "explanation": explanation,
                "probability_safe": prediction["probability_safe"],
                "probability_caution": prediction["probability_caution"],
                "probability_high_risk": prediction["probability_high_risk"],
                "crime_density": prediction["crime_density"],
                "crime_density_norm": crime_density_norm,
                "timestamp": format_timestamp(timestamp),
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
            # Ensure timestamp is not None
            if timestamp is None:
                timestamp = datetime.now()
            
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
                )
                segments.append(segment)
            
            # Analyze route with timestamp for time-based adjustments
            analysis = self.analyzer.analyze_route(segments, timestamp=timestamp)
            
            return {
                "route_name": route_name,
                "safety_score": round(analysis.safety_score, 1),
                "category": analysis.category,
                "color": analysis.color,
                "summary": analysis.summary,
                "timestamp": format_timestamp(timestamp),
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
                        "safety_score": round(seg["safety_score"], 1),
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
            approx_safety = 50.0
            category, color = "Caution", "#f59e0b"
            
            return {
                "route_name": route_name,
                "safety_score": round(approx_safety, 1),
                "category": category,
                "color": color,
                "summary": f"{category} - Fallback calculation",
                "timestamp": format_timestamp(timestamp if timestamp else datetime.now()),
                "total_segments": len(waypoints) if waypoints else 0,
                "high_risk_segments": 0,
                "high_risk_percentage": 0.0,
                "segment_details": [],
                "recommendations": ["Route analysis failed, use fallback estimate"],
                "processing_time_ms": 0.0,
                "is_fallback": True,
            }
    
    def analyze_multiple_locations(self, locations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze safety of multiple locations."""
        try:
            results = []
            high_risk_count = 0
            
            for location in locations:
                try:
                    result = self.analyze_location(
                        latitude=location["latitude"],
                        longitude=location["longitude"],
                        timestamp=location.get("timestamp"),
                        crime_density_norm=location.get("crime_density_norm", 0.5),
                    )
                    results.append(result)
                    
                    if result["label"] == "High Risk":
                        high_risk_count += 1
                except Exception as e:
                    logger.error(f"Error analyzing location: {str(e)}")
                    # Add fallback for this location
                    results.append(_get_fallback_result(
                        location.get("latitude", 0),
                        location.get("longitude", 0),
                        location.get("crime_density_norm", 0.5)
                    ))
            
            return {
                "count": len(results),
                "results": results,
                "high_risk_count": high_risk_count,
            }
        except Exception as e:
            logger.error(f"Error in analyze_multiple_locations: {str(e)}")
            return {
                "count": 0,
                "results": [],
                "high_risk_count": 0,
            }
