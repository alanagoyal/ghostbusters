import unittest
from datetime import datetime
from unittest.mock import Mock

from backend.src.clients.supabase_client import SupabaseClient


class UploadTests(unittest.TestCase):
    def test_cleanup_requires_image_and_record_success(self):
        for image, record, expected in [
            (None, {"id": "test"}, False),
            ("https://example.test/image", None, False),
            ("https://example.test/image", {"id": "test"}, True),
        ]:
            with self.subTest(image=image, record=record):
                client = SupabaseClient.__new__(SupabaseClient)
                client.upload_detection_image = Mock(return_value=image)
                client.insert_detection = Mock(return_value=record)
                self.assertEqual(
                    client.save_detection("unused", datetime.now(), 0.9, {}), expected
                )
