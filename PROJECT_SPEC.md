# Doorstep Costume Classifier — System Specification

## 1. Goal

Build a small edge computer vision system that:

- Watches live video from the existing DoorBird doorbell camera on Halloween night
- Detects when a person shows up
- Classifies their costume into a known set of costume types (witch, skeleton, spider-man, etc.)
- Logs each sighting (costume label, timestamp, confidence) to a Supabase database
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
    - Crops each person
    - Runs costume classification (CLIP zero-shot classifier)
    - Blurs faces before saving any thumbnails (privacy)
    - Posts {label, confidence, timestamp} to Supabase via REST
    |
    | (HTTPS)
    v
[Supabase]
    - Postgres table `sightings`
    - Row-level inserts from Pi
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

- Run small YOLO model on Pi 5 to detect: "is there a person in this frame?"
- For each bounding box with `class=person`, crop that region (the "kid in costume")

### 5.4 Costume Classification

Run CLIP-style zero-shot classifier on cropped person image.

**Fixed label set:**
- witch
- skeleton
- vampire
- pirate
- princess
- ghost
- superhero
- spiderman
- batman
- dinosaur
- cat
- pumpkin
- astronaut
- ninja
- fairy
- barbie
- doctor
- cowboy
- angel
- soccer player

**Process:**
- CLIP returns similarity scores for each prompt (e.g., "a photo of a witch costume")
- Pick the top-scoring label and its confidence

### 5.5 Privacy Preprocessing

Before saving any "evidence" image locally:
1. Run face detector (e.g., OpenCV/Mediapipe)
2. Blur the faces
3. Downscale to small thumbnail (e.g., 320px wide)
4. Optionally store locally for debugging or future gallery

**Privacy guarantees:**
- Do NOT upload raw frames or identifiable faces to the cloud
- ONLY upload text (label, timestamp, confidence) to Supabase

### 5.6 Posting Results to Supabase

Pi sends HTTP POST to Supabase REST API for each new sighting:
- `label` (string)
- `confidence` (float 0–1)
- `timestamp` (UTC ISO string)

**Authentication:**
- Pi authenticates using service or anon key stored in local config file

### 5.7 Service Behavior

- Script runs in a loop under SSH initially
- For "production night," launch via `nohup` or systemd service
- Persists even after SSH disconnect

## 6. Supabase Responsibilities

### 6.1 Database Schema

```sql
create table sightings (
  id uuid primary key default gen_random_uuid(),
  label text not null,
  confidence numeric,
  timestamp timestamptz default now()
);
```

**Fields:**
- `label`: Costume type the model guessed (e.g., "witch")
- `confidence`: Model confidence score (0–1)
- `timestamp`: When the detection occurred

### 6.2 Realtime

- Supabase Realtime enabled on `sightings` table
- Every insert from Pi triggers a realtime event
- Website subscribes to this channel and updates instantly without refresh

### 6.3 API Access

**Pi access:**
- Hits Supabase REST endpoint for `sightings` inserts

**Next.js frontend:**
- Uses public anon key to read `sightings` (via RLS policies)

**Row Level Security (RLS):**
- Allow inserts from Pi key
- Allow read-select from public website
- No updates/deletes needed

## 7. Next.js / Vercel Site Responsibilities

### 7.1 Stack

- Next.js (App Router)
- Supabase JS client
- Realtime subscription
- Recharts / Chart.js for visuals
- Deployed on Vercel

### 7.2 Live Dashboard UI

**Components:**

1. **Costume leaderboard**
   - Sorted list (e.g., "1. witch (23), 2. spider-man (17), ...")

2. **Donut / pie chart of costume distribution**
   - Shows % share by label

3. **Timeline graph**
   - x-axis: time of night
   - y-axis: number of sightings per 5-minute bin

4. **"New arrival" ticker**
   - Live toast notifications (e.g., "👻 ghost @ 7:42pm")
   - Powered by realtime channel

### 7.3 Data Flow in Browser

**Initial load:**
- Client fetches full `sightings` table (or last N rows)

**Realtime updates:**
- Opens Supabase Realtime subscription
- On new row insert: `useEffect` updates state
- Charts re-render live

## 8. Lifecycle / Flow-of-Data Walkthrough

1. **Kid walks up in costume**
   - DoorBird camera sees them

2. **DoorBird streams RTSP video on LAN**
   - Pi 5 continuously reads frames over RTSP

3. **Pi detects a person**
   - YOLO returns bounding boxes for "person"

4. **Pi classifies the costume**
   - Crop → CLIP → "witch (0.83 confidence)"

5. **Pi sends event to Supabase**
   ```json
   {
     "label": "witch",
     "confidence": 0.83,
     "timestamp": "2025-10-31T02:42:11Z"
   }
   ```

6. **Supabase stores and broadcasts**
   - Row inserted into `sightings`
   - Realtime event fires

7. **Next.js site updates instantly**
   - Leaderboard, pie chart, timeline all update live

8. **Optional: Pi keeps blurred thumbnail locally**
   - For future Halloween "poster" or debugging

## 9. Constraints / Considerations

### 9.1 Compute on Pi

**Pi 5 capabilities (8GB RAM):**
- Sufficient to run:
  - YOLOv8n for person detection at ~1 frame/sec
  - CLIP ViT-B/32 for zero-shot classification on cropped images

**Performance strategy:**
- Intentionally run inference at low frame rate (not full video FPS)
- Keeps CPU load/thermal load manageable with CanaKit fan + heatsink

### 9.2 Network

**Requirements:**
- Pi must be on same local network as DoorBird (for RTSP access)
- Pi must have outbound internet (to talk to Supabase)
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
- Raspberry Pi 5 (8GB RAM) kit with cooling + power + 128GB SD card
- No keyboard, no mouse, no monitor in normal use
- DoorBird is the only camera

### Edge Software (Pi)
Python script that:
- Pulls RTSP video from DoorBird
- Runs YOLO person detection
- Crops each person and classifies costume with CLIP
- Logs `{label, confidence, timestamp}` to Supabase

### Backend / Data Layer
- Supabase Postgres table `sightings`
- Supabase Realtime for live updates
- Acts as shared source of truth

### Frontend
Next.js app on Vercel that:
- Subscribes to Supabase Realtime
- Shows live charts, leaderboard, timeline of costumes

### Interface / Access
- All control of the Pi is done headlessly over SSH
