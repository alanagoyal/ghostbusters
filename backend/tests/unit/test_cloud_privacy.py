import contextlib
import io
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import requests

from backend.scripts import projects
from backend.scripts.cli import save_env
from backend.src.clients.supabase_client import SupabaseClient
from backend.src.clients.vision import create_vision_client, request_options


class CloudPrivacyTests(unittest.TestCase):
    def test_unsuitable_models_fail_before_request(self):
        for model in (
            "nvidia/nemotron-3.5-super-vl:free",
            "openrouter/free",
            "openrouter/auto",
            "",
        ):
            with self.subTest(model=model), self.assertRaises(ValueError):
                request_options(
                    {"INFERENCE_PROVIDER": "openrouter", "OPENROUTER_MODEL": model}
                )

    def test_every_openrouter_request_preserves_privacy_no_fallback(self):
        with patch.dict(
            os.environ,
            {
                "INFERENCE_PROVIDER": "openrouter",
                "OPENROUTER_API_KEY": "test",
                "OPENROUTER_MODEL": "openai/gpt-4.1-mini",
            },
            clear=True,
        ):
            client = create_vision_client()
        response = Mock()
        response.raise_for_status.side_effect = requests.HTTPError(
            "sensitive provider response"
        )
        client.session.post = Mock(return_value=response)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(client.classify_costume(b"synthetic"), (None, None, None))
            self.assertFalse(client.test_connection())
        self.assertNotIn("sensitive", output.getvalue())
        self.assertEqual(client.session.post.call_count, 2)
        for call in client.session.post.call_args_list:
            self.assertEqual(
                call.kwargs["json"]["provider"],
                {"data_collection": "deny", "zdr": True},
            )
        self.assertEqual(request_options({}), {})  # existing Baseten unchanged

    def test_private_upload_never_publishes_url(self):
        client = SupabaseClient.__new__(SupabaseClient)
        client.private_gallery = True
        client.device_id = "test"
        client.bucket_name = "detection-images"
        client.client = Mock()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "synthetic.jpg"
            path.write_bytes(b"synthetic")
            result = client.upload_detection_image(str(path), datetime(2026, 10, 28))
        self.assertEqual(result, "test/20261028_000000.jpg")
        client.client.storage.from_.return_value.get_public_url.assert_not_called()

    def test_grant_viewer_uuid_validation_and_no_secret_arguments(self):
        with patch.object(projects, "run_sql") as sql:
            with self.assertRaises(ValueError):
                projects.grant_viewer(
                    Path("source"), "'; drop table person_detections;--"
                )
            sql.assert_not_called()
            projects.grant_viewer(
                Path("source"), "00000000-0000-0000-0000-000000000001", True
            )
            self.assertIn(
                "delete from public.gallery_viewers", sql.call_args.kwargs["statement"]
            )

    def test_add_viewer_preserves_existing_account_and_creates_unconfirmed_user(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            save_env(
                root / ".env",
                {
                    "GALLERY_ACCESS": "private",
                    "NEXT_PUBLIC_SUPABASE_URL": "https://example.supabase.co",
                    "SUPABASE_SERVICE_ROLE_KEY": "sb_secret_test",
                },
            )
            client = Mock()
            existing = Mock(email="owner@example.com", id="user-id")
            client.auth.admin.list_users.return_value = [existing]
            with patch("supabase.create_client", return_value=client):
                projects.add_viewer("owner@example.com", root=root)
                client.auth.admin.create_user.assert_not_called()
                client.table.return_value.upsert.assert_called_with(
                    {"user_id": "user-id"}
                )
                client.auth.admin.list_users.return_value = []
                client.auth.admin.create_user.return_value.user = existing
                projects.add_viewer("owner@example.com", root=root)
                client.auth.admin.create_user.assert_called_once_with(
                    {"email": "owner@example.com", "email_confirm": False}
                )
                client.auth.admin.invite_user_by_email.assert_not_called()
