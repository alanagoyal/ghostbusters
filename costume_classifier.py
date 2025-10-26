"""
Costume Classification Module using Baseten Llama 3.2 11B Vision Instruct

This module provides a client for the Baseten API to classify Halloween costumes
from images of people detected by YOLO.
"""

import base64
import os
from io import BytesIO
from typing import Optional

import requests
from PIL import Image


class CostumeClassifier:
    """Client for Baseten Llama 3.2 11B Vision Instruct API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_id: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize the costume classifier.

        Args:
            api_key: Baseten API key. If None, reads from BASETEN_API_KEY env var.
            model_id: Baseten model ID. If None, reads from BASETEN_MODEL_ID env var.
            timeout: Request timeout in seconds (default: 30)
        """
        self.api_key = api_key or os.getenv("BASETEN_API_KEY")
        self.model_id = model_id or os.getenv("BASETEN_MODEL_ID")
        self.timeout = timeout

        if not self.api_key:
            raise ValueError(
                "Baseten API key required. Set BASETEN_API_KEY env var or pass api_key parameter."
            )
        if not self.model_id:
            raise ValueError(
                "Baseten model ID required. Set BASETEN_MODEL_ID env var or pass model_id parameter."
            )

        self.endpoint = (
            f"https://model-{self.model_id}.api.baseten.co/production/predict"
        )
        self.headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
        }

        # Optimized prompt for costume descriptions
        self.system_prompt = """Describe this person's Halloween costume in one short phrase (5-10 words maximum).
Focus only on the costume, not the background.
Examples:
- "witch with purple hat and broom"
- "inflatable T-Rex costume"
- "Spider-Man with web shooters"
- "princess in blue dress with crown"
- "ghost with white sheet"

Be specific about colors and key costume elements."""

    def image_to_base64(self, image: Image.Image) -> str:
        """
        Convert PIL Image to base64 string.

        Args:
            image: PIL Image object

        Returns:
            Base64 encoded string
        """
        buffered = BytesIO()
        image.save(buffered, format="JPEG", quality=85)
        img_bytes = buffered.getvalue()
        return base64.b64encode(img_bytes).decode("utf-8")

    def classify_costume(
        self,
        image: Image.Image,
        temperature: float = 0.3,
        max_tokens: int = 50,
        custom_prompt: Optional[str] = None,
    ) -> dict:
        """
        Classify a costume from a person image.

        Args:
            image: PIL Image of the person (already cropped by YOLO)
            temperature: Sampling temperature (0.0-1.0). Lower = more focused. Default: 0.3
            max_tokens: Maximum tokens to generate. Default: 50 (enough for 10-15 words)
            custom_prompt: Optional custom prompt to override default system prompt

        Returns:
            Dictionary with:
                - success (bool): Whether the classification succeeded
                - description (str): Costume description (if success=True)
                - error (str): Error message (if success=False)
                - usage (dict): Token usage stats (if success=True)
                - latency (float): Response time in seconds

        Raises:
            requests.exceptions.RequestException: If API request fails
        """
        # Encode image to base64
        image_b64 = self.image_to_base64(image)
        image_url = f"data:image/jpeg;base64,{image_b64}"

        # Construct API request
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": custom_prompt or self.system_prompt,
                }
            ],
            "image": image_url,
            "max_new_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }

        try:
            # Make API request
            response = requests.post(
                self.endpoint,
                json=payload,
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()

            # Parse response
            result = response.json()
            latency = response.elapsed.total_seconds()

            return {
                "success": True,
                "description": result.get("completion", "").strip(),
                "usage": result.get("usage", {}),
                "latency": latency,
            }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": f"Request timed out after {self.timeout} seconds",
                "latency": self.timeout,
            }

        except requests.exceptions.HTTPError as e:
            return {
                "success": False,
                "error": f"HTTP error: {e.response.status_code} - {e.response.text}",
                "latency": 0,
            }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}",
                "latency": 0,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "latency": 0,
            }

    def classify_from_file(
        self,
        image_path: str,
        temperature: float = 0.3,
        max_tokens: int = 50,
    ) -> dict:
        """
        Classify a costume from an image file path.

        Args:
            image_path: Path to image file
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Same as classify_costume()
        """
        try:
            image = Image.open(image_path).convert("RGB")
            return self.classify_costume(
                image, temperature=temperature, max_tokens=max_tokens
            )
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to load image: {str(e)}",
                "latency": 0,
            }

    def classify_from_array(
        self,
        image_array,
        temperature: float = 0.3,
        max_tokens: int = 50,
    ) -> dict:
        """
        Classify a costume from a numpy array (e.g., from OpenCV).

        Args:
            image_array: Numpy array in BGR format (OpenCV default)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Same as classify_costume()
        """
        try:
            # Convert BGR to RGB
            import cv2

            image_rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(image_rgb)
            return self.classify_costume(
                image, temperature=temperature, max_tokens=max_tokens
            )
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to convert array to image: {str(e)}",
                "latency": 0,
            }


# Example usage
if __name__ == "__main__":
    import sys

    # Check if image path provided
    if len(sys.argv) < 2:
        print("Usage: python costume_classifier.py <image_path>")
        print("\nMake sure to set these environment variables:")
        print("  export BASETEN_API_KEY='your-api-key'")
        print("  export BASETEN_MODEL_ID='your-model-id'")
        sys.exit(1)

    # Initialize classifier
    try:
        classifier = CostumeClassifier()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Classify costume
    image_path = sys.argv[1]
    print(f"Classifying costume from: {image_path}")
    print("Please wait...")

    result = classifier.classify_from_file(image_path)

    # Print results
    print("\n" + "=" * 60)
    if result["success"]:
        print(f"Costume Description: {result['description']}")
        print(f"Latency: {result['latency']:.2f} seconds")
        if result.get("usage"):
            usage = result["usage"]
            print(f"Tokens: {usage.get('input_tokens', 0)} in, {usage.get('output_tokens', 0)} out")
    else:
        print(f"Error: {result['error']}")
    print("=" * 60)
