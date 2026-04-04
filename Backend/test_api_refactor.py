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
    assert crime == 0.0, "Placeholder should return 0.0"
    print("PASS: Crime placeholder function works")


def test_service_layer():
    """Test service layer integration."""
    print("\nTEST 2: Service Layer")
    print("-" * 60)
    
    model = BeeWareRiskModel()
    model.load("beeware_model.pkl")
    
    extractor = FeatureExtractor()
    analyzer = RouteAnalyzer(model, extractor)
    service = SafetyAnalysisService(model, extractor, analyzer)
    
    timestamp = datetime(2024, 3, 15, 12, 0)
    
    result = service.analyze_location(
        latitude=28.6315,
        longitude=77.2167,
        timestamp=timestamp,
        crime_density_norm=0.3,
    )
    
    assert "latitude" in result
    assert "longitude" in result
    assert "safety_score" in result
    assert "label" in result
    assert "color" in result
    assert result["crime_density_norm"] == 0.3
    
    print(f"PASS: Single location analysis works")
    print(f"  Location: ({result['latitude']}, {result['longitude']})")
    print(f"  Safety Score: {result['safety_score']:.1f}/100")
    print(f"  Label: {result['label']}")
    print(f"  Crime Density: {result['crime_density_norm']}")


def test_route_service():
    """Test route analysis through service."""
    print("\nTEST 3: Route Analysis Service")
    print("-" * 60)
    
    model = BeeWareRiskModel()
    model.load("beeware_model.pkl")
    
    extractor = FeatureExtractor()
    analyzer = RouteAnalyzer(model, extractor)
    service = SafetyAnalysisService(model, extractor, analyzer)
    
    timestamp = datetime(2024, 3, 15, 22, 0)
    
    waypoints = [
        {
            "latitude": 28.6315,
            "longitude": 77.2167,
            "timestamp": timestamp,
            "crime_density_norm": 0.2,
            "name": "Start",
        },
        {
            "latitude": 28.6289,
            "longitude": 77.2215,
            "timestamp": timestamp,
            "crime_density_norm": 0.5,
            "name": "Middle",
        },
        {
            "latitude": 28.6263,
            "longitude": 77.2267,
            "timestamp": timestamp,
            "crime_density_norm": 0.3,
            "name": "End",
        },
    ]
    
    result = service.analyze_route(waypoints, route_name="Test Route")
    
    assert result["route_name"] == "Test Route"
    assert result["total_segments"] == 3
    assert "safety_score" in result
    assert "category" in result
    assert len(result["segment_details"]) == 3
    
    print(f"PASS: Route analysis works")
    print(f"  Route: {result['route_name']}")
    print(f"  Safety Score: {result['safety_score']:.1f}/100")
    print(f"  Category: {result['category']}")
    print(f"  Total Segments: {result['total_segments']}")
    print(f"  High Risk Segments: {result['high_risk_segments']}")


def test_bulk_locations():
    """Test bulk location analysis."""
    print("\nTEST 4: Bulk Location Analysis Service")
    print("-" * 60)
    
    model = BeeWareRiskModel()
    model.load("beeware_model.pkl")
    
    extractor = FeatureExtractor()
    analyzer = RouteAnalyzer(model, extractor)
    service = SafetyAnalysisService(model, extractor, analyzer)
    
    timestamp = datetime(2024, 3, 15, 12, 0)
    
    locations = [
        {
            "latitude": 28.6315,
            "longitude": 77.2167,
            "timestamp": timestamp,
            "crime_density_norm": 0.1,
        },
        {
            "latitude": 28.6289,
            "longitude": 77.2215,
            "timestamp": timestamp,
            "crime_density_norm": 0.5,
        },
        {
            "latitude": 28.6263,
            "longitude": 77.2267,
            "timestamp": timestamp,
            "crime_density_norm": 0.8,
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
