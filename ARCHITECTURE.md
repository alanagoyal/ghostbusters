# Halloween Costume Detection System - Architecture Document

## System Overview

This document describes the technical architecture for a real-time Halloween costume detection and display system that processes video from a DoorBird doorbell camera.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Web Display (React/Vue)                      │  │
│  │  - Real-time costume visualization                        │  │
│  │  - Animation engine                                       │  │
│  │  - Statistics dashboard                                   │  │
│  │  - WebSocket client                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            ▲ │
                            │ │ WebSocket
                            │ ▼
┌─────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Web Server (FastAPI/Flask)                      │  │
│  │  - REST API endpoints                                     │  │
│  │  - WebSocket server                                       │  │
│  │  - Session management                                     │  │
│  │  - Event broadcasting                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ▲ │                                   │
│                            │ ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          Detection Processing Service                     │  │
│  │  - Frame queue manager                                    │  │
│  │  - Detection coordinator                                  │  │
│  │  - Result aggregation                                     │  │
│  │  - State management                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ▲ │                                   │
│                            │ ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Computer Vision Engine                            │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │  │
│  │  │   Person    │  │   Costume    │  │   Confidence   │  │  │
│  │  │  Detection  │─▶│Classification│─▶│   Filtering    │  │  │
│  │  │   (YOLO)    │  │    (CLIP)    │  │   & Tracking   │  │  │
│  │  └─────────────┘  └──────────────┘  └────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            ▲ │
                            │ │ Video Stream
                            │ ▼
┌─────────────────────────────────────────────────────────────────┐
│                       INTEGRATION LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          Video Stream Adapter                             │  │
│  │  - RTSP/HTTP stream handler                               │  │
│  │  - Frame extraction                                       │  │
│  │  - Connection management                                  │  │
│  │  - Retry logic                                            │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            ▲
                            │ RTSP/HTTP
                            │
┌─────────────────────────────────────────────────────────────────┐
│                       HARDWARE LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│                    DoorBird Doorbell Camera                      │
└─────────────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. Hardware Layer

#### DoorBird Doorbell Camera
- **Responsibility**: Capture video feed of visitors at the door
- **Interfaces**: RTSP stream, HTTP API, Motion detection events
- **Configuration**:
  - Stream URL: `rtsp://username:password@doorbird-ip/mpeg/media.amp`
  - Snapshot URL: `http://doorbird-ip/bha-api/image.cgi`

### 2. Integration Layer

#### Video Stream Adapter
**Purpose**: Abstract camera communication and provide reliable video frames

**Components**:
- **Stream Manager**
  - Establishes and maintains RTSP/HTTP connection
  - Handles authentication
  - Implements reconnection logic with exponential backoff

- **Frame Extractor**
  - Decodes video stream
  - Samples frames at configurable rate (1-5 fps)
  - Resizes frames for optimal processing
  - Maintains frame buffer

**Technologies**:
- OpenCV (`cv2.VideoCapture` for RTSP)
- FFmpeg (fallback for stream handling)
- Python `asyncio` for non-blocking I/O

**Key Methods**:
```python
class VideoStreamAdapter:
    def connect(camera_url: str, credentials: dict) -> bool
    def get_frame() -> np.ndarray
    def is_connected() -> bool
    def reconnect() -> bool
    def close()
```

### 3. Application Layer

#### Computer Vision Engine

**Purpose**: Detect people and classify their costumes

**Components**:

1. **Person Detection Module**
   - **Model**: YOLOv8 or YOLOv5
   - **Input**: Raw video frames (640x640 or 1280x1280)
   - **Output**: Bounding boxes of detected persons with confidence scores
   - **Performance**: ~30-50ms per frame on GPU, ~200-400ms on CPU

2. **Costume Classification Module**
   - **Model Options**:
     - **Option A**: CLIP (Zero-shot classification)
       - Pros: No training required, flexible categories
       - Cons: May be less accurate for specific costumes
     - **Option B**: Fine-tuned ResNet/EfficientNet
       - Pros: Higher accuracy with training data
       - Cons: Requires labeled training dataset
   - **Input**: Cropped person images from detection
   - **Output**: Costume category + confidence score
   - **Categories**:
     ```python
     COSTUME_CATEGORIES = [
         "witch", "ghost", "vampire", "zombie",
         "superhero", "princess", "pirate", "skeleton",
         "monster", "animal", "robot", "other"
     ]
     ```

