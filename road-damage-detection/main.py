from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import numpy as np
import cv2
from PIL import Image
import io
import os
from dotenv import load_dotenv
from typing import List
import logging
import uuid
import tensorflow as tf

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://kenya_user:kenya_secure_pass_2024@localhost:5432/kenya_ai_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class RoadSegment(Base):
    __tablename__ = "road_segments"
    
    id = Column(Integer, primary_key=True, index=True)
    segment_id = Column(String, unique=True, index=True)
    road_name = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    length_km = Column(Float)
    surface_type = Column(String)  # asphalt, concrete, gravel
    last_inspection = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class DamageDetection(Base):
    __tablename__ = "damage_detections"
    
    id = Column(Integer, primary_key=True, index=True)
    detection_id = Column(String, unique=True, index=True)
    segment_id = Column(String)
    image_path = Column(String)
    damage_type = Column(String)  # pothole, crack, rut, patch
    severity = Column(String)  # low, medium, high, critical
    confidence = Column(Float)
    damage_area_sqm = Column(Float)
    location_lat = Column(Float)
    location_lon = Column(Float)
    detected_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON)

class DroneInspection(Base):
    __tablename__ = "drone_inspections"
    
    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(String, unique=True, index=True)
    segment_id = Column(String)
    drone_id = Column(String)
    flight_altitude = Column(Float)
    num_images = Column(Integer)
    damages_found = Column(Integer)
    coverage_percentage = Column(Float)
    inspection_date = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON)

Base.metadata.create_all(bind=engine)

# FastAPI App
app = FastAPI(
    title="AI Road Damage Detection Using Drone Images",
    description="Automated road condition assessment using drone imagery and deep learning",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Road Damage Detector
class RoadDamageDetector:
    def __init__(self):
        self.damage_classes = {
            0: "pothole",
            1: "crack",
            2: "rut",
            3: "patch",
            4: "normal"
        }
        self.severity_thresholds = {
            "pothole": {"low": 0.3, "medium": 0.6, "high": 0.8},
            "crack": {"low": 0.4, "medium": 0.7, "high": 0.85},
            "rut": {"low": 0.3, "medium": 0.65, "high": 0.85},
            "patch": {"low": 0.4, "medium": 0.7, "high": 0.9}
        }
        self.model = self._load_or_create_model()
    
    def _load_or_create_model(self):
        """
        Load pre-trained model or create a new one
        """
        model_path = "models/road_damage_model.h5"
        
        if os.path.exists(model_path):
            logger.info("Loading trained model...")
            return tf.keras.models.load_model(model_path)
        else:
            logger.info("Creating new model architecture...")
            # Simple CNN for demonstration
            model = tf.keras.Sequential([
                tf.keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=(224, 224, 3)),
                tf.keras.layers.MaxPooling2D((2, 2)),
                tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
                tf.keras.layers.MaxPooling2D((2, 2)),
                tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
                tf.keras.layers.Flatten(),
                tf.keras.layers.Dense(64, activation='relu'),
                tf.keras.layers.Dropout(0.5),
                tf.keras.layers.Dense(5, activation='softmax')
            ])
            return model
    
    def detect_damage(self, image_array: np.ndarray) -> dict:
        """
        Detect road damage in an image
        """
        # Preprocess image
        processed = cv2.resize(image_array, (224, 224))
        processed = processed / 255.0
        processed = np.expand_dims(processed, axis=0)
        
        # Make prediction
        predictions = self.model.predict(processed, verbose=0)
        class_idx = np.argmax(predictions[0])
        confidence = float(predictions[0][class_idx])
        damage_class = self.damage_classes[class_idx]
        
        # Determine severity
        if damage_class == "normal":
            severity = "none"
        else:
            thresholds = self.severity_thresholds.get(damage_class, {})
            if confidence < thresholds.get("low", 0.5):
                severity = "low"
            elif confidence < thresholds.get("medium", 0.7):
                severity = "medium"
            elif confidence < thresholds.get("high", 0.85):
                severity = "high"
            else:
                severity = "critical"
        
        # Estimate damage area (simplified)
        damage_area = self._estimate_damage_area(image_array, damage_class)
        
        return {
            "damage_type": damage_class,
            "confidence": confidence,
            "severity": severity,
            "damage_area_sqm": damage_area,
            "all_predictions": dict(zip(
                [self.damage_classes[i] for i in range(len(self.damage_classes))],
                [float(p) for p in predictions[0]]
            ))
        }
    
    def _estimate_damage_area(self, image_array: np.ndarray, damage_type: str) -> float:
        """
        Estimate damage area in square meters
        Assumes: image is 1m x 1m from drone at standard altitude
        """
        if damage_type == "normal":
            return 0.0
        
        # Convert to grayscale
        gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        
        # Detect dark areas (potential damage)
        _, binary = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)
        
        # Calculate percentage of damaged area
        damage_pixels = np.sum(binary > 0)
        total_pixels = binary.size
        damage_percentage = damage_pixels / total_pixels
        
        # Assume 1m x 1m per image
        area_sqm = damage_percentage
        
        return min(1.0, area_sqm)
    
    def detect_damage_batch(self, image_paths: List[str]) -> List[dict]:
        """
        Detect damage in multiple images
        """
        results = []
        for path in image_paths:
            image = Image.open(path).convert('RGB')
            image_array = np.array(image)
            result = self.detect_damage(image_array)
            result["image_path"] = path
            results.append(result)
        return results

