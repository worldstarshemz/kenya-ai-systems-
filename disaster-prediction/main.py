from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import numpy as np
import joblib
import os
from dotenv import load_dotenv
import logging

load_dotenv()

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://kenya_user:kenya_secure_pass_2024@localhost:5432/kenya_ai_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class DisasterPrediction(Base):
    __tablename__ = "disaster_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    location = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    disaster_type = Column(String)  # flood, earthquake, drought, landslide
    risk_score = Column(Float)  # 0-100
    confidence = Column(Float)
    prediction_date = Column(DateTime, default=datetime.utcnow)
    actual_outcome = Column(String, nullable=True)
    metadata = Column(JSON)

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI App
app = FastAPI(
    title="AI Disaster Prediction System for Kenya",
    description="Real-time disaster risk assessment and early warning",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ML Model (placeholder - would load trained model in production)
class DisasterPredictor:
    def __init__(self):
        self.model = None
        self.risk_thresholds = {
            "flood": {"low": 30, "high": 70},
            "earthquake": {"low": 40, "high": 80},
            "drought": {"low": 35, "high": 75},
            "landslide": {"low": 25, "high": 65}
        }
    
    def predict(self, latitude: float, longitude: float, rainfall: float, 
                soil_moisture: float, temperature: float, elevation: float) -> dict:
        """
        Predict disaster risk based on environmental factors
        """
        # Normalize inputs
        features = np.array([[latitude, longitude, rainfall, soil_moisture, temperature, elevation]])
        
        # Risk scoring logic
        flood_risk = self._calculate_flood_risk(rainfall, soil_moisture, latitude)
        drought_risk = self._calculate_drought_risk(rainfall, soil_moisture, temperature)
        earthquake_risk = self._calculate_earthquake_risk(latitude, longitude)
        landslide_risk = self._calculate_landslide_risk(elevation, rainfall, soil_moisture)
        
        return {
            "flood_risk": float(flood_risk),
            "drought_risk": float(drought_risk),
            "earthquake_risk": float(earthquake_risk),
            "landslide_risk": float(landslide_risk),
            "primary_threat": self._identify_primary_threat(
                flood_risk, drought_risk, earthquake_risk, landslide_risk
            )
        }
    
    def _calculate_flood_risk(self, rainfall, soil_moisture, latitude):
        # Higher rainfall + higher soil moisture = higher flood risk
        risk = (rainfall * 0.6 + soil_moisture * 0.4) * (1 + latitude/100)
        return min(100, max(0, risk))
    
    def _calculate_drought_risk(self, rainfall, soil_moisture, temperature):
        # Lower rainfall + lower soil moisture + higher temp = higher drought risk
        risk = (100 - rainfall) * 0.4 + (100 - soil_moisture) * 0.4 + (temperature/50) * 0.2
        return min(100, max(0, risk))
    
    def _calculate_earthquake_risk(self, latitude, longitude):
        # Simplified: certain regions have higher risk
        # Kenya's rift valley is seismically active
        if -1 < latitude < 4 and 36 < longitude < 41:
            risk = 55 + np.random.randint(-15, 15)
        else:
            risk = 30 + np.random.randint(-10, 10)
        return min(100, max(0, risk))
    
    def _calculate_landslide_risk(self, elevation, rainfall, soil_moisture):
        # Higher elevation + rainfall + soil moisture = higher landslide risk
        risk = (elevation/3000) * 0.4 + (rainfall * 0.3) + (soil_moisture * 0.3)
        return min(100, max(0, risk))
    
    def _identify_primary_threat(self, flood, drought, earthquake, landslide):
        threats = {
            "flood": flood,
            "drought": drought,
            "earthquake": earthquake,
            "landslide": landslide
        }
        return max(threats, key=threats.get)

predictor = DisasterPredictor()

# Dependency
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
        "service": "AI Disaster Prediction System for Kenya",
        "version": "1.0.0",
        "endpoints": [
            "/predict",
            "/predictions",
            "/predictions/{id}",
            "/health"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "disaster-prediction"}

@app.post("/predict")
async def predict_disaster(
    latitude: float,
    longitude: float,
    rainfall: float,
    soil_moisture: float,
    temperature: float,
    elevation: float,
    location_name: str = "Unknown",
    db: Session = None
):
    """
    Predict disaster risk for a specific location
    
    Parameters:
    - latitude: Location latitude (-90 to 90)
    - longitude: Location longitude (-180 to 180)
    - rainfall: Monthly rainfall in mm (0-500)
    - soil_moisture: Soil moisture percentage (0-100)
    - temperature: Temperature in Celsius
    - elevation: Elevation in meters
    - location_name: Name of the location
    """
    
    # Validate inputs
    if not (-90 <= latitude <= 90):
        raise HTTPException(status_code=400, detail="Invalid latitude")
    if not (-180 <= longitude <= 180):
        raise HTTPException(status_code=400, detail="Invalid longitude")
    
    # Get prediction
    prediction = predictor.predict(latitude, longitude, rainfall, soil_moisture, temperature, elevation)
    
    # Get primary threat and its score
    primary_threat = prediction["primary_threat"]
    risk_score = prediction[f"{primary_threat}_risk"]
    
    # Save to database
    if db is None:
        db = SessionLocal()
    
    db_prediction = DisasterPrediction(
        location=location_name,
        latitude=latitude,
        longitude=longitude,
        disaster_type=primary_threat,
        risk_score=risk_score,
        confidence=0.85,
        metadata={
            "rainfall": rainfall,
            "soil_moisture": soil_moisture,
            "temperature": temperature,
            "elevation": elevation,
            "all_risks": prediction
        }
    )
    db.add(db_prediction)
    db.commit()
    db.refresh(db_prediction)
    
    return {
        "id": db_prediction.id,
        "location": location_name,
        "latitude": latitude,
        "longitude": longitude,
        "primary_threat": primary_threat,
        "risk_score": risk_score,
        "confidence": 0.85,
        "all_risks": prediction,
        "timestamp": db_prediction.prediction_date,
        "recommendation": get_recommendation(primary_threat, risk_score)
    }

@app.get("/predictions")
async def get_predictions(db: Session = None, skip: int = 0, limit: int = 100):
    """
    Get all predictions with pagination
    """
    if db is None:
        db = SessionLocal()
    
    predictions = db.query(DisasterPrediction).offset(skip).limit(limit).all()
    return predictions

@app.get("/predictions/{prediction_id}")
async def get_prediction(prediction_id: int, db: Session = None):
    """
    Get a specific prediction by ID
    """
    if db is None:
        db = SessionLocal()
    
    prediction = db.query(DisasterPrediction).filter(DisasterPrediction.id == prediction_id).first()
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return prediction

@app.get("/stats")
async def get_statistics(db: Session = None):
    """
    Get statistics about predictions
    """
    if db is None:
        db = SessionLocal()
    
    total_predictions = db.query(DisasterPrediction).count()
    disaster_counts = {}
    
    for disaster_type in ["flood", "drought", "earthquake", "landslide"]:
        count = db.query(DisasterPrediction).filter(
            DisasterPrediction.disaster_type == disaster_type
        ).count()
        disaster_counts[disaster_type] = count
    
    avg_risk = db.query(DisasterPrediction).with_entities(
        db.func.avg(DisasterPrediction.risk_score)
    ).scalar() or 0
    
    return {
        "total_predictions": total_predictions,
        "disaster_breakdown": disaster_counts,
        "average_risk_score": float(avg_risk),
        "high_risk_count": db.query(DisasterPrediction).filter(
            DisasterPrediction.risk_score > 70
        ).count()
    }

def get_recommendation(disaster_type: str, risk_score: float) -> str:
    """
    Generate actionable recommendations based on risk
    """
    if risk_score < 30:
        level = "Low"
        action = "Monitor situation"
    elif risk_score < 60:
        level = "Medium"
        action = "Prepare contingency plans"
    else:
        level = "High"
        action = "Issue warning and activate emergency protocols"
    
    recommendations = {
        "flood": f"{level} flood risk - {action}. Evacuate low-lying areas if necessary.",
        "drought": f"{level} drought risk - {action}. Implement water conservation measures.",
        "earthquake": f"{level} earthquake risk - {action}. Ensure buildings meet safety standards.",
        "landslide": f"{level} landslide risk - {action}. Clear drainage systems and stabilize slopes."
    }
    
    return recommendations.get(disaster_type, f"{level} disaster risk - {action}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
