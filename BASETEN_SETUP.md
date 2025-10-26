# Baseten Setup Guide

This guide walks you through setting up Baseten for costume classification using the Llama 3.2 Vision model.

## What is Baseten?

Baseten is an AI infrastructure platform that provides production-ready APIs for deploying and serving AI models. For this project, we're using their **Llama 3.2 11B Vision Instruct** model, which can analyze images and identify objects, including Halloween costumes.

## Why Llama 3.2 Vision?

- **Visual Recognition**: Optimized for image understanding and object detection
- **Fast Inference**: 11B parameter model balances speed and accuracy
- **OpenAI-Compatible API**: Uses standard OpenAI client library
- **Production-Ready**: Hosted on Baseten's scalable infrastructure
- **Cost-Effective**: Pay per request, no idle server costs

## Setup Instructions

### Step 1: Create a Baseten Account

1. Visit [baseten.co](https://www.baseten.co/)
2. Click "Sign Up" or "Get Started"
3. Create your account (email or GitHub OAuth)
4. Complete the onboarding process

### Step 2: Get Your API Key

1. Log into your Baseten dashboard
2. Navigate to **Settings** or **API Keys** section
3. Click "Create API Key" or "Generate New Key"
4. Copy your API key
5. **IMPORTANT**: Store this key securely - you won't be able to see it again!

### Step 3: Deploy the Llama 3.2 Vision Model

**Important**: Baseten has two types of offerings:
- **Model APIs**: Pre-hosted models with fixed endpoints (currently no vision models)
- **Model Library**: Models you deploy yourself (this is what we need)

1. Visit the model deployment page:
   ```
   https://app.baseten.co/deploy/llama-3-2-11b-vision-instruct-vllm
   ```

2. Click the **"Deploy now"** button

3. Configure deployment settings:
   - Accept default settings (GPU type, scaling, etc.)
   - Click "Deploy"

4. Wait for deployment to complete (usually 2-5 minutes)

5. Once deployed, copy your **model ID**:
   - It will look like: `abc123xyz` (an alphanumeric string)
   - You'll see it in the deployment URL: `https://model-{YOUR_MODEL_ID}.api.baseten.co/...`

### Step 4: Add Credentials to Environment

1. Open your `.env` file in the project root:
   ```bash
   nano .env
   ```

2. Add both your API key and model ID:
   ```bash
   BASETEN_API_KEY=your_actual_api_key_here
   BASETEN_MODEL_ID=your_model_id_here
   ```

3. Save and exit (`Ctrl+X`, then `Y`, then `Enter`)

4. Verify they're set:
   ```bash
   grep BASETEN .env
   ```

### Step 5: Install Dependencies

Install required dependencies:

```bash
uv sync
```

This will install all dependencies including `openai` and `requests`.

### Step 6: Test the Costume Classifier

Run the test script to verify everything works:

```bash
uv run python costume_classifier.py
```

Expected output:
```
Costume Classifier Module
==================================================
✅ Initialized with deployed model
   Model ID: your_model_id
   Endpoint: https://model-your_model_id.api.baseten.co/production/predict
Ready to classify costumes!
```

If you see an error about missing `BASETEN_MODEL_ID`, make sure you completed Step 3 (Deploy the model) and Step 4 (Add credentials to .env).

## Usage

### Basic Costume Classification

The `costume_classifier.py` module provides a `CostumeClassifier` class:

```python
from costume_classifier import CostumeClassifier
import cv2

# Initialize classifier
classifier = CostumeClassifier()

# Load an image
image = cv2.imread("person.jpg")

# Classify costume
result = classifier.classify_costume(image)

print(f"Costume: {result['costume']}")
print(f"Confidence: {result['confidence']}")
print(f"Details: {result['details']}")
```

### Integrated Detection + Classification

Run the complete pipeline with:

```bash
uv run python detect_and_classify_costumes.py
```

This script:
1. Connects to your DoorBird camera RTSP stream
2. Detects people using YOLOv8
3. Classifies their costumes using Baseten's Llama 3.2 Vision
4. Saves annotated images with costume labels

## API Details

### Model Information

- **Model**: Llama 3.2 11B Vision Instruct
- **Deployment**: Model Library (requires individual deployment)
- **Endpoint Format**: `https://model-{YOUR_MODEL_ID}.api.baseten.co/production/predict`
- **API Format**: REST API with JSON payload
- **Input**: Base64-encoded images + text prompt
- **Output**: JSON with model response

### API Call Example

```python
import requests
import os

model_id = os.getenv("BASETEN_MODEL_ID")
api_key = os.getenv("BASETEN_API_KEY")

payload = {
    "messages": [{"role": "user", "content": "What Halloween costume is this?"}],
    "image": "data:image/jpeg;base64,...",  # base64-encoded image
    "max_new_tokens": 512,
    "temperature": 0.7
}

response = requests.post(
    f"https://model-{model_id}.api.baseten.co/production/predict",
    headers={"Authorization": f"Api-Key {api_key}"},
    json=payload
)

result = response.json()
print(result["output"])
```

### Rate Limits & Pricing

Check your Baseten dashboard for:
- Current rate limits
- Pricing per request
- Usage statistics
- Billing information

**Note**: The free tier may have limitations. Monitor your usage to avoid unexpected charges.

## Troubleshooting

### Error: "BASETEN_API_KEY environment variable not set"

**Solution**: Make sure your `.env` file exists and contains:
```bash
BASETEN_API_KEY=your_actual_key
BASETEN_MODEL_ID=your_model_id
```

### Error: "BASETEN_MODEL_ID environment variable not set"

**Cause**: You haven't deployed the model yet or haven't added the model ID to your `.env`

**Solution**:
1. Deploy the model at: https://app.baseten.co/deploy/llama-3-2-11b-vision-instruct-vllm
2. Copy your model ID from the deployment
3. Add it to `.env`: `BASETEN_MODEL_ID=your_model_id`

### Error: "Failed to encode image"

**Cause**: Invalid or corrupted image data

**Solution**:
- Verify the image loads correctly with `cv2.imread()`
- Check that person detection bounding boxes are valid
- Ensure cropped person images are large enough (>50x50 pixels)

### Error: API connection timeout

**Causes**:
- No internet connection
- Baseten API outage
- Firewall blocking HTTPS requests

**Solutions**:
- Check internet connection: `ping baseten.co`
- Verify API key is correct
- Check Baseten status page
- Try again in a few moments

### Low Confidence Results

**Tips for better classification**:
- Ensure good lighting in camera view
- Wait for people to face the camera
- Avoid classifying people too far from camera
- Use higher-resolution person crops if possible

## Model Limitations

The Llama 3.2 Vision model:
- Processes **one image per request**
- Works best with **clear, well-lit images**
- May struggle with:
  - Very small or distant people
  - Unusual or highly creative costumes
  - Poor lighting conditions
  - Partially obscured people

## Alternative Models

If you need different capabilities, Baseten offers other vision models:

1. **Llama 3.2 90B Vision Instruct**: More accurate but slower/pricier
2. **Qwen3 VL 235B**: Very large, highest accuracy
3. **Custom Models**: Deploy your own fine-tuned model

To use a different model:
1. Deploy the model from Baseten's Model Library
2. Get the new model ID
3. Update your `.env` file with the new `BASETEN_MODEL_ID`

For example, to use the larger 90B model:
1. Deploy: https://app.baseten.co/deploy/llama-3-2-90b-vision-instruct-vllm
2. Get the model ID
3. Update `.env`: `BASETEN_MODEL_ID=your_new_model_id`

## Next Steps

1. ✅ Baseten account created
2. ✅ API key configured
3. ✅ Dependencies installed
4. ✅ Test classification working
5. 🔄 Run integrated detection system
6. 📊 Set up Supabase for data storage (next phase)

## Resources

- [Baseten Documentation](https://docs.baseten.co/)
- [Baseten Model Library](https://www.baseten.co/library/)
- [Llama 3.2 Vision Model](https://www.baseten.co/library/llama-3-2-11b-vision-instruct/)
- [OpenAI Python Client](https://github.com/openai/openai-python)

## Support

- Baseten Support: support@baseten.co
- Project Issues: [GitHub Issues](https://github.com/your-repo/issues)
- Documentation: This repository's `/docs` folder
