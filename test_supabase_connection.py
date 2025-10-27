#!/usr/bin/env python3
"""
Test script to verify Supabase integration.
Checks database connection, storage, and all operations.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from dotenv import load_dotenv

from supabase_client import SupabaseClient

# Load environment variables
load_dotenv()


def create_test_image(filename: str = "test_detection.jpg") -> str:
    """Create a test image with a detection box drawn on it."""
    # Create a simple test image (640x480, blue background)
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img[:] = (200, 150, 100)  # BGR color

    # Draw a fake bounding box
    cv2.rectangle(img, (100, 150), (300, 450), (0, 255, 0), 2)
    cv2.putText(
        img,
        "Test Person 0.95",
        (100, 140),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2,
    )

    # Add timestamp
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(
        img,
        f"Test Detection - {timestamp_str}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2,
    )

    # Save image
    cv2.imwrite(filename, img)
    print(f"✅ Created test image: {filename}")
    return filename


def test_environment_variables():
    """Test that all required environment variables are set."""
    print("\n" + "=" * 60)
    print("TEST 1: Environment Variables")
    print("=" * 60)

    required_vars = ["SUPABASE_URL", "SUPABASE_KEY", "DEVICE_ID"]
    missing_vars = []

    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "KEY" in var:
                display_value = value[:10] + "..." + value[-4:] if len(value) > 14 else "***"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NOT SET")
            missing_vars.append(var)

    if missing_vars:
        print(f"\n❌ Missing environment variables: {', '.join(missing_vars)}")
        print("   Please update your .env file")
        return False

    print("\n✅ All environment variables configured")
    return True


def test_client_initialization():
    """Test Supabase client initialization."""
    print("\n" + "=" * 60)
    print("TEST 2: Supabase Client Initialization")
    print("=" * 60)

    try:
        client = SupabaseClient()
        print(f"✅ Client initialized successfully")
        print(f"   Device ID: {client.device_id}")
        print(f"   Supabase URL: {client.url}")
        print(f"   Bucket: {client.bucket_name}")
        return client
    except Exception as e:
        print(f"❌ Client initialization failed: {e}")
        return None


def test_database_insert(client: SupabaseClient):
    """Test inserting a detection record."""
    print("\n" + "=" * 60)
    print("TEST 3: Database Insert")
    print("=" * 60)

    try:
        test_timestamp = datetime.now()
        test_bbox = {"x1": 100, "y1": 150, "x2": 300, "y2": 450}

        result = client.insert_detection(
            timestamp=test_timestamp,
            confidence=0.95,
            bounding_box=test_bbox,
        )

        if result:
            print(f"✅ Detection record inserted successfully")
            print(f"   ID: {result['id']}")
            print(f"   Timestamp: {result['timestamp']}")
            print(f"   Confidence: {result['confidence']}")
            print(f"   Device: {result['device_id']}")
            return result["id"]
        else:
            print("❌ Insert returned no data")
            return None

    except Exception as e:
        print(f"❌ Database insert failed: {e}")
        return None


def test_database_query(client: SupabaseClient):
    """Test querying recent detections."""
    print("\n" + "=" * 60)
    print("TEST 4: Database Query")
    print("=" * 60)

    try:
        detections = client.get_recent_detections(limit=5)

        if detections:
            print(f"✅ Retrieved {len(detections)} recent detections")
            print("\n   Recent detections:")
            for i, det in enumerate(detections, 1):
                print(
                    f"   {i}. [{det['device_id']}] "
                    f"{det['timestamp'][:19]} - "
                    f"Confidence: {det['confidence']:.2f}"
                )
            return True
        else:
            print("⚠️  No detections found (database might be empty)")
            return True

    except Exception as e:
        print(f"❌ Database query failed: {e}")
        return False


def test_storage_upload(client: SupabaseClient):
    """Test uploading an image to storage."""
    print("\n" + "=" * 60)
    print("TEST 5: Storage Upload")
    print("=" * 60)

    # Create test image
    test_image = create_test_image()

    try:
        test_timestamp = datetime.now()
        public_url = client.upload_detection_image(test_image, test_timestamp)

        if public_url:
            print(f"✅ Image uploaded successfully")
            print(f"   Public URL: {public_url}")
            return public_url
        else:
            print("❌ Image upload failed (no URL returned)")
            return None

    except Exception as e:
        print(f"❌ Storage upload failed: {e}")
        return None
    finally:
        # Clean up test image
        if os.path.exists(test_image):
            os.remove(test_image)
            print(f"   Cleaned up local test image")


def test_complete_workflow(client: SupabaseClient):
    """Test the complete workflow: create image, upload, and insert record."""
    print("\n" + "=" * 60)
    print("TEST 6: Complete Workflow")
    print("=" * 60)

    # Create test image
    test_image = create_test_image("test_workflow.jpg")

    try:
        test_timestamp = datetime.now()
        test_bbox = {"x1": 100, "y1": 150, "x2": 300, "y2": 450}

        success = client.save_detection(
            image_path=test_image,
            timestamp=test_timestamp,
            confidence=0.92,
            bounding_box=test_bbox,
        )

        if success:
            print("✅ Complete workflow successful")
            return True
        else:
            print("❌ Complete workflow failed")
            return False

    except Exception as e:
        print(f"❌ Complete workflow failed: {e}")
        return False
    finally:
        # Clean up test image
        if os.path.exists(test_image):
            os.remove(test_image)
            print("   Cleaned up local test image")


def test_costume_classification_update(client: SupabaseClient, detection_id: str):
    """Test updating a detection with costume classification."""
    print("\n" + "=" * 60)
    print("TEST 7: Costume Classification Update")
    print("=" * 60)

    if not detection_id:
        print("⚠️  Skipping: No detection ID available")
        return False

    try:
        success = client.update_costume_classification(
            detection_id=detection_id,
            costume_classification="Test Superhero Costume",
            costume_confidence=0.88,
        )

        if success:
            print("✅ Costume classification updated successfully")
            print(f"   Detection ID: {detection_id}")
            print("   Classification: Test Superhero Costume")
            print("   Confidence: 0.88")
            return True
        else:
            print("❌ Update failed")
            return False

    except Exception as e:
        print(f"❌ Costume classification update failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("🧪 SUPABASE CONNECTION TEST SUITE")
    print("=" * 60)
    print("Testing Supabase integration for Person Detection MVP")
    print()

    # Track test results
    results = {}

    # Test 1: Environment variables
    results["env"] = test_environment_variables()
    if not results["env"]:
        print("\n❌ Cannot proceed without environment variables")
        print("   Please configure your .env file and try again")
        sys.exit(1)

    # Test 2: Client initialization
    client = test_client_initialization()
    results["client"] = client is not None
    if not client:
        print("\n❌ Cannot proceed without Supabase client")
        sys.exit(1)

    # Test 3: Database insert
    detection_id = test_database_insert(client)
    results["insert"] = detection_id is not None

    # Test 4: Database query
    results["query"] = test_database_query(client)

    # Test 5: Storage upload
    results["storage"] = test_storage_upload(client) is not None

    # Test 6: Complete workflow
    results["workflow"] = test_complete_workflow(client)

    # Test 7: Costume classification update (if we have a detection ID)
    results["classification"] = test_costume_classification_update(
        client, detection_id
    )

    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name.upper()}")

    print(f"\nTests passed: {passed}/{total}")

    if passed == total:
        print("\n✅ All tests passed! Supabase is ready for production.")
        print("\nNext steps:")
        print("1. Run detect_people.py to start detecting people")
        print("2. Check Supabase dashboard to see real-time detections")
        print("3. Build frontend dashboard to display detections")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
