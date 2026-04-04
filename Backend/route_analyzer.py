import datetime
import numpy as np
from dataclasses import dataclass, field
from typing import Optional
from risk_model import FEATURE_NAMES


@dataclass
class RouteSegment:
    lat: float
    lon: float
    length_m: float = 100.0
    name: str = ""
    crime_density_norm: float = 0.0

    features: Optional[np.ndarray] = None
    risk_result: Optional[dict] = None


@dataclass
class RouteAnalysis:
    segments: list
    timestamp: datetime.datetime
    safety_score: float
    category: str
    color: str
    summary: str
    recommendations: list
    high_risk_segments: list
    segment_scores: list
    segment_explanations: list
    processing_time_ms: float = 0.0
    model_metrics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "safety_score": self.safety_score,
            "category": self.category,
            "color": self.color,
            "summary": self.summary,
            "recommendations": self.recommendations,
            "high_risk_segments": self.high_risk_segments,
            "segment_scores": self.segment_scores,
            "segment_explanations": self.segment_explanations,
            "timestamp": self.timestamp.isoformat(),
            "processing_time_ms": self.processing_time_ms,
        }


RECOMMENDATIONS = {
    "Safe": [
        "Route appears safe for travel at this time.",
        "Stay aware of your surroundings.",
        "Keep your phone charged and share your location.",
    ],
    "Caution": [
        "Exercise heightened awareness.",
        "Prefer well-lit and busier routes.",
        "Travel with someone if possible.",
        "Keep emergency contacts ready.",
        "Enable live location sharing.",
    ],
    "Avoid": [
        "This route has significant safety concerns.",
        "Consider an alternative route or transport.",
        "Inform someone about your route and ETA.",
        "Stay in well-lit and populated areas.",
        "Keep emergency numbers ready.",
        "Consider using verified cab services.",
    ],
}


