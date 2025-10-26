# Quick Start: Costume Classifier

Fast track to get costume classification working in < 30 minutes.

## Prerequisites

- ✅ Python 3.10+ installed
- ✅ `uv` package manager installed
- ✅ Dependencies installed (`uv sync`)
- ✅ Credit card (for Baseten billing)

## 5-Step Deployment

### Step 1: Create Baseten Account (5 min)

1. Go to: https://www.baseten.co/
2. Sign up with email or GitHub
3. Add payment method (no charges until you use it)

### Step 2: Deploy Model (10 min)

1. Visit: https://www.baseten.co/library/llama-3-2-11b-vision-instruct/
2. Click **"Deploy now"**
3. Configure:
   - Name: `costume-classifier`
   - Hardware: A100 (default)
   - Autoscaling: ON
   - Min replicas: 0
   - Max replicas: 2
4. Click **Deploy**
5. Wait ~5-10 minutes for deployment

### Step 3: Get Credentials (2 min)

**API Key:**
1. Dashboard → Settings → Account → API Keys
2. Create new key: `costume-classifier-key`
3. Copy key (starts with `BT...`)

**Model ID:**
1. Dashboard → Models → `costume-classifier`
2. Copy model ID from URL (format: `model-xxxxx`)

### Step 4: Configure Environment (2 min)

Edit `.env` file:

```bash
BASETEN_API_KEY=BT_your_api_key_here
BASETEN_MODEL_ID=model-xxxxx
```

### Step 5: Test (5 min)

Download test image:

```bash
# Use any Halloween costume image
wget https://picsum.photos/400/600 -O test_costume.jpg
```

Run classifier:

```bash
uv run python costume_classifier.py test_costume.jpg
```

Expected output:

```
Classifying costume from: test_costume.jpg
Please wait...

============================================================
Costume Description: [costume description here]
Latency: 2.34 seconds
Tokens: 123 in, 8 out
============================================================
```

## ✅ Success!

If you see a costume description, you're ready to integrate with YOLO!

## Usage Examples

### From Python Script

```python
from costume_classifier import CostumeClassifier

classifier = CostumeClassifier()

# From file
result = classifier.classify_from_file("person.jpg")
print(result["description"])  # "witch with purple hat"

# From OpenCV (YOLO integration)
import cv2
image = cv2.imread("person.jpg")
result = classifier.classify_from_array(image)
print(result["description"])
```

### With Custom Settings

```python
# More consistent descriptions
result = classifier.classify_costume(
    image,
    temperature=0.3,      # Lower = more consistent
    max_tokens=50         # Concise output
)

# Custom prompt
custom_prompt = "What costume is this? Answer in 5 words."
result = classifier.classify_costume(image, custom_prompt=custom_prompt)
```

## Troubleshooting

### ❌ "Baseten API key required"

**Fix:** Check `.env` file has correct API key

```bash
cat .env | grep BASETEN_API_KEY
```

### ❌ "Request timed out"

**Fix:** Increase timeout or wait for cold start

```python
classifier = CostumeClassifier(timeout=60)
```

### ❌ "HTTP error: 401"

**Fix:** API key is invalid, regenerate in Baseten dashboard

### ❌ "HTTP error: 404"

**Fix:** Model ID is wrong, check model URL in dashboard

## Cost Monitoring

Check costs in real-time:

1. Baseten Dashboard → Settings → Billing
2. View usage and current charges
3. Set spending alerts (recommended):
   - Alert at $5
   - Alert at $10

**Expected costs:**
- Testing (40 images): ~$0.50
- Halloween night (150 kids): ~$1.04

## Next Steps

After successful testing:

1. ✅ Costume classifier working
2. 📋 Implement YOLO person detection
3. 📋 Integrate YOLO → Classifier pipeline
4. 📋 Set up Supabase database
5. 📋 Build dashboard
6. 📋 Deploy to Raspberry Pi

## Full Documentation

- **Architecture:** `COSTUME_CLASSIFICATION_ARCHITECTURE.md`
- **Detailed deployment:** `BASETEN_DEPLOYMENT.md`
- **Testing strategy:** `TEST_PLAN.md`
- **Implementation summary:** `IMPLEMENTATION_SUMMARY.md`

## Support

**Issues?**
- Check full docs above
- Review `costume_classifier.py` code
- Test API credentials
- Check Baseten status: https://status.baseten.co/

**Happy classifying! 🎃**
