#!/usr/bin/env python3
"""
Test script to verify Baseten Qwen-VL deployment.
Tests the connection and runs a sample classification.
"""

import os
import sys

from baseten_client import BasetenClient
from dotenv import load_dotenv

load_dotenv()


def main():
    print("🧪 Testing Baseten Qwen-VL Model")
    print("=" * 50)
    print()

    # Check environment variables
    print("1. Checking environment variables...")
    api_key = os.getenv("BASETEN_API_KEY")
    model_url = os.getenv("BASETEN_MODEL_URL")

    if not api_key:
        print("❌ BASETEN_API_KEY not found in .env")
        print("   Please add your Baseten API key to .env")
        sys.exit(1)
    else:
        print(f"   ✅ API Key: {api_key[:20]}...")

    if not model_url:
        print("❌ BASETEN_MODEL_URL not found in .env")
        print("   Please deploy the model and add the URL to .env")
        print()
        print("   Format: BASETEN_MODEL_URL=https://model-<ID>.api.baseten.co/development/predict")
        sys.exit(1)
    else:
        print(f"   ✅ Model URL: {model_url}")

    print()

    # Initialize client
    print("2. Initializing Baseten client...")
    try:
        client = BasetenClient()
        print("   ✅ Client initialized")
    except Exception as e:
        print(f"   ❌ Failed to initialize client: {e}")
        sys.exit(1)

    print()

    # Check for test image
    print("3. Looking for test image...")
    test_images = [
        "test_doorbird_frame.jpg",
        "detection_*.jpg",  # Any detection from person detector
    ]

    test_image = None
    for pattern in test_images:
        if "*" in pattern:
            # Find first matching file
            import glob

            matches = glob.glob(pattern)
            if matches:
                test_image = matches[0]
                break
        elif os.path.exists(pattern):
            test_image = pattern
            break

    if not test_image:
        print("   ⚠️  No test image found")
        print("   Run test_doorbird_connection.py first to capture a test image")
        print()
        print("   Skipping image classification test...")
        print()
        print("🎉 Baseten client setup is correct!")
        print("   Ready to classify costumes once you have images")
        return

    print(f"   ✅ Found test image: {test_image}")
    print()

    # Test classification
    print("4. Testing costume classification...")
    print("   (This may take 30-60 seconds on first request - cold start)")
    print()

    try:
        result = client.classify_costume(test_image)

        # Check if result is an error message
        if result.startswith("Error:"):
            print("   ❌ Classification failed!")
            print()
            print("   Error Details:")
            print("   " + "-" * 40)
            print(f"   {result}")
            print("   " + "-" * 40)
            print()

            # Check for specific errors
            if "not ready" in result.lower():
                print("⏳ Model is still deploying!")
                print()
                print("   The model needs more time to build and deploy.")
                print("   This usually takes 5-15 minutes for first deployment.")
                print()
                print("   Monitor progress at:")
                print("   https://app.baseten.co/models/nwxd8o7q/logs")
                print()
                print("   Run this script again in a few minutes.")
                sys.exit(1)
            else:
                sys.exit(1)

        # Success - got actual classification result
        print("   ✅ Classification successful!")
        print()
        print("   Result:")
        print("   " + "-" * 40)
        print(f"   {result}")
        print("   " + "-" * 40)
        print()
    except Exception as e:
        print(f"   ❌ Classification failed: {e}")
        sys.exit(1)

    # Success!
    print()
    print("=" * 50)
    print("🎉 All tests passed!")
    print()
    print("Next steps:")
    print("  1. Run classify_costumes.py to start real-time classification")
    print("  2. Test with actual Halloween costumes")
    print("  3. Deploy to Raspberry Pi")


if __name__ == "__main__":
    main()
