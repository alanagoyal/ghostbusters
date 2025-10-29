# Costume Detection and Database System - Comprehensive Overview

## Executive Summary

This is a Halloween costume detection system built on a Raspberry Pi 5 that watches a DoorBird doorbell camera, detects trick-or-treaters using YOLOv8, and classifies their costumes using an external vision-language model API (Baseten). Results are stored in Supabase and displayed on a Next.js dashboard with real-time updates.

**Important Finding:** The system currently has **MINIMAL support for multiple people detection** - it only saves the highest-confidence person when multiple are detected in a frame.

---

## 1. COSTUME DETECTION IMPLEMENTATION

### 1.1 Person Detection (Edge)
**File:** `/root/repo/detect_people.py`

**Technology:** YOLOv8n (nano/smallest model)
- Runs locally on Raspberry Pi 5
- COCO dataset (class 0 = person)
- Lightweight ~6MB model
- Process rate: 1 frame per second (every 30th frame processed)
- Confidence threshold: >0.5

**Detection Flow:**
```python
1. Capture frame from RTSP stream
2. Run YOLO inference: results = model(frame, verbose=False)
3. Filter for person class (class 0): if int(box.cls[0]) == 0
4. Extract bounding box coordinates: x1, y1, x2, y2
5. Track max confidence across detections
```

### 1.2 Costume Classification (Cloud)
**Planned but not yet implemented in production code**

**Technology:** Vision-Language Model via Baseten API
- According to PROJECT_SPEC.md: Plans to use CLIP + LLM (e.g., LLaVA, BLIP-2)
- Would generate open-ended natural language descriptions
- Example: "witch with purple hat and broom" instead of fixed labels

**Planned API Flow:**
```python
1. Crop person from frame using bounding box
2. Encode image to base64
3. POST to Baseten endpoint with image + prompt
4. Return: natural language costume description + confidence
```

**Status:** Infrastructure prepared in supabase_client.py with fields for costume_classification and costume_confidence, but actual Baseten integration not found in codebase.

### 1.3 Image Processing
**Privacy measures planned (not yet fully implemented):**
- Face blurring before saving local thumbnails
- Downscale to small thumbnails (320px wide)
- Only crop + costumes uploaded to cloud, not full frames

---

## 2. DATABASE ENTRY SYSTEM

### 2.1 Database Schema
**File:** `/root/repo/supabase_migration.sql`

**Table: `person_detections`**

```sql
CREATE TABLE person_detections (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  timestamp timestamptz NOT NULL,
  confidence float4 NOT NULL,                    -- YOLO detection confidence
  bounding_box jsonb NOT NULL,                  -- {x1, y1, x2, y2}
  image_url text,                               -- Uploaded detection image URL
  device_id text NOT NULL,                      -- Which device/camera
  costume_classification text,                  -- AI costume description (optional)
  costume_confidence float4,                    -- AI classification confidence (optional)
  created_at timestamptz DEFAULT now()
);
```

**Bounding Box Format:**
```json
{
  "x1": 100,
  "y1": 150,
  "x2": 300,
  "y2": 450
}
```

**Indexes:**
- `idx_person_detections_timestamp` - For recent data queries
- `idx_person_detections_device` - Per-device filtering
- `idx_person_detections_created_at` - Insert order queries

### 2.2 Storage Infrastructure
**Service:** Supabase Storage (S3-compatible)

**Bucket:** `detection-images`
- Public read access
- Path structure: `{device_id}/{YYYYMMDD_HHMMSS.jpg}`
- Used for storing detection frames

### 2.3 Data Insertion Flow
**File:** `/root/repo/supabase_client.py`

**Class:** `SupabaseClient`

**Method: `save_detection()` (Complete Workflow)**
```
1. upload_detection_image()
   - Read image file
   - Upload to Supabase Storage: detection-images/{device_id}/{timestamp}.jpg
   - Get public URL
   
2. insert_detection()
   - Create database record with:
     * timestamp (ISO format)
     * confidence (float 0.0-1.0)
     * bounding_box (JSONB)
     * image_url (optional)
     * device_id
     * costume_classification (optional)
     * costume_confidence (optional)
   - Execute SQL insert
   - Return record with generated ID
```

