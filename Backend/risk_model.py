import pickle
import numpy as np
import pandas as pd
import warnings
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

warnings.filterwarnings('ignore')

FEATURE_NAMES = [
    "crime_score",
    "population_density_norm",
    "road_density",
    "night_light_intensity_norm",
]


class BeeWareRiskModel:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.training_metrics = {}
        self.feature_names = FEATURE_NAMES
        self.normalization_params = {}

    def train_from_excel(self, excel_file_path):
        print("\nTraining ML model from Excel dataset\n" + "="*50 + "\n")
        
        print(f"Reading Excel file: {excel_file_path}")
        
        try:
            df = pd.read_excel(excel_file_path)
            print(f"Successfully loaded {len(df)} records\n")
            
            print(f"Dataset columns: {list(df.columns)}\n")
            
            required_cols = ['crime_score', 'population_density', 'road_density', 
                           'night_light_intensity', 'risk_score']
            missing = [col for col in required_cols if col not in df.columns]
            if missing:
                raise ValueError(f"Missing columns: {missing}")
            
            print("Dataset statistics:")
            print(f"   Crime Score           - Min: {df['crime_score'].min():.3f}, Max: {df['crime_score'].max():.3f}, Mean: {df['crime_score'].mean():.3f}")
            print(f"   Population Density    - Min: {df['population_density'].min():.0f}, Max: {df['population_density'].max():.0f}, Mean: {df['population_density'].mean():.0f}")
            print(f"   Road Density          - Min: {df['road_density'].min():.3f}, Max: {df['road_density'].max():.3f}, Mean: {df['road_density'].mean():.3f}")
            print(f"   Night Light Intensity - Min: {df['night_light_intensity'].min():.0f}, Max: {df['night_light_intensity'].max():.0f}, Mean: {df['night_light_intensity'].mean():.0f}")
            print(f"   Risk Score (Target)   - Min: {df['risk_score'].min():.3f}, Max: {df['risk_score'].max():.3f}, Mean: {df['risk_score'].mean():.3f}\n")
            
            self.normalization_params = {
                'pop_density_min': df['population_density'].min(),
                'pop_density_max': df['population_density'].max(),
                'night_light_min': df['night_light_intensity'].min(),
                'night_light_max': df['night_light_intensity'].max(),
            }
            
            df['population_density_norm'] = (
                (df['population_density'] - self.normalization_params['pop_density_min']) / 
                (self.normalization_params['pop_density_max'] - self.normalization_params['pop_density_min'] + 1e-8)
            )
            df['night_light_intensity_norm'] = (
                (df['night_light_intensity'] - self.normalization_params['night_light_min']) / 
                (self.normalization_params['night_light_max'] - self.normalization_params['night_light_min'] + 1e-8)
            )
            
            # Prepare features and target
            X = df[[
                'crime_score',
                'population_density_norm',
                'road_density',
                'night_light_intensity_norm'
            ]].values
            y = df['risk_score'].values
            
            print(f"Feature matrix shape: {X.shape}")
            print(f"Target vector shape: {y.shape}\n")
            
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            print(f"Data split:")
            print(f"   Training samples: {len(X_train)}")
            print(f"   Test samples: {len(X_test)}\n")
            
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            print(f"Training RandomForest model...")
            print(f"   Estimators: 200")
            print(f"   Max depth: 20")
            print(f"   Min samples split: 10")
            print(f"   Min samples leaf: 4\n")
            
            self.model = RandomForestRegressor(
                n_estimators=200,
                max_depth=20,
                min_samples_split=10,
                min_samples_leaf=4,
                random_state=42,
                n_jobs=-1,
                verbose=0
            )
            self.model.fit(X_train_scaled, y_train)
            
            print(f"Model evaluation:")
            y_train_pred = self.model.predict(X_train_scaled)
            y_test_pred = self.model.predict(X_test_scaled)
            
            train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
            test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
            train_r2 = r2_score(y_train, y_train_pred)
            test_r2 = r2_score(y_test, y_test_pred)
            train_mae = mean_absolute_error(y_train, y_train_pred)
            test_mae = mean_absolute_error(y_test, y_test_pred)
            
            self.training_metrics = {
                'train_rmse': float(train_rmse),
                'test_rmse': float(test_rmse),
                'train_r2': float(train_r2),
                'test_r2': float(test_r2),
                'train_mae': float(train_mae),
                'test_mae': float(test_mae),
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'total_samples': len(X),
            }
            
            print(f"   Train RMSE: {train_rmse:.4f}")
            print(f"   Test RMSE:  {test_rmse:.4f}")
            print(f"   Train R2:   {train_r2:.4f}")
            print(f"   Test R2:    {test_r2:.4f}")
            print(f"   Train MAE:  {train_mae:.4f}")
            print(f"   Test MAE:   {test_mae:.4f}\n")
            
            print(f"Feature importance ranking:")
            importance = self.model.feature_importances_
            sorted_idx = np.argsort(importance)[::-1]
            for idx in sorted_idx:
                print(f"   {self.feature_names[idx]:30s} - {importance[idx]:.4f}")
            
            self.is_trained = True
            
            print("\nModel training completed successfully!" + "\n")
            return self
            
        except Exception as e:
            print(f"Error during training: {e}")
            raise

    def load(self, path="beeware_model.pkl"):
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
            self.model = data.get('model')
            self.scaler = data.get('scaler')
            self.training_metrics = data.get('metrics', {})
            self.feature_names = data.get('feature_names', self.feature_names)
            self.normalization_params = data.get('normalization_params', {})
            self.is_trained = data.get('is_trained', False)
            print(f"Model loaded from {path}")
            print(f"   Test R2 score: {self.training_metrics.get('test_r2', 'N/A')}")
            print(f"   Training samples: {self.training_metrics.get('total_samples', 'N/A')}")
            return self
        except FileNotFoundError:
            print(f"Model file not found: {path}")
            self.is_trained = False
            return self
        except Exception as e:
            print(f"Failed to load model: {e}")
            self.is_trained = False
            return self

    def predict_segment(self, features, timestamp: datetime = None, poi_boost: float = 0.0):
        """
        Predict risk score using trained ML model.
        Separates survivability (non-crime factors) from crime impact.
        
        Args:
            features: [crime_score, pop_density_norm, road_density, night_light_norm]
            timestamp: datetime object (for time-based context)
            poi_boost: Survivability boost from nearby police/hospitals (0-30 points)
        
        Returns:
            Dict with safety_score, survivability_score, crime_score, label, color, etc.
        """
        if not self.is_trained or self.model is None:
            raise RuntimeError("Model not trained. Call train_from_excel() first.")
        
        # Validate feature count
        if len(features) != 4:
            raise ValueError(f"Expected 4 features, got {len(features)}")
        
        # Validate feature ranges
        for i, f in enumerate(features):
            if not (0.0 <= f <= 1.0):
                raise ValueError(f"Feature '{self.feature_names[i]}' out of range [0,1]: {f}")
        
        crime_score = features[0]
        pop_density = features[1]
        road_density = features[2]
        visibility = features[3]
        
        # Prepare input for prediction
        X = np.array([features])
        X_scaled = self.scaler.transform(X)
        
        # Predict risk score using trained model (with crime)
        risk_score = float(self.model.predict(X_scaled)[0])
        risk_score = np.clip(risk_score, 0.0, 1.0)
        
        # Predict survivability score (with crime = 0, keeping other features)
        survivability_features = [0.0, pop_density, road_density, visibility]
        X_survivability = np.array([survivability_features])
        X_survivability_scaled = self.scaler.transform(X_survivability)
        survivability_risk = float(self.model.predict(X_survivability_scaled)[0])
        survivability_risk = np.clip(survivability_risk, 0.0, 1.0)
        
        # Convert risks to safety scores
        safety_score = 100.0 * (1.0 - risk_score)
        survivability_score = 100.0 * (1.0 - survivability_risk)
        
        # Crime score: impact on safety (how much crime reduces it)
        crime_impact_score = survivability_score - safety_score
        crime_impact_score = np.clip(crime_impact_score, 0.0, 100.0)
        
        # Handle timestamp for time-based adjustments
        if timestamp is None:
            timestamp = datetime.now()
        
        hour = timestamp.hour
        is_night = (hour >= 22 or hour < 6)
        is_rush_hour = (7 <= hour <= 10 or 18 <= hour <= 21)
        
        # Time-based adjustments
        if is_night:
            # Night (22:00-06:00): Reduce by 7% (less visibility, fewer people)
            safety_score *= 0.93
            survivability_score *= 0.93
        elif is_rush_hour:
            # Rush hour (07:00-10:00, 18:00-21:00): INCREASE by 5% (crowded = safer)
            # More people = more witnesses, more visibility, more help available
            safety_score *= 1.05
            survivability_score *= 1.05
        
        safety_score = np.clip(safety_score, 0.0, 100.0)
        survivability_score = np.clip(survivability_score, 0.0, 100.0)
        crime_impact_score = np.clip(crime_impact_score, 0.0, 100.0)
        
        # Apply POI boost to survivability (police stations and hospitals nearby)
        if poi_boost > 0.0:
            survivability_score = min(100.0, survivability_score + poi_boost)
            # Also slightly boost safety score (but less than survivability)
            safety_score = min(100.0, safety_score + poi_boost * 0.5)
        
        # Determine label and color
        if safety_score >= 70:
            label = "Safe"
            color = "#22c55e"
            risk_class = 0
        elif safety_score >= 45:
            label = "Caution"
            color = "#f59e0b"
            risk_class = 1
        else:
            label = "High Risk"
            color = "#ef4444"
            risk_class = 2
        
        # Calculate confidence
        extremity = max(
            abs(crime_score - 0.5) * 2,
            abs(visibility - 0.5) * 2,
            abs(road_density - 0.5) * 2
        )
        confidence = float(min(0.99, 0.6 + extremity * 0.39))
        
        # Build explanation
        explanation = self._build_explanation(
            crime_score, pop_density, road_density, visibility, 
            safety_score, is_night, is_rush_hour
        )
        
        # Calculate probability distribution based on safety score
        if safety_score >= 70:
            prob_safe = (safety_score - 70) / 30 + 0.4  # 0.4 to 1.0
            prob_caution = 1.0 - prob_safe
            prob_high_risk = 0.0
        elif safety_score >= 45:
            prob_caution = (safety_score - 45) / 25 + 0.4
            prob_safe = (safety_score - 45) / 25 * 0.5
            prob_high_risk = 1.0 - prob_caution - prob_safe
        else:
            prob_high_risk = (45 - safety_score) / 45 + 0.5
            prob_caution = 1.0 - prob_high_risk
            prob_safe = 0.0
        
        return {
            "risk_class": risk_class,
            "label": label,
            "color": color,
            "safety_score": float(safety_score),
            "survivability_score": float(survivability_score),
            "crime_impact_score": float(crime_impact_score),
            "confidence": confidence,
            "explanation": explanation,
            "crime_density": float(crime_score),
            "timestamp": timestamp.isoformat() if timestamp else None,
            "probability_safe": max(0.0, min(1.0, float(prob_safe))),
            "probability_caution": max(0.0, min(1.0, float(prob_caution))),
            "probability_high_risk": max(0.0, min(1.0, float(prob_high_risk))),
        }

    def _build_explanation(self, crime, pop_density, road_density, visibility,
                          safety_score, is_night, is_rush_hour):
        """Build human-readable explanation incorporating all features."""
        factors = []
        
        # Crime assessment
        if crime > 0.7:
            factors.append("High crime area - significant risk")
        elif crime > 0.4:
            factors.append("Moderate crime - standard precautions")
        else:
            factors.append("Low crime area - generally safe")
        
        # Environmental assessment
        if visibility < 0.3:
            factors.append("Low visibility - increased risk")
        elif visibility > 0.7:
            factors.append("Good lighting and visibility")
        
        if road_density > 0.7:
            factors.append("Well-connected roads improve safety")
        elif road_density < 0.3:
            factors.append("Poor road connectivity")
        
        # Population density
        if pop_density > 0.7:
            factors.append("Crowded area - more witnesses/help available")
        elif pop_density < 0.3:
            factors.append("Sparse area - limited nearby support")
        
        # Time-based
        if is_night:
            factors.append("Night time - reduce travel if possible")
        
        if is_rush_hour:
            factors.append("Rush hour - congested but active")
        
        # Default if no factors
        if not factors:
            if safety_score >= 75:
                factors.append("Overall safe area")
            elif safety_score >= 50:
                factors.append("Exercise caution")
            else:
                factors.append("High risk - avoid if possible")
        
        return factors

    def save(self, path="beeware_model.pkl"):
        """Save trained model, scaler, and metadata."""
        data = {
            'model': self.model,
            'scaler': self.scaler,
            'metrics': self.training_metrics,
            'feature_names': self.feature_names,
            'normalization_params': self.normalization_params,
            'is_trained': self.is_trained,
        }
        with open(path, 'wb') as f:
            pickle.dump(data, f)
        print(f"✅ Model saved to {path}")
        return self