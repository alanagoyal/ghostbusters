# Costume Classification Architecture Decision

**Date:** 2025-10-26
**Status:** Proposed
**Decision:** Recommend VLM-only approach using Llama 3.2 11B Vision Instruct

## Executive Summary

After evaluating Segment Anything Model (SAM) + Vision-Language Model (VLM) two-stage approach versus VLM-only single-stage approach, I recommend using **Llama 3.2 11B Vision Instruct** directly without SAM segmentation for the following reasons:

1. **Simpler architecture** - One API call instead of two
2. **Lower latency** - ~2-3 seconds vs ~4-6 seconds per inference
3. **Lower cost** - 50% reduction in API calls
4. **Sufficient quality** - Modern VLMs handle background noise well
5. **Better YOLO integration** - YOLO bounding boxes already isolate the person

## Available Models on Baseten

### Vision-Language Models Found

| Model | Parameters | Hardware | Best For | Status |
|-------|-----------|----------|----------|--------|
| **Llama 3.2 11B Vision Instruct** | 11B | A100 | Image description, VQA | ✅ **Recommended** |
| Qwen3 VL 235B | 235B | Multi-GPU | High-accuracy tasks | ⚠️ Overkill for our use case |

### Llama 3.2 11B Vision Instruct Details

**Capabilities:**
- Vision-capable chat LLM from Meta
- Generates natural language descriptions from images
- Supports visual question answering
- Can follow specific prompting instructions

**Input Format:**
```python
{
    "messages": [
        {
            "role": "user",
            "content": "Describe this person's Halloween costume in one short phrase."
        }
    ],
    "image": "https://example.com/image.jpg",
    "max_new_tokens": 512,
    "temperature": 0.9,
    "stream": False
}
```

**Output Format:**
```python
{
    "completion": "witch with purple hat and broom",
    "usage": {
        "input_tokens": 123,
        "output_tokens": 8
    }
}
```

## Architecture Comparison

### Option A: SAM + VLM (Two-Stage)

```
RTSP Stream → YOLO Detection → SAM Segmentation → VLM Description
              (person bbox)     (remove background)  (costume text)
```

**Pros:**
- Clean segmentation removes background distractions
- Potentially higher quality on complex backgrounds
- Better focus on the person

**Cons:**
- Two API calls: SAM + VLM
- Higher latency: ~4-6 seconds total
- Higher cost: 2x API calls
- More complex error handling
- SAM requires A10G GPU ($9.984/hour minimum)
- Additional image processing between stages

**Cost Analysis:**
- SAM inference: ~1.5 seconds on A10G
- VLM inference: ~2-3 seconds on A100
- Total: ~4-6 seconds per costume
- For 100 trick-or-treaters: 400-600 seconds = 6-10 minutes total processing

### Option B: VLM-Only (Single-Stage) ✅ RECOMMENDED

```
RTSP Stream → YOLO Detection → VLM Description
              (person bbox)     (costume text)
```

**Pros:**
- Single API call
- Lower latency: ~2-3 seconds
- 50% cost reduction (one model instead of two)
- Simpler error handling
- YOLO already provides tight bounding boxes around people
- Modern VLMs (Llama 3.2) are robust to background noise
- Easier to deploy and maintain

**Cons:**
- Background might be included in the image
- Potentially less accurate on very busy backgrounds

**Cost Analysis:**
- VLM inference: ~2-3 seconds on A100
- For 100 trick-or-treaters: 200-300 seconds = 3-5 minutes total processing
- Baseten A100 pricing: ~$9.984/hour minimum (serverless auto-scales)

### Option C: Alternative VLMs

**Qwen3 VL 235B:**
- 235B parameter model
- Higher quality but likely overkill
- Slower inference (~5-8 seconds)
- More expensive
- Not necessary for costume descriptions

## Pricing Analysis

### Baseten Pricing Model

Baseten uses **per-minute GPU pricing** with autoscaling, not per-token pricing:

- **Dedicated deployment:** Pay per-minute for GPU instances
- **Serverless:** Autoscaling replicas with sub-second cold starts
- **Cost per token calculation:** `(minutes_to_generate_tokens) * (cost_per_minute)`

### Example Costs for Halloween Night

**Assumptions:**
- 50-200 trick-or-treaters (estimated)
- 1 inference per person
- Llama 3.2 11B Vision on A100 GPU

**VLM-Only Approach:**
- Single A100 GPU: $9.984/hour
- Inference time: ~2.5 seconds per image
- 150 inferences: 150 × 2.5s = 375 seconds = 6.25 minutes
- Cost: (6.25/60) × $9.984 = **~$1.04 for entire Halloween night**

**SAM + VLM Approach:**
- A10G GPU for SAM: $9.984/hour (estimated similar pricing)
- A100 GPU for VLM: $9.984/hour
- SAM inference: ~1.5s, VLM inference: ~2.5s = 4s total
- 150 inferences: 150 × 4s = 600 seconds = 10 minutes
- Cost: (10/60) × $9.984 × 2 GPUs = **~$3.33 for entire Halloween night**

**Savings with VLM-only:** ~$2.29 (68% cheaper)

Note: Baseten offers serverless autoscaling, so you only pay for actual inference time, not idle GPU hours.

## Why SAM May Not Add Value

### 1. YOLO Already Provides Good Isolation
- YOLO bounding boxes are tight around detected persons
- Background is minimal in cropped person images
- Additional segmentation provides marginal benefit