**Called From:** `/root/repo/detect_people.py` lines 155-164

---

## 3. MULTIPLE PEOPLE DETECTION - CURRENT SUPPORT

### 3.1 Detection Logic
**File:** `/root/repo/detect_people.py` (Lines 135-152)

```python
# Get bounding box from first detection for database
# (if multiple people, we'll use the first one for now)
first_box = None
max_confidence = 0.0

for result in results:
    boxes = result.boxes
    for box in boxes:
        if int(box.cls[0]) == 0:  # person class
            conf = float(box.conf[0])
            if conf > 0.5 and conf > max_confidence:
                max_confidence = conf
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                first_box = {
                    "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                }
```

### 3.2 Current Limitation - **CRITICAL FINDING**

**The Problem:**
- YOLO detects ALL people in frame correctly
- BUT: Only the **HIGHEST CONFIDENCE detection** is saved to database
- Other people in same frame are **DISCARDED**

**Evidence:**
- Comment on line 136: `# (if multiple people, we'll use the first one for now)`
- Only `first_box` is saved, not array of boxes
- Single `save_detection()` call per frame, even if multiple people detected

**Current Behavior:**
```
Frame: 2 people detected (confidence: 0.95, 0.87)
RESULT: Only person with 0.95 confidence saved
LOST: Person with 0.87 confidence is discarded
```

### 3.3 Dashboard Display
**File:** `/root/repo/dashboard/components/dashboard/dashboard-client.tsx`

- Each `PersonDetection` is treated as single entity
- No support for detecting multiple people from same detection event
- Costume stats count unique costume classifications (each detection = 1 person)

---

## 4. IMAGE PROCESSING & PERSON DETECTION CODE

### 4.1 YOLO Configuration
**File:** `/root/repo/detect_people.py` (Line 40)

```python
from ultralytics import YOLO

model = YOLO("yolov8n.pt")  # Download ~6MB on first run
results = model(frame, verbose=False)
```

**Model Details:**
- YOLOv8 nano (smallest/fastest variant)
- Pre-trained on COCO dataset
- 80 classes, person = class 0
- Inference time: <100ms per frame on Pi 5

### 4.2 Frame Capture
**File:** `/root/repo/detect_people.py` (Lines 52-62)

```python
import cv2

rtsp_url = f"rtsp://{DOORBIRD_USER}:{DOORBIRD_PASSWORD}@{DOORBIRD_IP}/mpeg/media.amp"
cap = cv2.VideoCapture(rtsp_url)

# Main loop reads frames continuously
ret, frame = cap.read()
```

**Optimization:**
- Process every 30th frame (~1 per second at 30fps)
- Reduces compute load on Pi
- 2-second debounce between detections (avoid duplicates)

### 4.3 Bounding Box Drawing
**File:** `/root/repo/detect_people.py` (Lines 103-116)

```python
cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
```

Used for visualization only, not for storage.

### 4.4 Detection Deduplication
**File:** `/root/repo/detect_people.py` (Lines 123-124)

```python
if current_time - last_detection_time > 2:
    # Save detection
```

Prevents duplicate uploads within 2-second window.

---

## 5. REAL-TIME DATA FLOW ARCHITECTURE

