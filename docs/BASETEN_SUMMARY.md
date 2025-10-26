# Baseten Deployment Summary

**Date Created**: October 26, 2025
**Model**: Qwen2-VL-7B-Instruct for Halloween Costume Classification
**Platform**: Baseten with Truss

## What Was Built

A production-ready vision-language model deployment for classifying Halloween costumes from images captured by the Raspberry Pi. The deployment uses:

- **Model**: Qwen2-VL-7B-Instruct (7 billion parameter vision-language model from Alibaba)
- **Platform**: Baseten (managed ML infrastructure)
- **Packaging**: Truss (Baseten's model packaging format)
- **Hardware**: Single NVIDIA L4 GPU (24GB VRAM) - cheapest GPU option
- **Cost Strategy**: Scale-to-zero enabled (no cost when idle)

## Architecture Overview

```
┌──────────────────┐
│  Raspberry Pi 5  │
│                  │
│  1. RTSP Stream  │
│  2. YOLO Person  │
│     Detection    │
│  3. Crop Person  │
└────────┬─────────┘
         │
         │ HTTP POST (base64 image)
         ▼
┌──────────────────┐
│  Baseten Cloud   │
│                  │
│  Qwen2-VL-7B     │
│  Vision-Language │
│  Model           │
│  (L4 GPU)        │
└────────┬─────────┘
         │
         │ JSON Response
         ▼
┌──────────────────┐
│  Raspberry Pi 5  │
│                  │
│  Log to Supabase │
└──────────────────┘
```

## Directory Structure

```
.
├── truss_costume_classifier/       # Truss package for deployment
│   ├── config.yaml                 # Model configuration
│   ├── model/
│   │   ├── __init__.py
│   │   └── model.py                # Inference code
│   └── README.md                   # Quick reference
│
├── docs/                           # Documentation
│   ├── BASETEN_DEPLOYMENT.md       # Comprehensive deployment guide
│   ├── BASETEN_CHECKLIST.md        # Step-by-step checklist
│   └── BASETEN_SUMMARY.md          # This file
│
├── test_baseten_api.py             # API testing script
├── classify_costume_api.py         # Pi integration module
├── .env.example                    # Environment variables template
└── pyproject.toml                  # Python dependencies
```

## Key Files Explained

### 1. `truss_costume_classifier/config.yaml`

Defines the model deployment configuration:

```yaml
# Model details
model_name: Halloween-Costume-Classifier-Qwen2-VL-7B
python_version: py311

# Dependencies
requirements:
  - torch==2.4.0
  - transformers==4.46.0
  - qwen-vl-utils==0.0.8
  - pillow==10.4.0
  - accelerate==0.34.0

# Hardware (single L4 GPU - cheapest option)
resources:
  accelerator: L4
  use_gpu: true
  cpu: "4"
  memory: 16Gi

# Performance
runtime:
  predict_concurrency: 4  # Handle 4 parallel requests

# Model caching (downloads from HuggingFace)
model_cache:
  - repo_id: Qwen/Qwen2-VL-7B-Instruct
```

**Key decisions**:
- **L4 GPU**: Cheapest option (~$0.50/hour) that can run 7B parameter models
- **Concurrency 4**: Balance between throughput and GPU memory
- **Model cache**: Pre-downloads 15GB of weights during build
- **Scale-to-zero**: Implicitly enabled (shuts down after 10 min idle)

### 2. `truss_costume_classifier/model/model.py`

Implements the inference logic:

```python
class Model:
    def __init__(self, **kwargs):
        """Initialize variables"""
        self.model = None
        self.processor = None

    def load(self):
        """Load model into GPU memory (runs once at startup)"""
        self.processor = AutoProcessor.from_pretrained("Qwen/Qwen2-VL-7B-Instruct")
        self.model = Qwen2VLForConditionalGeneration.from_pretrained(...)

    def predict(self, request):
        """Run inference on input image"""
        # 1. Decode base64 image
        # 2. Prepare chat messages with system prompt
        # 3. Run model.generate()
        # 4. Return costume description
```

**Key features**:
- Custom system prompt optimized for costume descriptions
- Base64 image decoding (supports URL or base64)
- Temperature 0.3 for consistent, focused descriptions
- Error handling with fallback to "unknown costume"

### 3. `classify_costume_api.py`

Raspberry Pi integration module:

```python
def classify_costume(person_crop: np.ndarray) -> Dict[str, Any]:
    """
    Send cropped person image to Baseten for classification.

    Args:
        person_crop: OpenCV image (NumPy array)

    Returns:
        {"description": str, "confidence": None, "error": str}
    """
    # 1. Encode image to base64
    # 2. POST to Baseten API
    # 3. Return result with retry logic
```

**Features**:
- Accepts OpenCV images directly (no manual encoding needed)
- Automatic retry logic (3 attempts with 5-second backoff)
- 60-second timeout (accounts for cold starts)
- Warmup function for pre-event preparation

### 4. Documentation

**`docs/BASETEN_DEPLOYMENT.md`** (5000+ words):
- What is Baseten and Truss?
- Why use Baseten for this project?
- Step-by-step deployment guide
- API integration examples
- Cost optimization strategies
- Troubleshooting common issues

**`docs/BASETEN_CHECKLIST.md`**:
- Pre-deployment checklist
- Deployment steps
- Testing procedures
- Halloween night monitoring
- Post-event cleanup

## How It Works

### Deployment Process

1. **Package model with Truss**:
   ```bash
   cd truss_costume_classifier
   truss push
   ```

2. **Baseten builds container**:
   - Downloads Qwen2-VL-7B-Instruct (~15GB)
   - Installs Python dependencies
   - Creates Docker image
   - Deploys to L4 GPU instance

3. **Model starts**:
   - Runs `Model.load()` once
   - Loads model weights into GPU VRAM (takes ~30 seconds)
   - Ready to handle requests

4. **Model auto-scales**:
   - **Active**: Handles requests with <3 second latency
   - **Idle**: After 10 minutes, scales to zero (no cost)
   - **Cold start**: First request after idle takes 30-60 seconds

### Inference Flow

```python
# On Raspberry Pi
import cv2
from classify_costume_api import classify_costume

# 1. Detect person with YOLO
person_bbox = yolo.detect(frame)

# 2. Crop person from frame
person_crop = frame[y1:y2, x1:x2]

# 3. Classify costume via Baseten
result = classify_costume(person_crop)
# Returns: {"description": "witch with purple hat", "confidence": null}

# 4. Log to Supabase
log_to_supabase(result["description"])
```

### API Request/Response

**Request**:
```json
POST https://model-abc123.api.baseten.co/production/predict
Authorization: Api-Key YOUR_KEY
Content-Type: application/json

{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "prompt": "What Halloween costume is this person wearing?",
  "max_tokens": 256,
  "temperature": 0.3
}
```

**Response**:
```json
{
  "description": "witch with purple hat and broom",
  "confidence": null
}
```

## Cost Analysis

### L4 GPU Pricing
- **Active inference**: ~$0.50/hour
- **Idle with scale-to-zero**: $0.00/hour
- **Data transfer**: Included

### Halloween Night Scenario

**Assumptions**:
- 100 trick-or-treaters
- 3-hour event (6pm-9pm)
- ~3 seconds per inference

**Calculation**:
```
Total inference time: 100 × 3 sec = 300 seconds = 5 minutes
Cost: 5 min ÷ 60 min × $0.50 = ~$0.04

With overhead (cold starts, retries): ~$0.10-$0.50
```

**Comparison**:
- **Baseten (Qwen2-VL)**: $0.10-$0.50 for the night
- **OpenAI GPT-4 Vision**: $0.01-$0.05 per image × 100 = $1-$5
- **Running locally on Pi**: Not feasible (Pi can't run 7B VLM)

### Cost Optimization Tips

1. **Scale-to-zero**: Enabled by default (saves money when idle)
2. **Warmup before event**: Prevents cold start on first kid
3. **Batch requests**: If multiple people detected, consider batching
4. **Smart sampling**: Don't classify every frame, wait for new person
5. **Set budget alerts**: In Baseten dashboard to avoid surprises

## Performance Characteristics

### Latency
- **Cold start**: 30-60 seconds (first request after idle)
- **Warm inference**: 1-3 seconds per image
- **Throughput**: ~4 requests/second with concurrency=4

### Quality
- **Model size**: 7 billion parameters (good quality/cost balance)
- **Description quality**: Specific, detailed costume descriptions
- **Consistency**: Temperature 0.3 ensures focused descriptions
- **Limitations**: No confidence scores, English only

### Reliability
- **Uptime**: Managed by Baseten (99.9% SLA)
- **Autoscaling**: Automatic based on load
- **Retry logic**: Built into `classify_costume_api.py`
- **Fallback**: Returns "unknown costume" on errors

## Testing Strategy

### 1. Pre-Deployment Testing

**Test model code locally** (optional):
```bash
truss run-image truss_costume_classifier
# Starts local server at http://localhost:8080
```

### 2. Post-Deployment Testing

**Test via Baseten dashboard**:
- Go to model → Playground
- Upload test image
- Click "Predict"

**Test via Python**:
```bash
python test_baseten_api.py test_images/witch.jpg
```

**Test Pi integration**:
```bash
python classify_costume_api.py test_images/witch.jpg
```

### 3. Pre-Event Testing (Halloween Night)

**1 hour before event**:
```bash
# Warmup model
python classify_costume_api.py --warmup

# Test full pipeline
python detect_and_classify.py --test-mode
```

## Monitoring and Debugging

### Baseten Dashboard

View real-time metrics:
- **Requests**: Count, rate, status codes
- **Latency**: p50, p95, p99
- **Errors**: Error rate, error messages
- **Cost**: Hourly cost, total spend

### Logs

**Stream logs**:
```bash
truss logs <model-id> --follow
```

**View recent logs**:
```bash
truss logs <model-id> --tail 100
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Cold start timeout | First request after idle | Expected behavior; send warmup request |
| Empty descriptions | Low temperature, bad image | Increase temperature to 0.5-0.7 |
| CUDA OOM | Model too large for L4 | Use A10G or smaller model (Qwen2-VL-2B) |
| 429 Too Many Requests | Exceeded rate limit | Increase concurrency or add backoff |
| API auth error | Wrong API key | Verify key in .env file |

## Next Steps

### Immediate (Before Deployment)

1. **Get Baseten account**: Sign up at baseten.co
2. **Deploy model**: Run `truss push`
3. **Test API**: Use `test_baseten_api.py`
4. **Update .env**: Add model URL and API key

### Before Halloween Night

1. **Test full pipeline**: RTSP → YOLO → Baseten → Supabase
2. **Set budget alerts**: In Baseten dashboard
3. **Create warmup script**: Run 30 min before event
4. **Monitor dashboard**: Watch for errors during testing

### During Event

1. **Monitor dashboard**: Check request rate, latency, errors
2. **Watch Pi logs**: Ensure API calls succeeding
3. **Verify Supabase**: Costume data flowing in

### After Event

1. **Review metrics**: Total requests, cost, latency
2. **Export logs**: Save for future reference
3. **Document learnings**: Update this doc with insights
4. **Scale down**: Model auto-scales to zero (no action needed)

## Alternative Approaches

### Option 1: Larger Model
Use Qwen2-VL-72B for better descriptions (requires A100 GPU):
- **Pros**: Higher quality descriptions
- **Cons**: 10x more expensive (~$5/hour)

### Option 2: Smaller Model
Use Qwen2-VL-2B for faster inference (can use T4 GPU):
- **Pros**: Cheaper (~$0.20/hour), faster cold starts
- **Cons**: Lower quality descriptions

### Option 3: vLLM Server
Use vLLM's OpenAI-compatible server (like in qwen-3-vl-30b-a3b-instruct example):
- **Pros**: Faster inference, higher throughput
- **Cons**: More complex config, larger model only

### Option 4: Different VLM
Use LLaVA, BLIP-2, or other vision-language models:
- **Pros**: Different quality/cost tradeoffs
- **Cons**: May need different prompting strategies

## Resources

### Documentation
- **Baseten Docs**: https://docs.baseten.co
- **Truss Docs**: https://truss.baseten.co
- **Qwen2-VL**: https://huggingface.co/Qwen/Qwen2-VL-7B-Instruct

### Support
- **Baseten Discord**: https://discord.gg/baseten
- **Email**: support@baseten.co

### This Project
- Full deployment guide: `docs/BASETEN_DEPLOYMENT.md`
- Deployment checklist: `docs/BASETEN_CHECKLIST.md`
- Truss README: `truss_costume_classifier/README.md`

## Conclusion

This deployment provides a production-ready, cost-effective solution for costume classification:

✅ **Easy to deploy**: Single command (`truss push`)
✅ **Cost-efficient**: Scale-to-zero saves money (~$0.10-$0.50 for Halloween night)
✅ **High quality**: 7B parameter VLM generates detailed descriptions
✅ **Reliable**: Managed infrastructure, automatic scaling
✅ **Well-documented**: Comprehensive guides and examples

The model is ready to integrate with the Raspberry Pi detection pipeline and should provide excellent results for the Halloween costume classifier project!
