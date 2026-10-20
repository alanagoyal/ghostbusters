import plistlib
import unittest
from pathlib import Path

from backend.scripts.service_runner import redact
from scripts.setup_macos_service import configuration


class ServiceTests(unittest.TestCase):
    def test_credentials_are_redacted_from_native_errors(self):
        message = "Failed rtsp://user:secret@192.168.1.2/feed and https://u:p@host/path"
        self.assertEqual(
            redact(message),
            "Failed rtsp://[redacted]@192.168.1.2/feed and https://[redacted]@host/path",
        )

    def test_plist_handles_spaces_without_shell_parsing(self):
        root = Path("/Users/example/My Project")
        config = configuration(root, Path("/Users/example/Library/Logs/Ghostbusters"))
        result = plistlib.loads(plistlib.dumps(config))
        self.assertEqual(result["ProgramArguments"][0], str(root / ".venv/bin/python"))
        self.assertEqual(result["WorkingDirectory"], str(root))
        self.assertTrue(result["RunAtLoad"])
        self.assertTrue(result["KeepAlive"])
