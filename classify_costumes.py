#!/usr/bin/env python3
"""
Real-time Halloween costume classification system.
Combines YOLOv8 person detection with Qwen-VL costume classification via Baseten.
"""

import os
import sys
import time
from datetime import datetime

import cv2
from baseten_client import BasetenClient
from dotenv import load_dotenv
from ultralytics import YOLO

# Load environment variables
load_dotenv()

# DoorBird connection details
DOORBIRD_USER = os.getenv("DOORBIRD_USERNAME")
DOORBIRD_PASSWORD = os.getenv("DOORBIRD_PASSWORD")
DOORBIRD_IP = os.getenv("DOORBIRD_IP")

# Check required environment variables
if not all([DOORBIRD_USER, DOORBIRD_PASSWORD, DOORBIRD_IP]):
    print("❌ ERROR: Missing DoorBird environment variables")
    print("Please check your .env file")
    sys.exit(1)

# Configuration
PERSON_CONFIDENCE_THRESHOLD = 0.5  # Minimum confidence for person detection
DETECTION_COOLDOWN = 5  # Seconds between classifications
FRAME_SKIP = 30  # Process every Nth frame (~1 per second at 30fps)
SAVE_DETECTIONS = True  # Save images with costume classifications

# Construct RTSP URL
rtsp_url = f"rtsp://{DOORBIRD_USER}:{DOORBIRD_PASSWORD}@{DOORBIRD_IP}/mpeg/media.amp"

print("🎃 Halloween Costume Classifier Starting...")
print("=" * 60)
print()
print(f"📹 Connecting to DoorBird at {DOORBIRD_IP}")

# Initialize Baseten client
print("🤖 Initializing Baseten Qwen-VL model...")
try:
    baseten_client = BasetenClient()
    print("✅ Baseten client ready!")
except ValueError as e:
    print(f"❌ Error: {e}")
    print()
    print("Please ensure:")
    print("  1. You've deployed Qwen-VL to Baseten")
    print("  2. BASETEN_MODEL_URL is set in .env")
    print("  3. BASETEN_API_KEY is set in .env")
    sys.exit(1)

# Load YOLOv8n model for person detection
print("🎯 Loading YOLOv8n person detector...")
model = YOLO("yolov8n.pt")
print("✅ Person detector ready!")

# Open RTSP stream
cap = cv2.VideoCapture(rtsp_url)

if not cap.isOpened():
    print("❌ ERROR: Could not connect to DoorBird RTSP stream")
    sys.exit(1)

print("✅ Connected to RTSP stream!")
print()
print("👻 Watching for trick-or-treaters...")
print("Press Ctrl+C to stop")
print("=" * 60)
print()

frame_count = 0
classification_count = 0
last_classification_time = 0

try:
    while True:
        # Read frame from stream
        ret, frame = cap.read()

        if not ret:
            print("⚠️  Failed to read frame, reconnecting...")
            time.sleep(1)
            continue

        frame_count += 1

        # Skip frames for performance
        if frame_count % FRAME_SKIP != 0:
            continue

        # Run YOLO person detection
        results = model(frame, verbose=False)

        # Check for person detections
        people_detected = False
        person_boxes = []

        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Class 0 is 'person' in COCO dataset
                if int(box.cls[0]) == 0:
                    confidence = float(box.conf[0])

                    if confidence > PERSON_CONFIDENCE_THRESHOLD:
                        people_detected = True
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        person_boxes.append((x1, y1, x2, y2, confidence))

        # If person detected, classify their costume
        if people_detected:
            current_time = time.time()

            # Cooldown to avoid repeated classifications
            if current_time - last_classification_time > DETECTION_COOLDOWN:
                classification_count += 1
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                print(f"👤 Person detected! Classifying costume...")

                # Classify costume using Baseten
                try:
                    costume = baseten_client.classify_costume(frame)

                    print()
                    print("🎭 COSTUME DETECTED")
                    print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
                    print(f"   Classification #{classification_count}")
                    print("   " + "-" * 50)
                    print(f"   {costume}")
                    print("   " + "-" * 50)
                    print()

                    # Draw bounding boxes and costume label
                    for x1, y1, x2, y2, conf in person_boxes:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                        # Draw person confidence
                        label = f"Person {conf:.2f}"
                        cv2.putText(
                            frame,
                            label,
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (0, 255, 0),
                            2,
                        )

                    # Add costume classification to image
                    # Create background for text
                    costume_text = costume[:60] + "..." if len(costume) > 60 else costume
                    text_size = cv2.getTextSize(
                        costume_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2
                    )[0]
                    cv2.rectangle(
                        frame,
                        (10, 10),
                        (text_size[0] + 20, text_size[1] + 20),
                        (0, 0, 0),
                        -1,
                    )
                    cv2.putText(
                        frame,
                        costume_text,
                        (15, text_size[1] + 15),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 255),
                        2,
                    )

                    # Save classified image
                    if SAVE_DETECTIONS:
                        filename = f"costume_{timestamp}.jpg"
                        cv2.imwrite(filename, frame)
                        print(f"   💾 Saved: {filename}")
                        print()

                except Exception as e:
                    print(f"   ⚠️  Classification error: {e}")
                    print()

                last_classification_time = current_time

except KeyboardInterrupt:
    print()
    print("🛑 Stopping costume classifier...")
    print()
    print("📊 Session Summary")
    print("=" * 60)
    print(f"   Total costumes classified: {classification_count}")
    print(f"   Total frames processed: {frame_count}")
    print("=" * 60)

finally:
    cap.release()
    print()
    print("✅ Cleanup complete!")
    print("🎃 Happy Halloween! 👻")
