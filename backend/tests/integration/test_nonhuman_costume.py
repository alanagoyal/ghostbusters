#!/usr/bin/env python3
"""
Test script for non-human costume detection (inflatable costumes, etc.).
Uses dual-pass YOLO detection to catch both regular people and inflatable/bulky costumes
that YOLO may misclassify as objects (cars, animals, etc.).
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import cv2
from dotenv import load_dotenv
from ultralytics import YOLO

from backend.src.clients.baseten_client import BasetenClient
from backend.src.clients.supabase_client import SupabaseClient
from backend.src.costume_detector import detect_people_and_costumes

# Load environment variables
load_dotenv()


def process_nonhuman_costume_image(
    image_path: str,
    model: YOLO,
    baseten_client: BasetenClient,
    supabase_client: SupabaseClient,
) -> list:
    """
    Process a single image that may contain people in non-human/inflatable costumes.
    Uses dual-pass detection:
    1. Standard person detection (class 0)
    2. Inflatable costume detection (classes 2, 14, 16, 17)
    3. Validates non-person detections with costume classifier

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

    # Run YOLO dual-pass detection using shared detector
    all_detections = detect_people_and_costumes(
        img,
        model,
        baseten_client,
        confidence_threshold=0.5,  # Lower threshold for test images
        verbose=True,
    )

    # Generate timestamp for this frame (Pacific time)
    timestamp = datetime.now(ZoneInfo("America/Los_Angeles"))
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")

    # Save frame locally with all bounding boxes drawn
    output_dir = Path("backend/tests/test_detections")
    output_dir.mkdir(exist_ok=True)

    frame_filename = f"frame_{timestamp_str}.jpg"
    frame_path = output_dir / frame_filename

    # Prepare results for processing
    detection_results = []

    # Print summary
    num_standard = sum(1 for d in all_detections if d.get("detection_type") == "person")
    num_inflatables = sum(1 for d in all_detections if d.get("detection_type") == "inflatable")
    print(f"\n🎃 Total detections: {len(all_detections)} ({num_standard} standard + {num_inflatables} inflatable)")

    # Classify costumes for detections that don't already have classification
    # (inflatables were already classified during validation)
    for person_idx, person in enumerate(all_detections, start=1):
        if person.get("costume_classification"):
            # Already classified during inflatable validation
            print(f"\n{'─'*70}")
            print(f"Detection {person_idx}/{len(all_detections)} - Already classified")
            print(f"  Type: {person['detection_type']}")
            print(f"  Costume: {person['costume_classification']}")
            continue

        person_conf = person["confidence"]
        person_box = person["bounding_box"]
        detection_type = person.get("detection_type", "person")

        print(f"\n{'─'*70}")
        print(f"Processing {detection_type.capitalize()} {person_idx}/{len(all_detections)}")
        print(f"  YOLO Confidence: {person_conf:.2f}")
        print(f"  Bounding Box: {person_box}")

        # Extract crop from ORIGINAL unblurred frame for classification
        x1, y1, x2, y2 = person_box["x1"], person_box["y1"], person_box["x2"], person_box["y2"]
        crop = img[y1:y2, x1:x2]

        # Encode crop to bytes
        _, buffer = cv2.imencode('.jpg', crop)
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

        # Store classification results
        person["costume_classification"] = costume_classification
        person["costume_description"] = costume_description
        person["costume_confidence"] = costume_confidence

    # Now blur the frame for privacy before saving
    print(f"\n🔒 Blurring {len(all_detections)} detection(s) for privacy...")
    blurred_frame = img.copy()

    for detection in all_detections:
        bbox = detection["bounding_box"]
        x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]

        # Extract region
        region = blurred_frame[y1:y2, x1:x2]

        # Apply moderate Gaussian blur (kernel size 33)
        if region.size > 0:
            blurred_region = cv2.GaussianBlur(region, (33, 33), 0)
            blurred_frame[y1:y2, x1:x2] = blurred_region

    # Draw bounding boxes on the blurred frame
    for idx, detection in enumerate(all_detections, start=1):
        bbox = detection["bounding_box"]
        x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]

        # Use different colors for different detection types
        if detection["detection_type"] == "person":
            color = (0, 255, 0)  # Green for standard person
        else:
            color = (255, 0, 255)  # Magenta for validated inflatable

        cv2.rectangle(blurred_frame, (x1, y1), (x2, y2), color, 3)

    cv2.imwrite(str(frame_path), blurred_frame)
    print(f"💾 Saved blurred frame with all detections: {frame_path}")

    # Upload to Supabase
    for detection_idx, detection in enumerate(all_detections, start=1):
        if supabase_client:
            try:
                print(f"  📤 Uploading detection {detection_idx} to Supabase...")
                success = supabase_client.save_detection(
                    image_path=str(frame_path),
                    timestamp=timestamp,
                    confidence=detection["confidence"],
                    bounding_box=detection["bounding_box"],
                    costume_classification=detection.get("costume_classification"),
                    costume_description=detection.get("costume_description"),
                    costume_confidence=detection.get("costume_confidence"),
                )

                if success:
                    print("  ✅ Successfully uploaded to Supabase!")
                else:
                    print("  ❌ Failed to upload to Supabase")

                detection_results.append({
                    "detection_number": detection_idx,
                    "detection_type": detection["detection_type"],
                    "yolo_confidence": detection["confidence"],
                    "classification": detection.get("costume_classification"),
                    "description": detection.get("costume_description"),
                    "uploaded": success,
                })

            except Exception as e:
                print(f"  ❌ Supabase upload error: {e}")

    return detection_results


