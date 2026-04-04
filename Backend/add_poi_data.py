import sqlite3

conn = sqlite3.connect('crime_local.db')
cursor = conn.cursor()

print("Adding sample POI data (police stations and hospitals)...")

# Add some sample data
poi_data = [
    (26.8467, 80.9462, 0, 'Police Station - Gomti Nagar', 2.0),
    (26.9124, 80.9055, 1, 'Hospital - Lucknow', 1.5),
    (26.8829, 80.9597, 0, 'Police Station - Aliganj', 2.0),
]

cursor.executemany('''
    INSERT INTO points_of_interest (latitude, longitude, poi_type, name, distance_influence_km) 
    VALUES (?, ?, ?, ?, ?)
''', poi_data)

conn.commit()

print("✓ Added sample POI entries")

# Verify
cursor.execute("SELECT COUNT(*) FROM points_of_interest;")
count = cursor.fetchone()[0]
print(f"✓ Total POI records: {count}")

conn.close()
