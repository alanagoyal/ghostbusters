# Baseten Quick Start Guide

**Goal**: Deploy the costume classification model to Baseten in under 10 minutes.

## Prerequisites

- [ ] Baseten account ([sign up here](https://baseten.co))
- [ ] Python 3.10+
- [ ] Terminal access

## Step 1: Install Truss (1 minute)

```bash
pip install truss
# or using uv
uv pip install truss
```

## Step 2: Authenticate (1 minute)

```bash
truss login
```

This opens a browser window to authenticate with Baseten.

## Step 3: Deploy Model (2 minutes to start, 10-15 minutes to build)

```bash
cd truss_costume_classifier
truss push
```

**Expected output**:
```
📦 Building Truss...
🚀 Uploading Truss...
🔨 Building model container...
✅ Model deployed successfully!

Model ID: abc123xyz
Model URL: https://model-abc123xyz.api.baseten.co/production/predict
```

**Important**: Copy the Model ID and URL!

## Step 4: Save Credentials (1 minute)

Add to your `.env` file:

```bash
echo "BASETEN_API_KEY=your_api_key_here" >> .env
echo "BASETEN_MODEL_ID=abc123xyz" >> .env
echo "BASETEN_MODEL_URL=https://model-abc123xyz.api.baseten.co/production/predict" >> .env
```

**Get your API key**: Baseten Dashboard → Settings → API Keys

## Step 5: Wait for Build (10-15 minutes)

While the model builds, grab a coffee! ☕

Monitor progress:
```bash
truss watch abc123xyz
```

Or check the Baseten dashboard.

## Step 6: Test Deployment (2 minutes)

Once the model status is "Active":

```bash
# Test with an image
python test_baseten_api.py path/to/test_image.jpg
```

**Expected output**:
```
📤 Sending request to Baseten...
   Image: test_image.jpg (245123 bytes)
   Prompt: What Halloween costume is this person wearing?

============================================================
✅ Result:
============================================================
📝 Description: witch with purple hat and broom
🎯 Confidence:  None
============================================================
```

## Step 7: Integrate with Pi (5 minutes)

Use the API client in your detection pipeline:

```python
from classify_costume_api import classify_costume
import cv2

# Load image
image = cv2.imread("person_crop.jpg")

# Classify costume
result = classify_costume(image)

print(f"Costume: {result['description']}")
# Output: "witch with purple hat and broom"
```

## Done! 🎉

Your costume classification model is now deployed and ready to use!

## Next Steps

### Before Halloween Night

1. **Warmup the model** (prevents cold start):
   ```bash
   python classify_costume_api.py --warmup
   ```

2. **Set budget alerts**: Go to Baseten dashboard → Billing → Set alert

3. **Test full pipeline**: RTSP → YOLO → Baseten → Supabase

### Need Help?

- **Full guide**: See `docs/BASETEN_DEPLOYMENT.md` (comprehensive 5000+ word guide)
- **Checklist**: See `docs/BASETEN_CHECKLIST.md` (step-by-step checklist)
- **Summary**: See `docs/BASETEN_SUMMARY.md` (architecture and design decisions)
- **Baseten Docs**: https://docs.baseten.co
- **Discord**: https://discord.gg/baseten

## Troubleshooting

### "Model build failed"

Check logs:
```bash
truss logs abc123xyz --tail 100
```

Common causes:
- PyPI package version conflicts
- HuggingFace model download issues
- GPU memory issues

### "Request timed out"

- **First request**: Expected (cold start takes 30-60 seconds)
- **Subsequent requests**: Check Baseten status page
- **Solution**: Send warmup request before event

### "Empty or poor descriptions"

- Try increasing temperature: Edit `model/model.py` and change `DEFAULT_TEMPERATURE = 0.5`
- Redeploy: `truss push`

### "API authentication error"

- Verify API key in `.env` file
- Check key is active in Baseten dashboard
- Ensure `.env` file is loaded (use `python-dotenv`)

## Cost Estimate

**Halloween Night (3 hours, 100 trick-or-treaters)**:
- Total cost: ~$0.10-$0.50
- Cost per inference: ~$0.001-$0.005

**Scale-to-zero** means:
- ✅ $0/hour when idle
- ✅ ~$0.50/hour when active
- ✅ Auto-shuts down after 10 minutes idle

## Configuration

### Using Different GPU

Edit `truss_costume_classifier/config.yaml`:

```yaml
resources:
  accelerator: A10G  # Options: L4, A10G, A100, H100
```

### Adjusting Concurrency

```yaml
runtime:
  predict_concurrency: 8  # Increase for more parallel requests
```

### Using Different Model

```yaml
model_cache:
  - repo_id: liuhaotian/llava-v1.6-vicuna-7b  # Change to different VLM
```

Update `model/model.py` to load the new model.

---

**Time to deploy**: ~25 minutes total (15 minutes is waiting for build)

**Time to test**: ~5 minutes

**Total time**: ~30 minutes from zero to deployed model! 🚀
