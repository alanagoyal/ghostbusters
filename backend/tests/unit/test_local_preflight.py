"""GPU checks fail safely before downloading models or starting services."""

import subprocess
import unittest
from unittest.mock import Mock, patch

from backend.src.local.cli import metal_available


class MetalPreflightTests(unittest.TestCase):
    def test_native_import_failure_is_unavailable(self):
        with patch(
            "backend.src.local.cli.subprocess.run", return_value=Mock(returncode=-6)
        ):
            self.assertFalse(metal_available())

    def test_hung_probe_is_unavailable(self):
        with patch(
            "backend.src.local.cli.subprocess.run",
            side_effect=subprocess.TimeoutExpired("probe", 15),
        ):
            self.assertFalse(metal_available())

    def test_usable_metal(self):
        with patch(
            "backend.src.local.cli.subprocess.run", return_value=Mock(returncode=0)
        ):
            self.assertTrue(metal_available())
