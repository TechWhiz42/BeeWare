from datetime import datetime
from validators import (
    validate_latitude, validate_longitude, validate_crime_density,
    ValidationError, get_crime_density
)
from service import SafetyAnalysisService
from risk_model import BeeWareRiskModel
from feature_extractor import FeatureExtractor
from route_analyzer import RouteAnalyzer


def test_validators():
    """Test input validation functions."""
    print("\nTEST 1: Input Validators")
    print("-" * 60)
    
    assert validate_latitude(45.5) == 45.5
    assert validate_longitude(-120.5) == -120.5
    assert validate_crime_density(0.5) == 0.5
    
    try:
        validate_latitude(91)
        assert False, "Should reject latitude > 90"
    except ValidationError:
        pass
    
    try:
        validate_longitude(181)
        assert False, "Should reject longitude > 180"
    except ValidationError:
        pass
    
    try:
        validate_crime_density(1.5)
        assert False, "Should reject crime > 1"
    except ValidationError:
        pass
    
    print("PASS: All validators work correctly")
    
    crime = get_crime_density(28.6315, 77.2167)
    assert 0.0 <= crime <= 1.0, f"Crime should be in [0, 1], got {crime}"
    assert crime > 0.0, "Crime database should return non-zero value for Lucknow location"
    print(f"PASS: Crime auto-fetch from database works (crime={crime:.4f})")


def test_service_layer():
    """Test service layer integration."""
    print("\nTEST 2: Service Layer")
    print("-" * 60)
    
    model = BeeWareRiskModel()
    model.load("beeware_model.pkl")
    
    extractor = FeatureExtractor()
    analyzer = RouteAnalyzer(model, extractor)
    service = SafetyAnalysisService(model, extractor, analyzer)
    
    result = service.analyze_location(
        latitude=28.6315,
        longitude=77.2167
    )
    
    assert "latitude" in result
    assert "longitude" in result
    assert "safety_score" in result
    assert "label" in result
    assert "color" in result
    
    print(f"PASS: Single location analysis works")
    print(f"  Location: ({result['latitude']}, {result['longitude']})")
    print(f"  Safety Score: {result['safety_score']:.1f}/100")
    print(f"  Label: {result['label']}")


def test_route_service():
    """Test route analysis through service."""
    print("\nTEST 3: Route Analysis Service")
    print("-" * 60)
    
    model = BeeWareRiskModel()
    model.load("beeware_model.pkl")
    
    extractor = FeatureExtractor()
    analyzer = RouteAnalyzer(model, extractor)
    service = SafetyAnalysisService(model, extractor, analyzer)
    
    waypoints = [
        {
            "latitude": 28.6315,
            "longitude": 77.2167,
            "name": "Start",
        },
        {
            "latitude": 28.6289,
            "longitude": 77.2215,
            "name": "Middle",
        },
        {
            "latitude": 28.6263,
            "longitude": 77.2267,
            "name": "End",
        },
    ]
    
    result = service.analyze_route(waypoints, route_name="Test Route")
    
    assert result["route_name"] == "Test Route"
    assert result["total_segments"] == 3
    assert "safety_score" in result
    assert "category" in result
    
    print(f"PASS: Route analysis works")
    print(f"  Route: {result['route_name']}")
    print(f"  Safety Score: {result['safety_score']:.1f}/100")
    print(f"  Category: {result['category']}")
    print(f"  Total Segments: {result['total_segments']}")


def test_bulk_locations():
    """Test bulk location analysis."""
    print("\nTEST 4: Bulk Location Analysis Service")
    print("-" * 60)
    
    model = BeeWareRiskModel()
    model.load("beeware_model.pkl")
    
    extractor = FeatureExtractor()
    analyzer = RouteAnalyzer(model, extractor)
    service = SafetyAnalysisService(model, extractor, analyzer)
    
    locations = [
        {
            "latitude": 28.6315,
            "longitude": 77.2167,
        },
        {
            "latitude": 28.6289,
            "longitude": 77.2215,
        },
        {
            "latitude": 28.6263,
            "longitude": 77.2267,
        },
    ]
    
    result = service.analyze_multiple_locations(locations)
    
    assert result["count"] == 3
    assert len(result["results"]) == 3
    assert result["high_risk_count"] >= 0
    
    print(f"PASS: Bulk location analysis works")
    print(f"  Total Locations: {result['count']}")
    print(f"  High Risk: {result['high_risk_count']}")
    
    for i, loc_result in enumerate(result["results"]):
        print(f"  Location {i+1}: {loc_result['label']} (score: {loc_result['safety_score']:.1f})")


def main():
    print("\n" + "=" * 70)
    print("BeeWare Backend Refactoring - Service Layer Tests")
    print("=" * 70)
    
    try:
        test_validators()
        test_service_layer()
        test_route_service()
        test_bulk_locations()
        
        print("\n" + "=" * 70)
        print("All tests PASSED")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\nTest FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
