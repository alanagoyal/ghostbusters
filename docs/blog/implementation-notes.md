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

*Last updated: 2025-10-27 (Day 5: Next.js dashboard with Realtime complete)*