detector = RoadDamageDetector()

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
        "service": "AI Road Damage Detection Using Drone Images",
        "version": "1.0.0",
        "endpoints": [
            "/detect",
            "/detections",
            "/inspections",
            "/segments",
            "/health"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "road-damage-detection"}

@app.post("/detect")
async def detect_road_damage(
    file: UploadFile = File(...),
    latitude: float = None,
    longitude: float = None,
    segment_id: str = None,
    db: Session = None
):
    """
    Detect road damage in a single drone image
    """
    if db is None:
        db = SessionLocal()
    
    try:
        # Read image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert('RGB')
        image_array = np.array(image)
        
        # Detect damage
        detection_result = detector.detect_damage(image_array)
        
        # Save to database
        detection_id = str(uuid.uuid4())
        detection = DamageDetection(
            detection_id=detection_id,
            segment_id=segment_id or "unknown",
            image_path=f"images/{detection_id}.jpg",
            damage_type=detection_result["damage_type"],
            severity=detection_result["severity"],
            confidence=detection_result["confidence"],
            damage_area_sqm=detection_result["damage_area_sqm"],
            location_lat=latitude,
            location_lon=longitude,
            metadata=detection_result["all_predictions"]
        )
        db.add(detection)
        db.commit()
        db.refresh(detection)
        
        return {
            "detection_id": detection_id,
            "damage_type": detection_result["damage_type"],
            "severity": detection_result["severity"],
            "confidence": detection_result["confidence"],
            "damage_area_sqm": detection_result["damage_area_sqm"],
            "location": {"latitude": latitude, "longitude": longitude},
            "timestamp": detection.detected_at,
            "recommendation": get_repair_recommendation(
                detection_result["damage_type"],
                detection_result["severity"],
                detection_result["damage_area_sqm"]
            )
        }
    
    except Exception as e:
        logger.error(f"Detection error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/inspect")
async def process_inspection(
    segment_id: str,
    drone_id: str,
    flight_altitude: float,
    files: List[UploadFile] = File(...),
    db: Session = None,
    background_tasks: BackgroundTasks = None
):
    """
    Process multiple images from a drone inspection
    """
    if db is None:
        db = SessionLocal()
    
    inspection_id = str(uuid.uuid4())
    damages_found = 0
    
    try:
        for file in files:
            contents = await file.read()
            image = Image.open(io.BytesIO(contents)).convert('RGB')
            image_array = np.array(image)
            
            result = detector.detect_damage(image_array)
            
            if result["damage_type"] != "normal":
                damages_found += 1
                
                # Save detection
                detection = DamageDetection(
                    detection_id=str(uuid.uuid4()),
                    segment_id=segment_id,
                    image_path=f"inspections/{inspection_id}/{file.filename}",
                    damage_type=result["damage_type"],
                    severity=result["severity"],
                    confidence=result["confidence"],
                    damage_area_sqm=result["damage_area_sqm"],
                    metadata=result["all_predictions"]
                )
                db.add(detection)
        
        # Save inspection record
        inspection = DroneInspection(
            inspection_id=inspection_id,
            segment_id=segment_id,
            drone_id=drone_id,
            flight_altitude=flight_altitude,
            num_images=len(files),
            damages_found=damages_found,
            coverage_percentage=100.0,
            metadata={"processed_at": datetime.utcnow().isoformat()}
        )
        db.add(inspection)
        db.commit()
        
        return {
            "inspection_id": inspection_id,
            "segment_id": segment_id,
            "drone_id": drone_id,
            "total_images": len(files),
            "damages_found": damages_found,
            "coverage_percentage": 100.0,
            "status": "completed"
        }
    
    except Exception as e:
        logger.error(f"Inspection error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/segments")
