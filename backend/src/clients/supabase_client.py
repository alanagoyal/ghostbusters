#!/usr/bin/env python3
"""
Supabase client for person detection system.
Handles database operations and storage uploads.
"""

import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from postgrest.exceptions import APIError
from storage3.exceptions import StorageApiError

from backend.src.gallery_media import prepare_gallery_media
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
        # Use existing HOSTNAME variable, fall back to DEVICE_ID for compatibility
        self.device_id = os.getenv("HOSTNAME") or os.getenv(
            "DEVICE_ID", "unknown-device"
        )

        if not self.url or not self.key:
            raise ValueError(
                "Missing NEXT_PUBLIC_SUPABASE_URL or "
                "SUPABASE_SERVICE_ROLE_KEY environment variables"
            )

        self.client: Client = create_client(self.url, self.key)
        self.bucket_name = "detection-images"
        self.private_gallery = os.getenv("GALLERY_ACCESS") == "private"

    def upload_detection_image(
        self, image_path: str, timestamp: datetime
    ) -> str | None:
        """
        Upload detection image to Supabase storage.

        Args:
            image_path: Local path to image file
            timestamp: Timestamp of detection

        Returns:
            Object path (private) or legacy public URL; None if upload fails
        """
        media = self.upload_detection_media(image_path)
        return media["image_url"] if media else None

    def upload_detection_media(self, image_path: str) -> dict | None:
        """Upload immutable variants before publishing the detection record.

        Input is the saved, privacy-processed scene, never the classification crop.
        Content-addressed names also make retries and multi-person scenes idempotent.
        """
        try:
            return self.upload_detection_bytes(Path(image_path).read_bytes())
        except OSError:
            print("❌ Could not read saved detection image")
            return None

    def upload_detection_bytes(self, image: bytes) -> dict | None:
        """Upload an existing processed scene without creating a temporary photo."""
        try:
            media = prepare_gallery_media(image)
            prefix = f"{self.device_id}/gallery-v1/{media.digest}"
            bucket = self.client.storage.from_(self.bucket_name)
            references = {}
            for field, name, content, kind in (
                ("thumbnail_url", "thumbnail.webp", media.thumbnail, "image/webp"),
                ("image_url", "original.jpg", media.original, "image/jpeg"),
            ):
                path = f"{prefix}/{name}"
                try:
                    bucket.upload(
                        path=path,
                        file=content,
                        file_options={
                            "content-type": kind,
                            # Private responses must not outlive signed links.
                            "cache-control": "0" if self.private_gallery else "3600",
                            "upsert": "false",
                        },
                    )
                except StorageApiError as error:
                    # Identical content already uploaded by a retry or another person.
                    if error.status != 409 and error.code not in (
                        "Duplicate",
                        "ResourceAlreadyExists",
                    ):
                        raise
                references[field] = (
                    path if self.private_gallery else bucket.get_public_url(path)
                )
            return {
                **references,
                "image_width": media.width,
                "image_height": media.height,
                "image_placeholder": media.placeholder,
            }
        except Exception:
            print("❌ Could not prepare or upload gallery images")
            return None

    def insert_detection(
        self,
        timestamp: datetime,
        confidence: float,
        bounding_box: dict,
        image_url: str | None = None,
        costume_classification: str | None = None,
        costume_description: str | None = None,
        costume_confidence: float | None = None,
        media: dict | None = None,
    ) -> dict | None:
        """
        Insert person detection record into database.

        Args:
            timestamp: When person was detected
            confidence: YOLO confidence score (0.0-1.0)
            bounding_box: Dict with x1, y1, x2, y2 coordinates
            image_url: Storage object path or legacy public URL (optional)
            costume_classification: Optional AI costume type
            costume_description: Detailed costume description (optional)
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
            if costume_description:
                data["costume_description"] = costume_description
            if costume_confidence is not None:
                data["costume_confidence"] = costume_confidence

            response = self._write_gallery_record(
                data,
                media,
                lambda values: self.client.table("person_detections").insert(values),
            )

            if response.data:
                return response.data[0]
            return None

        except Exception:
            print("❌ Error inserting detection")
            return None

    def _write_gallery_record(self, data, media, write):
        fields = {
            key: value
            for key, value in (media or {}).items()
            if key
            in (
                "thumbnail_url",
                "image_width",
                "image_height",
                "image_placeholder",
            )
        }
        if fields and getattr(self, "_media_columns", True):
            try:
                return write({**data, **fields}).execute()
            except APIError as error:
                # Legacy databases can derive gallery-v1 thumbnail paths until the
                # additive migration is applied. Never retry an authorization failure.
                if error.code not in ("PGRST204", "42703") or not any(
                    key in error.message for key in fields
                ):
                    raise
                self._media_columns = False
        return write(data).execute()

    def update_detection_media(
        self, detection_id: str, expected_url: str, media: dict
    ) -> bool:
        """Backfill only if this row still references the scene we downloaded."""
        try:
            response = self._write_gallery_record(
                {"image_url": media["image_url"]},
                media,
                lambda values: self.client.table("person_detections")
                .update(values)
                .eq("id", detection_id)
                .eq("image_url", expected_url),
            )
            return bool(response.data)
        except Exception:
            print("❌ Could not update gallery image metadata")
            return False

    def save_detection(
        self,
        image_path: str,
        timestamp: datetime,
        confidence: float,
        bounding_box: dict,
        costume_classification: str | None = None,
        costume_description: str | None = None,
        costume_confidence: float | None = None,
    ) -> bool:
        """
        Complete workflow: upload image and insert detection record.

        Args:
            image_path: Local path to detection image
            timestamp: When person was detected
            confidence: YOLO confidence score
            bounding_box: Dict with x1, y1, x2, y2 coordinates
            costume_classification: Optional AI costume type
            costume_description: Detailed costume description (optional)
            costume_confidence: AI classification confidence (optional)

        Returns:
            True if successful, False otherwise
        """
        # Upload image
        media = self.upload_detection_media(image_path)
        image_url = media["image_url"] if media else None

        if not image_url:
            print("⚠️  Image upload failed, saving detection without image URL")

        # Insert detection record
        result = self.insert_detection(
            timestamp=timestamp,
            confidence=confidence,
            bounding_box=bounding_box,
            image_url=image_url,
            costume_classification=costume_classification,
            costume_description=costume_description,
            costume_confidence=costume_confidence,
            media=media,
        )

        if result:
            print(f"✅ Detection saved to Supabase (ID: {result['id']})")
            return bool(image_url)
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
        except Exception:
            print("❌ Error retrieving detections")
            return []

    def update_costume_classification(
        self,
        detection_id: str,
        costume_classification: str,
        costume_description: str,
        costume_confidence: float,
    ) -> bool:
        """
        Update detection record with costume classification.

        Args:
            detection_id: UUID of detection record
            costume_classification: AI costume type (e.g., "witch", "skeleton")
            costume_description: Detailed costume description
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
                        "costume_description": costume_description,
                        "costume_confidence": costume_confidence,
                    }
                )
                .eq("id", detection_id)
                .execute()
            )
            return bool(response.data)
        except Exception:
            print("❌ Error updating costume classification")
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
    print("   Supabase configured")
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
