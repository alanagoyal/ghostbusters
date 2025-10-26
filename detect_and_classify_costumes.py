#!/usr/bin/env python3
"""
Person detection + costume classification using YOLOv8 and Baseten Llama 3.2 Vision.
Detects people in DoorBird RTSP stream and classifies their Halloween costumes.
"""

import os
import time
from datetime import datetime

import cv2
from dotenv import load_dotenv
from ultralytics import YOLO

from costume_classifier import CostumeClassifier

# Load environment variables
load_dotenv()

# DoorBird connection details
DOORBIRD_USER = os.getenv("DOORBIRD_USERNAME")
DOORBIRD_PASSWORD = os.getenv("DOORBIRD_PASSWORD")
DOORBIRD_IP = os.getenv("DOORBIRD_IP")
BASETEN_API_KEY = os.getenv("BASETEN_API_KEY")

# Check required environment variables
if not all([DOORBIRD_USER, DOORBIRD_PASSWORD, DOORBIRD_IP]):
    print("❌ ERROR: Missing required DoorBird environment variables")
    print("Please check your .env file")
    exit(1)

if not BASETEN_API_KEY:
    print("⚠️  WARNING: BASETEN_API_KEY not set")
    print("Costume classification will be disabled")
    print("To enable: add BASETEN_API_KEY to your .env file")
    print()
    use_classifier = False
else:
    use_classifier = True

# Construct RTSP URL
rtsp_url = f"rtsp://{DOORBIRD_USER}:{DOORBIRD_PASSWORD}@{DOORBIRD_IP}/mpeg/media.amp"

print("🎃 Starting Halloween Costume Detection System")
print("=" * 60)
print(f"📹 Connecting to DoorBird at {DOORBIRD_IP}")

# Load YOLOv8n model (smallest/fastest)
print("🤖 Loading YOLOv8n model...")
model = YOLO("yolov8n.pt")  # Will download on first run (~6MB)
print("✅ YOLOv8 model loaded!")

# Initialize costume classifier
classifier = None
if use_classifier:
    try:
        print("🎭 Initializing Baseten costume classifier...")
        classifier = CostumeClassifier()
        print("✅ Costume classifier ready!")
    except Exception as e:
        print(f"⚠️  Could not initialize classifier: {e}")
        print("Continuing with person detection only...")
        use_classifier = False

# Open RTSP stream
cap = cv2.VideoCapture(rtsp_url)

if not cap.isOpened():
    print("❌ ERROR: Could not connect to DoorBird RTSP stream")
    exit(1)

print("✅ Connected to RTSP stream!")
print()
print("👁️  Watching for trick-or-treaters...")
print("Press Ctrl+C to stop")
print("=" * 60)
print()

frame_count = 0
detection_count = 0
last_detection_time = 0
DETECTION_COOLDOWN = 5  # seconds between classifications (API rate limiting)

try:
    while True:
        # Read frame from stream
        ret, frame = cap.read()

        if not ret:
            print("⚠️  Failed to read frame, reconnecting...")
            time.sleep(1)
            continue

        frame_count += 1

        # Process every 30 frames (~1 per second at 30fps)
        if frame_count % 30 != 0:
            continue

        # Run YOLO detection
        results = model(frame, verbose=False)

        # Collect person detections
        person_boxes = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Class 0 is 'person' in COCO dataset
                if int(box.cls[0]) == 0:
                    confidence = float(box.conf[0])

                    # Only process high-confidence detections
                    if confidence > 0.5:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        person_boxes.append((x1, y1, x2, y2, confidence))

        # If people detected and cooldown elapsed, classify costumes
        if person_boxes:
            current_time = time.time()

            # Avoid duplicate classifications within cooldown period
            if current_time - last_detection_time > DETECTION_COOLDOWN:
                detection_count += 1
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                print(f"🎃 Detection #{detection_count} - {timestamp}")
                print(f"   Found {len(person_boxes)} person(s)")
                print()

                # Draw boxes and classify costumes
                annotated_frame = frame.copy()

                for idx, (x1, y1, x2, y2, conf) in enumerate(person_boxes, 1):
                    # Draw bounding box
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                    # Classify costume if enabled
                    if use_classifier and classifier:
                        print(f"   👤 Person {idx}: Classifying costume...")

                        person_img = frame[y1:y2, x1:x2]
                        result = classifier.classify_costume(person_img)

                        costume = result["costume"]
                        confidence_level = result["confidence"]
                        details = result["details"]

                        print(f"      🎭 Costume: {costume}")
                        print(f"      📊 Confidence: {confidence_level}")
                        if details:
                            print(f"      ℹ️  Details: {details}")
                        print()

                        # Draw costume label
                        label = f"Person {idx}: {costume}"
                        label_y = y1 - 10 if y1 > 30 else y1 + 20

                        # Draw label background for better visibility
                        (label_w, label_h), _ = cv2.getTextSize(
                            label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
                        )
                        cv2.rectangle(
                            annotated_frame,
                            (x1, label_y - label_h - 5),
                            (x1 + label_w, label_y + 5),
                            (0, 255, 0),
                            -1,
                        )

                        cv2.putText(
                            annotated_frame,
                            label,
                            (x1, label_y),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 0, 0),
                            2,
                        )
                    else:
                        # Just label as person if no classifier
                        label = f"Person {idx} ({conf:.2f})"
                        cv2.putText(
                            annotated_frame,
                            label,
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (0, 255, 0),
                            2,
                        )

                # Save annotated frame
                filename = f"costume_detection_{timestamp}.jpg"
                cv2.imwrite(filename, annotated_frame)
                print(f"   💾 Saved: {filename}")
                print("   " + "=" * 56)
                print()

                last_detection_time = current_time

except KeyboardInterrupt:
    print()
    print("🛑 Stopping costume detection system...")
    print(f"📊 Total detections: {detection_count}")

finally:
    cap.release()
    print("✅ Cleanup complete!")
    print("Happy Halloween! 🎃👻")
