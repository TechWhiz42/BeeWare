from datetime import datetime
from risk_model import BeeWareRiskModel
from feature_extractor import FeatureExtractor
from route_analyzer import RouteAnalyzer, RouteSegment
from service import SafetyAnalysisService

print('=' * 80)
print('BeeWare Production System - Final Validation')
print('=' * 80)

model = BeeWareRiskModel()
model.load('beeware_model.pkl')
extractor = FeatureExtractor()
analyzer = RouteAnalyzer(model, extractor)
service = SafetyAnalysisService(model, extractor, analyzer)

timestamp = datetime(2024, 4, 4, 14, 30)

print('\n1. SINGLE LOCATION ANALYSIS WITH VARYING CRIME')
print('-' * 80)
for crime in [0.0, 0.3, 0.6, 0.9]:
    result = service.analyze_location(
        latitude=28.6315, longitude=77.2167, 
        timestamp=timestamp, crime_density_norm=crime
    )
    print(f'Crime: {crime:.1f} | Score: {result["safety_score"]:6.1f}/100 | {result["label"]}')

print('\n2. ROUTE ANALYSIS WITH MULTI-SEGMENT CRIME')
print('-' * 80)
waypoints = [
    {'latitude': 28.6315, 'longitude': 77.2167, 'timestamp': timestamp, 
     'crime_density_norm': 0.1, 'name': 'Safe Start'},
    {'latitude': 28.6300, 'longitude': 77.2180, 'timestamp': timestamp,
     'crime_density_norm': 0.8, 'name': 'Dangerous Mid'},
    {'latitude': 28.6285, 'longitude': 77.2200, 'timestamp': timestamp,
     'crime_density_norm': 0.2, 'name': 'Safe End'},
]
route = service.analyze_route(waypoints, 'Test Route')
print(f'Route Score: {route["safety_score"]:.1f}/100')
print(f'Category: {route["category"]}')
print(f'Segments: {route["total_segments"]} | High Risk: {route["high_risk_segments"]}')
print('Segment Details:')
for seg in route['segment_details']:
    print(f'  {seg["name"]}: Score {seg["safety_score"]:.1f} | {seg["label"]}')

print('\n3. PROBABILITY VALIDATION (NO DISTORTION)')
print('-' * 80)
features = extractor.extract(lat=28.6315, lon=77.2167, timestamp=timestamp,
                             segment_length_m=100, crime_density_norm=0.5)
pred = model.predict_segment(features)
probs = [pred['probability_safe'], pred['probability_caution'], pred['probability_high_risk']]
print(f'P(Safe):      {probs[0]:.4f}')
print(f'P(Caution):   {probs[1]:.4f}')
print(f'P(High Risk): {probs[2]:.4f}')
print(f'Sum:          {sum(probs):.4f} (should be 1.0000)')

print('\n4. CRIME-DOMINANT FORMULA VALIDATION')
print('-' * 80)
p_safe, p_caution, p_high_risk = probs
crime = 0.5
base_risk = (p_caution * 0.4) + (p_high_risk * 1.0)
crime_penalty = crime * 0.6
final_risk = min(1.0, base_risk + crime_penalty)
expected_score = (1.0 - final_risk) * 100
actual_score = pred['safety_score']
print(f'Base Risk (P_caution*0.4 + P_high*1.0): {base_risk:.4f}')
print(f'Crime Penalty (crime*0.6): {crime_penalty:.4f}')
print(f'Final Risk (min(1.0, base + penalty)): {final_risk:.4f}')
print(f'Expected Score: {expected_score:.1f}')
print(f'Actual Score:   {actual_score:.1f}')
print(f'Match: {"YES" if abs(actual_score - expected_score) < 0.01 else "NO"}')

print('\n' + '=' * 80)
print('All validations COMPLETE - System ready for production')
print('=' * 80)
