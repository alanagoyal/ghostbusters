#!/usr/bin/env python3
"""
Person detection script using YOLOv8n on DoorBird RTSP stream.
Detects people in real-time and saves frames with bounding boxes.
Uploads detections to Supabase for dashboard display.
"""

import os
import time
from datetime import datetime

import cv2
from dotenv import load_dotenv
from ultralytics import YOLO

from ..config import (
    CONFIDENCE_THRESHOLD,
    DUPLICATE_DETECTION_TIMEOUT_SECONDS,
    FRAME_SKIP_INTERVAL,
    PERSON_CLASS_ID,
    YOLO_MODEL,
)
from ..storage.supabase_client import SupabaseClient

# Load environment variables
load_dotenv()

# DoorBird connection details
DOORBIRD_USER = os.getenv("DOORBIRD_USERNAME")
DOORBIRD_PASSWORD = os.getenv("DOORBIRD_PASSWORD")
DOORBIRD_IP = os.getenv("DOORBIRD_IP")

# Check required environment variables
if not all([DOORBIRD_USER, DOORBIRD_PASSWORD, DOORBIRD_IP]):
    print("❌ ERROR: Missing required environment variables")
    print("Please check your .env file")
    exit(1)

# Construct RTSP URL
rtsp_url = f"rtsp://{DOORBIRD_USER}:{DOORBIRD_PASSWORD}@{DOORBIRD_IP}/mpeg/media.amp"

print("🚀 Starting person detection system...")
print(f"📹 Connecting to DoorBird at {DOORBIRD_IP}")

# Load YOLOv8n model (smallest/fastest)
print(f"🤖 Loading {YOLO_MODEL} model...")
model = YOLO(YOLO_MODEL)  # Will download on first run (~6MB)
print("✅ Model loaded!")

# Initialize Supabase client (optional - graceful degradation if not configured)
supabase_client = None
try:
    supabase_client = SupabaseClient()
    print(f"✅ Connected to Supabase (Device: {supabase_client.device_id})")
except Exception as e:
    print(f"⚠️  Supabase not configured: {e}")
    print("   Detections will only be saved locally")

# Open RTSP stream
cap = cv2.VideoCapture(rtsp_url)

if not cap.isOpened():
    print("❌ ERROR: Could not connect to DoorBird RTSP stream")
    exit(1)

print("✅ Connected to RTSP stream!")
print()
print("👁️  Watching for people...")
print("Press Ctrl+C to stop")
print()

frame_count = 0
detection_count = 0
last_detection_time = 0

try:
    while True:
        # Read frame from stream
        ret, frame = cap.read()

        if not ret:
            print("⚠️  Failed to read frame, reconnecting...")
            time.sleep(1)
            continue

        frame_count += 1

        # Process every N frames (configured in config.py)
        if frame_count % FRAME_SKIP_INTERVAL != 0:
            continue

        # Run YOLO detection
        results = model(frame, verbose=False)

        # Check for person detections (class 0 in COCO dataset)
        people_detected = False
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Class 0 is 'person' in COCO dataset
                if int(box.cls[0]) == PERSON_CLASS_ID:
                    people_detected = True
                    confidence = float(box.conf[0])

                    # Only show high-confidence detections
                    if confidence > CONFIDENCE_THRESHOLD:
                        # Get bounding box coordinates
                        x1, y1, x2, y2 = map(int, box.xyxy[0])

                        # Draw bounding box
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                        # Draw label
                        label = f"Person {confidence:.2f}"
                        cv2.putText(
                            frame,
                            label,
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (0, 255, 0),
                            2,
                        )

        # If person detected, save frame and upload to Supabase
        if people_detected:
            current_time = time.time()

            # Avoid duplicate detections within configured timeout
            if current_time - last_detection_time > DUPLICATE_DETECTION_TIMEOUT_SECONDS:
                detection_count += 1
                detection_timestamp = datetime.now()
                timestamp_str = detection_timestamp.strftime("%Y%m%d_%H%M%S")
                filename = f"detection_{timestamp_str}.jpg"

                # Save frame locally
                cv2.imwrite(filename, frame)

                print(f"👤 Person detected! (#{detection_count})")
                print(f"   Saved locally: {filename}")

                # Get bounding box from first detection for database
                # (if multiple people, we'll use the first one for now)
                first_box = None
                max_confidence = 0.0
                for result in results:
                    boxes = result.boxes
                    for box in boxes:
                        if int(box.cls[0]) == PERSON_CLASS_ID:  # person class
                            conf = float(box.conf[0])
                            if conf > CONFIDENCE_THRESHOLD and conf > max_confidence:
                                max_confidence = conf
                                x1, y1, x2, y2 = map(int, box.xyxy[0])
                                first_box = {
                                    "x1": x1,
                                    "y1": y1,
                                    "x2": x2,
                                    "y2": y2,
                                }

                # Upload to Supabase if configured
                if supabase_client and first_box:
                    try:
                        supabase_client.save_detection(
                            image_path=filename,
                            timestamp=detection_timestamp,
                            confidence=max_confidence,
                            bounding_box=first_box,
                        )
                    except Exception as e:
                        print(f"   ⚠️  Supabase upload failed: {e}")

                print()
                last_detection_time = current_time

except KeyboardInterrupt:
    print()
    print("🛑 Stopping person detection...")
    print(f"📊 Total detections: {detection_count}")

finally:
    cap.release()
    print("✅ Cleanup complete!")
