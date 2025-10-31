#!/usr/bin/env python3
"""
Test script to verify YOLO detects people in full-body costumes.
Compares default vs costume-optimized detection settings.
"""

import cv2
from ultralytics import YOLO

def test_detection(image_path, conf_threshold=0.7, iou_threshold=0.45):
    """Test YOLO detection with given thresholds."""
    print(f"\n{'='*60}")
    print(f"Testing with conf={conf_threshold}, iou={iou_threshold}")
    print(f"{'='*60}")

    # Load model
    model = YOLO("yolov8n.pt")

    # Read image
    frame = cv2.imread(image_path)
    if frame is None:
        print(f"❌ Could not read image: {image_path}")
        return

    # Run detection
    results = model(frame, conf=conf_threshold, iou=iou_threshold, verbose=False)

    # Count person detections
    people_detected = []
    for result in results:
        boxes = result.boxes
        for box in boxes:
            if int(box.cls[0]) == 0:  # person class
                confidence = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                people_detected.append({
                    "confidence": confidence,
                    "bbox": [x1, y1, x2, y2]
                })

    print(f"\n✅ Detected {len(people_detected)} person(s):")
    for i, person in enumerate(people_detected, 1):
        conf = person["confidence"]
        bbox = person["bbox"]
        print(f"   Person {i}: confidence={conf:.3f}, bbox={bbox}")

    # Draw boxes on image
    output_frame = frame.copy()
    for person in people_detected:
        x1, y1, x2, y2 = person["bbox"]
        conf = person["confidence"]
        cv2.rectangle(output_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(output_frame, f"{conf:.2f}", (x1, y1-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Save result
    output_filename = f"detection_conf{conf_threshold}_iou{iou_threshold}.jpg"
    cv2.imwrite(output_filename, output_frame)
    print(f"\n💾 Saved annotated image: {output_filename}")

    return len(people_detected)

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python test_costume_detection.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]

    print(f"\n🎭 Testing YOLO costume detection on: {image_path}")

    # Test 1: Original settings (high threshold - may miss costumes)
    print("\n📊 TEST 1: Original Settings (Default)")
    count_original = test_detection(image_path, conf_threshold=0.7, iou_threshold=0.45)

    # Test 2: Costume-optimized settings (lower thresholds)
    print("\n📊 TEST 2: Costume-Optimized Settings")
    count_costume = test_detection(image_path, conf_threshold=0.3, iou_threshold=0.4)

    # Summary
    print(f"\n{'='*60}")
    print("📈 SUMMARY")
    print(f"{'='*60}")
    print(f"Original settings:  {count_original} person(s) detected")
    print(f"Costume-optimized:  {count_costume} person(s) detected")

    if count_costume > count_original:
        print(f"\n✅ Costume mode detected {count_costume - count_original} additional person(s)!")
        print("   This confirms the lower thresholds help with full-body costumes.")
    elif count_costume == count_original:
        print("\n⚠️  Same detection count. The costume may be well-formed enough")
        print("   that even default settings work, or thresholds need further tuning.")
    else:
        print("\n⚠️  Original detected more. This is unexpected - please review.")