3. **Confidence Filtering & Tracking**
   - Filters low-confidence detections (threshold: 0.6)
   - Tracks persons across frames (simple centroid tracking)
   - Aggregates classifications over multiple frames
   - De-duplicates detections (same person within time window)

**Technologies**:
- PyTorch or TensorFlow
- Ultralytics YOLOv8
- OpenAI CLIP or Hugging Face Transformers
- OpenCV for image preprocessing

**Key Methods**:
```python
class CostumeDetectionEngine:
    def detect_persons(frame: np.ndarray) -> List[BoundingBox]
    def classify_costume(person_crop: np.ndarray) -> CostumeResult
    def process_frame(frame: np.ndarray) -> List[Detection]
    def aggregate_detections(detections: List[Detection]) -> Detection
```

#### Detection Processing Service

**Purpose**: Orchestrate the detection pipeline and manage state

**Responsibilities**:
- Receive frames from Video Stream Adapter
- Queue frames for processing
- Coordinate CV Engine operations
- Aggregate and filter results
- Maintain detection history
- Trigger events for new detections

**Processing Pipeline**:
```
Frame Input → Frame Queue → Person Detection →
Costume Classification → Confidence Filtering →
Deduplication → Event Emission → Result Storage
```

**State Management**:
- Active detections (last 30 seconds)
- Detection history (entire session)
- Statistics (counts, most popular, etc.)
- Processing metrics (FPS, latency)

**Technologies**:
- Python `asyncio` for concurrent processing
- Queue for frame buffering
- SQLite or Redis for temporary storage

**Key Methods**:
```python
class DetectionProcessor:
    async def process_video_stream()
    async def handle_frame(frame: np.ndarray)
    def deduplicate(detection: Detection) -> bool
    def update_statistics(detection: Detection)
    async def emit_detection(detection: Detection)
```

#### Web Server

**Purpose**: Provide HTTP API and WebSocket communication

**API Endpoints**:

**REST API**:
- `GET /api/health` - Health check
- `GET /api/detections` - Get recent detections
- `GET /api/statistics` - Get session statistics
- `GET /api/stream/status` - Camera stream status
- `POST /api/settings` - Update configuration

**WebSocket**:
- `/ws/detections` - Real-time detection stream
- Event types:
  - `new_detection` - New costume detected
  - `statistics_update` - Updated stats
  - `status_update` - System status change

**Technologies**:
- FastAPI (recommended) or Flask
- Socket.IO or native WebSockets
- CORS middleware for web access
- Pydantic for data validation

**Data Models**:
```python
class Detection:
    id: str
    timestamp: datetime
    costume_type: str
    confidence: float
    bbox: BoundingBox
    thumbnail: Optional[str]  # base64 encoded

class Statistics:
    total_visitors: int
    costume_counts: Dict[str, int]
    most_popular: str
    detections_per_hour: float
```

### 4. Client Layer

#### Web Display Application

**Purpose**: Visualize detections in real-time with engaging animations

**Components**:

1. **Real-time Display View**
   - Large, prominent costume display
   - Smooth entry/exit animations
   - Costume icon/illustration
   - Confidence indicator
   - Timestamp

2. **Statistics Dashboard**
   - Total visitor count
   - Costume breakdown (pie chart or bar chart)
   - Timeline of detections
   - Current detection rate

3. **Connection Manager**
   - WebSocket connection handling
   - Reconnection logic
   - Connection status indicator
   - Offline mode handling

**UI/UX Design**:
- Dark theme (Halloween aesthetic)
- Orange/purple color scheme
- Large, readable fonts (viewable from distance)
- Smooth animations (fade, slide, scale)
- Responsive design

**Technologies**:
- React with TypeScript or Vue.js
- TailwindCSS or styled-components
- Framer Motion or React Spring (animations)
- Socket.IO client or native WebSocket
- Chart.js or Recharts (statistics visualization)

**Key Components**:
```typescript
// React example
interface CostumeDisplayProps {
  detection: Detection;
  onAnimationComplete: () => void;
}

function CostumeDisplay({ detection }: CostumeDisplayProps)
function StatisticsDashboard({ stats }: StatisticsProps)
function ConnectionStatus({ connected }: ConnectionProps)
function DetectionHistory({ history }: HistoryProps)
```

