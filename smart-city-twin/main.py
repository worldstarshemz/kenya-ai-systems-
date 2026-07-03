from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import json
import os
from dotenv import load_dotenv
from typing import List, Dict
import asyncio
from enum import Enum
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://kenya_user:kenya_secure_pass_2024@localhost:5432/kenya_ai_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class CityDistrict(Base):
    __tablename__ = "city_districts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    area_sqkm = Column(Float)
    population = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class CityAsset(Base):
    __tablename__ = "city_assets"
    
    id = Column(Integer, primary_key=True, index=True)
    district_id = Column(Integer)
    asset_type = Column(String)  # road, building, traffic_light, sensor
    name = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    status = Column(String)  # operational, maintenance, damaged
    condition_score = Column(Float)  # 0-100
    last_maintenance = Column(DateTime)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer)
    sensor_type = Column(String)  # air_quality, temperature, traffic_flow, water_level
    value = Column(Float)
    unit = Column(String)
    reading_time = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON)

class TrafficEvent(Base):
    __tablename__ = "traffic_events"
    
    id = Column(Integer, primary_key=True, index=True)
    location = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    event_type = Column(String)  # congestion, accident, construction
    severity = Column(Integer)  # 1-5
    description = Column(String)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

Base.metadata.create_all(bind=engine)

