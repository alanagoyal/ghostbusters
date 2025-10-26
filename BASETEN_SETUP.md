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
4. Copy your API key (it should start with something like `sk-...`)
5. **IMPORTANT**: Store this key securely - you won't be able to see it again!

### Step 3: Add API Key to Environment

1. Open your `.env` file in the project root:
   ```bash
   nano .env
   ```

2. Add your Baseten API key:
   ```bash
   BASETEN_API_KEY=your_actual_api_key_here
   ```

3. Save and exit (`Ctrl+X`, then `Y`, then `Enter`)

4. Verify it's set:
   ```bash
   grep BASETEN_API_KEY .env
   ```

### Step 4: Install Dependencies

Install the OpenAI client library (used to connect to Baseten):

```bash
uv sync
```

This will install all dependencies including the `openai` package.

### Step 5: Test the Costume Classifier

Run the test script to verify everything works:

```bash
uv run python costume_classifier.py
```

Expected output:
```
Costume Classifier Module
==================================================
✅ Initialized with model: llama-3.2-11b-vision
Ready to classify costumes!
```

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

- **Model**: `llama-3.2-11b-vision`
- **Endpoint**: `https://inference.baseten.co/v1`
- **API Format**: OpenAI-compatible Chat Completions
- **Input**: Base64-encoded images or image URLs
- **Output**: Structured text responses

### API Call Example

```python
from openai import OpenAI

client = OpenAI(
    api_key="your_baseten_api_key",
    base_url="https://inference.baseten.co/v1"
)

response = client.chat.completions.create(
    model="llama-3.2-11b-vision",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}},
                {"type": "text", "text": "What Halloween costume is this?"}
            ]
        }
    ],
    temperature=0.7,
    max_tokens=512
)
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
```

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

To use a different model, modify the `model` parameter in `CostumeClassifier`:

```python
classifier = CostumeClassifier(model="llama-3.2-90b-vision")
```

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
