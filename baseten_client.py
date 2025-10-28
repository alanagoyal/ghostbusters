#!/usr/bin/env python3
"""
Baseten API client for costume classification using vision models.
Uses Llama 3.2 90B Vision Instruct with structured outputs.
"""

import base64
import os
from typing import Optional, Tuple

from openai import OpenAI


class CostumeClassification:
    """Structured output schema for costume classification"""

    def __init__(self, label: str, confidence: float, description: str):
        self.label = label
        self.confidence = confidence
        self.description = description


class BasetenClient:
    """Client for Baseten vision model API using OpenAI-compatible interface"""

    def __init__(self):
        """
        Initialize Baseten client with API key and model configuration.

        Raises:
            ValueError: If BASETEN_API_KEY is not set
        """
        self.api_key = os.getenv("BASETEN_API_KEY")
        if not self.api_key:
            raise ValueError("BASETEN_API_KEY environment variable not set")

        # Initialize OpenAI client with Baseten base URL
        self.client = OpenAI(
            base_url="https://inference.baseten.co/v1", api_key=self.api_key
        )

        # Model configuration
        self.model = "meta-llama/Llama-3.2-90B-Vision-Instruct"
        self.temperature = 0.7  # Slightly creative for varied descriptions
        self.max_tokens = 100  # Short costume descriptions

    def classify_costume(
        self, image_bytes: bytes, custom_prompt: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[float], Optional[str]]:
        """
        Classify a Halloween costume from an image using Llama 3.2 Vision.

        Args:
            image_bytes: Image data as bytes (JPEG/PNG format)
            custom_prompt: Optional custom prompt (uses default if not provided)

        Returns:
            Tuple of (classification, confidence, description) where:
            - classification: Short costume type (e.g., "witch", "skeleton")
            - confidence: Confidence score (0.0-1.0)
            - description: Detailed description (e.g., "witch with purple hat and broom")

        Example:
            >>> client = BasetenClient()
            >>> with open("costume.jpg", "rb") as f:
            ...     image_bytes = f.read()
            >>> classification, confidence, desc = client.classify_costume(image_bytes)
            >>> print(f"{classification} ({confidence:.2f}): {desc}")
            witch (0.95): witch with purple hat and broom
        """
        try:
            # Encode image to base64
            img_base64 = base64.b64encode(image_bytes).decode("utf-8")
            data_uri = f"data:image/jpeg;base64,{img_base64}"

            # Default prompt optimized for Halloween costume classification
            prompt = custom_prompt or (
                "Analyze this Halloween costume and provide:\n"
                "1. A short classification (1-3 words, e.g., 'witch', 'skeleton', 'superhero')\n"
                "2. A confidence score between 0.0 and 1.0\n"
                "3. A detailed description (one sentence)\n\n"
                "Respond ONLY with valid JSON in this exact format:\n"
                '{"classification": "costume_type", "confidence": 0.95, "description": "detailed description"}\n\n'
                "If you cannot identify a costume, use classification='person' and lower confidence."
            )

            # Call Baseten API with vision model
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": data_uri}},
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"},  # Enable structured outputs
            )

            # Extract response
            result_text = response.choices[0].message.content
            if not result_text:
                return None, None, None

            # Parse JSON response
            import json

            result = json.loads(result_text)

            classification = result.get("classification", "unknown")
            confidence = float(result.get("confidence", 0.0))
            description = result.get("description", "")

            return classification, confidence, description

        except Exception as e:
            print(f"⚠️  Baseten API error: {e}")
            return None, None, None

    def test_connection(self) -> bool:
        """
        Test connection to Baseten API.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Simple test with a minimal request
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Test connection"}],
                max_tokens=5,
            )
            return bool(response.choices)
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
