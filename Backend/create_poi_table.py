import sqlite3

conn = sqlite3.connect('crime_local.db')
cursor = conn.cursor()

print("Creating points_of_interest table...")

# Create points_of_interest table
cursor.execute('''
CREATE TABLE points_of_interest (
    id INTEGER PRIMARY KEY,
    latitude REAL,
    longitude REAL,
    poi_type INTEGER,
    name TEXT,
    distance_influence_km REAL
)
''')

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

print("✓ points_of_interest table created successfully")
print(f"✓ Added {len(poi_data)} sample POI entries")

conn.close()
