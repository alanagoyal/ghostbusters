# Building an AI-Powered Halloween Costume Detector in One Week

I have two modes: desperately searching for an idea, or desperately trying to implement one. Last Saturday, while shopping at Walgreens, I was reminded that Halloween was among us. Living in a neighborhood full of kids, inspiration struck—I could hook up my doorbell's video stream, run some vision models to detect and classify trick-or-treaters' Halloween costumes, and put it all on a cool website.

There was just one problem: it was Saturday, I'd be traveling Monday through Wednesday, and Halloween was Friday. I had less than a week to make it work.

## The Hardware Sprint

The first thing I did was order a Raspberry Pi 5, and within a few hours, it showed up on my doorstep (thank you, modern logistics). I got started immediately.

Setting up the Pi had its moments. I struggled to figure out where the microSD card went in the USB reader—it turns out I *had* put it in the right place, but I thought I'd done it wrong because it was so hard to get out. Eventually, I successfully flashed the microSD card and set up SSH so I could do everything from my laptop.

## The DoorBird Challenge

Next came what ended up being one of the hardest parts: connecting to my DoorBird doorbell. DoorBird has an RTSP video stream, but I had to figure out the IP address and create a username and password for an account with RTSP privileges. This wasn't glamorous work, but it was essential.

Here's the RTSP connection code that ended up working ([`backend/scripts/main.py:48`](backend/scripts/main.py:48)):

```python
# Construct RTSP URL
rtsp_url = f"rtsp://{DOORBIRD_USER}:{DOORBIRD_PASSWORD}@{DOORBIRD_IP}/mpeg/media.amp"

# Open RTSP stream with optimized settings
cap = cv2.VideoCapture(rtsp_url)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to minimize delay
cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)
cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 10000)
```

## Getting YOLO to Work

The last thing I accomplished on Sunday was getting YOLO person detection working. I needed to detect people before I could classify their costumes. I used YOLOv8n—the smallest, fastest version—and surprisingly, it was actually pretty easy to get running. I had a lot of fun testing it by going out on my doorstep and walking into the frame. Sure enough, it detected me.

At this point, I felt like I had the core pieces working. I could figure out the BaseTen classification API, Supabase backend, and the dashboard while traveling, then put it all together on Thursday when I got back.

## Vision Model Integration

For costume classification, I used BaseTen's model API, which gives you an OpenAI-like interface for running vision models. I looked through their model library for something with vision capabilities and ended up choosing Gemma. I don't really know if it's particularly good or cost-effective, but I tested it and it worked.

This is where I got creative with testing. Obviously, I don't have trick-or-treaters at my door when it's not Halloween. So I used a still image the script captured of my husband on the front porch, went into Google AI Studio, and used Google's image model to create a bunch of fake images of kids in costumes. I used those to test the BaseTen integration.

Here's the costume classification code ([`backend/src/clients/baseten_client.py:106`](backend/src/clients/baseten_client.py:106)):

```python
def classify_costume(self, image_bytes: bytes) -> Tuple[Optional[str], Optional[float], Optional[str]]:
    """Classify a Halloween costume from an image using Gemma vision model."""
    # Encode image to base64
    img_base64 = base64.b64encode(image_bytes).decode("utf-8")
    data_uri = f"data:image/jpeg;base64,{img_base64}"

    # Prompt for structured output
    prompt = (
        "Analyze this Halloween costume and respond with ONLY a JSON object:\n"
        '{"classification": "costume type", "confidence": 0.95, "description": "costume description"}\n\n'
        "Preferred categories:\n"
        "- witch, vampire, zombie, skeleton, ghost\n"
        "- superhero, princess, pirate, ninja, clown, monster\n"
        # ... 75+ categories total
    )

    # Call Baseten API
    response = self.session.post(
        self.model_url,
        json={
            "model": "gemma",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_uri}}
                ]
            }]
        }
    )

    # Parse structured JSON response
    result = response.json()
    content = result["choices"][0]["message"]["content"]
    parsed = json.loads(content)

    return (
        parsed["classification"],
        float(parsed["confidence"]),
        parsed["description"]
    )
```

The key here was using structured outputs. I give the model a set of ~75 common Halloween costume categories and ask it to both generate a description and classify the costume. This lets me group costumes on the dashboard while still capturing unique details.

## Building the Backend

Setting up Supabase was straightforward. I enabled Realtime, which ended up being crucial for displaying updates in real-time on the dashboard. I used both storage (to upload the stills) and a database table to store the detection metadata.

Here's the Supabase integration ([`backend/src/clients/supabase_client.py:135`](backend/src/clients/supabase_client.py:135)):

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
    """Complete workflow: upload image and insert detection record."""
    # Upload image to storage
    image_url = self.upload_detection_image(image_path, timestamp)

    # Insert detection record with costume data
    result = self.insert_detection(
        timestamp=timestamp,
        confidence=confidence,
        bounding_box=bounding_box,
        image_url=image_url,
        costume_classification=costume_classification,
        costume_description=costume_description,
        costume_confidence=costume_confidence,
    )

    return bool(result)
```

## The Frontend Dashboard

I wanted to create a cool dashboard with stats about trick-or-treaters and their costumes. I built it with Next.js 16, React 19, and Tailwind CSS v4.

The magic happens with Supabase Realtime. Instead of polling the database, the dashboard subscribes to changes via WebSocket and updates in real-time ([`frontend/components/dashboard/dashboard-client.tsx:38`](frontend/components/dashboard/dashboard-client.tsx:38)):

```typescript
useEffect(() => {
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

  return () => {
    supabase.removeChannel(channel);
  };
}, []);
```

New detections appear on the dashboard instantly without any page refresh. Sub-second latency from someone stepping on my doorstep to appearing on the website.

## Edge Cases and Privacy

As I built this, I realized I'd need to handle several edge cases I hadn't originally anticipated:

### Face Blurring

If I was going to put pictures on the website, I had to blur faces. At first, I thought about just doing basic face detection, but I decided to blur everything in the bounding box, which seemed safer ([`backend/scripts/main.py:340`](backend/scripts/main.py:340)):

```python
# Blur the frame for privacy AFTER classification
blurred_frame = frame.copy()

