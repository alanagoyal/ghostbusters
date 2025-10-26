# System Architecture Diagram

Visual representation of the complete costume classification system.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     HALLOWEEN NIGHT SYSTEM                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────┐
│   DoorBird      │  RTSP Stream (1280x720)
│   Doorbell      │  rtsp://192.168.x.x:8557/mpeg/media.amp
│   Camera        │
└────────┬────────┘
         │
         │ Network (RTSP over WiFi)
         ▼
┌─────────────────┐
│ Raspberry Pi 5  │
│   (Edge)        │
│  ┌───────────┐  │
│  │ OpenCV    │  │  Frame capture (30 FPS)
│  │ Video     │  │
│  │ Capture   │  │
│  └─────┬─────┘  │
│        │        │
│        ▼        │
│  ┌───────────┐  │
│  │  YOLOv8n  │  │  Person detection
│  │  Detector │  │  → Bounding boxes
│  └─────┬─────┘  │
│        │        │
│        ▼        │
│  ┌───────────┐  │
│  │   Crop    │  │  Extract person from frame
│  │  Person   │  │  Using bbox coordinates
│  └─────┬─────┘  │
└────────┼────────┘
         │
         │ HTTPS (Base64 encoded image)
         ▼
┌─────────────────┐
│  Baseten API    │
│   (Cloud)       │
│  ┌───────────┐  │
│  │  Llama    │  │  Vision-Language Model
│  │  3.2 11B  │  │  Image → Text description
│  │  Vision   │  │
│  └─────┬─────┘  │
└────────┼────────┘
         │
         │ JSON response
         │ {"description": "witch with purple hat"}
         ▼
┌─────────────────┐
│ Raspberry Pi 5  │
│  ┌───────────┐  │
│  │  Process  │  │  Parse costume description
│  │  Result   │  │  Add timestamp, metadata
│  └─────┬─────┘  │
└────────┼────────┘
         │
         │ HTTPS (JSON)
         ▼
┌─────────────────┐
│   Supabase      │
│   Database      │
│  ┌───────────┐  │
│  │ costume   │  │  Store detection record
│  │   table   │  │  + realtime updates
│  └─────┬─────┘  │
└────────┼────────┘
         │
         │ Realtime Subscription
         ▼
┌─────────────────┐
│   Next.js       │
│   Dashboard     │
│  ┌───────────┐  │
│  │  Live     │  │  Public display
│  │  Updates  │  │  Shows costumes in real-time
│  └───────────┘  │
└─────────────────┘
```

## Data Flow Diagram

```
┌──────────────┐
│  RTSP Frame  │
│ 1280x720 RGB │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ YOLO Detect  │
│ Person: 87%  │  ← Confidence threshold
│ bbox: (x,y,  │
│        w,h)  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Crop Person  │
│ 300x500 RGB  │  ← Typical person crop
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Base64 Encode│
│ data:image/  │
│ jpeg;base64, │
│ /9j/4AAQ...  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   API Call   │
│   Baseten    │
│              │
│ POST /predict│
│ {            │
│   "messages":│
│   "image":   │
│   "temp": 0.3│
│ }            │
└──────┬───────┘
       │
       │ ~2-3 seconds
       ▼