# FastAPI App
app = FastAPI(
    title="Kenya Smart City Digital Twin",
    description="3D city simulation and real-time IoT integration",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data Models
class AssetType(str, Enum):
    ROAD = "road"
    BUILDING = "building"
    TRAFFIC_LIGHT = "traffic_light"
    SENSOR = "sensor"
    UTILITY = "utility"

class SensorType(str, Enum):
    AIR_QUALITY = "air_quality"
    TEMPERATURE = "temperature"
    TRAFFIC_FLOW = "traffic_flow"
    WATER_LEVEL = "water_level"
    NOISE = "noise"
    POWER = "power"

# City Data Manager
class CityTwinManager:
    def __init__(self):
        self.connected_clients = []
        self.simulation_running = False
    
    def get_city_overview(self, db: Session) -> Dict:
        """
        Get comprehensive city overview
        """
        districts = db.query(CityDistrict).all()
        assets = db.query(CityAsset).all()
        sensors = db.query(SensorReading).all()
        
        return {
            "districts": len(districts),
            "total_population": sum([d.population for d in districts]),
            "assets": len(assets),
            "sensor_count": len(sensors),
            "asset_breakdown": self._breakdown_assets(assets),
            "health_status": self._calculate_city_health(assets)
        }
    
    def _breakdown_assets(self, assets) -> Dict:
        breakdown = {}
        for asset in assets:
            breakdown[asset.asset_type] = breakdown.get(asset.asset_type, 0) + 1
        return breakdown
    
    def _calculate_city_health(self, assets) -> float:
        if not assets:
            return 0
        avg_condition = sum([a.condition_score for a in assets]) / len(assets)
        return avg_condition
    
    def get_district_3d_data(self, district_id: int, db: Session) -> Dict:
        """
        Get 3D visualization data for a district
        """
        district = db.query(CityDistrict).filter(CityDistrict.id == district_id).first()
        if not district:
            return None
        
        assets = db.query(CityAsset).filter(CityAsset.district_id == district_id).all()
        
        # Convert assets to 3D geometry format
        geometries = []
        for asset in assets:
            geometries.append({
                "id": asset.id,
                "type": asset.asset_type,
                "position": {
                    "x": asset.longitude,
                    "y": asset.latitude,
                    "z": 0  # Height placeholder
                },
                "color": self._get_asset_color(asset.status),
                "name": asset.name,
                "status": asset.status
            })
        
        return {
            "district": {
                "id": district.id,
                "name": district.name,
                "center": {
                    "latitude": district.latitude,
                    "longitude": district.longitude
                },
                "area": district.area_sqkm,
                "population": district.population
            },
            "geometries": geometries
        }
    
    def _get_asset_color(self, status: str) -> str:
        colors = {
            "operational": "#00ff00",
            "maintenance": "#ffff00",
            "damaged": "#ff0000"
        }
        return colors.get(status, "#808080")

manager = CityTwinManager()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Routes
@app.get("/")
async def root():
    return {
        "service": "Kenya Smart City Digital Twin",
        "version": "1.0.0",
        "endpoints": [
            "/city/overview",
            "/districts",
            "/districts/{id}/3d",
            "/assets",
            "/sensors",
            "/traffic",
            "/health"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "smart-city-twin"}

@app.get("/city/overview")
async def city_overview(db: Session = None):
    """
    Get comprehensive city overview
    """
    if db is None:
        db = SessionLocal()
    
    overview = manager.get_city_overview(db)
    return overview

@app.post("/districts")
async def create_district(
    name: str,
    latitude: float,
    longitude: float,
    area_sqkm: float,
    population: int,
    db: Session = None
):
    """
    Create a new city district
    """
    if db is None:
        db = SessionLocal()
    
    district = CityDistrict(
        name=name,
        latitude=latitude,
        longitude=longitude,
        area_sqkm=area_sqkm,
        population=population
    )
    db.add(district)
    db.commit()
    db.refresh(district)
    
    return {
        "id": district.id,
        "name": district.name,
        "message": f"District {name} created successfully"
    }

@app.get("/districts")
async def get_districts(db: Session = None, skip: int = 0, limit: int = 100):
    """
    Get all city districts
    """
    if db is None:
        db = SessionLocal()
    
    districts = db.query(CityDistrict).offset(skip).limit(limit).all()
    return districts

@app.get("/districts/{district_id}/3d")
async def get_district_3d(district_id: int, db: Session = None):
    """
    Get 3D visualization data for a district
    """
    if db is None:
        db = SessionLocal()
    
    data = manager.get_district_3d_data(district_id, db)
    if not data:
        raise HTTPException(status_code=404, detail="District not found")
    
    return data

@app.post("/assets")
async def create_asset(
    district_id: int,
    asset_type: AssetType,
    name: str,
    latitude: float,
    longitude: float,
    db: Session = None
):
    """
    Register a city asset (road, building, sensor, etc.)
    """
    if db is None:
        db = SessionLocal()
    
    asset = CityAsset(
        district_id=district_id,
        asset_type=asset_type,
        name=name,
        latitude=latitude,
        longitude=longitude,
        status="operational",
        condition_score=100.0,
        metadata={}
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    
    return {
        "id": asset.id,
        "name": asset.name,
        "type": asset.asset_type,
        "message": "Asset registered successfully"
    }

@app.get("/assets")
async def get_assets(
    asset_type: str = None,
    status: str = None,
    db: Session = None,
    skip: int = 0,
    limit: int = 100
):
    """
    Get city assets with optional filtering
    """
    if db is None:
        db = SessionLocal()
    
    query = db.query(CityAsset)
    
    if asset_type:
        query = query.filter(CityAsset.asset_type == asset_type)
    if status:
        query = query.filter(CityAsset.status == status)
    
    assets = query.offset(skip).limit(limit).all()
    return assets

@app.post("/sensors/reading")
async def record_sensor_reading(
    asset_id: int,
    sensor_type: SensorType,
    value: float,
    unit: str,
    db: Session = None
):
    """
    Record sensor reading from IoT devices
    """
    if db is None:
        db = SessionLocal()
    
    reading = SensorReading(
        asset_id=asset_id,
        sensor_type=sensor_type,
        value=value,
        unit=unit,
        metadata={
            "timestamp": datetime.utcnow().isoformat(),
            "source": "iot_device"
        }
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    
    return {
        "id": reading.id,
        "sensor_type": sensor_type,
        "value": value,
        "unit": unit,
        "recorded_at": reading.reading_time
    }

@app.get("/sensors/latest/{asset_id}")
async def get_latest_sensor_readings(asset_id: int, db: Session = None):
    """
    Get latest sensor readings for an asset
    """
    if db is None:
        db = SessionLocal()
    
    readings = db.query(SensorReading).filter(
        SensorReading.asset_id == asset_id
    ).order_by(SensorReading.reading_time.desc()).limit(10).all()
    
    return readings

@app.post("/traffic/event")
async def report_traffic_event(
    location: str,
    latitude: float,
    longitude: float,
    event_type: str,
    severity: int,
    description: str = "",
    db: Session = None
):
    """
    Report a traffic event (congestion, accident, construction)
    """
    if db is None:
        db = SessionLocal()
    
    if severity < 1 or severity > 5:
        raise HTTPException(status_code=400, detail="Severity must be between 1-5")
    
    event = TrafficEvent(
        location=location,
        latitude=latitude,
        longitude=longitude,
        event_type=event_type,
        severity=severity,
        description=description
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    
    return {
        "id": event.id,
        "location": location,
        "event_type": event_type,
        "severity": severity,
        "status": "reported"
    }

@app.get("/traffic/active")
async def get_active_traffic_events(db: Session = None):
    """
    Get all active (unresolved) traffic events
    """
    if db is None:
        db = SessionLocal()
    
    events = db.query(TrafficEvent).filter(
        TrafficEvent.resolved == False
    ).order_by(TrafficEvent.severity.desc()).all()
    
    return events

@app.patch("/traffic/event/{event_id}/resolve")
async def resolve_traffic_event(event_id: int, db: Session = None):
    """
    Mark a traffic event as resolved
    """
    if db is None:
        db = SessionLocal()
    
    event = db.query(TrafficEvent).filter(TrafficEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    event.resolved = True
    event.resolved_at = datetime.utcnow()
    db.commit()
    
    return {"id": event.id, "status": "resolved"}

@app.get("/stats")
async def get_city_statistics(db: Session = None):
    """
    Get comprehensive city statistics
    """
    if db is None:
        db = SessionLocal()
    
    return {
        "total_districts": db.query(CityDistrict).count(),
        "total_assets": db.query(CityAsset).count(),
        "sensor_readings_today": db.query(SensorReading).filter(
            SensorReading.reading_time >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count(),
        "active_traffic_events": db.query(TrafficEvent).filter(
            TrafficEvent.resolved == False
        ).count(),
        "asset_status": {
            "operational": db.query(CityAsset).filter(CityAsset.status == "operational").count(),
            "maintenance": db.query(CityAsset).filter(CityAsset.status == "maintenance").count(),
            "damaged": db.query(CityAsset).filter(CityAsset.status == "damaged").count()
        }
    }

@app.websocket("/ws/live-data")
async def websocket_live_data(websocket: WebSocket):
    """
    WebSocket endpoint for live city data streaming
    """
    await websocket.accept()
    manager.connected_clients.append(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            # Echo or process received data
            await websocket.send_json({
                "type": "ack",
                "data": json.loads(data)
            })
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.connected_clients.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
