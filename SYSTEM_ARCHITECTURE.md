# System Architecture: Complete Component Map

## Quick Reference: File Relationships

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        HALLOWEEN COSTUME DETECTION SYSTEM                   │
└─────────────────────────────────────────────────────────────────────────────┘

LAYER 1: EDGE DEVICE (Raspberry Pi 5)
┌──────────────────────────────────────────────────────────────┐
│ detect_people.py                                             │
│ ├─ Captures RTSP stream from DoorBird                       │
│ ├─ Runs YOLOv8n detection (person class only)              │
│ ├─ ISSUE: Only saves highest confidence person when 2+ in  │
│ │         frame (see MULTIPLE_PEOPLE_DESIGN.md)            │
│ ├─ Saves frame locally with bounding box annotations        │
│ └─ Calls supabase_client.save_detection() with results     │
└──────────────────────────────────────────────────────────────┘
                            │
                            │ Uses
                            ▼
LAYER 2: DATA CLIENT (Local Python)
┌──────────────────────────────────────────────────────────────┐
│ supabase_client.py                                           │
│ ├─ SupabaseClient class                                    │
│ ├─ Methods:                                                 │
│ │  ├─ upload_detection_image() → storage URL              │
│ │  ├─ insert_detection() → database row                   │
│ │  ├─ save_detection() → complete workflow                │
│ │  ├─ update_costume_classification() → add AI result     │
│ │  └─ get_recent_detections() → query recent events      │
│ └─ Handles authentication with SUPABASE_SERVICE_ROLE_KEY  │
└──────────────────────────────────────────────────────────────┘
                            │
                            │ HTTPS POST/GET
                            ▼
LAYER 3: CLOUD BACKEND (Supabase)
┌──────────────────────────────────────────────────────────────┐
│ supabase_migration.sql                                       │
│ ├─ TABLE: person_detections                                │
│ │  ├─ id (uuid)                                           │
│ │  ├─ timestamp (when detected)                           │
│ │  ├─ confidence (YOLO confidence)                        │
│ │  ├─ bounding_box (JSONB: x1,y1,x2,y2)                 │
│ │  ├─ image_url (link to storage)                        │
│ │  ├─ device_id (which camera)                           │
│ │  ├─ costume_classification (AI description)            │
│ │  ├─ costume_confidence (AI confidence)                 │
│ │  └─ created_at (insertion time)                        │
│ │                                                          │
│ ├─ STORAGE BUCKET: detection-images                       │
│ │  └─ Path: {device_id}/{YYYYMMDD_HHMMSS.jpg}           │
│ │                                                          │
│ ├─ RLS POLICIES:                                           │
│ │  ├─ Public read access (for dashboard)                 │
│ │  ├─ Service role insert (from Pi)                      │
│ │  └─ Service role update (for costume classification)   │
│ │                                                          │
│ ├─ REALTIME PUBLICATION:                                  │
│ │  └─ Broadcasts INSERT/UPDATE events to subscribed      │
│ │     clients (dashboard)                                │
│ │                                                          │
│ └─ INDEXES:                                                │
│    ├─ idx_person_detections_timestamp                     │
│    ├─ idx_person_detections_device                        │
│    └─ idx_person_detections_created_at                    │
└──────────────────────────────────────────────────────────────┘
                            │
                            │ WebSocket subscription
                            ▼
LAYER 4: FRONTEND (Next.js on Vercel)
┌──────────────────────────────────────────────────────────────┐
│ dashboard/components/dashboard/                             │
│ ├─ dashboard-client.tsx                                    │
│ │  ├─ Subscribes to person_detections realtime            │
│ │  ├─ Maintains detections state (max 200 records)       │
│ │  ├─ Calculates costume stats & activity trends         │
│ │  └─ Renders child components with live data            │
│ │                                                          │
│ ├─ live-feed.tsx                                           │
│ │  └─ Shows 5-8 most recent detections                   │
│ │     - Costume description (if classified)              │
│ │     - Confidence score                                 │
│ │     - Timestamp                                        │
│ │                                                          │
│ ├─ costume-distribution.tsx                               │
│ │  └─ Bar chart of top 5 costumes                        │
│ │     - Count per costume                                │
│ │     - Percentage of total                              │
│ │                                                          │
│ ├─ activity-timeline.tsx                                  │
│ │  └─ Line chart of detections over time                │
│ │     - 5-minute time buckets                            │
│ │     - Real-time animation                              │
│ │                                                          │
│ ├─ confidence-meter.tsx                                   │
│ │  └─ Average YOLO detection confidence                 │
│ │                                                          │
│ ├─ stats-card.tsx                                         │
│ │  ├─ Total Visitors (all-time count)                   │
│ │  ├─ Unique Costumes (distinct descriptions)           │
│ │  ├─ Active Now (last 5 minutes)                        │
│ │  └─ Confidence meter (average confidence)             │
│ │                                                          │
│ ├─ badge.tsx, button.tsx, card.tsx, separator.tsx        │
│ │  └─ Reusable UI components                             │
│ │                                                          │
│ └─ lib/supabase.ts                                         │
│    └─ Creates Supabase client with NEXT_PUBLIC keys      │
└──────────────────────────────────────────────────────────────┘
```

---

## Critical Data Flow: Detection to Dashboard

```
1. DoorBird Camera
   ↓ (RTSP stream, local network)
   