## Data Flow

### Detection Flow

1. **Frame Capture** (1-5 fps)
   ```
   DoorBird Camera → Video Stream Adapter → Frame Queue
   ```

2. **Processing** (~500ms - 2s per frame)
   ```
   Frame Queue → Person Detection → Costume Classification →
   Confidence Filtering → Deduplication
   ```

3. **Broadcasting** (<100ms)
   ```
   Detection Result → Web Server → WebSocket →
   Connected Clients → UI Update
   ```

4. **Storage** (optional)
   ```
   Detection Result → Database/Cache → Statistics Update
   ```

### Event Flow

```
Motion at Door → Frame Captured → Person Detected →
Costume Classified → High Confidence? →
Not Recent Duplicate? → Emit Event →
Broadcast to Clients → Update Display →
Update Statistics
```

## Deployment Architecture

### Option 1: Single Machine Deployment (Recommended)

```
┌─────────────────────────────────────────────┐
│         Local Server/Laptop/Pi              │
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │  Docker Container (Optional)          │ │
│  │                                       │ │
│  │  ┌─────────────┐  ┌───────────────┐ │ │
│  │  │   Backend   │  │   Frontend    │ │ │
│  │  │  (Python)   │  │  (Static)     │ │ │
│  │  │             │  │               │ │ │
│  │  │  - FastAPI  │  │  - React App  │ │ │
│  │  │  - CV       │  │  - Nginx      │ │ │
│  │  │  - WebSocket│  │               │ │ │
│  │  └─────────────┘  └───────────────┘ │ │
│  └───────────────────────────────────────┘ │
│                                             │
│  Port 8000: Backend API                     │
│  Port 3000: Frontend                        │
└─────────────────────────────────────────────┘
           │
           │ RTSP/HTTP
           ▼
    ┌──────────────┐
    │   DoorBird   │
    │    Camera    │
    └──────────────┘
```

**Requirements**:
- OS: Linux/macOS/Windows
- RAM: 8GB minimum, 16GB recommended
- CPU: 4+ cores (or GPU for faster processing)
- Storage: 10GB minimum
- Network: Stable local network connection

### Option 2: Distributed Deployment

```
┌──────────────────┐      ┌─────────────────┐
│  Processing      │      │   Web Server    │
│  Server          │◄────►│   (Frontend +   │
│  (CV Engine)     │      │   API)          │
│                  │      │                 │
│  - Heavy compute │      │  - Lightweight  │
│  - GPU optional  │      │  - Many clients │
└──────────────────┘      └─────────────────┘
         │
         │ RTSP/HTTP
         ▼
  ┌──────────────┐
  │   DoorBird   │
  │    Camera    │
  └──────────────┘
```

## Technology Stack Details

### Backend Stack

```python
# requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-socketio==5.10.0
opencv-python==4.8.1
torch==2.1.0
ultralytics==8.0.200  # YOLOv8
transformers==4.35.0  # For CLIP
pillow==10.1.0
numpy==1.24.3
pydantic==2.5.0
python-multipart==0.0.6
aiohttp==3.9.0
redis==5.0.1  # Optional
```

### Frontend Stack

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "socket.io-client": "^4.6.1",
    "framer-motion": "^10.16.0",
    "tailwindcss": "^3.3.0",
    "chart.js": "^4.4.0",
    "react-chartjs-2": "^5.2.0",
    "axios": "^1.6.0"
  }
}
```

## Configuration Management

### Environment Variables

```bash
# .env
DOORBIRD_IP=192.168.1.100
DOORBIRD_USERNAME=admin
DOORBIRD_PASSWORD=your_password
RTSP_URL=rtsp://${DOORBIRD_USERNAME}:${DOORBIRD_PASSWORD}@${DOORBIRD_IP}/mpeg/media.amp

# Processing
FRAME_RATE=2  # frames per second to process
DETECTION_THRESHOLD=0.6
DEDUP_WINDOW_SECONDS=30

# Models
YOLO_MODEL=yolov8n.pt  # nano model for speed
USE_GPU=true

# Server
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=*

