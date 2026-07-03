from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import numpy as np
import cv2
from PIL import Image
import io
import os
from dotenv import load_dotenv
from typing import List, Optional
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
class FarmPlot(Base):
    __tablename__ = "farm_plots"
    
    id = Column(Integer, primary_key=True, index=True)
    plot_id = Column(String, unique=True, index=True)
    farmer_name = Column(String)
    county = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    area_hectares = Column(Float)
    crop_type = Column(String)  # maize, wheat, rice, beans
    planting_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class DiseaseDetection(Base):
    __tablename__ = "crop_disease_detections"
    
    id = Column(Integer, primary_key=True, index=True)
    detection_id = Column(String, unique=True, index=True)
    plot_id = Column(String, index=True)
    disease_name = Column(String)  # powdery_mildew, leaf_rust, blight, etc
    severity = Column(String)  # low, moderate, high, severe
    confidence = Column(Float)
    infected_area_percentage = Column(Float)
    ndvi_score = Column(Float)  # Normalized Difference Vegetation Index
    satellite_source = Column(String)  # Sentinel-2, Landsat-8, etc
    detected_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON)

class SatelliteImage(Base):
    __tablename__ = "satellite_images"
    
    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(String, unique=True, index=True)
    plot_id = Column(String, index=True)
    source = Column(String)  # Sentinel-2, Landsat-8, Planet Labs
    acquisition_date = Column(DateTime)
    cloud_coverage = Column(Float)
    resolution_m = Column(Float)
    bands = Column(JSON)
    stored_at = Column(DateTime, default=datetime.utcnow)

class DiseaseAlert(Base):
    __tablename__ = "disease_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String, unique=True, index=True)
    plot_id = Column(String, index=True)
    disease_name = Column(String)
    severity = Column(String)
    recommended_action = Column(String)
    sent_to_farmer = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# FastAPI App
