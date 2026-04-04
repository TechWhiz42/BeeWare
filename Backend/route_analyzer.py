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
        """Analyze route and return safety assessment."""
        import time
        t0 = time.perf_counter()

        if timestamp is None:
            timestamp = datetime.datetime.now()

        segment_results = []
        segment_scores = []
        high_risk_segments = []
        segment_explanations = []

        for i, seg in enumerate(segments):
            assert seg.crime_density_norm >= 0.0 and seg.crime_density_norm <= 1.0, \
                f"Segment {i} crime_density_norm {seg.crime_density_norm} out of valid range [0, 1]"
            
            seg.features = self.extractor.extract(
                lat=seg.lat,
                lon=seg.lon,
                timestamp=timestamp,
                segment_length_m=seg.length_m,
                crime_density_norm=seg.crime_density_norm,
            )

            assert len(seg.features) == 11, \
                f"Segment {i} feature vector length {len(seg.features)} != 11"
            
            crime_idx = FEATURE_NAMES.index("crime_density_norm")
            assert seg.features[crime_idx] == seg.crime_density_norm, \
                f"Segment {i} feature vector crime {seg.features[crime_idx]} != segment crime {seg.crime_density_norm}"

            seg.risk_result = self.model.predict_segment(seg.features)
            score = seg.risk_result["safety_score"]
            segment_scores.append(score)
            risk_class = seg.risk_result["risk_class"]
            
            explanation = self._build_segment_explanation(seg.risk_result, i)

            seg_info = {
                "index": i,
                "name": seg.name or f"Segment {i+1}",
                "lat": seg.lat,
                "lon": seg.lon,
                "safety_score": score,
                "label": seg.risk_result["label"],
                "color": seg.risk_result["color"],
                "explanation": explanation,
            }
            segment_results.append(seg_info)
            segment_explanations.append(explanation)

            if risk_class == 2:
                high_risk_segments.append(seg_info)

        n_high = len(high_risk_segments)
        n_total = len(segments)
        
        final_score, category, color = self._aggregate_route_score(
            segment_scores, n_high, n_total
        )

        pct_high = round(100 * n_high / max(n_total, 1), 1)

        time_label = self._time_label(timestamp)
        summary = (
            f"{category} | Score: {final_score}/100 | "
            f"{n_high}/{n_total} high-risk segments ({pct_high}%) | {time_label}"
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
        from feature_extractor import haversine_km
        
        segments = []
        for i, (lat, lon) in enumerate(coords):
            if i > 0:
                length_m = haversine_km(
                    coords[i-1][0], coords[i-1][1], lat, lon
                ) * 1000
            else:
                length_m = 100.0

            segments.append(RouteSegment(
                lat=lat,
                lon=lon,
                length_m=length_m,
                name=f"Point {i+1}"
            ))

        return self.analyze_route(segments, timestamp=timestamp)

    def _aggregate_route_score(self, segment_scores: list, n_high: int, n_total: int) -> tuple:
        """Aggregate segment scores with strict risk penalties."""
        arr = np.array(segment_scores)
        
        min_score = float(np.min(arr))
        p10 = float(np.percentile(arr, 10))
        p25 = float(np.percentile(arr, 25))
        mean = float(np.mean(arr))
        
        high_risk_penalty = (n_high / max(n_total, 1)) * 60
        worst_segment_penalty = (100 - min_score) * 0.5
        
        final_score = round(
            0.35 * mean +
            0.30 * p25 +
            0.20 * p10 +
            0.15 * min_score -
            high_risk_penalty -
            worst_segment_penalty,
            1
        )
        
        final_score = max(0.0, min(100.0, final_score))
        
        if n_high > 0:
            category = "Avoid"
            color = "#ef4444"
        elif final_score >= 70:
            category = "Safe"
            color = "#22c55e"
        elif final_score >= 45:
            category = "Caution"
            color = "#f59e0b"
        else:
            category = "Avoid"
            color = "#ef4444"
        
        return final_score, category, color

    def _build_segment_explanation(self, risk_result: dict, index: int) -> str:
        """Build human-readable explanation for segment risk."""
        crime_density = risk_result.get("crime_density_norm", 0)
        prob_high_risk = risk_result.get("probability_high_risk", 0)
        label = risk_result["label"]
        
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