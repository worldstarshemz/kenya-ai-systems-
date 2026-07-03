# Kenya Smart City Digital Twin

A real-time 3D city simulation platform with IoT integration for Nairobi and other Kenyan cities.

## Features

- **3D City Visualization**: Interactive 3D models of city districts
- **Real-time IoT Integration**: Connect and monitor sensors across the city
- **Asset Management**: Track roads, buildings, utilities, and infrastructure
- **Traffic Monitoring**: Real-time traffic events and congestion tracking
- **Sensor Analytics**: Air quality, temperature, water levels, power consumption
- **Live Data Streaming**: WebSocket support for real-time updates
- **District Management**: Create and manage multiple city districts

## API Endpoints

### City Overview

```bash
curl "http://localhost:8002/city/overview"
```

**Response:**
```json
{
  "districts": 5,
  "total_population": 4500000,
  "assets": 1250,
  "sensor_count": 450,
  "asset_breakdown": {
    "road": 350,
    "building": 400,
    "traffic_light": 250,
    "sensor": 450
  },
  "health_status": 87.5
}
```

### Create District

```bash
curl -X POST "http://localhost:8002/districts?name=Westlands&latitude=-1.2837&longitude=36.8025&area_sqkm=12.5&population=250000"
```

### Get Districts

```bash
curl "http://localhost:8002/districts"
```

### Get District 3D Data

```bash
curl "http://localhost:8002/districts/1/3d"
```

### Register Asset

```bash
curl -X POST "http://localhost:8002/assets?district_id=1&asset_type=road&name=Kenyatta%20Avenue&latitude=-1.2837&longitude=36.8025"
```

### Get Assets

```bash
curl "http://localhost:8002/assets?asset_type=road&status=operational"
```

### Record Sensor Reading

```bash
curl -X POST "http://localhost:8002/sensors/reading?asset_id=1&sensor_type=air_quality&value=85.5&unit=AQI"
```

### Get Latest Sensor Readings

```bash
curl "http://localhost:8002/sensors/latest/1"
```

### Report Traffic Event

```bash
curl -X POST "http://localhost:8002/traffic/event" \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Tom Mboya Street",
    "latitude": -1.2838,
    "longitude": 36.8025,
    "event_type": "congestion",
    "severity": 4,
    "description": "Heavy traffic during rush hour"
  }'
```

### Get Active Traffic Events

```bash
curl "http://localhost:8002/traffic/active"
```

### Resolve Traffic Event

```bash
curl -X PATCH "http://localhost:8002/traffic/event/1/resolve"
```

### Get Statistics

```bash
curl "http://localhost:8002/stats"
```

### WebSocket Live Data

```javascript
const ws = new WebSocket('ws://localhost:8002/ws/live-data');

ws.onopen = () => {
  ws.send(JSON.stringify({type: 'subscribe', channel: 'city-data'}));
};

ws.onmessage = (event) => {
  console.log('Live data:', JSON.parse(event.data));
};
```

## Setup

### Installation

```bash
cd smart-city-twin
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8002
```

### Docker

```bash
docker build -t smart-city-twin .
docker run -p 8002:8000 \
  -e DATABASE_URL=postgresql://user:pass@postgres:5432/db \
  smart-city-twin
```

## Database Schema

```sql
CREATE TABLE city_districts (
    id SERIAL PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    area_sqkm FLOAT NOT NULL,
    population INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE city_assets (
    id SERIAL PRIMARY KEY,
    district_id INT NOT NULL,
    asset_type VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    status VARCHAR DEFAULT 'operational',
    condition_score FLOAT DEFAULT 100,
    last_maintenance TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sensor_readings (
    id SERIAL PRIMARY KEY,
    asset_id INT NOT NULL,
    sensor_type VARCHAR NOT NULL,
    value FLOAT NOT NULL,
    unit VARCHAR NOT NULL,
    reading_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE TABLE traffic_events (
    id SERIAL PRIMARY KEY,
    location VARCHAR NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    event_type VARCHAR NOT NULL,
    severity INT NOT NULL,
    description TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);
```

## 3D Visualization Integration

For 3D visualization, integrate with Three.js:

```javascript
import * as THREE from 'three';

// Fetch district 3D data
const response = await fetch('/districts/1/3d');
const data = await response.json();

// Create 3D scene
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);

data.geometries.forEach(geo => {
  const geometry = new THREE.BoxGeometry(0.1, 0.1, 0.1);
  const color = new THREE.Color(geo.color);
  const material = new THREE.MeshBasicMaterial({ color });
  const mesh = new THREE.Mesh(geometry, material);
  
  mesh.position.set(geo.position.x, geo.position.y, geo.position.z);
  scene.add(mesh);
});
```

## Performance

- Asset query: < 50ms
- Sensor ingestion: 5,000+ readings/second
- 3D rendering: 60 FPS (with optimization)
- WebSocket latency: < 100ms

## Future Enhancements

- [ ] Advanced 3D rendering with Cesium.js
- [ ] Machine learning for traffic prediction
- [ ] Smart grid integration
- [ ] Water management system
- [ ] Waste management tracking
- [ ] Public transportation simulation
- [ ] Mobile app for citizens

## License

MIT License
