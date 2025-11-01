# Doorstep Costume Classifier — System Specification

## 1. Goal

Build a small edge computer vision system that:

- Watches live video from the existing DoorBird doorbell camera on Halloween night
- Detects when a person shows up
- Classifies their costume with open-ended description (e.g., "witch with purple hat", "skeleton with glowing bones", "homemade cardboard robot")
- Logs each sighting (costume description, timestamp, confidence) to a Supabase database
- Shows a live dashboard on a public Next.js site (hosted on Vercel) using Supabase Realtime
- Operates headless over SSH (no keyboard/mouse/monitor on the Pi)

## 2. Physical / Hardware Setup

### 2.1 Hardware List

| Component | Specifications | Purpose |
|-----------|---------------|---------|
| **Raspberry Pi 5** | 8GB RAM, 2.4GHz 64-bit quad-core CPU | Main compute node for Linux, Python, OpenCV, and ML models |
| **128GB EVO+ microSD card** | Pre-loaded with Raspberry Pi OS | Storage for OS, code, logs, and blurred thumbnails |
| **USB microSD card reader** | Standard USB reader | For initial OS configuration |
| **CanaKit Turbine Black Case** | For Raspberry Pi 5 | Enclosure |
| **CanaKit Low Noise Bearing System Fan** | With Mega Black Anodized Heatsink | Cooling during continuous inference |
| **CanaKit 45W PD Power Supply** | For Raspberry Pi 5 | Stable 5V power with current headroom |
| **2x 6ft display cables** | Up to 4K@60 support | Available for debugging (not required for normal operation) |

### 2.2 Camera

- **DoorBird doorbell system** (already installed)
  - Acts as the only camera
  - Exposes an RTSP video stream on the local network
  - No separate webcam required

### 2.3 Networking Model

- DoorBird and Raspberry Pi 5 are on the same LAN (home Wi-Fi / ethernet network)
- Pi connects to DoorBird's RTSP feed over LAN
- Pi connects to Supabase over the internet for logging events

### 2.4 Physical Deployment

- Pi 5 lives indoors near power and (ideally) ethernet or strong Wi-Fi
- No new sensors, no soldering required
- DoorBird remains mounted at the door as normal

## 3. Access / Control Model

### 3.1 Headless Operation (SSH)

**No local peripherals:**
- NO keyboard, mouse, or monitor connected to Raspberry Pi
- All interaction via SSH over network

**Pre-boot configuration:**
Configure the Pi's OS image before first boot to:
- Enable SSH
- Join home Wi-Fi
- Set hostname (e.g., `halloween-pi`)
- Create username/password

**Access method:**
```bash
ssh <username>@halloween-pi.local
```

All development, updates, and logs are handled via SSH terminal sessions.

## 4. High-Level Architecture

```
[DoorBird Camera]
    |
    | (RTSP video stream over local network)
    v
[Raspberry Pi 5]
    - Captures frames from RTSP
    - Runs person detection (YOLO)
    - Detects ALL people in frame (handles multiple people)
    - Crops each detected person individually
    - Sends each cropped person image to Baseten API for costume classification
    - Baseten runs vision-language model and returns description
    - Blurs faces before saving any thumbnails (privacy)
    - Posts separate {description, confidence, timestamp} entry per person to Supabase
    |
    | (HTTPS)
    v
[Supabase]
    - Postgres table `person_detections`
    - Row-level inserts from Pi (one per detected person)
    - Supabase Realtime broadcasts inserts
    |
    | (Realtime websocket)
    v
[Next.js app on Vercel]
    - Listens to Supabase Realtime channel
    - Live charts of costume counts
    - Timeline of arrivals
    - Leaderboard of most common costumes
```

## 5. Raspberry Pi Software Responsibilities

### 5.1 RTSP Capture

- Use OpenCV (`cv2.VideoCapture(rtsp_url)`) to open the DoorBird stream
- RTSP URL format:
  ```
  rtsp://<doorbird_user>:<doorbird_password>@<doorbird_ip>/mpeg/media.amp
  ```
- Obtain `<doorbird_ip>` via DoorBird IP Finder / router
- Continuously read frames from the URL

### 5.2 Motion / Presence Detection

- No need to analyze every frame
- Loop captures ~1 frame per second (or only when motion detected - optional optimization)
- Frames sent to lightweight person detector (YOLOv8n or similar)

### 5.3 Person Detection

**Dual-Pass Detection Strategy:**

The system uses a sophisticated dual-pass detection approach to handle both regular costumes and inflatable costumes:

