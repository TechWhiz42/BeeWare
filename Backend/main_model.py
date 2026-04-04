import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from risk_model import BeeWareRiskModel
from feature_extractor import FeatureExtractor
from route_analyzer import RouteAnalyzer, RouteSegment


class BeeWareSystem:
    """Route safety analysis system."""

    MODEL_PATH = "beeware_model.pkl"

    def __init__(self):
        self.model = BeeWareRiskModel()
        self.extractor = FeatureExtractor()
        self.analyzer = RouteAnalyzer(self.model, self.extractor)

    def train_from_csv(self, csv_path):
        """Train model from CSV dataset."""
        self.model.train_from_csv(csv_path)
        self.model.save(self.MODEL_PATH)
        return self

    def load(self):
        """Load a pre-trained model."""
        self.model.load(self.MODEL_PATH)
        return self

    def analyze_route(self,
                      coords: list[tuple[float, float]],
                      timestamp: datetime.datetime = None,
                      route_name: str = "Route") -> dict:
        """Analyze a route."""
        if not self.model.is_trained:
            raise ValueError("Model not trained. Call .train_from_csv() or .load() first.")

        segments = [
            RouteSegment(lat, lon, name=f"Point {i+1}")
            for i, (lat, lon) in enumerate(coords)
        ]
        
        analysis = self.analyzer.analyze_route(
            segments=segments,
            timestamp=timestamp,
        )

        return analysis.to_dict()

    def analyze_location(self,
                         lat: float,
                         lon: float,
                         timestamp: datetime.datetime = None,
                         crime_density_norm: float = 0.0) -> dict:
        """Analyze location safety."""
        if not self.model.is_trained:
            raise ValueError("Model not trained. Call .train_from_csv() or .load() first.")

        features = self.extractor.extract(
            lat=lat,
            lon=lon,
            timestamp=timestamp,
            segment_length_m=100.0,
            crime_density_norm=crime_density_norm,
        )
        
        result = self.model.predict_segment(features)
        return result


def main():
    """Entry point for model initialization."""
    system = BeeWareSystem()
    
    if os.path.exists(system.MODEL_PATH):
        system.load()


if __name__ == "__main__":
    main()

