# Baseten Integration Guide

This guide explains how to set up and use the Baseten vision model API for costume classification in the Doorstep Costume Classifier system.

## Overview

The system uses **Gemma vision model** through Baseten's API to classify Halloween costumes from person crops detected by YOLOv8n.

## Architecture

```
Person Detection (YOLOv8n on Pi)
    ↓
Crop person from frame
    ↓
Send to Baseten API (Gemma Vision)
    ↓
Receive structured JSON response:
{
  "classification": "witch",
  "confidence": 0.95,
  "description": "witch with purple hat and black dress"
}
    ↓
Store in Supabase database:
  - costume_classification: "witch"
  - costume_description: "witch with purple hat and black dress"
  - costume_confidence: 0.95
    ↓
Display on Next.js dashboard
```

## Prerequisites

1. **Baseten Account**: Sign up at [https://baseten.co](https://baseten.co)
2. **API Key**: Generate an API key from your Baseten account settings
3. **Model Deployment**: Deploy a Gemma vision model and get the model endpoint URL

## Setup Instructions

### 1. Install Dependencies

The required dependencies (requests) are already included in `pyproject.toml`. If you need to install them manually:

```bash
uv sync
```

### 2. Configure Environment Variables

Add your Baseten API key and model URL to the `.env` file:

```bash
# Copy the example if you haven't already
cp .env.example .env

# Edit .env and add your Baseten credentials
nano .env
```

Add these lines to `.env`:
```
BASETEN_API_KEY=your_baseten_api_key_here
BASETEN_MODEL_URL=https://model-XXXXXXXX.api.baseten.co/environments/production/predict
```

**Where to find these:**
- **API Key**: [https://app.baseten.co/settings/api-keys](https://app.baseten.co/settings/api-keys)
- **Model URL**: From your Gemma model deployment page in Baseten dashboard

### 3. Test the Connection

Run the test script to verify your Baseten setup:

```bash
uv run python test_baseten_connection.py
```

Expected output:
```
🧪 Testing Baseten API Connection
==================================================
✅ API key found: base_...
✅ Model URL found: https://model-...
🔧 Initializing Baseten client...
✅ Client initialized successfully
   Model: gemma
🔌 Testing API connection...
✅ Connection test passed!
```

### 4. Test with Real Costume Images

Run the comprehensive test with 4 real Halloween costume images:

```bash
uv run python test_costume_detection.py
```

This script will:
1. Load test images from `test_images/` (Tiger, Elsa, Spider-Man, Vampire)
2. Classify each costume using Baseten API
3. Upload results to Supabase database
4. Save annotated images to `test_detections/`

Expected output:
```
🎃 Halloween Costume Detection Test
======================================================================
Found 4 test images

Processing: image-BVH1NL6gKJp8QQ3kW_9e1.png
✅ Classification successful!
   Type:        tiger
   Confidence:  0.95
   Description: child in orange and black tiger costume with hood

Processing: image-qORO3FwW7UYsD2iSDwVnA.png
✅ Classification successful!
   Type:        princess
   Confidence:  0.92
   Description: Elsa from Frozen in blue dress with blonde braid

... (processes all 4 images)

📊 SUMMARY
Total images processed: 4
Successful classifications: 4
Uploaded to Supabase: 4
```

**Benefits of this test:**
- ✅ Tests full pipeline without needing camera/Raspberry Pi
- ✅ Verifies Baseten API integration works correctly
- ✅ Confirms Supabase uploads with both `classification` and `description` fields
- ✅ Validates JSON response parsing works properly
- ✅ Provides visual confirmation (annotated images in `test_detections/`)

### 5. Run Person Detection with Costume Classification

Start the main detection script:

```bash
uv run python detect_people.py
```

When a person is detected, you'll see:
```
👤 Person detected! (#1)
   Saved locally: detection_20251028_123456.jpg
   🎭 Classifying costume...
   👗 Costume: witch (0.95)
      witch with purple hat, black dress, and broomstick
```

## Implementation Details

### BasetenClient Class

Located in `baseten_client.py`, this module provides a clean interface to the Baseten API:

```python
from baseten_client import BasetenClient

# Initialize client (reads BASETEN_API_KEY and BASETEN_MODEL_URL from environment)
client = BasetenClient()

# Classify a costume from image bytes
with open("person_crop.jpg", "rb") as f:
    image_bytes = f.read()

classification, confidence, description = client.classify_costume(image_bytes)
print(f"{classification} ({confidence:.2f}): {description}")
# Output: witch (0.95): witch with purple hat, black dress, and broomstick
```

**Key Features:**
- Uses `requests.Session()` for connection pooling and reuse
- Handles model artifacts like `<end_of_turn>` in responses
- Automatic base64 encoding of images
- Robust JSON parsing from text responses

### JSON Response Format

The system prompts the model to return JSON and parses it from the response:

**Request to Baseten:**
```json
{
  "model": "gemma",
  "stream": false,
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "Analyze this Halloween costume and provide..."},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
      ]
    }
  ],
  "max_tokens": 512,
  "temperature": 0.5
}
```

**Response from Baseten:**
```json
{
  "choices": [
    {
      "message": {
        "content": "{\"classification\": \"skeleton\", \"confidence\": 0.92, \"description\": \"skeleton costume with glow-in-the-dark bones\"}"
      }
    }
  ]
}
```

The client extracts the JSON from the content and parses it.

**Database Schema:**
The parsed fields are mapped to the Supabase database:
- `classification` → `costume_classification` (short costume type, e.g., "witch", "skeleton")
- `confidence` → `costume_confidence` (0.0-1.0 confidence score)
- `description` → `costume_description` (detailed description)

### Integration with detect_people.py

The costume classification happens automatically during person detection:

1. **YOLOv8n** detects a person in the frame
2. **Bounding box** is extracted (x1, y1, x2, y2)
3. **Person crop** is extracted from the frame
4. **BasetenClient** sends the crop to Gemma 3 27B IT Vision
5. **JSON response** is extracted and parsed from the model output
6. **Results** are saved to Supabase with the detection

The integration is **optional** and **gracefully degrades** if Baseten is not configured:
- If `BASETEN_API_KEY` is not set, costume classification is skipped
- Person detection and database uploads continue normally
- Dashboard will show "No costume data available yet"

## Cost Considerations

### Pricing
- **Gemma 3 27B IT** on Baseten: Check current pricing at [https://baseten.co/pricing](https://baseten.co/pricing)
- Gemma models are typically more cost-effective than larger models
- Typical range: $0.005-0.02 per inference

### Halloween Night Estimates
Assuming 50-200 trick-or-treaters:
- **50 detections** × $0.01 = **$0.50**
- **100 detections** × $0.01 = **$1.00**
- **200 detections** × $0.01 = **$2.00**

Gemma provides excellent quality at a lower cost compared to proprietary vision models.

### Optimization Tips

1. **Detection throttling**: The system already throttles detections to once every 2 seconds to avoid duplicates
2. **Confidence threshold**: Only high-confidence YOLO detections (>0.5) trigger costume classification
3. **Single person per frame**: Currently processes only the highest-confidence person per detection

## Model Selection

### Why Gemma 3 27B IT?

**Pros:**
- ✅ State-of-the-art vision-language model from Google DeepMind
- ✅ Excellent at image understanding and description tasks
- ✅ Optimized for instruction-following (IT = Instruction-Tuned)
- ✅ Supports multimodal inputs (text + images)
- ✅ Fast inference through Baseten's optimized infrastructure
- ✅ Open-source model (no vendor lock-in)
- ✅ Cost-effective compared to larger proprietary models

**Alternatives on Baseten:**
- **Llama 3.2 Vision**: Larger model with more parameters
- **Qwen2-VL**: Another excellent vision-language model
- **Custom models**: Deploy your own vision model using Baseten

### Prompt Engineering

The default prompt in `baseten_client.py` is optimized for Halloween costumes:

```python
prompt = (
    "Analyze this Halloween costume and provide:\n"
    "1. A short label (1-3 words, e.g., 'witch', 'skeleton', 'superhero')\n"
    "2. A confidence score between 0.0 and 1.0\n"
    "3. A detailed description (one sentence)\n\n"
    "Respond ONLY with valid JSON in this exact format:\n"
    '{"label": "costume_type", "confidence": 0.95, "description": "detailed description"}\n\n'
    "If you cannot identify a costume, use label='person' and lower confidence."
)
```

You can customize this prompt in `baseten_client.py` to:
- Focus on specific costume attributes (colors, accessories)
- Request different label formats
- Adjust the description length
- Add context about expected costumes

## Troubleshooting

### API Key Issues

**Error**: `ValueError: BASETEN_API_KEY environment variable not set`

**Solution**: Add your API key to `.env`:
```bash
echo "BASETEN_API_KEY=your_api_key_here" >> .env
```

### Connection Errors

**Error**: `Connection test failed: Connection timeout`

**Solutions**:
1. Check your internet connection
2. Verify the API key is correct
3. Check Baseten status: [https://status.baseten.co](https://status.baseten.co)

### Model URL Issues

**Error**: `BASETEN_MODEL_URL environment variable not set`

**Solution**:
1. Log into Baseten dashboard
2. Find your Gemma vision model deployment
3. Copy the model endpoint URL (looks like `https://model-XXXXXXXX.api.baseten.co/environments/production/predict`)
4. Add it to your `.env` file

**Error**: `HTTP 404 Not Found`

**Solution**:
- Verify your model URL is correct
- Check that the model is deployed and running in Baseten
- Ensure you're using the production endpoint URL

### Classification Failures

**Error**: `Could not classify costume`

**Possible causes**:
1. **Poor crop quality**: Person too small or obscured
2. **Image encoding issue**: Check JPEG encoding is working
3. **API timeout**: Network latency or slow response
4. **Rate limiting**: Too many requests in short period

**Debug steps**:
1. Save the person crop locally to inspect quality:
   ```python
   cv2.imwrite("debug_crop.jpg", person_crop)
   ```
2. Test the saved crop with `test_baseten_connection.py`
3. Check Baseten API logs in the dashboard

## Performance Tuning

### Latency Optimization

Typical API response times:
- **Network latency**: 50-200ms
- **Model inference**: 500-2000ms
- **Total**: 550-2200ms (~1 second average)

This is acceptable since:
- Person detection already throttles to 2-second intervals
- Costume classification happens asynchronously
- Dashboard updates in real-time via Supabase Realtime

### Concurrent Detections

The system processes **one person at a time** to:
- Minimize API costs
- Avoid rate limiting
- Maintain stable performance on Raspberry Pi

For high-traffic scenarios, consider:
- Queuing detections and processing in batches
- Using multiple Baseten API keys for parallel requests
- Caching classifications for similar-looking costumes

## Dashboard Integration

The costume data automatically appears in the Next.js dashboard:

### Costume Distribution Chart
Shows top 5 most common costumes with counts:
```
Witch        ████████████ 12 (24%)
Skeleton     ██████████   10 (20%)
Superhero    ████████      8 (16%)
```

### Live Feed
Shows recent detections with costume badges:
```
🎭 witch - 2 minutes ago (95% confidence)
Description: witch with purple hat and black dress
```

No dashboard code changes needed! The components in `dashboard/components/dashboard/` already support costume data.

## Next Steps

1. **Run the test script**: Process the 4 test images to verify everything works
   ```bash
   uv run python test_costume_detection.py
   ```
2. **Check the results**:
   - View annotated images in `test_detections/`
   - Check Supabase dashboard for uploaded records
   - Open Next.js dashboard to see live costume data
3. **Tune the prompt**: Adjust the classification prompt in `baseten_client.py` for your needs
4. **Monitor costs**: Track API usage in Baseten dashboard
5. **Test with live camera**: Once hardware is set up, run `detect_people.py`
6. **Add face blurring**: Implement privacy protection before production use (see `PROJECT_SPEC.md` section 5.5)

## Additional Resources

- **Baseten Docs**: [https://docs.baseten.co](https://docs.baseten.co)
- **Gemma 3 27B IT on Baseten**: [https://docs.baseten.co/examples/models/gemma/gemma-3-27b-it](https://docs.baseten.co/examples/models/gemma/gemma-3-27b-it)
- **Gemma Model Family**: [https://ai.google.dev/gemma](https://ai.google.dev/gemma)
- **Project Spec**: See `PROJECT_SPEC.md` for full system architecture
