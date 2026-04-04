import sys
import os
from risk_model import BeeWareRiskModel


def main():
    excel_path = "lucknow_10k_ml_dataset.xlsx"
    model_path = "beeware_model.pkl"
    
    if len(sys.argv) > 1:
        excel_path = sys.argv[1]
    if len(sys.argv) > 2:
        model_path = sys.argv[2]
    
    if not os.path.exists(excel_path):
        print(f"Error: Excel file not found at {excel_path}")
        print(f"Expected location: {os.path.abspath(excel_path)}")
        sys.exit(1)
    
    print("Starting model training...\n")
    
    model = BeeWareRiskModel()
    model.train_from_excel(excel_path)
    
    print(f"\nSaving model to {model_path}...")
    model.save(model_path)
    print("Model saved successfully!\n")
    
    print("Testing model predictions:\n")
    test_cases = [
        ([0.2, 0.5, 0.7, 0.8], "Safe area: Low crime, good visibility"),
        ([0.8, 0.3, 0.4, 0.2], "Risky area: High crime, bad visibility"),
        ([0.5, 0.6, 0.6, 0.6], "Moderate area: Average conditions"),
        ([0.3, 0.7, 0.5, 0.7], "Protected area: Low crime, good lighting"),
        ([0.9, 0.4, 0.3, 0.1], "Dangerous area: High crime, low visibility"),
    ]
    
    for i, (features, description) in enumerate(test_cases, 1):
        result = model.predict_segment(features)
        print(f"   Test {i}: {description}")
        print(f"      Safety Score: {result['safety_score']:.2f}/100")
        print(f"      Label: {result['label']} ({result['color']})")
        print(f"      Confidence: {result['confidence']:.1%}")
        if result['explanation']:
            print(f"      Key factors: {', '.join(result['explanation'][:3])}")
        print()
    
    print("Model training and testing completed!")


if __name__ == "__main__":
    main()
