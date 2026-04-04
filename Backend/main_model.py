import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from risk_model import BeeWareRiskModel
from feature_extractor import FeatureExtractor
from route_analyzer import RouteAnalyzer

# ─── Demo Route Definitions ────────────────────────────────────────────────────

DEMO_ROUTES = {
    "Delhi_Safe_Morning": {
        "description": "Connaught Place → India Gate (morning commute)",
        "timestamp": datetime.datetime(2024, 3, 15, 8, 30),
        "coords": [
            (28.6315, 77.2167), (28.6289, 77.2215), (28.6263, 77.2267),
            (28.6237, 77.2312), (28.6200, 77.2373),
        ],
        "road_types": ["primary", "secondary", "secondary", "tertiary", "primary"],
    },
    "Delhi_Risky_Night": {
        "description": "Nizamuddin → Lajpat Nagar (late night)",
        "timestamp": datetime.datetime(2024, 3, 15, 23, 45),
        "coords": [
            (28.5894, 77.2497), (28.5841, 77.2428), (28.5789, 77.2372),
            (28.5741, 77.2309), (28.5701, 77.2245),
        ],
        "road_types": ["residential", "service", "alley", "residential", "tertiary"],
    },
    "Mumbai_College_Evening": {
        "description": "Andheri Station → SVKM College (evening)",
        "timestamp": datetime.datetime(2024, 3, 15, 19, 15),
        "coords": [
            (19.1136, 72.8697), (19.1098, 72.8659), (19.1073, 72.8631),
            (19.1051, 72.8608), (19.1031, 72.8581),
        ],
        "road_types": ["secondary", "residential", "residential", "path", "secondary"],
    },
}


# ─── BeeWare System ────────────────────────────────────────────────────────────

class BeeWareSystem:
    """
    Provides train, analyze, and report capabilities.
    """

    MODEL_PATH = "beeware_model.pkl"

    def __init__(self, use_live_api: bool = False):
        self.model = BeeWareRiskModel()
        self.extractor = FeatureExtractor(use_live_api=use_live_api)
        self.analyzer = RouteAnalyzer(self.model, self.extractor)

    def train(self, n_samples: int = 50000, save: bool = True):
        """Train the ML model."""
        print("\n" + "="*60)
        print("🐝  BeeWare — Safety Intelligence System")
        print("="*60)
        self.model.train(n_samples=n_samples, verbose=True)
        if save:
            self.model.save(self.MODEL_PATH)
        return self

    def load(self):
        """Load a pre-trained model."""
        self.model.load(self.MODEL_PATH)
        return self

    def analyze_route(self,
                      coords: list[tuple[float, float]],
                      road_types: list[str] = None,
                      timestamp: datetime.datetime = None,
                      route_name: str = "Route") -> dict:
        """Analyze a route and return structured results."""
        if not self.model.is_trained:
            raise RuntimeError("Model not trained. Call .train() or .load() first.")

        print(f"\n📍 Analyzing: {route_name}")
        print(f"   Segments: {len(coords)} | Time: {timestamp or datetime.datetime.now()}")

        analysis = self.analyzer.analyze_coordinates(
            coords=coords,
            road_types=road_types,
            timestamp=timestamp,
        )

        self._print_analysis(analysis, route_name)
        return analysis.to_dict()

    def run_demos(self):
        """Run all built-in demo routes."""
        results = {}
        print("\n" + "─"*60)
        print("🗺️  Running Demo Route Analyses")
        print("─"*60)

        for name, route in DEMO_ROUTES.items():
            result = self.analyze_route(
                coords=route["coords"],
                road_types=route["road_types"],
                timestamp=route["timestamp"],
                route_name=f"{name}: {route['description']}",
            )
            results[name] = result

        return results

    def _print_analysis(self, analysis, name: str):
        """Pretty-print analysis results to console."""
        score = analysis.safety_score
        category = analysis.category
        color_map = {"Safe": "\033[92m", "Caution": "\033[93m", "Avoid": "\033[91m"}
        reset = "\033[0m"
        col = color_map.get(category, "")

        print(f"\n  {'─'*50}")
        print(f"  {col}Safety Score: {score}/100 — {category}{reset}")
        print(f"  {analysis.summary}")
        print(f"\n  📊 Segment Breakdown:")

        for seg in analysis.segments:
            seg_col = color_map.get(seg["label"], "")
            bar_len = int(seg["safety_score"] / 5)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            print(f"    [{seg['index']+1:2}] {seg_col}{bar}{reset} "
                  f"{seg['safety_score']:5.1f}  {seg['label']:<10} {seg['name']}")

        if analysis.high_risk_segments:
            print(f"\n  ⚠️  High Risk Segments ({len(analysis.high_risk_segments)}):")
            for hr in analysis.high_risk_segments:
                print(f"    • {hr['name']} (score: {hr['safety_score']:.1f})")

        print(f"\n  💡 Risk Factors Detected:")
        for seg in analysis.segments:
            pass  # Detailed explanations in segment results

        print(f"\n  📋 Recommendations:")
        for rec in analysis.recommendations:
            print(f"    • {rec}")

        print(f"\n  ⏱️  Analyzed in {analysis.processing_time_ms}ms")

    def export_report(self, results: dict, path: str = "beeware_report.json"):
        """Export analysis results to JSON."""
        with open(path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Report exported to {path}")

    def feature_importance_report(self):
        """Print feature importance ranking."""
        if not self.model.feature_importances_:
            print("Model not trained yet.")
            return

        print("\n" + "="*60)
        print("📊 BeeWare Feature Importance Report")
        print("="*60)
        sorted_features = sorted(
            self.model.feature_importances_.items(),
            key=lambda x: -x[1]
        )
        for rank, (name, importance) in enumerate(sorted_features, 1):
            bar = "█" * int(importance * 80)
            pct = importance * 100
            print(f"  {rank:2}. {name:<25} {bar:<16} {pct:.2f}%")


# ─── CLI / Main ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="BeeWare — Stay Aware. Stay Safe.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Full demo: train + analyze routes
  python main.py --train-only       # Train and save model
  python main.py --load-model       # Use saved model
  python main.py --samples 100000   # Train with more data
        """
    )
    parser.add_argument("--train-only", action="store_true")
    parser.add_argument("--load-model", action="store_true")
    parser.add_argument("--samples", type=int, default=50000)
    parser.add_argument("--live-api", action="store_true",
                        help="Use live Overpass API for feature extraction")
    parser.add_argument("--export", action="store_true",
                        help="Export results to JSON report")
    args = parser.parse_args()

    system = BeeWareSystem(use_live_api=args.live_api)

    # Train or load
    if args.load_model and os.path.exists(system.MODEL_PATH):
        system.load()
    else:
        system.train(n_samples=args.samples)

    if args.train_only:
        system.feature_importance_report()
        return

    # Run demos
    results = system.run_demos()
    system.feature_importance_report()

    # Export
    if args.export:
        system.export_report(results)

    print("\n" + "="*60)
    print("🐝 BeeWare analysis complete. Stay safe out there.")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
