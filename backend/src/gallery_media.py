"""Prepare small gallery assets from the already privacy-processed saved scene."""

import base64
import hashlib
from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class GalleryMedia:
    original: bytes
    thumbnail: bytes
    width: int
    height: int
    placeholder: str
    digest: str


def prepare_gallery_media(image: bytes) -> GalleryMedia:
    frame = cv2.imdecode(np.frombuffer(image, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("Invalid saved detection image")
    height, width = frame.shape[:2]

    def webp(size: int, quality: int, longest_side: bool = False) -> bytes:
        scale = min(1.0, size / (max(width, height) if longest_side else width))
        resized = cv2.resize(
            frame,
            (max(1, round(width * scale)), max(1, round(height * scale))),
            interpolation=cv2.INTER_AREA,
        )
        ok, encoded = cv2.imencode(
            ".webp", resized, [cv2.IMWRITE_WEBP_QUALITY, quality]
        )
        if not ok:
            raise ValueError("Could not encode gallery image")
        return encoded.tobytes()

    thumbnail = webp(360, 76)
    # Bound the longest side, including portrait camera scenes.
    placeholder = "data:image/webp;base64," + base64.b64encode(
        webp(10, 20, True)
    ).decode("ascii")
    return GalleryMedia(
        image,
        thumbnail,
        width,
        height,
        placeholder,
        hashlib.sha256(image + thumbnail).hexdigest(),
    )
