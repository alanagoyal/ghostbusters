#!/usr/bin/env python3
"""
Person detection script using YOLOv8n on DoorBird RTSP stream.
Detects people in real-time and saves frames with bounding boxes.
Uploads detections to Supabase for dashboard display.

DUAL-PASS DETECTION:
- PASS 1: Detects standard people (YOLO class 0)
- PASS 2: Detects potential inflatable costumes (YOLO classes 2, 14, 16, 17)
  that may be misclassified by YOLO (e.g., T-Rex detected as "car")
- Validates inflatable detections with Baseten costume classifier
- Rejects detections that return "No costume" (filters out actual cars/objects)
"""

import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import cv2
from dotenv import load_dotenv
from ultralytics import YOLO

from backend.src.camera import camera_source, open_camera, region_of_interest
from backend.src.clients.supabase_client import SupabaseClient
from backend.src.clients.vision import create_vision_client, vision_settings
from backend.src.costume_detector import (
    INFLATABLE_CLASSES,
    PERSON_CLASS,
    detect_people_and_costumes,
)

# Load environment variables
load_dotenv()

# Validate settings before loading models or contacting services.
vision_settings()
rtsp_url = camera_source()
ROI_X_MIN, ROI_X_MAX, ROI_Y_MIN, ROI_Y_MAX = region_of_interest()
print("🚀 Starting person detection system...")
print("📹 Connecting to configured camera")

# Load YOLOv8n model (smallest/fastest)
print("🤖 Loading YOLOv8n model...")
model = YOLO("yolov8n.pt")  # Will download on first run (~6MB)
print("✅ Model loaded!")

# Initialize Supabase client (optional - graceful degradation if not configured)
supabase_client = None
try:
    supabase_client = SupabaseClient()
    print(f"✅ Connected to Supabase (Device: {supabase_client.device_id})")
except Exception:
    print("⚠️  Supabase not configured")
    print("   Detections will only be saved locally")

# Initialize Baseten client for costume classification (optional)
baseten_client = None
try:
    baseten_client = create_vision_client()
    print(f"✅ Cloud vision configured (Model: {baseten_client.model})")
except Exception:
    print("Cloud vision is not configured")
    print("   Costume classification will be skipped")

# Detection parameters
CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence for person detection
CONSECUTIVE_FRAMES_REQUIRED = 2  # Number of consecutive detections before capture
CAPTURE_COOLDOWN = 30  # Seconds to wait before next capture

# Region of Interest (ROI) - only detect people in doorstep area
# Coordinates are normalized (0.0 to 1.0) relative to frame dimensions
# Configured through ROI_*; legacy DoorBird defaults preserve the original view.

print(
    f"🎯 Detection: {CONSECUTIVE_FRAMES_REQUIRED} consecutive frames at "
    f">{CONFIDENCE_THRESHOLD} confidence"
)
print(
    "🎈 Dual-pass: Standard people (class 0) + inflatable costumes (classes 2, 14, 16, "
    "17)"
)
print(
    f"📍 ROI: Doorstep area only (x: {ROI_X_MIN}-{ROI_X_MAX}, y: "
    f"{ROI_Y_MIN}-{ROI_Y_MAX})"
)
print(f"⏱️  Cooldown: {CAPTURE_COOLDOWN}s between captures")


# Function to check if a bounding box is within the region of interest
def is_in_roi(bbox, frame_width, frame_height):
    """Check if bounding box center is within the doorstep ROI."""
    x1, y1, x2, y2 = bbox
    # Calculate center of bounding box
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2

    # Normalize to 0-1 range
    norm_x = center_x / frame_width
    norm_y = center_y / frame_height

    # Check if center is within ROI bounds
    return ROI_X_MIN <= norm_x <= ROI_X_MAX and ROI_Y_MIN <= norm_y <= ROI_Y_MAX


# Function to connect/reconnect to RTSP stream
connect_to_stream = open_camera

# Open RTSP stream
cap = connect_to_stream(rtsp_url)

if not cap.isOpened():
    print("❌ ERROR: Could not connect to camera")
    exit(1)

print("✅ Connected to camera!")
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

