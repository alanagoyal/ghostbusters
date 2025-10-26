#!/usr/bin/env python3
"""
Costume classification API client for Raspberry Pi integration.

This module provides a simple interface for classifying costumes
using the Baseten API. It's designed to integrate with the Pi's
person detection pipeline.

Usage:
    from classify_costume_api import classify_costume

    # person_crop is a NumPy array (OpenCV image)
    result = classify_costume(person_crop)
    print(f"Costume: {result['description']}")
"""

import os
import base64
import time
from typing import Dict, Any, Optional
import requests
import cv2
import numpy as np


# Load API credentials from environment
BASETEN_API_KEY = os.getenv("BASETEN_API_KEY")
BASETEN_MODEL_URL = os.getenv("BASETEN_MODEL_URL")

# Configuration
DEFAULT_PROMPT = "What Halloween costume is this person wearing? Provide a brief, specific description."
DEFAULT_MAX_TOKENS = 256
DEFAULT_TEMPERATURE = 0.3
REQUEST_TIMEOUT = 60  # seconds (accounts for cold starts)
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds


class CostumeClassifierError(Exception):
    """Custom exception for costume classification errors."""
    pass


def classify_costume(
    person_crop: np.ndarray,
    prompt: str = DEFAULT_PROMPT,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE,
    retry: bool = True
) -> Dict[str, Any]:
    """
    Classify a costume from a cropped person image using Baseten API.

    Args:
        person_crop: NumPy array (OpenCV image) of cropped person
        prompt: Custom prompt for classification (optional)
        max_tokens: Maximum tokens to generate (optional)
        temperature: Sampling temperature 0-1 (optional)
        retry: Whether to retry on failure (optional)

    Returns:
        Dictionary with keys:
            - description: Costume description string
            - confidence: Confidence score (always None for Qwen2-VL)
            - error: Error message if classification failed

    Raises:
        CostumeClassifierError: If API credentials are missing
        CostumeClassifierError: If all retry attempts fail (when retry=False)

    Example:
        >>> import cv2
        >>> image = cv2.imread("person.jpg")
        >>> result = classify_costume(image)
        >>> print(result["description"])
        "witch with purple hat and broom"
    """
    # Validate API credentials
    if not BASETEN_API_KEY:
        raise CostumeClassifierError(
            "BASETEN_API_KEY not set. Add to .env file."
        )

    if not BASETEN_MODEL_URL:
        raise CostumeClassifierError(
            "BASETEN_MODEL_URL not set. Add to .env file."
        )

    # Encode image to base64
    try:
        _, buffer = cv2.imencode('.jpg', person_crop)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
    except Exception as e:
        return {
            "description": "unknown costume",
            "confidence": None,
            "error": f"Failed to encode image: {e}"
        }

    # Prepare request payload
    payload = {
        "image": f"data:image/jpeg;base64,{img_base64}",
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature
    }

    # Attempt classification with retry logic
    attempts = MAX_RETRIES if retry else 1

    for attempt in range(1, attempts + 1):
        try:
            response = requests.post(
                BASETEN_MODEL_URL,
                headers={
                    "Authorization": f"Api-Key {BASETEN_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()

            result = response.json()

            # Successful response
            return {
                "description": result.get("description", "unknown costume"),
                "confidence": result.get("confidence"),
                "error": result.get("error")
            }

        except requests.exceptions.Timeout:
            error_msg = f"Request timed out (attempt {attempt}/{attempts})"
            print(f"⚠️  {error_msg}")

            if attempt < attempts:
                print(f"   Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
                continue

            return {
                "description": "unknown costume",
                "confidence": None,
                "error": error_msg
            }

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error {response.status_code}: {response.text}"
            print(f"❌ {error_msg}")

            # Don't retry on 4xx errors (client errors)
            if 400 <= response.status_code < 500:
                return {
                    "description": "unknown costume",
                    "confidence": None,
                    "error": error_msg
                }

            # Retry on 5xx errors (server errors)
            if attempt < attempts:
                print(f"   Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
                continue

            return {
                "description": "unknown costume",
                "confidence": None,
                "error": error_msg
            }

        except requests.exceptions.RequestException as e:
            error_msg = f"Request error: {e}"
            print(f"❌ {error_msg}")

            if attempt < attempts:
                print(f"   Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
                continue

            return {
                "description": "unknown costume",
                "confidence": None,
                "error": error_msg
            }

    # Should never reach here
    return {
        "description": "unknown costume",
        "confidence": None,
        "error": "All retry attempts failed"
    }


def warmup_model():
    """
    Send a warmup request to prevent cold start during Halloween night.

    This should be called 30-60 minutes before the event starts.
    Uses a small 1x1 pixel dummy image to minimize cost.

    Returns:
        bool: True if warmup successful, False otherwise
    """
    print("🔥 Warming up Baseten model...")

    # Create tiny dummy image (1x1 pixel)
    dummy_image = np.zeros((1, 1, 3), dtype=np.uint8)

    result = classify_costume(
        dummy_image,
        prompt="test",
        max_tokens=10,
        retry=True
    )

    if result.get("error"):
        print(f"❌ Warmup failed: {result['error']}")
        return False

    print("✅ Model warmed up successfully!")
    return True


# Example usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python classify_costume_api.py <image_path>")
        print("\nOr to warmup the model:")
        print("  python classify_costume_api.py --warmup")
        sys.exit(1)

    if sys.argv[1] == "--warmup":
        warmup_model()
        sys.exit(0)

    # Load test image
    image_path = sys.argv[1]
    image = cv2.imread(image_path)

    if image is None:
        print(f"❌ Failed to load image: {image_path}")
        sys.exit(1)

    print(f"🎃 Classifying costume from: {image_path}")
    result = classify_costume(image)

    print("\n" + "=" * 60)
    print("Result:")
    print("=" * 60)
    print(f"Description: {result['description']}")
    print(f"Confidence:  {result['confidence']}")

    if result.get("error"):
        print(f"Error:       {result['error']}")

    print("=" * 60)
