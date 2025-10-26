# Baseten Deployment Guide for Costume Classification Model

This guide explains how to deploy the costume classification model to Baseten using Truss, and how it integrates with the Halloween Doorstep Costume Classifier system.

## Table of Contents

1. [What is Baseten and Truss?](#what-is-baseten-and-truss)
2. [Why Use Baseten for Costume Classification?](#why-use-baseten-for-costume-classification)
3. [Model Overview](#model-overview)
4. [Prerequisites](#prerequisites)
5. [Installation](#installation)
6. [Deployment Steps](#deployment-steps)
7. [Testing the Deployment](#testing-the-deployment)
8. [Integration with Raspberry Pi](#integration-with-raspberry-pi)
9. [Cost Optimization](#cost-optimization)
10. [Monitoring and Debugging](#monitoring-and-debugging)

## What is Baseten and Truss?

### Baseten

**Baseten** is a platform for deploying and serving machine learning models in production. Think of it as a specialized hosting service for AI models that handles:

- **Infrastructure**: GPU servers, autoscaling, load balancing
- **Model serving**: Fast inference APIs with low latency
- **DevOps**: Monitoring, logging, versioning, rollbacks
- **Cost efficiency**: Pay-per-use pricing with automatic scale-to-zero

### Truss

**Truss** is Baseten's open-source model packaging format. It's like a Docker container specifically designed for ML models. A Truss package contains:

1. **`config.yaml`**: Configuration file specifying:
   - Model metadata and name
   - Python dependencies (requirements)
   - Hardware resources (GPU type, CPU, memory)
   - Runtime settings (concurrency, autoscaling)

2. **`model/model.py`**: Python code defining the model class with three required methods:
   - `__init__()`: Initialize variables
   - `load()`: Load model weights into memory (runs once at startup)
   - `predict()`: Run inference on input data (called for each request)

3. **Optional files**:
   - Additional Python packages
   - Data files
   - Custom dependencies

## Why Use Baseten for Costume Classification?

For the Halloween Doorstep Costume Classifier project, we offload costume classification to Baseten for several reasons:

### 1. **Hardware Constraints**
- Raspberry Pi 5 (8GB RAM) cannot run large vision-language models
- Pi only runs lightweight YOLO for person detection
- Heavy lifting (VLM inference) happens in the cloud

### 2. **Cost Efficiency**
- **Scale-to-zero**: When idle, replicas shut down (no cost)
- **Pay-per-inference**: Only pay for actual costume classifications
- **Estimated cost**: ~$0.50-$10 for Halloween night (50-200 trick-or-treaters)

### 3. **Performance**
- **GPU acceleration**: L4 GPU provides fast inference (~1-3 seconds per image)
- **Autoscaling**: Handles traffic spikes when multiple kids arrive
- **Low latency**: Optimized inference infrastructure

### 4. **Flexibility**
- Easy to swap models (upgrade to Qwen3-VL, LLaVA, etc.)
- No code changes on Pi required
- Can test and iterate independently

## Model Overview

### Architecture

**Model**: Qwen2-VL-7B-Instruct (Vision-Language Model)

**Input**:
```json
{
  "image": "base64_encoded_image_string",
  "prompt": "What Halloween costume is this person wearing?",
  "max_tokens": 256,
  "temperature": 0.3
}
```

**Output**:
```json
{
  "description": "witch with purple hat and broom",
  "confidence": null
}
```

### System Prompt

The model is configured with a specialized system prompt:

> "You are a Halloween costume classifier. Describe the person's costume in one short, specific phrase (e.g., 'witch with purple hat and broom', 'skeleton with glowing bones', 'inflatable T-Rex'). Focus on distinctive details and colors."

This ensures:
- Concise descriptions (not paragraphs)
- Specific details (colors, props, themes)
- Consistent format

### Resource Configuration

- **GPU**: Single NVIDIA L4 (24GB VRAM) - cheapest GPU option
- **CPU**: 4 cores
- **Memory**: 16GB RAM
- **Concurrency**: 4 parallel requests
- **Autoscaling**: Scale from 0 to 2 replicas based on load

## Prerequisites

### 1. Baseten Account

Sign up at [https://baseten.co](https://baseten.co)

### 2. API Key

Get your API key from the Baseten dashboard:
1. Go to Settings → API Keys
2. Copy your API key
3. Add to `.env` file:
   ```bash
   BASETEN_API_KEY=your_api_key_here
   ```

### 3. Install Truss CLI

```bash
pip install truss
```

Or using uv (if you're using this project's setup):
```bash
uv pip install truss
```

### 4. Authenticate Truss CLI

```bash
truss login
```

This will open a browser window to authenticate with Baseten.

## Installation

The Truss model is already configured in this repository at:

```
truss_costume_classifier/
├── config.yaml          # Model configuration
└── model/
    ├── __init__.py
    └── model.py         # Model inference code
```

No additional installation needed - the directory structure is ready to deploy!

## Deployment Steps

### Step 1: Navigate to Truss Directory

```bash
cd truss_costume_classifier
```

### Step 2: Deploy to Baseten

```bash
truss push
```

This command will:
1. Package your model code and config
2. Upload to Baseten
3. Build a Docker container with all dependencies
4. Deploy to GPU infrastructure
5. Return a model URL and ID

**Example output**:
```
📦 Building Truss...
🚀 Uploading Truss...
🔨 Building model container...
✅ Model deployed successfully!

Model ID: abc123xyz
Model URL: https://model-abc123xyz.api.baseten.co/production/predict
```

### Step 3: Save Model Information

Add the model ID and URL to your `.env` file:

```bash
echo "BASETEN_MODEL_ID=abc123xyz" >> ../.env
echo "BASETEN_MODEL_URL=https://model-abc123xyz.api.baseten.co/production/predict" >> ../.env
```

### Step 4: Wait for Model to be Ready

The first deployment takes ~10-15 minutes as Baseten:
- Downloads the Qwen2-VL-7B model weights (~15GB)
- Builds the Docker container
- Starts the GPU instance
- Loads model into VRAM

Check status in Baseten dashboard or via CLI:
```bash
truss watch <model-id>
```

## Testing the Deployment

### Option 1: Test via Baseten Dashboard

1. Go to Baseten dashboard
2. Navigate to your model
3. Click "Playground" tab
4. Upload a test image
5. Click "Predict"

### Option 2: Test via Python

Create `test_baseten_api.py`:

```python
import requests
import base64
import os
from pathlib import Path

# Load API key from .env
BASETEN_API_KEY = os.getenv("BASETEN_API_KEY")
BASETEN_MODEL_URL = os.getenv("BASETEN_MODEL_URL")

# Load and encode test image
with open("test_costume.jpg", "rb") as f:
    image_bytes = f.read()
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')

# Prepare request
payload = {
    "image": f"data:image/jpeg;base64,{image_base64}",
    "prompt": "What Halloween costume is this person wearing?",
    "max_tokens": 256,
    "temperature": 0.3
}

# Send request
response = requests.post(
    BASETEN_MODEL_URL,
    headers={"Authorization": f"Api-Key {BASETEN_API_KEY}"},
    json=payload
)

# Print result
result = response.json()
print(f"Description: {result['description']}")
print(f"Confidence: {result['confidence']}")
```

Run:
```bash
python test_baseten_api.py
```

### Option 3: Test via cURL

```bash
# Encode image to base64
IMAGE_BASE64=$(base64 -i test_costume.jpg)

# Send request
curl -X POST https://model-abc123xyz.api.baseten.co/production/predict \
  -H "Authorization: Api-Key ${BASETEN_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"image\": \"data:image/jpeg;base64,${IMAGE_BASE64}\",
    \"prompt\": \"What Halloween costume is this person wearing?\",
    \"max_tokens\": 256,
    \"temperature\": 0.3
  }"
```

## Integration with Raspberry Pi

### Pi-Side Code

The Raspberry Pi will call the Baseten API after detecting a person. Here's how it integrates:

```python
import requests
import base64
import cv2
import os

BASETEN_API_KEY = os.getenv("BASETEN_API_KEY")
BASETEN_MODEL_URL = os.getenv("BASETEN_MODEL_URL")

def classify_costume(person_crop_image):
    """
    Send cropped person image to Baseten for costume classification.

    Args:
        person_crop_image: NumPy array (OpenCV image) of cropped person

    Returns:
        dict: {"description": str, "confidence": float or None}
    """
    # Encode image to base64
    _, buffer = cv2.imencode('.jpg', person_crop_image)
    img_base64 = base64.b64encode(buffer).decode('utf-8')

    # Prepare request
    payload = {
        "image": f"data:image/jpeg;base64,{img_base64}",
        "prompt": "What Halloween costume is this person wearing?",
        "max_tokens": 256,
        "temperature": 0.3
    }

    # Send to Baseten
    try:
        response = requests.post(
            BASETEN_MODEL_URL,
            headers={"Authorization": f"Api-Key {BASETEN_API_KEY}"},
            json=payload,
            timeout=30  # 30 second timeout
        )
        response.raise_for_status()

        result = response.json()
        return {
            "description": result["description"],
            "confidence": result.get("confidence")
        }
    except requests.exceptions.RequestException as e:
        print(f"Error calling Baseten API: {e}")
        return {
            "description": "unknown costume",
            "confidence": None
        }
```

### Full Pipeline on Pi

```python
# 1. Capture frame from DoorBird RTSP stream
frame = capture_frame_from_rtsp()

# 2. Detect person with YOLO (runs locally on Pi)
person_detections = yolo_detect_persons(frame)

# 3. For each detected person
for bbox in person_detections:
    # Crop person from frame
    person_crop = crop_person(frame, bbox)

    # 4. Classify costume via Baseten (cloud inference)
    result = classify_costume(person_crop)

    # 5. Log to Supabase
    log_to_supabase({
        "description": result["description"],
        "confidence": result["confidence"],
        "timestamp": datetime.now().isoformat()
    })
```

## Cost Optimization

### Scale-to-Zero Configuration

The Truss config enables scale-to-zero to minimize costs:

```yaml
runtime:
  predict_concurrency: 4  # Handle 4 requests in parallel
```

**How it works**:
- **Idle state**: After 10 minutes of no requests, replica shuts down (cost = $0)
- **Cold start**: First request after idle triggers startup (~30-60 seconds)
- **Warm state**: Subsequent requests are fast (~1-3 seconds)

### Cost Estimates

**L4 GPU pricing** (approximate):
- **Active inference**: ~$0.50/hour
- **Idle with scale-to-zero**: $0/hour

**Halloween night scenario**:
- **Traffic**: 100 trick-or-treaters over 3 hours
- **Inference time**: ~3 seconds per costume
- **Total active time**: ~5 minutes (100 × 3 sec = 300 sec)
- **Estimated cost**: ~$0.05

**Comparison to GPT-4 Vision**:
- GPT-4V: ~$0.01-0.05 per image × 100 = $1-5
- Baseten (Qwen2-VL): ~$0.05 total

### Optimization Tips

1. **Batch requests**: If multiple people detected, batch them
2. **Caching**: Cache descriptions for similar costumes (optional)
3. **Smart sampling**: Don't classify every frame, use motion detection
4. **Off-peak deployment**: Deploy a day before to avoid cold starts

## Monitoring and Debugging

### Baseten Dashboard

View in the Baseten dashboard:
- **Logs**: Real-time inference logs
- **Metrics**: Request count, latency, error rate
- **Usage**: GPU utilization, cost tracking

### Viewing Logs

```bash
# Stream logs in real-time
truss logs <model-id> --follow

# View recent logs
truss logs <model-id> --tail 100
```

### Common Issues

#### 1. Cold Start Timeout

**Symptom**: First request after idle takes >60 seconds

**Solution**:
- Expected behavior with scale-to-zero
- Send a "warm-up" request 30 minutes before Halloween night
- Or disable scale-to-zero for the event

#### 2. CUDA Out of Memory

**Symptom**: Error: "CUDA out of memory"

**Solution**:
- Model is too large for L4 (24GB VRAM)
- Try smaller model (Qwen2-VL-2B) or use A10G/A100 GPU
- Check config.yaml resource settings

#### 3. Rate Limiting

**Symptom**: 429 Too Many Requests error

**Solution**:
- Increase `predict_concurrency` in config.yaml
- Add retry logic with exponential backoff on Pi
- Contact Baseten support for rate limit increase

#### 4. Model Returns Empty Descriptions

**Symptom**: `description` field is empty or very short

**Solution**:
- Adjust `temperature` (try 0.5-0.7 for more creative descriptions)
- Modify system prompt to be more directive
- Increase `max_tokens` to 512

### Debugging Model Code

To test model locally before deploying:

```bash
# Run Truss locally (requires Docker)
truss run-image truss_costume_classifier
```

This starts a local server at `http://localhost:8080` for testing.

## Advanced Configuration

### Using a Different Model

To swap to a different vision-language model:

1. **Edit `config.yaml`**:
   ```yaml
   model_cache:
     - repo_id: liuhaotian/llava-v1.6-vicuna-7b  # Change model
   requirements:
     - torch==2.4.0
     - transformers==4.46.0
     # Add model-specific dependencies
   ```

2. **Edit `model/model.py`**:
   ```python
   # Update model loading code
   self.model = LlavaForConditionalGeneration.from_pretrained(...)
   ```

3. **Redeploy**:
   ```bash
   truss push
   ```

### Enabling Autoscaling

For high-traffic scenarios, enable autoscaling:

```yaml
# Add to config.yaml (not currently supported in basic config)
# Check Baseten docs for latest autoscaling options
```

Currently, scaling is managed by `predict_concurrency`. Baseten automatically scales up when requests exceed concurrency limit.

## Summary

You now have a production-ready costume classification model deployed on Baseten!

**Next steps**:
1. Test the API with sample images
2. Integrate with Raspberry Pi code
3. Set up monitoring for Halloween night
4. Consider a warm-up script to avoid cold starts

**Questions or issues?**
- Check Baseten docs: https://docs.baseten.co
- Truss docs: https://truss.baseten.co
- Baseten Discord: https://discord.gg/baseten
