# Satellite-Based Crop Disease Detection

AI-powered agricultural disease detection system using satellite imagery and deep learning for early warning and crop management.

## Features

- **Multi-disease Detection**: Identifies powdery mildew, leaf rust, blight, fusarium wilt, and septoria
- **Severity Classification**: Assesses disease severity as low, moderate, high, or severe
- **NDVI Analysis**: Normalized Difference Vegetation Index for crop health monitoring
- **Satellite Integration**: Compatible with Sentinel-2 and Landsat-8 multispectral data
- **Farmer Alerts**: Automated alerts with treatment recommendations
- **Multispectral Analysis**: Support for advanced remote sensing indices
- **County-level Monitoring**: Track disease patterns across regions

## Supported Diseases

- **Powdery Mildew**: Fungal infection causing white coating on leaves
- **Leaf Rust**: Orange/brown pustules on leaf undersides
- **Blight**: Rapid leaf and stem necrosis
- **Fusarium Wilt**: Vascular wilt disease
- **Septoria**: Circular lesions with dark margins

## API Endpoints

### Register Farm Plot

```bash
curl -X POST "http://localhost:8004/plots" \
  -H "Content-Type: application/json" \
  -d '{
    "farmer_name": "John Kamau",
    "county": "Kiambu",
    "latitude": -1.2637,
    "longitude": 36.8025,
    "area_hectares": 2.5,
    "crop_type": "maize"
  }'
```

**Response:**
```json
{
  "plot_id": "PLOT-Kiambu-a1b2c3d4",
  "farmer_name": "John Kamau",
  "crop_type": "maize",
  "message": "Farm plot registered successfully"
}
```

### Get Farm Plots

```bash
# Get all plots
curl "http://localhost:8004/plots"

# Filter by county
curl "http://localhost:8004/plots?county=Kiambu"

# Filter by crop type
curl "http://localhost:8004/plots?crop_type=maize"
```

### Detect Disease

```bash
curl -X POST "http://localhost:8004/detect" \
  -F "plot_id=PLOT-Kiambu-a1b2c3d4" \
  -F "file=@field_image.jpg"
```

**Response:**
```json
{
  "detection_id": "uuid",
  "plot_id": "PLOT-Kiambu-a1b2c3d4",
  "farmer_name": "John Kamau",
  "crop_type": "maize",
  "disease_name": "leaf_rust",
  "severity": "high",
  "confidence": 0.89,
  "infected_area_percentage": 35.2,
  "ndvi_score": 0.45,
  "timestamp": "2026-07-03T10:00:00",
  "recommendation": "Apply triazole-based fungicide (e.g., Propiconazole) at 7-10 day intervals"
}
```

### Get Detections

```bash
# All detections
curl "http://localhost:8004/detections"

# By plot
curl "http://localhost:8004/detections?plot_id=PLOT-Kiambu-a1b2c3d4"

# By disease
curl "http://localhost:8004/detections?disease_name=leaf_rust"

# By severity
curl "http://localhost:8004/detections?severity=high"
```

### Get Alerts

```bash
# Get pending alerts
curl "http://localhost:8004/alerts?sent_to_farmer=false"

# Get alerts for specific plot
curl "http://localhost:8004/alerts?plot_id=PLOT-Kiambu-a1b2c3d4"

# Get critical alerts
curl "http://localhost:8004/alerts?severity=severe"
```

### Send Alert to Farmer

```bash
curl -X POST "http://localhost:8004/alerts/alert-uuid/send"
```

### Get Statistics

```bash
# Overall stats
curl "http://localhost:8004/stats"

# By county
curl "http://localhost:8004/stats?county=Kiambu"

# By crop type
curl "http://localhost:8004/stats?crop_type=maize"
```

## Setup

### Installation

```bash
cd crop-disease-detection
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8004
```

### Docker

```bash
docker build -t crop-disease-detection .
docker run -p 8004:8000 \
  -e DATABASE_URL=postgresql://user:pass@postgres:5432/db \
  crop-disease-detection
```

## Database Schema

```sql
CREATE TABLE farm_plots (
    id SERIAL PRIMARY KEY,
    plot_id VARCHAR UNIQUE NOT NULL,
    farmer_name VARCHAR NOT NULL,
    county VARCHAR NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    area_hectares FLOAT NOT NULL,
    crop_type VARCHAR NOT NULL,
    planting_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE crop_disease_detections (
    id SERIAL PRIMARY KEY,
    detection_id VARCHAR UNIQUE NOT NULL,
    plot_id VARCHAR NOT NULL,
    disease_name VARCHAR NOT NULL,
    severity VARCHAR NOT NULL,
    confidence FLOAT NOT NULL,
    infected_area_percentage FLOAT,
    ndvi_score FLOAT,
    satellite_source VARCHAR,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE TABLE satellite_images (
    id SERIAL PRIMARY KEY,
    image_id VARCHAR UNIQUE NOT NULL,
    plot_id VARCHAR NOT NULL,
    source VARCHAR,
    acquisition_date TIMESTAMP,
    cloud_coverage FLOAT,
    resolution_m FLOAT,
    bands JSONB,
    stored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE disease_alerts (
    id SERIAL PRIMARY KEY,
    alert_id VARCHAR UNIQUE NOT NULL,
    plot_id VARCHAR NOT NULL,
    disease_name VARCHAR NOT NULL,
    severity VARCHAR NOT NULL,
    recommended_action TEXT,
    sent_to_farmer BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_plot_id ON farm_plots(plot_id);
CREATE INDEX idx_county ON farm_plots(county);
CREATE INDEX idx_crop_type ON farm_plots(crop_type);
CREATE INDEX idx_disease_name ON crop_disease_detections(disease_name);
CREATE INDEX idx_severity ON crop_disease_detections(severity);
```

## Integration with Satellite Services

### Sentinel-2 Data

```python
from sentinelhub import SentinelHubRequest, DataCollection, bbox_to_dimensions

# Fetch Sentinel-2 image
config = SHConfig()
bbox = BBox(bbox=[36.8, -1.3, 36.9, -1.2], crs=CRS.WGS84)

request = SentinelHubRequest(
    data_collection=DataCollection.SENTINEL2_L2A,
    bbox=bbox,
    size=bbox_to_dimensions(bbox, resolution=10),
    time_interval=("2026-06-01", "2026-06-30"),
    data_folder="satellite_data"
)

response = request.get_data()
```

## Disease Management Recommendations

The system provides crop-specific, disease-specific, and severity-specific recommendations:

- **Low Severity**: Preventive measures and monitoring
- **Moderate Severity**: Regular fungicide applications
- **High Severity**: Intensive treatment and cultural practices
- **Severe**: Emergency intervention, possible replanting

## Performance

- Detection latency: 100-200ms
- NDVI calculation: 50-100ms per image
- Accuracy: 82%+ on validation set
- Throughput: 200+ images/hour

## Future Enhancements

- [ ] Real-time Sentinel-2 imagery integration
- [ ] Pest detection (locusts, armyworms, etc.)
- [ ] Yield prediction modeling
- [ ] SMS alerts to farmers in Swahili/local languages
- [ ] Mobile app for farmers
- [ ] Weather-based treatment timing recommendations
- [ ] Market price integration for economic impact analysis

## License

MIT License
