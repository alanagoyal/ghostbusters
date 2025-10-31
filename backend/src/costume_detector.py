#!/usr/bin/env python3
"""
Costume detection module with dual-pass YOLO detection.

This module provides the core detection logic used by both production code
and test scripts. It implements a dual-pass detection strategy:

PASS 1: Detects standard people (YOLO class 0)
PASS 2: Detects potential inflatable costumes (YOLO classes 2, 14, 16, 17)
        and validates them with the Baseten costume classifier

This approach ensures we capture both regular costumes and inflatable/bulky
costumes that YOLO may misclassify as objects (cars, animals, etc.).
"""

import cv2
import numpy as np
from ultralytics import YOLO

from backend.src.clients.baseten_client import BasetenClient

# YOLO COCO classes for dual-pass detection
PERSON_CLASS = 0
INFLATABLE_CLASSES = [2, 14, 16, 17]  # car, bird, dog, cat (common misclassifications for inflatables)


def detect_people_and_costumes(
    frame: np.ndarray,
    model: YOLO,
    baseten_client: BasetenClient,
    confidence_threshold: float = 0.7,
    verbose: bool = False,
) -> list[dict]:
    """
    Detect people and costumes using dual-pass YOLO detection.

    This function implements a two-pass detection strategy:
    1. PASS 1: Detect standard people (YOLO class 0)
    2. PASS 2: Detect potential inflatable costumes (YOLO classes 2, 14, 16, 17)
    3. Validate inflatable detections with Baseten costume classifier
    4. Reject detections that return "No costume" (filters out actual cars/objects)

    Args:
        frame: Input image as numpy array (BGR format from cv2.imread)
        model: YOLOv8 model instance
        baseten_client: Baseten client for costume classification
        confidence_threshold: Minimum confidence for YOLO detections (default: 0.7)
        verbose: Print detailed detection information (default: False)

    Returns:
        List of detection dicts, each containing:
        - confidence: YOLO detection confidence (float)
        - bounding_box: {"x1": int, "y1": int, "x2": int, "y2": int}
        - detection_type: "person" or "inflatable" (str)
        - yolo_class: YOLO class ID (int)
        - yolo_class_name: YOLO class name for inflatable detections (str, optional)
        - costume_classification: Costume type if validated (str, optional)
        - costume_description: Costume description if validated (str, optional)
        - costume_confidence: Classification confidence if validated (float, optional)

    Example:
        >>> model = YOLO("yolov8n.pt")
        >>> baseten_client = BasetenClient()
        >>> frame = cv2.imread("doorbell.jpg")
        >>> detections = detect_people_and_costumes(frame, model, baseten_client)
        >>> print(f"Found {len(detections)} people")
    """
    if verbose:
        print("🔍 Running YOLO dual-pass detection...")

    # Run YOLO detection
    results = model(frame, verbose=False)

    # PASS 1: Collect standard person detections (class 0)
    detected_people = []
    potential_inflatables = []

    for result in results:
        boxes = result.boxes
        for box in boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])

            if conf > confidence_threshold:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                bbox_dict = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}

                if cls == PERSON_CLASS:
                    # Standard person detection
                    detected_people.append({
                        "confidence": conf,
                        "bounding_box": bbox_dict,
                        "detection_type": "person",
                        "yolo_class": cls,
                    })
                elif cls in INFLATABLE_CLASSES:
                    # Potential inflatable costume (needs validation)
                    class_name = model.names[cls]
                    potential_inflatables.append({
                        "confidence": conf,
                        "bounding_box": bbox_dict,
                        "detection_type": "inflatable",
                        "yolo_class": cls,
                        "yolo_class_name": class_name,
                    })

    if verbose:
        print(f"✅ PASS 1: Detected {len(detected_people)} standard person(s)")
        print(f"🎈 PASS 2: Found {len(potential_inflatables)} potential inflatable(s)")

    # PASS 2: Validate potential inflatable costumes with Baseten
    if baseten_client and potential_inflatables:
        if verbose:
            print(f"   Validating {len(potential_inflatables)} potential inflatable costume(s)...")

        for inflatable in potential_inflatables:
            try:
                bbox = inflatable["bounding_box"]
                x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]
                crop = frame[y1:y2, x1:x2]
                _, buffer = cv2.imencode('.jpg', crop)
                image_bytes = buffer.tobytes()

                (
                    costume_classification,
                    costume_confidence,
                    costume_description,
                ) = baseten_client.classify_costume(image_bytes)

                # Only validate if we got a real costume classification
                # Reject if: no classification, or "person" with "No costume"
                is_valid = (
                    costume_classification and
                    not (costume_classification.lower() == "person" and
                         costume_description and "no costume" in costume_description.lower())
                )

                if is_valid:
                    if verbose:
                        print(f"   ✅ Validated inflatable: {costume_classification} (YOLO saw as {inflatable['yolo_class_name']})")
                    inflatable["costume_classification"] = costume_classification
                    inflatable["costume_description"] = costume_description
                    inflatable["costume_confidence"] = costume_confidence
                    detected_people.append(inflatable)
                else:
                    if verbose:
                        print(f"   ❌ Rejected {inflatable['yolo_class_name']} (not a costume)")
            except Exception as e:
                if verbose:
                    print(f"   ⚠️  Validation failed for {inflatable.get('yolo_class_name', 'unknown')}: {e}")

    return detected_people
