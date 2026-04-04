import pickle
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import roc_auc_score
from sklearn.calibration import CalibratedClassifierCV


FEATURE_NAMES = [
    "crime_density",
    "population_density",
    "road_density",
    "visibility_score",
    "isolation_score",
    "activity_score",
    "env_risk",
]


class BeeWareRiskModel:
    def __init__(self):
        self.model = None
        self.is_trained = False
        self.training_metrics = {}

    def build_pipeline(self):
        """Build ML pipeline with standardization and calibration."""
        rf = RandomForestClassifier(
            n_estimators=150,
            max_depth=10,
            random_state=42,
            n_jobs=-1,
            class_weight="balanced",
        )

        calibrated = CalibratedClassifierCV(rf, method="isotonic", cv=3)

        return Pipeline([
            ("scaler", StandardScaler()),
            ("clf", calibrated)
        ])


    def train_from_csv(self, csv_path):
        """Train model from CSV dataset with improved validation."""
        from sklearn.model_selection import cross_val_score
        
        df = pd.read_csv(csv_path)

        if not all(col in df.columns for col in FEATURE_NAMES):
            missing = [f for f in FEATURE_NAMES if f not in df.columns]
            raise ValueError(f"Dataset missing required features: {missing}")

        if "label" not in df.columns:
            raise ValueError("Dataset must contain 'label' column")

        n_rows = len(df)
        if n_rows < 1000:
            print(f"⚠️  WARNING: Dataset has {n_rows} rows (recommended >= 1000)")
            print(f"   Small dataset may lead to overfitting")

        X = df[FEATURE_NAMES].values
        y = df["label"].values

        if np.isnan(X).any():
            raise ValueError("Dataset contains NaN values")

        if not (np.all(X >= 0) and np.all(X <= 1)):
            raise ValueError("All feature values must be normalized between 0 and 1")

        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=0.2,
            stratify=y,
            random_state=42
        )

        # Build and train pipeline
        self.model = self.build_pipeline()
        self.model.fit(X_train, y_train)

        # Evaluation on test set
        y_pred = self.model.predict(X_test)
        y_proba = self.model.predict_proba(X_test)
        
        from sklearn.metrics import classification_report, confusion_matrix
        auc = roc_auc_score(y_test, y_proba, multi_class="ovr")
        
        print(f"\n📊 Test Set Performance:")
        print(f"   AUC: {auc:.4f}")
        if auc > 0.98:
            print(f"   ⚠️  WARNING: AUC {auc:.4f} > 0.98 (possible overfitting)")

        # Cross-validation on full dataset
        print(f"\n🔄 Cross-Validation (5-fold on full dataset):")
        cv_scores = cross_val_score(
            self.build_pipeline(), X, y, 
            cv=5, scoring='roc_auc_ovr', n_jobs=-1
        )
        print(f"   Fold scores: {[round(s, 4) for s in cv_scores]}")
        print(f"   Mean: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
        if cv_scores.std() > 0.15:
            print(f"   ⚠️  WARNING: High variance across folds (possible instability)")

        # Class balance
        unique, counts = np.unique(y, return_counts=True)
        max_class = counts.max()
        min_class = counts.min()
        imbalance_ratio = max_class / min_class
        if imbalance_ratio > 2.0:
            print(f"\n⚠️  WARNING: Class imbalance ratio {imbalance_ratio:.2f} (max/min: {max_class}/{min_class})")

        # Detailed classification report
        print(f"\n📋 Classification Report:")
        print(classification_report(y_test, y_pred, target_names=["Safe", "Caution", "High Risk"]))

        self.training_metrics = {
            "auc": round(auc, 4),
            "cv_mean_auc": round(cv_scores.mean(), 4),
            "cv_std_auc": round(cv_scores.std(), 4),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "n_features": X.shape[1],
            "dataset_source": "csv",
            "class_imbalance_ratio": round(imbalance_ratio, 2),
        }

        self.is_trained = True
        print(f"\n✅ Model trained and saved successfully")
        return self

    def save(self, path="beeware_model.pkl"):
        """Save trained model to disk."""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")

        with open(path, "wb") as f:
            pickle.dump({
                "model": self.model,
                "metrics": self.training_metrics,
                "feature_names": FEATURE_NAMES
            }, f)

    def load(self, path="beeware_model.pkl"):
        """Load trained model from disk."""
        with open(path, "rb") as f:
            data = pickle.load(f)

        self.model = data["model"]
        self.training_metrics = data.get("metrics", {})
        self.is_trained = True
        return self

    def predict_segment(self, features):
        """
        Predict risk for a segment using production-ready formula.
        
        Feature vector (7 features):
        0: crime_density
        1: population_density
        2: road_density
        3: visibility_score
        4: isolation_score
        5: activity_score
        6: env_risk
        """
        if not self.is_trained:
            raise ValueError("Model not trained")

        if len(features) != len(FEATURE_NAMES):
            raise ValueError(f"Feature vector must have {len(FEATURE_NAMES)} values, got {len(features)}")

        # Extract features by index
        crime_density = features[0]
        population_density = features[1]
        road_density = features[2]
        visibility_score = features[3]
        isolation_score = features[4]
        activity_score = features[5]
        env_risk = features[6]
        
        # Validation
        assert 0.0 <= crime_density <= 1.0, \
            f"crime_density {crime_density} not in valid range [0, 1]"
        assert np.all(features >= 0) and np.all(features <= 1), \
            f"Feature vector values out of range [0, 1]: {features}"
        
        x = features.reshape(1, -1)
        pred = int(self.model.predict(x)[0])
        probs = self.model.predict_proba(x)[0]
        
        # Extract probabilities for each class
        p_safe = probs[0]
        p_caution = probs[1]
        p_high_risk = probs[2]

        # === PRODUCTION-GRADE SAFETY SCORE FORMULA ===
        
        # Step 1: Model Risk (weighted probability)
        model_risk = (0.3 * p_caution) + (0.9 * p_high_risk)
        
        # Step 2: Crime Effect (non-linear amplification)
        crime_effect = crime_density ** 1.2
        
        # Step 3: Combine Risk (probabilistic fusion, no double counting)
        final_risk = 1 - (1 - model_risk) * (1 - crime_effect)
        
        # Step 4: Apply environmental risk modifier
        final_risk = final_risk + env_risk * (1 - final_risk)
        
        # Step 5: Convert to safety score
        final_risk = np.clip(final_risk, 0.0, 1.0)
        safety_score = 100 * (1 - (final_risk ** 0.85))
        safety_score = max(0.0, min(100.0, float(safety_score)))
        
        # Confidence Score: based on probability entropy
        # High entropy (uncertain) = low confidence
        # Low entropy (certain) = high confidence
        entropy = -np.sum(probs * np.log(probs + 1e-10))
        max_entropy = np.log(3)  # 3 classes
        confidence = float(1 - (entropy / max_entropy))
        confidence = max(0.0, min(1.0, confidence))
        
        # Build explanation from key factors
        explanation = self._build_explanation(
            safety_score=safety_score,
            crime_density=crime_density,
            visibility_score=visibility_score,
            isolation_score=isolation_score,
            activity_score=activity_score,
            env_risk=env_risk,
            p_high_risk=p_high_risk,
        )
        
        # Determine risk category
        label = ["Safe", "Caution", "High Risk"][pred]
        color = ["#22c55e", "#f59e0b", "#ef4444"][pred]

        return {
            "risk_class": pred,
            "label": label,
            "color": color,
            "safety_score": float(safety_score),
            "confidence": float(round(confidence, 3)),
            "explanation": explanation,
            "probability_safe": float(p_safe),
            "probability_caution": float(p_caution),
            "probability_high_risk": float(p_high_risk),
            "crime_density": float(crime_density),
            "model_metrics": self.training_metrics
        }
    
    def _build_explanation(self, 
                          safety_score: float,
                          crime_density: float,
                          visibility_score: float,
                          isolation_score: float,
                          activity_score: float,
                          env_risk: float,
                          p_high_risk: float) -> list:
        """
        Build human-readable explanation of risk factors.
        
        Returns list of strings explaining the safety assessment.
        """
        factors = []
        
        # Crime factor
        if crime_density > 0.80:
            factors.append("High crime area")
        elif crime_density > 0.60:
            factors.append("Moderate-high crime area")
        elif crime_density > 0.40:
            factors.append("Moderate crime area")
        
        # Visibility (lighting/night_light_intensity)
        if visibility_score < 0.30:
            factors.append("Low visibility (poor lighting)")
        elif visibility_score > 0.70:
            factors.append("Good visibility")
        
        # Isolation vs Urban activity
        if isolation_score > 0.70:
            factors.append("Isolated location")
        elif activity_score > 0.70:
            factors.append("High urban activity")
        
        # Environmental risk composite
        if env_risk > 0.70:
            factors.append("Unfavorable environmental conditions")
        elif env_risk < 0.30:
            factors.append("Favorable environmental conditions")
        
        # Model's high-risk prediction
        if p_high_risk > 0.60:
            factors.append("Model confidence: High risk")
        elif p_high_risk < 0.20:
            factors.append("Model confidence: Safe")
        
        # If no specific factors, add general assessment
        if not factors:
            if safety_score >= 75:
                factors.append("Safe area with favorable conditions")
            elif safety_score >= 50:
                factors.append("Standard caution advised")
            else:
                factors.append("Avoid if alternative routes available")
        
        return factors
