import pickle
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from sklearn.calibration import CalibratedClassifierCV


FEATURE_NAMES = [
    "hour_sin",
    "hour_cos",
    "is_night",
    "is_rush_hour",
    "is_lit",
    "isolation_score",
    "poi_density_norm",
    "crowd_estimate",
    "police_proximity",
    "segment_length_norm",
]

RECOMMENDATIONS = {
    0: [
        "Route appears safe for travel at this time.",
        "Stay aware of your surroundings.",
        "Keep your phone charged and share your location.",
    ],
    1: [
        "Exercise heightened awareness.",
        "Prefer well-lit and busier routes.",
        "Travel with someone if possible.",
        "Keep emergency contacts ready.",
        "Enable live location sharing.",
    ],
    2: [
        "This location has significant safety concerns.",
        "Consider alternative routes or transport.",
        "Inform someone about your location and plans.",
        "Stay in well-lit and populated areas.",
        "Keep emergency numbers ready.",
        "Consider using verified cab services.",
    ],
}


class BeeWareRiskModel:
    def __init__(self):
        self.model = None
        self.is_trained = False
        self.training_metrics = {}

    def build_pipeline(self):
        rf = RandomForestClassifier(
            n_estimators=120,
            max_depth=8,
            random_state=42,
            n_jobs=-1
        )

        calibrated = CalibratedClassifierCV(rf, method="isotonic", cv=3)

        return Pipeline([
            ("scaler", StandardScaler()),
            ("clf", calibrated)
        ])

    def train(self, n_samples=50000, save=True):
        print(f"Generating {n_samples} training samples...")
        
        rng = np.random.default_rng(seed=42)
        X = np.zeros((n_samples, len(FEATURE_NAMES)))
        
        hours = rng.integers(0, 24, n_samples)
        hour_rad = 2 * np.pi * hours / 24
        
        X[:, 0] = np.sin(hour_rad)  # hour_sin
        X[:, 1] = np.cos(hour_rad)  # hour_cos
        X[:, 2] = ((hours >= 20) | (hours <= 5)).astype(float)  # is_night
        X[:, 3] = (((hours >= 7) & (hours <= 9)) | ((hours >= 17) & (hours <= 19))).astype(float)  # is_rush_hour
        
        X[:, 4] = np.clip(rng.normal(0.65, 0.3, n_samples), 0, 1)  # is_lit
        X[:, 5] = np.clip(rng.beta(2, 3, n_samples), 0, 1)  # isolation_score
        X[:, 6] = np.clip(rng.exponential(0.4, n_samples), 0, 1)  # poi_density_norm
        X[:, 7] = np.clip(rng.normal(0.4, 0.25, n_samples), 0, 1)  # crowd_estimate
        X[:, 8] = np.clip(rng.exponential(0.3, n_samples), 0, 1)  # police_proximity
        X[:, 9] = np.clip(rng.exponential(0.3, n_samples), 0, 1)  # segment_length_norm
        
        risk_score = (
            0.25 * X[:, 2] +
            0.18 * X[:, 5] +
            0.15 * X[:, 3] +
            0.10 * (1 - X[:, 4]) +
            0.12 * X[:, 8] -
            0.08 * X[:, 6] -
            0.05 * X[:, 7] +
            rng.normal(0, 0.05, n_samples)
        )
        
        risk_score = np.clip(risk_score, 0, 1)
        y = np.where(risk_score < 0.30, 0, np.where(risk_score < 0.55, 1, 2))
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, stratify=y, random_state=42
        )
        
        print("Training model...")
        self.model = self.build_pipeline()
        self.model.fit(X_train, y_train)
        
        y_proba = self.model.predict_proba(X_test)
        auc = roc_auc_score(y_test, y_proba, multi_class="ovr")
        
        self.training_metrics = {
            "auc": round(auc, 4),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "n_features": X.shape[1]
        }
        
        print(f"Training complete. AUC: {round(auc, 4)}")
        
        self.is_trained = True
        
        if save:
            self.save()
        
        return self

    def train_from_csv(self, csv_path):
        print("Loading dataset...")

        df = pd.read_csv(csv_path)

        if not all(col in df.columns for col in FEATURE_NAMES):
            raise Exception("Dataset missing required feature columns")

        if "label" not in df.columns:
            raise Exception("Dataset must contain 'label' column")

        X = df[FEATURE_NAMES].values
        y = df["label"].values

        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=0.2,
            stratify=y,
            random_state=42
        )

        print("Training model...")
        self.model = self.build_pipeline()
        self.model.fit(X_train, y_train)

        y_proba = self.model.predict_proba(X_test)
        auc = roc_auc_score(y_test, y_proba, multi_class="ovr")

        self.training_metrics = {
            "auc": round(auc, 4),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "n_features": X.shape[1]
        }

        print("Training complete")
        print("AUC:", round(auc, 4))

        self.is_trained = True

    def save(self, path="beeware_model.pkl"):
        if not self.is_trained:
            raise Exception("Cannot save untrained model")

        with open(path, "wb") as f:
            pickle.dump({
                "model": self.model,
                "metrics": self.training_metrics
            }, f)

        print(f"Model saved to {path}")

    def load(self, path="beeware_model.pkl"):
        with open(path, "rb") as f:
            data = pickle.load(f)

        self.model = data["model"]
        self.training_metrics = data.get("metrics", {})
        self.is_trained = True

        print(f"Model loaded from {path}")
        return self

    def predict_segment(self, features):
        if not self.is_trained:
            raise Exception("Model not trained")

        if len(features) != len(FEATURE_NAMES):
            raise Exception(f"Feature vector must have {len(FEATURE_NAMES)} values")

        x = features.reshape(1, -1)

        pred = int(self.model.predict(x)[0])
        probas = self.model.predict_proba(x)[0]

        safety_score = round(
            probas[0] * 100 +
            probas[1] * 50 +
            probas[2] * 0,
            1
        )

        label = ["Safe", "Caution", "High Risk"][pred]

        return {
            "risk_class": pred,
            "label": label,
            "color": ["#22c55e", "#f59e0b", "#ef4444"][pred],
            "safety_score": safety_score,
            "probability_safe": float(probas[0]),
            "probability_caution": float(probas[1]),
            "probability_high_risk": float(probas[2]),
            "recommendations": RECOMMENDATIONS[pred],
            "explanation": ["Model prediction based on learned patterns"],
            "model_metrics": self.training_metrics
        }