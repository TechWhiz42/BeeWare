from sqlalchemy import create_engine, Column, Float, Integer
from sqlalchemy.orm import sessionmaker, declarative_base
import math
import os

db_file = os.path.join(os.path.dirname(__file__), "crime_local.db")
DATABASE_URL = f"sqlite:///{db_file}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class AreaFeature(Base):
    __tablename__ = "area_features"

    id = Column(Integer, primary_key=True)
    latitude = Column(Float)
    longitude = Column(Float)

    population_density = Column(Float)
    night_light_intensity = Column(Float)
    crime_score = Column(Float)
    road_density = Column(Float)
    risk_score = Column(Float)


class PointOfInterest(Base):
    """Police stations, hospitals, and other emergency services."""
    __tablename__ = "points_of_interest"

    id = Column(Integer, primary_key=True)
    latitude = Column(Float)
    longitude = Column(Float)
    poi_type = Column(Integer)  # 0: Police Station, 1: Hospital
    name = Column(Integer)  # Store as string representation
    distance_influence_km = Column(Float, default=2.0)  # Influence radius


# -------------------------
# DISTANCE FUNCTION
# -------------------------

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(d_lat / 2) ** 2 +
        math.cos(math.radians(lat1)) *
        math.cos(math.radians(lat2)) *
        math.sin(d_lon / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(a))


# -------------------------
# MAIN FEATURE FETCH
# -------------------------

def get_area_features(lat: float, lon: float):
    session = SessionLocal()

    try:
        areas = session.query(AreaFeature).all()

        if not areas:
            return default_features()

        # -------- k-NN (top 5 nearest) --------
        nearest_points = sorted(
            areas,
            key=lambda a: haversine(lat, lon, a.latitude, a.longitude)
        )[:5]

        # -------- Aggregate --------
        crime = sum(p.crime_score for p in nearest_points) / len(nearest_points)
        pop = sum(p.population_density for p in nearest_points) / len(nearest_points)
        road = sum(p.road_density for p in nearest_points) / len(nearest_points)
        light = sum(p.night_light_intensity for p in nearest_points) / len(nearest_points)

        # -------- Normalize --------
        return {
            "crime_density": float(crime),  # already 0–1
            "population_density": min(1.0, pop / 15000),
            "road_density": float(road),
            "visibility_score": min(1.0, light / 100),
        }

    except Exception as e:
        print("DB ERROR:", e)
        return default_features()

    finally:
        session.close()


# -------------------------
# DEFAULT FALLBACK
# -------------------------

def default_features():
    return {
        "crime_density": 0.3,
        "population_density": 0.5,
        "road_density": 0.5,
        "visibility_score": 0.5,
    }



