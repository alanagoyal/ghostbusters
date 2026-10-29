import json
import unittest
from unittest.mock import patch

from backend.src.detector_heartbeat import DetectorHeartbeat, STATUS_PATH


class DetectorHeartbeatTests(unittest.TestCase):
    def setUp(self):
        self.client_patch = patch("backend.src.detector_heartbeat.create_client")
        self.client = self.client_patch.start()
        self.addCleanup(self.client_patch.stop)
        self.bucket = self.client.return_value.storage.from_.return_value
        self.clock_patch = patch("backend.src.detector_heartbeat.time.monotonic", return_value=0)
        self.clock = self.clock_patch.start()
        self.addCleanup(self.clock_patch.stop)
        self.heartbeat = DetectorHeartbeat("https://example.supabase.co", "private-key")

    def test_no_heartbeat_until_a_frame_then_throttled(self):
        self.bucket.upload.assert_not_called()
        self.heartbeat.report(True)
        self.clock.return_value = 14
        self.heartbeat.report(True)
        self.assertEqual(self.bucket.upload.call_count, 1)
        self.clock.return_value = 15
        self.heartbeat.report(True)
        self.assertEqual(self.bucket.upload.call_count, 2)
        path, payload = self.bucket.upload.call_args.args
        self.assertEqual(path, STATUS_PATH)
        self.assertEqual(set(json.loads(payload)), {"running", "updated_at"})
        self.assertTrue(json.loads(payload)["running"])

    def test_stop_and_recovery_bypass_throttle(self):
        self.heartbeat.report(True)
        self.heartbeat.report(False)
        self.assertFalse(json.loads(self.bucket.upload.call_args.args[1])["running"])
        self.heartbeat.report(True)
        self.assertEqual(self.bucket.upload.call_count, 3)

    @patch("builtins.print")
    def test_network_error_does_not_stop_capture_or_leak_details(self, output):
        self.bucket.upload.side_effect = RuntimeError("private-key")
        self.heartbeat.report(True)
        self.heartbeat.report(True)
        self.assertEqual(self.bucket.upload.call_count, 1)
        self.assertNotIn("private-key", str(output.call_args))
        self.clock.return_value = 15
        self.heartbeat.report(True)
        self.assertEqual(self.bucket.upload.call_count, 2)