┌──────────────┐
│ API Response │
│ {            │
│  "success":  │
│   true,      │
│  "desc":     │
│   "witch     │
│    with hat",│
│  "latency":  │
│   2.34       │
│ }            │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Save to DB   │
│ {            │
│  id: uuid    │
│  timestamp:  │
│  costume:    │
│  confidence: │
│  image_url:  │
│ }            │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Dashboard   │
│  Updates     │
└──────────────┘
```

## Component Details

### Edge Layer (Raspberry Pi)

```
┌────────────────────────────────────────┐
│        Raspberry Pi 5 (8GB RAM)        │
├────────────────────────────────────────┤
│                                        │
│  Python 3.10 Application               │
│  ┌──────────────────────────────────┐  │
│  │  Main Detector Loop              │  │
│  │  ├─ Capture frame (OpenCV)       │  │
│  │  ├─ Detect person (YOLO)         │  │
│  │  ├─ Classify costume (Baseten)   │  │
│  │  └─ Save to Supabase             │  │
│  └──────────────────────────────────┘  │
│                                        │
│  Dependencies:                         │
│  • opencv-python (video processing)    │
│  • ultralytics (YOLOv8)               │
│  • requests (HTTP client)             │
│  • pillow (image encoding)            │
│  • supabase-py (database client)      │
│                                        │
└────────────────────────────────────────┘
```

### Cloud Layer (Baseten)

```
┌────────────────────────────────────────┐
│           Baseten Platform             │
├────────────────────────────────────────┤
│                                        │
│  Model: Llama 3.2 11B Vision Instruct  │
│  Hardware: A100 GPU                    │
│  Autoscaling: 0-2 replicas            │
│                                        │
│  Input:                                │
│  • Image (base64 or URL)              │
│  • Prompt (text)                      │
│  • Parameters (temp, max_tokens)      │
│                                        │
│  Output:                               │
│  • Costume description (text)         │
│  • Token usage stats                  │
│  • Latency metrics                    │
│                                        │
│  Pricing: Per-minute GPU usage        │
│  ~$9.984/hour for A100                │
│                                        │
└────────────────────────────────────────┘
```

### Data Layer (Supabase)

```
┌────────────────────────────────────────┐
│          Supabase Database             │
├────────────────────────────────────────┤
│                                        │
│  Table: detections                     │
│  ┌──────────────────────────────────┐  │
│  │ id              UUID PRIMARY KEY │  │
│  │ created_at      TIMESTAMP        │  │
│  │ costume         TEXT             │  │
│  │ confidence      FLOAT            │  │
│  │ image_url       TEXT             │  │
│  │ bbox            JSONB            │  │
│  │ latency_ms      INTEGER          │  │
│  └──────────────────────────────────┘  │
│                                        │
│  Features:                             │
│  • Realtime subscriptions             │
│  • Row-level security                 │
│  • Automatic timestamps               │
│  • Storage for images                 │
│                                        │
└────────────────────────────────────────┘
```

### Frontend Layer (Vercel)

```
┌────────────────────────────────────────┐
│         Next.js Dashboard              │
├────────────────────────────────────────┤
│                                        │
│  Features:                             │
│  • Live costume feed                   │
│  • Real-time updates (Supabase)       │
│  • Image gallery                      │
│  • Statistics/counts                  │
│                                        │
│  Pages:                                │
│  • /          - Live feed             │
│  • /stats     - Analytics             │
│  • /gallery   - All costumes          │
│                                        │
│  Deployment: Vercel (serverless)      │
│                                        │
└────────────────────────────────────────┘
```

## Network Topology

```
┌─────────────────────────────────────────────────────────┐
│                   Home Network (WiFi)                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│   ┌─────────────┐                 ┌─────────────┐      │
│   │  DoorBird   │                 │ Raspberry   │      │
│   │   Camera    │ ────RTSP───────▶│    Pi 5     │      │
│   │ 192.168.x.1 │                 │ 192.168.x.2 │      │
│   └─────────────┘                 └──────┬──────┘      │
│                                           │             │
└───────────────────────────────────────────┼─────────────┘
                                            │
                                  ┌─────────▼─────────┐
                                  │  Internet Router  │
                                  └─────────┬─────────┘
                                            │
                        ┌───────────────────┼──────────────────┐
                        │                   │                  │
                 ┌──────▼──────┐    ┌──────▼──────┐   ┌──────▼──────┐
                 │   Baseten   │    │  Supabase   │   │   Vercel    │
                 │ API Endpoint│    │  Database   │   │  Frontend   │
                 └─────────────┘    └─────────────┘   └─────────────┘
```

## Processing Timeline

```
Halloween Night Event Timeline:

00:00 │ ────────────────────────────────────────────────────
      │
00:01 │  Doorbell rings → Camera motion detected
      │  ↓
00:02 │  Frame captured (1280x720)
      │  ↓
00:03 │  YOLO processes frame → Person detected (95%)
      │  ↓
00:04 │  Person cropped from frame
      │  ↓
00:05 │  Image sent to Baseten API
      │  ↓
