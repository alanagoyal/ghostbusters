#!/usr/bin/env python3
"""
Full costume detection and classification pipeline.
Combines YOLOv8 person detection with OpenAI Vision costume classification.
"""

import os
import time
from datetime import datetime

import cv2
from dotenv import load_dotenv
from ultralytics import YOLO

from classify_costume import CostumeClassifier

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
    exit(1)

# Check OpenAI API key
if not os.getenv("OPENAI_API_KEY"):
    print("❌ ERROR: Missing OPENAI_API_KEY environment variable")
    print("Please add your OpenAI API key to .env file")
    exit(1)

# Construct RTSP URL
rtsp_url = f"rtsp://{DOORBIRD_USER}:{DOORBIRD_PASSWORD}@{DOORBIRD_IP}/mpeg/media.amp"

print("🎃 Halloween Costume Classifier")
print("=" * 50)
print(f"📹 Connecting to DoorBird at {DOORBIRD_IP}")

# Load YOLOv8n model for person detection
print("🤖 Loading YOLOv8n model...")
yolo_model = YOLO("yolov8n.pt")
print("✅ YOLO model loaded!")

# Initialize costume classifier
print("🎨 Initializing OpenAI Vision classifier...")
costume_classifier = CostumeClassifier()
print("✅ Classifier ready!")

# Open RTSP stream
cap = cv2.VideoCapture(rtsp_url)

if not cap.isOpened():
    print("❌ ERROR: Could not connect to DoorBird RTSP stream")
    exit(1)

print("✅ Connected to RTSP stream!")
print()
print("👁️  Watching for trick-or-treaters...")
print("Press Ctrl+C to stop")
print()

frame_count = 0
detection_count = 0
last_detection_time = 0

# Detection settings
DETECTION_INTERVAL = 30  # Process every Nth frame (~1 per second at 30fps)
PERSON_CONFIDENCE_THRESHOLD = 0.5  # Minimum confidence for person detection
COOLDOWN_SECONDS = 3  # Seconds between detections to avoid duplicates

try:
    while True:
        # Read frame from stream
        ret, frame = cap.read()

        if not ret:
            print("⚠️  Failed to read frame, reconnecting...")
            time.sleep(1)
            continue

        frame_count += 1

        # Process every N frames to reduce CPU load
        if frame_count % DETECTION_INTERVAL != 0:
            continue

        # Run YOLO person detection
        results = yolo_model(frame, verbose=False)

        # Process detected people
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Class 0 is 'person' in COCO dataset
                if int(box.cls[0]) == 0:
                    confidence = float(box.conf[0])

                    # Only process high-confidence detections
                    if confidence > PERSON_CONFIDENCE_THRESHOLD:
                        current_time = time.time()

                        # Avoid duplicate detections within cooldown period
                        if current_time - last_detection_time > COOLDOWN_SECONDS:
                            detection_count += 1
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                            # Get bounding box coordinates
                            x1, y1, x2, y2 = map(int, box.xyxy[0])

                            # Crop person from frame
                            person_crop = frame[y1:y2, x1:x2]

                            # Save cropped person image
                            crop_filename = f"person_{timestamp}.jpg"
                            cv2.imwrite(crop_filename, person_crop)

                            print(f"👤 Person detected! (#{detection_count})")
                            print(f"   Confidence: {confidence:.2f}")
                            print(f"   Saved crop: {crop_filename}")

                            # Classify costume using OpenAI Vision
                            print("   🎨 Classifying costume...")
                            classification = costume_classifier.classify(person_crop)

                            print(f"   🎭 Costume: {classification['description']}")
                            print(
                                f"   📊 Classification confidence: {classification['confidence']:.2f}"
                            )

                            # Draw bounding box on full frame
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                            # Draw costume label
                            label = classification["description"]
                            cv2.putText(
                                frame,
                                label,
                                (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.6,
                                (0, 255, 0),
                                2,
                            )

                            # Save annotated full frame
                            frame_filename = f"detection_{timestamp}.jpg"
                            cv2.imwrite(frame_filename, frame)
                            print(f"   Saved annotated frame: {frame_filename}")

                            # TODO: Log to Supabase
                            # Future: Send {description, confidence, timestamp} to Supabase

                            print()

                            last_detection_time = current_time

except KeyboardInterrupt:
    print()
    print("🛑 Stopping costume classifier...")
    print(f"📊 Total detections: {detection_count}")

finally:
    cap.release()
    print("✅ Cleanup complete!")
