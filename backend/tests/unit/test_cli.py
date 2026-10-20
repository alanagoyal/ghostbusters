import base64
import contextlib
import io
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dotenv import dotenv_values

from backend.scripts import cli


class CliTests(unittest.TestCase):
    def test_only_public_keys_can_enter_browser_config(self):
        def jwt(role):
            data = (
                base64.urlsafe_b64encode(('{"role":"' + role + '"}').encode())
                .decode()
                .rstrip("=")
            )
            return f"header.{data}.signature"

        self.assertTrue(cli.public_key("sb_publishable_example"))
        self.assertTrue(cli.public_key(jwt("anon")))
        for value in ("sb_secret_private", jwt("service_role"), "garbage", "a.!!!.b"):
            self.assertFalse(cli.public_key(value))

    def test_env_preserves_settings_and_roundtrips_special_characters(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("# keep comment\nROI_X_MAX='0.8'\nTOKEN='old'\n")
            secret = "p'a$ss\\word#@"
            cli.save_env(path, {"TOKEN": secret})
            self.assertEqual(dotenv_values(path)["TOKEN"], secret)
            self.assertEqual(dotenv_values(path)["ROI_X_MAX"], "0.8")
            self.assertIn("# keep comment", path.read_text())
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(len(list(path.parent.iterdir())), 1)

    def test_check_does_not_expose_exception_credentials(self):
        def fail():
            raise ValueError("secret-camera-password")

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertFalse(cli.check("Camera", fail, "Check connection"))
        self.assertNotIn("secret-camera-password", output.getvalue())
        self.assertIn("Check connection", output.getvalue())

    def test_setup_rejects_private_browser_key_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "frontend").mkdir()
            values = iter(
                [
                    "0",
                    "front-door",
                    "baseten-key",
                    cli.ENDPOINT,
                    cli.MODEL,
                    "Bearer",
                    "https://example.supabase.co",
                    "sb_secret_backend",
                    "sb_secret_wrong",
                ]
            )
            with (
                patch.object(cli, "ROOT", root),
                patch("sys.stdin.isatty", return_value=True),
                patch("builtins.input", return_value="1"),
                patch.object(cli, "prompt", side_effect=lambda *a, **k: next(values)),
                contextlib.redirect_stdout(io.StringIO()),
                self.assertRaises(ValueError),
            ):
                cli.setup()
            self.assertFalse((root / ".env").exists())
            self.assertFalse((root / "frontend/.env.local").exists())

    def test_macos_stop_disables_login_restart_before_unloading(self):
        with (
            patch.object(cli.sys, "platform", "darwin"),
            patch.object(
                cli.subprocess, "run", return_value=subprocess.CompletedProcess([], 1)
            ) as run,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(cli.service("stop"), 0)
        self.assertEqual(run.call_args_list[0].args[0][1], "disable")
        self.assertEqual(run.call_args_list[1].args[0][1], "bootout")

    def test_linux_stop_disables_boot_startup(self):
        with (
            patch.object(cli.sys, "platform", "linux"),
            patch.object(cli.subprocess, "call", return_value=0) as call,
        ):
            self.assertEqual(cli.service("stop"), 0)
        call.assert_called_once_with(
            ["sudo", "systemctl", "disable", "--now", cli.UNIT]
        )

    def test_setup_is_safe_without_interactive_terminal(self):
        with (
            patch("sys.stdin.isatty", return_value=False),
            patch.object(cli, "save_env") as save,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(cli.setup(), 1)
            save.assert_not_called()

    def test_setup_writes_separate_configs_and_preserves_custom_roi(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "frontend").mkdir()
            (root / ".env").write_text("ROI_X_MAX='0.8'\n")
            answers = iter(
                [
                    "0",
                    "front-door",
                    "baseten-private",
                    cli.ENDPOINT,
                    cli.MODEL,
                    "Bearer",
                    "https://example.supabase.co",
                    "sb_secret_backend",
                    "sb_publishable_browser",
                ]
            )
            with (
                patch.object(cli, "ROOT", root),
                patch("sys.stdin.isatty", return_value=True),
                patch("builtins.input", return_value="1"),
                patch.object(cli, "prompt", side_effect=lambda *a, **k: next(answers)),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(cli.setup(), 0)
            backend = dotenv_values(root / ".env")
            frontend = dotenv_values(root / "frontend/.env.local")
            self.assertEqual(backend["ROI_X_MAX"], "0.8")
            self.assertEqual(backend["SUPABASE_SERVICE_ROLE_KEY"], "sb_secret_backend")
            self.assertEqual(
                frontend["NEXT_PUBLIC_SUPABASE_ANON_KEY"], "sb_publishable_browser"
            )
            self.assertNotIn("sb_secret", (root / "frontend/.env.local").read_text())
            self.assertNotIn(
                "baseten-private", (root / "frontend/.env.local").read_text()
            )

    def test_doctor_failure_checks_remaining_services_without_writes(self):
        from unittest.mock import Mock

        import requests

        response = Mock(status_code=401)
        failure = requests.HTTPError("sensitive URL and key", response=response)
        env = {
            "CAMERA_SOURCE": "0",
            "BASETEN_API_KEY": "private",
            "BASETEN_MODEL_URL": cli.ENDPOINT,
            "SUPABASE_SERVICE_ROLE_KEY": "sb_secret_example",
            "NEXT_PUBLIC_SUPABASE_URL": "https://example.supabase.co",
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cli.save_env(
                root / "frontend/.env.local",
                {
                    "NEXT_PUBLIC_SUPABASE_URL": env["NEXT_PUBLIC_SUPABASE_URL"],
                    "NEXT_PUBLIC_SUPABASE_ANON_KEY": "sb_publishable_example",
                },
            )
            output = io.StringIO()
            with (
                patch.object(cli, "ROOT", root),
                patch.dict(cli.os.environ, env, clear=True),
                patch("requests.post", side_effect=failure),
                patch("requests.get", side_effect=failure) as get,
                patch.object(cli.subprocess, "run") as camera,
                contextlib.redirect_stdout(output),
            ):
                self.assertEqual(cli.doctor(skip_camera=True), 1)
            camera.assert_not_called()
            self.assertEqual(get.call_count, 3)
            self.assertIn("HTTP 401", output.getvalue())
            self.assertNotIn("sensitive URL", output.getvalue())
