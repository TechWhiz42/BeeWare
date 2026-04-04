import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

print("\n" + "="*60)
print("Testing BeeWare Safety API")
print("="*60 + "\n")

# Test 1: Location Safety Check
print("Test 1: Location Safety Check")
print("-" * 60)
location_data = {
    "latitude": 26.8124,
    "longitude": 75.8863,
    "timestamp": datetime.now().isoformat()
}

try:
    response = requests.post(f"{BASE_URL}/location/safety", json=location_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

print("\n")

# Test 2: Route Safety Check
print("Test 2: Route Safety Check")
print("-" * 60)
route_data = {
    "waypoints": [
        {
            "latitude": 26.8124,
            "longitude": 75.8863,
            "timestamp": datetime.now().isoformat(),
            "name": "Start"
        },
        {
            "latitude": 26.8200,
            "longitude": 75.8950,
            "timestamp": datetime.now().isoformat(),
            "name": "Mid"
        },
        {
            "latitude": 26.8300,
            "longitude": 75.9000,
            "timestamp": datetime.now().isoformat(),
            "name": "End"
        }
    ],
    "route_name": "Downtown Route"
}

try:
    response = requests.post(f"{BASE_URL}/route/safety", json=route_data)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Route Name: {data.get('route_name')}")
    print(f"Safety Score: {data.get('safety_score')}/100")
    print(f"Category: {data.get('category')}")
    print(f"Segments: {data.get('total_segments')}")
except Exception as e:
    print(f"Error: {e}")

print("\n")

# Test 3: Multiple Locations Check
print("Test 3: Multiple Locations Check")
print("-" * 60)
bulk_data = {
    "locations": [
        {
            "latitude": 26.8124,
            "longitude": 75.8863,
            "timestamp": datetime.now().isoformat()
        },
        {
            "latitude": 26.9124,
            "longitude": 75.9863,
            "timestamp": datetime.now().isoformat()
        }
    ]
}

try:
    response = requests.post(f"{BASE_URL}/locations/safety/bulk", json=bulk_data)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Locations analyzed: {data.get('count')}")
    print(f"High risk count: {data.get('high_risk_count')}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*60)
print("Testing Complete")
print("="*60 + "\n")
