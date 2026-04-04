from database import SessionLocal, AreaFeature
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import numpy as np
import pickle

print("\n" + "="*80)
print("BeeWare ML Model - Training on Local Database")
print("="*80 + "\n")

# Load data from local SQLite database
session = SessionLocal()

print("Loading data from local database...")
try:
    records = session.query(AreaFeature).all()
    print(f"✓ Loaded {len(records)} records from database")
except Exception as e:
    print(f"✗ Database error: {e}")
    exit(1)
finally:
    session.close()

if len(records) < 5:
    print("✗ Not enough data to train model (minimum 5 records needed)")
    exit(1)

# Prepare features
print("\nPreparing training data...")
X_data = []
y_data = []

for record in records:
    features = [
        record.crime_score,
        record.population_density / 15000,
        record.road_density,
        record.night_light_intensity / 100,
    ]
    
    label = record.risk_score if record.risk_score else 0.5
    
    X_data.append(features)
    y_data.append(label)

X = np.array(X_data, dtype=np.float32)
y = np.array(y_data, dtype=np.float32)

print(f"  Features shape: {X.shape}")
print(f"  Labels shape: {y.shape}")
print(f"  Feature ranges:")
print(f"    Crime Score: {X[:, 0].min():.3f} - {X[:, 0].max():.3f}")
print(f"    Population: {X[:, 1].min():.3f} - {X[:, 1].max():.3f}")
print(f"    Road Density: {X[:, 2].min():.3f} - {X[:, 2].max():.3f}")
print(f"    Night Light: {X[:, 3].min():.3f} - {X[:, 3].max():.3f}")
print(f"  Label ranges: {y.min():.3f} - {y.max():.3f}")

# Train model
print("\nTraining RandomForest model...")
print(f"  Training samples: {len(records)}")

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

model = RandomForestRegressor(
    n_estimators=200,
    max_depth=20,
    min_samples_split=10,
    min_samples_leaf=4,
    random_state=42,
    n_jobs=-1
)

model.fit(X_scaled, y)
print(f"  ✓ Model trained successfully")

# Evaluate
train_score = model.score(X_scaled, y)
y_pred = model.predict(X_scaled)
rmse = np.sqrt(mean_squared_error(y, y_pred))
mae = mean_absolute_error(y, y_pred)

print(f"\nModel Performance:")
print(f"  Training R² Score: {train_score:.4f}")
print(f"  Training RMSE: {rmse:.4f}")
print(f"  Training MAE: {mae:.4f}")

# Feature importance
importances = model.feature_importances_
features = ["Crime Score", "Population Density", "Road Density", "Night Light"]
print(f"\nFeature Importance:")
for feat, imp in zip(features, importances):
    print(f"  {feat}: {imp*100:.2f}%")

# Save model and scaler with metadata
print(f"\nSaving model...")
try:
    model_data = {
        "model": model,
        "scaler": scaler,
        "is_trained": True,
        "metrics": {
            "train_r2": train_score,
            "train_rmse": rmse,
            "train_mae": mae,
            "total_samples": len(records),
        },
        "feature_names": ["crime_score", "population_density_norm", "road_density", "night_light_intensity_norm"],
        "normalization_params": {
            "pop_density_min": min([r.population_density for r in records]),
            "pop_density_max": max([r.population_density for r in records]),
            "night_light_min": min([r.night_light_intensity for r in records]),
            "night_light_max": max([r.night_light_intensity for r in records]),
        }
    }
    with open("beeware_model_local.pkl", "wb") as f:
        pickle.dump(model_data, f)
    print(f"  ✓ Model saved to beeware_model_local.pkl")
except Exception as e:
    print(f"  ✗ Error saving model: {e}")
    exit(1)

# Test predictions
print(f"\nTesting predictions on sample data:")
for i, record in enumerate(records[:5]):
    features = np.array([[
        record.crime_score,
        record.population_density / 15000,
        record.road_density,
        record.night_light_intensity / 100,
    ]], dtype=np.float32)
    
    features_scaled = scaler.transform(features)
    prediction = model.predict(features_scaled)[0]
    actual = record.risk_score
    
    print(f"  Record {i+1}: Predicted={prediction:.3f}, Actual={actual:.3f}, Area=({record.latitude:.2f}, {record.longitude:.2f})")

print("\n" + "="*80)
print("Training completed successfully!")
print("="*80 + "\n")
