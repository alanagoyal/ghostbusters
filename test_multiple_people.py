#!/usr/bin/env python3
"""
Test script to verify multiple people detection logic.
This simulates the core logic without requiring RTSP connection.
"""

from datetime import datetime


def simulate_detection(num_people):
    """Simulate detection of multiple people."""

    # Simulate YOLO results
    detected_people = []
    for i in range(num_people):
        detected_people.append({
            "confidence": 0.85 + (i * 0.05),  # Varying confidence
            "bounding_box": {
                "x1": 100 + (i * 150),
                "y1": 100,
                "x2": 200 + (i * 150),
                "y2": 400,
            }
        })

    num_people = len(detected_people)
    detection_count = 0
    detection_timestamp = datetime.now()
    timestamp_str = detection_timestamp.strftime("%Y%m%d_%H%M%S")

    # Simulate the new logic
    full_frame_filename = f"detection_{timestamp_str}.jpg"

    if num_people == 1:
        print(f"👤 Person detected!")
    else:
        print(f"👥 {num_people} people detected!")
    print(f"   Full frame would be saved as: {full_frame_filename}")

    # Simulate database insertion for each person
    for idx, person in enumerate(detected_people, 1):
        if num_people > 1:
            person_filename = f"detection_{timestamp_str}_person{idx}.jpg"
            print(f"   Person {idx}/{num_people} would be saved as: {person_filename}")
        else:
            person_filename = full_frame_filename
            print(f"   Single person uses full frame: {person_filename}")

        print(f"      - Confidence: {person['confidence']:.2f}")
        print(f"      - Bounding box: {person['bounding_box']}")
        print(f"      - Would insert to database with timestamp: {detection_timestamp.isoformat()}")

    return num_people


if __name__ == "__main__":
    print("🧪 Testing multiple people detection logic\n")

    print("=" * 60)
    print("Test 1: Single person")
    print("=" * 60)
    count1 = simulate_detection(1)
    print(f"✅ Result: {count1} database entry would be created\n")

    print("=" * 60)
    print("Test 2: Three people (like three kids in costumes)")
    print("=" * 60)
    count2 = simulate_detection(3)
    print(f"✅ Result: {count2} database entries would be created\n")

    print("=" * 60)
    print("Test 3: Five people")
    print("=" * 60)
    count3 = simulate_detection(5)
    print(f"✅ Result: {count3} database entries would be created\n")

    total = count1 + count2 + count3
    print("=" * 60)
    print(f"📊 Summary: {total} total database entries would be created")
    print("   (Previously, only 3 entries would have been created - one per frame)")
    print("=" * 60)
