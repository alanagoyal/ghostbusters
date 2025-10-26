#!/usr/bin/env python3
"""
Costume classification module using OpenAI Vision API.
Takes cropped person images and returns costume descriptions.
"""

import base64
import os
from io import BytesIO

import cv2
from openai import OpenAI


class CostumeClassifier:
    """Classifies Halloween costumes using OpenAI's GPT-4 Vision model."""

    def __init__(self, api_key: str | None = None):
        """
        Initialize the costume classifier.

        Args:
            api_key: OpenAI API key. If None, reads from OPENAI_API_KEY env var.
        """
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"  # GPT-4o has vision capabilities

    def classify(self, image_array, confidence_threshold: float = 0.5) -> dict:
        """
        Classify a Halloween costume from an image.

        Args:
            image_array: OpenCV image array (BGR format) containing a person
            confidence_threshold: Minimum confidence for detection (0-1)

        Returns:
            dict with keys:
                - description: str - Natural language costume description
                - confidence: float - Model confidence (0-1)
                - raw_response: str - Full model response
        """
        # Encode image to base64
        img_base64 = self._encode_image(image_array)

        # Create the prompt for costume classification
        prompt = """Analyze this image and describe the person's Halloween costume in one concise phrase (3-8 words).

Focus on:
- Main costume theme (e.g., witch, superhero, princess, skeleton)
- Key visual details (colors, props, accessories)
- Creative or unique elements

Examples of good descriptions:
- "witch with purple hat and broom"
- "skeleton with glowing bones"
- "homemade cardboard robot"
- "superhero in red cape"
- "inflatable T-Rex costume"

Provide ONLY the costume description, nothing else."""

        try:
            # Call OpenAI Vision API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_base64}",
                                    "detail": "low",  # Use low detail for faster/cheaper API calls
                                },
                            },
                        ],
                    }
                ],
                max_tokens=50,
                temperature=0.3,  # Lower temperature for more consistent descriptions
            )

            # Extract the description
            description = response.choices[0].message.content.strip()

            # OpenAI doesn't provide confidence scores, so we'll use a proxy
            # based on the finish_reason and length of response
            confidence = self._estimate_confidence(response)

            return {
                "description": description,
                "confidence": confidence,
                "raw_response": description,
            }

        except Exception as e:
            print(f"Error classifying costume: {e}")
            return {
                "description": "unknown costume",
                "confidence": 0.0,
                "raw_response": str(e),
            }

    def _encode_image(self, image_array) -> str:
        """
        Encode OpenCV image to base64 string.

        Args:
            image_array: OpenCV image array (BGR format)

        Returns:
            base64 encoded JPEG image string
        """
        # Encode image as JPEG
        success, buffer = cv2.imencode(".jpg", image_array)
        if not success:
            raise ValueError("Failed to encode image")

        # Convert to base64
        img_base64 = base64.b64encode(buffer).decode("utf-8")
        return img_base64

    def _estimate_confidence(self, response) -> float:
        """
        Estimate confidence from OpenAI response.

        Since OpenAI doesn't provide confidence scores for vision tasks,
        we use heuristics based on response quality.

        Args:
            response: OpenAI API response object

        Returns:
            float: Estimated confidence (0-1)
        """
        # Check if the response completed successfully
        if response.choices[0].finish_reason != "stop":
            return 0.5

        # Check response length (very short or very long might indicate issues)
        description = response.choices[0].message.content.strip()
        word_count = len(description.split())

        if 3 <= word_count <= 10:
            return 0.9  # Good length for costume description
        elif word_count < 3:
            return 0.6  # Too short, might be uncertain
        else:
            return 0.75  # Longer description, moderate confidence


def main():
    """Test the costume classifier with a sample image."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python classify_costume.py <image_path>")
        print("Example: python classify_costume.py detection_20241026_123456.jpg")
        sys.exit(1)

    image_path = sys.argv[1]

    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        sys.exit(1)

    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not read image from {image_path}")
        sys.exit(1)

    print(f"Classifying costume in {image_path}...")

    # Create classifier and classify
    classifier = CostumeClassifier()
    result = classifier.classify(image)

    print("\nResults:")
    print(f"  Description: {result['description']}")
    print(f"  Confidence: {result['confidence']:.2f}")


if __name__ == "__main__":
    main()
