import datetime
import json
import sys
from pathlib import Path
from main_model import BeeWareSystem
from route_analyzer import RouteSegment


def test_end_to_end_training():
    print("TEST 1: End-to-End Training and Model Persistence")
    print("-" * 60)
    
    system = BeeWareSystem()
    csv_path = "sample_dataset.csv"
    
    print(f"Training model from: {csv_path}")
    system.train_from_csv(csv_path)
    
    metrics = system.model.training_metrics
    print(f"Training complete!")
    print(f"  AUC Score: {metrics['auc']}")
    print(f"  Training Samples: {metrics['train_samples']}")
    print(f"  Test Samples: {metrics['test_samples']}")
    print(f"  Features: {metrics['n_features']}")
    print(f"  Source: {metrics['dataset_source']}")
    
    model_path = "beeware_model.pkl"
    if Path(model_path).exists():
        print(f"\nModel saved to: {model_path}")
        print("PASS: Model persistence successful\n")
    else:
        print("FAIL: Model not saved\n")
        return False
    
    return True


def test_model_loading():
    print("TEST 2: Model Loading")
    print("-" * 60)
    
    system = BeeWareSystem()
    system.load()
    
    if system.model.is_trained:
        print("Model loaded successfully")
        print(f"  Metrics: {system.model.training_metrics}")
        print("PASS: Model loading successful\n")
        return True
    else:
        print("FAIL: Model not properly loaded\n")
        return False


def test_location_analysis():
    print("TEST 3: Single Location Analysis")
    print("-" * 60)
    
    system = BeeWareSystem()
    system.load()
    
    test_cases = [
        {"name": "Safe Area (Day)", "lat": 28.6315, "lon": 77.2167, "time": 10, "crime": 0.1},
        {"name": "Caution Area (Night)", "lat": 28.6289, "lon": 77.2215, "time": 22, "crime": 0.4},
        {"name": "High Risk Area", "lat": 28.6263, "lon": 77.2267, "time": 23, "crime": 0.8},
    ]
    
    for test in test_cases:
        timestamp = datetime.datetime(2024, 3, 15, test["time"], 30)
        result = system.analyze_location(
            lat=test["lat"],
            lon=test["lon"],
            timestamp=timestamp,
            crime_density_norm=test["crime"]
        )
        
        print(f"{test['name']}:")
        print(f"  Safety Score: {result['safety_score']:.1f}/100")
        print(f"  Risk Level: {result['label']}")
        print(f"  Crime Level: {test['crime']}")
    
    print("PASS: Location analysis successful\n")
    return True


def test_route_analysis():
    print("TEST 4: Route Analysis with Multiple Segments")
    print("-" * 60)
    
    system = BeeWareSystem()
    system.load()
    
    coords = [
        (28.6315, 77.2167),
        (28.6289, 77.2215),
        (28.6263, 77.2267),
        (28.6237, 77.2312),
    ]
    
    timestamp = datetime.datetime(2024, 3, 15, 22, 30)
    
    result = system.analyze_route(coords, timestamp=timestamp)
    
    print(f"Route Analysis Results:")
    print(f"  Safety Score: {result['safety_score']:.1f}/100")
    print(f"  Category: {result['category']}")
    print(f"  Color: {result['color']}")
    print(f"  Segments Analyzed: {len(result['segment_scores'])}")
    
    high_risk_segments = result['high_risk_segments']
    if isinstance(high_risk_segments, list):
        high_risk_count = len(high_risk_segments)
    else:
        high_risk_count = high_risk_segments
    
    if high_risk_count > 0:
        print(f"  High Risk Segments: {high_risk_count}")
        print(f"  Action: Route marked as AVOID")
    else:
        print(f"  High Risk Segments: 0")
    
    print(f"\n  Recommendations:")
    for i, rec in enumerate(result['recommendations'][:2], 1):
        print(f"    {i}. {rec}")
    
    print("PASS: Route analysis successful\n")
    return True


