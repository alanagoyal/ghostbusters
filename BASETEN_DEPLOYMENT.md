# Baseten Deployment Guide

Step-by-step guide to deploy Llama 3.2 11B Vision Instruct on Baseten for costume classification.

## Prerequisites

- Baseten account (sign up at https://www.baseten.co/)
- Credit card for billing (serverless autoscaling charges only for usage)
- Estimated cost for Halloween night (150 inferences): ~$1-2

## Step 1: Create Baseten Account

1. Go to https://www.baseten.co/
2. Click "Sign Up" or "Get Started"
3. Create account with email or GitHub
4. Complete onboarding steps

## Step 2: Deploy Llama 3.2 11B Vision Instruct

### Option A: Deploy from Model Library (Recommended)

1. Navigate to Baseten Model Library: https://www.baseten.co/library/
2. Search for "Llama 3.2 11B Vision Instruct"
3. Click on the model card
4. Click "Deploy now" button
5. Configure deployment:
   - **Deployment name:** `costume-classifier-llama-vision`
   - **Hardware:** A100 GPU (default, recommended)
   - **Autoscaling:** Enable serverless autoscaling
   - **Min replicas:** 0 (saves cost when idle)
   - **Max replicas:** 1-2 (sufficient for Halloween night)
6. Click "Deploy"
7. Wait 5-10 minutes for deployment to complete

### Option B: Deploy via API (Advanced)

If you prefer programmatic deployment, you can use the Baseten API or Truss CLI. See: https://docs.baseten.co/deploy/library

## Step 3: Get API Credentials

### Get API Key

1. Go to Baseten dashboard: https://app.baseten.co/
2. Click on your profile (top right)
3. Select "Settings" → "Account"
4. Navigate to "API Keys" section
5. Click "Create API Key"
6. Name it: `costume-classifier-key`
7. Copy the API key (starts with `BTxxxxxx`)
8. **Important:** Save this key securely - it won't be shown again!

### Get Model ID

1. Go to Baseten dashboard: https://app.baseten.co/
2. Click "Models" in left sidebar
3. Find your deployed model: `costume-classifier-llama-vision`
4. Click on the model
5. Copy the Model ID from the URL or model details
   - Format: `model-xxxxx`
   - Example: `model-a1b2c3d4`

## Step 4: Configure Environment Variables

1. Open your `.env` file in the project root
2. Add your credentials:

```bash
# Baseten API for costume classification
BASETEN_API_KEY=BTxxxxxxxxxxxxxxxxxxxxxx
BASETEN_MODEL_ID=model-xxxxx
```

3. Save the file
4. **Never commit `.env` to git!** (already in `.gitignore`)

## Step 5: Test the Deployment

### Install Dependencies

```bash
uv sync
```

This will install the required packages:
- `pillow` - Image processing
- `requests` - HTTP client
- `opencv-python` - Computer vision

### Test with Example Image

Create a test image or download a sample:

```bash
# Download a sample Halloween costume image
wget https://example.com/witch-costume.jpg -O test_costume.jpg
```

Run the classifier:

```bash
uv run python costume_classifier.py test_costume.jpg
```

Expected output:

```
Classifying costume from: test_costume.jpg
Please wait...

============================================================
Costume Description: witch with purple hat and broom
Latency: 2.34 seconds
Tokens: 123 in, 8 out
============================================================
```

### Test from Python

```python
from costume_classifier import CostumeClassifier
from PIL import Image

# Initialize classifier
classifier = CostumeClassifier()

# Test with image file
result = classifier.classify_from_file("test_costume.jpg")

if result["success"]:
    print(f"Description: {result['description']}")
    print(f"Latency: {result['latency']:.2f}s")
else:
    print(f"Error: {result['error']}")
```

### Test with OpenCV (Integration Preview)

```python
import cv2
from costume_classifier import CostumeClassifier

# Initialize classifier
classifier = CostumeClassifier()

# Load image with OpenCV (simulating YOLO cropped image)
image = cv2.imread("test_costume.jpg")

# Classify
result = classifier.classify_from_array(image)

if result["success"]:
    print(f"Costume: {result['description']}")
```

## Step 6: Monitor Usage and Costs

### View Real-time Metrics

1. Go to Baseten dashboard
2. Click on your model
3. View metrics:
   - Requests per minute
   - Latency (p50, p95, p99)
   - Error rate
   - GPU utilization

### Check Billing

1. Go to Settings → Billing
2. View current usage
3. Set spending alerts (recommended):
   - Alert at $5/month
   - Alert at $10/month

### Cost Estimation

**For Halloween Night (3-4 hours, 50-200 trick-or-treaters):**

| Scenario | Inferences | Time per Inference | Total Time | Cost (A100 @ $9.984/hr) |
|----------|-----------|-------------------|-----------|------------------------|
| Low traffic | 50 | 2.5s | 125s (2.1 min) | $0.35 |
| Medium traffic | 100 | 2.5s | 250s (4.2 min) | $0.70 |
| High traffic | 150 | 2.5s | 375s (6.25 min) | $1.04 |
| Very high traffic | 200 | 2.5s | 500s (8.3 min) | $1.39 |

**Note:** These costs assume:
- Serverless autoscaling (only pay for active inference time)
- No idle GPU time charges
- A100 GPU at ~$9.984/hour list price
- Average 2.5 seconds per inference

Actual costs may vary based on:
- Baseten volume discounts (possible for larger usage)
- Exact inference time
- Network latency
- Image size

## Step 7: Optimize Settings (Optional)

### Adjust Temperature

Lower temperature = more consistent, focused descriptions:

```python
# More creative (higher variance)
result = classifier.classify_costume(image, temperature=0.7)

# More consistent (lower variance) - RECOMMENDED
result = classifier.classify_costume(image, temperature=0.3)

# Deterministic (no randomness)
result = classifier.classify_costume(image, temperature=0.0)
```

### Adjust Max Tokens

Shorter descriptions = faster + cheaper:

```python
# Very short (3-5 words)
result = classifier.classify_costume(image, max_tokens=20)

# Default (5-10 words)
result = classifier.classify_costume(image, max_tokens=50)

# Longer (allows detailed descriptions)
result = classifier.classify_costume(image, max_tokens=100)
```

### Custom Prompts

Experiment with different prompts:

```python
custom_prompt = """Describe this Halloween costume using exactly 3 words.
Focus on the most distinctive feature.
Examples: "inflatable dinosaur costume", "wizard with staff", "superhero with cape"
"""

result = classifier.classify_costume(
    image,
    custom_prompt=custom_prompt,
    max_tokens=20
)
```

## Troubleshooting

### Error: "Baseten API key required"

**Solution:** Make sure you've set the environment variables:

```bash
export BASETEN_API_KEY='your-api-key'
export BASETEN_MODEL_ID='your-model-id'
```

Or add them to your `.env` file.

### Error: "Request timed out"

**Possible causes:**
- Cold start (first request after idle period)
- Network issues
- Model deployment issue

**Solutions:**
1. Increase timeout: `CostumeClassifier(timeout=60)`
2. Check model status in Baseten dashboard
3. Verify autoscaling settings (min replicas > 0 eliminates cold starts)

### Error: "HTTP error: 401"

**Cause:** Invalid API key

**Solution:**
1. Verify API key in Baseten dashboard
2. Check for typos in `.env` file
3. Make sure you copied the full key

### Error: "HTTP error: 404"

**Cause:** Invalid model ID or model not deployed

**Solution:**
1. Verify model is deployed in Baseten dashboard
2. Check model ID is correct (format: `model-xxxxx`)
3. Wait for deployment to complete if just created

### Poor Quality Descriptions

**Possible issues:**
1. Temperature too high (too creative/random)
2. Prompt not specific enough
3. Image quality too low
4. Background too busy

**Solutions:**
1. Lower temperature to 0.3 or 0.0
2. Refine prompt with more specific instructions
3. Ensure YOLO crops are clear
4. Try adding "ignore background" to prompt

### Slow Response Times

**Expected latency:** 2-3 seconds on A100

**If slower:**
1. Check network connection
2. Verify A100 GPU is being used (not CPU)
3. Check image size (resize to max 1024x1024)
4. Monitor Baseten dashboard for GPU utilization

## Next Steps

1. ✅ Baseten deployment complete
2. ✅ API credentials configured
3. ✅ Test successful
4. Integrate with YOLO person detection
5. Connect to Supabase database
6. Build detection pipeline
7. Create dashboard

## Additional Resources

- [Baseten Documentation](https://docs.baseten.co/)
- [Llama 3.2 Model Card](https://www.baseten.co/library/llama-3-2-11b-vision-instruct/)
- [Baseten API Reference](https://docs.baseten.co/development/model-apis/overview)
- [Baseten Pricing](https://www.baseten.co/pricing/)
- [Truss Documentation](https://truss.baseten.co/)

## Support

If you encounter issues:
1. Check Baseten status: https://status.baseten.co/
2. Join Baseten community: https://discord.gg/baseten
3. Contact support: support@baseten.co
4. Check documentation: https://docs.baseten.co/
