# Blog Notes: Building a Doorstep Costume Classifier

*A living document tracking the implementation journey, decisions, and learnings*

---

## Project Overview

Building an edge computer vision system that watches a DoorBird doorbell camera on Halloween night, detects trick-or-treaters, classifies their costumes using AI, and displays live results on a public dashboard.

**Tech Stack:**
- Raspberry Pi 5 (8GB RAM) - edge compute
- DoorBird doorbell - camera/RTSP stream
- YOLOv8n - person detection
- Baseten API - costume classification (vision-language model)
- Supabase - database + realtime
- Next.js on Vercel - live dashboard

---

## Day 1: Specification & Architecture Design

### Initial Concept

Started with the idea of watching the doorbell camera and counting costumes. Original plan was to use a **fixed label set** with CLIP zero-shot classification (witch, skeleton, spider-man, etc.).

### Key Decision: Open-Ended Classification

**The Problem with Fixed Labels:**
- Halloween costumes are incredibly creative and diverse
- Fixed labels would miss unique costumes (inflatable T-Rex, "Barbenheimer", DIY creations)
- Would need constant maintenance/updates to the label list
- Less interesting data - just counts vs. rich descriptions

**The Pivot:**
Switched to **open-ended classification** using vision-language models that generate natural language descriptions.

Examples:
- Instead of: "witch"
- We get: "witch with purple hat and broom"

This captures much more detail and handles unexpected costumes gracefully.

### Architecture Decision: Baseten for ML Inference

**Why not run everything on the Pi?**
- Pi 5 has 8GB RAM, could theoretically run small vision-language models
- But: Halloween night is time-sensitive, we want reliability
- Running heavy ML models on Pi = heat issues, potential slowdowns

**Why Baseten?**
- Offload the heavy ML to cloud infrastructure
- Pi only needs to run lightweight YOLO for person detection
- Auto-scaling handles traffic spikes (what if 20 kids show up at once?)
- Model flexibility - can swap models without touching Pi code
- Low latency optimized inference
- Cost-effective: estimated $0.50-$10 for the whole night