app = FastAPI(
    title="Satellite-Based Crop Disease Detection",
    description="AI-powered agricultural disease detection using satellite imagery",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crop Disease Detector
class CropDiseaseDetector:
    def __init__(self):
        self.diseases = {
            0: "healthy",
            1: "powdery_mildew",
            2: "leaf_rust",
            3: "blight",
            4: "fusarium_wilt",
            5: "septoria"
        }
        self.crop_types = ["maize", "wheat", "rice", "beans"]
        self.model = self._load_or_create_model()
    
    def _load_or_create_model(self):
        """
        Load pre-trained model or create a new one
        """
        model_path = "models/crop_disease_model.h5"
        
        if os.path.exists(model_path):
            logger.info("Loading trained model...")
            return tf.keras.models.load_model(model_path)
        else:
            logger.info("Creating new model architecture...")
            model = tf.keras.Sequential([
                tf.keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=(224, 224, 3)),
                tf.keras.layers.MaxPooling2D((2, 2)),
                tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
                tf.keras.layers.MaxPooling2D((2, 2)),
                tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
                tf.keras.layers.Flatten(),
                tf.keras.layers.Dense(128, activation='relu'),
                tf.keras.layers.Dropout(0.5),
                tf.keras.layers.Dense(len(self.diseases), activation='softmax')
            ])
            return model
    
    def detect_disease(self, image_array: np.ndarray, crop_type: str = None) -> dict:
        """
        Detect crop disease in satellite/field image
        """
        # Preprocess image
        processed = cv2.resize(image_array, (224, 224))
        processed = processed / 255.0
        processed = np.expand_dims(processed, axis=0)
        
        # Make prediction
        predictions = self.model.predict(processed, verbose=0)
        class_idx = np.argmax(predictions[0])
        confidence = float(predictions[0][class_idx])
        disease = self.diseases[class_idx]
        
        # Calculate NDVI (Normalized Difference Vegetation Index)
        ndvi = self._calculate_ndvi(image_array)
        
        # Determine severity based on disease and NDVI
        severity = self._determine_severity(disease, confidence, ndvi)
        
        # Estimate infected area
        infected_percentage = self._estimate_infected_area(image_array, disease)
        
        return {
            "disease_name": disease,
            "confidence": confidence,
            "severity": severity,
            "ndvi_score": ndvi,
            "infected_area_percentage": infected_percentage,
            "crop_type": crop_type,
            "all_predictions": dict(zip(
                list(self.diseases.values()),
                [float(p) for p in predictions[0]]
            ))
        }
    
    def _calculate_ndvi(self, image_array: np.ndarray) -> float:
        """
        Calculate Normalized Difference Vegetation Index
        NDVI = (NIR - Red) / (NIR + Red)
        For RGB images, approximate using channel differences
        """
        # Extract channels
        if len(image_array.shape) == 3 and image_array.shape[2] >= 3:
            red = image_array[:, :, 0].astype(float)
            green = image_array[:, :, 1].astype(float)
            blue = image_array[:, :, 2].astype(float)
            
            # Approximate NIR from green and red
            nir = green + (green - red)
            
            # Calculate NDVI
            ndvi_array = (nir - red) / (nir + red + 1e-8)
            ndvi = np.mean(ndvi_array)
        else:
            ndvi = 0.0
        
        return float(np.clip(ndvi, -1, 1))
    
    def _determine_severity(self, disease: str, confidence: float, ndvi: float) -> str:
        """
        Determine disease severity based on multiple factors
        """
        if disease == "healthy":
            return "none"
        
        # NDVI below -0.2 indicates poor vegetation
        ndvi_factor = 1.0 if ndvi < 0.3 else 0.7
        combined_score = confidence * ndvi_factor
        
        if combined_score < 0.4:
            return "low"
        elif combined_score < 0.6:
            return "moderate"
        elif combined_score < 0.8:
            return "high"
        else:
            return "severe"
    
    def _estimate_infected_area(self, image_array: np.ndarray, disease: str) -> float:
        """
        Estimate percentage of infected area
        """
        if disease == "healthy":
            return 0.0
        
        # Convert to HSV for better disease detection
        if len(image_array.shape) == 3 and image_array.shape[2] == 3:
            hsv = cv2.cvtColor(image_array.astype(np.uint8), cv2.COLOR_RGB2HSV)
            
            # Disease symptoms typically appear as color anomalies
            # Lower saturation (grayscale) indicates stress
            saturation = hsv[:, :, 1].astype(float) / 255.0
            affected_pixels = np.sum(saturation < 0.5)
            total_pixels = saturation.size
            
            infected_percentage = (affected_pixels / total_pixels) * 100
        else:
            infected_percentage = 0.0
        
        return float(np.clip(infected_percentage, 0, 100))
    
    def analyze_multispectral(self, red: np.ndarray, green: np.ndarray, blue: np.ndarray, nir: np.ndarray) -> dict:
        """
        Analyze multispectral satellite data (Sentinel-2 bands)
        """
        # Calculate various indices
        red_f = red.astype(float)
        nir_f = nir.astype(float)
        green_f = green.astype(float)
        blue_f = blue.astype(float)
        
        # NDVI
        ndvi = (nir_f - red_f) / (nir_f + red_f + 1e-8)
        
        # NDMI (Normalized Difference Moisture Index)
        ndmi = (nir_f - green_f) / (nir_f + green_f + 1e-8)
        
        # GNDVI (Green Normalized Difference Vegetation Index)
        gndvi = (nir_f - green_f) / (nir_f + green_f + 1e-8)
        
        return {
            "ndvi_mean": float(np.mean(ndvi)),
            "ndvi_std": float(np.std(ndvi)),
            "ndmi_mean": float(np.mean(ndmi)),
            "gndvi_mean": float(np.mean(gndvi)),
            "stress_areas": float(np.sum(ndvi < 0.3) / ndvi.size * 100)
        }

detector = CropDiseaseDetector()

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
        "service": "Satellite-Based Crop Disease Detection",
        "version": "1.0.0",
        "endpoints": [
            "/detect",
            "/plots",
            "/detections",
            "/alerts",
            "/health"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "crop-disease-detection"}

@app.post("/plots")
async def register_farm_plot(
    farmer_name: str,
    county: str,
    latitude: float,
    longitude: float,
    area_hectares: float,
    crop_type: str,
    db: Session = None
):
    """
    Register a new farm plot for monitoring
    """
    if db is None:
        db = SessionLocal()
    
    if crop_type not in detector.crop_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid crop type. Choose from: {', '.join(detector.crop_types)}"
        )
    
    plot_id = f"PLOT-{county.replace(' ', '-')}-{uuid.uuid4().hex[:8]}"
    
    plot = FarmPlot(
        plot_id=plot_id,
        farmer_name=farmer_name,
        county=county,
        latitude=latitude,
        longitude=longitude,
        area_hectares=area_hectares,
        crop_type=crop_type,
        planting_date=datetime.utcnow()
    )
    db.add(plot)
    db.commit()
    db.refresh(plot)
    
    return {
        "plot_id": plot_id,
        "farmer_name": farmer_name,
        "crop_type": crop_type,
        "message": "Farm plot registered successfully"
    }