### 5.1 Complete End-to-End Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ DoorBird Camera (RTSP Stream over local network)               │
└────────────────────────────┬────────────────────────────────────┘
                             │ rtsp://user:pass@ip/mpeg/media.amp
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ Raspberry Pi 5 (detect_people.py)                              │
│  - Read frame from RTSP stream                                 │
│  - Run YOLO person detection (every 30th frame)               │
│  - Extract bounding box + confidence                           │
│  - ISSUE: Only save highest confidence if multiple people     │
│  - Save frame locally with annotations                         │
│  - Upload to Supabase (image + metadata)                       │
└────────┬─────────────────────────────────────────┬──────────────┘
         │ HTTPS                                   │
         ▼                                         ▼
    ┌────────────────────┐           ┌───────────────────────┐
    │ Supabase Storage   │           │ Supabase Database     │
    │ (S3-compatible)    │           │ (PostgreSQL)          │
    │                    │           │                       │
    │ detection-images/  │           │ person_detections     │
    │ {device}/{time}    │           │ table                 │
    │                    │           │                       │
    │ Public read access │           │ - Realtime enabled    │
    │ ~2-5MB per image   │           │ - RLS policies        │
    └────────────────────┘           └───────┬───────────────┘
                                              │ WebSocket subscription
                                              ▼
                                    ┌─────────────────────────┐
                                    │ Next.js Dashboard       │
                                    │ (dashboard-client.tsx)  │
                                    │                         │
                                    │ - Real-time updates     │
                                    │ - Live costume stats    │
                                    │ - Activity timeline     │
                                    │ - Live feed             │
                                    └─────────────────────────┘
```

### 5.2 Supabase Realtime Configuration
**File:** `/root/repo/supabase_migration.sql` (Line 66)

```sql
ALTER PUBLICATION supabase_realtime ADD TABLE person_detections;
```

**Dashboard Subscription:** Lines 33-43 in `dashboard-client.tsx`

```typescript
const channel = supabase
  .channel("person_detections")
  .on(
    "postgres_changes",
    { event: "INSERT", schema: "public", table: "person_detections" },
    (payload) => {
      const newDetection = payload.new as PersonDetection;
      setDetections((prev) => [newDetection, ...prev.slice(0, 199)]);
    }
  )
  .subscribe();
```

---

## 6. RECOMMENDED APPROACH FOR MULTIPLE PEOPLE SUPPORT

### 6.1 Database Schema Changes Needed

**Current Limitation:** One detection = one person in database

**Recommended Approach:**

**Option A: Nested Array (Simpler, Good for Real-time)**
```sql
-- Modify person_detections table
ALTER TABLE person_detections ADD COLUMN bounding_boxes jsonb[] NOT NULL DEFAULT ARRAY[]::jsonb[];
ALTER TABLE person_detections ADD COLUMN confidences float4[] NOT NULL DEFAULT ARRAY[]::float4[];
ALTER TABLE person_detections ADD COLUMN person_count int DEFAULT 1;