### 2. Modern VLMs Handle Background Well
- Llama 3.2 11B Vision trained on diverse real-world images
- Models inherently learn to focus on salient objects (people)
- Prompt engineering can guide attention: "Describe the person's costume..."

### 3. Segment Anything Limitations
- SAM produces masks, not cropped images
- Requires additional processing to apply masks and remove background
- May segment costume accessories (broom, prop) separately from person
- Adds complexity without clear quality improvement for this use case

## Recommended Architecture

### Final Design: VLM-Only with Llama 3.2 11B Vision Instruct

```
┌─────────────────┐
│  DoorBird RTSP  │
│   1280x720      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Raspberry Pi 5 │
│  Frame Capture  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   YOLOv8n       │
│  Person Detect  │
│  (bbox coords)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Crop Person    │
│  from Frame     │
│  (OpenCV)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Base64 Encode  │
│  or Upload to   │
│  Temp Storage   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Baseten API    │
│  Llama 3.2 11B  │
│  Vision Instruct│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Costume Text   │
│  "witch with    │
│   purple hat"   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Supabase DB    │
│  + Realtime     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Next.js        │
│  Dashboard      │
└─────────────────┘
```

### Prompt Engineering Strategy

**System Prompt:**
```python
prompt = """Describe this person's Halloween costume in one short phrase (5-10 words maximum).
Focus only on the costume, not the background.
Examples:
- "witch with purple hat and broom"
- "inflatable T-Rex costume"
- "Spider-Man with web shooters"
- "princess in blue dress with crown"
- "ghost with white sheet"

Be specific about colors and key costume elements."""
```

**Temperature Setting:**
- Use `temperature=0.3` for consistent, focused descriptions
- Lower temperature = more deterministic outputs
- Reduce hallucination risk

**Token Limit:**
- Set `max_new_tokens=50` (enough for 10-15 word descriptions)
- Reduces cost and latency
- Ensures concise outputs

## Implementation Plan

### Phase 1: Model Deployment
1. ✅ Research complete - Llama 3.2 11B Vision selected
2. Create Baseten account and API key
3. Deploy Llama 3.2 11B Vision Instruct from model library
4. Get model endpoint URL and API credentials

### Phase 2: API Client Development
1. Create `costume_classifier.py` module
2. Implement image encoding (base64 or upload to temp storage)
3. Implement Baseten API client with retry logic
4. Add prompt template with optimized parameters
5. Parse and validate API responses
6. Handle errors gracefully (timeouts, API failures, etc.)

### Phase 3: Integration Testing
1. Test with sample DoorBird frames
2. Test with various costume types (simple, complex, groups)
3. Evaluate description quality and consistency
4. Measure actual latency in production conditions
5. Verify cost per inference matches estimates

### Phase 4: Optimization
1. Fine-tune prompt for better descriptions
2. Implement caching for duplicate detections
3. Add confidence thresholding
4. Optimize image preprocessing (resize, compress)

## Alternative: Future Enhancements

If VLM-only quality is insufficient (unlikely), we can add SAM as a second stage:

### Hybrid Approach (Future Enhancement)
1. Use VLM-only by default
2. If confidence score is low (<0.7), fall back to SAM + VLM
3. Only pay for SAM when needed
4. Best of both worlds: speed + quality

### Prompt Engineering Iteration
Before adding SAM complexity, try:
- More specific prompts
- Few-shot examples in prompt
- Chain-of-thought prompting
- Multiple temperature samples (select best)

## Decision Rationale

**Why Llama 3.2 11B Vision?**
1. Right-sized model (11B not overkill like 235B)
2. Meta's proven vision-language architecture
3. Fast inference on A100 GPUs
4. Well-documented API on Baseten
5. Good balance of quality, speed, and cost

**Why skip SAM?**
1. YOLO already isolates persons well
2. Modern VLMs handle background noise
3. 2x cost increase not justified
4. Added complexity and latency
5. No clear quality improvement for costume descriptions

**When to reconsider SAM:**
1. Testing shows background significantly affects quality
2. Doorbell camera has very busy background
3. Quality requirements increase
4. Budget increases

## Next Steps

1. ✅ Architecture decision documented
2. Deploy Llama 3.2 11B Vision to Baseten
3. Implement `costume_classifier.py` API client
4. Create test suite with sample images
5. Measure real-world latency and quality
6. Integrate with YOLO detection pipeline
7. Connect to Supabase for storage

## References

- [Baseten Model Library](https://www.baseten.co/library/)
- [Llama 3.2 11B Vision Instruct](https://www.baseten.co/library/llama-3-2-11b-vision-instruct/)
- [Segment Anything Model](https://github.com/basetenlabs/truss-examples/tree/main/segment-anything)
- [Baseten Pricing](https://www.baseten.co/pricing/)
- [Truss Documentation](https://docs.baseten.co/)

## Appendix: SAM Technical Details

For reference, if we decide to use SAM later:

**Model:** Segment Anything Model (SAM)
**Architecture:** Vision Transformer (ViT-H)
**Hardware:** A10G GPU (1000m CPU, 10Gi RAM)
**Dependencies:**
- PyTorch 2.1.0
- segment-anything @ commit 6fdee8f
- OpenCV 4.8.1.78

**Input:** Image URL
**Output:** COCO RLE format segmentation masks (JSON)
**Checkpoint:** sam_vit_h_4b8939.pth (Facebook Research)

**Limitations:**
- Only produces masks, not descriptions
- Requires post-processing to apply masks
- May segment costume pieces separately
- No built-in text generation