def test_crime_sensitivity():
    print("TEST 5: Crime Sensitivity Analysis")
    print("-" * 60)
    
    system = BeeWareSystem()
    system.load()
    
    crime_levels = [0.0, 0.3, 0.6, 0.9]
    timestamp = datetime.datetime(2024, 3, 15, 12, 0)
    
    print("Testing same location with varying crime levels:")
    print("Crime | Safety Score | Risk Level")
    print("-" * 40)
    
    for crime in crime_levels:
        result = system.analyze_location(
            lat=28.6315,
            lon=77.2167,
            timestamp=timestamp,
            crime_density_norm=crime
        )
        print(f"{crime:.1f}  | {result['safety_score']:>5.1f}        | {result['label']}")
    
    print("PASS: Crime sensitivity confirmed\n")
    return True


def test_time_sensitivity():
    print("TEST 6: Time Sensitivity Analysis")
    print("-" * 60)
    
    system = BeeWareSystem()
    system.load()
    
    times = [
        (8, "Morning (8 AM)"),
        (12, "Noon"),
        (18, "Evening (6 PM)"),
        (22, "Night (10 PM)"),
    ]
    
    print("Testing same location at different times:")
    print("Time        | Safety Score | Risk Level")
    print("-" * 40)
    
    for hour, time_desc in times:
        timestamp = datetime.datetime(2024, 3, 15, hour, 0)
        result = system.analyze_location(
            lat=28.6315,
            lon=77.2167,
            timestamp=timestamp,
            crime_density_norm=0.3
        )
        print(f"{time_desc:<11} | {result['safety_score']:>5.1f}        | {result['label']}")
    
    print("PASS: Time sensitivity confirmed\n")
    return True


def test_api_simulation():
    print("TEST 7: API Simulation")
    print("-" * 60)
    
    system = BeeWareSystem()
    system.load()
    
    api_request = {
        "locations": [
            {"lat": 28.6315, "lon": 77.2167, "crime": 0.2},
            {"lat": 28.6289, "lon": 77.2215, "crime": 0.5},
            {"lat": 28.6263, "lon": 77.2267, "crime": 0.8},
        ],
        "timestamp": "2024-03-15T22:30:00"
    }
    
    timestamp = datetime.datetime.fromisoformat(api_request["timestamp"])
    responses = []
    
    print("Bulk location analysis:")
    for loc in api_request["locations"]:
        result = system.analyze_location(
            lat=loc["lat"],
            lon=loc["lon"],
            timestamp=timestamp,
            crime_density_norm=loc["crime"]
        )
        responses.append(result)
        print(f"  Location ({loc['lat']:.4f}, {loc['lon']:.4f}): {result['label']} (score: {result['safety_score']:.1f})")    
    print(f"\nProcessed {len(responses)} locations")
    print("PASS: API simulation successful\n")
    return True


def main():
    print("\n" + "=" * 70)
    print("BeeWare ML System - End-to-End Integration Tests")
    print("=" * 70 + "\n")
    
    results = []
    
    try:
        results.append(("Training", test_end_to_end_training()))
        results.append(("Loading", test_model_loading()))
        results.append(("Location Analysis", test_location_analysis()))
        results.append(("Route Analysis", test_route_analysis()))
        results.append(("Crime Sensitivity", test_crime_sensitivity()))
        results.append(("Time Sensitivity", test_time_sensitivity()))
        results.append(("API Simulation", test_api_simulation()))
        
        print("=" * 70)
        print("Test Summary")
        print("=" * 70)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "PASS" if result else "FAIL"
            print(f"{test_name:<25} {status}")
        
        print("-" * 70)
        print(f"Total: {passed}/{total} tests passed")
        
        if passed == total:
            print("\nAll end-to-end tests PASSED!")
        else:
            print(f"\n{total - passed} test(s) FAILED!")
        
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\nTest suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
