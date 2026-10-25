"""Identity-safe rediscovery and continuous probe regressions; no real devices."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np

from backend.src.local import cameras, discovery, probe


class DiscoveryTests(unittest.TestCase):
    def test_missing_or_ambiguous_identity_cannot_refresh(self):
        with patch.object(cameras, "discover") as discover:
            with self.assertRaisesRegex(cameras.CameraError, "missing_device_identity"):
                cameras.refresh({"kind": "onvif", "identity": ""})
            discover.assert_not_called()
            discover.return_value = [
                {"identity": "same", "host": host}
                for host in ("192.168.1.10", "192.168.1.99")
            ]
            with self.assertRaisesRegex(
                cameras.CameraError, "ambiguous_device_identity"
            ):
                cameras.refresh({"kind": "onvif", "identity": "same"})

    def test_bonjour_and_arp_merge_without_losing_selected_identity(self):
        bonjour = {
            "kind": "doorbird",
            "identity": "bonjour",
            "host": "192.168.1.10",
            "port": 80,
        }
        arp = {**bonjour, "identity": "mac:selected"}
        other = {**arp, "identity": "mac:other", "host": "192.168.1.20"}
        with (
            patch.object(discovery, "discover_doorbird", return_value=[bonjour]),
            patch.object(discovery, "doorbird_neighbors", return_value=[arp, other]),
        ):
            found = discovery.discover("doorbird")
        self.assertEqual(len(found), 2)
        with patch.object(cameras, "discover", return_value=found):
            refreshed = cameras.refresh({**arp, "host": "192.168.1.9"})
        self.assertEqual(refreshed["host"], "192.168.1.10")
        self.assertEqual(refreshed["identity"], "mac:selected")

    def test_onvif_rejects_missing_and_duplicate_endpoint_across_hosts(self):
        def packet(identity, host):
            endpoint = (
                f"<a:EndpointReference><a:Address>{identity}</a:Address></a:EndpointReference>"
                if identity
                else ""
            )
            data = (
                '<Envelope xmlns:a="urn:addressing" xmlns:d="urn:discovery">'
                "<a:Address>unrelated-header-address</a:Address>"
                f"{endpoint}<d:XAddrs>http://{host}/onvif/device_service</d:XAddrs>"
                "</Envelope>"
            ).encode()
            return data, (host, 3702)

        responses = iter(
            [
                packet("", "192.168.1.1"),
                packet("urn:duplicate", "192.168.1.2"),
                packet("urn:duplicate", "192.168.1.3"),
                packet("urn:unique", "192.168.1.4"),
            ]
        )

        def receive(_size):
            try:
                return next(responses)
            except StopIteration:
                raise TimeoutError from None

        sock = Mock()
        sock.recvfrom.side_effect = receive
        clock = iter(i / 10 for i in range(30))
        with (
            patch.object(discovery.socket, "socket") as factory,
            patch.object(discovery.time, "monotonic", side_effect=lambda: next(clock)),
        ):
            factory.return_value.__enter__.return_value = sock
            found = discovery.discover_onvif(seconds=1)
        self.assertEqual([item["identity"] for item in found], ["urn:unique"])


class ProbeTests(unittest.TestCase):
    def run_probe(self, times):
        frame = np.zeros((10, 20, 3), dtype=np.uint8)
        output = io.StringIO()
        with (
            tempfile.TemporaryDirectory() as temporary,
            patch.object(probe, "load", return_value={"camera": {"kind": "fixture"}}),
            patch.object(probe, "refresh", side_effect=lambda camera: camera),
            patch.object(probe, "home", return_value=Path(temporary)),
            patch.object(probe, "stream", return_value=iter([frame, frame])),
            patch.object(probe.sys, "argv", ["probe", "15", "0"]),
            patch.object(probe.time, "monotonic", side_effect=times),
            contextlib.redirect_stdout(output),
        ):
            result = probe.main()
        return result, json.loads(output.getvalue())

    def test_two_frames_then_eof_is_not_continuous_success(self):
        code, result = self.run_probe([0, 0.1, 0.2, 0.3])
        self.assertEqual(code, 2)
        self.assertEqual(result["reason"], "stream_ended_early")
        self.assertEqual(result["frames"], 2)
        self.assertEqual(result["requested_seconds"], 15)

    def test_stream_covering_requested_duration_passes(self):
        code, result = self.run_probe([0, 1, 15, 15.1])
        self.assertIsNone(code)
        self.assertEqual(result["status"], "ok")
        self.assertGreaterEqual(result["seconds"], 15)
