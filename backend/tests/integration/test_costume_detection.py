#!/usr/bin/env python3
"""
Test script for costume detection with real Halloween images.
Processes test images through Baseten API and uploads to Supabase.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import cv2
from dotenv import load_dotenv

from backend.src.clients.baseten_client import BasetenClient
from backend.src.clients.supabase_client import SupabaseClient

# Load environment variables
load_dotenv()


def extract_person_bbox_from_image(image_path: str) -> dict:
    """
    Extract bounding box from test image filename.
    These test images already have YOLO detections with bounding boxes visible.
    We'll use the full image for now, but in production this would come from YOLO.

    Returns:
        Dict with approximate bounding box coordinates
    """
    # Read image to get dimensions
    img = cv2.imread(image_path)
    height, width = img.shape[:2]

    # For these test images, the person is roughly centered
    # We'll use approximate values based on the visible green bounding boxes
    # In production, these come from YOLO detection
    return {
        "x1": int(width * 0.35),   # Left edge
        "y1": int(height * 0.15),  # Top edge
        "x2": int(width * 0.65),   # Right edge
        "y2": int(height * 0.90),  # Bottom edge
    }


def process_test_image(
    image_path: str,
    baseten_client: BasetenClient,
    supabase_client: SupabaseClient,
) -> dict:
    """
    Process a single test image through the complete pipeline:
    1. Load image
    2. Classify costume with Baseten
    3. Upload to Supabase

    Args:
        image_path: Path to test image
        baseten_client: Initialized Baseten client
        supabase_client: Initialized Supabase client

    Returns:
        Dict with detection results
    """
    print(f"\n{'='*70}")
    print(f"Processing: {Path(image_path).name}")
    print('='*70)

    # Read image
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Failed to read image: {image_path}")
        return None

    height, width = img.shape[:2]
    print(f"📐 Image dimensions: {width}x{height}")

    # Get bounding box (simulated - in production this comes from YOLO)
    bbox = extract_person_bbox_from_image(image_path)
    print(f"📦 Bounding box: {bbox}")

    # Extract person crop from ORIGINAL unblurred image for classification
    person_crop = img[bbox["y1"]:bbox["y2"], bbox["x1"]:bbox["x2"]]

    # Encode person crop to bytes (for Baseten)
    _, buffer = cv2.imencode('.jpg', person_crop)
    image_bytes = buffer.tobytes()

    print("\n🎭 Classifying costume with Baseten...")

    # Classify costume
    try:
        classification, confidence, description = baseten_client.classify_costume(
            image_bytes
        )

        if classification:
            print(f"✅ Classification successful!")
            print(f"   Type:        {classification}")
            print(f"   Confidence:  {confidence:.2f}")
            print(f"   Description: {description}")
        else:
            print("❌ Classification failed - no results returned")
            return None

    except Exception as e:
        print(f"❌ Baseten API error: {e}")
        return None

    # Generate timestamp for this detection (Pacific time)
    timestamp = datetime.now(ZoneInfo("America/Los_Angeles"))

    # Save processed image locally
    output_dir = Path("backend/tests/test_detections")
    output_dir.mkdir(exist_ok=True)

    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
    output_filename = f"detection_{timestamp_str}_{classification}.jpg"
    output_path = output_dir / output_filename

    # Now blur the frame for privacy before saving
    blurred_img = img.copy()
    x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]

    # Extract person region
    person_region = blurred_img[y1:y2, x1:x2]

    # Apply moderate Gaussian blur (kernel size 33)
    # This obscures facial features while keeping costume colors/shapes visible
    if person_region.size > 0:
        blurred_person = cv2.GaussianBlur(person_region, (33, 33), 0)
        blurred_img[y1:y2, x1:x2] = blurred_person
        print(f"🔒 Blurred person for privacy")

    # Draw bounding box on blurred image
    cv2.rectangle(
        blurred_img,
        (x1, y1),
        (x2, y2),
        (0, 255, 0),
        3
    )

    cv2.imwrite(str(output_path), blurred_img)
    print(f"\n💾 Saved detection locally: {output_path}")

    # Upload to Supabase
    print("\n📤 Uploading to Supabase...")
    try:
        success = supabase_client.save_detection(
            image_path=str(output_path),
            timestamp=timestamp,
            confidence=0.94,  # High confidence from YOLO detection (simulated)
            bounding_box=bbox,
            costume_classification=classification,
            costume_description=description,
            costume_confidence=confidence,
        )

        if success:
            print("✅ Successfully uploaded to Supabase!")
        else:
            print("❌ Failed to upload to Supabase")

    except Exception as e:
        print(f"❌ Supabase upload error: {e}")

    return {
        "image_path": image_path,
        "classification": classification,
        "description": description,
        "confidence": confidence,
        "timestamp": timestamp,
        "uploaded": success if 'success' in locals() else False,
    }


def main():
    """Main test script"""
    print("🎃 Halloween Costume Detection Test")
    print("="*70)
    print("\nThis script will:")
    print("1. Load test images from test_images/")
    print("2. Classify costumes using Baseten API")
    print("3. Upload results to Supabase database")
    print("4. Save annotated images to backend/tests/test_detections/")
    print()

    # Check for required environment variables
    if not os.getenv("BASETEN_API_KEY"):
        print("❌ ERROR: BASETEN_API_KEY not set in .env file")
        print("   Please add your Baseten API key to continue")
        sys.exit(1)

    if not os.getenv("NEXT_PUBLIC_SUPABASE_URL") or not os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
        print("❌ ERROR: Supabase credentials not set in .env file")
        print("   Please add NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
        sys.exit(1)

    # Initialize clients
    print("🔧 Initializing clients...")
    try:
        baseten_client = BasetenClient()
        print(f"✅ Baseten connected (Model: {baseten_client.model})")
    except Exception as e:
        print(f"❌ Failed to initialize Baseten client: {e}")
        sys.exit(1)

    try:
        supabase_client = SupabaseClient()
        print(f"✅ Supabase connected (Device: {supabase_client.device_id})")
    except Exception as e:
        print(f"❌ Failed to initialize Supabase client: {e}")
        sys.exit(1)

    # Find test images (all images with prefix "test-single-" for single-person detection)
    test_images_dir = Path("backend/tests/fixtures")
    if not test_images_dir.exists():
        print(f"❌ ERROR: {test_images_dir} directory not found")
        sys.exit(1)

    # Find all images with "test-single-" prefix
    test_images = sorted(test_images_dir.glob("test-single-*"))

    if not test_images:
        print(f"❌ ERROR: No test images with prefix 'test-single-' found in {test_images_dir}")
        sys.exit(1)

    print(f"\n📸 Found {len(test_images)} test images")

    # Process each image
    results = []
    for i, image_path in enumerate(test_images, 1):
        result = process_test_image(
            str(image_path),
            baseten_client,
            supabase_client,
        )

        if result:
            results.append(result)

    # Print summary
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    print(f"\nTotal images processed: {len(test_images)}")
    print(f"Successful classifications: {len(results)}")
    print(f"Uploaded to Supabase: {sum(1 for r in results if r.get('uploaded'))}")

    if results:
        print("\n🎭 Detected Costumes:")
        print("-" * 70)
        for result in results:
            print(f"\n  {Path(result['image_path']).name}")
            print(f"    Classification: {result['classification']}")
            print(f"    Confidence:     {result['confidence']:.2f}")
            print(f"    Description:    {result['description']}")
            print(f"    Uploaded:       {'✅' if result.get('uploaded') else '❌'}")

    print("\n" + "="*70)
    print("✨ Test complete!")
    print("\n📁 Check backend/tests/test_detections/ for annotated images")
    print("🌐 Check your Supabase dashboard for uploaded detections")
    print("📊 Check your Next.js dashboard for real-time display")
    print("="*70)


if __name__ == "__main__":
    main()
