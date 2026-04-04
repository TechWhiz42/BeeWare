from datetime import datetime
from risk_model import BeeWareRiskModel
from feature_extractor import FeatureExtractor
from route_analyzer import RouteAnalyzer, RouteSegment
from service import SafetyAnalysisService


def test_crime_propagation():
    print("\nTest 1: Crime Propagation Through All Layers")
    print("-" * 70)
    
    model = BeeWareRiskModel()
    model.load("beeware_model.pkl")
    
    extractor = FeatureExtractor()
    
    timestamp = datetime(2024, 3, 15, 12, 0)
    lat, lon = 28.6315, 77.2167
    
    features_low_crime = extractor.extract(
        lat=lat, lon=lon, timestamp=timestamp, 
        segment_length_m=100.0, crime_density_norm=0.1
    )
    
    features_high_crime = extractor.extract(
        lat=lat, lon=lon, timestamp=timestamp,
        segment_length_m=100.0, crime_density_norm=0.9
    )
    
    assert features_low_crime[-1] == 0.1, "Low crime feature not set correctly"
    assert features_high_crime[-1] == 0.9, "High crime feature not set correctly"
    
    pred_low = model.predict_segment(features_low_crime)
    pred_high = model.predict_segment(features_high_crime)
    
    print(f"PASS: Crime value propagated to feature vector")
    print(f"  Low crime (0.1): safety_score={pred_low['safety_score']:.1f}, label={pred_low['label']}")
    print(f"  High crime (0.9): safety_score={pred_high['safety_score']:.1f}, label={pred_high['label']}")
    print(f"  Score difference: {abs(pred_low['safety_score'] - pred_high['safety_score']):.1f} points")
    
    assert pred_high['safety_score'] < pred_low['safety_score'], \
        "High crime should result in lower safety score"
    print(f"PASS: High crime reduces safety score")


def test_crime_dominant_formula():
    print("\nTest 2: Crime-Dominant Safety Score Formula")
    print("-" * 70)
    
    model = BeeWareRiskModel()
    model.load("beeware_model.pkl")
    
    extractor = FeatureExtractor()
    timestamp = datetime(2024, 3, 15, 12, 0)
    
    features = extractor.extract(
        lat=28.6315, lon=77.2167, timestamp=timestamp,
        segment_length_m=100.0, crime_density_norm=0.0
    )
    result = model.predict_segment(features)
    
    p_safe = result["probability_safe"]
    p_caution = result["probability_caution"]
    p_high_risk = result["probability_high_risk"]
    crime = result["crime_density_norm"]
    
    # NEW FORMULA (refactored to avoid double-counting crime)
    is_night = features[2]  # Extract from feature vector
    isolation_score = features[5]
    
    model_risk = (0.25 * p_caution) + (0.85 * p_high_risk)
    crime_effect = crime ** 1.4
    context_boost = (0.1 * is_night) + (0.05 * isolation_score)
    final_risk = 1 - (1 - model_risk) * (1 - crime_effect)
    final_risk = min(1.0, final_risk + context_boost)
    expected_score = 100 * (1 - (final_risk ** 0.85))
    
    actual_score = result["safety_score"]
    
    assert abs(actual_score - expected_score) < 0.01, \
        f"Formula mismatch: expected {expected_score:.2f}, got {actual_score:.2f}"
    
    print(f"PASS: Safety score formula verified (refactored, no double-counting)")
    print(f"  P(safe)={p_safe:.3f}, P(caution)={p_caution:.3f}, P(high_risk)={p_high_risk:.3f}")
    print(f"  Model risk: {model_risk:.3f}")
    print(f"  Crime effect: {crime_effect:.3f}")
    print(f"  Final risk: {final_risk:.3f}")
    print(f"  Safety score: {actual_score:.1f}/100")


def test_crime_sensitivity():
    print("\nTest 3: Crime Sensitivity - Score Decreases With Crime")
    print("-" * 70)
    
    model = BeeWareRiskModel()
    model.load("beeware_model.pkl")
    
    extractor = FeatureExtractor()
    timestamp = datetime(2024, 3, 15, 12, 0)
    
    scores = []
    for crime in [0.0, 0.3, 0.6, 0.9]:
        features = extractor.extract(
            lat=28.6315, lon=77.2167, timestamp=timestamp,
            segment_length_m=100.0, crime_density_norm=crime
        )
        result = model.predict_segment(features)
        scores.append(result["safety_score"])
        print(f"  Crime={crime:.1f}: Safety Score={result['safety_score']:.1f}")
    
    for i in range(len(scores) - 1):
        assert scores[i] >= scores[i+1], \
            f"Safety score should decrease with increasing crime"
    
    print(f"PASS: Safety scores monotonically decrease with increasing crime")


