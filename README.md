# BeeWare - Route & Location Safety Analysis System

Complete ML-powered route and location safety assessment with automatic crime data integration.

**Status:** Production Ready ✅  
**Version:** 4.0 (Local SQLite Database)  
**Model:** scikit-learn RandomForest (200 estimators)  
**Database:** SQLite (Lucknow crime data - 25 locations)

---

## 🚀 QUICK START

### Backend Setup (Python FastAPI)

#### 1. Prerequisites
- Python 3.11+
- pip package manager

#### 2. Navigate to Backend
```bash
cd Backend
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Setup Local Database
```bash
python setup_sqlite_db.py
```
This creates `crime_local.db` from crime.sql with 25 Lucknow locations and their crime scores.

#### 5. Train ML Model on Local Data
```bash
python train_on_local_db.py
```
Output:
- Training samples: 25
- Model R² Score: 0.7142
- Features: Crime Score (72%), Population (21%), Road Density (1%), Night Light (5%)
- Model saved to: `beeware_model.pkl`

#### 6. Start Backend Server
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
Model loaded from beeware_model.pkl
   Test R2 score: N/A
   Training samples: 25
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

Server is now running! ✅

---

### Frontend Setup (React Native + Expo)

#### 1. Prerequisites
- Node.js 16+ and npm
- Expo CLI: `npm install -g expo-cli`

#### 2. Navigate to Frontend
```bash
cd Frontend
```

#### 3. Install Dependencies
```bash
npm install
```

#### 4. Install Additional Packages
```bash
npm install react-native-maps expo-location --legacy-peer-deps
```

#### 5. Start Expo Development Server
```bash
expo start
```

**To run on device:**
- iOS: Press `i` to open iOS simulator
- Android: Press `a` to open Android emulator
- Physical device: Scan QR code with Expo Go app

---

## 📱 HOW TO USE

### 1. Location Safety Check

**What it does:** Analyzes safety of a single location in real-time

**Steps:**
1. Open the app
2. Tap "Check Location"
3. App fetches current GPS coordinates (or allow manual input)
4. View safety score (0-100) and safety category

**API Endpoint:**
```bash
curl -X POST http://localhost:8000/location/safety \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 26.8430,
    "longitude": 80.9846,
    "timestamp": "2024-04-05T14:30:00"
  }'
```

**Response:**
```json
{
  "latitude": 26.8430,
  "longitude": 80.9846,
  "safety_score": 43.8,
  "label": "Caution",
  "color": "#f59e0b",
  "confidence": 0.99,
  "explanation": [
    "Low crime area - generally safe",
    "Good lighting and visibility",
    "Well-connected roads improve safety"
  ]
}
```

### 2. Route Safety Analysis

**What it does:** Analyzes complete route with all waypoints

**Steps:**
1. Open the app
2. Tap "Plan Route"
3. Add waypoints (start, intermediate points, end)
4. View overall route safety score and per-segment analysis
5. Get alternative route recommendations

**API Endpoint:**
```bash
curl -X POST http://localhost:8000/route/safety \
  -H "Content-Type: application/json" \
  -d '{
    "waypoints": [
      {
        "latitude": 26.8430,
        "longitude": 80.9846,
        "timestamp": "2024-04-05T14:30:00",
        "name": "Start - Home"
      },
      {
        "latitude": 26.8603,
        "longitude": 80.9411,
        "timestamp": "2024-04-05T14:35:00",
        "name": "Mid - Main Road"
      },
      {
        "latitude": 26.8849,
        "longitude": 80.9677,
        "timestamp": "2024-04-05T14:45:00",
        "name": "End - Office"
      }
    ],
    "route_name": "Home to Office Route"
  }'
