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

from baseten_client import BasetenClient
from supabase_client import SupabaseClient

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
print("🤖 Loading YOLOv8n model...")
model = YOLO("yolov8n.pt")  # Will download on first run (~6MB)
print("✅ Model loaded!")

# Initialize Supabase client (optional - graceful degradation if not configured)
supabase_client = None
try:
    supabase_client = SupabaseClient()
    print(f"✅ Connected to Supabase (Device: {supabase_client.device_id})")
except Exception as e:
    print(f"⚠️  Supabase not configured: {e}")
    print("   Detections will only be saved locally")

# Initialize Baseten client for costume classification (optional)
baseten_client = None
try:
    baseten_client = BasetenClient()
    print(f"✅ Connected to Baseten (Model: {baseten_client.model})")
except Exception as e:
    print(f"⚠️  Baseten not configured: {e}")
    print("   Costume classification will be skipped")

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

        # Process every 30 frames (~1 per second at 30fps)
        if frame_count % 30 != 0:
            continue

        # Run YOLO detection
        results = model(frame, verbose=False)

        # Check for person detections (class 0 in COCO dataset)
        people_detected = False
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Class 0 is 'person' in COCO dataset
                if int(box.cls[0]) == 0:
                    people_detected = True
                    confidence = float(box.conf[0])

                    # Only show high-confidence detections
                    if confidence > 0.5:
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

            # Avoid duplicate detections within 2 seconds
            if current_time - last_detection_time > 2:
                detection_count += 1
                detection_timestamp = datetime.now()
                timestamp_str = detection_timestamp.strftime("%Y%m%d_%H%M%S")
                filename = f"detection_{timestamp_str}.jpg"

                # Save frame locally
                cv2.imwrite(filename, frame)

                # Collect ALL person detections (not just the highest confidence)
                detected_people = []
                for result in results:
                    boxes = result.boxes
                    for box in boxes:
                        if int(box.cls[0]) == 0:  # person class
                            conf = float(box.conf[0])
                            if conf > 0.5:
                                x1, y1, x2, y2 = map(int, box.xyxy[0])
                                detected_people.append({
                                    "confidence": conf,
                                    "bounding_box": {
                                        "x1": x1,
                                        "y1": y1,
                                        "x2": x2,
                                        "y2": y2,
                                    }
                                })

                num_people = len(detected_people)
                print(f"👤 {num_people} person(s) detected! (Detection #{detection_count})")
                print(f"   Saved locally: {filename}")

                # Process each detected person separately
                for person_idx, person in enumerate(detected_people, start=1):
                    person_conf = person["confidence"]
                    person_box = person["bounding_box"]

                    if num_people > 1:
                        print(f"   Processing person {person_idx}/{num_people} (confidence: {person_conf:.2f})")

                    # Classify costume using Baseten if configured
                    costume_classification = None
                    costume_confidence = None
                    costume_description = None

                    if baseten_client:
                        try:
                            print(f"   🎭 Classifying costume...")
                            # Extract person crop from frame
                            x1, y1, x2, y2 = (
                                person_box["x1"],
                                person_box["y1"],
                                person_box["x2"],
                                person_box["y2"],
                            )
                            person_crop = frame[y1:y2, x1:x2]

                            # Encode image to bytes
                            _, buffer = cv2.imencode(".jpg", person_crop)
                            image_bytes = buffer.tobytes()

                            # Classify costume
                            (
                                costume_classification,
                                costume_confidence,
                                costume_description,
                            ) = baseten_client.classify_costume(image_bytes)

                            if costume_classification:
                                print(
                                    f"   👗 Costume: {costume_classification} ({costume_confidence:.2f})"
                                )
                                print(f"      {costume_description}")
                            else:
                                print("   ⚠️  Could not classify costume")
                        except Exception as e:
                            print(f"   ⚠️  Costume classification failed: {e}")

                    # Upload to Supabase if configured
                    if supabase_client:
                        try:
                            supabase_client.save_detection(
                                image_path=filename,
                                timestamp=detection_timestamp,
                                confidence=person_conf,
                                bounding_box=person_box,
                                costume_classification=costume_classification,
                                costume_description=costume_description,
                                costume_confidence=costume_confidence,
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