00:08 │  Costume classified: "witch with purple hat"
      │  ↓
00:09 │  Saved to Supabase database
      │  ↓
00:10 │  Dashboard updated in real-time
      │  ↓
00:11 │  Ready for next detection
      │
      │ Total: ~11 seconds end-to-end
```

## Error Handling Flow

```
┌─────────────┐
│ Capture     │
│ Frame       │
└──────┬──────┘
       │
       ▼
┌─────────────┐      ┌──────────────┐
│ YOLO Detect │─NO──▶│ Skip frame   │
│ Person?     │      │ Continue     │
└──────┬──────┘      └──────────────┘
       │YES
       ▼
┌─────────────┐
│ Call Baseten│
│ API         │
└──────┬──────┘
       │
       ▼
┌─────────────┐      ┌──────────────┐
│ Success?    │─NO──▶│ Retry 3x     │
│             │      │ with backoff │
└──────┬──────┘      └──────┬───────┘
       │YES                  │FAIL
       │                     ▼
       │              ┌──────────────┐
       │              │ Log error    │
       │              │ Continue     │
       │              └──────────────┘
       ▼
┌─────────────┐
│ Save to DB  │
└──────┬──────┘
       │
       ▼
┌─────────────┐      ┌──────────────┐
│ Success?    │─NO──▶│ Queue for    │
│             │      │ retry later  │
└──────┬──────┘      └──────────────┘
       │YES
       ▼
┌─────────────┐
│ Continue    │
└─────────────┘
```

## Cost Breakdown

```
Halloween Night (4 hours, 150 trick-or-treaters):

┌─────────────────────────────────────────┐
│         Component Costs                 │
├─────────────────────────────────────────┤
│                                         │
│  Baseten API (Llama 3.2 Vision):        │
│  • 150 inferences × 2.5s each           │
│  • Total: 375 seconds = 6.25 minutes    │
│  • Cost: $9.984/hr × (6.25/60) hr       │
│  • = $1.04                              │
│                                         │
│  Supabase:                              │
│  • Free tier (< 500MB, < 2GB transfer)  │
│  • = $0.00                              │
│                                         │
│  Vercel:                                │
│  • Free tier (hobby plan)               │
│  • = $0.00                              │
│                                         │
│  Raspberry Pi:                          │
│  • Already owned                        │
│  • Electricity: ~5W × 4hr = 0.02 kWh    │
│  • = $0.003 (negligible)                │
│                                         │
├─────────────────────────────────────────┤
│  TOTAL: ~$1.04                          │
└─────────────────────────────────────────┘
```

## Performance Metrics

```
Expected Performance (per detection):

┌────────────────────────┬──────────────┐
│ Component              │ Latency      │
├────────────────────────┼──────────────┤
│ Frame capture          │ ~30ms        │
│ YOLO inference         │ ~100-200ms   │
│ Image preprocessing    │ ~50ms        │
│ Baseten API call       │ ~2000-3000ms │
│ Database save          │ ~100ms       │
├────────────────────────┼──────────────┤
│ TOTAL                  │ ~2.5-3.5s    │
└────────────────────────┴──────────────┘

Bottleneck: Baseten API call (2-3 seconds)
Optimization: Use temperature=0.3, max_tokens=50
```

## Scalability

```
Current Setup (1 Pi, 1 Camera):
  → ~20 detections/minute (limited by Baseten API)
  → 150 trick-or-treaters in 4 hours: ✅ Easy

Future Scaling Options:

1. Multiple Cameras:
   → 1 Pi can handle 2-3 RTSP streams
   → Parallel API calls to Baseten

2. Multiple Raspberry Pis:
   → Each Pi handles 1 camera
   → Share same Supabase database

3. Faster Model:
   → Switch to smaller VLM (7B instead of 11B)
   → Trade-off: Lower quality for higher speed

4. Batch Processing:
   → Queue detections
   → Process in batches (if delay acceptable)
```

---

## Legend

```
┌─────────┐
│  Box    │  = Component or process
└─────────┘

─────────▶  = Data flow

─────NO───▶ = Conditional flow

│
▼           = Continues downward
```
