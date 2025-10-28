#!/usr/bin/env python3
"""
Test script for Baseten API connection and costume classification.
Tests the vision model with a sample image.
"""

import os
import sys

import cv2
from dotenv import load_dotenv

from baseten_client import BasetenClient

# Load environment variables
load_dotenv()


def create_test_image():
    """
    Create a simple test image with text.
    Returns: image as bytes in JPEG format
    """
    import numpy as np

    # Create a blank image (640x480, white background)
    img = np.ones((480, 640, 3), dtype=np.uint8) * 255

    # Add some text to make it identifiable
    cv2.putText(
        img,
        "TEST IMAGE",
        (150, 240),
        cv2.FONT_HERSHEY_SIMPLEX,
        2,
        (0, 0, 255),
        3,
    )

    # Encode to JPEG
    _, buffer = cv2.imencode(".jpg", img)
    return buffer.tobytes()


def main():
    """Test Baseten API connection and costume classification"""
    print("🧪 Testing Baseten API Connection")
    print("=" * 50)

    # Check for API key
    api_key = os.getenv("BASETEN_API_KEY")
    if not api_key:
        print("❌ ERROR: BASETEN_API_KEY not set in .env file")
        print("   Please add your Baseten API key to .env")
        sys.exit(1)

    # Check for model URL
    model_url = os.getenv("BASETEN_MODEL_URL")
    if not model_url:
        print("❌ ERROR: BASETEN_MODEL_URL not set in .env file")
        print("   Please add your Baseten model URL to .env")
        sys.exit(1)

    print(f"✅ API key found: {api_key[:10]}...")
    print(f"✅ Model URL found: {model_url[:50]}...")
    print()

    # Initialize client
    print("🔧 Initializing Baseten client...")
    try:
        client = BasetenClient()
        print("✅ Client initialized successfully")
        print(f"   Model: {client.model}")
        print(f"   Endpoint: {client.model_url}")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        sys.exit(1)

    # Test basic connection
    print("🔌 Testing API connection...")
    if client.test_connection():
        print("✅ Connection test passed!")
        print()
    else:
        print("❌ Connection test failed")
        print("   Check your API key and network connection")
        sys.exit(1)

    # Test with sample image
    print("🖼️  Testing costume classification with sample image...")
    print()

    # Create test image
    test_image = create_test_image()
    print("   📸 Created test image (640x480 white background with text)")

    # Classify
    print("   🤖 Sending to Baseten for classification...")
    classification, confidence, description = client.classify_costume(test_image)

    # Display results
    print()
    print("=" * 50)
    print("🎭 CLASSIFICATION RESULTS")
    print("=" * 50)

    if classification:
        print(f"   Classification: {classification}")
        print(f"   Confidence:     {confidence:.2f}")
        print(f"   Description:    {description}")
        print()
        print("✅ Classification successful!")
        print()
        print("💡 Note: This is just a test image with text.")
        print("   For real costume detection, use actual photos.")
    else:
        print("❌ Classification failed - no results returned")
        sys.exit(1)

    # Instructions for next steps
    print()
    print("=" * 50)
    print("🎉 NEXT STEPS")
    print("=" * 50)
    print("1. Test with a real image:")
    print("   - Take a photo of someone in a costume")
    print("   - Save it as test_costume.jpg")
    print("   - Modify this script to load that image")
    print()
    print("2. Integrate into detect_people.py:")
    print("   - The baseten_client module is ready to use")
    print("   - Import it in detect_people.py")
    print("   - Call classify_costume() on person crops")
    print()
    print("3. Monitor usage and costs:")
    print("   - Check Baseten dashboard for API usage")
    print("   - Llama 3.2 90B Vision pricing applies per request")
    print()


if __name__ == "__main__":
    main()