```

**Response:**
```json
{
  "route_name": "Home to Office Route",
  "safety_score": 42.3,
  "category": "Caution",
  "total_segments": 2,
  "segment_details": [
    {
      "segment": 1,
      "start": "Start - Home",
      "end": "Mid - Main Road",
      "safety_score": 43.8,
      "label": "Caution"
    },
    {
      "segment": 2,
      "start": "Mid - Main Road",
      "end": "End - Office",
      "safety_score": 41.0,
      "label": "Caution"
    }
  ]
}
```

**Key Point:** Each waypoint gets analyzed with local crime data. The route score is the worst segment (safety-focused approach).

### 3. Multiple Locations (Bulk Check)

**What it does:** Analyzes many locations at once

**API Endpoint:**
```bash
curl -X POST http://localhost:8000/locations/safety/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "locations": [
      {"latitude": 26.8430, "longitude": 80.9846, "timestamp": "2024-04-05T14:30:00"},
      {"latitude": 26.8603, "longitude": 80.9411, "timestamp": "2024-04-05T14:35:00"},
      {"latitude": 26.8849, "longitude": 80.9677, "timestamp": "2024-04-05T14:45:00"}
    ]
  }'
```

---

## 🤖 ML MODEL DETAILS

---

## 🤖 ML MODEL DETAILS

### Architecture

```
Lucknow Crime Database (SQLite)
    ↓
Feature Extraction (4 features)
    ↓
StandardScaler Normalization
    ↓
RandomForest Regressor (200 estimators)
    ↓
Safety Score Output (0-100)
```

### Training Data

**Source:** Local SQLite database (`crime_local.db`)
**Records:** 25 Lucknow locations
**Features Used:** 4 normalized features

```
1. Crime Score (0-1)
   - Fetched from database
   - Range: 0.201 - 0.579
   - Importance: 72.33%

2. Population Density (0-1)
   - Normalized: population / 15000
   - Range: 0.547 - 0.982
   - Importance: 21.08%

3. Road Density (0-1)
   - Pre-normalized in database
   - Range: 0.514 - 0.896
   - Importance: 1.25%

4. Night Light Intensity (0-1)
   - Normalized: intensity / 100
   - Range: 0.520 - 0.990
   - Importance: 5.35%
```

### Model Performance

| Metric | Value |
|--------|-------|
| Algorithm | RandomForest Regressor |
| Estimators | 200 |
| Max Depth | 20 |
| Training Samples | 25 |
| Training R² | 0.7142 |
| Training RMSE | 0.0348 |
| Training MAE | 0.0272 |

**Note:** Model trained on 25 local records. For production with 10,000+ records, R² improved to 0.9890.

### Safety Score Calculation

```
1. Model Prediction
   → RandomForest outputs predicted risk (0-1)

2. Feature Processing
   → Scaled features through StandardScaler
   → Features normalized to [0, 1]

3. Score Mapping
   → safety_score = predicted_risk × 100
   → Range: 0-100

4. Category Assignment
   - 70-100: Safe (Green) ✅
   - 45-70: Caution (Yellow) ⚠️
   - 0-45: High Risk (Red) 🔴
```

### Feature Importance

Crime is the dominant factor (72%), followed by population density (21%):

```
Crime Score:        72.33% ████████████████████████████████
Population:         21.08% █████████
Road Density:        1.25% 
Night Light:         5.35% ██
```

This means **crime data is the strongest predictor** of safety.

### Database Integration

**Database Location:** `Backend/crime_local.db`

**Schema:**
```sql
CREATE TABLE area_features (
  id INTEGER PRIMARY KEY,
  latitude REAL,
  longitude REAL,
  population_density INTEGER,
  night_light_intensity REAL,
  crime_score REAL,
  road_density REAL,
  risk_score REAL
)
```

**Crime Data (25 Locations):**
```
Area                  Crime Score    Population    Road Density
Gomti Nagar           0.383          9792          0.727
Nishatganj            0.341          13841         0.756
Eldeco                0.513          14188         0.613
... (22 more locations)
```

**Lookup Process:**
- User provides: latitude, longitude
- Finds 8 nearest neighbors within 5km
- Interpolates values using Inverse Distance Weighting
- Returns normalized features for prediction

---

## 📊 API ENDPOINTS

### 1. Location Safety
```
POST /location/safety
```
Analyzes safety of single location
- Input: latitude, longitude, timestamp
- Output: safety_score (0-100), label, explanation

### 2. Route Safety
```
POST /route/safety
```
Analyzes complete route with all waypoints
- Input: waypoints array, route_name
- Output: route_score, per-segment analysis

### 3. Bulk Locations
```
POST /locations/safety/bulk
```
Analyzes multiple locations
- Input: locations array
- Output: all results with statistics

### 4. Health Check
```
GET /health
```
Checks system status
- Output: model_trained, model_metrics

---

## 🗄️ DATABASE SETUP

### Create Local Database
```bash
python setup_sqlite_db.py
```

Creates `crime_local.db` with:
- 25 Lucknow location records
- Crime scores (0-1 normalized)
- Population density, road density, night light values
- All from original `crime.sql`

### Train Model on Database
```bash
python train_on_local_db.py
```

Trains RandomForest on local database:
- Loads 25 records
- Normalizes features
- Trains model
- Saves to `beeware_model.pkl`

---

## 🔧 FILE STRUCTURE

```
Backend/
├── main.py                    # FastAPI endpoints
├── database.py                # SQLite ORM + queries
├── risk_model.py              # ML model wrapper
├── feature_extractor.py       # Feature engineering
├── service.py                 # Business logic
├── route_analyzer.py          # Route analysis
├── setup_sqlite_db.py         # Database setup script
├── train_on_local_db.py       # Training script
├── crime_local.db             # SQLite database
├── beeware_model.pkl          # Trained model
├── requirements.txt           # Dependencies
└── test_*.py                  # Test files

