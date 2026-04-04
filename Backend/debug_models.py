import pickle
import os

print("="*80)
print("Debugging Model Files")
print("="*80 + "\n")

# Check original model
print("1. Original beeware_model.pkl")
print("-" * 80)
if os.path.exists("beeware_model.pkl"):
    with open("beeware_model.pkl", "rb") as f:
        try:
            data = pickle.load(f)
            print(f"   Type: {type(data)}")
            if isinstance(data, dict):
                print(f"   Keys: {data.keys()}")
                if "model" in data:
                    print(f"   Model type: {type(data['model'])}")
                    print(f"   Model n_estimators: {data['model'].n_estimators}")
            print(f"   ✓ File is valid")
        except Exception as e:
            print(f"   ✗ Error loading: {e}")
else:
    print("   ✗ File not found")

# Check local model
print("\n2. Local beeware_model_local.pkl")
print("-" * 80)
if os.path.exists("beeware_model_local.pkl"):
    with open("beeware_model_local.pkl", "rb") as f:
        try:
            data = pickle.load(f)
            print(f"   Type: {type(data)}")
            if isinstance(data, dict):
                print(f"   Keys: {data.keys()}")
                if "model" in data:
                    print(f"   Model type: {type(data['model'])}")
                    print(f"   Model n_estimators: {data['model'].n_estimators}")
            print(f"   ✓ File is valid")
        except Exception as e:
            print(f"   ✗ Error loading: {e}")
else:
    print("   ✗ File not found")

print("\n" + "="*80)
