# Costume Classification Implementation Guide

This guide explains how to use the OpenAI Vision-based costume classification system.

## Overview

The costume classification system combines YOLOv8 person detection with OpenAI's GPT-4o Vision model to:
1. Detect people in the DoorBird camera feed
2. Extract and crop person images
3. Classify costumes with natural language descriptions
4. Save annotated frames with costume labels

## Architecture

```
DoorBird RTSP Stream
  ↓
YOLOv8 Person Detection (on Raspberry Pi)
  ↓
Person Crop Extraction
  ↓
OpenAI GPT-4o Vision API
  ↓
Costume Description (e.g., "witch with purple hat and broom")
  ↓
Save Annotated Frame + Log to Supabase (future)
```

## Setup

### 1. Get OpenAI API Key

1. Sign up at [platform.openai.com](https://platform.openai.com)
2. Create an API key
3. Add to your `.env` file:
   ```bash
   OPENAI_API_KEY=sk-...
   ```

### 2. Install Dependencies

```bash
uv sync
```

This installs:
- `opencv-python` - Image processing
- `ultralytics` - YOLOv8 person detection
- `openai` - OpenAI API client
- `python-dotenv` - Environment variable management

## Usage

### Standalone Costume Classification

Classify a costume in a single image:

```bash
uv run python classify_costume.py path/to/image.jpg
```

**Example output:**
```
Classifying costume in detection_20241026_121049.jpg...

Results:
  Description: witch with purple hat and broom
  Confidence: 0.90
```

### Full Detection + Classification Pipeline

Run the complete pipeline on the DoorBird stream:

```bash
uv run python detect_and_classify.py
```

**What it does:**
1. Connects to DoorBird RTSP stream
2. Processes frames at ~1 fps
3. Detects people with YOLOv8
4. Crops each detected person
5. Classifies costume with OpenAI Vision
6. Saves both cropped person image and annotated full frame

**Example output:**
```
🎃 Halloween Costume Classifier
==================================================
📹 Connecting to DoorBird at 192.168.4.49
🤖 Loading YOLOv8n model...
✅ YOLO model loaded!
🎨 Initializing OpenAI Vision classifier...
✅ Classifier ready!
✅ Connected to RTSP stream!

👁️  Watching for trick-or-treaters...
Press Ctrl+C to stop

👤 Person detected! (#1)
   Confidence: 0.87
   Saved crop: person_20241026_153045.jpg
   🎨 Classifying costume...
   🎭 Costume: witch with purple hat and broom
   📊 Classification confidence: 0.90
   Saved annotated frame: detection_20241026_153045.jpg
```

**Output files:**
- `person_TIMESTAMP.jpg` - Cropped person image (sent to OpenAI)
- `detection_TIMESTAMP.jpg` - Full frame with bounding box + costume label

## Configuration

### Detection Parameters

Edit `detect_and_classify.py` to adjust:

```python
DETECTION_INTERVAL = 30  # Process every Nth frame (~1 fps at 30fps)
PERSON_CONFIDENCE_THRESHOLD = 0.5  # YOLO confidence threshold
COOLDOWN_SECONDS = 3  # Minimum seconds between detections
```

### OpenAI API Parameters

Edit `classify_costume.py` to adjust:

```python
# In CostumeClassifier.classify()
response = self.client.chat.completions.create(
    model="gpt-4o",  # Model to use
    max_tokens=50,  # Max description length
    temperature=0.3,  # Lower = more consistent
)

# Image detail level
"detail": "low",  # "low" or "high" (low is cheaper/faster)
```

## Cost Estimation

**OpenAI GPT-4o Vision Pricing (as of Oct 2024):**
- Low detail image: $0.00265 per image
- Text output: ~$0.01 per 1K tokens

**Per detection cost:** ~$0.003

**Halloween night estimates:**
- 100 trick-or-treaters: **$0.30**
- 200 trick-or-treaters: **$0.60**
- 500 trick-or-treaters: **$1.50**

Very affordable for a one-night event!

## Performance

**Latency per detection:**
- YOLO inference: ~200-250ms
- OpenAI Vision API: ~1000-2000ms
- **Total: ~1.2-2.5 seconds**

**Resource usage on Raspberry Pi 5:**
- CPU: ~25-30% average
- RAM: ~350MB for Python process
- Temperature: ~50°C with active cooling
- No thermal throttling

## Prompt Engineering

The costume classification uses a carefully crafted prompt:

```python
"""Analyze this image and describe the person's Halloween costume in one concise phrase (3-8 words).

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

**Why this works:**
- **Concise phrase requirement:** Keeps descriptions chart-friendly
- **Focus points:** Guides attention to important details
- **Examples:** Few-shot learning for consistent format
- **"ONLY the costume description":** Prevents verbose responses

## Troubleshooting

### "Missing OPENAI_API_KEY"

Make sure your `.env` file has:
```bash
OPENAI_API_KEY=sk-your-actual-key-here
```

### API Rate Limits

If you hit rate limits:
1. Increase `COOLDOWN_SECONDS` in `detect_and_classify.py`
2. Check your OpenAI account rate limits
3. Consider upgrading to a paid tier

### "Could not connect to RTSP stream"

Check:
1. DoorBird is on the same network
2. `.env` has correct `DOORBIRD_IP`, `DOORBIRD_USERNAME`, `DOORBIRD_PASSWORD`
3. RTSP stream is enabled on DoorBird

### High Latency

To reduce latency:
1. Use `detail: "low"` (default, sufficient for costumes)
2. Reduce `max_tokens` to 30-40
3. Ensure good network connection (ethernet preferred over WiFi)

## Example Descriptions

Here are example outputs from the system:

| Image | Description |
|-------|-------------|
| Traditional witch | "witch with black hat and broom" |
| Superhero | "Superman in red cape" |
| Group costume | "Scooby-Doo gang" |
| DIY costume | "homemade cardboard robot" |
| Inflatable costume | "inflatable T-Rex dinosaur" |
| Classic monster | "skeleton with glowing bones" |
| Pop culture | "Wednesday Addams in braids" |

The model handles:
- Traditional costumes (witch, ghost, vampire)
- Superhero costumes
- Pop culture references
- DIY/homemade costumes
- Group costumes
- Inflatable costumes
- Creative/unique costumes

## Next Steps

After costume classification is working:
1. Set up Supabase database
2. Add logging to store costume descriptions
3. Build Next.js dashboard for live visualization
4. Deploy to Vercel
5. Test end-to-end on Halloween night

## API Module Reference

### CostumeClassifier Class

```python
from classify_costume import CostumeClassifier

# Initialize
classifier = CostumeClassifier()  # Uses OPENAI_API_KEY from env
# OR
classifier = CostumeClassifier(api_key="sk-...")  # Explicit API key

# Classify a costume
result = classifier.classify(image_array)  # OpenCV image (BGR format)

# Result structure
{
    "description": str,  # Natural language costume description
    "confidence": float,  # Estimated confidence (0-1)
    "raw_response": str  # Full model response
}
```

### Methods

**`__init__(api_key: str | None = None)`**
- Initialize classifier with optional API key
- Falls back to `OPENAI_API_KEY` environment variable

**`classify(image_array) -> dict`**
- Classify costume in an OpenCV image array
- Returns dict with description, confidence, and raw response

**`_encode_image(image_array) -> str`** (internal)
- Encodes OpenCV image to base64 JPEG

**`_estimate_confidence(response) -> float`** (internal)
- Estimates confidence from OpenAI response quality
- Based on completion status and description length

## License

MIT
