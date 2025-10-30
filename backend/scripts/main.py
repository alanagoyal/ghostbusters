#!/usr/bin/env python3
"""
Person detection script using YOLOv8n on DoorBird RTSP stream.
Detects people in real-time and saves frames with bounding boxes.
Uploads detections to Supabase for dashboard display.
"""

import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import cv2
from dotenv import load_dotenv
from ultralytics import YOLO

from backend.src.clients.baseten_client import BasetenClient
from backend.src.clients.supabase_client import SupabaseClient
from backend.src.utils.face_blur import FaceBlurrer

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

# Initialize face blurrer for privacy protection
face_blurrer = FaceBlurrer(blur_strength=51)
print("✅ Face blurrer initialized (privacy protection enabled)")

# Dwell-time and cooldown configuration
DWELL_TIME = int(os.getenv("DWELL_TIME", "10"))  # Seconds person must be present before capture
CAPTURE_COOLDOWN = int(os.getenv("CAPTURE_COOLDOWN", "60"))  # Seconds to wait before next capture
DETECTION_GRACE_PERIOD = int(os.getenv("DETECTION_GRACE_PERIOD", "3"))  # Seconds to allow brief detection gaps
print(f"⏱️  Dwell time: {DWELL_TIME}s, Cooldown: {CAPTURE_COOLDOWN}s, Grace period: {DETECTION_GRACE_PERIOD}s")

# Function to connect/reconnect to RTSP stream
def connect_to_stream(url):
    """Connect to RTSP stream with optimized settings."""
    cap = cv2.VideoCapture(url)
    # Set RTSP transport protocol to TCP (more reliable than UDP)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to minimize delay
    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)  # 10 second connection timeout
    cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 10000)  # 10 second read timeout
    return cap

# Open RTSP stream
cap = connect_to_stream(rtsp_url)

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
last_reconnect_time = time.time()
last_health_check = time.time()
failed_frame_count = 0
start_time = time.time()
RECONNECT_INTERVAL = 3600  # Reconnect every hour to clear memory
HEALTH_CHECK_INTERVAL = 300  # Print health stats every 5 minutes

# Dwell-time tracking state
person_present = False
first_detection_time = None
last_capture_time = 0
in_cooldown = False
last_seen_time = None  # Track when person was last detected (for grace period)

try:
    while True:
        current_time = time.time()

        # Health check - print stats every 5 minutes
        if current_time - last_health_check > HEALTH_CHECK_INTERVAL:
            uptime_minutes = (current_time - start_time) / 60
            print(f"\n📊 Health Check (Uptime: {uptime_minutes:.1f} min)")
            print(f"   Frames processed: {frame_count}")
            print(f"   Detections: {detection_count}")
            print(f"   Failed frames: {failed_frame_count}")
            print()
            last_health_check = current_time

        # Periodic reconnection to prevent memory leaks
        if current_time - last_reconnect_time > RECONNECT_INTERVAL:
            print("🔄 Performing periodic reconnection (memory management)...")
            cap.release()
            time.sleep(1)
            cap = connect_to_stream(rtsp_url)
            last_reconnect_time = current_time
            if cap.isOpened():
                print("✅ Reconnected successfully!")
            else:
                print("❌ Reconnection failed, will retry...")

        # Read frame from stream
        ret, frame = cap.read()

        if not ret:
            failed_frame_count += 1
            print("⚠️  Failed to read frame, reconnecting...")
            cap.release()
            time.sleep(2)
            cap = connect_to_stream(rtsp_url)
            last_reconnect_time = time.time()  # Reset reconnect timer
            if not cap.isOpened():
                print("❌ Failed to reconnect, retrying in 5 seconds...")
                time.sleep(5)
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
                    break
            if people_detected:
                break

        current_time = time.time()

        # State machine for dwell-time tracking
        if people_detected:
            # Person is currently in frame
            last_seen_time = current_time  # Update last seen timestamp

            if not person_present:
                # New person detected - start dwell timer
                person_present = True
                first_detection_time = current_time
                print(f"👁️  Person detected - starting {DWELL_TIME}s dwell timer...")

            # Check if we're in cooldown period
            if in_cooldown:
                time_until_ready = CAPTURE_COOLDOWN - (current_time - last_capture_time)
                if time_until_ready > 0:
                    # Still in cooldown, skip capture
                    continue
                else:
                    # Cooldown expired
                    in_cooldown = False
                    print("✅ Cooldown expired - ready to capture again")

            # Check if dwell time has been met
            dwell_duration = current_time - first_detection_time
            if dwell_duration >= DWELL_TIME and not in_cooldown:
                # Person has been present long enough - capture!
                print(f"📸 Dwell time met ({dwell_duration:.1f}s) - capturing still...")

                detection_count += 1
                detection_timestamp = datetime.now(ZoneInfo("America/Los_Angeles"))
                timestamp_str = detection_timestamp.strftime("%Y%m%d_%H%M%S")
                filename = f"detection_{timestamp_str}.jpg"

                # Blur faces for privacy protection FIRST on original frame
                blurred_frame, num_faces = face_blurrer.blur_faces(frame)

                # Draw bounding boxes on the blurred frame
                for result in results:
                    boxes = result.boxes
                    for box in boxes:
                        # Class 0 is 'person' in COCO dataset
                        if int(box.cls[0]) == 0:
                            confidence = float(box.conf[0])
                            # Only show high-confidence detections
                            if confidence > 0.5:
                                # Get bounding box coordinates
                                x1, y1, x2, y2 = map(int, box.xyxy[0])

                                # Draw bounding box on blurred frame
                                cv2.rectangle(blurred_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                # Save blurred frame locally
                cv2.imwrite(filename, blurred_frame)

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
                if num_faces > 0:
                    print(f"   🔒 {num_faces} face(s) blurred for privacy")
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
                            # Extract person crop from blurred frame
                            x1, y1, x2, y2 = (
                                person_box["x1"],
                                person_box["y1"],
                                person_box["x2"],
                                person_box["y2"],
                            )
                            person_crop = blurred_frame[y1:y2, x1:x2]

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

                # Clean up local file after all persons processed and uploaded
                try:
                    if supabase_client and os.path.exists(filename):
                        os.remove(filename)
                        print(f"   🗑️  Cleaned up local file: {filename}")
                except Exception as e:
                    print(f"   ⚠️  Failed to cleanup local file: {e}")

                print()

                # Start cooldown period
                last_capture_time = current_time
                in_cooldown = True
                print(f"⏸️  Starting {CAPTURE_COOLDOWN}s cooldown period...")
        else:
            # No person detected in this frame
            if person_present:
                # Person was previously detected - check grace period
                time_since_last_seen = current_time - last_seen_time if last_seen_time else 0

                if time_since_last_seen > DETECTION_GRACE_PERIOD:
                    # Grace period expired - person actually left
                    print(f"👋 Person left frame (no detection for {time_since_last_seen:.1f}s) - resetting dwell timer")
                    person_present = False
                    first_detection_time = None
                    last_seen_time = None
                # else: within grace period, ignore brief gap in detection

except KeyboardInterrupt:
    print()
    print("🛑 Stopping person detection...")
    print(f"📊 Total detections: {detection_count}")

finally:
    cap.release()
    print("✅ Cleanup complete!")