**Pass 1: Standard Person Detection**
- Run YOLOv8n with `class=0` (person) to detect people in frame
- Apply ROI (Region of Interest) filtering to doorstep area only (x: 0.0-0.7, y: 0.0-1.0)
- This focuses detection on the left 70% of frame, preventing false positives from street/background

**Pass 2: Inflatable Costume Detection**
- YOLOv8n often misclassifies inflatable costumes (T-Rex, dinosaurs) as objects instead of people
- Second pass detects potential inflatables using YOLO classes:
  - Class 2: car (inflatable cars, vehicles)
  - Class 14: bird (inflatable birds, flamingos)
  - Class 16: dog (inflatable dogs)
  - Class 17: cat (inflatable cats)
- Same ROI filtering applied
- Baseten vision model validates whether detection is actually a costume (filters false positives)

**Multi-Person Detection:**
- System detects ALL people in frame simultaneously
- Creates separate database entries for each detected person
- Handles groups of trick-or-treaters arriving together

**Detection Requirements:**
- Consecutive frame detection: Requires detection in 2 consecutive frames before capturing
- Cooldown period: 30-second cooldown between captures to prevent duplicate detections
- Frame processing rate: ~1 frame per second (processes every 30th frame)

### 5.4 Costume Classification

**Vision-Language Model via Baseten:**

The Pi sends cropped person images to a Baseten-hosted **Gemma vision model** endpoint for costume classification.

**Model: Gemma Vision (Google)**
- Multimodal vision-language model
- Processes both image and text prompt
- Returns structured JSON response

**API Integration:**

Pi sends HTTP POST to Baseten with:
- Base64-encoded cropped person image
- Custom prompt requesting costume classification

**Structured Response Format:**
```json
{
  "classification": "witch",
  "confidence": 0.89,
  "description": "witch with purple hat and broom"
}
```

**Response Processing:**
- Removes markdown code fences (```json, ```) if present
- Strips artifact tags from model output
- Parses JSON to extract three fields:
  - `classification`: Costume category from predefined list (75+ categories)
  - `confidence`: Model confidence score (0-1)
  - `description`: Detailed open-ended description

**Predefined Costume Categories (75+):**
Include: witch, skeleton, superhero, princess, pirate, vampire, zombie, ghost, ninja, dinosaur, astronaut, cowboy, fairy, robot, doctor, police officer, firefighter, inflatable costume, movie character, video game character, historical figure, animal, scary mask, no costume, unclear/uncertain, and many more.

**Inflatable Validation:**
- For detections from Pass 2 (inflatable detection), model validates if it's actually a costume
- Filters out false positives (real cars, birds, etc.)
- Only logs if model confirms it's a costume

**Example API call from Pi:**
```python
import requests
import base64

# Crop person from frame
person_crop = crop_from_bbox(frame, bbox)

# Encode image
_, buffer = cv2.imencode('.jpg', person_crop)
img_base64 = base64.b64encode(buffer).decode('utf-8')

# Call Baseten endpoint
response = requests.post(
    "https://model-<id>.api.baseten.co/production/predict",
    headers={"Authorization": f"Api-Key {BASETEN_API_KEY}"},
    json={
        "image": img_base64,
        "prompt": "Classify this Halloween costume..."
    }
)

result = response.json()
classification = result["classification"]  # e.g., "witch"
confidence = result["confidence"]  # e.g., 0.89
description = result["description"]  # e.g., "witch with purple hat and broom"
```

**Benefits:**
- **Low latency**: Optimized Baseten inference infrastructure
- **No Pi compute overhead**: All vision-language processing in cloud
- **Structured output**: Consistent JSON format for database storage
- **Dual-purpose**: Both classification (category) and description (details)
- **Validation**: Filters false positives from inflatable detection
- **Scalability**: Auto-scaling handles Halloween night traffic spikes

### 5.5 Privacy Preprocessing

**Two-Stage Face Blurring Process:**

1. **Classification Stage**: Send original, unblurred crop to Baseten
   - AI model needs clear image for accurate costume classification

2. **Storage Stage**: Blur faces BEFORE saving or uploading
   - Apply face detection and blurring
   - Upload blurred image to Supabase Storage
   - Delete local original image after upload

**Face Blurring Implementation (`FaceBlurrer` class):**

**Detection:**
- Uses OpenCV Haar Cascade classifiers
- Detects both frontal faces and profile faces
- Two-pass detection for comprehensive coverage

**Duplicate Removal:**
- Uses IoU (Intersection over Union) threshold
- Merges overlapping detections from frontal + profile passes
- Prevents same face being blurred multiple times

