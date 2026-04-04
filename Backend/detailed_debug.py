import requests
import json
from database import SessionLocal, AreaFeature
from feature_extractor import FeatureExtractor

print("="*80)
print("Debugging BeeWare System - Local Database")
print("="*80 + "\n")

# Test 1: Database connectivity
print("1. DATABASE CHECK")
print("-" * 80)
try:
    session = SessionLocal()
    records = session.query(AreaFeature).limit(3).all()
    print(f"   ✓ Database connected")
    print(f"   ✓ Found {len(records)} test records")
    for i, r in enumerate(records):
        print(f"     {i+1}. ({r.latitude:.4f}, {r.longitude:.4f}) - Crime: {r.crime_score:.3f}")
    session.close()
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 2: Feature extraction
print("\n2. FEATURE EXTRACTION CHECK")
print("-" * 80)
try:
    session = SessionLocal()
    records = session.query(AreaFeature).all()
    area_features = [{
        "latitude": r.latitude,
        "longitude": r.longitude,
        "crime_score": r.crime_score,
        "population_density": r.population_density,
        "road_density": r.road_density,
        "night_light_intensity": r.night_light_intensity,
    } for r in records]
    session.close()
    
    extractor = FeatureExtractor(area_features)
    print(f"   ✓ FeatureExtractor initialized with {len(area_features)} records")
    
    # Test extraction at different points
    test_points = [
        (26.8430, 80.9846),
        (26.8603, 80.9411),
        (26.8849, 80.9677),
    ]
    
    for lat, lon in test_points:
        features = extractor.extract(lat, lon)
        print(f"   Point ({lat:.4f}, {lon:.4f}): {features}")
        
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: API health check
print("\n3. API HEALTH CHECK")
print("-" * 80)
try:
    response = requests.get("http://localhost:8000/health")
    data = response.json()
    print(f"   Response: {json.dumps(data, indent=2)}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 4: Single location prediction
print("\n4. API LOCATION PREDICTION")
print("-" * 80)
try:
    from datetime import datetime
    payload = {
        "latitude": 26.8430,
        "longitude": 80.9846,
        "timestamp": datetime.now().isoformat()
    }
    response = requests.post("http://localhost:8000/location/safety", json=payload)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Score: {data['safety_score']}")
        print(f"   Label: {data['label']}")
        print(f"   Explanation: {data['explanation']}")
    else:
        print(f"   Error: {response.text}")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "="*80)
