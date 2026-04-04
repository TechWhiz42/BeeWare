from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Annotated, Optional, List
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from contextlib import asynccontextmanager
import logging
import os

from risk_model import BeeWareRiskModel
from feature_extractor import FeatureExtractor
from route_analyzer import RouteAnalyzer, RouteSegment
from crime_data_handler import CrimeDataHandler
from database import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

model = BeeWareRiskModel()
crime_handler = CrimeDataHandler()
extractor = FeatureExtractor(crime_handler=crime_handler)
analyzer = RouteAnalyzer(model, extractor)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model, crime data, and database on startup, cleanup on shutdown."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("Environment variables loaded")
    except ImportError:
        logger.warning("python-dotenv not installed. Using default environment variables.")
    
    logger.info("Connecting to database...")
    try:
        db.connect()
        logger.info("Database connected successfully")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
    
    logger.info("Loading model...")
    try:
        model.load("beeware_model.pkl")
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.warning(f"Could not load model: {e}")
    
    logger.info("Loading crime data from database...")
    try:
        crime_handler.load_from_database()
        logger.info("Crime data loaded successfully")
    except Exception as e:
        logger.warning(f"Could not load crime data: {e}")
    
    yield
    
    logger.info("Disconnecting from database...")
    try:
        db.disconnect()
        logger.info("Database disconnected")
    except Exception as e:
        logger.warning(f"Error disconnecting database: {e}")
    
    logger.info("Shutting down system...")


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

class Location(BaseModel):
    latitude: Annotated[float, Field(..., description="Latitude coordinate")]
    longitude: Annotated[float, Field(..., description="Longitude coordinate")]
    timestamp: Annotated[datetime, Field(..., description="Time for safety assessment")]
    city: Optional[str] = Field(None, description="City name for crime data lookup")
    area: Optional[str] = Field(None, description="Area name for crime data lookup")


class RoutePoint(BaseModel):
    latitude: float
    longitude: float
    name: Optional[str] = None
    timestamp: Annotated[datetime, Field(..., description="Time for safety assessment")]
    city: Optional[str] = Field(None, description="City name for crime data lookup")
    area: Optional[str] = Field(None, description="Area name for crime data lookup")
    


class RouteRequest(BaseModel):
    waypoints: List[RoutePoint] = Field(..., description="List of route waypoints")
    route_name: Optional[str] = Field("Route", description="Route identifier/name")


class SegmentRiskResult(BaseModel):
    index: int
    name: str
    latitude: float
    longitude: float
    safety_score: float
    label: str
    color: str
    risk_class: Optional[int] = None


class SafetyRecommendation(BaseModel):
    text: str
    priority: Optional[str] = None


class LocationSafetyResponse(BaseModel):
    location_name: str
    latitude: float
    longitude: float
    safety_score: float
    category: str
    color: str
    timestamp: datetime
    recommendations: List[str]
    explanation: List[str]
    details: Optional[dict] = None


class RouteSafetyResponse(BaseModel):
    """Response for route safety assessment."""
    route_name: str
    safety_score: float
    category: str
    color: str
    summary: str
    timestamp: datetime
    total_segments: int
    high_risk_segments: int
    high_risk_percentage: float
    segment_details: List[SegmentRiskResult]
    recommendations: List[str]
    processing_time_ms: float


class BulkLocationRequest(BaseModel):
    """Request to analyze multiple locations."""
    locations: List[Location]
    timestamp: Optional[datetime] = None


class BulkLocationResponse(BaseModel):
    """Response for bulk location analysis."""
    count: int
    results: List[LocationSafetyResponse]
    high_risk_count: int




@app.post("/location/safety", response_model=LocationSafetyResponse)
def analyze_location_safety(location: Location):
    """
    Analyze safety of a single location.
    
    - latitude: Latitude coordinate
    - longitude: Longitude coordinate
    - timestamp: Time for safety assessment
    """
    if not model.is_trained:
        raise HTTPException(
            status_code=503,
            detail="Model not trained. Call /admin/train first."
        )
    
    try:
        features = extractor.extract(
            lat=location.latitude,
            lon=location.longitude,
            timestamp=location.timestamp,
            segment_length_m=100,
            city=location.city,
            area=location.area
        )
        
        risk_result = model.predict_segment(features)
        location_name = f"{location.latitude:.4f}, {location.longitude:.4f}"
        
        return LocationSafetyResponse(
            location_name=location_name,
            latitude=location.latitude,
            longitude=location.longitude,
            safety_score=risk_result["safety_score"],
            category=risk_result["label"],
            color=risk_result["color"],
            timestamp=location.timestamp,
            recommendations=risk_result.get("recommendations", []),
            explanation=risk_result.get("explanation", []),
            details=risk_result
        )
    except Exception as e:
        logger.error(f"Error analyzing location: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/route/safety", response_model=RouteSafetyResponse)