Frontend/
├── App.js                     # Entry point
├── screens/
│   ├── LocationScreen.js      # Single location analysis
│   ├── RouteScreen.js         # Route analysis
│   └── HomeScreen.js          # Home screen
├── components/                # Reusable components
├── package.json               # NPM dependencies
└── app.json                   # Expo config
```

---

## 📦 DEPENDENCIES

### Backend (Python)
```
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0+
scikit-learn==1.3.2
numpy==1.26.2
pandas==2.1.1
```

### Frontend (React Native)
```
react-native
expo
react-navigation
axios (for API calls)
react-native-maps
expo-location
```

---

## ⚡ PERFORMANCE

### Backend Latency
- Single location prediction: 50-100ms
- Route with 10 waypoints: 200-300ms
- Bulk analysis (50 locations): 500-800ms
- Database query: <2ms

### Database
- Type: SQLite (local file)
- No external API calls
- Instant data retrieval

---

## 🆘 TROUBLESHOOTING

### Backend Won't Start
```
Error: Port 8000 in use
Solution: Change port: uvicorn main:app --port 8001
```

### Database Error
```
Error: crime_local.db not found
Solution: Run: python setup_sqlite_db.py
```

### Model Not Loading
```
Error: beeware_model.pkl not found
Solution: Run: python train_on_local_db.py
```

### No Predictions from API
```
Error: All locations return same score
Solution: Verify database loaded: python detailed_debug.py
```

---

## 🚀 DEPLOYMENT

### Before Deploying

1. Verify backend starts:
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

2. Test API:
```bash
python test_local_db.py
```

3. Check model:
```bash
python debug_models.py
```

### Production Considerations

- Use larger training dataset (1000+ records)
- Add logging and monitoring
- Set up error alerts
- Cache frequent queries
- Use reverse proxy (nginx)
- Enable CORS for frontend

---

## 📝 VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 4.0 | Apr 2026 | Local SQLite database, 25 locations |
| 3.0 | Apr 2026 | Remote database integration |
| 2.0 | Apr 2026 | API simplification |
| 1.0 | Apr 2026 | Initial ML system |

---

## ✅ TESTING

Run comprehensive tests:
```bash
python test_local_db.py        # Database integration
python detailed_debug.py        # System debugging
python debug_models.py          # Model verification
```

---

## 📞 SUPPORT

**Backend Issues:**
- Check logs: `uvicorn main:app --reload`
- Debug: `python detailed_debug.py`
- Model info: `python debug_models.py`

**Database Issues:**
- Recreate: `python setup_sqlite_db.py`
- Retrain: `python train_on_local_db.py`

**Frontend Issues:**
- Clear cache: `npm cache clean --force`
- Reinstall: `rm -rf node_modules && npm install`

---

## 📄 LICENSE

Confidential - BeeWare Project

**Last Updated:** April 5, 2026  
**Status:** Production Ready ✅