# Detection tracking state
consecutive_detections = 0  # Count of consecutive frames with person detected
last_capture_time = 0  # When we last captured an image
in_cooldown = False  # Whether we're in cooldown period

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
        if supabase_client:
            supabase_client.report_detector_running()

        # Get frame dimensions for ROI checking
        frame_height, frame_width = frame.shape[:2]

        # DUAL-PASS DETECTION: Check for people OR potential inflatable costumes in ROI
        # PASS 1: Standard person detection (class 0)
        # PASS 2: Potential inflatable costumes (classes 2, 14, 16, 17)
        people_detected = False
        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls = int(box.cls[0])
                # Check both standard people and potential inflatables
                if cls == PERSON_CLASS or cls in INFLATABLE_CLASSES:
                    confidence = float(box.conf[0])
                    if confidence > CONFIDENCE_THRESHOLD:
                        # Check if detection is in the doorstep ROI
                        bbox = box.xyxy[0].tolist()
                        if is_in_roi(bbox, frame_width, frame_height):
                            people_detected = True
                            break
            if people_detected:
                break

        current_time = time.time()

        # Check if we're in cooldown period
        if in_cooldown:
            time_since_capture = current_time - last_capture_time
            if time_since_capture >= CAPTURE_COOLDOWN:
                # Cooldown expired
                in_cooldown = False
                print("✅ Cooldown expired - ready for next detection")
            # While in cooldown, ignore all detections and reset counter
            consecutive_detections = 0
            continue

        # Track consecutive detections
        if people_detected:
            consecutive_detections += 1
            print(
                f"👁️  Person detected "
                f"({consecutive_detections}/{CONSECUTIVE_FRAMES_REQUIRED})"
            )

            # Check if we have enough consecutive detections to capture
            if consecutive_detections >= CONSECUTIVE_FRAMES_REQUIRED:
                # Person detected in required consecutive frames - capture!
                print(
                    f"📸 Capturing still ({CONSECUTIVE_FRAMES_REQUIRED} consecutive "
                    f"detections)..."
                )

                detection_count += 1
                detection_timestamp = datetime.now(ZoneInfo("America/Los_Angeles"))
                timestamp_str = detection_timestamp.strftime("%Y%m%d_%H%M%S")
                filename = f"detection_{timestamp_str}.jpg"

                # DUAL-PASS DETECTION: Collect ALL detections using shared detector
                all_detections = detect_people_and_costumes(
                    frame,
                    model,
                    baseten_client,
                    confidence_threshold=CONFIDENCE_THRESHOLD,
                    verbose=True,
                )

                # Filter detections to only include those in the doorstep ROI
                detected_people = [
                    person
                    for person in all_detections
                    if is_in_roi(
                        [
                            person["bounding_box"]["x1"],
                            person["bounding_box"]["y1"],
                            person["bounding_box"]["x2"],
                            person["bounding_box"]["y2"],
                        ],
                        frame_width,
                        frame_height,
                    )
                ]

                num_people = len(detected_people)
                print(
                    f"👤 {num_people} person(s) detected! "
                    f"(Detection #{detection_count})"
                )

                # Start cooldown period immediately after detection (before Baseten
                # call)
                last_capture_time = current_time
                in_cooldown = True
                consecutive_detections = 0
                print(f"⏸️  Starting {CAPTURE_COOLDOWN}s cooldown period...")
                print()

                # Process each detected person separately for costume classification (on
                # UNBLURRED frame)
                # Note: Validated inflatables already have costume data from validation
                # step
                for person_idx, person in enumerate(detected_people, start=1):
                    person_conf = person["confidence"]
                    person_box = person["bounding_box"]
                    detection_type = person.get("detection_type", "person")

                    if num_people > 1:
                        print(
                            f"   Processing {detection_type} {person_idx}/{num_people} "
                            f"(confidence: {person_conf:.2f})"
                        )

                    # Skip costume classification if already done during inflatable
                    # validation
                    if person.get("costume_classification"):
                        print(
                            f"   ✓ Costume already classified: "
                            f"{person['costume_classification']}"
                        )
                        continue

                    # Classify costume using Baseten if configured (using original
                    # unblurred frame)
                    costume_classification = None
                    costume_confidence = None
                    costume_description = None

                    if baseten_client:
                        try:
                            print("   🎭 Classifying costume...")
                            # Extract person crop from ORIGINAL frame (not blurred)
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
                                    f"   👗 Costume: {costume_classification} "
                                    f"({costume_confidence:.2f})"
                                )
                                print(f"      {costume_description}")
                            else:
                                print("   ⚠️  Could not classify costume")
                        except Exception:
                            print("   ⚠️  Costume classification failed")

                    # Store classification results for later use
                    person["costume_classification"] = costume_classification
                    person["costume_description"] = costume_description
                    person["costume_confidence"] = costume_confidence

                # Now blur the frame for privacy before saving/uploading
                blurred_frame = frame.copy()
                num_people_blurred = 0

                for person in detected_people:
                    bbox = person["bounding_box"]
                    x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]

                    # Extract person region
                    person_region = blurred_frame[y1:y2, x1:x2]

                    # Apply moderate Gaussian blur (kernel size 33)
                    # This obscures facial features while keeping costume colors/shapes
                    # visible
                    if person_region.size > 0:  # Ensure region is valid
                        blurred_person = cv2.GaussianBlur(person_region, (33, 33), 0)
                        blurred_frame[y1:y2, x1:x2] = blurred_person
                        num_people_blurred += 1

                # Draw bounding boxes on the blurred frame
                for person in detected_people:
                    bbox = person["bounding_box"]
                    x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]
                    cv2.rectangle(blurred_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                # Save blurred frame locally
                if not cv2.imwrite(filename, blurred_frame):
                    raise OSError("Could not save detection image; check disk space")
                print(f"   🔒 {num_people_blurred} person(s) blurred for privacy")
                print(f"   Saved locally: {filename}")

                # Retain the file unless every image and record was saved.
                uploads_succeeded = bool(supabase_client) and bool(detected_people)
                for person in detected_people:
                    if supabase_client:
                        try:
                            saved = supabase_client.save_detection(
                                image_path=filename,
                                timestamp=detection_timestamp,
                                confidence=person["confidence"],
                                bounding_box=person["bounding_box"],
                                costume_classification=person.get(
                                    "costume_classification"
                                ),
                                costume_description=person.get("costume_description"),
                                costume_confidence=person.get("costume_confidence"),
                            )
                            uploads_succeeded = uploads_succeeded and saved
                        except Exception:
                            uploads_succeeded = False
                            print("   ⚠️  Supabase upload failed")

                # Clean up local file after all persons processed and uploaded
                try:
                    if uploads_succeeded and os.path.exists(filename):
                        os.remove(filename)
                        print(f"   🗑️  Cleaned up local file: {filename}")
                except Exception:
                    print("   ⚠️  Failed to cleanup local file")
        else:
            # No person detected - reset consecutive counter
            if consecutive_detections > 0:
                print(
                    f"👋 Person left frame - resetting counter (was at "
                    f"{consecutive_detections})"
                )
            consecutive_detections = 0

except KeyboardInterrupt:
    print()
    print("🛑 Stopping person detection...")
    print(f"📊 Total detections: {detection_count}")

finally:
    if supabase_client:
        supabase_client.report_detector_running(False)
    cap.release()
    print("✅ Cleanup complete!")
