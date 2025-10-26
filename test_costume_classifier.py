#!/usr/bin/env python3
"""
Test script for costume classification.
Creates a simple test image and attempts to classify it.
"""

import os

import cv2
import numpy as np
from dotenv import load_dotenv

from costume_classifier import CostumeClassifier

# Load environment variables
load_dotenv()

print("🎃 Costume Classifier Test")
print("=" * 60)

# Check if API key is set
api_key = os.getenv("BASETEN_API_KEY")
if not api_key:
    print("❌ ERROR: BASETEN_API_KEY not set in .env file")
    print()
    print("To fix this:")
    print("1. Get your API key from baseten.co")
    print("2. Add it to your .env file:")
    print("   BASETEN_API_KEY=your_actual_key_here")
    print()
    print("See BASETEN_SETUP.md for detailed instructions.")
    exit(1)

print(f"✅ API key found: {api_key[:15]}...")
print()

# Initialize classifier
try:
    print("🤖 Initializing classifier...")
    classifier = CostumeClassifier()
    print(f"✅ Classifier initialized with model: {classifier.model}")
    print()
except Exception as e:
    print(f"❌ ERROR: Failed to initialize classifier: {e}")
    exit(1)

# Create a simple test image (black square with text)
print("📸 Creating test image...")
test_image = np.zeros((400, 400, 3), dtype=np.uint8)
cv2.putText(
    test_image,
    "TEST",
    (150, 200),
    cv2.FONT_HERSHEY_SIMPLEX,
    2,
    (255, 255, 255),
    3,
)
print("✅ Test image created")
print()

# Try to classify the test image
print("🎭 Testing costume classification...")
print("(This may take 5-10 seconds...)")
print()

try:
    result = classifier.classify_costume(test_image, temperature=0.7, max_tokens=512)

    print("✅ Classification completed!")
    print()
    print("Results:")
    print("-" * 60)
    print(f"Costume:    {result['costume']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Details:    {result['details']}")
    print()
    print("Full Response:")
    print("-" * 60)
    print(result["full_response"])
    print("-" * 60)
    print()

    if result["costume"] == "Error":
        print("⚠️  Classification returned an error.")
        print("This might be normal for a blank test image.")
        print("Try with a real photo to verify the system works.")
    else:
        print("✅ System is working! Ready for real costume classification.")
        print()
        print("Next steps:")
        print("1. Run 'python detect_and_classify_costumes.py'")
        print("2. Wait for trick-or-treaters!")
        print("3. Watch the costume classifications appear")

except Exception as e:
    print(f"❌ ERROR: Classification failed: {e}")
    print()
    print("Possible issues:")
    print("- Invalid API key")
    print("- Network connection problem")
    print("- Baseten API issue")
    print()
    print("Check BASETEN_SETUP.md for troubleshooting.")
    exit(1)

print()
print("=" * 60)
print("🎃 Test complete!")
