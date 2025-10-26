#!/usr/bin/env python3
"""
Quick test script for OpenAI Vision costume classification.
Downloads a test image and classifies it.
"""

import os

import cv2
import requests
from dotenv import load_dotenv

from classify_costume import CostumeClassifier

# Load environment variables
load_dotenv()

# Check OpenAI API key
if not os.getenv("OPENAI_API_KEY"):
    print("❌ ERROR: Missing OPENAI_API_KEY environment variable")
    print("Please add your OpenAI API key to .env file")
    exit(1)

print("🎃 Testing OpenAI Vision Costume Classification")
print("=" * 50)
print()

# Option 1: Use an existing detection image if available
test_image_path = None
for filename in os.listdir("."):
    if filename.startswith("detection_") and filename.endswith(".jpg"):
        test_image_path = filename
        break

if test_image_path:
    print(f"📸 Found existing test image: {test_image_path}")
    image = cv2.imread(test_image_path)
else:
    # Option 2: Download a test Halloween costume image
    print("📥 No local detection images found, downloading test image...")
    test_url = "https://images.unsplash.com/photo-1509557965875-b88c97052f0e?w=800&q=80"

    try:
        response = requests.get(test_url, timeout=10)
        response.raise_for_status()

        # Save test image
        test_image_path = "test_costume.jpg"
        with open(test_image_path, "wb") as f:
            f.write(response.content)

        print(f"✅ Downloaded test image to {test_image_path}")
        image = cv2.imread(test_image_path)
    except Exception as e:
        print(f"❌ Failed to download test image: {e}")
        print(
            "\nAlternative: Run detect_people.py first to generate a detection image,"
        )
        print("then run this script again.")
        exit(1)

if image is None:
    print(f"❌ Failed to read image from {test_image_path}")
    exit(1)

print(f"✅ Loaded image: {image.shape[1]}x{image.shape[0]} pixels")
print()

# Initialize classifier
print("🎨 Initializing OpenAI Vision classifier...")
classifier = CostumeClassifier()
print("✅ Classifier ready!")
print()

# Classify the costume
print("🔍 Analyzing costume...")
print("   (This may take 1-2 seconds)")
print()

result = classifier.classify(image)

# Display results
print("=" * 50)
print("🎭 CLASSIFICATION RESULTS")
print("=" * 50)
print(f"Description:  {result['description']}")
print(f"Confidence:   {result['confidence']:.2f}")
print()
print("✅ Test complete!")
print()
print("Next steps:")
print("  1. Run 'uv run python detect_and_classify.py' to test the full pipeline")
print("  2. Wave at your DoorBird camera to generate a real detection")
print("  3. See the costume classification in real-time!")
