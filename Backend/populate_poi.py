import sqlite3

conn = sqlite3.connect('crime_local.db')
cursor = conn.cursor()

print("Clearing existing POI data...")
cursor.execute("DELETE FROM points_of_interest")

print("Inserting complete POI data (police stations and hospitals)...")

# POI data: (latitude, longitude, type, name, distance_influence_km)
# type: 0 = Police Station, 1 = Hospital
pois_data = [
    # Police Stations in Lucknow
    (26.8469, 80.9460, 0, "Gomti Nagar Police Station", 2.0),
    (26.8361, 80.9146, 0, "Charbagh Police Station", 2.0),
    (26.8631, 80.9355, 0, "Nishatganj Police Station", 2.0),
    (26.8660, 80.9215, 0, "Indira Nagar Police Station", 2.0),
    (26.8398, 80.9075, 0, "Aminabad Police Station", 2.0),
    
    # Hospitals in Lucknow
    (26.8460, 80.9450, 1, "Lucknow Medical College Hospital", 2.0),
    (26.8640, 80.9340, 1, "Sahara Hospital", 2.0),
    (26.8370, 80.9150, 1, "Balrampur Hospital", 2.0),
    (26.8500, 80.9200, 1, "KGMU Medical University Hospital", 2.0),
    (26.8300, 80.9000, 1, "City Nursing Home", 2.0),
]

cursor.executemany('INSERT INTO points_of_interest (latitude, longitude, poi_type, name, distance_influence_km) VALUES (?, ?, ?, ?, ?)', pois_data)

conn.commit()

# Verify
cursor.execute("SELECT COUNT(*) FROM points_of_interest")
count = cursor.fetchone()[0]
print(f"✓ Total POI records now: {count}")

cursor.execute("SELECT COUNT(*) FROM points_of_interest WHERE poi_type = 0")
police_count = cursor.fetchone()[0]
print(f"  - Police Stations: {police_count}")

cursor.execute("SELECT COUNT(*) FROM points_of_interest WHERE poi_type = 1")
hospital_count = cursor.fetchone()[0]
print(f"  - Hospitals: {hospital_count}")

conn.close()
