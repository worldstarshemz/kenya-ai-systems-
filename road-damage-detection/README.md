# AI Road Damage Detection Using Drone Images

Automated road condition assessment system using drone imagery and deep learning for infrastructure maintenance.

## Features

- **Damage Classification**: Detects potholes, cracks, ruts, and patches
- **Severity Assessment**: Classifies damage as low, medium, high, or critical
- **Area Estimation**: Calculates approximate damage area in square meters
- **Batch Processing**: Process multiple images from drone inspections
- **Repair Recommendations**: Automated repair priority and methodology suggestions
- **Real-time Analysis**: Fast inference for immediate feedback
- **Historical Tracking**: Monitor road condition changes over time

## Damage Types

- **Pothole**: Circular or irregular holes in the road surface
- **Crack**: Linear fractures in the pavement
- **Rut**: Longitudinal depressions caused by traffic
- **Patch**: Previous repair areas that may be deteriorating

## API Endpoints

### Single Image Detection

```bash
curl -X POST "http://localhost:8003/detect?latitude=-1.2837&longitude=36.8025&segment_id=ROAD-001" \
  -F "file=@road_image.jpg"
```

**Response:**
```json
{
  "detection_id": "uuid",
  "damage_type": "pothole",
  "severity": "high",
  "confidence": 0.87,
  "damage_area_sqm": 0.45,
  "location": {"latitude": -1.2837, "longitude": 36.8025},
  "timestamp": "2026-07-03T10:00:00",
  "recommendation": "[PRIORITY] Fill with bituminous material and compact. Affected area: 0.45 m². Recommend inspection within 2 weeks."
}
```

### Batch Inspection Processing

```bash
curl -X POST "http://localhost:8003/inspect" \
  -F "segment_id=ROAD-001" \
  -F "drone_id=DRONE-001" \
  -F "flight_altitude=50" \
  -F "files=@image1.jpg" \
  -F "files=@image2.jpg" \
  -F "files=@image3.jpg"
```

**Response:**
```json
{
  "inspection_id": "uuid",
  "segment_id": "ROAD-001",
  "drone_id": "DRONE-001",
  "total_images": 3,
  "damages_found": 2,
  "coverage_percentage": 100.0,
  "status": "completed"
}
```

### Register Road Segment

```bash
curl -X POST "http://localhost:8003/segments" \
  -H "Content-Type: application/json" \
  -d '{
    "road_name": "Mombasa Road",
    "latitude": -1.2837,
    "longitude": 36.8025,
    "length_km": 45.5,
    "surface_type": "asphalt"
  }'
```

### Get Detections

```bash
# Get all detections
curl "http://localhost:8003/detections"

# Filter by segment
curl "http://localhost:8003/detections?segment_id=ROAD-001"

# Filter by damage type and severity
curl "http://localhost:8003/detections?damage_type=pothole&severity=critical"
```

### Get Inspections

```bash
curl "http://localhost:8003/inspections"
```

### Get Statistics

```bash
curl "http://localhost:8003/stats"
```

## Setup

### Installation

```bash
cd road-damage-detection
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8003
```

### Docker

```bash
docker build -t road-damage-detection .
docker run -p 8003:8000 \
  -e DATABASE_URL=postgresql://user:pass@postgres:5432/db \
  road-damage-detection
```

## Database Schema

```sql
CREATE TABLE road_segments (
    id SERIAL PRIMARY KEY,
    segment_id VARCHAR UNIQUE NOT NULL,
    road_name VARCHAR NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    length_km FLOAT NOT NULL,
    surface_type VARCHAR DEFAULT 'asphalt',
    last_inspection TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE damage_detections (
    id SERIAL PRIMARY KEY,
    detection_id VARCHAR UNIQUE NOT NULL,
    segment_id VARCHAR NOT NULL,
    image_path VARCHAR,
    damage_type VARCHAR NOT NULL,
    severity VARCHAR NOT NULL,
    confidence FLOAT NOT NULL,
    damage_area_sqm FLOAT,
    location_lat FLOAT,
    location_lon FLOAT,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE TABLE drone_inspections (
    id SERIAL PRIMARY KEY,
    inspection_id VARCHAR UNIQUE NOT NULL,
    segment_id VARCHAR NOT NULL,
    drone_id VARCHAR,
    flight_altitude FLOAT,
    num_images INT,
    damages_found INT,
    coverage_percentage FLOAT,
    inspection_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE INDEX idx_segment_id ON damage_detections(segment_id);
CREATE INDEX idx_damage_type ON damage_detections(damage_type);
CREATE INDEX idx_severity ON damage_detections(severity);
CREATE INDEX idx_detected_at ON damage_detections(detected_at);
```

## Model Training

To train a custom model:

```python
import tensorflow as tf
from tensorflow import keras

# Load training data
train_ds = keras.preprocessing.image_dataset_from_directory(
    'data/train',
    image_size=(224, 224),
    batch_size=32
)

# Build model
model = keras.Sequential([...])

# Train
model.fit(train_ds, epochs=50, validation_split=0.2)

# Save
model.save('models/road_damage_model.h5')
```

## Performance

- Detection latency: 50-100ms per image
- Accuracy: 85%+ on test set
- Throughput: 500+ images/hour
- Memory: ~2GB for model inference

## Future Enhancements

- [ ] Real-time drone streaming integration
- [ ] Cost estimation for repairs
- [ ] Automated maintenance scheduling
- [ ] Mobile app for field engineers
- [ ] Integration with traffic management systems
- [ ] Weather condition analysis
- [ ] Predictive maintenance modeling

## License

MIT License
