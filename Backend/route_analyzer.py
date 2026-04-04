import datetime
import numpy as np
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RouteSegment:
    lat: float
    lon: float
    road_type: str = "residential"
    length_m: float = 100.0
    name: str = ""

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
            "timestamp": self.timestamp.isoformat(),
            "processing_time_ms": self.processing_time_ms,
        }


CATEGORY_THRESHOLDS = {
    (70, 100): ("Safe", "#22c55e", ""),
    (45, 70): ("Caution", "#f59e0b", ""),
    (0, 45): ("Avoid", "#ef4444", ""),
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


def aggregate_segment_recommendations(segments: list) -> list[str]:
    avoid_recs = set()
    caution_recs = set()
    safe_recs = set()
    
    for seg in segments:
        if seg.risk_result:
            label = seg.risk_result["label"]
            recs = seg.risk_result.get("recommendations", [])
            
            if label == "High Risk":
                avoid_recs.update(recs)
            elif label == "Caution":
                caution_recs.update(recs)
            else:
                safe_recs.update(recs)
    
    combined = []
    if avoid_recs:
        combined.extend(sorted(list(avoid_recs)))
    if caution_recs:
        combined.extend(sorted(list(caution_recs)))
    if safe_recs:
        combined.extend(sorted(list(safe_recs)))
    
    return combined


class RouteAnalyzer:
    def __init__(self, model, feature_extractor):
        self.model = model
        self.extractor = feature_extractor

    def analyze_route(self, segments: list[RouteSegment],
                      timestamp: Optional[datetime.datetime] = None) -> RouteAnalysis:
        import time
        t0 = time.perf_counter()

        if timestamp is None:
            timestamp = datetime.datetime.now()

        segment_results = []
        segment_scores = []
        high_risk_segments = []
        all_explanations = []

        for i, seg in enumerate(segments):
            seg.features = self.extractor.extract(
                lat=seg.lat,
                lon=seg.lon,
                timestamp=timestamp,
                road_type=seg.road_type,
                segment_length_m=seg.length_m,
            )

            seg.risk_result = self.model.predict_segment(seg.features)
            score = seg.risk_result["safety_score"]
            segment_scores.append(score)

            seg_info = {
                "index": i,
                "name": seg.name or f"Segment {i+1}",
                "lat": seg.lat,
                "lon": seg.lon,
                "safety_score": score,
                "label": seg.risk_result["label"],
                "color": seg.risk_result["color"],
            }
            segment_results.append(seg_info)

            if seg.risk_result["risk_class"] == 2:
                high_risk_segments.append(seg_info)
                all_explanations.extend(seg.risk_result["explanation"][:2])

        arr = np.array(segment_scores)
        p10 = float(np.percentile(arr, 10))
        p25 = float(np.percentile(arr, 25))
        mean = float(np.mean(arr))

        final_score = round(0.40 * mean + 0.35 * p25 + 0.25 * p10, 1)
        final_score = max(0.0, min(100.0, final_score))

        category, color, _ = "Caution", "#f59e0b", ""
        for (lo, hi), (cat, col, _) in CATEGORY_THRESHOLDS.items():
            if lo <= final_score <= hi:
                category, color = cat, col
                break

        n_high = len(high_risk_segments)
        n_total = len(segments)
        pct_risk = round(100 * n_high / max(n_total, 1), 0)

        time_label = _time_label(timestamp)
        summary = (
            f"{category} route | Score: {final_score}/100 | "
            f"{n_high}/{n_total} high-risk segments ({pct_risk}%) | "
            f"Analyzed for {time_label}"
        )

        unique_explanations = list(dict.fromkeys(all_explanations))[:6]
        route_recommendations = aggregate_segment_recommendations(segments)
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

        return RouteAnalysis(
            segments=segment_results,
            timestamp=timestamp,
            safety_score=final_score,
            category=category,
            color=color,
            summary=summary,
            recommendations=route_recommendations if route_recommendations else RECOMMENDATIONS[category],
            high_risk_segments=high_risk_segments,
            segment_scores=segment_scores,
            processing_time_ms=elapsed_ms,
            model_metrics=self.model.training_metrics,
        )

    def analyze_coordinates(self,
                             coords: list[tuple[float, float]],
                             road_types: Optional[list[str]] = None,
                             timestamp: Optional[datetime.datetime] = None) -> RouteAnalysis:
        if road_types is None:
            road_types = ["residential"] * len(coords)

        segments = []
        for i, ((lat, lon), rtype) in enumerate(zip(coords, road_types)):
            if i > 0:
                from feature_extractor import haversine_km
                length_m = haversine_km(
                    coords[i-1][0], coords[i-1][1], lat, lon
                ) * 1000
            else:
                length_m = 100.0

            segments.append(RouteSegment(
                lat=lat,
                lon=lon,
                road_type=rtype,
                length_m=length_m,
                name=f"Point {i+1}"
            ))

        return self.analyze_route(segments, timestamp=timestamp)


def _time_label(dt: datetime.datetime) -> str:
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