2. detect_people.py
   ├─ Read frame from RTSP
   ├─ Run YOLO model.predict(frame)
   ├─ Extract all person bounding boxes (class 0)
   ├─ CRITICAL BUG: Only keep highest confidence box
   └─ Return single detection object
   ↓
   
3. supabase_client.save_detection()
   ├─ Upload frame image to storage
   ├─ Get public URL back
   └─ Insert 1 database row with metadata
   ↓
   
4. Supabase PostgreSQL (person_detections table)
   ├─ Record inserted
   ├─ Realtime publication triggered
   └─ Broadcast "INSERT" event to WebSocket subscribers
   ↓
   
5. Supabase Realtime (WebSocket channel)
   └─ Broadcast to all connected clients
   ↓
   
6. Dashboard (React component)
   ├─ dashboard-client.tsx receives event
   ├─ Update detections state: [newDetection, ...prev.slice(0, 199)]
   ├─ Recalculate costumeStats via useMemo
   └─ Re-render all child components with new data
   ↓
   
7. UI Updates (all realtime, <1s latency)
   ├─ Stats card: "Total Visitors: N" increments
   ├─ Live feed: New detection appears at top
   ├─ Costume distribution: Bars update
   └─ Activity timeline: Point added to chart
```

---

## Component Dependencies

### Backend (Python)
```
detect_people.py
├─ Imports: cv2, ultralytics (YOLO)
├─ Depends on: supabase_client.py
└─ Calls: SupabaseClient.save_detection()

supabase_client.py
├─ Imports: supabase SDK
├─ No dependencies on other project files
└─ Standalone utility class
```

### Frontend (TypeScript/React)
```
page.tsx (Server Component)
└─ Calls getInitialDetections() → Supabase query
└─ Passes to <DashboardClient />

dashboard-client.tsx (Client Component)
├─ Imports: supabase library
├─ Imports: All dashboard components
├─ Children:
│  ├─ StatsCard (x4)
│  ├─ CostumeDistribution
│  ├─ LiveFeed
│  └─ ActivityTimeline
└─ State: detections[], realtime subscription

live-feed.tsx
├─ Props: detections[], limit
└─ Maps to UI rows

costume-distribution.tsx
├─ Props: costumes[] (name, count, percentage)
└─ Renders bar chart

activity-timeline.tsx
├─ Props: detections[]
└─ Renders line chart over time

confidence-meter.tsx
├─ Props: detections[]
└─ Calculates average confidence

stats-card.tsx
├─ Props: title, value, description, icon, trend
└─ Generic card renderer
```

---

## Data Structures

### Person Detection (from YOLO)
```python
{
    "class": 0,              # Person class in COCO
    "confidence": 0.95,      # 0.0-1.0
    "bbox": {
        "x1": 100,
        "y1": 150,
        "x2": 300,
        "y2": 450
    },
    "box": Box(),            # ultralytics Box object
}
```

### Database Record (person_detections)
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2025-10-31T20:42:11.123456Z",
    "confidence": 0.95,
    "bounding_box": {"x1": 100, "y1": 150, "x2": 300, "y2": 450},
    "image_url": "https://supabase.../halloween-pi/20251031_204211.jpg",
    "device_id": "halloween-pi",
    "costume_classification": "witch with purple hat and broom",
    "costume_confidence": 0.92,
    "created_at": "2025-10-31T20:42:12Z"
}
```

### Dashboard Detection (TypeScript)
```typescript
interface PersonDetection {
    id: string;                          // UUID from database
    timestamp: string;                   // ISO string
    confidence: number;                  // YOLO confidence (0-1)
    bounding_box: any;                   // JSONB from database
    image_url: string | null;            // Storage URL
    device_id: string;                   // "halloween-pi"
    costume_classification: string | null;  // AI description
    costume_confidence: number | null;   // AI confidence
}
```

---

## Environment Variables Required

### Raspberry Pi (.env)
```
# DoorBird Configuration
DOORBIRD_USERNAME=<doorbell_user>
DOORBIRD_PASSWORD=<doorbell_pass>
DOORBIRD_IP=192.168.1.X

# Supabase Backend
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJh...         # Service role (full access)
SUPABASE_KEY=eyJh...                      # Anon key (optional)

# Device Identification
HOSTNAME=halloween-pi                    # Used for device_id
DEVICE_ID=halloween-pi                   # Fallback for HOSTNAME

# Optional: Baseten for costume classification
BASETEN_API_KEY=...
BASETEN_MODEL_ID=...
```

