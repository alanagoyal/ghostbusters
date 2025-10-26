#!/usr/bin/env python3
"""
Baseten API client for Qwen-VL costume classification.
Handles image encoding and API communication.
"""

import base64
import os
from io import BytesIO
from typing import Optional, Union

import numpy as np
import requests
from dotenv import load_dotenv
from PIL import Image

load_dotenv()


class BasetenClient:
    """Client for interacting with Qwen-VL model on Baseten."""

    def __init__(self):
        self.api_key = os.getenv("BASETEN_API_KEY")
        self.model_url = os.getenv("BASETEN_MODEL_URL")

        if not self.api_key:
            raise ValueError("BASETEN_API_KEY not found in .env file")
        if not self.model_url:
            raise ValueError(
                "BASETEN_MODEL_URL not found in .env file. "
                "Please deploy the model first and add the URL."
            )

        self.headers = {"Authorization": f"Api-Key {self.api_key}"}

    def _encode_image(
        self, image: Union[str, np.ndarray, Image.Image]
    ) -> str:
        """
        Convert image to base64 string with data URI preamble.

        Args:
            image: Can be a file path, numpy array (OpenCV), or PIL Image

        Returns:
            Base64 encoded image string with data:image/png;base64, preamble
        """
        b64_data = None

        if isinstance(image, str):
            # File path
            with open(image, "rb") as f:
                b64_data = base64.b64encode(f.read()).decode("utf-8")
        elif isinstance(image, np.ndarray):
            # OpenCV/numpy array
            pil_img = Image.fromarray(image)
            buffered = BytesIO()
            pil_img.save(buffered, format="PNG")
            b64_data = base64.b64encode(buffered.getvalue()).decode("utf-8")
        elif isinstance(image, Image.Image):
            # PIL Image
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            b64_data = base64.b64encode(buffered.getvalue()).decode("utf-8")
        else:
            raise ValueError(
                f"Unsupported image type: {type(image)}. "
                "Expected str (path), np.ndarray, or PIL.Image"
            )

        # Add data URI preamble required by Qwen-VL
        return f"data:image/png;base64,{b64_data}"

    def classify_costume(
        self, image: Union[str, np.ndarray, Image.Image], prompt: Optional[str] = None
    ) -> str:
        """
        Classify a Halloween costume in an image.

        Args:
            image: Image to classify (path, numpy array, or PIL Image)
            prompt: Custom prompt (uses default costume classification if None)

        Returns:
            Classification result as string
        """
        if prompt is None:
            prompt = (
                "You are a Halloween costume classifier. "
                "Analyze this image and identify what Halloween costume the person is wearing. "
                "Provide a specific costume name (e.g., 'Witch', 'Vampire', 'Superhero - Spider-Man', "
                "'Princess - Elsa', 'Ghost', 'Zombie'). "
                "If you can see multiple people, describe each costume. "
                "If no clear costume is visible, say 'No costume detected'. "
                "Be specific but concise - just the costume name(s)."
            )

        # Encode image
        image_b64 = self._encode_image(image)

        # Make API request
        payload = {"image": image_b64, "prompt": prompt}

        try:
            response = requests.post(
                self.model_url, headers=self.headers, json=payload, timeout=60
            )
            response.raise_for_status()

            result = response.json()
            return result.get("output", result)

        except requests.exceptions.Timeout:
            return "Error: Request timed out (model may be cold starting)"
        except requests.exceptions.RequestException as e:
            # Try to get detailed error message from response
            error_details = str(e)
            try:
                if hasattr(e, 'response') and e.response is not None:
                    error_body = e.response.text
                    error_details = f"{str(e)}\nResponse: {error_body}"
            except:
                pass
            return f"Error: API request failed - {error_details}"

    def analyze_image(
        self, image: Union[str, np.ndarray, Image.Image], prompt: str
    ) -> str:
        """
        Analyze an image with a custom prompt.

        Args:
            image: Image to analyze (path, numpy array, or PIL Image)
            prompt: Custom analysis prompt

        Returns:
            Analysis result as string
        """
        return self.classify_costume(image, prompt=prompt)


def test_connection():
    """Test Baseten connection and model availability."""
    try:
        client = BasetenClient()
        print("✅ BasetenClient initialized successfully")
        print(f"   Model URL: {client.model_url}")
        return True
    except ValueError as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    # Quick connection test
    test_connection()
