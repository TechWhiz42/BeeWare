BeeWare ML System - Dataset-Driven Setup Guide
================================================

CRITICAL: This is now a DATASET-DRIVEN system only. 
All synthetic data generation has been removed.

=== TRAINING REQUIREMENTS ===

1. CSV Dataset Format
   - Must have columns for all 11 features (see FEATURE_NAMES below)
   - Must have a 'label' column (0=Safe, 1=Caution, 2=High Risk)
   - All values must be normalized between 0 and 1
   - No NaN values allowed

2. Required Features (FEATURE_NAMES order)
   - hour_sin: sin(hour_of_day * 2π/24)
   - hour_cos: cos(hour_of_day * 2π/24)
   - is_night: 1.0 if 20:00-05:00, else 0.0
   - is_rush_hour: 1.0 if 07-09 or 17-19, else 0.0
   - is_lit: lighting level (0-1)
   - isolation_score: isolation level (0-1)
   - poi_density_norm: points of interest density (0-1)
   - crowd_estimate: crowd level (0-1)
   - police_proximity: police station proximity (0-1)
   - segment_length_norm: normalized segment length (0-1)
   - crime_density_norm: crime density (0-1) *** PRIMARY SIGNAL ***

3. Training Command
   python train_model.py path/to/dataset.csv

=== ARCHITECTURE ===

Key Modules:
- feature_extractor.py
  * extract() now requires crime_density_norm parameter
  * All features are independent (no derivation from crime)
  * Time-based features only, no location-based hardcoding

- risk_model.py
  * train_from_csv() ONLY training method (no synthetic)
  * train() method REMOVED
  * Smooth crime penalty: crime_density * 0.3
  * Formula: risk_score = P_caution*0.5 + P_high_risk*1.0 + crime_penalty

- route_analyzer.py
  * Strict rule: If n_high > 0, route category = "Avoid"
  * Penalties:
    - high_risk_penalty = (n_high / n_total) * 60
    - worst_segment_penalty = (100 - min_score) * 0.5
  * Deterministic segment explanations

- train_model.py
  * NEW: Requires CSV path argument
  * OLD: No longer generates synthetic data

- main_model.py
  * train_from_csv() method for dataset training
  * load() to use pre-trained model
  * NO synthetic training capability

- main.py
  * /admin/train now requires csv_path query parameter
  * POST /admin/train?csv_path=path/to/data.csv

=== CRIME SIGNAL PIPELINE ===

Crime Integration:
1. Extract features from dataset CSV
2. Pass crime_density_norm to feature_extractor.extract()
3. In predict_segment():
   - Apply smooth penalty (alpha=0.6)
   - Adjust probabilities proportionally
   - Add crime_penalty to final_risk

Smooth Penalty Logic:
  risk_boost = crime_density * 0.6
  P_high_risk' = min(1.0, P_high_risk + risk_boost)
  P_safe' = max(0.0, P_safe - risk_boost * 0.7)
  P_caution' = max(0.0, P_caution - risk_boost * 0.3)
  
  (NO hard overrides like "if crime > 0.7 then class=2")

=== FEATURE INDEPENDENCE ===

Features are INDEPENDENT - NOT DERIVED FROM CRIME:
  ✓ is_lit: Set by time period only
  ✓ poi_density_norm: Set by time period only
  ✓ crowd_estimate: Set by time period only
  ✓ police_proximity: Set by time period only
  ✓ crime_density_norm: Externally provided

=== ROUTE-LEVEL LOGIC ===

Strict Safety Rules:
1. If ANY segment is High Risk (class=2):
   - Entire route category = "Avoid"
   - Aggressive score penalty applied

2. Route Score Calculation:
   final_score = 0.35*mean + 0.30*p25 + 0.20*p10 + 0.15*min
               - high_risk_penalty (60 * n_high/n_total)
               - worst_segment_penalty (0.5 * (100 - min_score))

3. Category Assignment:
   - n_high > 0 → "Avoid"
   - score >= 70 → "Safe"
   - score >= 45 → "Caution"
   - score < 45 → "Avoid"

=== API ENDPOINTS ===

Training (Dataset-only):
  POST /admin/train?csv_path=path/to/data.csv
  
Location Safety:
  POST /location/safety
  - Accepts: latitude, longitude, timestamp
  - Crime must be set externally (currently 0.0 placeholder)

Route Safety:
  POST /route/safety
  - Accepts: List of waypoints with timestamps
  
Bulk Analysis:
  POST /locations/safety/bulk
  - Analyze multiple locations at once

=== VALIDATION TESTS ===

Run: python test_integration.py

Tests coverage:
✓ Feature extraction accepts crime parameter
✓ Feature independence (no derivation)
✓ Smooth crime penalty (not hard override)
✓ CSV training validation
✓ Route strict rule (any high-risk → Avoid)
✓ Segment explanations (deterministic)

=== NEXT STEPS ===

1. Prepare CSV dataset with all 11 features
2. Validate feature normalization (0-1 range)
3. Train: python train_model.py your_dataset.csv
4. Test: python test_integration.py
5. Start API server with trained model
6. Implement crime data source integration externally
7. Pass crime_density_norm to extract() calls
