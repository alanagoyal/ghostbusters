"""Offline local vision adapter. Model loading is confined to the job worker."""

import io
import json
import math
from pathlib import Path

MODEL_ID = "mlx-community/Qwen3-VL-4B-Instruct-4bit"
MODEL_REVISION = "2fd8dacbdb8f1e54b8c005f081ec5bf79c56376b"
PROMPT = (
    "Describe the visible Halloween costume, including masks, character hats or "
    "inflatable suits. If this is a real animal or object without a costumed "
    'person, say "No costume". If ordinary clothing, say "No costume". If '
    'unclear, say "Unknown". Do not identify the person. Return ONLY a JSON '
    "object with keys costume (short name), description (one factual sentence), "
    "confidence (number 0 to 1)."
)


def parse_result(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("invalid model result")
    for key, limit in [("costume", 100), ("description", 600)]:
        if not isinstance(value.get(key), str) or not 0 < len(value[key]) <= limit:
            raise ValueError("invalid model text")
    confidence = value.get("confidence")
    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, (float, int))
        or not math.isfinite(confidence)
        or not 0 <= confidence <= 1
    ):
        raise ValueError("invalid model confidence")
    return value


class LocalVision:
    def __init__(self, path):
        from mlx_vlm import load
        from mlx_vlm.utils import load_config

        self.path = str(Path(path).resolve())
        self.model, self.processor = load(self.path)
        self.config = load_config(self.path)

    def classify(self, image_bytes):
        from mlx_vlm import generate
        from mlx_vlm.prompt_utils import apply_chat_template
        from PIL import Image

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image.thumbnail((640, 640))
        prompt = apply_chat_template(self.processor, self.config, PROMPT, num_images=1)
        result = generate(
            self.model,
            self.processor,
            prompt,
            [image],
            max_tokens=180,
            temperature=0.0,
            verbose=False,
        )
        return parse_result(result.text)
