import sys
from risk_model import BeeWareRiskModel


def main():
    """Train model from CSV dataset only."""
    if len(sys.argv) < 2:
        raise ValueError("Usage: python train_model.py <path_to_dataset.csv>")
    
    csv_path = sys.argv[1]
    model = BeeWareRiskModel()
    model.train_from_csv(csv_path)
    model.save("beeware_model.pkl")


if __name__ == "__main__":
    main()