def main():
    """Main test script"""
    print("🎃 Non-Human Costume Detection Test")
    print("="*70)
    print("\nThis script tests dual-pass detection for inflatable/non-human costumes:")
    print("1. PASS 1: Detect standard people (YOLO class 0)")
    print("2. PASS 2: Detect potential inflatable costumes (YOLO classes 2, 14, 16, 17)")
    print("3. Validate inflatable detections with costume classifier")
    print("4. Upload validated detections to Supabase")
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

    # Find test images (all images with prefix "test-nonhuman-")
    test_images_dir = Path("backend/tests/fixtures")
    if not test_images_dir.exists():
        print(f"❌ ERROR: {test_images_dir} directory not found")
        sys.exit(1)

    # Find all images with "test-nonhuman-" prefix
    test_images = sorted(test_images_dir.glob("test-nonhuman-*"))

    if not test_images:
        print(f"❌ ERROR: No test images with prefix 'test-nonhuman-' found in {test_images_dir}")
        sys.exit(1)

    print(f"\n📸 Found {len(test_images)} test image(s)")

    # Process each image
    all_results = []
    total_detections = 0

    for i, image_path in enumerate(test_images, 1):
        results = process_nonhuman_costume_image(
            str(image_path),
            model,
            baseten_client,
            supabase_client,
        )

        if results:
            all_results.extend(results)
            total_detections += len(results)

    # Print summary
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    print(f"\nTotal images processed:      {len(test_images)}")
    print(f"Total detections:            {total_detections}")
    print(f"  Standard people:           {sum(1 for r in all_results if r.get('detection_type') == 'person')}")
    print(f"  Validated inflatables:     {sum(1 for r in all_results if r.get('detection_type') == 'inflatable')}")
    print(f"Successful classifications:  {sum(1 for r in all_results if r.get('classification'))}")
    print(f"Uploaded to Supabase:        {sum(1 for r in all_results if r.get('uploaded'))}")

    if all_results:
        print("\n🎭 All Detections:")
        print("-" * 70)
        for result in all_results:
            print(f"\n  Detection {result['detection_number']} ({result['detection_type']})")
            print(f"    YOLO Confidence:  {result['yolo_confidence']:.2f}")
            print(f"    Classification:   {result.get('classification', 'N/A')}")
            if result.get('description'):
                print(f"    Description:      {result['description']}")
            print(f"    Uploaded:         {'✅' if result.get('uploaded') else '❌'}")

    print("\n" + "="*70)
    print("✨ Test complete!")
    print("\n📁 Check backend/tests/test_detections/ for annotated images")
    if supabase_client:
        print("🌐 Check your Supabase dashboard for uploaded detections")
        print("📊 Check your Next.js dashboard for real-time display")
    print("="*70)


if __name__ == "__main__":
    main()