def analyze_route_safety(route_req: RouteRequest):
    """
    Analyze safety of a complete route.
    
    Requires a list of waypoints (at least 2).
    Returns aggregated safety assessment with segment-level details.
    """
    if not model.is_trained:
        raise HTTPException(
            status_code=503,
            detail="Model not trained. Call /admin/train first."
        )
    
    if len(route_req.waypoints) < 2:
        raise HTTPException(
            status_code=400,
            detail="Route must have at least 2 waypoints"
        )
    
    try:
        coords = [(wp.latitude, wp.longitude) for wp in route_req.waypoints]
        timestamp = route_req.waypoints[0].timestamp if route_req.waypoints else datetime.now()
        
        analysis = analyzer.analyze_coordinates(
            coords=coords,
            timestamp=timestamp
        )
        
        segment_details = [
            SegmentRiskResult(
                index=seg["index"],
                name=seg["name"],
                latitude=seg["lat"],
                longitude=seg["lon"],
                safety_score=seg["safety_score"],
                label=seg["label"],
                color=seg["color"]
            )
            for seg in analysis.segments
        ]
        
        high_risk_pct = (
            100 * len(analysis.high_risk_segments) / len(analysis.segments)
            if analysis.segments else 0
        )
        
        return RouteSafetyResponse(
            route_name=route_req.route_name or "Custom Route",
            safety_score=analysis.safety_score,
            category=analysis.category,
            color=analysis.color,
            summary=analysis.summary,
            timestamp=timestamp,
            total_segments=len(analysis.segments),
            high_risk_segments=len(analysis.high_risk_segments),
            high_risk_percentage=high_risk_pct,
            segment_details=segment_details,
            recommendations=analysis.recommendations,
            processing_time_ms=analysis.processing_time_ms
        )
    except Exception as e:
        logger.error(f"Error analyzing route: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/locations/safety/bulk", response_model=BulkLocationResponse)
def analyze_multiple_locations(request: BulkLocationRequest):
    """
    Analyze safety of multiple locations in bulk.
    
    Useful for analyzing a grid of locations or comparing multiple destinations.
    """
    if not model.is_trained:
        raise HTTPException(
            status_code=503,
            detail="Model not trained. Call /admin/train first."
        )
    
    results = []
    high_risk_count = 0
    
    try:
        for location in request.locations:
            features = extractor.extract(
                lat=location.latitude,
                lon=location.longitude,
                timestamp=location.timestamp,
                segment_length_m=100,
                city=location.city,
                area=location.area
            )
            
            risk_result = model.predict_segment(features)
            location_name = f"{location.latitude:.4f}, {location.longitude:.4f}"
            
            response = LocationSafetyResponse(
                location_name=location_name,
                latitude=location.latitude,
                longitude=location.longitude,
                safety_score=risk_result["safety_score"],
                category=risk_result["label"],
                color=risk_result["color"],
                timestamp=location.timestamp,
                recommendations=risk_result.get("recommendations", []),
                explanation=risk_result.get("explanation", []),
                details=risk_result
            )
            results.append(response)
            
            if risk_result["label"] == "Avoid":
                high_risk_count += 1
        
        return BulkLocationResponse(
            count=len(results),
            results=results,
            high_risk_count=high_risk_count
        )
    except Exception as e:
        logger.error(f"Error in bulk analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/train")
def train_model(n_samples: int = Query(50000, description="Training samples")):
    """Train the ML model."""
    try:
        logger.info(f"Starting model training with {n_samples} samples...")
        model.train(n_samples=n_samples, save=True)
        logger.info("Model training complete")
        
        return {
            "status": "success",
            "message": "Model trained and saved",
            "samples": n_samples,
            "model_path": "beeware_model.pkl"
        }
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/reload")
def reload_model():
    """Reload the model from disk."""
    try:
        logger.info("Reloading model...")
        model.load("beeware_model.pkl")
        logger.info("Model reloaded successfully")
        
        return {
            "status": "success",
            "message": "Model reloaded successfully",
            "is_trained": model.is_trained
        }
    except Exception as e:
        logger.error(f"Reload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/model-info")
def get_model_info():
    """Get information about the current model."""
    return {
        "is_trained": model.is_trained,
        "model_path": "beeware_model.pkl",
        "feature_extractor": "live_api_disabled",
        "training_metrics": getattr(model, "training_metrics", {})
    }


@app.post("/admin/load-crime-data")
def reload_crime_data():
    """Reload crime data from database."""
    try:
        logger.info("Reloading crime data from database...")
        crime_handler.load_from_database()
        
        record_count = len(crime_handler.crime_data) if crime_handler.crime_data is not None else 0
        logger.info(f"Crime data reloaded: {record_count} records")
        
        return {
            "status": "success",
            "message": "Crime data reloaded successfully",
            "data_records": record_count
        }
    except Exception as e:
        logger.error(f"Crime data reload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/location/database/{location_id}")
def get_location_from_database(location_id: int):
    """
    Fetch location info from your database.
    
    TODO: Replace with actual database query
    Example response shows what to implement in your DB layer.
    """
    return {
        "id": location_id,
        "name": "Example Location",
        "latitude": 28.6315,
        "longitude": 77.2167,
        "address": "Connaught Place, Delhi",
        "description": "Database placeholder - implement your DB query here"
    }


@app.get("/route/database/{route_id}")
def get_route_from_database(route_id: int):
    """
    Fetch route waypoints from your database.
    
    TODO: Replace with actual database query
    """
    return {
        "id": route_id,
        "name": "Example Route",
        "waypoints": [
            {"latitude": 28.6315, "longitude": 77.2167, "name": "Start"},
            {"latitude": 28.6289, "longitude": 77.2215, "name": "Middle"},
            {"latitude": 28.5700, "longitude": 77.2250, "name": "End"}
        ],
        "description": "Database placeholder - implement your DB query here"
    }


@app.post("/route/database/analyze/{route_id}")
def analyze_route_from_database(route_id: int):
    """
    Fetch a route from database and analyze its safety.
    Combines database query with ML analysis.
    """
    try:
        route_data = get_route_from_database(route_id)
        
        waypoints = [
            RoutePoint(
                latitude=wp["latitude"],
                longitude=wp["longitude"],
                name=wp.get("name")
            )
            for wp in route_data["waypoints"]
        ]
        
        route_request = RouteRequest(
            waypoints=waypoints,
            route_name=route_data.get("name", "Route")
        )
        
        return analyze_route_safety(route_request)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))