-- Example data:
{
  "bounding_boxes": [
    {"x1": 100, "y1": 150, "x2": 300, "y2": 450},
    {"x1": 350, "y1": 100, "x2": 500, "y2": 400}
  ],
  "confidences": [0.95, 0.87],
  "person_count": 2,
  "timestamp": "2025-10-31T20:42:11Z"
}
```

**Option B: Separate People Table (Better for querying individual people)**
```sql
CREATE TABLE person_detections (
  id uuid PRIMARY KEY,
  timestamp timestamptz NOT NULL,
  device_id text NOT NULL,
  image_url text,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE detected_people (
  id uuid PRIMARY KEY,
  detection_id uuid REFERENCES person_detections(id),
  bounding_box jsonb NOT NULL,
  confidence float4 NOT NULL,
  costume_classification text,
  costume_confidence float4
);
```

### 6.2 Code Changes in detect_people.py

**Current (Lines 135-162):**
- Loops through all detections
- Only saves the one with highest confidence
- **Total detections lost: 100% of non-highest-confidence people**

**Required Changes:**
1. Collect ALL person detections with confidence > 0.5
2. Pass array of bounding boxes to database
3. Create/update detection record with all people
4. For costume classification: either:
   - Send each crop to Baseten separately (parallel API calls)
   - OR create separate database entries per person
   - OR save multi-crop image for batch processing

### 6.3 Dashboard Updates Needed

**Current:** One `PersonDetection` = one person

**Required Changes:**
- Update `PersonDetection` interface to support `bounding_boxes: BoundingBox[]`
- Update costume stats to handle multiple people per detection
- Update "Total Visitors" counter (need to decide: count detections or people?)
- Update cost/performance estimates (more DB inserts)

---

## 7. KEY IMPLEMENTATION DETAILS

### 7.1 Environment Variables
**Required:** `/root/repo/.env`
```
DOORBIRD_USERNAME=
DOORBIRD_PASSWORD=
DOORBIRD_IP=
NEXT_PUBLIC_SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_KEY=
HOSTNAME= (device identifier)
```

### 7.2 Deployment Architecture
- **Pi**: Runs as continuous Python process via SSH
- **Supabase**: Cloud PostgreSQL + S3 storage + realtime pubsub
- **Dashboard**: Next.js on Vercel
- **Communication:** HTTPS/WebSocket only (local RTSP for camera)

### 7.3 Performance Metrics
- Person detection: <100ms per frame (YOLOv8n on Pi 5)
- Frame processing rate: 1/second (every 30th frame)
- Database write latency: ~500ms (Supabase API)
- Real-time dashboard update: <1s (WebSocket subscription)
- Image upload: 1-3s (depending on image size, network)

### 7.4 Cost Considerations
- Baseten API: Estimated $0.50-$10 per Halloween night (~50-200 inferences)
- Supabase: Free tier covers testing, ~$25/month for production
- Vercel: Free tier for Next.js dashboard
- AWS/Network: Minimal (only uploads, no continuous streaming)

---

## SUMMARY TABLE: Current vs. Recommended

| Aspect | Current | Recommended for Multiple People |
|--------|---------|----------------------------------|
| **Detection** | YOLOv8 finds all people ✓ | Same (no change needed) |
| **Saving** | Only highest confidence ✗ | Save ALL detections above threshold |
| **Database** | Single bounding_box | Array of bounding_boxes OR separate table |
| **Costume Classification** | Planned (single) | Parallel API calls or batch processing |
| **Dashboard** | Counts detections | May need to count people vs. detections |
| **Real-time Performance** | Established ✓ | Depends on multi-person implementation |

---

## FILES INVOLVED IN DETECTION PIPELINE

1. **Edge Detection:**
   - `/root/repo/detect_people.py` - Main detection loop, YOLO inference

2. **Database & Storage:**
   - `/root/repo/supabase_client.py` - Database operations
   - `/root/repo/supabase_migration.sql` - Schema definition

3. **Dashboard & Real-time:**
   - `/root/repo/dashboard/components/dashboard/dashboard-client.tsx` - Realtime subscription
   - `/root/repo/dashboard/components/dashboard/live-feed.tsx` - Display component
   - `/root/repo/dashboard/components/dashboard/costume-distribution.tsx` - Stats

4. **Testing & Configuration:**
   - `/root/repo/test_supabase_connection.py` - Database test
   - `/root/repo/test_doorbird_connection.py` - Camera test
   - `/root/repo/.env.example` - Configuration template

---

## CRITICAL ISSUES & LIMITATIONS

### Issue #1: Multiple People Discarded
- **Severity:** HIGH for Halloween use case
- **Impact:** Loses 50%+ of detected people when 2+ in frame
- **Fix Complexity:** MEDIUM (requires schema + code changes)

### Issue #2: Costume Classification Not Implemented
- **Severity:** HIGH (core feature per spec)
- **Impact:** No costume descriptions in database
- **Fix Complexity:** HIGH (requires Baseten integration)

### Issue #3: No Batch Processing
- **Severity:** MEDIUM (affects reliability on busy night)
- **Impact:** Sequential API calls, slower processing
- **Fix Complexity:** MEDIUM (add async/queue system)

### Issue #4: Privacy Measures Incomplete
- **Severity:** MEDIUM (privacy concern)
- **Impact:** Full frames saved locally, face blurring not implemented
- **Fix Complexity:** LOW-MEDIUM (use mediapipe/OpenCV)

