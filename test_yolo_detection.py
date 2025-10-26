"""
Test YOLO person detection on the DoorBird test frame.
"""

import cv2
from ultralytics import YOLO
import os

def test_yolo_detection():
    print("🔍 Testing YOLO person detection...")

    # Load YOLOv8 nano model (smallest, fastest)
    print("\n📦 Loading YOLOv8n model...")
    model = YOLO('yolov8n.pt')  # Will auto-download on first run

    # Load the test frame
    test_frame_path = "test_doorbird_frame.jpg"
    if not os.path.exists(test_frame_path):
        print(f"❌ Error: {test_frame_path} not found!")
        print("   Run test_doorbird_connection.py first to capture a test frame.")
        return

    print(f"\n📸 Loading test frame: {test_frame_path}")
    frame = cv2.imread(test_frame_path)

    if frame is None:
        print("❌ Error: Could not load test frame!")
        return

    print(f"   Frame size: {frame.shape[1]}x{frame.shape[0]}")

    # Run YOLO detection
    print("\n🤖 Running YOLO detection...")
    results = model(frame, verbose=False)

    # Filter for person detections (class 0 in COCO dataset)
    person_detections = []
    for result in results:
        boxes = result.boxes
        for box in boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            if class_id == 0:  # Person class
                person_detections.append({
                    'bbox': box.xyxy[0].cpu().numpy(),
                    'confidence': confidence
                })

    print(f"\n✅ Found {len(person_detections)} person(s) in the frame!")

    # Draw bounding boxes and save
    annotated_frame = frame.copy()
    for i, detection in enumerate(person_detections):
        bbox = detection['bbox']
        conf = detection['confidence']

        x1, y1, x2, y2 = map(int, bbox)

        # Draw rectangle
        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Add label
        label = f"Person {i+1}: {conf:.2f}"
        cv2.putText(annotated_frame, label, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        print(f"   Person {i+1}:")
        print(f"      Confidence: {conf:.2f}")
        print(f"      Bounding box: ({x1}, {y1}) -> ({x2}, {y2})")
        print(f"      Size: {x2-x1}x{y2-y1} pixels")

    # Save annotated frame
    output_path = "test_yolo_detections.jpg"
    cv2.imwrite(output_path, annotated_frame)
    print(f"\n💾 Saved annotated frame to: {output_path}")

    # Also save cropped person images
    for i, detection in enumerate(person_detections):
        bbox = detection['bbox']
        x1, y1, x2, y2 = map(int, bbox)

        # Crop person from frame
        person_crop = frame[y1:y2, x1:x2]

        crop_path = f"test_person_crop_{i+1}.jpg"
        cv2.imwrite(crop_path, person_crop)
        print(f"   Saved person crop {i+1} to: {crop_path}")

    if len(person_detections) == 0:
        print("\n⚠️  No people detected in the test frame.")
        print("   This could mean:")
        print("   - The frame doesn't contain people")
        print("   - The camera angle needs adjustment")
        print("   - YOLO threshold is too high")
    else:
        print(f"\n🎉 YOLO person detection test PASSED!")
        print(f"\nNext step: Test CLIP costume classification on the cropped person images")

if __name__ == "__main__":
    test_yolo_detection()
