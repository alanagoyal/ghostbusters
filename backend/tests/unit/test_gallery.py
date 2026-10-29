import unittest
from unittest.mock import Mock

from backend.scripts.gallery import backfill, object_path


class GalleryBackfillTests(unittest.TestCase):
    def client(self, rows):
        client = Mock()
        client.url = "https://test.supabase.co"
        client.bucket_name = "detection-images"
        query = client.client.table.return_value.select.return_value
        ordered = query.order.return_value.order.return_value
        ordered.limit.return_value.execute.return_value.data = rows
        client.upload_detection_bytes.return_value = {"image_url": "versioned-original"}
        client.update_detection_media.return_value = True
        return client

    def test_downloads_are_scoped_to_this_project_bucket(self):
        base = "https://test.supabase.co"
        self.assertEqual(
            object_path(
                base + "/storage/v1/object/public/detection-images/device/photo.jpg",
                base,
            ),
            "device/photo.jpg",
        )
        for path in (
            "../secret",
            "/absolute",
            "device\\secret",
            "device/photo?token=x",
            "https://other.test/photo.jpg",
            base + "/storage/v1/object/public/other/photo.jpg",
            base + "/storage/v1/object/public/detection-images/device%2F..%2Fsecret",
        ):
            self.assertIsNone(object_path(path, base))

    def test_dry_run_never_downloads_uploads_or_updates_records(self):
        client = self.client([{"id": "a", "image_url": "device/photo.jpg"}])
        result = backfill(client, dry_run=True)
        self.assertEqual(result["updated"], 1)
        client.client.storage.from_.assert_not_called()
        client.upload_detection_bytes.assert_not_called()
        client.update_detection_media.assert_not_called()

    def test_shared_scenes_upload_once_and_reruns_skip_versioned_paths(self):
        client = self.client(
            [
                {"id": "a", "image_url": "device/photo.jpg"},
                {"id": "b", "image_url": "device/photo.jpg"},
                {
                    "id": "c",
                    "image_url": "device/gallery-v1/" + "a" * 64 + "/original.jpg",
                },
            ]
        )
        result = backfill(client)
        self.assertEqual(result["updated"], 2)
        self.assertEqual(result["skipped"], 1)
        client.client.storage.from_.return_value.download.assert_called_once_with(
            "device/photo.jpg"
        )
        client.upload_detection_bytes.assert_called_once()
        self.assertEqual(client.update_detection_media.call_count, 2)
