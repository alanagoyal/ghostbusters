# Baseten Integration Guide

This guide explains how to set up and use the Baseten vision model API for costume classification in the Doorstep Costume Classifier system.

## Overview

The system uses **Llama 3.2 90B Vision Instruct** through Baseten's OpenAI-compatible API to classify Halloween costumes from person crops detected by YOLOv8n.

## Architecture

```
Person Detection (YOLOv8n on Pi)
    ↓
Crop person from frame
    ↓
Send to Baseten API (Llama 3.2 Vision)
    ↓
Receive structured JSON response:
{
  "label": "witch",
  "confidence": 0.95,
  "description": "witch with purple hat and black dress"
}
    ↓
Store in Supabase database
    ↓
Display on Next.js dashboard
```

## Prerequisites

1. **Baseten Account**: Sign up at [https://baseten.co](https://baseten.co)
2. **API Key**: Generate an API key from your Baseten account settings
3. **Model Access**: Ensure you have access to `meta-llama/Llama-3.2-90B-Vision-Instruct`

## Setup Instructions

### 1. Install Dependencies

```bash
# Install the OpenAI Python SDK (required for Baseten's OpenAI-compatible API)
uv add openai
```

Or if using pip:
```bash
pip install openai>=1.59.7
```

### 2. Configure Environment Variables

Add your Baseten API key to the `.env` file:

```bash
# Copy the example if you haven't already
cp .env.example .env

# Edit .env and add your Baseten API key
nano .env
```

Add this line to `.env`:
```
BASETEN_API_KEY=your_baseten_api_key_here
```

Get your API key from: [https://app.baseten.co/settings/api-keys](https://app.baseten.co/settings/api-keys)

### 3. Test the Connection

Run the test script to verify your Baseten setup:

```bash
uv run python test_baseten_connection.py
```

Expected output:
```
🧪 Testing Baseten API Connection
==================================================
✅ API key found: sk-base...
🔧 Initializing Baseten client...
✅ Client initialized successfully
   Model: meta-llama/Llama-3.2-90B-Vision-Instruct
🔌 Testing API connection...
✅ Connection test passed!
```

### 4. Run Person Detection with Costume Classification

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

# Initialize client (reads BASETEN_API_KEY from environment)
client = BasetenClient()

# Classify a costume from image bytes
with open("person_crop.jpg", "rb") as f:
    image_bytes = f.read()

label, confidence, description = client.classify_costume(image_bytes)
print(f"{label} ({confidence:.2f}): {description}")
# Output: witch (0.95): witch with purple hat, black dress, and broomstick
```

### Structured Outputs

The system uses JSON structured outputs to ensure consistent response format:

**Request to Baseten:**
```json
{
  "model": "meta-llama/Llama-3.2-90B-Vision-Instruct",
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}},
        {"type": "text", "text": "Analyze this Halloween costume and provide..."}
      ]
    }
  ],
  "response_format": {"type": "json_object"}
}
```

**Response from Baseten:**
```json
{
  "label": "skeleton",
  "confidence": 0.92,
  "description": "skeleton costume with glow-in-the-dark bones"
}
```

### Integration with detect_people.py

The costume classification happens automatically during person detection:

1. **YOLOv8n** detects a person in the frame
2. **Bounding box** is extracted (x1, y1, x2, y2)
3. **Person crop** is extracted from the frame
4. **BasetenClient** sends the crop to Llama 3.2 Vision
5. **Structured JSON** response is parsed
6. **Results** are saved to Supabase with the detection

The integration is **optional** and **gracefully degrades** if Baseten is not configured:
- If `BASETEN_API_KEY` is not set, costume classification is skipped
- Person detection and database uploads continue normally
- Dashboard will show "No costume data available yet"

## Cost Considerations

### Pricing
- **Llama 3.2 90B Vision Instruct** on Baseten: Check current pricing at [https://baseten.co/pricing](https://baseten.co/pricing)
- Typical range: $0.01-0.05 per inference

### Halloween Night Estimates
Assuming 50-200 trick-or-treaters:
- **50 detections** × $0.03 = **$1.50**
- **100 detections** × $0.03 = **$3.00**
- **200 detections** × $0.03 = **$6.00**

Much more affordable than GPT-4 Vision while maintaining excellent quality with open-source models.

### Optimization Tips

1. **Detection throttling**: The system already throttles detections to once every 2 seconds to avoid duplicates
2. **Confidence threshold**: Only high-confidence YOLO detections (>0.5) trigger costume classification
3. **Single person per frame**: Currently processes only the highest-confidence person per detection

## Model Selection

### Why Llama 3.2 90B Vision Instruct?

**Pros:**
- ✅ State-of-the-art vision-language model from Meta
- ✅ Excellent at open-ended image description
- ✅ Supports structured JSON outputs
- ✅ Fast inference through Baseten's optimized infrastructure
- ✅ Open-source model (no vendor lock-in)

**Alternatives on Baseten:**
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

### Model Access Issues

**Error**: `Model not found: meta-llama/Llama-3.2-90B-Vision-Instruct`

**Solution**:
1. Log into Baseten dashboard
2. Navigate to Model APIs
3. Ensure Llama 3.2 Vision is enabled for your account
4. Some models require accepting license agreements

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

1. **Test with real photos**: Take sample costume photos and test classification accuracy
2. **Tune the prompt**: Adjust the classification prompt for your needs
3. **Monitor costs**: Track API usage in Baseten dashboard
4. **Add face blurring**: Implement privacy protection before production use (see `PROJECT_SPEC.md` section 5.5)

## Additional Resources

- **Baseten Docs**: [https://docs.baseten.co](https://docs.baseten.co)
- **Llama 3.2 Vision**: [https://ai.meta.com/blog/llama-3-2-connect-2024-vision-edge-mobile-devices/](https://ai.meta.com/blog/llama-3-2-connect-2024-vision-edge-mobile-devices/)
- **OpenAI SDK**: [https://platform.openai.com/docs/api-reference](https://platform.openai.com/docs/api-reference)
- **Project Spec**: See `PROJECT_SPEC.md` for full system architecture