async def create_road_segment(
    road_name: str,
    latitude: float,
    longitude: float,
    length_km: float,
    surface_type: str = "asphalt",
    db: Session = None
):
    """
    Register a road segment for monitoring
    """
    if db is None:
        db = SessionLocal()
    
    segment_id = f"ROAD-{road_name.replace(' ', '-')}-{uuid.uuid4().hex[:8]}"
    
    segment = RoadSegment(
        segment_id=segment_id,
        road_name=road_name,
        latitude=latitude,
        longitude=longitude,
        length_km=length_km,
        surface_type=surface_type,
        last_inspection=datetime.utcnow()
    )
    db.add(segment)
    db.commit()
    db.refresh(segment)
    
    return {
        "segment_id": segment_id,
        "road_name": road_name,
        "length_km": length_km,
        "message": "Road segment registered successfully"
    }

@app.get("/segments")
async def get_road_segments(db: Session = None, skip: int = 0, limit: int = 100):
    """
    Get all registered road segments
    """
    if db is None:
        db = SessionLocal()
    
    segments = db.query(RoadSegment).offset(skip).limit(limit).all()
    return segments

@app.get("/detections")
async def get_detections(
    segment_id: str = None,
    damage_type: str = None,
    severity: str = None,
    db: Session = None,
    skip: int = 0,
    limit: int = 100
):
    """
    Get damage detections with filtering
    """
    if db is None:
        db = SessionLocal()
    
    query = db.query(DamageDetection)
    
    if segment_id:
        query = query.filter(DamageDetection.segment_id == segment_id)
    if damage_type:
        query = query.filter(DamageDetection.damage_type == damage_type)
    if severity:
        query = query.filter(DamageDetection.severity == severity)
    
    detections = query.order_by(DamageDetection.detected_at.desc()).offset(skip).limit(limit).all()
    return detections

@app.get("/inspections")
async def get_inspections(db: Session = None, skip: int = 0, limit: int = 100):
    """
    Get drone inspection records
    """
    if db is None:
        db = SessionLocal()
    
    inspections = db.query(DroneInspection).order_by(
        DroneInspection.inspection_date.desc()
    ).offset(skip).limit(limit).all()
    
    return inspections

@app.get("/stats")
async def get_statistics(db: Session = None):
    """
    Get system statistics
    """
    if db is None:
        db = SessionLocal()
    
    return {
        "total_segments": db.query(RoadSegment).count(),
        "total_detections": db.query(DamageDetection).count(),
        "total_inspections": db.query(DroneInspection).count(),
        "damage_breakdown": {
            "pothole": db.query(DamageDetection).filter(
                DamageDetection.damage_type == "pothole"
            ).count(),
            "crack": db.query(DamageDetection).filter(
                DamageDetection.damage_type == "crack"
            ).count(),
            "rut": db.query(DamageDetection).filter(
                DamageDetection.damage_type == "rut"
            ).count(),
            "patch": db.query(DamageDetection).filter(
                DamageDetection.damage_type == "patch"
            ).count()
        },
        "severity_breakdown": {
            "low": db.query(DamageDetection).filter(
                DamageDetection.severity == "low"
            ).count(),
            "medium": db.query(DamageDetection).filter(
                DamageDetection.severity == "medium"
            ).count(),
            "high": db.query(DamageDetection).filter(
                DamageDetection.severity == "high"
            ).count(),
            "critical": db.query(DamageDetection).filter(
                DamageDetection.severity == "critical"
            ).count()
        },
        "avg_damage_area_sqm": db.query(DamageDetection).with_entities(
            db.func.avg(DamageDetection.damage_area_sqm)
        ).scalar() or 0
    }

def get_repair_recommendation(damage_type: str, severity: str, area: float) -> str:
    """
    Generate repair recommendations based on damage characteristics
    """
    priority = {
        "critical": "URGENT",
        "high": "PRIORITY",
        "medium": "SCHEDULE",
        "low": "MONITOR"
    }
    
    repair_methods = {
        "pothole": "Fill with bituminous material and compact",
        "crack": "Seal with crack sealant or overlay",
        "rut": "Mill and overlay or full reconstruction",
        "patch": "Monitor for deterioration and potential re-patching"
    }
    
    priority_level = priority.get(severity, "MONITOR")
    repair_method = repair_methods.get(damage_type, "Inspect and assess")
    
    return f"[{priority_level}] {repair_method}. Affected area: {area:.2f} m². Recommend inspection within 2 weeks."

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