**Blurring:**
- Applies Gaussian blur to detected face regions
- Configurable parameters:
  - Blur kernel size: 51 (strong blur for privacy)
  - Padding factor: 0.3 (extends blur beyond face bbox)
  - IoU threshold: 0.3 for duplicate detection
- Can blur specific regions or entire frame

**Privacy Guarantees:**
- Original frames NEVER uploaded to cloud
- Face blurring applied before ANY storage
- Blurred images uploaded to Supabase Storage bucket
- Local images deleted immediately after upload
- Database only contains: classifications, descriptions, timestamps, bounding boxes, image URLs
- No identifiable faces in any stored/uploaded content

### 5.6 Posting Results to Supabase

**Data Upload Process:**

For each detected person, Pi sends to Supabase:

1. **Image Upload** (to Storage bucket `detection-images`):
   - Blurred person crop as JPEG
   - Returns public URL

2. **Database Insert** (to `person_detections` table):
   ```json
   {
     "timestamp": "2025-10-31T02:42:11Z",
     "confidence": 0.95,
     "bounding_box": {"x1": 120, "y1": 80, "x2": 340, "y2": 520, "width": 220, "height": 440},
     "image_url": "https://<supabase-project>.supabase.co/storage/v1/object/public/detection-images/<filename>.jpg",
     "device_id": "halloween-pi",
     "costume_classification": "witch",
     "costume_description": "witch with purple hat and broom",
     "costume_confidence": 0.89
   }
   ```

**Authentication:**
- Pi uses service role key for full access (insert + storage upload)
- Stored in environment variable `SUPABASE_SERVICE_ROLE_KEY`

**Error Handling:**
- Graceful degradation if Supabase unavailable
- Logs errors but continues processing
- Local cleanup happens even if upload fails

### 5.7 Production Service Behavior

**Deployment:**
- Systemd service (`costume-detector.service`) for production operation
- Auto-restart on failure
- Runs on boot

**Service Management:**
```bash
# Start service
sudo systemctl start costume-detector

# Enable on boot
sudo systemctl enable costume-detector

# Check status
sudo systemctl status costume-detector

# View logs
sudo journalctl -u costume-detector -f
```

**Production Features:**

1. **Health Monitoring:**
   - Stats logged every 5 minutes (frames processed, detections, cooldown status)
   - Failed frame tracking

2. **Connection Management:**
   - Auto-reconnect if RTSP stream fails
   - Periodic reconnection every 1 hour (prevents memory leaks)
   - Retry logic with exponential backoff

3. **Resource Management:**
   - Processes only every 30th frame (~1 FPS)
   - Local file cleanup after upload
   - Memory-efficient operation for 24+ hour runtime

4. **State Tracking:**
   - Consecutive detection count
   - Last detection timestamp (for cooldown)
   - Frame counter
   - Last reconnection time

## 6. Supabase Responsibilities

### 6.1 Database Schema

```sql
create table person_detections (
  id uuid primary key default gen_random_uuid(),
  timestamp timestamptz not null,
  confidence float4,
  bounding_box jsonb,
  image_url text,
  device_id text,
  costume_classification text,
  costume_description text,
  costume_confidence float4,
  created_at timestamptz default now()
);
```

**Fields:**
- `id`: Unique identifier for each detection
- `timestamp`: When the detection occurred (from Pi)
- `confidence`: YOLO person detection confidence score (0–1)
- `bounding_box`: JSONB containing detection coordinates `{x1, y1, x2, y2, width, height}`
- `image_url`: URL to blurred detection image in Supabase Storage
- `device_id`: Identifier for the Pi device (supports multiple devices)
- `costume_classification`: Costume category from predefined list (e.g., "witch", "skeleton", "superhero")
- `costume_description`: Detailed open-ended description from vision-language model (e.g., "witch with purple hat and broom")
- `costume_confidence`: AI model confidence for costume classification (0–1)
- `created_at`: Database insertion timestamp

### 6.2 Storage

**Bucket: `detection-images`**
- Public bucket for storing blurred detection images
- Images are uploaded after face blurring
- Original images are deleted from Pi after upload
- URL stored in `image_url` field of `person_detections` table

### 6.3 Realtime

- Supabase Realtime enabled on `person_detections` table
- Every insert from Pi triggers a realtime event
- Website subscribes to this channel and updates instantly without refresh

### 6.4 API Access

**Pi access:**
- Hits Supabase REST endpoint for `person_detections` inserts
- Uses service role key for authentication

**Next.js frontend:**
- Uses public anon key to read `person_detections` (via RLS policies)

**Row Level Security (RLS):**
- Allow inserts from service role key
- Allow read-select from public website (anon key)
- No updates/deletes needed

