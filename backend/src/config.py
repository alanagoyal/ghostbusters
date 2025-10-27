#!/usr/bin/env python3
"""
Configuration constants for the person detection system.
"""

# Detection settings
FRAME_SKIP_INTERVAL = 30  # Process every Nth frame (~1 per second at 30fps)
CONFIDENCE_THRESHOLD = 0.5  # Minimum confidence for person detection (0.0-1.0)
DUPLICATE_DETECTION_TIMEOUT_SECONDS = 2  # Minimum time between detections

# YOLO model
YOLO_MODEL = "yolov8n.pt"  # YOLOv8 nano model (~6MB)
PERSON_CLASS_ID = 0  # COCO dataset class ID for 'person'

# Supabase storage
STORAGE_BUCKET_NAME = "detection-images"

# Device identification
# Uses HOSTNAME environment variable, falls back to DEVICE_ID
DEFAULT_DEVICE_ID = "unknown-device"
