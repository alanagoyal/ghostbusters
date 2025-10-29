#!/usr/bin/env python3
"""
Quick test script for user-provided multi-person images.
Tests the multi-person detection on specific images.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import cv2
from dotenv import load_dotenv
from ultralytics import YOLO

from baseten_client import BasetenClient
from supabase_client import SupabaseClient

# Load environment variables
load_dotenv()


def process_image(
    image_path: str,
    model: YOLO,
    baseten_client: BasetenClient = None,
    supabase_client: SupabaseClient = None,
) -> list:
    """Process a single image with multiple people."""
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

    # Generate timestamp
    timestamp = datetime.now()
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")

    # Save frame with bounding boxes
    output_dir = Path("test_detections")
    output_dir.mkdir(exist_ok=True)

    frame_filename = f"frame_{timestamp_str}.jpg"
    frame_path = output_dir / frame_filename

    # Draw all bounding boxes
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

    # Process each detected person
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

        # Save individual person crop
        person_crop_path = output_dir / f"person_{timestamp_str}_{person_idx}.jpg"
        cv2.imwrite(str(person_crop_path), person_crop)
        print(f"  💾 Saved crop: {person_crop_path}")

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
        uploaded = False
        if supabase_client:
            try:
                print("  📤 Uploading to Supabase...")
                uploaded = supabase_client.save_detection(
                    image_path=str(frame_path),
                    timestamp=timestamp,
                    confidence=person_conf,
                    bounding_box=person_box,
                    costume_classification=costume_classification,
                    costume_description=costume_description,
                    costume_confidence=costume_confidence,
                )

                if uploaded:
                    print("  ✅ Successfully uploaded to Supabase!")
                else:
                    print("  ❌ Failed to upload to Supabase")

            except Exception as e:
                print(f"  ❌ Supabase upload error: {e}")

        detection_results.append({
            "person_number": person_idx,
            "confidence": person_conf,
            "bounding_box": person_box,
            "classification": costume_classification,
            "description": costume_description,
            "costume_confidence": costume_confidence,
            "uploaded": uploaded,
        })

    return detection_results


def main():
    """Main test script"""
    print("🎃 Testing Multi-Person Detection on User Images")
    print("="*70)

    # Image paths
    image_paths = [
        "/tmp/images/image-2fFWPW1BDqm3a16FFsDp0.png",
        "/tmp/images/image-BXmcqIxnCvBpp5wj9EWo0.png",
    ]

    # Check if images exist
    for img_path in image_paths:
        if not Path(img_path).exists():
            print(f"❌ ERROR: Image not found: {img_path}")
            sys.exit(1)

    print(f"\n✅ Found {len(image_paths)} test images")

    # Initialize Baseten client (optional)
    baseten_client = None
    if os.getenv("BASETEN_API_KEY"):
        try:
            baseten_client = BasetenClient()
            print(f"✅ Baseten connected (Model: {baseten_client.model})")
        except Exception as e:
            print(f"⚠️  Baseten not available: {e}")
    else:
        print("⚠️  BASETEN_API_KEY not set - costume classification will be skipped")

    # Initialize Supabase client (optional)
    supabase_client = None
    if os.getenv("NEXT_PUBLIC_SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
        try:
            supabase_client = SupabaseClient()
            print(f"✅ Supabase connected (Device: {supabase_client.device_id})")
        except Exception as e:
            print(f"⚠️  Supabase not available: {e}")
    else:
        print("⚠️  Supabase credentials not set - uploads will be skipped")

    # Load YOLO model
    print("\n🤖 Loading YOLOv8n model...")
    model = YOLO("yolov8n.pt")
    print("✅ Model loaded!")

    # Process each image
    all_results = []
    total_people = 0

    for image_path in image_paths:
        results = process_image(
            image_path,
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
    print(f"\nTotal images processed:      {len(image_paths)}")
    print(f"Total people detected:       {total_people}")
    print(f"Successful classifications:  {sum(1 for r in all_results if r.get('classification'))}")
    print(f"Uploaded to Supabase:        {sum(1 for r in all_results if r.get('uploaded'))}")

    if all_results:
        print("\n🎭 All Detections:")
        print("-" * 70)
        for result in all_results:
            print(f"\n  Person {result['person_number']}")
            print(f"    YOLO Confidence:  {result['confidence']:.2f}")
            print(f"    Bounding Box:     {result['bounding_box']}")
            if result.get('classification'):
                print(f"    Classification:   {result['classification']} ({result.get('costume_confidence', 0):.2f})")
                if result.get('description'):
                    print(f"    Description:      {result['description']}")
            else:
                print(f"    Classification:   N/A")
            print(f"    Uploaded:         {'✅' if result.get('uploaded') else '❌'}")

    print("\n" + "="*70)
    print("✨ Test complete!")
    print("\n📁 Check test_detections/ for:")
    print("   - Annotated frames with bounding boxes")
    print("   - Individual person crops")
    if supabase_client:
        print("🌐 Check your dashboard to see all detections appear in real-time!")
    print("="*70)


if __name__ == "__main__":
    main()
