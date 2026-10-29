import unittest
from unittest.mock import Mock, patch

from backend.src.clients.supabase_client import SupabaseClient


class DetectorStatusTests(unittest.TestCase):
    def client(self):
        client = SupabaseClient.__new__(SupabaseClient)
        client.client = Mock()
        client.detector_session = "synthetic-session"
        client.last_detector_heartbeat = float("-inf")
        return client

    @patch("backend.src.clients.supabase_client.time.monotonic")
    def test_throttle_and_immediate_stop(self, clock):
        client = self.client()
        clock.side_effect = [0, 1, 10, 11]
        client.report_detector_running()
        client.report_detector_running()
        client.report_detector_running()
        self.assertEqual(client.client.rpc.call_count, 2)
        client.report_detector_running(False)
        client.client.rpc.assert_called_with("report_detector_heartbeat", {
            "session_id": "synthetic-session", "running": False,
        })

    @patch("backend.src.clients.supabase_client.time.monotonic")
    def test_reporting_failure_does_not_stop_detection_and_retries(self, clock):
        client = self.client()
        client.client.rpc.side_effect = RuntimeError("network unavailable")
        clock.side_effect = [0, 5, 10]
        for _ in range(3):
            client.report_detector_running()
        self.assertEqual(client.client.rpc.call_count, 2)
