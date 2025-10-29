#!/usr/bin/env python3
"""
Quick test to verify face blurring implementation works correctly.
Tests that the FaceBlurrer can be imported and initialized.
"""

import sys

try:
    # Test import
    from face_blur import FaceBlurrer, blur_faces
    print("✅ Successfully imported FaceBlurrer")

    # Test initialization
    blurrer = FaceBlurrer(blur_strength=51)
    print("✅ Successfully initialized FaceBlurrer")

    # Test Haar Cascade is available
    if blurrer.face_cascade.empty():
        print("❌ ERROR: Haar Cascade classifier not loaded")
        sys.exit(1)
    else:
        print("✅ Haar Cascade classifier loaded successfully")

    print("\n🎉 Face blurring module is ready to use!")
    print("\nTo test with an actual image, run:")
    print("  uv run python face_blur.py test_images/test-1.png output_blurred.jpg")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nMake sure you have opencv-python installed:")
    print("  uv sync")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