@app.get("/plots")
async def get_farm_plots(
    county: Optional[str] = None,
    crop_type: Optional[str] = None,
    db: Session = None,
    skip: int = 0,
    limit: int = 100
):
    """
    Get farm plots with optional filtering
    """
    if db is None:
        db = SessionLocal()
    
    query = db.query(FarmPlot)
    
    if county:
        query = query.filter(FarmPlot.county == county)
    if crop_type:
        query = query.filter(FarmPlot.crop_type == crop_type)
    
    plots = query.offset(skip).limit(limit).all()
    return plots

@app.post("/detect")
async def detect_crop_disease(
    plot_id: str,
    file: UploadFile = File(...),
    db: Session = None
):
    """
    Detect crop disease in an uploaded image or satellite data
    """
    if db is None:
        db = SessionLocal()
    
    # Get plot info
    plot = db.query(FarmPlot).filter(FarmPlot.plot_id == plot_id).first()
    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")
    
    try:
        # Read image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert('RGB')
        image_array = np.array(image)
        
        # Detect disease
        detection_result = detector.detect_disease(image_array, crop_type=plot.crop_type)
        
        # Save detection
        detection_id = str(uuid.uuid4())
        detection = DiseaseDetection(
            detection_id=detection_id,
            plot_id=plot_id,
            disease_name=detection_result["disease_name"],
            severity=detection_result["severity"],
            confidence=detection_result["confidence"],
            infected_area_percentage=detection_result["infected_area_percentage"],
            ndvi_score=detection_result["ndvi_score"],
            satellite_source="manual_upload",
            metadata=detection_result["all_predictions"]
        )
        db.add(detection)
        
        # Create alert if disease detected
        if detection_result["disease_name"] != "healthy":
            alert_id = str(uuid.uuid4())
            recommendation = get_disease_recommendation(
                detection_result["disease_name"],
                detection_result["severity"],
                plot.crop_type
            )
            
            alert = DiseaseAlert(
                alert_id=alert_id,
                plot_id=plot_id,
                disease_name=detection_result["disease_name"],
                severity=detection_result["severity"],
                recommended_action=recommendation
            )
            db.add(alert)
        
        db.commit()
        
        return {
            "detection_id": detection_id,
            "plot_id": plot_id,
            "farmer_name": plot.farmer_name,
            "crop_type": plot.crop_type,
            "disease_name": detection_result["disease_name"],
            "severity": detection_result["severity"],
            "confidence": detection_result["confidence"],
            "infected_area_percentage": detection_result["infected_area_percentage"],
            "ndvi_score": detection_result["ndvi_score"],
            "timestamp": datetime.utcnow(),
            "recommendation": get_disease_recommendation(
                detection_result["disease_name"],
                detection_result["severity"],
                plot.crop_type
            )
        }
    
    except Exception as e:
        logger.error(f"Detection error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/detections")
async def get_detections(
    plot_id: Optional[str] = None,
    disease_name: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = None,
    skip: int = 0,
    limit: int = 100
):
    """
    Get disease detections with filtering
    """
    if db is None:
        db = SessionLocal()
    
    query = db.query(DiseaseDetection)
    
    if plot_id:
        query = query.filter(DiseaseDetection.plot_id == plot_id)
    if disease_name:
        query = query.filter(DiseaseDetection.disease_name == disease_name)
    if severity:
        query = query.filter(DiseaseDetection.severity == severity)
    
    detections = query.order_by(DiseaseDetection.detected_at.desc()).offset(skip).limit(limit).all()
    return detections

@app.get("/alerts")
async def get_disease_alerts(
    plot_id: Optional[str] = None,
    severity: Optional[str] = None,
    sent_to_farmer: bool = False,
    db: Session = None,
    skip: int = 0,
    limit: int = 100
):
    """
    Get disease alerts
    """
    if db is None:
        db = SessionLocal()
    
    query = db.query(DiseaseAlert)
    
    if plot_id:
        query = query.filter(DiseaseAlert.plot_id == plot_id)
    if severity:
        query = query.filter(DiseaseAlert.severity == severity)
    
    query = query.filter(DiseaseAlert.sent_to_farmer == sent_to_farmer)
    
    alerts = query.order_by(DiseaseAlert.created_at.desc()).offset(skip).limit(limit).all()
    return alerts