### Dashboard (.env.local)
```
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJh...     # Public/anon key only
```

---

## Key Files Summary

| File | Purpose | Language | Status |
|------|---------|----------|--------|
| `detect_people.py` | Main detection loop, YOLO inference | Python | Ready, but has multi-person bug |
| `supabase_client.py` | Database & storage operations | Python | Complete |
| `supabase_migration.sql` | Database schema & RLS policies | SQL | Complete |
| `dashboard-client.tsx` | Main React component, realtime subscription | TypeScript | Complete |
| `live-feed.tsx` | Recent detections display | TypeScript | Complete |
| `costume-distribution.tsx` | Bar chart of popular costumes | TypeScript | Complete |
| `activity-timeline.tsx` | Line chart of activity over time | TypeScript | Complete |
| `confidence-meter.tsx` | Average detection confidence | TypeScript | Complete |
| `stats-card.tsx` | Generic stats card component | TypeScript | Complete |
| `page.tsx` | Server-side initial data fetch | TypeScript | Complete |
| `CODEBASE_ANALYSIS.md` | Detailed technical analysis | Markdown | Generated |
| `MULTIPLE_PEOPLE_DESIGN.md` | Design guide for fixing multi-person | Markdown | Generated |

---

## Known Issues & Limitations

### Critical Issues

1. **Multiple People Data Loss** (HIGH)
   - Location: `detect_people.py` lines 135-152
   - Impact: When 2+ people in frame, only highest confidence saved
   - Data Loss: 50%+ of detections in crowded scenes
   - Fix: See `MULTIPLE_PEOPLE_DESIGN.md`

2. **Costume Classification Not Implemented** (HIGH)
   - Status: Planned in spec, infrastructure prepared, but no Baseten integration
   - Impact: No AI costume descriptions in production
   - Fields exist in DB but never populated
   - Location: Baseten integration missing from codebase

### Medium Issues

3. **No Batch Processing** (MEDIUM)
   - Impact: Sequential operations, slower on busy night
   - Solution: Add async/queue system for parallel processing

4. **Privacy Measures Incomplete** (MEDIUM)
   - Face blurring not implemented
   - Full frames saved locally (not just crops)
   - Location: `detect_people.py` lines 129-130

### Performance Notes

- Person detection: <100ms per frame (YOLOv8n)
- Frame processing rate: 1/second (every 30th frame)
- Database latency: ~500ms (Supabase API)
- Real-time update latency: <1s (WebSocket)
- Image upload: 1-3s (network dependent)

---

## Testing the System

### Manual Testing Checklist

```bash
# 1. Test DoorBird connection
uv run python test_doorbird_connection.py

# 2. Test Supabase connection
uv run python test_supabase_connection.py

# 3. Run detection script
uv run python detect_people.py

# 4. Monitor database
# Visit https://supabase.com/dashboard
# Watch person_detections table for new rows

# 5. Test dashboard
cd dashboard
npm install
npm run dev
# Visit http://localhost:3000
# Should show real-time updates from Supabase
```

### Testing Multiple People (After Fix)

```python
# Simulate 2 people detected
# Person 1: confidence 0.95, bbox (100,150,300,450)
# Person 2: confidence 0.87, bbox (350,100,500,400)

# Expected in database:
# {
#   "person_count": 2,
#   "bounding_boxes": [..., ...],  # Both saved
#   "confidences": [0.95, 0.87]
# }

# Dashboard should show:
# - Total Visitors: 2 (not 1)
# - Live feed: Both detections visible
# - Costume distribution: Both costumes counted
```

---

## Deployment Architecture

### Production Setup

```
Internet
  │
  ├─ Raspberry Pi 5 (halloween-pi.local)
  │  └─ detect_people.py (continuous process)
  │
  ├─ Supabase (Cloud)
  │  ├─ PostgreSQL (person_detections table)
  │  ├─ Storage (detection-images bucket)
  │  └─ Realtime (WebSocket broker)
  │
  └─ Vercel (Frontend)
     └─ Next.js dashboard (real-time viewer)

Local Network
  │
  └─ DoorBird Camera
     └─ RTSP stream (rtsp://...)
```

### Connectivity Requirements

- **Pi to DoorBird**: Local network only (RTSP)
- **Pi to Supabase**: Internet connection (HTTPS)
- **Dashboard to Supabase**: Internet connection (WebSocket)
- **Pi to Baseten**: Internet connection (HTTPS) - when implemented

---

## Git Branch Info

Current branch: `terragon/handle-multiple-people-p1otfx`
Main branch: `main`

Recent related PRs:
- #19: Activity timeline changes
- #17: Chart animations on load

---