class RouteAnalyzer:
    def __init__(self, model, feature_extractor):
        self.model = model
        self.extractor = feature_extractor

    def analyze_route(self, segments: list[RouteSegment],
                      timestamp: Optional[datetime.datetime] = None) -> RouteAnalysis:
        """Analyze route and return safety assessment with weighted scoring."""
        import time
        t0 = time.perf_counter()

        if timestamp is None:
            timestamp = datetime.datetime.now()

        segment_results = []
        segment_scores = []
        segment_lengths = []
        high_risk_segments = []
        segment_explanations = []

        for i, seg in enumerate(segments):
            try:
                # Extract features using spatial interpolation
                seg.features = self.extractor.extract(
                    lat=seg.lat,
                    lon=seg.lon,
                    segment_length_m=seg.length_m,
                )
                
                # Calculate POI proximity boost (police stations, hospitals)
                poi_info = self.extractor.calculate_poi_boost(seg.lat, seg.lon)

                # Validate feature vector (should be 4 features)
                assert len(seg.features) == 4, \
                    f"Segment {i} feature vector length {len(seg.features)} != 4"
                
                assert np.all(seg.features >= 0) and np.all(seg.features <= 1), \
                    f"Segment {i} features out of range [0,1]: {seg.features}"

                # Get prediction
                seg.risk_result = self.model.predict_segment(
                    seg.features,
                    poi_boost=poi_info.get("proximity_boost", 0.0)
                )
                score = seg.risk_result["safety_score"]
                
                # Apply time-based risk adjustment
                from time_utils import get_time_risk_multiplier
                time_multiplier = get_time_risk_multiplier(timestamp)
                adjusted_score = score / time_multiplier
                adjusted_score = max(0.0, min(100.0, adjusted_score))
                
                segment_scores.append(adjusted_score)
                segment_lengths.append(seg.length_m)
                risk_class = seg.risk_result["risk_class"]
                
                explanation = self._build_segment_explanation(seg.risk_result, i)

                seg_info = {
                    "index": i,
                    "name": seg.name or f"Segment {i+1}",
                    "lat": seg.lat,
                    "lon": seg.lon,
                    "length_m": seg.length_m,
                    "safety_score": adjusted_score,
                    "survivability_score": seg.risk_result["survivability_score"],
                    "crime_impact_score": seg.risk_result["crime_impact_score"],
                    "label": seg.risk_result["label"],
                    "color": seg.risk_result["color"],
                    "has_police_nearby": poi_info.get("has_police_nearby", False),
                    "has_hospital_nearby": poi_info.get("has_hospital_nearby", False),
                    "closest_police_dist_km": poi_info.get("closest_police_dist_km"),
                    "closest_hospital_dist_km": poi_info.get("closest_hospital_dist_km"),
                    "explanation": explanation,
                }
                segment_results.append(seg_info)
                segment_explanations.append(explanation)

                if risk_class == 2:
                    high_risk_segments.append(seg_info)
            except Exception as e:
                # Fallback for failed segment
                import logging
                logging.error(f"Error analyzing segment {i}: {str(e)}")
                fallback_score = 50.0
                segment_scores.append(fallback_score)
                segment_lengths.append(seg.length_m)
                
                seg_info = {
                    "index": i,
                    "name": seg.name or f"Segment {i+1}",
                    "lat": seg.lat,
                    "lon": seg.lon,
                    "length_m": seg.length_m,
                    "safety_score": fallback_score,
                    "survivability_score": 70.0,
                    "crime_impact_score": 20.0,
                    "label": "Caution",
                    "color": "#f59e0b",
                    "has_police_nearby": False,
                    "has_hospital_nearby": False,
                    "closest_police_dist_km": None,
                    "closest_hospital_dist_km": None,
                    "explanation": ["Analysis failed for this segment"],
                }
                segment_results.append(seg_info)
                segment_explanations.append("Analysis failed for this segment")

        n_high = len(high_risk_segments)
        n_total = len(segments)
        
        # Use weighted route scoring
        final_score, category, color = self._aggregate_route_score(
            segment_scores=segment_scores,
            segment_lengths=segment_lengths,
            n_high=n_high,
            n_total=n_total
        )

        pct_high = round(100 * n_high / max(n_total, 1), 1)

        summary = (
            f"{category} | Score: {final_score}/100 | "
            f"{n_high}/{n_total} high-risk segments ({pct_high}%)"
        )

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

        return RouteAnalysis(
            segments=segment_results,
            timestamp=timestamp,
            safety_score=final_score,
            category=category,
            color=color,
            summary=summary,
            recommendations=RECOMMENDATIONS[category],
            high_risk_segments=high_risk_segments,
            segment_scores=segment_scores,
            segment_explanations=segment_explanations,
            processing_time_ms=elapsed_ms,
            model_metrics=self.model.training_metrics,
        )


    def analyze_coordinates(self,
                             coords: list[tuple[float, float]],
                             timestamp: Optional[datetime.datetime] = None) -> RouteAnalysis:
        """Analyze route from list of coordinates."""
        from feature_extractor import haversine_distance
        
        segments = []
        for i, (lat, lon) in enumerate(coords):
            if i > 0:
                length_m = haversine_distance(
                    coords[i-1][0], coords[i-1][1], lat, lon
                ) * 1000
            else:
                length_m = 100.0

            segments.append(RouteSegment(
                lat=lat,
                lon=lon,
                length_m=length_m,
                name=f"Point {i+1}",
                crime_density_norm=0.0,  # Not used with new extractor
            ))

        return self.analyze_route(segments, timestamp=timestamp)

    def _aggregate_route_score(self, 
                               segment_scores: list, 
                               segment_lengths: list,
                               n_high: int, 
                               n_total: int) -> tuple:
        """
        Aggregate segment scores using weighted averaging by segment length.
        
        PRODUCTION FORMULA:
        - Weighted score: Σ(score * length) / Σ(length)
        - Final score: 0.7 * weighted_score + 0.3 * min(segment_scores)
        
        This ensures:
        - Longer high-risk segments have more impact
        - One bad segment doesn't ruin entire route (30% worst segment penalty)
        - Overall balance between average and worst case
        """
        if not segment_scores:
            return 50.0, "Caution", "#f59e0b"
        
        arr_scores = np.array(segment_scores)
        arr_lengths = np.array(segment_lengths)
        
        # Handle case where all lengths are zero
        if np.sum(arr_lengths) == 0:
            arr_lengths = np.ones_like(arr_lengths)
        
        # Weighted average: Σ(score * length) / Σ(length)
        weighted_score = float(np.sum(arr_scores * arr_lengths) / np.sum(arr_lengths))
        
        # Worst single segment (to avoid ignoring bad spots)
        worst_score = float(np.min(arr_scores))
        
        # Final score: 70% weighted + 30% worst case
        final_score = round(
            (0.7 * weighted_score) + (0.3 * worst_score),
            1
        )
        
        # Ensure bounded
        final_score = max(0.0, min(100.0, final_score))
        
        # Category assignment (smoother transitions)
        if final_score >= 75:
            category = "Safe"
            color = "#22c55e"
        elif final_score >= 50:
            category = "Caution"
            color = "#f59e0b"
        else:
            category = "Avoid"
            color = "#ef4444"
        
        return final_score, category, color

    def _build_segment_explanation(self, risk_result: dict, index: int) -> str:
        """Build human-readable explanation for segment risk."""
        crime_density = risk_result.get("crime_density", 0)
        prob_high_risk = risk_result.get("probability_high_risk", 0)
        label = risk_result["label"]
        explanation_list = risk_result.get("explanation", [])
        
        # Use the model's explanation if available
        if explanation_list:
            return f"Segment {index+1}: {'; '.join(explanation_list)}"
        
        # Fallback explanation
        reasons = []
        
        if crime_density > 0.7:
            reasons.append("high crime area")
        elif crime_density > 0.5:
            reasons.append("elevated crime risk")
        
        if label == "High Risk":
            if prob_high_risk > 0.8:
                reasons.append("high risk classification")
            
            if crime_density > 0.6:
                reasons.append("dangerous area")
        elif label == "Caution":
            reasons.append("caution advised")
        
        if not reasons:
            reasons.append("standard conditions")
        
        explanation = f"Segment {index+1}: {', '.join(reasons)}"
        return explanation

    @staticmethod
    def _time_label(dt: datetime.datetime) -> str:
        """Generate time period label."""
        hour = dt.hour
        if 5 <= hour < 12:
            period = "morning"
        elif 12 <= hour < 17:
            period = "afternoon"
        elif 17 <= hour < 20:
            period = "evening"
        else:
            period = "night"

        return f"{dt.strftime('%H:%M')} ({period})"