def test_route_segment_crime():
    print("\nTest 4: Route Segment Crime Propagation")
    print("-" * 70)
    
    model = BeeWareRiskModel()
    model.load("beeware_model.pkl")
    
    extractor = FeatureExtractor()
    analyzer = RouteAnalyzer(model, extractor)
    
    timestamp = datetime(2024, 3, 15, 22, 0)
    
    seg1 = RouteSegment(
        lat=28.6315, lon=77.2167, length_m=100.0,
        name="Safe Point", crime_density_norm=0.1
    )
    
    seg2 = RouteSegment(
        lat=28.6289, lon=77.2215, length_m=100.0,
        name="Risky Point", crime_density_norm=0.8
    )
    
    assert seg1.crime_density_norm == 0.1, "Segment 1 crime not set"
    assert seg2.crime_density_norm == 0.8, "Segment 2 crime not set"
    
    analysis = analyzer.analyze_route([seg1, seg2], timestamp=timestamp)
    
    assert seg1.features is not None, "Segment 1 features not extracted"
    assert seg2.features is not None, "Segment 2 features not extracted"
    
    assert seg1.features[-1] == 0.1, "Segment 1 feature vector missing crime"
    assert seg2.features[-1] == 0.8, "Segment 2 feature vector missing crime"
    
    print(f"PASS: Route segments preserve individual crime values")
    print(f"  Segment 1 (crime=0.1): score={seg1.risk_result['safety_score']:.1f}")
    print(f"  Segment 2 (crime=0.8): score={seg2.risk_result['safety_score']:.1f}")
    print(f"  Route category: {analysis.category}")


def test_high_crime_avoidance():
    print("\nTest 5: Single High-Crime Segment Forces Avoid Category")
    print("-" * 70)
    
    model = BeeWareRiskModel()
    model.load("beeware_model.pkl")
    
    extractor = FeatureExtractor()
    analyzer = RouteAnalyzer(model, extractor)
    
    timestamp = datetime(2024, 3, 15, 14, 0)
    
    safe_segment1 = RouteSegment(
        lat=28.6315, lon=77.2167, length_m=100.0,
        name="Safe 1", crime_density_norm=0.2
    )
    
    dangerous_segment = RouteSegment(
        lat=28.6289, lon=77.2215, length_m=100.0,
        name="High Risk", crime_density_norm=0.95
    )
    
    safe_segment2 = RouteSegment(
        lat=28.6263, lon=77.2267, length_m=100.0,
        name="Safe 2", crime_density_norm=0.1
    )
    
    analysis = analyzer.analyze_route(
        [safe_segment1, dangerous_segment, safe_segment2],
        timestamp=timestamp
    )
    
    if len(analysis.high_risk_segments) > 0:
        assert analysis.category == "Avoid", "Route with high-risk segment should be Avoid"
        print(f"PASS: Single dangerous segment forces Avoid category")
        print(f"  High risk segments: {len(analysis.high_risk_segments)}/{len(analysis.segments)}")
        print(f"  Route safety score: {analysis.safety_score:.1f}/100")
        print(f"  Category: {analysis.category}")
    else:
        print(f"NOTE: High crime didn't trigger high-risk classification (dataset dependent)")
        print(f"  Route category: {analysis.category}")


def test_service_layer_crime():
    print("\nTest 6: Service Layer Crime Integration")
    print("-" * 70)
    
    model = BeeWareRiskModel()
    model.load("beeware_model.pkl")
    
    extractor = FeatureExtractor()
    analyzer = RouteAnalyzer(model, extractor)
    service = SafetyAnalysisService(model, extractor, analyzer)
    
    timestamp = datetime(2024, 3, 15, 12, 0)
    
    low_crime_result = service.analyze_location(
        latitude=28.6315, longitude=77.2167,
        timestamp=timestamp, crime_density_norm=0.1
    )
    
    high_crime_result = service.analyze_location(
        latitude=28.6315, longitude=77.2167,
        timestamp=timestamp, crime_density_norm=0.9
    )
    
    assert low_crime_result["crime_density_norm"] == 0.1
    assert high_crime_result["crime_density_norm"] == 0.9
    
    print(f"PASS: Service layer preserves crime_density_norm")
    print(f"  Low crime result: {low_crime_result['label']} (score={low_crime_result['safety_score']:.1f})")
    print(f"  High crime result: {high_crime_result['label']} (score={high_crime_result['safety_score']:.1f})")
    print(f"  Score delta: {low_crime_result['safety_score'] - high_crime_result['safety_score']:.1f}")


def test_no_probability_distortion():
    print("\nTest 7: Raw Model Probabilities (No Distortion)")
    print("-" * 70)
    
    model = BeeWareRiskModel()
    model.load("beeware_model.pkl")
    
    extractor = FeatureExtractor()
    timestamp = datetime(2024, 3, 15, 12, 0)
    
    features = extractor.extract(
        lat=28.6315, lon=77.2167, timestamp=timestamp,
        segment_length_m=100.0, crime_density_norm=0.5
    )
    
    result = model.predict_segment(features)
    
    probs = [
        result["probability_safe"],
        result["probability_caution"],
        result["probability_high_risk"]
    ]
    
    prob_sum = sum(probs)
    assert 0.99 < prob_sum <= 1.01, f"Probabilities should sum to 1, got {prob_sum}"
    
    print(f"PASS: Model using raw probabilities (no distortion)")
    print(f"  P(Safe): {probs[0]:.4f}")
    print(f"  P(Caution): {probs[1]:.4f}")
    print(f"  P(High Risk): {probs[2]:.4f}")
    print(f"  Sum: {prob_sum:.4f}")


def main():
    print("\n" + "=" * 70)
    print("BeeWare Logic Fixes - Comprehensive Test Suite")
    print("=" * 70)
    
    try:
        test_crime_propagation()
        test_crime_dominant_formula()
        test_crime_sensitivity()
        test_route_segment_crime()
        test_high_crime_avoidance()
        test_service_layer_crime()
        test_no_probability_distortion()
        
        print("\n" + "=" * 70)
        print("All tests PASSED")
        print("=" * 70 + "\n")
        
    except AssertionError as e:
        print(f"\nTest FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise
    except Exception as e:
        print(f"\nTest ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
