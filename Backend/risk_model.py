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
    "crime_density_norm",
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
        """Train model from CSV dataset."""
        df = pd.read_csv(csv_path)

        if not all(col in df.columns for col in FEATURE_NAMES):
            missing = [f for f in FEATURE_NAMES if f not in df.columns]
            raise ValueError(f"Dataset missing required features: {missing}")

        if "label" not in df.columns:
            raise ValueError("Dataset must contain 'label' column")

        n_rows = len(df)
        if n_rows < 1000:
            print(f"WARNING: Dataset has {n_rows} rows (recommended >= 1000)")

        X = df[FEATURE_NAMES].values
        y = df["label"].values

        if np.isnan(X).any():
            raise ValueError("Dataset contains NaN values")

        if not (np.all(X >= 0) and np.all(X <= 1)):
            raise ValueError("All feature values must be normalized between 0 and 1")

        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=0.2,
            stratify=y,
            random_state=42
        )

        self.model = self.build_pipeline()
        self.model.fit(X_train, y_train)

        y_proba = self.model.predict_proba(X_test)
        auc = roc_auc_score(y_test, y_proba, multi_class="ovr")

        if auc > 0.98:
            print(f"WARNING: AUC {auc:.4f} > 0.98 (possible overfitting)")

        unique, counts = np.unique(y, return_counts=True)
        max_class = counts.max()
        min_class = counts.min()
        imbalance_ratio = max_class / min_class
        if imbalance_ratio > 2.0:
            print(f"WARNING: Class imbalance ratio {imbalance_ratio:.2f} (max/min: {max_class}/{min_class})")

        self.training_metrics = {
            "auc": round(auc, 4),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "n_features": X.shape[1],
            "dataset_source": "csv"
        }

        self.is_trained = True
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
        """Predict risk for a segment."""
        if not self.is_trained:
            raise ValueError("Model not trained")

        if len(features) != len(FEATURE_NAMES):
            raise ValueError(f"Feature vector must have {len(FEATURE_NAMES)} values")

        crime_density_idx = FEATURE_NAMES.index("crime_density_norm")
        crime_density = features[crime_density_idx]
        
        assert 0.0 <= crime_density <= 1.0, \
            f"Feature vector crime_density_norm {crime_density} not in valid range [0, 1]"
        
        x = features.reshape(1, -1)
        pred = int(self.model.predict(x)[0])
        probas = self.model.predict_proba(x)[0]
        
        p_safe = probas[0]
        p_caution = probas[1]
        p_high_risk = probas[2]
        
        base_risk = (p_caution * 0.4) + (p_high_risk * 1.0)
        crime_penalty = crime_density * 0.7
        final_risk = min(1.0, base_risk + crime_penalty)
        safety_score = (1.0 - final_risk) * 100
        
        label = ["Safe", "Caution", "High Risk"][pred]
        color = ["#22c55e", "#f59e0b", "#ef4444"][pred]

        return {
            "risk_class": pred,
            "label": label,
            "color": color,
            "safety_score": float(safety_score),
            "probability_safe": float(p_safe),
            "probability_caution": float(p_caution),
            "probability_high_risk": float(p_high_risk),
            "crime_density_norm": float(crime_density),
            "model_metrics": self.training_metrics
        }
