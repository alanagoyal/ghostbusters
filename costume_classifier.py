#!/usr/bin/env python3
"""
Costume classification module using Baseten's Llama 3.2 Vision API.
Analyzes cropped person images to identify Halloween costumes.
"""

import base64
import os
from io import BytesIO

import cv2
import numpy as np
from openai import OpenAI


class CostumeClassifier:
    """Classifies Halloween costumes using Baseten's vision model."""

    def __init__(self, api_key: str | None = None, model: str = "llama-3.2-11b-vision"):
        """
        Initialize the costume classifier.

        Args:
            api_key: Baseten API key (defaults to BASETEN_API_KEY env var)
            model: Model to use (default: llama-3.2-11b-vision)
        """
        self.api_key = api_key or os.getenv("BASETEN_API_KEY")
        if not self.api_key:
            raise ValueError(
                "BASETEN_API_KEY environment variable not set or no api_key provided"
            )

        self.model = model
        self.client = OpenAI(
            api_key=self.api_key, base_url="https://inference.baseten.co/v1"
        )

    def _encode_image_to_base64(self, image: np.ndarray) -> str:
        """
        Encode OpenCV image (numpy array) to base64 string.

        Args:
            image: OpenCV image (BGR format)

        Returns:
            Base64 encoded image string with data URI prefix
        """
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Encode to JPEG
        success, buffer = cv2.imencode(".jpg", image_rgb)
        if not success:
            raise ValueError("Failed to encode image")

        # Convert to base64
        image_bytes = buffer.tobytes()
        base64_str = base64.b64encode(image_bytes).decode("utf-8")

        return f"data:image/jpeg;base64,{base64_str}"

    def classify_costume(
        self, image: np.ndarray, temperature: float = 0.7, max_tokens: int = 512
    ) -> dict:
        """
        Classify the Halloween costume in the provided image.

        Args:
            image: OpenCV image (numpy array) containing a person
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response

        Returns:
            Dictionary with classification results:
            {
                "costume": str,          # Main costume description
                "confidence": str,       # Confidence level (high/medium/low)
                "details": str,          # Additional costume details
                "full_response": str     # Complete model response
            }
        """
        # Encode image to base64
        image_b64 = self._encode_image_to_base64(image)

        # Create the prompt for costume classification
        prompt = """Analyze this image and identify the Halloween costume the person is wearing.

Provide your response in this exact format:
COSTUME: [name of the costume, e.g., "Witch", "Superhero", "Ghost", "Zombie"]
CONFIDENCE: [high/medium/low]
DETAILS: [brief description of costume elements like colors, accessories, etc.]

If it's not clearly a Halloween costume, say "No costume detected" and explain what the person is wearing."""

        # Make API call
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": image_b64}},
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Extract response text
            full_response = response.choices[0].message.content

            # Parse the structured response
            result = {
                "costume": "Unknown",
                "confidence": "low",
                "details": "",
                "full_response": full_response,
            }

            # Simple parsing of the response
            lines = full_response.split("\n")
            for line in lines:
                if line.startswith("COSTUME:"):
                    result["costume"] = line.replace("COSTUME:", "").strip()
                elif line.startswith("CONFIDENCE:"):
                    result["confidence"] = line.replace("CONFIDENCE:", "").strip()
                elif line.startswith("DETAILS:"):
                    result["details"] = line.replace("DETAILS:", "").strip()

            return result

        except Exception as e:
            return {
                "costume": "Error",
                "confidence": "low",
                "details": f"Classification failed: {e!s}",
                "full_response": "",
            }

    def classify_multiple_people(
        self, frame: np.ndarray, boxes: list[tuple[int, int, int, int]]
    ) -> list[dict]:
        """
        Classify costumes for multiple people detected in a frame.

        Args:
            frame: Full video frame
            boxes: List of bounding boxes [(x1, y1, x2, y2), ...]

        Returns:
            List of classification results for each person
        """
        results = []

        for box in boxes:
            x1, y1, x2, y2 = box
            # Crop person from frame
            person_img = frame[y1:y2, x1:x2]

            # Skip if crop is too small
            if person_img.shape[0] < 50 or person_img.shape[1] < 50:
                results.append(
                    {
                        "costume": "Image too small",
                        "confidence": "low",
                        "details": "Person detection box too small for classification",
                        "full_response": "",
                    }
                )
                continue

            # Classify costume
            result = self.classify_costume(person_img)
            results.append(result)

        return results


if __name__ == "__main__":
    # Simple test
    print("Costume Classifier Module")
    print("=" * 50)

    try:
        classifier = CostumeClassifier()
        print(f"✅ Initialized with model: {classifier.model}")
        print("Ready to classify costumes!")
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("Please set BASETEN_API_KEY in your .env file")
