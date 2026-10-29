import unittest
from datetime import datetime
from unittest.mock import Mock

import cv2
import numpy as np
from postgrest.exceptions import APIError
from storage3.exceptions import StorageApiError

from backend.src.clients.supabase_client import SupabaseClient
from backend.src.gallery_media import prepare_gallery_media


def synthetic_jpeg(width=1344, height=768):
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    frame[:, : width // 2] = (60, 120, 200)
    return cv2.imencode(".jpg", frame)[1].tobytes()


class UploadTests(unittest.TestCase):
    def test_cleanup_requires_image_and_record_success(self):
        for image, record, expected in [
            (None, {"id": "test"}, False),
            ("https://example.test/image", None, False),
            ("https://example.test/image", {"id": "test"}, True),
        ]:
            with self.subTest(image=image, record=record):
                client = SupabaseClient.__new__(SupabaseClient)
                client.upload_detection_media = Mock(
                    return_value={"image_url": image} if image else None
                )
                client.insert_detection = Mock(return_value=record)
                self.assertEqual(
                    client.save_detection("unused", datetime.now(), 0.9, {}), expected
                )

    def client(self, private=True):
        client = SupabaseClient.__new__(SupabaseClient)
        client.private_gallery = private
        client.device_id = "synthetic"
        client.bucket_name = "detection-images"
        client.client = Mock()
        client.client.storage.from_.return_value.get_public_url.side_effect = (
            lambda path: "https://example.test/" + path
        )
        return client

    def test_thumbnail_dimensions_placeholder_and_content_addressing(self):
        media = prepare_gallery_media(synthetic_jpeg())
        thumbnail = cv2.imdecode(
            np.frombuffer(media.thumbnail, dtype=np.uint8), cv2.IMREAD_COLOR
        )
        self.assertEqual(thumbnail.shape[:2], (206, 360))
        self.assertEqual((media.width, media.height), (1344, 768))
        self.assertLess(len(media.thumbnail), len(media.original))
        self.assertLess(len(media.placeholder), 2048)
        self.assertTrue(media.placeholder.startswith("data:image/webp;base64,"))
        self.assertEqual(media.digest, prepare_gallery_media(media.original).digest)
        self.assertNotEqual(
            media.digest, prepare_gallery_media(synthetic_jpeg(64, 64)).digest
        )

    def test_portrait_and_small_images_do_not_upscale(self):
        import base64

        for width, height in ((64, 64), (360, 1000)):
            media = prepare_gallery_media(synthetic_jpeg(width, height))
            tiny = cv2.imdecode(
                np.frombuffer(
                    base64.b64decode(media.placeholder.split(",")[1]), dtype=np.uint8
                ),
                cv2.IMREAD_COLOR,
            )
            self.assertLessEqual(max(tiny.shape[:2]), 10)
            thumb = cv2.imdecode(
                np.frombuffer(media.thumbnail, dtype=np.uint8), cv2.IMREAD_COLOR
            )
            self.assertLessEqual(thumb.shape[1], width)

    def test_private_variants_are_ready_before_record_and_never_get_public_urls(self):
        client = self.client()
        result = client.upload_detection_bytes(synthetic_jpeg())
        bucket = client.client.storage.from_.return_value
        self.assertEqual(
            [
                call.kwargs["file_options"]["content-type"]
                for call in bucket.upload.call_args_list
            ],
            ["image/webp", "image/jpeg"],
        )
        self.assertTrue(result["image_url"].endswith("/original.jpg"))
        self.assertTrue(result["thumbnail_url"].endswith("/thumbnail.webp"))
        for call in bucket.upload.call_args_list:
            self.assertEqual(call.kwargs["file_options"]["upsert"], "false")
            self.assertEqual(call.kwargs["file_options"]["cache-control"], "0")
        bucket.get_public_url.assert_not_called()

    def test_duplicate_content_is_success_but_failed_variant_is_not_published(self):
        client = self.client()
        bucket = client.client.storage.from_.return_value
        bucket.upload.side_effect = StorageApiError("exists", "Duplicate", 409)
        self.assertIsNotNone(client.upload_detection_bytes(synthetic_jpeg()))
        bucket.upload.side_effect = StorageApiError("denied", "AccessDenied", 403)
        self.assertIsNone(client.upload_detection_bytes(synthetic_jpeg()))

    def test_legacy_schema_fallback_is_narrow_and_does_not_retry_denial(self):
        client = self.client()
        write = Mock()
        write.return_value.execute.side_effect = [
            APIError(
                {
                    "code": "PGRST204",
                    "message": "Missing thumbnail_url column",
                    "details": None,
                    "hint": None,
                }
            ),
            Mock(data=[{"id": "test"}]),
        ]
        result = client._write_gallery_record(
            {"image_url": "original"}, {"thumbnail_url": "thumb"}, write
        )
        self.assertTrue(result.data)
        self.assertEqual(write.call_args_list[1].args[0], {"image_url": "original"})
        client = self.client()
        write.reset_mock()
        write.return_value.execute.side_effect = APIError(
            {"code": "42501", "message": "denied", "details": None, "hint": None}
        )
        with self.assertRaises(APIError):
            client._write_gallery_record(
                {"image_url": "original"}, {"thumbnail_url": "thumb"}, write
            )
        self.assertEqual(write.call_count, 1)

    def test_backfill_does_not_overwrite_a_concurrently_changed_image(self):
        client = self.client()
        client._media_columns = False
        query = client.client.table.return_value.update.return_value
        filtered = query.eq.return_value.eq.return_value
        filtered.execute.return_value.data = []
        self.assertFalse(
            client.update_detection_media("id", "old-image", {"image_url": "new-image"})
        )
        client.client.table.return_value.update.return_value.eq.assert_called_with(
            "id", "id"
        )
        client.client.table.return_value.update.return_value.eq.return_value.eq.assert_called_with(
            "image_url", "old-image"
        )
