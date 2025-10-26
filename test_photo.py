#!/usr/bin/env python3
"""
Test costume classification on the provided photo.
"""

import os
import sys

import cv2
from dotenv import load_dotenv

from classify_costume import CostumeClassifier

# Load environment variables
load_dotenv()

# Check OpenAI API key
if not os.getenv("OPENAI_API_KEY"):
    print("❌ ERROR: Missing OPENAI_API_KEY environment variable")
    print("Please add your OpenAI API key to .env file")
    exit(1)

# Path to the test image
image_path = "/tmp/images/image-5gZJYpw92qx-Fn6BbFNpo.png"

if not os.path.exists(image_path):
    print(f"❌ ERROR: Image not found at {image_path}")
    exit(1)

print("🎃 Testing OpenAI Vision Costume Classification")
print("=" * 50)
print()

# Load the image
print(f"📸 Loading image: {image_path}")
image = cv2.imread(image_path)

if image is None:
    print(f"❌ Failed to read image")
    exit(1)

print(f"✅ Loaded image: {image.shape[1]}x{image.shape[0]} pixels")
print()

# Initialize classifier
print("🎨 Initializing OpenAI Vision classifier...")
classifier = CostumeClassifier()
print("✅ Classifier ready!")
print()

# Classify the costume
print("🔍 Analyzing costumes...")
print("   (This may take 1-2 seconds)")
print()

result = classifier.classify(image)

# Display results
print("=" * 50)
print("🎭 CLASSIFICATION RESULTS")
print("=" * 50)
print(f"Description:  {result['description']}")
print(f"Confidence:   {result['confidence']:.2f}")
print(f"Raw response: {result['raw_response']}")
print()
print("✅ Test complete!")
