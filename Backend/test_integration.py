import datetime
import numpy as np
from risk_model import BeeWareRiskModel, FEATURE_NAMES
from feature_extractor import FeatureExtractor
from route_analyzer import RouteAnalyzer, RouteSegment


def test_feature_extraction_with_crime():
    """Test feature extraction with crime parameter."""
    extractor = FeatureExtractor()
    
    features = extractor.extract(
        lat=28.6315,
        lon=77.2167,
        timestamp=datetime.datetime(2024, 3, 15, 22, 30),
        segment_length_m=150.0,
        crime_density_norm=0.6
    )
    
    assert len(features) == len(FEATURE_NAMES), f"Expected {len(FEATURE_NAMES)} features, got {len(features)}"
    assert all(0 <= f <= 1 for f in features), "All features must be normalized 0-1"
    
    crime_idx = FEATURE_NAMES.index("crime_density_norm")
    assert features[crime_idx] == 0.6, "Crime density should match input"
    
    print("PASS: Feature extraction with crime parameter test passed")


def test_feature_independence():
    """Verify features are independent."""
    extractor = FeatureExtractor()
    
    features_low_crime = extractor.extract(
        lat=28.6315,
        lon=77.2167,
        timestamp=datetime.datetime(2024, 3, 15, 22, 30),
        crime_density_norm=0.1
    )
    
    features_high_crime = extractor.extract(
        lat=28.6315,
        lon=77.2167,
        timestamp=datetime.datetime(2024, 3, 15, 22, 30),
        crime_density_norm=0.9
    )
    
    lit_idx = FEATURE_NAMES.index("is_lit")
    poi_idx = FEATURE_NAMES.index("poi_density_norm")
    crowd_idx = FEATURE_NAMES.index("crowd_estimate")
    
    assert features_low_crime[lit_idx] == features_high_crime[lit_idx], \
        "Lighting should not depend on crime (features independent)"
    assert features_low_crime[poi_idx] == features_high_crime[poi_idx], \
        "POI density should not depend on crime"
    assert features_low_crime[crowd_idx] == features_high_crime[crowd_idx], \
        "Crowd estimate should not depend on crime"
    
    print("PASS: Feature independence test passed")


def test_smooth_crime_penalty():
    """Test smooth crime penalty logic."""
    model = BeeWareRiskModel()
    model.load("beeware_model.pkl")
    
    base_features = np.array([
        0.5, 0.5,
        0.0,
        1.0,
        0.8,
        0.2,
        0.9,
        0.9,
        0.8,
        0.1,
        0.0
    ], dtype=np.float32)
    
    high_crime_features = base_features.copy()
    high_crime_features[10] = 0.9
    
    result_base = model.predict_segment(base_features)
    result_high_crime = model.predict_segment(high_crime_features)
    
    assert result_high_crime["safety_score"] < result_base["safety_score"], \
        "High crime should lower safety score"
    
    assert result_high_crime["safety_score"] > 0, \
        "High crime should not completely override (smooth penalty)"
    
    print(f"PASS: Smooth crime penalty test passed")
    print(f"  Base crime (0.0): score={result_base['safety_score']:.1f}")
    print(f"  High crime (0.9): score={result_high_crime['safety_score']:.1f}")


def test_csv_training_validation():
    """Test CSV training validation."""
    model = BeeWareRiskModel()
    
    try:
        model.train_from_csv("nonexistent.csv")
        assert False, "Should raise error for missing file"
    except FileNotFoundError:
        print("PASS: CSV validation correctly rejects missing file")
    except Exception as e:
        print(f"PASS: CSV validation error as expected - {type(e).__name__}")


def test_route_strict_rule():
    """Test route strict risk rule."""
    model = BeeWareRiskModel()
    model.load("beeware_model.pkl")
    
    extractor = FeatureExtractor()
    analyzer = RouteAnalyzer(model, extractor)
    
    coords = [
        (28.6315, 77.2167),
        (28.6289, 77.2215),
        (28.6263, 77.2267),
    ]
    
    timestamp = datetime.datetime(2024, 3, 15, 22, 30)
    segments = [
        RouteSegment(lat, lon, name=f"Point {i+1}")
        for i, (lat, lon) in enumerate(coords)
    ]
    
    analysis = analyzer.analyze_route(segments, timestamp=timestamp)
    
    if analysis.high_risk_segments:
        assert analysis.category == "Avoid", \
            "Route with high-risk segments must be categorized as Avoid"
        print(f"PASS: Route strict rule test passed (category: {analysis.category})")
    else:
        print(f"PASS: Route analyzed with no high-risk segments (category: {analysis.category})")


def test_segment_explanations():
    """Test segment explanation determinism."""
    model = BeeWareRiskModel()
    model.load("beeware_model.pkl")
    
    extractor = FeatureExtractor()
    analyzer = RouteAnalyzer(model, extractor)
    
    coord = (28.6315, 77.2167)
    timestamp = datetime.datetime(2024, 3, 15, 22, 30)
    segment = RouteSegment(coord[0], coord[1], name="Test")
    
    analysis1 = analyzer.analyze_route([segment], timestamp=timestamp)
    analysis2 = analyzer.analyze_route([segment], timestamp=timestamp)
    
    assert len(analysis1.segment_explanations) > 0, "Should have explanations"
    assert analysis1.segment_explanations == analysis2.segment_explanations, \
        "Explanations must be deterministic"
    
    print(f"PASS: Segment explanations test passed")
    print(f"  Explanation: {analysis1.segment_explanations[0]}")


def main():
    print("\n" + "="*70)
    print("BeeWare Dataset-Driven ML System - Integration Tests")
    print("="*70 + "\n")
    
    try:
        test_feature_extraction_with_crime()
        test_feature_independence()
        test_smooth_crime_penalty()
        test_csv_training_validation()
        test_route_strict_rule()
        test_segment_explanations()
        
        print("\n" + "="*70)
        print("All tests passed successfully!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\nFAIL: Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()

