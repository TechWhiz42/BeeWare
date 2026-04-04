from database import SessionLocal, AreaFeature
from feature_extractor import FeatureExtractor

# Load features from database  
session = SessionLocal()
records = session.query(AreaFeature).limit(20).all()

area_features = []
for record in records:
    area_features.append({
        "latitude": record.latitude,
        "longitude": record.longitude,
        "crime_score": record.crime_score,
        "population_density": record.population_density,
        "road_density": record.road_density,
        "night_light_intensity": record.night_light_intensity,
    })

session.close()

print(f"Loaded {len(area_features)} features from database")
print("\nFirst 5 records:")
for i, feat in enumerate(area_features[:5]):
    print(f"  {i}: lat={feat['latitude']}, lon={feat['longitude']}, crime={feat['crime_score']:.3f}")

# Test feature extraction
extractor = FeatureExtractor(area_features)

test_points = [
    (26.8124, 75.8863, "Downtown"),
    (26.9100, 75.9000, "North"),
    (26.8500, 75.8200, "East"),
]

print("\n" + "="*70)
print("Feature Extraction Test")
print("="*70)

for lat, lon, name in test_points:
    features = extractor.extract(lat, lon)
    print(f"\n{name} ({lat}, {lon}):")
    print(f"  Crime Density: {features[0]:.3f}")
    print(f"  Population: {features[1]:.3f}")
    print(f"  Road Density: {features[2]:.3f}")
    print(f"  Night Light: {features[3]:.3f}")
    print(f"  Vector: {features}")