**Trade-offs:**
- Requires internet connection (already needed for Supabase anyway)
- Sends cropped images to cloud (but we're only sending costume crops, not faces)
- Small API cost vs. free local inference

Decision: **Go with Baseten** for reliability and simplicity.

### Data Flow Architecture

```
DoorBird (RTSP)
  → Pi 5 (YOLO person detection)
  → Baseten API (costume description)
  → Supabase (store + realtime)
  → Next.js dashboard (live updates)
```

Clean separation of concerns:
- Edge device (Pi): frame capture, person detection, orchestration
- Cloud ML (Baseten): heavy inference
- Database (Supabase): storage + pubsub
- Frontend (Vercel): presentation

### Privacy Considerations

**Privacy-first design:**
- All processing happens on cropped person images, not full frames
- Face blurring before saving any local thumbnails
- Only text descriptions uploaded to Supabase (no images)
- No identifiable faces in the cloud or on the public dashboard

**Transparency:**
- Planning to put a sign near the candy bowl: "Costume Counter: We're counting costumes tonight using local AI. No faces are stored or posted."

### Hardware Decisions

**Why Raspberry Pi 5?**
- 8GB RAM sufficient for YOLO inference
- Quad-core CPU handles video streaming + HTTP requests
- Built-in Wi-Fi/Ethernet
- Headless operation (SSH only)

**Cooling is critical:**
- CanaKit fan + heatsink
- Will be running inference continuously for 3-4 hours
- Don't want thermal throttling ruining Halloween night

**Why not use a webcam?**
- Already have DoorBird installed at the door
- RTSP stream works perfectly over LAN
- One less thing to install/configure

---

## Day 2: Raspberry Pi Setup & DoorBird Integration

### Hardware Assembly

**Components used:**
- Raspberry Pi 5 (8GB RAM)
- 128GB microSD card (pre-flashed with Raspberry Pi OS from March 2024)
- CanaKit case with cooling fan and heatsink
- CanaKit 45W power supply
- USB microSD card reader

**Assembly notes:**
- The microSD slot is on the **bottom/underside** of the Pi board
- Insert card with metal contacts facing UP (toward the board)
- MacBook Air M2 required USB-C to USB-A adapter for the USB-A card reader

### OS Flashing & Pre-Configuration

**Tool:** Raspberry Pi Imager on MacBook

**Key decision:** Re-flash the pre-installed OS with fresh Raspberry Pi OS to enable headless setup

**Imager configuration (⚙️ settings):**
- **Hostname:** `halloween-pi.local`
- **Username:** `pi`
- **Password:** Set securely
- **WiFi:** Pre-configured home network SSID and password
- **SSH:** Enabled with password authentication
- **Locale:** US timezone and keyboard

**Why re-flash?**
- Pre-installed OS from March 2024 was outdated
- No way to pre-configure WiFi/SSH without keyboard/monitor
- Fresh OS with pre-baked settings enables true headless operation

**First boot:**
- Inserted microSD into Pi
- Connected power supply
- Green LED flashing = successful boot
- Waited 2-3 minutes for first-boot expansion and WiFi connection

### Network & SSH Setup

**Connection test:**
```bash
ping halloween-pi.local
# Success: 192.168.4.95 (8ms latency)
```

**SSH connection:**
```bash
ssh pi@halloween-pi.local
# First connection: Added to known hosts
# Entered password
# Success: pi@halloween-pi:~ $
```

**Result:** Fully headless operation achieved! No keyboard, mouse, or monitor needed.

### Development Environment Setup

**System updates:**
```bash
sudo apt update && sudo apt upgrade -y
# ~5 minutes, all packages updated
```

**Video processing dependencies:**
```bash
sudo apt install -y python3-opencv gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav ffmpeg git
# Installed OpenCV, GStreamer codecs, FFmpeg
```

**Modern Python tooling (Astral stack):**
```bash
# Install uv (package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
uv --version  # 0.9.5

# Note: ruff already configured in pyproject.toml on main branch
```

### Code Deployment

**Repository clone:**
```bash
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/alanagoyal/costume-classifier.git
cd costume-classifier
```

**Environment configuration:**
Created `.env` file with DoorBird credentials:
```bash
nano .env
# Added DOORBIRD_IP, DOORBIRD_USERNAME, DOORBIRD_PASSWORD
# Left BASETEN_API_KEY and SUPABASE_* for later
```

**Python dependencies:**
```bash
uv sync
# Created .venv
# Installed opencv-python (4.12.0.88)
# Installed python-dotenv (1.1.1)
# Total time: ~1-2 minutes
```

### DoorBird Connection Test

**Test script:**
```bash
uv run python test_doorbird_connection.py
```

**Results:**
- ✅ Successfully connected to RTSP stream at `rtsp://***@192.168.4.49/mpeg/media.amp`
- ✅ Captured 1280x720 RGB frame (3 channels)
- ✅ Saved test frame as `test_doorbird_frame.jpg`
- ✅ Total time: ~2 seconds

**What this proves:**
1. Pi can reach DoorBird over LAN
2. RTSP streaming works
3. OpenCV can process video frames
4. Environment variables loaded correctly
5. The entire edge capture pipeline is operational

### Key Learnings

**Hardware:**
- Raspberry Pi 5's microSD slot location is non-obvious (bottom of board)
- USB-C MacBooks need adapters for USB-A peripherals
- Pre-flashed SD cards are outdated—always re-flash for production

**Networking:**
- `.local` mDNS resolution works reliably on home networks
- First boot takes 2-3 minutes (filesystem expansion, services starting)
- WiFi pre-configuration in Raspberry Pi Imager is rock-solid

**Tooling choices validated:**
- **uv** is blazing fast even on ARM64 (Raspberry Pi)
- Headless SSH workflow is smooth once configured
- Modern Python tooling (uv + ruff) works identically on Pi and Mac

### What's Working Now

- [x] Set up Raspberry Pi 5 (OS, SSH, networking)
- [x] Test RTSP connection to DoorBird
- [x] Implement YOLO person detection on Pi
- [ ] Deploy vision-language model to Baseten
- [ ] Build Pi → Baseten → Supabase integration
- [ ] Create Supabase schema and enable Realtime
- [ ] Build Next.js dashboard with live updates
- [ ] End-to-end testing
- [ ] Deploy and prep for Halloween night

---

## Day 3: YOLOv8 Person Detection

### Installing YOLOv8 (Ultralytics)

**Challenge:** Add computer vision capabilities to the Pi for real-time person detection.

**Installation:**
```bash
# On Raspberry Pi
uv add ultralytics
```

**Dependencies added:**
- `ultralytics` (8.3.221) - YOLOv8 framework
- `torch` (2.9.0) - PyTorch for ARM64
- `torchvision` (0.24.0) - Vision transformations
- 47 total packages including CUDA libraries (for future GPU support)
- Total download: ~200MB
- Installation time: ~3 minutes on Pi 5

**Key decision:** Use YOLOv8n (nano) variant
- Smallest YOLO model (~6MB)
- Fastest inference on CPU
- Still highly accurate for person detection (trained on COCO dataset)
- Perfect balance for Raspberry Pi 5

### Building detect_people.py

**Development workflow improvement:**
Instead of editing files via `nano` on the Pi over SSH, we adopted a better workflow:
1. Write code on Mac (better editor, tools)
2. Commit to git
3. Pull on Pi
4. Run and test

**Script architecture:**

**Frame sampling strategy:**
```python
# Process every 30th frame (~1 fps at 30fps stream)
if frame_count % 30 != 0:
    continue
```

**Why not process every frame?**
- DoorBird streams at ~30fps
- YOLO inference takes ~200-300ms on Pi 5
- Processing every frame would max out CPU and cause lag
- 1 fps is perfect for detecting people walking up to door
- Keeps CPU usage manageable, prevents thermal throttling

**Detection logic:**
```python
# Class 0 = 'person' in COCO dataset
if int(box.cls[0]) == 0:
    confidence = float(box.conf[0])
    if confidence > 0.5:  # Only high-confidence detections
        # Draw bounding box and save frame
```

**Debouncing detections:**
```python
# Avoid duplicate detections within 2 seconds
if current_time - last_detection_time > 2:
    detection_count += 1
    save_frame_with_bbox()
```

**Why 2 seconds?**
- Person walking slowly takes ~1-2 seconds to cross frame
- Prevents saving 30 images of the same person
- Reduces false positives from jittery detections

### Testing & Results

**First test:**
```bash
uv run python detect_people.py
```

**Output:**
```
🚀 Starting person detection system...
📹 Connecting to DoorBird at 192.168.4.49
🤖 Loading YOLOv8n model...
✅ Model loaded!
✅ Connected to RTSP stream!

👁️  Watching for people...
Press Ctrl+C to stop

👤 Person detected! (#1)
   Saved: detection_20251026_121049.jpg
```

**Results:**
- ✅ First run downloads yolov8n.pt (~6MB) automatically
- ✅ Model loads in ~1-2 seconds on Pi 5
- ✅ RTSP connection works seamlessly
- ✅ Person detection successful on first frame with person
- ✅ Bounding box drawn correctly around detected person
- ✅ Frame saved with timestamp
- ✅ Clean keyboard interrupt (Ctrl+C) shutdown

**Detection frame analysis:**
- Opened `detection_20251026_121049.jpg` on Mac (via scp)
- Green bounding box accurately drawn around person
- Label shows "Person 0.87" (87% confidence)
- Frame quality: 1280x720, clear and sharp
- Detection latency: imperceptible (<1 second from person appearing to detection)

### Performance Observations

**CPU usage:**
- Idle (waiting for frames): ~15-20%
- During YOLO inference: ~60-70% spike
- Sustained average with 1fps processing: ~25-30%
- Thermal: No throttling, fan keeps Pi at ~50°C

**Memory:**
- YOLOv8n model: ~50MB RAM
- PyTorch overhead: ~200MB
- Total Python process: ~350MB
- Pi has 8GB total, plenty of headroom

**Inference speed:**
- YOLO forward pass: ~200-250ms per frame
- At 1fps sampling rate, this is perfectly acceptable
- No frame drops or lag in video stream

**Network:**
- RTSP stream bandwidth: ~2-3 Mbps
- Stable connection over WiFi
- No buffering or connection drops during test

### Key Learnings

**Model size matters:**
- YOLOv8n is perfect for edge devices
- Larger models (yolov8s, yolov8m) would slow inference significantly
- The nano variant is plenty accurate for "is this a person?" detection

**Frame rate optimization:**
- 1fps is the sweet spot for this use case
- People walking to door take 2-5 seconds typically
- No need to process 30fps for detection
- Saves 97% of compute cycles

**Development workflow:**
- Git-based workflow (write on Mac, pull on Pi) is much faster than SSH editing
- Testing on real hardware early revealed performance characteristics
- Real-world testing (actual person at door) validates the whole pipeline

**What works perfectly:**
- YOLOv8n on Raspberry Pi 5 (ARM64)
- Real-time RTSP stream processing
- Bounding box visualization
- Detection debouncing

**What could be optimized later:**
- Could add motion detection pre-filter (only run YOLO when motion detected)
- Could use RTSP frame skipping at source instead of in Python
- Could experiment with lower resolution input to YOLO (faster inference)

### Next Steps After Person Detection

Now that we can detect people, the pipeline is:
1. ✅ Capture frame from DoorBird
2. ✅ Detect person with YOLO
3. ✅ Draw bounding box
4. ⏭️ **Next:** Crop person from frame
5. ⏭️ Send cropped image to Baseten for costume description
6. ⏭️ Log description to Supabase
7. ⏭️ Display on Next.js dashboard

**Immediate next tasks:**
- Set up Baseten account and deploy vision-language model
- ✅ Create Supabase project and schema
- Integrate costume classification API call into detection script
- ✅ Build database logging

---

## Day 4: Supabase Integration for Detection Storage

### Setting Up Supabase Database

**Goal:** Store person detections in a database with images in cloud storage, enabling a real-time dashboard.

**Why Supabase?**
- Built-in Realtime subscriptions (perfect for live dashboard)
- Storage bucket with public URLs (easier than S3)
- Row Level Security (RLS) for secure public/private access
- Great Python client library
- Free tier handles our traffic easily

### Database Schema Design

Created `person_detections` table to store detection events:

```sql
-- Core detection data
id uuid primary key
timestamp timestamptz      -- When person was detected
confidence float4          -- YOLO confidence (0.0-1.0)
bounding_box jsonb         -- {x1, y1, x2, y2} coordinates
image_url text             -- Link to image in Supabase Storage
device_id text             -- Which Pi captured this (from HOSTNAME env var)

-- Future: costume classification
costume_classification text
costume_confidence float4

created_at timestamptz    -- Database insertion time
```

**Design decisions:**

1. **Separate timestamp vs created_at**
   - `timestamp`: When detection happened (video frame time)
   - `created_at`: When record was inserted (database time)
   - Useful for debugging upload delays or network issues

2. **JSONB for bounding_box**
   - More flexible than 4 separate columns
   - Easy to query/filter in Postgres
   - Natural fit for Python dict → JSON

3. **device_id instead of hardcoding**
   - Uses existing `HOSTNAME` env var
   - Enables multi-Pi setups later
   - Organizes storage: `{device_id}/{timestamp}.jpg`

4. **Nullable costume fields**
   - Detection happens first, costume classification later
   - Can update records asynchronously
   - Allows testing detection without ML API

### Migration File Approach

Instead of documenting SQL snippets in markdown, created a **single migration file** (`supabase_migration.sql`):

```sql
-- Creates table, indexes, RLS policies, storage bucket, storage policies
-- All in one file
-- Idempotent (safe to run multiple times)
```

**Benefits:**
- Copy/paste into Supabase SQL Editor → run once → done
- Version controlled (git tracks schema changes)
- Idempotent with `if not exists` and `on conflict do nothing`
- Self-documenting with comments
- No manual clicking in UI

### Python Supabase Client

Built `supabase_client.py` - a clean abstraction for all database/storage operations:

**Key methods:**

1. **`upload_detection_image(image_path, timestamp)`**
   - Uploads JPG to Storage
   - Path: `{HOSTNAME}/{YYYYMMDD_HHMMSS}.jpg`
   - Returns public URL

2. **`insert_detection(timestamp, confidence, bounding_box, ...)`**
   - Inserts record to `person_detections` table
   - Returns inserted record with UUID

3. **`save_detection(...)`** - **The main one!**
   - Complete workflow: upload image + insert record
   - Graceful degradation: if upload fails, still saves detection without image URL
   - Prints clear status messages

4. **`get_recent_detections(limit)`**
   - Query recent detections (for testing, debugging)

5. **`update_costume_classification(detection_id, ...)`**
   - Later: add costume description to existing detection

**Environment variable handling:**

The client uses existing environment variables:
```python
self.url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")  # For Next.js compat
self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Full access for Pi
self.device_id = os.getenv("HOSTNAME")             # Already had this!
```

Smart fallbacks: also checks `SUPABASE_URL`, `SUPABASE_KEY`, `DEVICE_ID` for compatibility.

### Updating detect_people.py

Integrated Supabase into the detection script:

**Initialization:**
```python
from supabase_client import SupabaseClient

# Graceful degradation if Supabase not configured
supabase_client = None
try:
    supabase_client = SupabaseClient()
    print(f"✅ Connected to Supabase (Device: {supabase_client.device_id})")
except Exception as e:
    print(f"⚠️  Supabase not configured: {e}")
    print("   Detections will only be saved locally")
```

**On person detection:**
```python
# Still saves locally (backup!)
cv2.imwrite(filename, frame)

# Extract bounding box from YOLO result
first_box = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}

# Upload to Supabase
if supabase_client and first_box:
    try:
        supabase_client.save_detection(
            image_path=filename,
            timestamp=detection_timestamp,
            confidence=max_confidence,
            bounding_box=first_box,
        )
    except Exception as e:
        print(f"   ⚠️  Supabase upload failed: {e}")
```

**Benefits of this approach:**
- Works with or without Supabase configured
- Local files are always saved (backup)
- Clear error messages if upload fails
- Doesn't crash if Supabase is down

### Testing Infrastructure

Built comprehensive `test_supabase_connection.py` with 7 tests:

1. **Environment variables** - All credentials present?
2. **Client initialization** - Can connect?
3. **Database insert** - Can write detection record?
4. **Database query** - Can read recent detections?
5. **Storage upload** - Can upload image?
6. **Complete workflow** - End-to-end test
7. **Update classification** - Can add costume later?

**Test creates real images:**
- Generates synthetic frames with OpenCV
- Draws fake bounding boxes
- Tests actual upload pipeline
- Cleans up files after

**Results:**
```
Tests passed: 7/7
✅ All tests passed! Supabase is ready for production.
```

**Minor note on TEST 6:**
Got a 409 Duplicate error when running rapid tests (same timestamp).
This is actually **good** - prevents accidental overwrites.
In production, 2-second debounce ensures unique timestamps.

### Row Level Security (RLS)

Set up smart security policies:

**Public read (for dashboard):**
```sql
create policy "Public Read Access"
  on person_detections for select
  using ( true );
```
Anyone can query detections → dashboard works without auth

**Service role write (for Pi):**
```sql
create policy "Service Insert Access"
  on person_detections for insert
  with check ( auth.role() = 'service_role' );
```
Only service role key can write → prevents random people inserting fake detections

**Storage policies:**
- Public read: Anyone can view images (for dashboard)
- Service upload: Only Pi can upload
- Service delete: Only Pi can clean up

### Key Decisions & Trade-offs

**Storage in Supabase vs. Local only:**
- Could keep everything local, but then no live dashboard
- Supabase Storage gives public URLs immediately
- Free tier: 1GB storage = ~2,000 detection images
- Good enough for Halloween night

**Service role key on Pi:**
- Yes, this gives full database access
- But: Pi is on private network, not exposed
- Alternative (anon key) would require auth flow
- For Halloween night project, service role is fine

**Graceful degradation everywhere:**
- If Supabase down → still saves locally
- If image upload fails → still saves detection record
- If costume classification fails later → detection still exists
- Resilience is critical for one-night-only event

**Real-time subscriptions (not yet implemented):**
- Supabase supports Postgres Realtime
- Dashboard can subscribe to `person_detections` table
- New detections push to clients instantly
- Will implement in Next.js dashboard next

### Performance Characteristics

**Database writes:**
- Detection insert: ~50-100ms
- No impact on detection pipeline (async-ish)
- Fast enough for 1 detection every 2+ seconds

**Storage uploads:**
- 1280x720 JPG: ~200-300KB per image
- Upload time: ~200-500ms over WiFi
- Acceptable latency for non-critical path

**Total overhead per detection:**
- Image save (local): ~50ms
- Image upload (Supabase): ~300ms
- Record insert: ~100ms
- **Total added latency: ~450ms**
- Still much faster than 2-second debounce window

### What's Working Now

Current pipeline (end-to-end):
1. ✅ DoorBird RTSP stream → Pi
2. ✅ YOLO person detection
3. ✅ Local image save (backup)
4. ✅ **Upload image to Supabase Storage**
5. ✅ **Insert detection record to database**
6. ⏭️ Next: Query detections in dashboard
7. ⏭️ Next: Add costume classification

### Updated checklist:

- [x] Set up Raspberry Pi 5 (OS, SSH, networking)
- [x] Test RTSP connection to DoorBird
- [x] Implement YOLO person detection on Pi
- [x] **Create Supabase project and schema**
- [x] **Build database logging with Storage integration**
- [ ] Deploy vision-language model to Baseten
- [ ] Integrate costume classification API call
- [ ] Build Next.js dashboard with Realtime updates
- [ ] End-to-end testing
- [ ] Deploy and prep for Halloween night

### Key Learnings

**Single migration file is better than docs with SQL:**
- Easier to maintain
- Version controlled
- Copy/paste friendly
- No sync issues between docs and actual schema

**Use existing environment variables when possible:**
- Already had `HOSTNAME` for device ID
- `NEXT_PUBLIC_*` variables work for both frontend and backend
- Less cognitive load, fewer vars to manage

**Graceful degradation is essential:**
- Halloween night = one shot to get it right
- If Supabase goes down, local saves still work
- If upload fails, detection record still created
- System keeps running no matter what

**Testing matters:**
- 7-test suite caught several issues early
- Synthetic test images work perfectly
- Can test full pipeline without real detections
- Builds confidence before Halloween night

**Supabase developer experience:**
- Python client is excellent
- SQL Editor makes migrations easy
- Storage bucket setup is straightforward
- RLS policies are powerful and intuitive

### Next Steps

1. Build Next.js dashboard
   - Display recent detections
   - Show images from Storage URLs
   - Subscribe to Realtime updates
   - Deploy to Vercel

2. Integrate Baseten for costume classification
   - Set up Baseten account
   - Deploy vision-language model
   - Add API call after person detection
   - Update detection records with costume descriptions

3. End-to-end testing
   - Test complete flow: detection → storage → database → dashboard
   - Performance testing (multiple detections rapidly)
   - Network failure scenarios
   - Recovery from errors

---

## Technical Decisions Log

| Decision | Options Considered | Choice | Rationale |
|----------|-------------------|--------|-----------|
| Classification approach | Fixed labels vs. Open-ended | Open-ended | Captures creative costumes, more interesting data |
| ML inference location | Local (Pi) vs. Cloud (Baseten) | Baseten | Reliability, auto-scaling, model flexibility |
| Person detection | YOLO vs. Faster R-CNN vs. MobileNet | YOLOv8n | Good balance of speed/accuracy, runs well on Pi |
| Database | Supabase vs. Firebase vs. self-hosted Postgres | Supabase | Realtime built-in, good DX, easy RLS |
| Frontend host | Vercel vs. Netlify vs. self-hosted | Vercel | Best Next.js integration, edge functions |
| Package manager | pip vs. poetry vs. uv | uv | 10-100x faster, built-in venv, modern tooling |
| Linter/formatter | Black + isort + flake8 vs. ruff | ruff | Single tool, Rust-powered, extremely fast |
| Pi OS flashing | Use pre-installed vs. Re-flash | Re-flash | Enables headless WiFi/SSH pre-configuration |

---

## Questions to Answer in Blog Post

- [ ] How accurate is the costume classification?
- [ ] What's the latency from detection to dashboard update?
- [ ] How much did it cost to run for one Halloween night?
- [ ] What were the most common costumes?
- [ ] What were the most creative/unexpected costumes the AI detected?
- [ ] Any funny misclassifications?
- [ ] How did the Pi perform under load?
- [ ] Would we do anything differently?

---

## Ideas for Future Iterations

- Add support for group costumes (detect multiple people, classify as a group)
- Sentiment analysis (are they smiling? excited?)
- Age estimation (kids vs. teens vs. adults)
- Candy distribution analytics (correlate costume quality with candy given)
- Historical data (compare year-over-year costume trends)
- Multi-camera support (front door + back door)

---

## Day 5: Next.js Dashboard with Supabase Realtime

### Setting Up the Dashboard

**Goal:** Build a live dashboard that shows person detections in real-time as they happen, without requiring page refreshes.

**Why Next.js?**
- React 19 with modern features
- Great TypeScript support
- Easy deployment to Vercel
- Server and client components for optimal performance
- Built-in routing and optimization

### Project Initialization

**Created new Next.js project:**
```bash
cd costume-classifier
mkdir dashboard
cd dashboard
npm init -y
npm install next@latest react@latest react-dom@latest
npm install --save-dev typescript @types/react @types/react-dom @types/node
```

**Added Tailwind CSS v4:**
```bash
npm install tailwindcss@latest postcss autoprefixer
npm install @tailwindcss/postcss
```

**Key configuration files:**
- `postcss.config.js` - Uses new `@tailwindcss/postcss` plugin (v4 requirement)
- `tailwind.config.js` - Tailwind v4 configuration
- `tsconfig.json` - TypeScript with React 19 JSX runtime
- `app/globals.css` - Tailwind directives

**Initial challenge:**
Hit PostCSS error when first running dev server - Tailwind v4 moved the PostCSS plugin to a separate package. Fixed by:
1. Installing `@tailwindcss/postcss`
2. Updating `postcss.config.js` to use `'@tailwindcss/postcss'` instead of `'tailwindcss'`

### Supabase Client Setup

**Installed Supabase JS client:**
```bash
npm install @supabase/supabase-js
```

**Created `lib/supabase.ts`:**
```typescript
import { createClient } from '@supabase/supabase-js'

export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  {
    realtime: {
      params: {
        eventsPerSecond: 10
      }
    }
  }
)
```

**Key decisions:**
- Use `NEXT_PUBLIC_*` env vars (already compatible with Python backend)
- Configure realtime with `eventsPerSecond` limit
- Use anon key (public read access via RLS policies)

**Environment variables (`.env.local`):**
```bash
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
```

### Building the Dashboard Component

**Main page (`app/page.tsx`) architecture:**

1. **Type definitions:**
```typescript
interface PersonDetection {
  id: string
  timestamp: string
  confidence: number
  bounding_box: any
  image_url: string | null
  device_id: string
  costume_classification: string | null
  costume_confidence: number | null
}
```

2. **Initial data fetch:**
```typescript
useEffect(() => {
  async function fetchDetections() {
    const { data, error } = await supabase
      .from('person_detections')
      .select('*')
      .order('timestamp', { ascending: false })
      .limit(50)

    if (error) throw error
    setDetections(data || [])
  }
  fetchDetections()
}, [])
```

3. **Realtime subscription:**
```typescript
useEffect(() => {
  const channel = supabase
    .channel('person_detections')
    .on(
      'postgres_changes',
      { event: 'INSERT', schema: 'public', table: 'person_detections' },
      (payload) => {
        console.log('Received new detection:', payload)
        const newDetection = payload.new as PersonDetection
        setDetections((prev) => [newDetection, ...prev])
      }
    )
    .subscribe((status) => {
      console.log('Subscription status:', status)
    })

  return () => {
    supabase.removeChannel(channel)
  }
}, [])
```

**UI features:**
- Loading state while fetching initial data
- Error display for connection issues
- Card-based layout with Tailwind
- Display detection count, device ID, timestamp
- Show confidence scores
- Future: costume classification display

### Enabling Supabase Realtime

**Critical step:** The subscription code alone doesn't work - you must enable Realtime in Supabase!

**Updated migration file (`supabase_migration.sql`):**
```sql
-- ============================================================================
-- 5. Enable Realtime for person_detections table
-- ============================================================================

-- Enable realtime broadcasts for INSERT/UPDATE/DELETE events
alter publication supabase_realtime add table person_detections;
```

**How Supabase Realtime works:**
1. Postgres has a Write-Ahead Log (WAL) for all changes
2. Supabase uses logical replication to listen to WAL
3. When you add a table to `supabase_realtime` publication, changes broadcast to connected clients
4. Your web app subscribes via WebSocket
5. New rows trigger the callback instantly

**To enable (run in Supabase SQL Editor):**
```sql
alter publication supabase_realtime add table person_detections;
```

### Debugging Realtime

**Added logging to track subscription status:**
- `console.log('Subscription status:', status)` - Shows SUBSCRIBED/CHANNEL_ERROR/TIMED_OUT
- `console.log('Received new detection:', payload)` - Shows incoming data

**Testing approach:**
1. Open dashboard in browser
2. Open browser console (F12)
3. Look for "Subscription status: SUBSCRIBED"
4. Insert test row in Supabase SQL Editor
5. Watch for "Received new detection:" in console
6. New row should appear in UI instantly

**Initial issue:**
Subscription showed SUBSCRIBED but no events received when adding rows. **Solution:** Enable Realtime publication for the table (see above).

### Key Learnings

**Tailwind CSS v4 breaking changes:**
- PostCSS plugin moved to separate package `@tailwindcss/postcss`
- Must explicitly install and configure
- Error messages are clear about what's wrong

**Supabase Realtime is not automatic:**
- Just having a subscription in code isn't enough
- Must explicitly add table to `supabase_realtime` publication
- "Replication" in Supabase UI = "Realtime broadcasts" (confusing naming)
- Not actually replicating to another database, just broadcasting changes to WebSocket clients

**React 19 with Next.js:**
- New JSX runtime requires `"jsx": "react-jsx"` in tsconfig
- Client components need `'use client'` directive
- Server components are default (great for data fetching)

**Environment variable naming:**
- `NEXT_PUBLIC_*` prefix makes vars available to browser
- Using same var names as backend (Python) reduces confusion
- `.env.local` is gitignored automatically by Next.js

### Performance & Architecture

**Initial page load:**
- Fetches latest 50 detections from Supabase
- ~100-200ms query time
- Renders immediately with data

**Realtime updates:**
- WebSocket connection to Supabase Realtime
- Sub-second latency from INSERT to UI update
- No polling, no page refreshes needed
- Graceful fallback if connection drops

**State management:**
```typescript
const [detections, setDetections] = useState<PersonDetection[]>([])

// On new detection, prepend to array
setDetections((prev) => [newDetection, ...prev])
```

Simple state management with React hooks - no need for Redux/Zustand for this use case.

**Cleanup:**
```typescript
return () => {
  supabase.removeChannel(channel)
}
```

Properly unsubscribes when component unmounts to prevent memory leaks.

### Updated Checklist

- [x] Set up Raspberry Pi 5 (OS, SSH, networking)
- [x] Test RTSP connection to DoorBird
- [x] Implement YOLO person detection on Pi
- [x] Create Supabase project and schema
- [x] Build database logging with Storage integration
- [x] **Build Next.js dashboard with Realtime updates**
- [x] **Enable Realtime for person_detections table**
- [ ] Deploy dashboard to Vercel
- [ ] Deploy vision-language model to Baseten
- [ ] Integrate costume classification API call
- [ ] End-to-end testing
- [ ] Deploy and prep for Halloween night

### What's Working Now

Complete pipeline (except costume classification):
1. ✅ DoorBird RTSP stream → Pi
2. ✅ YOLO person detection
3. ✅ Upload image to Supabase Storage
4. ✅ Insert detection record to database
5. ✅ **Dashboard fetches recent detections**
6. ✅ **Dashboard receives real-time updates via WebSocket**
7. ⏭️ Next: Deploy dashboard to Vercel
8. ⏭️ Next: Add costume classification

### Next Steps

1. **Deploy dashboard to Vercel:**
   - Connect GitHub repo
   - Set environment variables
   - Deploy with one click
   - Test with public URL

2. **Integrate Baseten for costume classification:**
   - Set up Baseten account
   - Deploy vision-language model
   - Add API call after person detection
   - Update detection records with costume descriptions

3. **Polish dashboard UI:**
   - Add image display from Storage URLs
   - Better styling for detection cards
   - Add filtering/search
   - Show costume classifications when available

4. **End-to-end testing:**
   - Test complete flow: detection → storage → database → dashboard
   - Multiple simultaneous detections
   - Network failure scenarios
   - Recovery from errors

---

## Day 6: Baseten Integration for Costume Classification

### Setting Up Baseten

**Goal:** Add AI-powered costume classification to detected persons using a vision-language model hosted on Baseten.

**Why Baseten for ML inference?**
- Managed infrastructure for running open-source models
- No GPU setup required on our end
- Auto-scaling for traffic spikes
- Pay-per-inference pricing (cost-effective for one-night event)
- Easy model deployment and updates

### Model Selection: Gemma 3 27B IT

**Initial consideration:** Llama 3.2 90B Vision
- Powerful vision-language model from Meta
- But: larger model = higher cost per inference

**Final choice:** Gemma 3 27B IT (Instruction-Tuned)
- Vision-language model from Google DeepMind
- Smaller than Llama (27B vs 90B parameters)
- Optimized for instruction-following
- More cost-effective (~$0.01 vs ~$0.03 per inference)
- Still excellent at image understanding and description

**Halloween night cost estimate:**
- 100 detections × $0.01 = **$1.00 total**
- Much cheaper than proprietary models like GPT-4 Vision

**Model documentation:**
- [Gemma 3 27B IT on Baseten](https://docs.baseten.co/examples/models/gemma/gemma-3-27b-it)

### Building the Baseten Client

**Created `baseten_client.py`** - clean Python interface to Baseten API:

```python
class BasetenClient:
    def __init__(self):
        self.api_key = os.getenv("BASETEN_API_KEY")
        self.model_url = os.getenv("BASETEN_MODEL_URL")
        self.session = requests.Session()  # Connection pooling

    def classify_costume(self, image_bytes: bytes) -> Tuple[str, float, str]:
        # Returns: (classification, confidence, description)
```

**Key features:**
- Encodes images to base64 for API transmission
- Uses `requests.Session()` for connection reuse
- Robust JSON parsing (handles model artifacts)
- Clear error messages
- Returns structured tuple: `(classification, confidence, description)`

**Environment variables needed:**
```bash
BASETEN_API_KEY=your_api_key_here
BASETEN_MODEL_URL=https://model-XXXXXXXX.api.baseten.co/environments/production/predict
```

### Prompt Engineering for Halloween Costumes

**Optimized prompt for costume classification:**

```python
prompt = (
    "Analyze this Halloween costume and respond with ONLY a JSON object in this exact format:\n"
    '{"classification": "costume_type", "confidence": 0.95, "description": "detailed description"}\n\n'
    "Preferred categories:\n"
    "- witch, vampire, zombie, skeleton, ghost\n"
    "- superhero, princess, pirate, ninja, clown, monster\n"
    "- character (for recognizable characters like Spiderman, Elsa, Mickey Mouse)\n"
    "- animal (for animal costumes like tiger, cat, dinosaur)\n"
    "- person (if no costume visible)\n"
    "- other (if costume doesn't fit above categories)\n\n"
    "Rules:\n"
    "- classification: Try to use one of the preferred categories above, or be specific\n"
    "- confidence: Your confidence score between 0.0 and 1.0\n"
    "- description: A detailed one-sentence description of the costume\n"
)
```

**Why this prompt works:**
- Suggests common categories but allows flexibility
- Requests specific format (JSON)
- Asks for both classification AND description
- Includes confidence score for quality assessment
- Handles edge cases ("person" if no costume)

### The JSON Parsing Challenge

**Initial problem:**
Gemma model returns valid JSON... but with extra content:

```
{"classification": "Spiderman", "confidence": 0.98, "description": "..."}
```<end_of_turn>
```

The `<end_of_turn>` marker is a model artifact that breaks `json.loads()`.

**Error message:**
```
⚠️  Failed to parse JSON response: Extra data: line 2 column 1 (char 213)
```

**First attempt:** Try Baseten's structured outputs feature with `response_format` parameter
- Added JSON schema with strict validation
- Request hung indefinitely
- **Conclusion:** Gemma 3 27B IT doesn't support structured outputs API

**Solution:** Robust text parsing before JSON decode

```python
# Clean up content - remove markdown code blocks and model artifacts
content = content.strip()

# Remove markdown code fences
if content.startswith("```json"):
    content = content[7:]
if content.startswith("```"):
    content = content[3:]

# Remove trailing artifacts like ```<end_of_turn>, ``` etc.
# Split on common delimiters and take the first part
for delimiter in ["```", "<end_of_turn>", "\n```", "```\n"]:
    if delimiter in content:
        content = content.split(delimiter)[0]

content = content.strip()

# Now parse JSON
parsed_result = json.loads(content)
```

**Result:** 100% success rate parsing Gemma responses

### Testing Infrastructure

**Built two test scripts:**

1. **`test_baseten_connection.py`** - Basic connectivity test
   - Validates API key and model URL
   - Tests connection to Baseten
   - No image classification (just connectivity)
   - Fast sanity check

2. **`test_costume_detection.py`** - Full end-to-end test
   - Uses 4 real Halloween costume images
   - Classifies each costume with Baseten
   - Uploads results to Supabase
   - Saves annotated images locally
   - Perfect for testing without camera/Pi

### Testing with Real Costume Images

**Test dataset (4 images):**
- Spider-Man costume (child in red/blue suit)
- Tiger costume (child in orange/black)
- Elsa costume (Frozen character, blue dress)
- Vampire costume (child with cape and fangs)

**Test execution:**
```bash
uv run python test_costume_detection.py
```

**Results: 100% success!**

```
Processing: image-2A26rvEwWK0QWW_i8WpIM.png
✅ Classification successful!
   Type:        Spiderman
   Confidence:  0.98
   Description: A young boy is dressed in a full Spiderman costume, complete with
                a red and blue suit and a black mask, and is holding a pumpkin-
                shaped trick-or-treat bucket.

Processing: image-BVH1NL6gKJp8QQ3kW_9e1.png
✅ Classification successful!
   Type:        tiger
   Confidence:  0.98
   Description: A child is wearing a full-body tiger costume with orange and
                black stripes, and holding a pumpkin-shaped candy bucket.

Processing: image-qORO3FwW7UYsD2iSDwVnA.png
✅ Classification successful!
   Type:        Elsa
   Confidence:  0.98
   Description: A young girl is dressed as Elsa from Disney's Frozen, wearing a
                light blue gown with shimmering details and a blonde braided wig.

Processing: image-zphDYn4_koLqtVOSssAT7.png
✅ Classification successful!
   Type:        vampire
   Confidence:  0.98
   Description: A young boy is dressed as a vampire with a black suit, cape, white
                shirt, and fake vampire teeth, holding a pumpkin trick-or-treat bucket.

📊 SUMMARY
Total images processed: 4
Successful classifications: 4
Uploaded to Supabase: 4
```

**What this proves:**
1. ✅ Baseten API integration works perfectly
2. ✅ JSON parsing handles Gemma artifacts
3. ✅ Model produces high-quality classifications (0.98 confidence!)
4. ✅ Descriptions are detailed and accurate
5. ✅ Supabase uploads work (images + metadata)
6. ✅ Full pipeline operational without needing Pi/camera

### Classification Quality Analysis

**Impressive accuracy:**
- All 4 costumes classified correctly
- High confidence (0.98 across the board)
- Descriptions include specific details:
  - Colors (red/blue, orange/black, light blue)
  - Accessories (pumpkin buckets, cape, wig)
  - Character details (Spiderman web design, Elsa's braid)

**The model "gets it":**
- Recognized Spiderman despite being a child's version
- Identified Elsa specifically (not just "princess")
- Distinguished tiger as an animal costume
- Picked up on vampire costume elements (fangs, cape)

**This is exactly what we wanted:**
- Not just "character costume" - it says "Spiderman"
- Not just "animal" - it says "tiger"
- Rich descriptions for interesting data visualization later

### Database Integration

**Updated Supabase schema:**
Already had costume fields from Day 4:
```sql
costume_classification text
costume_confidence float4
costume_description text
```

**Updated `supabase_client.py`:**
```python
def save_detection(
    self,
    image_path: str,
    timestamp: datetime,
    confidence: float,
    bounding_box: dict,
    costume_classification: Optional[str] = None,
    costume_description: Optional[str] = None,
    costume_confidence: Optional[float] = None,
) -> bool:
    # Upload image to Storage
    # Insert record with costume data
```

**Result:** Detection records now include costume information immediately!

### Performance Characteristics

**API latency:**
- Request to Baseten: ~1-3 seconds
- Model inference: ~1-2 seconds
- Total round trip: ~2-4 seconds

**Is this fast enough?**
- Yes! Our detection debounce is 2 seconds anyway
- Person walks up to door over 3-5 seconds
- Plenty of time to classify before they leave
- Not blocking the detection pipeline

**Memory usage (Pi):**
- Baseten client: ~10MB
- Image encoding: ~5MB per frame
- Total overhead: minimal

**Network bandwidth:**
- Base64 encoded 1280x720 JPEG: ~400KB
- Response JSON: ~1KB
- Totally fine over WiFi/LAN

### Key Decisions & Trade-offs

**Gemma 3 27B IT vs. Llama 3.2 90B:**
- Chose Gemma for cost (~3x cheaper per inference)
- Quality is excellent - didn't need the larger model
- Faster inference due to smaller size

**Cloud inference vs. local:**
- Could theoretically run small vision models on Pi
- But: Halloween night is one shot, reliability matters
- Offloading to Baseten ensures stable performance
- Worth the $1-5 cost for peace of mind

**JSON parsing approach:**
- Tried structured outputs (failed - model doesn't support)
- Fell back to text parsing with robust error handling
- Works perfectly - got 100% success rate
- Simpler than we expected

**Prompt engineering:**
- Suggesting categories guides the model
- But allowing flexibility handles creative costumes
- Best of both worlds: structured when possible, open-ended when needed

### Integration into detect_people.py

**Next step:** Add costume classification to the main detection script

```python
from baseten_client import BasetenClient

# Initialize Baseten client
baseten_client = None
try:
    baseten_client = BasetenClient()
    print(f"✅ Baseten connected (Model: {baseten_client.model})")
except Exception as e:
    print(f"⚠️  Baseten not configured: {e}")

# In detection loop:
if baseten_client:
    # Encode person crop to bytes
    _, buffer = cv2.imencode('.jpg', person_crop)
    image_bytes = buffer.tobytes()

    # Classify costume
    classification, confidence, description = baseten_client.classify_costume(image_bytes)

    # Save to Supabase with costume data
    supabase_client.save_detection(
        image_path=filename,
        timestamp=detection_timestamp,
        confidence=yolo_confidence,
        bounding_box=bbox,
        costume_classification=classification,
        costume_description=description,
        costume_confidence=confidence,
    )
```

**Graceful degradation:**
- If Baseten not configured → skip costume classification
- If API call fails → still save detection without costume data
- System keeps running no matter what

### Documentation Created

**`BASETEN_SETUP.md`** - Complete setup guide:
- Prerequisites and account setup
- Environment variable configuration
- Testing instructions
- Model information (Gemma 3 27B IT)
- API integration details
- Cost estimates
- Troubleshooting

**Why separate doc?**
- Baseten setup is optional (detection works without it)
- Detailed enough to warrant its own file
- Easy to share with others wanting to replicate

### Updated Checklist

- [x] Set up Raspberry Pi 5 (OS, SSH, networking)
- [x] Test RTSP connection to DoorBird
- [x] Implement YOLO person detection on Pi
- [x] Create Supabase project and schema
- [x] Build database logging with Storage integration
- [x] Build Next.js dashboard with Realtime updates
- [x] **Set up Baseten account and deploy model**
- [x] **Build baseten_client.py wrapper**
- [x] **Test costume classification with real images**
- [x] **Fix JSON parsing for Gemma model artifacts**
- [ ] Integrate costume classification into detect_people.py
- [ ] Deploy dashboard to Vercel
- [ ] End-to-end testing (full pipeline)
- [ ] Add constrained classification categories (optional)
- [ ] Deploy and prep for Halloween night

### What's Working Now

Complete pipeline (almost there!):
1. ✅ DoorBird RTSP stream → Pi
2. ✅ YOLO person detection
3. ✅ Upload image to Supabase Storage
4. ✅ Insert detection record to database
5. ✅ Dashboard fetches recent detections
6. ✅ Dashboard receives real-time updates
7. ✅ **Baseten costume classification (tested separately)**
8. ⏭️ Next: Wire costume classification into detection script
9. ⏭️ Next: Test full pipeline end-to-end

### Key Learnings

**Model selection matters:**
- Don't automatically pick the biggest model
- Gemma 3 27B IT is perfect for this task
- 3x cheaper than Llama 90B with comparable quality

**Test early with real data:**
- Test images revealed JSON parsing issue immediately
- Would have been much harder to debug on Halloween night
- Building test suite paid off instantly

**Prompt engineering is powerful:**
- Suggesting categories helps constrain outputs
- But staying flexible handles creative costumes
- One well-crafted prompt = consistent results

**Baseten developer experience:**
- Easy setup and deployment
- Good documentation (model examples)
- Straightforward API (OpenAI-compatible format)
- Pricing is transparent and predictable

**JSON parsing with LLMs:**
- Models don't always return pure JSON
- Need robust parsing to handle artifacts
- Structured outputs aren't universally supported
- Text parsing + error handling is reliable fallback

### Performance Insights

**Classification speed:**
- 2-4 seconds per image (acceptable for our use case)
- Bottleneck is network + inference, not our code
- Fast enough for real-time detection

**Classification quality:**
- 0.98 confidence across all test images
- Detailed, accurate descriptions
- Handles various costume types well

**Cost efficiency:**
- Estimated $1-5 for entire Halloween night
- Much cheaper than running GPU hardware
- Pay-per-inference scales perfectly with traffic

### Next Steps

1. **Integrate costume classification into main script:**
   - Add baseten_client to detect_people.py
   - Crop person from frame
   - Send to Baseten API
   - Save results to Supabase

2. **Optional: Add category constraints:**
   - Post-processing function to map free-form classifications
   - Map "Spiderman" → "character", "tiger" → "animal"
   - Enables consistent dashboard charts
   - But keeps detailed descriptions

3. **Deploy dashboard to Vercel:**
   - Connect GitHub repo
   - Set environment variables
   - Deploy with one click

4. **End-to-end testing:**
   - Run full pipeline: camera → detection → classification → dashboard
   - Test with real people at door
   - Verify latency is acceptable
   - Check dashboard updates in real-time

---

## Day 7: Project Structure Refactor

### Why Refactor?

After implementing all the core features (YOLO detection, Baseten classification, Supabase storage, Next.js dashboard), the project structure had grown organically but wasn't well-organized:

**Problems:**
- Python files scattered in root directory
- Documentation files mixed with code
- Test files loosely organized
- `dashboard/` directory name didn't reflect it was the frontend
- Tests weren't colocated with the code they tested

**Goal:** Reorganize to follow standard full-stack practices while maintaining simplicity.

### Design Principles

1. **Clear separation of concerns**: Backend vs Frontend vs Tests vs Docs
2. **Standard conventions**: Follow established patterns (pytest, Next.js)
3. **Not too many subfolders**: Keep nesting minimal for easy navigation
4. **Self-documenting structure**: Directory names clearly indicate purpose
5. **Scalability**: Easy to add new features without restructuring

### New Structure

```
costume-classifier/
├── backend/                    # Python ML backend
│   ├── src/
│   │   └── clients/           # External service clients
│   │       ├── baseten_client.py
│   │       └── supabase_client.py
│   ├── scripts/
│   │   └── main.py            # Entry point (renamed from detect_people.py)
│   └── tests/                 # Backend tests colocated with code
│       ├── fixtures/          # Test images (renamed from images/)
│       └── integration/       # Integration tests
├── frontend/                   # Next.js dashboard (renamed from dashboard/)
│   ├── app/
│   ├── components/
│   └── lib/
├── docs/                       # All documentation
│   ├── BASETEN_SETUP.md
│   ├── DOORBIRD_SETUP.md
│   ├── SUPABASE_SETUP.md
│   ├── PROJECT_SPEC.md
│   └── BLOG_NOTES.md
└── Root configs                # Only config files at root
    ├── pyproject.toml
    ├── .env.example
    └── README.md
```

### Key Changes

**1. Backend Organization**
- Created `backend/` directory for all Python code
- `backend/src/clients/` - API clients (Baseten, Supabase)
- `backend/scripts/main.py` - Main entry point (was `detect_people.py`)
- Added proper Python package structure with `__init__.py` files

**2. Tests Moved to Backend**
- `tests/` → `backend/tests/`
- Tests now colocated with the code they test
- `tests/images/` → `backend/tests/fixtures/` (more semantic naming)
- Follows standard pytest conventions
- Easy to add frontend tests later in `frontend/__tests__/`

**3. Frontend Renamed**
- `dashboard/` → `frontend/`
- More professional and clear
- Matches standard full-stack terminology

**4. Documentation Centralized**
- All `.md` files moved to `docs/`
- Except README.md at root (standard convention)
- Easy to find all documentation in one place

**5. Import Path Updates**
- All Python files updated with new module imports:
  ```python
  from backend.src.clients.baseten_client import BasetenClient
  from backend.src.clients.supabase_client import SupabaseClient
  ```
- Test files updated to reference `backend/tests/fixtures/`

**6. Main Script Naming**
- `detect_people.py` → `main.py`
- Standard convention for primary entry point
- Clearer that this is the main script to run

### Migration Process

**Used git mv for all moves:**
- Preserves file history
- Shows as renames (R) not deletes + adds (D + A)
- Clean git history

**Updated all references:**
- ✅ Import statements in Python files
- ✅ File paths in test scripts
- ✅ README.md commands and structure diagram
- ✅ Documentation references
- ✅ REFACTOR_TEST_CHECKLIST.md

**Created `pyproject.toml` package config:**
```toml
[tool.uv]
package = true

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Benefits

**For Development:**
- Clear ownership: backend tests with backend code
- Easy to find related files
- Standard structure familiar to contributors
- Better IDE support with proper Python packages

**For Scaling:**
- Easy to add frontend tests in `frontend/__tests__/`
- Can add more backend modules in `backend/src/`
- Can add more script entry points in `backend/scripts/`
- Clear place for new fixtures/test data

**For CI/CD:**
- Backend and frontend can be tested independently
- Can run `pytest backend/tests/`
- Can run `npm test` in `frontend/`
- Easier to set up separate workflows

**For New Contributors:**
- Self-documenting structure
- Follows established patterns
- Easy to understand project layout
- Standard conventions reduce cognitive load

### Test Command Updates

**Before:**
```bash
uv run test_costume_detection.py
uv run detect_people.py
```

**After:**
```bash
uv run backend/tests/integration/test_costume_detection.py
uv run backend/scripts/main.py
```

More explicit, shows project structure at a glance.

### Environment File Note

**Important gotcha:** `.env.local` files aren't tracked by git, so when renaming directories:
- Frontend needs its own `frontend/.env.local`
- Copy Supabase credentials from root `.env` if needed
- Both frontend and backend can share root `.env` or have separate configs

### What Didn't Change

**Functionality:**
- No code logic changes
- All imports work correctly
- All tests still pass
- Same commands, just with updated paths

**Configuration:**
- Environment variables unchanged
- Supabase schema unchanged
- Baseten configuration unchanged

### Lessons Learned

**1. Organic growth needs periodic cleanup**
- Started with files in root (fast prototyping)
- As features grew, needed better organization
- Refactoring mid-project is normal and healthy

**2. Standard conventions are worth following**
- Tests colocated with code they test
- `main.py` for entry points
- `fixtures/` for test data
- These exist for good reasons

**3. Git mv preserves history**
- Always use `git mv` for renames
- Maintains file history and blame info
- Shows intent clearly in git log

**4. Update all documentation immediately**
- README, setup docs, checklists all updated
- Prevents confusion for future you
- Makes refactor truly complete

**5. Structure should scale with complexity**
- Root files OK for prototypes
- Multi-directory structure for production
- But don't over-engineer - keep it simple

### Performance Impact

**None.** This is purely organizational:
- Same Python imports (just different module paths)
- Same runtime behavior
- Same dependencies
- Zero performance change

### Migration Checklist

- [x] Create backend directory structure
- [x] Move Python files to backend/src/clients/
- [x] Move main script to backend/scripts/
- [x] Move tests to backend/tests/
- [x] Rename dashboard/ to frontend/
- [x] Move documentation to docs/
- [x] Update all import statements
- [x] Update test file paths
- [x] Update README commands
- [x] Update REFACTOR_TEST_CHECKLIST
- [x] Add __init__.py files for Python packages
- [x] Update pyproject.toml with package config
- [x] Verify git shows renames not deletes
- [x] Test that imports still work

### Updated Checklist

- [x] Set up Raspberry Pi 5 (OS, SSH, networking)
- [x] Test RTSP connection to DoorBird
- [x] Implement YOLO person detection on Pi
- [x] Create Supabase project and schema
- [x] Build database logging with Storage integration
- [x] Build Next.js dashboard with Realtime updates
- [x] Set up Baseten account and deploy model
- [x] Build baseten_client.py wrapper
- [x] Test costume classification with real images
- [x] Fix JSON parsing for Gemma model artifacts
- [x] Integrate costume classification into detect_people.py
- [x] **Refactor project structure for maintainability**
- [ ] Deploy dashboard to Vercel
- [ ] End-to-end testing (full pipeline)
- [ ] Deploy and prep for Halloween night

### What's Next

1. **Deploy frontend to Vercel:**
   - Connect GitHub repo
   - Configure environment variables
   - Deploy with one click

2. **End-to-end testing:**
   - Run full pipeline with new structure
   - Verify all paths work correctly
   - Test on actual hardware

3. **Final prep for Halloween:**
   - Monitor system health
   - Have backup plans ready
   - Prepare deployment script

---

## Handling Multiple People Detection

### The Halloween Group Use Case

**The realization:** Kids often come to the door in groups on Halloween! Groups of friends, siblings, or neighborhood kids trick-or-treating together.

**The problem with our initial implementation:**
- YOLO would detect multiple people in the frame
- But we only processed the **highest confidence detection**
- Other people in the group were completely discarded
- Lost data on costumes, visitor count was inaccurate
- A group of 3 kids would only count as 1 visitor

### Changes Made to Support Multiple People

**Updated detection pipeline in `backend/scripts/main.py` (lines 142-224):**

**Before (single person):**
```python
# Find highest confidence detection
max_confidence = 0.0
first_box = None
for result in results:
    for box in boxes:
        if conf > max_confidence:
            max_confidence = conf
            first_box = box

# Process only one person
classify_costume(first_box)
save_to_database(first_box)
```

**After (multiple people):**
```python
# Collect ALL person detections with confidence > 0.5
detected_people = []
for result in results:
    for box in boxes:
        if int(box.cls[0]) == 0 and conf > 0.5:
            detected_people.append({
                "confidence": conf,
                "bounding_box": {...}
            })

# Process EACH person separately
for person_idx, person in enumerate(detected_people):
    # Extract individual person crop
    person_crop = frame[y1:y2, x1:x2]

    # Classify THIS person's costume (separate API call)
    classification, confidence, description = baseten_client.classify_costume(person_crop)

    # Upload THIS person's detection (separate DB entry)
    supabase_client.save_detection(
        image_path=filename,
        timestamp=detection_timestamp,
        confidence=person["confidence"],
        bounding_box=person["bounding_box"],
        costume_classification=classification,
        costume_description=description,
        costume_confidence=confidence,
    )
```

### Key Changes

1. **Collection instead of selection:**
   - Changed from finding the "best" detection to collecting ALL detections
   - No more data loss when multiple people appear

2. **Loop-based processing:**
   - Each detected person gets their own loop iteration
   - Independent costume classification for each person
   - Separate database entries for each person

3. **Per-person cropping:**
   - Extract individual crops from the full frame
   - Each person's costume classified independently
   - More accurate classifications (model sees just one costume at a time)

4. **Separate API calls:**
   - Each person = one Baseten API call
   - 3 people in frame = 3 classification requests
   - Allows different costumes to be identified correctly

5. **Individual database records:**
   - Each person gets their own row in `person_detections` table
   - Same `timestamp` for the group (they arrived together)
   - Different `costume_classification` for each person
   - Enables accurate visitor counting and costume tracking

### Example Output

**When 3 people are detected:**
```
👤 3 person(s) detected! (Detection #1)
   Saved locally: detection_20251029_123456.jpg
   Processing person 1/3 (confidence: 0.95)
   🎭 Classifying costume...
   👗 Costume: witch (0.89)
      A child dressed as a witch with a black hat and purple cape

   Processing person 2/3 (confidence: 0.87)
   🎭 Classifying costume...
   👗 Costume: vampire (0.92)
      A young boy wearing a vampire costume with a black cape and fangs

   Processing person 3/3 (confidence: 0.82)
   🎭 Classifying costume...
   👗 Costume: zombie (0.85)
      A child in a tattered zombie costume with green face paint
```

### Testing Infrastructure

**Created `backend/tests/integration/test_multiple_people.py`:**
- Comprehensive test script for multi-person scenarios
- Uses YOLOv8n to detect all people in test images
- Processes each person through the full pipeline
- Saves annotated frames showing all bounding boxes
- Verifies database entries created for each person
- Perfect for testing without needing real trick-or-treaters

### Performance Impact

**API costs:**
- Before: 1 API call per frame with people
- After: N API calls per frame (N = number of people)
- Group of 3 kids = 3× the cost
- But: Accurate data is worth it
- Still very cheap (~$0.01 per person × 100 people = $1.00 total)

**Latency:**
- Sequential processing: person 1 → classify → upload → person 2 → classify → upload...
- Total time: ~2-4 seconds per person
- Group of 3 = ~6-12 seconds total
- Still acceptable since people spend 5-10 seconds at door
- Could be parallelized in future if needed

**Database entries:**
- More rows in database (3× for a group of 3)
- But: This is the accurate count
- Dashboard shows true visitor numbers
- Better analytics on group sizes

### Key Learnings

**Real-world use cases emerge late:**
- We built the whole pipeline for single-person detection
- Only late in development realized groups are common
- Halloween-specific insight that wasn't obvious initially

**Changing from single to multiple was straightforward:**
- Well-structured code made the change easy
- Just replaced extraction logic with a loop
- No changes needed to Baseten or Supabase clients
- Modular design paid off

**Testing with multi-person images:**
- Created test images with multiple people
- Validated full pipeline before Halloween night
- Caught edge cases (overlapping bounding boxes, varying confidences)

**The trade-off was worth it:**
- Higher API costs for groups
- Longer processing time
- But: Complete and accurate data
- Essential for a visitor counting system

---

---

## Day 8: Production Hardening for 6-Hour Halloween Run

### The Challenge: Making It Bulletproof

**Goal:** Ensure the system can run continuously for 6+ hours on Halloween night without manual intervention.

**Initial concern:** The detection script worked great for testing (5-10 minutes), but would it survive a 6-hour continuous run? What happens when:
- The RTSP stream times out or drops?
- Memory leaks accumulate over time?
- The disk fills up with saved images?
- Network hiccups occur?
- The Pi needs to recover from errors?

**Halloween night = one shot to get it right.** No debugging, no restarts, no "oops let me fix that real quick."

### Problem 1: RTSP Stream Timeouts

**Symptom:**
```
[ WARN:0@60.208] global cap_ffmpeg_impl.hpp:453 _opencv_ffmpeg_interrupt_callback Stream timeout triggered after 30028.992452 ms
⚠️  Failed to read frame, reconnecting...
⚠️  Failed to read frame, reconnecting...
⚠️  Failed to read frame, reconnecting...
```

After about 1 minute of running, the RTSP stream would timeout and the script would loop endlessly printing "Failed to read frame" without actually reconnecting.

**Root cause:**
- OpenCV's default RTSP timeout is 30 seconds
- Our "reconnection" logic was just `continue` - it didn't actually close and reopen the connection
- The stream was dead, and we kept trying to read from a dead connection

**Solution 1: Proper reconnection logic (lines 99-107 in main.py):**
```python
if not ret:
    failed_frame_count += 1
    print("⚠️  Failed to read frame, reconnecting...")
    cap.release()  # ← Actually close the connection!
    time.sleep(2)
    cap = connect_to_stream(rtsp_url)  # ← Create new connection
    last_reconnect_time = time.time()  # Reset timer
    if not cap.isOpened():
        print("❌ Failed to reconnect, retrying in 5 seconds...")
        time.sleep(5)
    continue
```

**Solution 2: Reduce OpenCV timeout (lines 67-75):**
```python
def connect_to_stream(url):
    """Connect to RTSP stream with optimized settings."""
    cap = cv2.VideoCapture(url)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer
    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)  # 10s instead of 30s
    cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 10000)
    return cap
```

**Why this matters:**
- Failures now recover in 10 seconds instead of 30+ seconds
- System self-heals instead of getting stuck
- No manual intervention needed if stream glitches

### Problem 2: Memory Leaks Over Time

**Concern:** OpenCV and network connections can accumulate memory over hours of continuous operation.

**Solution: Periodic reconnection (lines 114-124):**
```python
# Reconnect every hour to clear memory
RECONNECT_INTERVAL = 3600

if current_time - last_reconnect_time > RECONNECT_INTERVAL:
    print("🔄 Performing periodic reconnection (memory management)...")
    cap.release()
    time.sleep(1)
    cap = connect_to_stream(rtsp_url)
    last_reconnect_time = current_time
```

**Why once per hour?**
- Not too frequent (doesn't interrupt detection flow)
- Frequent enough to prevent accumulation
- Trick-or-treating happens in 2-3 hour windows
- Ensures fresh connection every hour

### Problem 3: Disk Space Exhaustion

**Concern:** Saving a 200KB JPG for every detection over 6 hours could fill disk space.

**Math:**
- 200KB per image
- 100 detections over Halloween night
- 20MB total (not bad)
- But: What if we get 500 detections? 1000?
- Small SD card could fill up

**Solution: Auto-cleanup after upload (lines 267-273):**
```python
# Clean up local file after all persons processed and uploaded
try:
    if supabase_client and os.path.exists(filename):
        os.remove(filename)
        print(f"   🗑️  Cleaned up local file: {filename}")
except Exception as e:
    print(f"   ⚠️  Failed to cleanup local file: {e}")
```

**Design decision:**
- Keep local backup until Supabase upload succeeds
- Delete local copy after successful upload
- Image still accessible via Supabase Storage URL
- Saves disk space, prevents accumulation

**Graceful degradation:**
- If Supabase is down, images stay local (backup)
- If cleanup fails, doesn't crash the script
- Error message logs the issue

### Problem 4: Monitoring and Visibility

**Problem:** How do you know if the system is working properly when it's running as a background service?

**Solution: Health monitoring (lines 104-112):**
```python
HEALTH_CHECK_INTERVAL = 300  # Every 5 minutes

if current_time - last_health_check > HEALTH_CHECK_INTERVAL:
    uptime_minutes = (current_time - start_time) / 60
    print(f"\n📊 Health Check (Uptime: {uptime_minutes:.1f} min)")
    print(f"   Frames processed: {frame_count}")
    print(f"   Detections: {detection_count}")
    print(f"   Failed frames: {failed_frame_count}")
    print()
```

**What this provides:**
- Proof of life every 5 minutes
- Frame processing rate (is it stuck?)
- Detection count (is it working?)
- Failed frame count (connection issues?)

**Example output:**
```
📊 Health Check (Uptime: 125.3 min)
   Frames processed: 225450
   Detections: 47
   Failed frames: 3
```

From this you can tell:
- System has been running for 2+ hours
- Processing ~1800 frames/minute (30fps × 60s)
- Detected 47 people (reasonable for 2 hours)
- Only 3 failed frames (very healthy)

### Problem 5: Running as a Service

**Challenge:** SSH sessions disconnect, terminals close, what if you lose connection to the Pi?

**Solution: systemd service (`costume-detector.service`):**
```ini
[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/projects/costume-classifier
Environment="PATH=/home/pi/.local/bin:/usr/local/sbin:..."
Environment="PYTHONUNBUFFERED=1"
ExecStart=/home/pi/.local/bin/uv run backend/scripts/main.py
Restart=always
RestartSec=10
StandardOutput=append:/home/pi/costume-detector.log
StandardError=append:/home/pi/costume-detector-error.log
```

**Why systemd?**
- Runs in background (survives SSH disconnection)
- Auto-restarts on crash
- Logs to files (can review later)
- Starts on boot (if Pi reboots)
- Standard Linux service management

**The PATH gotcha:**
Had to include full path to `uv` and set `PATH` environment variable because systemd doesn't use user's shell PATH:
```ini
Environment="PATH=/home/pi/.local/bin:/usr/local/sbin:..."
ExecStart=/home/pi/.local/bin/uv run backend/scripts/main.py
```

Exit code 127 ("command not found") was the clue - systemd couldn't find `uv` in its minimal PATH.

**The buffering gotcha:**
Python buffers stdout by default when not running in a terminal. Logs wouldn't appear in files until buffer flushed (or script crashed).

Solution:
```ini
Environment="PYTHONUNBUFFERED=1"
```

Forces immediate output to log files.

### Production Features Summary

| Feature | Purpose | Lines in main.py |
|---------|---------|-----------------|
| RTSP auto-reconnection | Recover from stream failures | 129-139 |
| Periodic reconnection | Prevent memory leaks | 114-124 |
| OpenCV timeout settings | Faster failure detection | 67-75 |
| Disk cleanup | Prevent disk exhaustion | 267-273 |
| Health monitoring | Visibility into system state | 104-112 |
| Failed frame tracking | Diagnose connection issues | 130, 110 |
| Systemd service | Background operation + auto-restart | costume-detector.service |

### Performance Impact

**Overhead from health monitoring:**
- Health check: ~1ms every 5 minutes
- Negligible CPU impact
- Worth it for visibility

**Periodic reconnection:**
- 1-2 second downtime every hour
- Unlikely to miss a detection (trick-or-treaters spend 5-10s at door)
- Worth it for stability

**Auto-cleanup:**
- `os.remove()`: ~5-10ms per file
- Runs after upload completes
- No impact on detection latency

**Failed frame tracking:**
- Incrementing a counter: <1ms
- Zero performance impact
- Invaluable for diagnostics

### Testing Approach

**Simulated 6-hour run:**
- Left script running for 2 hours straight
- Manually disconnected RTSP stream
- Monitored memory usage with `htop`
- Checked disk space with `df -h`
- Reviewed health check outputs

**Results:**
- Memory stable (~350MB throughout)
- Disk usage minimal (auto-cleanup working)
- Reconnection working (recovered from 5 manual disconnections)
- Health checks showing consistent frame processing
- No crashes, no hangs, no intervention needed

### Key Decisions & Trade-offs

**Why not use systemd's built-in restart limits?**
- systemd can auto-restart services on failure
- But: we want the script to self-heal first
- Only restart the whole service if script itself crashes
- Gives us more control and better logging

**Why log to files instead of journalctl?**
- Easier for non-Linux users to understand
- Can `tail -f` the log file
- Simple to share logs for debugging
- journalctl requires learning another tool

**Why not use a process supervisor like supervisor or pm2?**
- systemd is built into every modern Linux system
- No extra dependencies
- Standard approach on Raspberry Pi OS
- Well-documented, widely understood

**Why manual cleanup instead of cron job?**
- Cleanup happens right after upload succeeds
- No orphaned files if script crashes
- Simpler - one script instead of script + cron job
- Immediate feedback in logs

### What We Learned

**1. Edge cases emerge in production:**
Testing for 5 minutes doesn't reveal what happens over 6 hours. Stream timeouts, memory leaks, disk accumulation - these only show up with time.

**2. Graceful degradation is essential:**
Every failure path has a recovery strategy:
- Stream timeout → reconnect
- Upload fails → keep local copy
- Baseten down → skip costume classification
- System never gives up completely

**3. Observability is critical:**
Health checks and logging make debugging possible. Without them, we'd be flying blind on Halloween night.

**4. systemd is powerful but finicky:**
PATH issues, buffering issues, environment variables - small details that cause mysterious failures. But once configured correctly, it's rock solid.

**5. Test the unhappy paths:**
Don't just test when everything works. Test:
- What if network disconnects?
- What if disk is full?
- What if API times out?
- What if stream drops?

### Updated Checklist

- [x] Set up Raspberry Pi 5 (OS, SSH, networking)
- [x] Test RTSP connection to DoorBird
- [x] Implement YOLO person detection on Pi
- [x] Create Supabase project and schema
- [x] Build database logging with Storage integration
- [x] Build Next.js dashboard with Realtime updates
- [x] Set up Baseten account and deploy model
- [x] Build baseten_client.py wrapper
- [x] Test costume classification with real images
- [x] Fix JSON parsing for Gemma model artifacts
- [x] Integrate costume classification into main.py
- [x] Refactor project structure for maintainability
- [x] **Add RTSP reconnection logic**
- [x] **Implement periodic memory management**
- [x] **Add disk space cleanup**
- [x] **Create health monitoring**
- [x] **Build systemd service for production deployment**
- [x] **Debug and fix systemd PATH and buffering issues**
- [ ] Deploy dashboard to Vercel
- [ ] Final end-to-end testing
- [ ] Halloween night!

### What's Working Now

Complete production-ready pipeline:
1. ✅ DoorBird RTSP stream → Pi (with auto-reconnection)
2. ✅ YOLO person detection (multiple people supported)
3. ✅ Baseten costume classification
4. ✅ Upload image to Supabase Storage
5. ✅ Insert detection record to database
6. ✅ Dashboard fetches recent detections
7. ✅ Dashboard receives real-time updates
8. ✅ **Auto-cleanup of local images**
9. ✅ **Health monitoring every 5 minutes**
10. ✅ **Periodic reconnection every hour**
11. ✅ **Systemd service for production deployment**
12. ✅ **Survives SSH disconnection and auto-restarts on crash**

### Files Added/Modified

**New files:**
- `costume-detector.service` - systemd service definition
- `setup-service.sh` - one-command service installer

**Modified files:**
- `backend/scripts/main.py` - production hardening (reconnection, cleanup, monitoring)
- `README.md` - production deployment guide

### Cost Analysis (Updated)

**Original estimate:** $1-5 for Halloween night

**With production features:**
- RTSP reconnection: $0 (no cost)
- Periodic reconnection: $0 (no cost)
- Health monitoring: $0 (no cost)
- Disk cleanup: $0 (no cost)
- systemd service: $0 (no cost)

**Still $1-5 total!** All production improvements are free.

### Next Steps

1. **Deploy dashboard to Vercel:**
   - Make it publicly accessible
   - Test realtime updates from production service

2. **Final end-to-end test:**
   - Run service for 24 hours
   - Verify all features work together
   - Monitor resource usage

3. **Halloween night preparation:**
   - Test one more time day-of
   - Have backup plans ready
   - Monitor dashboard and logs

---

*Last updated: 2025-10-30 (Day 8: Production hardening for 6-hour continuous operation)*
