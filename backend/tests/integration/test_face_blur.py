#!/usr/bin/env python3
"""
Test script to verify face blurring functionality on test images.
"""

import os
import cv2
from pathlib import Path

from backend.src.utils.face_blur import FaceBlurrer


def main():
    # Setup paths
    fixtures_dir = Path(__file__).parent.parent / "fixtures"
    output_dir = Path(__file__).parent.parent / "test_blurred_output"
    output_dir.mkdir(exist_ok=True)

    # Initialize face blurrer
    face_blurrer = FaceBlurrer(blur_strength=51)
    print("🔒 Testing face blurring on test images...\n")

    # Get all test images
    test_images = sorted(fixtures_dir.glob("test-*.png"))

    if not test_images:
        print("❌ No test images found in fixtures directory")
        return

    total_faces = 0

    # Process each test image
    for img_path in test_images:
        print(f"📸 Processing {img_path.name}...")

        # Read image
        image = cv2.imread(str(img_path))

        if image is None:
            print(f"   ⚠️  Failed to load image")
            continue

        # Blur faces
        blurred_image, num_faces = face_blurrer.blur_faces(image)

        # Save blurred image
        output_path = output_dir / f"blurred_{img_path.name}"
        cv2.imwrite(str(output_path), blurred_image)

        print(f"   ✅ Detected and blurred {num_faces} face(s)")
        print(f"   💾 Saved to: {output_path}")
        print()

        total_faces += num_faces

    print(f"🎉 Complete! Processed {len(test_images)} images, blurred {total_faces} total faces")
    print(f"📁 Output directory: {output_dir}")


if __name__ == "__main__":
    main()