@app.post("/alerts/{alert_id}/send")
async def send_alert(alert_id: str, db: Session = None):
    """
    Mark alert as sent to farmer
    """
    if db is None:
        db = SessionLocal()
    
    alert = db.query(DiseaseAlert).filter(DiseaseAlert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.sent_to_farmer = True
    alert.sent_at = datetime.utcnow()
    db.commit()
    
    return {"alert_id": alert_id, "status": "sent_to_farmer"}

@app.get("/stats")
async def get_statistics(
    county: Optional[str] = None,
    crop_type: Optional[str] = None,
    db: Session = None
):
    """
    Get system statistics
    """
    if db is None:
        db = SessionLocal()
    
    plot_query = db.query(FarmPlot)
    detection_query = db.query(DiseaseDetection)
    alert_query = db.query(DiseaseAlert)
    
    if county:
        plot_query = plot_query.filter(FarmPlot.county == county)
        detection_query = detection_query.filter(FarmPlot.county == county)
    if crop_type:
        plot_query = plot_query.filter(FarmPlot.crop_type == crop_type)
    
    return {
        "total_plots": plot_query.count(),
        "total_detections": detection_query.count(),
        "pending_alerts": alert_query.filter(DiseaseAlert.sent_to_farmer == False).count(),
        "disease_breakdown": {
            disease: detection_query.filter(
                DiseaseDetection.disease_name == disease
            ).count()
            for disease in list(detector.diseases.values())[1:]  # Exclude 'healthy'
        },
        "severity_breakdown": {
            severity: detection_query.filter(
                DiseaseDetection.severity == severity
            ).count()
            for severity in ["low", "moderate", "high", "severe"]
        },
        "avg_infected_area_percentage": float(
            detection_query.with_entities(
                db.func.avg(DiseaseDetection.infected_area_percentage)
            ).scalar() or 0
        ),
        "avg_ndvi_score": float(
            detection_query.with_entities(
                db.func.avg(DiseaseDetection.ndvi_score)
            ).scalar() or 0
        )
    }

def get_disease_recommendation(disease_name: str, severity: str, crop_type: str) -> str:
    """
    Generate treatment recommendations based on disease and crop type
    """
    recommendations = {
        "powdery_mildew": {
            "low": "Apply sulfur-based fungicide or organic neem oil spray",
            "moderate": "Use systemic fungicide (e.g., Metyl Thiophanate) every 7-10 days",
            "high": "Apply copper sulfate or benzimidazole fungicides. Improve air circulation.",
            "severe": "URGENT: Multiple fungicide applications, remove affected leaves, consult agronomist"
        },
        "leaf_rust": {
            "low": "Monitor closely. Early application of leaf protectant fungicides recommended",
            "moderate": "Apply triazole-based fungicide (e.g., Propiconazole) at 7-10 day intervals",
            "high": "Combine multiple fungicides, practice crop rotation, remove infected leaves",
            "severe": "URGENT: Apply emergency fungicide treatment. Consider replanting in affected areas."
        },
        "blight": {
            "low": "Remove infected plant material. Apply preventive mancozeb spray",
            "moderate": "Weekly applications of chlorothalonil or copper-based fungicide required",
            "high": "Intensive fungicide regime. Ensure proper drainage. Reduce plant density.",
            "severe": "CRITICAL: Field may be at risk. Emergency intervention with multiple fungicides required."
        },
        "fusarium_wilt": {
            "low": "Ensure proper sanitation. Avoid overhead watering. Monitor for spread.",
            "moderate": "Apply systemic fungicide (e.g., Carbendazim). Improve soil drainage and aeration.",
            "high": "Consider crop rotation. Remove heavily infected plants. Soil treatment required.",
            "severe": "CRITICAL: Field rotation essential. Consider replanting with resistant varieties."
        }
    }
    
    if disease_name in recommendations:
        return recommendations[disease_name].get(severity, "Consult local agricultural extension office")
    else:
        return f"Disease: {disease_name}. Severity: {severity}. Consult agronomist for tailored advice."

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
