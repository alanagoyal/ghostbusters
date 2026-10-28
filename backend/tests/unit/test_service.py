import contextlib
import io
import plistlib
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from backend.scripts import service_runner
from backend.scripts.service_runner import redact
from scripts.setup_macos_service import configuration


class ServiceTests(unittest.TestCase):
    def test_credentials_are_redacted_from_native_errors(self):
        message = "Failed rtsp://user:secret@192.168.1.2/feed and https://u:p@host/path"
        self.assertEqual(
            redact(message),
            "Failed [redacted-url] and [redacted-url]",
        )

    def test_foreground_redacts_native_child_output(self):
        child = Mock()
        child.stdout = ["native error rtsp://camera:secret@192.168.1.2/feed\n"]
        child.wait.return_value = 0
        child.poll.return_value = 0
        output = io.StringIO()
        with (
            contextlib.redirect_stdout(output),
            patch.object(service_runner.subprocess, "Popen", return_value=child),
            patch.object(service_runner.signal, "signal"),
            patch.object(service_runner.sys, "platform", "linux"),
        ):
            self.assertEqual(service_runner.main(foreground=True), 0)
        self.assertIn("[redacted-url]", output.getvalue())
        self.assertNotIn("192.168", output.getvalue())
        self.assertNotIn("secret", output.getvalue())

    def test_plist_handles_spaces_without_shell_parsing(self):
        root = Path("/Users/example/My Project")
        config = configuration(root, Path("/Users/example/Library/Logs/Ghostbusters"))
        result = plistlib.loads(plistlib.dumps(config))
        self.assertEqual(result["ProgramArguments"][0], str(root / ".venv/bin/python"))
        self.assertEqual(result["WorkingDirectory"], str(root))
        self.assertTrue(result["RunAtLoad"])
        self.assertTrue(result["KeepAlive"])
