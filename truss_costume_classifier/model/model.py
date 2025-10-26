"""
Costume Classification Model using Qwen2-VL-7B-Instruct

This model takes cropped person images and returns Halloween costume descriptions.
It's optimized for the Halloween doorstep costume classifier project.

Input format:
{
    "image": "base64_encoded_image_string",  # Can have data:image/png;base64, prefix or not
    "prompt": "What Halloween costume is this person wearing?",  # Optional, will use default if not provided
    "max_tokens": 256,  # Optional, default 256
    "temperature": 0.3  # Optional, default 0.3
}

Output format:
{
    "description": "witch with purple hat and broom",
    "confidence": 0.89  # Note: Qwen models don't provide confidence scores, so this will be null
}
"""

import base64
import os
import tempfile
from io import BytesIO
from typing import Dict, Any, Optional

from PIL import Image
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
import torch

# Base64 image format prefix
BASE64_PREAMBLE = "data:image/png;base64,"

# Default system prompt for costume classification
DEFAULT_SYSTEM_PROMPT = """You are a Halloween costume classifier. Describe the person's costume in one short, specific phrase (e.g., 'witch with purple hat and broom', 'skeleton with glowing bones', 'inflatable T-Rex'). Focus on distinctive details and colors. Be concise and descriptive."""

DEFAULT_USER_PROMPT = "What Halloween costume is this person wearing? Provide a brief, specific description."


class Model:
    """
    Truss model class for costume classification using Qwen2-VL-7B-Instruct.

    This follows the standard Truss pattern:
    - __init__: Initialize model variables
    - load: Load the model into memory
    - predict: Run inference on input data
    """

    def __init__(self, **kwargs):
        """Initialize model variables."""
        self.model = None
        self.processor = None
        self.device = None

    def load(self):
        """
        Load the Qwen2-VL model and processor into memory.
        This runs once when the model container starts.
        """
        print("Loading Qwen2-VL-7B-Instruct model...")

        # Determine device
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")

        # Load processor
        self.processor = AutoProcessor.from_pretrained(
            "Qwen/Qwen2-VL-7B-Instruct",
            trust_remote_code=True
        )

        # Load model with automatic device mapping
        self.model = Qwen2VLForConditionalGeneration.from_pretrained(
            "Qwen/Qwen2-VL-7B-Instruct",
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto",
            trust_remote_code=True
        )

        print("Model loaded successfully!")

    def b64_to_pil(self, b64_str: str) -> Image.Image:
        """
        Convert base64 string to PIL Image.

        Args:
            b64_str: Base64 encoded image string (with or without prefix)

        Returns:
            PIL Image object
        """
        # Remove base64 prefix if present
        if b64_str.startswith(BASE64_PREAMBLE):
            b64_str = b64_str.replace(BASE64_PREAMBLE, "")
        elif b64_str.startswith("data:image/jpeg;base64,"):
            b64_str = b64_str.replace("data:image/jpeg;base64,", "")
        elif b64_str.startswith("data:image/jpg;base64,"):
            b64_str = b64_str.replace("data:image/jpg;base64,", "")

        return Image.open(BytesIO(base64.b64decode(b64_str)))

    def predict(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run costume classification inference.

        Args:
            request: Dictionary containing:
                - image: Base64 encoded image or URL
                - prompt: Optional custom prompt (default: costume description request)
                - max_tokens: Optional max tokens to generate (default: 256)
                - temperature: Optional temperature (default: 0.3)

        Returns:
            Dictionary containing:
                - description: Costume description string
                - confidence: Always null (Qwen doesn't provide confidence scores)
        """
        # Extract parameters
        image_data = request.get("image")
        user_prompt = request.get("prompt", DEFAULT_USER_PROMPT)
        max_tokens = request.get("max_tokens", 256)
        temperature = request.get("temperature", 0.3)

        if not image_data:
            return {
                "error": "No image provided",
                "description": None,
                "confidence": None
            }

        # Handle image input
        temp_file_path = None
        try:
            # Check if image is a URL or base64
            if image_data.startswith("http://") or image_data.startswith("https://"):
                # URL - Qwen2-VL can handle URLs directly
                image_path = image_data
            else:
                # Base64 - convert to image file
                image = self.b64_to_pil(image_data)

                # Save to temporary file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                image.save(temp_file.name, format="JPEG")
                temp_file.close()
                image_path = temp_file.name
                temp_file_path = temp_file.name

            # Construct messages in Qwen2-VL format
            messages = [
                {
                    "role": "system",
                    "content": DEFAULT_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "image": image_path
                        },
                        {
                            "type": "text",
                            "text": user_prompt
                        }
                    ]
                }
            ]

            # Apply chat template
            text = self.processor.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

            # Process vision info
            image_inputs, video_inputs = process_vision_info(messages)

            # Prepare inputs
            inputs = self.processor(
                text=[text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt"
            )
            inputs = inputs.to(self.device)

            # Generate response
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=temperature > 0
                )

            # Trim generated tokens to remove input
            generated_ids_trimmed = [
                out_ids[len(in_ids):]
                for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]

            # Decode output
            description = self.processor.batch_decode(
                generated_ids_trimmed,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False
            )[0]

            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)

            return {
                "description": description.strip(),
                "confidence": None  # Qwen doesn't provide confidence scores
            }

        except Exception as e:
            # Clean up temporary file on error
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)

            return {
                "error": str(e),
                "description": None,
                "confidence": None
            }
