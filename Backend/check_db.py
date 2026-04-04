import sqlite3

conn = sqlite3.connect('crime_local.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("Tables in database:")
for table in tables:
    print(f"  - {table[0]}")
    
# Check specifically for points_of_interest
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='points_of_interest';")
poi_exists = cursor.fetchone()

if poi_exists:
    print("\n✓ points_of_interest table exists")
else:
    print("\n✗ points_of_interest table MISSING")

conn.close()
