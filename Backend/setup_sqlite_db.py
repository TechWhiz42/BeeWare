import sqlite3
import os

db_path = "crime_local.db"

# Remove existing database if it exists
if os.path.exists(db_path):
    os.remove(db_path)

connection = sqlite3.connect(db_path)
cursor = connection.cursor()

print("Creating database schema...")

# Create areas table
cursor.execute('''
CREATE TABLE areas (
    id INTEGER PRIMARY KEY,
    area_name TEXT
)
''')

# Create area_features table
cursor.execute('''
CREATE TABLE area_features (
    id INTEGER PRIMARY KEY,
    area_id INTEGER,
    latitude REAL,
    longitude REAL,
    population_density INTEGER,
    night_light_intensity REAL,
    crime_score REAL,
    road_density REAL,
    risk_score REAL
)
''')

# Create area_crime_summary table
cursor.execute('''
CREATE TABLE area_crime_summary (
    id INTEGER PRIMARY KEY,
    total_crimes INTEGER,
    area_id INTEGER
)
''')

print("Inserting areas data...")
areas_data = [
    (3, 'Alambagh'),
    (23, 'Aliganj'),
    (9, 'Aminabad'),
    (13, 'Ashiyana'),
    (6, 'Charbagh'),
    (20, 'Chinhat'),
    (5, 'Chowk'),
    (17, 'Eldeco'),
    (1, 'Gomti Nagar'),
    (4, 'Hazratganj'),
    (2, 'Indira Nagar'),
    (10, 'Jankipuram'),
    (12, 'Kaiserbagh'),
    (21, 'Kapoorthala'),
    (24, 'Kursi Road'),
    (22, 'Lalbagh'),
    (7, 'Mahanagar'),
    (15, 'Naka Hindola'),
    (16, 'Nishatganj'),
    (8, 'Rajajipuram'),
    (18, 'Sitapur Road'),
    (25, 'Talkatora'),
    (14, 'Telibagh'),
    (19, 'Thakurganj'),
    (11, 'Vikas Nagar'),
]

cursor.executemany('INSERT INTO areas VALUES (?, ?)', areas_data)

print("Inserting area_crime_summary data...")
crimes_data = [
    (1, 12456, 3),
    (2, 12227, 9),
    (3, 13151, 13),
    (4, 12593, 6),
    (5, 12644, 5),
    (6, 12006, 1),
    (7, 12707, 4),
    (8, 12497, 2),
    (9, 13289, 10),
    (10, 12237, 12),
    (11, 11626, 7),
    (12, 12062, 15),
    (13, 12751, 8),
    (14, 11798, 14),
    (15, 12681, 11),
]

cursor.executemany('INSERT INTO area_crime_summary VALUES (?, ?, ?)', crimes_data)

print("Inserting area_features data...")
features_data = [
    (1, 1, 26.84300148985731, 80.98462104315811, 9792, 57, 0.383, 0.727, 0.4244),
    (2, 16, 26.86025165371409, 80.94109795981309, 13841, 52, 0.341, 0.756, 0.4657),
    (3, 17, 26.84864616449397, 80.96663489401298, 14188, 73, 0.513, 0.613, 0.5258),
    (4, 18, 26.90138077109849, 80.93517408474808, 12095, 87, 0.542, 0.607, 0.4827),
    (5, 4, 26.84592561987685, 80.93448597339595, 10535, 99, 0.308, 0.643, 0.3371),
    (6, 16, 26.85307425493517, 80.94462548325349, 13170, 98, 0.479, 0.758, 0.4196),
    (7, 6, 26.8359296394918, 80.91461310699484, 14584, 92, 0.533, 0.572, 0.5093),
    (8, 17, 26.8430854662751, 80.97842836201886, 12175, 70, 0.363, 0.645, 0.4385),
    (9, 3, 26.81251214065734, 80.89146393196096, 14209, 80, 0.458, 0.692, 0.4743),
    (10, 1, 26.84626769307363, 80.98492771310008, 11609, 81, 0.316, 0.658, 0.3876),
    (11, 4, 26.84880898151758, 80.93737117185039, 12924, 68, 0.547, 0.514, 0.5523),
    (12, 6, 26.83105263080397, 80.91348659334449, 10352, 93, 0.579, 0.685, 0.4466),
    (13, 4, 26.84884064939008, 80.9499353749364, 10163, 57, 0.201, 0.6, 0.3819),
    (14, 16, 26.86945043205412, 80.94158514044594, 10760, 66, 0.344, 0.74, 0.4011),
    (15, 8, 26.83018097934397, 80.90611801008527, 12629, 70, 0.202, 0.668, 0.3756),
    (16, 3, 26.81518731686804, 80.89998775941459, 12642, 80, 0.296, 0.715, 0.384),
    (17, 3, 26.8122178716272, 80.90400186217536, 13487, 98, 0.39, 0.896, 0.3606),
    (18, 7, 26.87180617969155, 80.94179737687222, 8650, 68, 0.4, 0.519, 0.4355),
    (19, 10, 26.89509484892621, 80.92688743574084, 11585, 75, 0.206, 0.559, 0.3751),
    (20, 1, 26.85334213238928, 80.98260960429027, 12380, 55, 0.403, 0.576, 0.5011),
    (21, 13, 26.79530802361026, 80.92058830420575, 13625, 61, 0.391, 0.872, 0.4417),
    (22, 13, 26.79138737264976, 80.91801773218455, 8208, 94, 0.482, 0.572, 0.3998),
    (23, 16, 26.86768895484083, 80.95645455978907, 8560, 75, 0.226, 0.831, 0.2883),
    (24, 19, 26.84098669629269, 80.90996042121405, 14732, 67, 0.529, 0.816, 0.5108),
    (25, 20, 26.87645872301801, 80.99281498090603, 8716, 91, 0.38, 0.791, 0.328),
]

cursor.executemany('INSERT INTO area_features VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', features_data)

connection.commit()
print(f"Database created successfully at {db_path}")

# Verify data
cursor.execute('SELECT COUNT(*) FROM area_features')
count = cursor.fetchone()[0]
print(f"Total feature records: {count}")

connection.close()
