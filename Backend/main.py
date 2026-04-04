from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, validator
from typing import Annotated, Optional, List
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from contextlib import asynccontextmanager
import logging

from risk_model import BeeWareRiskModel
from feature_extractor import FeatureExtractor
from route_analyzer import RouteAnalyzer
from service import SafetyAnalysisService
from validators import (
    validate_latitude, validate_longitude, validate_crime_density,
    ValidationError, get_crime_density
)
from database import AREA_COORDINATES, CRIME_STATS, normalize_crime_density

logger = logging.getLogger(__name__)


def _create_area_features():
    """
    Create area features from database coordinates and crime data.
    Returns list of dicts with geocoded features for spatial interpolation.
    """
    area_features = []
    
    for area_id, (latitude, longitude) in AREA_COORDINATES.items():
        crime_count = CRIME_STATS.get(area_id, 0)
        crime_density = normalize_crime_density(crime_count)
        
        # Create realistic synthetic features based on area properties
        # In a production system, these would come from actual data sources
        area_features.append({
            "latitude": latitude,
            "longitude": longitude,
            "crime_score": crime_density,
            "population_density": 0.6,  # Moderate population across Lucknow
            "road_density": 0.7,  # Good road infrastructure
            "night_light_intensity": 0.65,  # Urban night lighting
        })
    
    return area_features


model = BeeWareRiskModel()
# Initialize extractor with area features from database
area_features = _create_area_features()
extractor = FeatureExtractor(area_features=area_features)
analyzer = RouteAnalyzer(model, extractor)
service = SafetyAnalysisService(model, extractor, analyzer)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    try:
        model.load("beeware_model.pkl")
    except Exception as e:
        logger.warning(f"Could not load model: {e}")
    
    yield


