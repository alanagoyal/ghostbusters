import ast
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from backend.src.publishing import publishing_enabled


class PublishingTests(unittest.TestCase):
    def test_capture_skips_upload_and_retains_rehearsal_photo(self):
        # Exercise the actual upload/cleanup block without starting the camera.
        main = Path(__file__).resolve().parents[2] / "scripts/main.py"
        tree = ast.parse(main.read_text())
        block = next(
            node.body
            for node in ast.walk(tree)
            if isinstance(node, ast.If)
            and any(
                isinstance(child, ast.Assign)
                and any(
                    isinstance(target, ast.Name) and target.id == "uploads_succeeded"
                    for target in child.targets
                )
                for child in node.body
            )
        )
        start = next(
            i
            for i, node in enumerate(block)
            if isinstance(node, ast.Assign)
            and any(
                isinstance(t, ast.Name) and t.id == "uploads_succeeded"
                for t in node.targets
            )
        )
        code = compile(
            ast.Module(body=block[start:], type_ignores=[]), str(main), "exec"
        )
        with tempfile.TemporaryDirectory() as directory:
            photo = Path(directory) / "synthetic.jpg"
            for enabled in (False, True):
                photo.write_bytes(b"synthetic")
                client = Mock()
                client.save_detection.return_value = True
                with patch("builtins.print"):
                    exec(
                        code,
                        {
                            "publish_capture": enabled,
                            "supabase_client": client,
                            "detected_people": [
                                {"confidence": 0.9, "bounding_box": {}}
                            ],
                            "filename": str(photo),
                            "detection_timestamp": None,
                            "os": os,
                        },
                    )
                self.assertEqual(client.save_detection.call_count, int(enabled))
                self.assertEqual(photo.exists(), not enabled)

    def test_rehearsal_toggle_is_reloaded_without_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            with patch.dict(os.environ, {"PUBLISH_DETECTIONS": "false"}):
                path.write_text("PUBLISH_DETECTIONS=false\n")
                self.assertFalse(publishing_enabled(path))
                path.write_text("PUBLISH_DETECTIONS=true\n")
                self.assertTrue(publishing_enabled(path))
                path.write_text("PUBLISH_DETECTIONS=false\n")
                self.assertFalse(publishing_enabled(path))

    def test_unset_preserves_legacy_behavior_and_invalid_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            with patch.dict(os.environ, {}, clear=True):
                self.assertTrue(publishing_enabled(path))
                for value in ("false", "", "yes", "tru", "${OTHER}"):
                    path.write_text(f"PUBLISH_DETECTIONS={value}\n")
                    self.assertFalse(publishing_enabled(path))
                path.write_text("PUBLISH_DETECTIONS\n")
                self.assertFalse(publishing_enabled(path))

    def test_unreadable_settings_fail_closed(self):
        with patch("backend.src.publishing.dotenv_values", side_effect=OSError):
            self.assertFalse(publishing_enabled(Path(".env")))
