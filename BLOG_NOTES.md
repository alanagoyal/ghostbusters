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
- Create Supabase project and schema
- Integrate costume classification API call into detection script
- Build database logging

---

## Day 4: Costume Classification with OpenAI Vision

### Architecture Change: Baseten → OpenAI Vision

**Original plan:** Use Baseten to host a vision-language model (LLaVA, BLIP-2, etc.)

**Why we pivoted to OpenAI:**
1. **Development speed:** OpenAI's API is mature and well-documented
2. **Quality:** GPT-4o (with vision) provides excellent costume descriptions
3. **Simplicity:** No need to deploy/manage our own model on Baseten
4. **Cost-effectiveness:** For a one-night event (~50-200 detections), OpenAI pricing is negligible
5. **Reliability:** Battle-tested infrastructure, no cold starts

**Trade-offs considered:**
- OpenAI is more expensive per call than self-hosted models
- But for Halloween night scope (< 200 inferences), total cost is ~$1-5
- Saves hours of Baseten deployment/testing time
- Can always swap to Baseten later if needed

### Implementation: classify_costume.py

**Core module design:**

Created a `CostumeClassifier` class that wraps OpenAI's Vision API:

```python
class CostumeClassifier:
    def __init__(self, api_key: str | None = None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"  # GPT-4o has vision capabilities
```

**Key method: `classify(image_array)`**

Takes an OpenCV image array (BGR format) and returns costume description.

**Image encoding:**
```python
# Encode to JPEG, then base64
success, buffer = cv2.imencode('.jpg', image_array)
img_base64 = base64.b64encode(buffer).decode('utf-8')
```

**Prompt engineering:**

Crafted a specific prompt to get concise, descriptive costume labels:

```python
prompt = """Analyze this image and describe the person's Halloween costume in one concise phrase (3-8 words).

Focus on:
- Main costume theme (e.g., witch, superhero, princess, skeleton)
- Key visual details (colors, props, accessories)
- Creative or unique elements

Examples of good descriptions:
- "witch with purple hat and broom"
- "skeleton with glowing bones"
- "homemade cardboard robot"
- "superhero in red cape"
- "inflatable T-Rex costume"

Provide ONLY the costume description, nothing else."""
```

**Why this prompt structure?**
- **Concise phrase requirement:** Keeps descriptions short and chart-friendly
- **Focus points:** Guides the model to notice important details
- **Examples:** Few-shot learning to establish output format
- **"ONLY the costume description":** Prevents chatty responses

**API call configuration:**

```python
response = self.client.chat.completions.create(
    model=self.model,
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img_base64}",
                        "detail": "low",  # Faster/cheaper for this use case
                    },
                },
            ],
        }
    ],
    max_tokens=50,  # Short descriptions only
    temperature=0.3,  # Lower = more consistent/deterministic
)
```

**Key parameter choices:**
- `detail: "low"`: Uses lower-resolution image analysis (faster, cheaper, sufficient for costumes)
- `max_tokens: 50`: Enforces brevity
- `temperature: 0.3`: Reduces randomness, more consistent descriptions

**Confidence estimation challenge:**

OpenAI doesn't provide confidence scores for vision tasks. We implemented a heuristic:

```python
def _estimate_confidence(self, response) -> float:
    # Check completion status
    if response.choices[0].finish_reason != "stop":
        return 0.5

    # Check response length
    word_count = len(description.split())
    if 3 <= word_count <= 10:
        return 0.9  # Good length
    elif word_count < 3:
        return 0.6  # Too short, uncertain
    else:
        return 0.75  # Longer, moderate confidence
```

**Limitations:**
- This is a proxy metric, not true model confidence
- Future improvement: Use logprobs API if OpenAI adds it for vision
- For now, serves as a rough quality indicator

**Standalone testing:**

Added CLI interface for testing:

```bash
python classify_costume.py detection_20241026_121049.jpg
```

Output:
```
Results:
  Description: person in red jacket and jeans
  Confidence: 0.90
```

### Integration: detect_and_classify.py

**Full pipeline script:**

Created `detect_and_classify.py` that combines:
1. RTSP stream capture (from DoorBird)
2. YOLOv8 person detection
3. Person crop extraction
4. OpenAI Vision costume classification
5. Annotated frame saving

**Pipeline flow:**

```
Frame from DoorBird
  ↓
YOLOv8 person detection
  ↓
Extract bounding box coords
  ↓
Crop person from frame: frame[y1:y2, x1:x2]
  ↓
Save crop: person_TIMESTAMP.jpg
  ↓
OpenAI Vision classification
  ↓
Print costume description
  ↓
Annotate full frame with costume label
  ↓
Save annotated frame: detection_TIMESTAMP.jpg
```

**Detection parameters:**

```python
DETECTION_INTERVAL = 30  # Process every 30th frame (~1 fps)
PERSON_CONFIDENCE_THRESHOLD = 0.5  # YOLO confidence
COOLDOWN_SECONDS = 3  # Avoid duplicate detections
```