## 7. Next.js / Vercel Site Responsibilities

### 7.1 Stack

- **Next.js 16** (App Router with React 19 RC)
- **React 19** (Release Candidate)
- **TypeScript** (strict mode)
- **Tailwind CSS v4** (beta) for styling
- **Supabase JS client** for database + realtime
- **Recharts** for costume distribution charts
- **Lucide React** for icons
- **Deployed on Vercel** (production)

### 7.2 Live Dashboard UI

**Title: "Ghostbusters"**
- Custom mummy bandage wrapping effect
- Styled with animations and Halloween theme

**Dashboard Components:**

1. **Stats Cards** (top row, 4 cards):
   - **Total Visitors**: Count of all detections
   - **Unique Costumes**: Count of distinct costume classifications
   - **Active Now**: Count of detections in last 5 minutes
   - **Confidence Meter**: Average costume classification confidence

2. **Costume Distribution Chart**:
   - Bar chart showing top 5 most common costumes
   - Uses costume_classification field
   - Built with Recharts
   - Real-time updates

3. **Live Activity Timeline**:
   - Horizontal timeline showing detection frequency over time
   - Groups detections into time bins
   - Visualizes traffic patterns throughout the night

4. **Recent Detections Feed**:
   - Scrolling list of recent arrivals
   - Shows: costume classification, description, timestamp, confidence
   - Displays detection images (blurred)
   - Auto-updates via Supabase Realtime

5. **Photo Gallery**:
   - Grid of recent detection images
   - All faces blurred for privacy
   - Click to expand/view details

### 7.3 Data Flow in Browser

**Initial load:**
- Client fetches `person_detections` table ordered by timestamp DESC
- Loads all historical detections for Halloween night

**Realtime updates:**
- Supabase Realtime WebSocket subscription to `person_detections` table
- Listens for `INSERT` events
- On new detection:
  - State automatically updates via React hooks
  - All dashboard components re-render
  - Stats cards update counts
  - Charts refresh with new data
  - Detection appears in recent feed
  - Image added to photo gallery

**State Management:**
- React state with `useState` for detections array
- Derived stats computed from detections (total, unique, active now)
- Real-time subscription in `useEffect` hook
- Cleanup on component unmount

## 8. Lifecycle / Flow-of-Data Walkthrough

1. **Kid walks up in costume at doorstep**
   - DoorBird camera captures them in frame
   - RTSP stream continuously running

2. **Pi 5 processes video frames**
   - Reads RTSP stream from DoorBird over LAN
   - Processes every 30th frame (~1 FPS)

3. **Dual-pass person detection**
   - **Pass 1**: YOLOv8n detects people (class 0) in ROI area
   - **Pass 2**: YOLOv8n detects potential inflatables (classes 2, 14, 16, 17)
   - Both passes filtered to doorstep ROI (left 70% of frame)

4. **Consecutive frame validation**
   - Detection must occur in 2 consecutive frames
   - Prevents false positives from transient objects

5. **Cooldown check**
   - Checks if 30 seconds passed since last detection
   - Prevents duplicate captures of same person

6. **Multi-person processing**
   - For EACH detected person in frame:
     - Crop person from frame
     - Send to Baseten for classification

7. **Costume classification (Baseten API)**
   - Gemma vision model analyzes original crop
   - Returns structured JSON:
     ```json
     {
       "classification": "witch",
       "confidence": 0.89,
       "description": "witch with purple hat and broom"
     }
     ```
   - For inflatable detections: validates if actually a costume

8. **Face blurring**
   - Apply FaceBlurrer to person crop
   - Blur all detected faces (frontal + profile)
   - Generate blurred JPEG

9. **Upload to Supabase**
   - Upload blurred image to Storage bucket `detection-images`
   - Get public URL
   - Insert record into `person_detections` table:
     ```json
     {
       "timestamp": "2025-10-31T02:42:11Z",
       "confidence": 0.95,
       "bounding_box": {"x1": 120, "y1": 80, "x2": 340, "y2": 520, "width": 220, "height": 440},
       "image_url": "https://...supabase.co/storage/.../abc123.jpg",
       "device_id": "halloween-pi",
       "costume_classification": "witch",
       "costume_description": "witch with purple hat and broom",
       "costume_confidence": 0.89
     }
     ```

10. **Local cleanup**
    - Delete original and blurred images from Pi
    - Free up storage space

11. **Supabase broadcasts update**
    - Row inserted into `person_detections`
    - Realtime WebSocket event fires to all connected clients

