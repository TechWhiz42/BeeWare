#!/usr/bin/env python3
"""Test the route endpoint to see where 50s are coming from."""

import logging
logging.basicConfig(level=logging.DEBUG)

from main import app, analyzer
from fastapi.testclient import TestClient
from datetime import datetime

client = TestClient(app)

print("=" * 80)
print("Testing Route Endpoint")
print("=" * 80)

# Test with two waypoints in known areas
route_data = {
    "route_name": "Test Route",
    "waypoints": [
        {
            "latitude": 26.8,
            "longitude": 80.85,
            "timestamp": "2024-04-04T14:30:00",
            "name": "Area 1"
        },
        {
            "latitude": 27.15,
            "longitude": 80.68,
            "timestamp": "2024-04-04T14:45:00",
            "name": "Area 10"
        }
    ]
}

print("\nSending request:")
print(f"  Route: {route_data['route_name']}")
print(f"  Waypoints: {len(route_data['waypoints'])}")

response = client.post('/route/safety', json=route_data)

print(f"\nResponse Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"Safety Score: {data['safety_score']}")
    print(f"Category: {data['category']}")
    print(f"is_fallback: {data.get('is_fallback', False)}")
    
    if 'segment_details' in data:
        print(f"\nSegment Details:")
        for seg in data['segment_details']:
            print(f"  {seg['name']}: {seg['safety_score']} ({seg['label']})")
else:
    print(f"Error Response:")
    print(response.text)

print("\n" + "=" * 80)
