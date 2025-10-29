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
                detection_timestamp = datetime.now()
                timestamp_str = detection_timestamp.strftime("%Y%m%d_%H%M%S")

                # Save full frame locally with all people
                full_frame_filename = f"detection_{timestamp_str}.jpg"
                cv2.imwrite(full_frame_filename, frame)

                # Collect all people detected in this frame
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
                detection_count += num_people

                if num_people == 1:
                    print(f"👤 Person detected! (#{detection_count})")
                else:
                    print(f"👥 {num_people} people detected! (Total count: #{detection_count})")
                print(f"   Saved full frame: {full_frame_filename}")

                # Upload each person as a separate database entry
                if supabase_client and detected_people:
                    for idx, person in enumerate(detected_people, 1):
                        try:
                            # For multiple people, create person-specific filename
                            if num_people > 1:
                                person_filename = f"detection_{timestamp_str}_person{idx}.jpg"
                                # Crop and save individual person image
                                bbox = person["bounding_box"]
                                person_img = frame[bbox["y1"]:bbox["y2"], bbox["x1"]:bbox["x2"]]
                                cv2.imwrite(person_filename, person_img)
                                print(f"   Saved person {idx}/{num_people}: {person_filename}")
                            else:
                                # For single person, use full frame
                                person_filename = full_frame_filename

                            supabase_client.save_detection(
                                image_path=person_filename,
                                timestamp=detection_timestamp,
                                confidence=person["confidence"],
                                bounding_box=person["bounding_box"],
                            )
                        except Exception as e:
                            print(f"   ⚠️  Supabase upload failed for person {idx}: {e}")

                print()
                last_detection_time = current_time

except KeyboardInterrupt:
    print()
    print("🛑 Stopping person detection...")
    print(f"📊 Total detections: {detection_count}")

finally:
    cap.release()
    print("✅ Cleanup complete!")