12. **Dashboard updates instantly**
    - Next.js app receives Realtime event
    - React state updates with new detection
    - All components re-render:
      - Stats cards increment counts
      - New bar appears in costume distribution chart
      - Detection appears in recent feed with image
      - Photo added to gallery
      - Timeline graph updates

13. **Cooldown period starts**
    - 30-second timer begins
    - No new captures until cooldown expires
    - Continues processing frames for next arrival

## 9. Constraints / Considerations

### 9.1 Compute on Pi

**Pi 5 capabilities (8GB RAM):**
- Runs only YOLOv8n for person detection at ~1 frame/sec
- Costume classification offloaded to Baseten API
- Pi just handles: frame capture, person detection, image encoding, HTTP requests

**Performance strategy:**
- Intentionally run inference at low frame rate (not full video FPS)
- Keeps CPU load/thermal load manageable with CanaKit fan + heatsink
- Baseten API calls are async - won't block the main loop
- May queue requests if multiple people detected simultaneously

### 9.2 Network

**Requirements:**
- Pi must be on same local network as DoorBird (for RTSP access)
- Pi must have outbound internet for:
  - Baseten API (costume classification)
  - Supabase API (logging events)
- Public website does NOT talk to Pi directly, only Supabase

### 9.3 Privacy & Signage

**Privacy measures:**
- All recognition runs locally
- Only upload abstracted results (label + time)
- Do not publish kids' faces

**Recommended signage:**
Print a sign near the candy bowl:
> "Costume Counter: We're counting costumes tonight using local AI. No faces are stored or posted."

## 10. Summary

### Hardware
- **Raspberry Pi 5** (8GB RAM) with CanaKit case, fan, and heatsink
- **128GB microSD card** for OS and storage
- **DoorBird doorbell** as RTSP camera source
- **Headless operation**: No keyboard, mouse, or monitor
- **Network**: LAN for RTSP, internet for Baseten + Supabase

### Edge Software (Raspberry Pi 5)

**Main Script**: `/backend/scripts/main.py`

**Detection Pipeline**:
1. Capture RTSP stream from DoorBird (OpenCV)
2. Dual-pass YOLOv8n detection:
   - Pass 1: People (class 0)
   - Pass 2: Inflatables (classes 2, 14, 16, 17)
3. ROI filtering (doorstep area only: x 0-70%)
4. Consecutive frame validation (2 frames required)
5. Cooldown enforcement (30 seconds between captures)
6. Multi-person support (all detected people processed)

**Classification**: Baseten Gemma vision model
- Returns structured JSON: `{classification, confidence, description}`
- 75+ predefined costume categories
- Validates inflatable detections

**Privacy**: Face blurring before storage
- OpenCV Haar Cascade (frontal + profile)
- Gaussian blur (kernel size 51)
- IoU-based duplicate removal
- Original images never uploaded

**Production Features**:
- Systemd service with auto-restart
- Health monitoring every 5 minutes
- Periodic RTSP reconnection (hourly)
- Graceful error handling
- Resource-efficient (~1 FPS processing)

**Tech Stack**: Python, OpenCV, Ultralytics YOLO, Supabase client, `uv` package manager

### Backend / Data Layer (Supabase)

**Database Table**: `person_detections`
- Full schema with 9 fields (timestamp, confidence, bounding_box, image_url, device_id, costume_classification, costume_description, costume_confidence, created_at)
- Realtime enabled for live updates
- RLS: Service role write, public read

**Storage**: Bucket `detection-images`
- Public bucket for blurred images
- JPEG format
- Auto-cleanup on Pi after upload

### Frontend (Next.js on Vercel)

**Stack**: Next.js 16, React 19, TypeScript, Tailwind CSS v4

**Dashboard Features**:
- **Title**: "Ghostbusters" with mummy bandage styling
- **Stats cards**: Total visitors, unique costumes, active now, confidence meter
- **Costume distribution chart**: Top 5 costumes (Recharts)
- **Live activity timeline**: Detection frequency over time
- **Recent detections feed**: Scrolling list with images
- **Photo gallery**: Grid of blurred detection images

**Real-time**: Supabase Realtime WebSocket subscription
- Automatic state updates on new detections
- All components re-render live

### Development & Testing

**Testing**: 6 integration tests (1,427 lines)
- Baseten connection, costume detection, DoorBird RTSP, multi-person, inflatables, Supabase

**Code Quality**: Ruff for linting/formatting

**Documentation**: Comprehensive setup guides for Baseten, Supabase, DoorBird, face blurring

### Interface / Access
- **SSH-only**: All control headlessly via `ssh <user>@halloween-pi.local`
- **Systemd service**: Production deployment with auto-restart
- **Monitoring**: Journalctl logs for troubleshooting
