#!/usr/bin/env python3
"""
Supabase client for person detection system.
Handles database operations and storage uploads.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from supabase import Client, create_client

# Load environment variables
load_dotenv()


class SupabaseClient:
    """Client for interacting with Supabase database and storage."""

    def __init__(self):
        """Initialize Supabase client with credentials from environment."""
        # Support both NEXT_PUBLIC_SUPABASE_URL and SUPABASE_URL for flexibility
        self.url = os.getenv("NEXT_PUBLIC_SUPABASE_URL") or os.getenv("SUPABASE_URL")
        # Use service role key for backend operations (full access)
        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
        self.device_id = os.getenv("DEVICE_ID", "unknown-device")

        if not self.url or not self.key:
            raise ValueError(
                "Missing NEXT_PUBLIC_SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables"
            )

        self.client: Client = create_client(self.url, self.key)
        self.bucket_name = "detection-images"

    def upload_detection_image(
        self, image_path: str, timestamp: datetime
    ) -> Optional[str]:
        """
        Upload detection image to Supabase storage.

        Args:
            image_path: Local path to image file
            timestamp: Timestamp of detection

        Returns:
            Public URL of uploaded image, or None if upload fails
        """
        try:
            # Generate storage path: device_id/YYYYMMDD_HHMMSS.jpg
            filename = timestamp.strftime("%Y%m%d_%H%M%S.jpg")
            storage_path = f"{self.device_id}/{filename}"

            # Read image file
            with open(image_path, "rb") as f:
                image_data = f.read()

            # Upload to Supabase storage
            self.client.storage.from_(self.bucket_name).upload(
                path=storage_path,
                file=image_data,
                file_options={"content-type": "image/jpeg"},
            )

            # Get public URL
            public_url = self.client.storage.from_(self.bucket_name).get_public_url(
                storage_path
            )

            return public_url

        except Exception as e:
            print(f"❌ Error uploading image: {e}")
            return None

    def insert_detection(
        self,
        timestamp: datetime,
        confidence: float,
        bounding_box: dict,
        image_url: Optional[str] = None,
        costume_classification: Optional[str] = None,
        costume_confidence: Optional[float] = None,
    ) -> Optional[dict]:
        """
        Insert person detection record into database.

        Args:
            timestamp: When person was detected
            confidence: YOLO confidence score (0.0-1.0)
            bounding_box: Dict with x1, y1, x2, y2 coordinates
            image_url: URL to uploaded image (optional)
            costume_classification: AI costume description (optional)
            costume_confidence: AI classification confidence (optional)

        Returns:
            Inserted record data, or None if insert fails
        """
        try:
            data = {
                "timestamp": timestamp.isoformat(),
                "confidence": confidence,
                "bounding_box": bounding_box,
                "device_id": self.device_id,
            }

            # Add optional fields if provided
            if image_url:
                data["image_url"] = image_url
            if costume_classification:
                data["costume_classification"] = costume_classification
            if costume_confidence is not None:
                data["costume_confidence"] = costume_confidence

            # Insert into database
            response = (
                self.client.table("person_detections").insert(data).execute()
            )

            if response.data:
                return response.data[0]
            return None

        except Exception as e:
            print(f"❌ Error inserting detection: {e}")
            return None

    def save_detection(
        self,
        image_path: str,
        timestamp: datetime,
        confidence: float,
        bounding_box: dict,
        costume_classification: Optional[str] = None,
        costume_confidence: Optional[float] = None,
    ) -> bool:
        """
        Complete workflow: upload image and insert detection record.

        Args:
            image_path: Local path to detection image
            timestamp: When person was detected
            confidence: YOLO confidence score
            bounding_box: Dict with x1, y1, x2, y2 coordinates
            costume_classification: AI costume description (optional)
            costume_confidence: AI classification confidence (optional)

        Returns:
            True if successful, False otherwise
        """
        # Upload image
        image_url = self.upload_detection_image(image_path, timestamp)

        if not image_url:
            print("⚠️  Image upload failed, saving detection without image URL")

        # Insert detection record
        result = self.insert_detection(
            timestamp=timestamp,
            confidence=confidence,
            bounding_box=bounding_box,
            image_url=image_url,
            costume_classification=costume_classification,
            costume_confidence=costume_confidence,
        )

        if result:
            print(f"✅ Detection saved to Supabase (ID: {result['id']})")
            if image_url:
                print(f"   Image URL: {image_url}")
            return True
        else:
            print("❌ Failed to save detection to Supabase")
            return False

    def get_recent_detections(self, limit: int = 10) -> list:
        """
        Retrieve recent person detections.

        Args:
            limit: Maximum number of records to retrieve

        Returns:
            List of detection records
        """
        try:
            response = (
                self.client.table("person_detections")
                .select("*")
                .order("timestamp", desc=True)
                .limit(limit)
                .execute()
            )
            return response.data
        except Exception as e:
            print(f"❌ Error retrieving detections: {e}")
            return []

    def update_costume_classification(
        self,
        detection_id: str,
        costume_classification: str,
        costume_confidence: float,
    ) -> bool:
        """
        Update detection record with costume classification.

        Args:
            detection_id: UUID of detection record
            costume_classification: AI costume description
            costume_confidence: AI classification confidence

        Returns:
            True if successful, False otherwise
        """
        try:
            response = (
                self.client.table("person_detections")
                .update(
                    {
                        "costume_classification": costume_classification,
                        "costume_confidence": costume_confidence,
                    }
                )
                .eq("id", detection_id)
                .execute()
            )
            return bool(response.data)
        except Exception as e:
            print(f"❌ Error updating costume classification: {e}")
            return False


# Example usage
if __name__ == "__main__":
    # Initialize client
    client = SupabaseClient()

    # Test detection data
    test_timestamp = datetime.now()
    test_bbox = {"x1": 100, "y1": 150, "x2": 300, "y2": 450}

    print("🧪 Testing Supabase client...")
    print(f"   Device ID: {client.device_id}")
    print(f"   Supabase URL: {client.url}")
    print()

    # Insert test detection (without image)
    result = client.insert_detection(
        timestamp=test_timestamp,
        confidence=0.95,
        bounding_box=test_bbox,
    )

    if result:
        print("✅ Test detection inserted successfully!")
        print(f"   Detection ID: {result['id']}")
        print()

        # Retrieve recent detections
        print("📊 Recent detections:")
        recent = client.get_recent_detections(limit=5)
        for detection in recent:
            print(f"   - {detection['timestamp']}: {detection['confidence']:.2f}")
    else:
        print("❌ Test detection failed")