for person in detected_people:
    bbox = person["bounding_box"]
    x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]

    # Extract person region
    person_region = blurred_frame[y1:y2, x1:x2]

    # Apply Gaussian blur (kernel size 33)
    if person_region.size > 0:
        blurred_person = cv2.GaussianBlur(person_region, (33, 33), 0)
        blurred_frame[y1:y2, x1:x2] = blurred_person
```

Importantly, I run the vision model on the unblurred image first for better accuracy, then blur before saving or uploading.

### Multiple People

I realized kids often come up in groups or with parents, so I had to adjust YOLO to detect multiple people and send each one to BaseTen separately ([`backend/src/costume_detector.py:27`](backend/src/costume_detector.py:27)):

```python
def detect_people_and_costumes(
    frame: np.ndarray,
    model: YOLO,
    baseten_client: BasetenClient,
    confidence_threshold: float = 0.7,
) -> list[dict]:
    """Detect ALL people in frame and classify their costumes."""
    results = model(frame, verbose=False)
    detected_people = []

    # Collect all person detections
    for result in results:
        for box in result.boxes:
            if int(box.cls[0]) == PERSON_CLASS:
                conf = float(box.conf[0])
                if conf > confidence_threshold:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    detected_people.append({
                        "confidence": conf,
                        "bounding_box": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                    })

    return detected_people
```

Each person gets their own row in the database.

### Inflatable Costumes

I tested on some blow-up dinosaur costumes and realized YOLO wasn't detecting them as people—it was detecting them as cars or animals! So I implemented a dual-pass detection system ([`backend/src/costume_detector.py:23`](backend/src/costume_detector.py:23)):

```python
PERSON_CLASS = 0
INFLATABLE_CLASSES = [2, 14, 16, 17]  # car, bird, dog, cat

# PASS 1: Detect standard people (class 0)
# PASS 2: Detect potential inflatable costumes (classes 2, 14, 16, 17)
```

If YOLO detects something as a car or animal, I send it to BaseTen for costume classification. If BaseTen confirms it's actually a costume (not a real car), I save it. Otherwise, I reject it.

### Region of Interest

I found that YOLO was detecting people on the street, so I had to constrain it to just my doorstep area ([`backend/scripts/main.py:85`](backend/scripts/main.py:85)):

```python
# Region of Interest - only detect in doorstep area
ROI_X_MIN = 0.0   # Left edge (0%)
ROI_X_MAX = 0.7   # Stop at 70% across (excludes street)
ROI_Y_MIN = 0.0   # Top
ROI_Y_MAX = 1.0   # Bottom

def is_in_roi(bbox, frame_width, frame_height):
    """Check if bounding box center is within the doorstep ROI."""
    x1, y1, x2, y2 = bbox
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2

    norm_x = center_x / frame_width
    norm_y = center_y / frame_height

    return (ROI_X_MIN <= norm_x <= ROI_X_MAX and
            ROI_Y_MIN <= norm_y <= ROI_Y_MAX)
```

### Cooldown Period

YOLO runs at roughly 1 frame per second, and I didn't want multiple captures of the same person. So I implemented a 60-second cooldown and a requirement that the person be detected in at least 2 consecutive frames ([`backend/scripts/main.py:82`](backend/scripts/main.py:82)):

```python
CONSECUTIVE_FRAMES_REQUIRED = 2  # Detect in 2 consecutive frames
CAPTURE_COOLDOWN = 30  # Wait 30 seconds before next capture

# Track consecutive detections
if people_detected:
    consecutive_detections += 1
    if consecutive_detections >= CONSECUTIVE_FRAMES_REQUIRED:
        # Capture!
        detection_count += 1
        # ... process detection ...

        # Start cooldown
        last_capture_time = current_time
        in_cooldown = True
        consecutive_detections = 0
```

If a kid walks up and stays for at least 2 seconds, they get captured. Then there's a 30-second cooldown before the next capture.

## What I Learned

**Hardware is always hard.** The hardest parts of this project weren't the ML models or the web dashboard—they were literally finding the IP address of my doorbell camera and figuring out where to insert the microSD card. Not super hard stuff, but hardware challenges are always unpredictable.

**Hardware is rewarding.** Having a physical Raspberry Pi sitting in my house, running 24/7, processing a video stream in real-time—that felt really cool. There's something tangible about edge computing that makes it more satisfying than pure cloud work.

**You never know what will happen in the real world.** The irony? I built this whole system, tested it exhaustively, got it working perfectly... and I literally only got one trick-or-treater on Halloween. The rest of the entries on the website are test images and my mail carrier.

But honestly? That's the best part of building things. Sometimes the journey—figuring out RTSP streams, wrangling YOLO detections, debugging WebSocket subscriptions at 11 PM—is more fun than the destination.

---

**Tech Stack:**
- Edge: Raspberry Pi 5, YOLOv8n, OpenCV, Python
- Vision API: BaseTen (Gemma vision model)
- Backend: Supabase (PostgreSQL + Storage + Realtime)
- Frontend: Next.js 16, React 19, TypeScript, Tailwind CSS v4
- Deployment: Raspberry Pi (edge), Vercel (web)

The complete code is on [GitHub](https://github.com/alanagoyal/ghostbusters), and the live dashboard is at [ghostbusters.alanagoyal.com](https://ghostbusters.alanagoyal.com).