app = FastAPI(
    title="BeeWare Safety API",
    description="Location and route safety assessment system",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class LocationRequest(BaseModel):
    latitude: Annotated[float, Field(..., ge=-90, le=90, description="Latitude [-90, 90]")]
    longitude: Annotated[float, Field(..., ge=-180, le=180, description="Longitude [-180, 180]")]
    timestamp: Annotated[datetime, Field(..., description="Time for assessment")]
    
    @validator("latitude")
    def validate_lat(cls, v):
        return validate_latitude(v)
    
    @validator("longitude")
    def validate_lon(cls, v):
        return validate_longitude(v)


class WaypointRequest(BaseModel):
    latitude: Annotated[float, Field(..., ge=-90, le=90, description="Latitude [-90, 90]")]
    longitude: Annotated[float, Field(..., ge=-180, le=180, description="Longitude [-180, 180]")]
    timestamp: Annotated[datetime, Field(..., description="Time for assessment")]
    name: Optional[str] = Field(None, description="Waypoint name/identifier")
    
    @validator("latitude")
    def validate_lat(cls, v):
        return validate_latitude(v)
    
    @validator("longitude")
    def validate_lon(cls, v):
        return validate_longitude(v)


class RouteRequest(BaseModel):
    waypoints: List[WaypointRequest] = Field(..., min_items=2, description="Route waypoints (min 2)")
    route_name: Optional[str] = Field("Route", description="Route name/identifier")


class LocationResponse(BaseModel):
    latitude: float
    longitude: float
    safety_score: float
    label: str
    color: str
    probability_safe: float
    probability_caution: float
    probability_high_risk: float
    crime_density_norm: float
    crime_density: Optional[float] = None
    timestamp: Optional[str] = None
    time_features: Optional[dict] = None
    confidence: Optional[float] = None
    explanation: Optional[List[str]] = None


class BulkLocationRequest(BaseModel):
    locations: List[LocationRequest] = Field(..., min_items=1, description="Locations to analyze")


class BulkLocationResponse(BaseModel):
    count: int
    results: List[LocationResponse]
    high_risk_count: int


class SegmentDetail(BaseModel):
    index: int
    name: str
    latitude: float
    longitude: float
    safety_score: float
    label: str
    color: str
    explanation: str


class RouteResponse(BaseModel):
    route_name: str
    safety_score: float
    category: str
    color: str
    summary: str
    timestamp: str
    total_segments: int
    high_risk_segments: int
    high_risk_percentage: float
    segment_details: List[SegmentDetail]
    recommendations: List[str]
    processing_time_ms: float


class ErrorResponse(BaseModel):
    error: str
    detail: str
    status_code: int


@app.get("/health")
def health_check():
    """Check API health and model status."""
    return {
        "status": "healthy",
        "model_trained": model.is_trained,
        "model_metrics": model.training_metrics if model.is_trained else None
    }


@app.post("/location/safety", response_model=LocationResponse)
def analyze_location_safety(request: LocationRequest):
    """Analyze safety of a single location.
    
    Required input:
    - latitude: float [-90, 90]
    - longitude: float [-180, 180]
    - timestamp: datetime
    
    Returns safety assessment with or without trained model (uses fallback if needed).
    """
    try:
        crime = get_crime_density(request.latitude, request.longitude)
        
        result = service.analyze_location(
            latitude=request.latitude,
            longitude=request.longitude,
            timestamp=request.timestamp,
            crime_density_norm=crime,
        )
        return LocationResponse(**result)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Location analysis error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/route/safety", response_model=RouteResponse)
def analyze_route_safety(request: RouteRequest):
    """Analyze safety of a complete route.
    
    Each waypoint must include:
    - latitude: float [-90, 90]
    - longitude: float [-180, 180]
    - timestamp: datetime
    - name: optional str
    
    Returns route safety assessment with or without trained model (uses fallback if needed).
    """
    try:
        waypoints_data = []
        for wp in request.waypoints:
            crime = get_crime_density(wp.latitude, wp.longitude)
            
            waypoints_data.append({
                "latitude": wp.latitude,
                "longitude": wp.longitude,
                "timestamp": wp.timestamp,
                "crime_density_norm": crime,
                "name": wp.name,
            })
        
        result = service.analyze_route(
            waypoints=waypoints_data,
            route_name=request.route_name,
            timestamp=request.waypoints[0].timestamp if request.waypoints else None,
        )
        return RouteResponse(**result)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Route analysis error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/locations/safety/bulk", response_model=BulkLocationResponse)
def analyze_multiple_locations(request: BulkLocationRequest):
    """Analyze safety of multiple locations in bulk.
    
    Each location must include:
    - latitude: float [-90, 90]
    - longitude: float [-180, 180]
    - timestamp: datetime
    
    Returns bulk analysis with or without trained model (uses fallback if needed).
    """
    try:
        locations_data = []
        for loc in request.locations:
            crime = get_crime_density(loc.latitude, loc.longitude)
            
            locations_data.append({
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "timestamp": loc.timestamp,
                "crime_density_norm": crime,
            })
        
        result = service.analyze_multiple_locations(locations_data)
        
        return BulkLocationResponse(
            count=result["count"],
            results=[LocationResponse(**r) for r in result["results"]],
            high_risk_count=result["high_risk_count"],
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Bulk analysis error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/admin/train")
def train_model(csv_path: str = Query(..., description="Path to CSV dataset")):
    """Train the ML model from CSV dataset.
    
    CSV must contain all 11 required features and a label column.
    All values must be normalized to [0, 1].
    """
    if not csv_path:
        raise HTTPException(status_code=400, detail="csv_path is required")
    
    try:
        model.train_from_csv(csv_path)
        model.save("beeware_model.pkl")
        
        return {
            "status": "success",
            "message": "Model trained and saved",
            "csv_path": csv_path,
            "metrics": model.training_metrics
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"CSV file not found: {csv_path}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise HTTPException(status_code=500, detail="Training failed")


@app.post("/admin/reload")
def reload_model():
    """Reload the model from disk."""
    try:
        model.load("beeware_model.pkl")
        
        return {
            "status": "success",
            "message": "Model reloaded successfully",
            "is_trained": model.is_trained,
            "metrics": model.training_metrics
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Model file not found")
    except Exception as e:
        logger.error(f"Reload failed: {e}")
        raise HTTPException(status_code=500, detail="Reload failed")


@app.get("/admin/model-info")
def get_model_info():
    """Get information about the current model."""
    return {
        "is_trained": model.is_trained,
        "model_path": "beeware_model.pkl",
        "metrics": model.training_metrics if model.is_trained else None
    }
