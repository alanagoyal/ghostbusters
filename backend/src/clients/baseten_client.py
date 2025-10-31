#!/usr/bin/env python3
"""
Baseten API client for costume classification using vision models.
Uses Gemma vision model with structured outputs.
"""

import base64
import json
import os
from typing import Optional, Tuple

import requests

# Allowed costume categories for classification
ALLOWED_CATEGORIES = [
    "witch",
    "vampire",
    "zombie",
    "skeleton",
    "ghost",
    "superhero",
    "princess",
    "pirate",
    "ninja",
    "clown",
    "monster",
    "character",  # For recognizable characters (Spiderman, Elsa, etc.)
    "animal",     # For animal costumes (tiger, cat, etc.)
    "person",     # No costume visible
    "other",      # Doesn't fit any category
]


class BasetenClient:
    """Client for Baseten vision model API"""

    def __init__(self):
        """
        Initialize Baseten client with API key and model URL.

        Raises:
            ValueError: If BASETEN_API_KEY or BASETEN_MODEL_URL is not set
        """
        self.api_key = os.getenv("BASETEN_API_KEY")
        self.model_url = os.getenv("BASETEN_MODEL_URL")

        if not self.api_key:
            raise ValueError("BASETEN_API_KEY environment variable not set")
        if not self.model_url:
            raise ValueError("BASETEN_MODEL_URL environment variable not set")

        # Build session so connections can be re-used across requests
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Api-Key {self.api_key}"})

        # Model configuration
        self.model = "gemma"
        self.temperature = 0.5
        self.max_tokens = 512

    def classify_costume(
        self, image_bytes: bytes, custom_prompt: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[float], Optional[str]]:
        """
        Classify a Halloween costume from an image using Gemma vision model.

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
                "Analyze this Halloween costume and respond with ONLY a JSON object in this exact format:\n"
                '{"classification": "costume_type", "confidence": 0.95, "description": "costume label"}\n\n'
                "Preferred categories:\n"
                "- witch, vampire, zombie, skeleton, ghost\n"
                "- superhero, princess, pirate, ninja, clown, monster\n"
                "- character (for recognizable characters like Spiderman, Elsa, Mickey Mouse)\n"
                "- animal (for animal costumes like tiger, cat, dinosaur)\n"
                "- person (if no costume visible)\n"
                "- other (if costume doesn't fit above categories)\n\n"
                "Rules:\n"
                "- classification: Try to use one of the preferred categories above, or be specific (e.g., 'Spiderman', 'tiger')\n"
                "- confidence: Your confidence score between 0.0 and 1.0\n"
                "- description: A short description focused on the costume itself (e.g., 'An astronaut with a space helmet', 'A pop-star holding a microphone', 'A witch with a pointed hat'). Describe the costume elements directly, not the person or their clothing. If no costume is visible, use 'No costume'.\n"
                "- Output ONLY the JSON object, nothing else"
            )

            # Call Baseten API with Gemma vision model
            response = self.session.post(
                self.model_url,
                json={
                    "model": self.model,
                    "stream": False,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": data_uri}},
                            ],
                        }
                    ],
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                },
            )

            # Check for HTTP errors
            response.raise_for_status()

            # Parse response
            result = response.json()

            # Extract content from response
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0].get("message", {}).get("content", "")
            else:
                print(f"⚠️  Unexpected response format: {result}")
                return None, None, None

            if not content:
                return None, None, None

            # Clean up content - remove markdown code blocks and model artifacts
            content = content.strip()

            # Remove markdown code fences
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]

            # Remove trailing artifacts like ```<end_of_turn>, ``` etc.
            # Split on common delimiters and take the first part
            for delimiter in ["```", "<end_of_turn>", "\n```", "```\n"]:
                if delimiter in content:
                    content = content.split(delimiter)[0]

            content = content.strip()

            # Parse JSON response
            parsed_result = json.loads(content)

            classification = parsed_result.get("classification", "unknown")
            confidence = float(parsed_result.get("confidence", 0.0))
            description = parsed_result.get("description", "")

            return classification, confidence, description

        except requests.exceptions.RequestException as e:
            print(f"⚠️  Baseten API request error: {e}")
            return None, None, None
        except json.JSONDecodeError as e:
            print(f"⚠️  Failed to parse JSON response: {e}")
            print(f"   Raw content: {content if 'content' in locals() else 'N/A'}")
            return None, None, None
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
            response = self.session.post(
                self.model_url,
                json={
                    "model": self.model,
                    "stream": False,
                    "messages": [
                        {"role": "user", "content": [{"type": "text", "text": "Hello"}]}
                    ],
                    "max_tokens": 10,
                },
            )
            response.raise_for_status()
            result = response.json()
            return "choices" in result
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
