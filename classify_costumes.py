#!/usr/bin/env python3
"""
Real-time Halloween costume classifier.
Combines YOLOv8 person detection with Qwen-VL costume classification via Baseten.
"""

import base64
import os
import sys
import time
from datetime import datetime
from io import BytesIO

import cv2
import requests
from dotenv import load_dotenv
from PIL import Image
from ultralytics import YOLO

load_dotenv()

# Configuration
DOORBIRD_IP = os.getenv("DOORBIRD_IP")
DOORBIRD_USER = os.getenv("DOORBIRD_USERNAME")
DOORBIRD_PASSWORD = os.getenv("DOORBIRD_PASSWORD")
BASETEN_API_KEY = os.getenv("BASETEN_API_KEY")
BASETEN_MODEL_URL = os.getenv("BASETEN_MODEL_URL")

# Check credentials
if not all([DOORBIRD_IP, DOORBIRD_USER, DOORBIRD_PASSWORD]):
    print("❌ Missing DoorBird credentials in .env")
    sys.exit(1)

if not all([BASETEN_API_KEY, BASETEN_MODEL_URL]):
    print("❌ Missing Baseten credentials in .env")
    sys.exit(1)

# Settings
PERSON_CONFIDENCE = 0.5
COOLDOWN_SECONDS = 5
FRAME_SKIP = 30  # Process every 30th frame


def classify_costume(frame):
    """Classify costume in frame using Baseten API."""
    # Convert frame to base64
    pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    buffered = BytesIO()
    pil_img.save(buffered, format="PNG")
    image_b64 = f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode('utf-8')}"

    # Call Baseten API
    payload = {
        "image": image_b64,
        "prompt": (
            "What Halloween costume is this person wearing? "
            "Just give the costume name (e.g., 'Witch', 'Vampire', 'Spider-Man', etc.). "
            "Be specific but brief."
        ),
        "max_new_tokens": 100,
        "temperature": 0.7,
    }

    try:
        response = requests.post(
            BASETEN_MODEL_URL,
            headers={"Authorization": f"Api-Key {BASETEN_API_KEY}"},
            json=payload,
            timeout=60
        )

        if response.status_code != 200:
            return f"Error: {response.status_code}"

        result = response.json()
        output = result.get("output", "No response")

        # Clean up output - remove special tokens
        output = output.replace("<|endoftext|>", "").strip()
        output = output.replace("<|im_end|>", "").strip()

        # Remove prompt echo - extract response after prompt
        prompt_text = "Halloween costume"
        if prompt_text in output:
            parts = output.split("?", 1)
            if len(parts) > 1:
                output = parts[1].strip()

        # Remove image references
        if output.startswith("Picture"):
            lines = output.split("\n")
            output = "\n".join(lines[1:]) if len(lines) > 1 else output

        return output

    except Exception as e:
        return f"Error: {str(e)}"


print("🎃 Halloween Costume Classifier")
print("=" * 60)
print()

# Load YOLO
print("🤖 Loading YOLOv8...")
yolo = YOLO("yolov8n.pt")

# Connect to DoorBird
rtsp_url = f"rtsp://{DOORBIRD_USER}:{DOORBIRD_PASSWORD}@{DOORBIRD_IP}/mpeg/media.amp"
print(f"📹 Connecting to DoorBird at {DOORBIRD_IP}...")
cap = cv2.VideoCapture(rtsp_url)

if not cap.isOpened():
    print("❌ Failed to connect to DoorBird")
    sys.exit(1)

print("✅ Connected!")
print()
print("👻 Watching for trick-or-treaters...")
print("Press Ctrl+C to stop")
print("=" * 60)
print()

frame_count = 0
detection_count = 0
last_detection = 0

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(1)
            continue

        frame_count += 1
        if frame_count % FRAME_SKIP != 0:
            continue

        # Detect people with YOLO
        results = yolo(frame, verbose=False)
        person_detected = False

        for result in results:
            for box in result.boxes:
                if int(box.cls[0]) == 0 and float(box.conf[0]) > PERSON_CONFIDENCE:
                    person_detected = True
                    break

        # Classify costume if person detected
        if person_detected and time.time() - last_detection > COOLDOWN_SECONDS:
            detection_count += 1
            print(f"👤 Person detected! Classifying costume...")

            costume = classify_costume(frame)

            print()
            print("🎭 COSTUME CLASSIFICATION")
            print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
            print(f"   #{detection_count}")
            print("   " + "-" * 50)
            print(f"   {costume}")
            print("   " + "-" * 50)
            print()

            # Save image
            filename = f"costume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            cv2.imwrite(filename, frame)
            print(f"   💾 Saved: {filename}")
            print()

            last_detection = time.time()

except KeyboardInterrupt:
    print()
    print("🛑 Stopping...")
    print(f"📊 Total costumes classified: {detection_count}")

finally:
    cap.release()
    print("✅ Done!")
