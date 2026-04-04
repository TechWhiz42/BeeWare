#!/usr/bin/env python3
"""Test the location endpoint."""

import logging
logging.basicConfig(level=logging.WARNING)

from main import app
from fastapi.testclient import TestClient
from datetime import datetime

client = TestClient(app)

print("=" * 80)
print("Testing Location Endpoint")
print("=" * 80)

# Test single location
location_data = {
    "latitude": 26.8,
    "longitude": 80.85,
    "timestamp": "2024-04-04T14:30:00"
}

print("\nTesting /location/safety endpoint:")
response = client.post('/location/safety', json=location_data)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"Safety Score: {data['safety_score']}")
    print(f"Label: {data['label']}")
else:
    print(f"Error: {response.text}")

# Test bulk locations
print("\n" + "=" * 80)
print("Testing /locations/safety/bulk endpoint:")

bulk_data = {
    "locations": [
        {"latitude": 26.8, "longitude": 80.85, "timestamp": "2024-04-04T14:30:00"},
        {"latitude": 27.15, "longitude": 80.68, "timestamp": "2024-04-04T14:30:00"},
        {"latitude": 26.63, "longitude": 80.9, "timestamp": "2024-04-04T14:30:00"},
    ]
}

response = client.post('/locations/safety/bulk', json=bulk_data)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"Total Locations: {data['count']}")
    print("Scores:")
    for result in data['results']:
        print(f"  ({result['latitude']}, {result['longitude']}): {result['safety_score']} ({result['label']})")
else:
    print(f"Error: {response.text}")

print("=" * 80)