# Storage
REDIS_URL=redis://localhost:6379
SESSION_DURATION_HOURS=6
```

## Security Considerations

1. **Privacy**
   - No permanent video storage
   - No facial recognition
   - Session-based data only
   - Clear privacy notice for visitors

2. **Network Security**
   - Run on isolated local network
   - Use HTTPS if exposing publicly
   - Secure DoorBird credentials
   - Rate limiting on API endpoints

3. **Data Protection**
   - Encrypt credentials in configuration
   - Clear data after session
   - No cloud uploads
   - Local processing only

## Performance Optimization

### Strategies

1. **Model Optimization**
   - Use smaller YOLO model (nano or small)
   - Quantize models for faster inference
   - Use GPU if available (CUDA)
   - Batch processing when possible

2. **Frame Processing**
   - Skip frames (process every Nth frame)
   - Reduce frame resolution
   - Use motion detection to trigger processing
   - Async processing pipeline

3. **Caching**
   - Cache model weights in memory
   - Redis for detection deduplication
   - Browser caching for static assets

4. **Network**
   - Compress WebSocket messages
   - Debounce statistics updates
   - Use CDN for frontend assets (optional)

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Frame Processing | <2s per frame | 95th percentile |
| Detection to Display | <3s end-to-end | 95th percentile |
| WebSocket Latency | <100ms | Average |
| Memory Usage | <4GB | Peak |
| CPU Usage | <80% | Average |

## Error Handling & Resilience

### Failure Modes

1. **Camera Disconnection**
   - Automatic reconnection with backoff
   - Display "Waiting for camera..." status
   - Log connection attempts

2. **Model Inference Failure**
   - Catch and log exceptions
   - Skip problematic frames
   - Fallback to "Unknown" costume
   - Alert on repeated failures

3. **WebSocket Disconnection**
   - Client auto-reconnect
   - Queue messages during disconnection
   - Sync state on reconnection

4. **Resource Exhaustion**
   - Frame queue size limits
   - Request rate limiting
   - Memory monitoring and alerts
   - Graceful degradation

## Monitoring & Logging

### Logging Strategy

```python
# Log levels
INFO: Detection events, connections, normal operations
WARNING: Low confidence detections, reconnections
ERROR: Processing failures, connection failures
DEBUG: Frame processing details, performance metrics
```

### Metrics to Track

- Frames processed per second
- Detection latency (95th percentile)
- Active WebSocket connections
- Memory and CPU usage
- Camera connection status
- Detection accuracy (confidence scores)

### Health Checks

- `/api/health` endpoint
- Camera stream status
- Model loaded status
- WebSocket server status
- Resource utilization

## Testing Strategy

### Unit Tests
- Video stream adapter connection logic
- Detection deduplication logic
- Costume classification with sample images
- API endpoint responses

### Integration Tests
- End-to-end frame processing pipeline
- WebSocket message flow
- Database operations
- Camera API integration

### Performance Tests
- Load testing (multiple concurrent viewers)
- Frame processing throughput
- Memory leak detection
- Extended runtime stability

### User Acceptance Testing
- Test with real costume images
- Verify display animations
- Check statistics accuracy
- Test on Halloween night (dry run)

## Backup & Contingency Plans

1. **Manual Override**
   - Admin interface to manually add detections
   - Useful if CV fails for certain costumes

2. **Degraded Mode**
   - Simple person counter if classification fails
   - Display generic "visitor" instead of costume type

3. **Offline Fallback**
   - Pre-recorded detections for demo
   - Static display if streaming fails

## Future Enhancements

### Phase 2 Features
- Multi-camera support
- Cloud deployment option
- Mobile app for display
- Sound effects triggered by detections
- Photo booth mode (save best shots)
- Social media integration
- Voting system for costumes
- Historical data analysis
- Integration with smart lights/decorations

### Technical Improvements
- Model fine-tuning with collected data
- Active learning for better accuracy
- Edge deployment (TPU/Neural Compute Stick)
- Kubernetes deployment
- Advanced tracking algorithms
- 3D pose estimation for better classification

## References

### DoorBird Documentation
- API: https://www.doorbird.com/downloads/api_lan.pdf
- RTSP Stream: `rtsp://[user]:[pass]@[ip]/mpeg/media.amp`

### ML Models
- YOLOv8: https://github.com/ultralytics/ultralytics
- CLIP: https://github.com/openai/CLIP
- MediaPipe: https://google.github.io/mediapipe/

### Frameworks
- FastAPI: https://fastapi.tiangolo.com/
- Socket.IO: https://socket.io/
- React: https://react.dev/
