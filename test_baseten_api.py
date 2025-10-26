#!/usr/bin/env python3
"""
Test script for Baseten costume classification API.

This script tests the deployed Baseten model by sending a sample image
and displaying the costume description.

Usage:
    python test_baseten_api.py <image_path>

Example:
    python test_baseten_api.py test_images/witch.jpg
"""

import sys
import os
import base64
import requests
from pathlib import Path
from typing import Dict, Any


def load_env():
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        print("❌ Error: .env file not found")
        print("   Create a .env file with:")
        print("   BASETEN_API_KEY=your_api_key")
        print("   BASETEN_MODEL_URL=your_model_url")
        sys.exit(1)

    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key] = value


def classify_costume(
    image_path: str,
    api_key: str,
    model_url: str,
    prompt: str = "What Halloween costume is this person wearing?",
    max_tokens: int = 256,
    temperature: float = 0.3
) -> Dict[str, Any]:
    """
    Send image to Baseten API for costume classification.

    Args:
        image_path: Path to image file
        api_key: Baseten API key
        model_url: Baseten model URL
        prompt: Custom prompt (optional)
        max_tokens: Max tokens to generate (optional)
        temperature: Sampling temperature (optional)

    Returns:
        Dictionary with 'description' and 'confidence' keys
    """
    # Validate image path
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    # Load and encode image
    with open(image_path, "rb") as f:
        image_bytes = f.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

    # Determine image format
    ext = Path(image_path).suffix.lower()
    mime_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp"
    }.get(ext, "image/jpeg")

    # Prepare request payload
    payload = {
        "image": f"data:{mime_type};base64,{image_base64}",
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature
    }

    print(f"📤 Sending request to Baseten...")
    print(f"   Image: {image_path} ({len(image_bytes)} bytes)")
    print(f"   Prompt: {prompt}")

    # Send request
    try:
        response = requests.post(
            model_url,
            headers={
                "Authorization": f"Api-Key {api_key}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=60  # 60 second timeout (accounts for cold starts)
        )
        response.raise_for_status()

        result = response.json()
        return result

    except requests.exceptions.Timeout:
        print("❌ Request timed out (cold start may take 30-60 seconds)")
        print("   Try again in a minute")
        sys.exit(1)

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP error: {e}")
        print(f"   Response: {response.text}")
        sys.exit(1)

    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        sys.exit(1)


def main():
    """Main function."""
    # Check arguments
    if len(sys.argv) < 2:
        print("Usage: python test_baseten_api.py <image_path>")
        print("\nExample:")
        print("  python test_baseten_api.py test_images/witch.jpg")
        sys.exit(1)

    image_path = sys.argv[1]

    # Load environment variables
    load_env()

    api_key = os.getenv("BASETEN_API_KEY")
    model_url = os.getenv("BASETEN_MODEL_URL")

    if not api_key:
        print("❌ Error: BASETEN_API_KEY not found in .env")
        sys.exit(1)

    if not model_url:
        print("❌ Error: BASETEN_MODEL_URL not found in .env")
        sys.exit(1)

    print("=" * 60)
    print("🎃 Halloween Costume Classifier - Baseten API Test")
    print("=" * 60)

    # Classify costume
    result = classify_costume(image_path, api_key, model_url)

    # Display results
    print("\n" + "=" * 60)
    print("✅ Result:")
    print("=" * 60)
    print(f"📝 Description: {result['description']}")
    print(f"🎯 Confidence:  {result['confidence']}")
    print("=" * 60)

    # Check for errors
    if "error" in result:
        print(f"\n⚠️  Warning: {result['error']}")


if __name__ == "__main__":
    main()