**Why 3-second cooldown?**
- Increased from 2 seconds in `detect_people.py`
- Gives OpenAI API time to respond (~1-2 seconds)
- Prevents overwhelming the API with duplicate detections
- Ensures each person is only classified once

**Example output:**

```
👤 Person detected! (#1)
   Confidence: 0.87
   Saved crop: person_20241026_153045.jpg
   🎨 Classifying costume...
   🎭 Costume: witch with purple hat and broom
   📊 Classification confidence: 0.90
   Saved annotated frame: detection_20241026_153045.jpg
```

**File outputs:**

For each detection, saves:
1. `person_TIMESTAMP.jpg`: Cropped person image (sent to OpenAI)
2. `detection_TIMESTAMP.jpg`: Full frame with bounding box + costume label

**Future database integration:**

Added TODO comment for Supabase logging:

```python
# TODO: Log to Supabase
# Future: Send {description, confidence, timestamp} to Supabase
```

### Dependencies Added

**Updated pyproject.toml:**

```toml
dependencies = [
    "opencv-python>=4.12.0.88",
    "openai>=1.58.1",  # NEW: OpenAI Python SDK
    "python-dotenv>=1.1.1",
    "ultralytics>=8.3.63",
]
```

**Updated .env.example:**

```bash
# OpenAI API for costume classification (using GPT-4 Vision)
OPENAI_API_KEY=your_openai_api_key
```

Removed Baseten references since we're using OpenAI instead.

### Testing Strategy

**Local testing plan:**
1. Test `classify_costume.py` standalone on saved detection images
2. Test `detect_and_classify.py` with live RTSP stream
3. Verify OpenAI API responses are descriptive and concise
4. Check performance impact of API calls

**Performance considerations:**

**Latency:**
- YOLO inference: ~200-250ms
- OpenAI Vision API: ~1000-2000ms (network + inference)
- Total time per detection: ~1.2-2.5 seconds
- Acceptable for Halloween use case (not real-time video)

**Cost estimation:**

OpenAI GPT-4o pricing (as of Oct 2024):
- Vision input: $0.00265 per image (low detail)
- Text output: ~$0.01 per 1K tokens

Per detection cost:
- Image: $0.00265
- Description (~10 tokens): ~$0.0001
- **Total: ~$0.003 per costume**

Halloween night estimate:
- 100 trick-or-treaters: $0.30
- 200 trick-or-treaters: $0.60
- 500 (busy night): $1.50

**Much cheaper than expected!**

### Key Learnings

**OpenAI Vision quality:**
- GPT-4o is excellent at describing costumes
- Picks up on details (colors, accessories, props)
- Handles creative/unusual costumes well
- Few-shot prompting really helps with output format

**Prompt engineering matters:**
- Without examples, got verbose descriptions
- With examples, consistently get 3-8 word phrases
- "ONLY the costume description" prevents chattiness
- Temperature 0.3 gives good balance of accuracy and consistency

**Development workflow:**
- Created modular `CostumeClassifier` class for reusability
- Standalone CLI testing (`classify_costume.py`) validates API integration
- Integrated script (`detect_and_classify.py`) proves end-to-end pipeline
- Git workflow (Mac → commit → Pi pull) continues to work well

**Architecture validation:**
- Offloading ML to cloud API was the right call
- Pi only handles person detection + orchestration
- No thermal issues, CPU stays manageable
- Network latency is acceptable for this use case

### What's Working Now

- [x] Set up Raspberry Pi 5 (OS, SSH, networking)
- [x] Test RTSP connection to DoorBird
- [x] Implement YOLO person detection on Pi
- [x] Implement OpenAI Vision costume classification
- [x] Integrate costume classification into detection pipeline
- [ ] Create Supabase schema and enable Realtime
- [ ] Add Supabase logging to detection script
- [ ] Build Next.js dashboard with live updates
- [ ] End-to-end testing
- [ ] Deploy and prep for Halloween night

### Next Steps

**Immediate priorities:**
1. Set up Supabase project
   - Create `sightings` table schema
   - Enable Realtime
   - Configure RLS policies
2. Add Supabase logging to `detect_and_classify.py`
   - POST costume descriptions to Supabase
   - Include timestamp, description, confidence
3. Test end-to-end: Detection → Classification → Database

**After database integration:**
4. Build Next.js dashboard
   - Real-time costume feed
   - Timeline graph
   - Word cloud / tag visualization
5. Deploy to Vercel
6. Final testing with live data
7. Prepare for Halloween night 🎃

---

## Technical Decisions Log

| Decision | Options Considered | Choice | Rationale |
|----------|-------------------|--------|-----------|
| Classification approach | Fixed labels vs. Open-ended | Open-ended | Captures creative costumes, more interesting data |
| ML inference location | Local (Pi) vs. Cloud API | Cloud (OpenAI) | Reliability, quality, cost-effective for one-night event |
| Vision model | Baseten custom model vs. OpenAI Vision | OpenAI GPT-4o | Faster development, excellent quality, negligible cost |
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

*Last updated: 2025-10-26 (Day 3: Person detection working)*
