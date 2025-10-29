#!/usr/bin/env python3
"""
Test script for multi-person detection in a single frame.
Uses YOLOv8n to detect all people in test images and processes each separately.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import cv2
from dotenv import load_dotenv
from ultralytics import YOLO

from backend.src.clients.baseten_client import BasetenClient
from backend.src.clients.supabase_client import SupabaseClient

# Load environment variables
load_dotenv()


def process_multi_person_image(
    image_path: str,
    model: YOLO,
    baseten_client: BasetenClient,
    supabase_client: SupabaseClient,
) -> list:
    """
    Process a single image that may contain multiple people.
    Detects all people using YOLO, classifies each costume, and saves separately.

    Args:
        image_path: Path to test image
        model: YOLOv8 model
        baseten_client: Initialized Baseten client
        supabase_client: Initialized Supabase client

    Returns:
        List of detection results
    """
    print(f"\n{'='*70}")
    print(f"Processing: {Path(image_path).name}")
    print('='*70)

    # Read image
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Failed to read image: {image_path}")
        return []

    height, width = img.shape[:2]
    print(f"📐 Image dimensions: {width}x{height}")

    # Run YOLO detection
    print("🔍 Running YOLO person detection...")
    results = model(img, verbose=False)

    # Collect all person detections
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

    if num_people == 0:
        print("⚠️  No people detected in this image")
        return []

    print(f"✅ Detected {num_people} person(s)")

    # Generate timestamp for this frame
    timestamp = datetime.now()
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")

    # Save frame locally with all bounding boxes drawn
    output_dir = Path("test_detections")
    output_dir.mkdir(exist_ok=True)

    frame_filename = f"frame_{timestamp_str}.jpg"
    frame_path = output_dir / frame_filename

    # Create copy for drawing all boxes
    frame_with_boxes = img.copy()
    for idx, person in enumerate(detected_people, start=1):
        bbox = person["bounding_box"]
        x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]

        # Draw bounding box
        cv2.rectangle(frame_with_boxes, (x1, y1), (x2, y2), (0, 255, 0), 3)

        # Add person number label
        label = f"Person {idx} ({person['confidence']:.2f})"
        cv2.putText(
            frame_with_boxes,
            label,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 255, 0),
            2,
        )

    cv2.imwrite(str(frame_path), frame_with_boxes)
    print(f"💾 Saved frame with all detections: {frame_path}")

    # Process each detected person separately
    detection_results = []

    for person_idx, person in enumerate(detected_people, start=1):
        person_conf = person["confidence"]
        person_box = person["bounding_box"]

        print(f"\n{'─'*70}")
        print(f"Processing Person {person_idx}/{num_people}")
        print(f"  YOLO Confidence: {person_conf:.2f}")
        print(f"  Bounding Box: {person_box}")

        # Extract person crop
        x1, y1, x2, y2 = person_box["x1"], person_box["y1"], person_box["x2"], person_box["y2"]
        person_crop = img[y1:y2, x1:x2]

        # Encode person crop to bytes
        _, buffer = cv2.imencode('.jpg', person_crop)
        image_bytes = buffer.tobytes()

        # Classify costume
        costume_classification = None
        costume_confidence = None
        costume_description = None

        if baseten_client:
            try:
                print("  🎭 Classifying costume...")
                (
                    costume_classification,
                    costume_confidence,
                    costume_description,
                ) = baseten_client.classify_costume(image_bytes)

                if costume_classification:
                    print(f"  ✅ Costume: {costume_classification} ({costume_confidence:.2f})")
                    print(f"     {costume_description}")
                else:
                    print("  ⚠️  Could not classify costume")
            except Exception as e:
                print(f"  ❌ Costume classification failed: {e}")

        # Upload to Supabase
        if supabase_client:
            try:
                print("  📤 Uploading to Supabase...")
                success = supabase_client.save_detection(
                    image_path=str(frame_path),
                    timestamp=timestamp,
                    confidence=person_conf,
                    bounding_box=person_box,
                    costume_classification=costume_classification,
                    costume_description=costume_description,
                    costume_confidence=costume_confidence,
                )

                if success:
                    print("  ✅ Successfully uploaded to Supabase!")
                else:
                    print("  ❌ Failed to upload to Supabase")

                detection_results.append({
                    "person_number": person_idx,
                    "confidence": person_conf,
                    "classification": costume_classification,
                    "description": costume_description,
                    "uploaded": success,
                })

            except Exception as e:
                print(f"  ❌ Supabase upload error: {e}")

    return detection_results


def main():
    """Main test script"""
    print("🎃 Multi-Person Detection Test")
    print("="*70)
    print("\nThis script will:")
    print("1. Load test images from tests/images/")
    print("2. Detect ALL people using YOLOv8n")
    print("3. Classify each person's costume separately")
    print("4. Upload each detection as a separate database entry")
    print("5. Save annotated images to test_detections/")
    print()

    # Check for required environment variables
    if not os.getenv("BASETEN_API_KEY"):
        print("❌ ERROR: BASETEN_API_KEY not set in .env file")
        print("   Test will continue but costume classification will be skipped")
        baseten_client = None
    else:
        try:
            baseten_client = BasetenClient()
            print(f"✅ Baseten connected (Model: {baseten_client.model})")
        except Exception as e:
            print(f"⚠️  Failed to initialize Baseten client: {e}")
            baseten_client = None

    if not os.getenv("NEXT_PUBLIC_SUPABASE_URL") or not os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
        print("❌ ERROR: Supabase credentials not set in .env file")
        print("   Test will continue but uploads will be skipped")
        supabase_client = None
    else:
        try:
            supabase_client = SupabaseClient()
            print(f"✅ Supabase connected (Device: {supabase_client.device_id})")
        except Exception as e:
            print(f"⚠️  Failed to initialize Supabase client: {e}")
            supabase_client = None

    # Load YOLO model
    print("\n🤖 Loading YOLOv8n model...")
    model = YOLO("yolov8n.pt")
    print("✅ Model loaded!")

    # Find test images (only test-6.png and test-7.png for multi-person detection)
    test_images_dir = Path("tests/images")
    if not test_images_dir.exists():
        print(f"❌ ERROR: {test_images_dir} directory not found")
        sys.exit(1)

    test_images = [
        test_images_dir / "test-6.png",
        test_images_dir / "test-7.png",
    ]

    # Filter to only existing files
    test_images = [img for img in test_images if img.exists()]

    if not test_images:
        print(f"❌ ERROR: test-6.png and test-7.png not found in {test_images_dir}")
        sys.exit(1)

    print(f"\n📸 Found {len(test_images)} test images")

    # Process each image
    all_results = []
    total_people = 0

    for i, image_path in enumerate(test_images, 1):
        results = process_multi_person_image(
            str(image_path),
            model,
            baseten_client,
            supabase_client,
        )

        if results:
            all_results.extend(results)
            total_people += len(results)

    # Print summary
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    print(f"\nTotal images processed:      {len(test_images)}")
    print(f"Total people detected:       {total_people}")
    print(f"Successful classifications:  {sum(1 for r in all_results if r.get('classification'))}")
    print(f"Uploaded to Supabase:        {sum(1 for r in all_results if r.get('uploaded'))}")

    if all_results:
        print("\n🎭 All Detections:")
        print("-" * 70)
        for result in all_results:
            print(f"\n  Person {result['person_number']}")
            print(f"    YOLO Confidence:  {result['confidence']:.2f}")
            print(f"    Classification:   {result.get('classification', 'N/A')}")
            if result.get('description'):
                print(f"    Description:      {result['description']}")
            print(f"    Uploaded:         {'✅' if result.get('uploaded') else '❌'}")

    print("\n" + "="*70)
    print("✨ Test complete!")
    print("\n📁 Check test_detections/ for annotated images")
    if supabase_client:
        print("🌐 Check your Supabase dashboard for uploaded detections")
        print("📊 Check your Next.js dashboard for real-time display")
    print("="*70)


if __name__ == "__main__":
    main()
