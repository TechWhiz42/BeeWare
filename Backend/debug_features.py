#!/usr/bin/env python3
"""Debug script to check feature extraction and safety scores."""

from main import extractor, model, _create_area_features
from database import AREA_COORDINATES
from datetime import datetime

print("=" * 80)
print("DEBUG: Feature Extraction and Safety Scores")
print("=" * 80)

# Check if extractor has area features
area_features = _create_area_features()
print(f"\n1. Area features created: {len(area_features)} records")

if area_features:
    # Print first few
    for i, af in enumerate(area_features[:3]):
        print(f"   Area {i}: lat={af['latitude']}, lon={af['longitude']}, "
              f"crime_score={af['crime_score']:.3f}, "
              f"population={af['population_density']}, "
              f"road={af['road_density']}, visibility={af['night_light_intensity']}")

print(f"\n2. Extractor area_features: {len(extractor.area_features)} records")

# Test feature extraction at different area coordinates
print("\n3. Testing feature extraction at area coordinates:")

for area_id, (lat, lon) in list(AREA_COORDINATES.items())[:5]:
    features = extractor.extract(lat, lon)
    print(f"\n   Area {area_id} ({lat}, {lon}):")
    print(f"      Features: crime={features[0]:.3f}, pop={features[1]:.3f}, "
          f"road={features[2]:.3f}, visibility={features[3]:.3f}")
    
    # Also check neighbors
    neighbors = extractor._find_nearest_neighbors(lat, lon, 8)
    print(f"      Neighbors found: {len(neighbors)}")
    if neighbors:
        for idx, dist, rec in neighbors[:2]:
            print(f"         - Distance: {dist:.2f} km, crime={rec['crime_score']:.3f}")

# Now test predictions
print("\n" + "=" * 80)
print("4. Testing safety score predictions:")
print("=" * 80)

if not model.is_trained:
    print("\n   Training model...")
    model.train_from_csv('sample_dataset.csv')

for area_id in [1, 5, 10, 15]:
    lat, lon = AREA_COORDINATES[area_id]
    features = extractor.extract(lat, lon)
    pred = model.predict_segment(features)
    print(f"\n   Area {area_id}: Safety Score = {pred['safety_score']:.1f}")

print("\n" + "=" * 80)
