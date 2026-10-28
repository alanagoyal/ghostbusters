import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from dotenv import dotenv_values

from backend.scripts import projects
from backend.scripts.cli import save_env
from backend.src.clients.vision import create_vision_client


class ProjectsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "provisioned.env"
        self.camera = self.root / "camera.env"
        save_env(
            self.source,
            {
                "SUPABASE_PROJECT_URL": "https://example.supabase.co",
                "SUPABASE_PUBLISHABLE_KEY": "sb_publishable_public",
                "SUPABASE_SECRET_KEY": "sb_secret_private",
                "OPENROUTER_API_API_KEY": "inference-private",
            },
        )
        save_env(self.camera, {"CAMERA_SOURCE": "0"})

    def configure(self, **kwargs):
        return projects.configure(
            self.source, self.camera, "provider/vision", root=self.root, **kwargs
        )

    def test_alias_import_private_permissions_and_rerun(self):
        original = self.source.read_bytes()
        self.configure()
        self.configure()
        backend = self.root / ".env"
        front = self.root / "frontend/.env.local"
        self.assertEqual(
            dotenv_values(backend)["OPENROUTER_API_KEY"], "inference-private"
        )
        self.assertNotIn("sb_secret_private", front.read_text())
        self.assertEqual(dotenv_values(front)["NEXT_PUBLIC_GALLERY_ACCESS"], "private")
        self.assertEqual(backend.stat().st_mode & 0o777, 0o600)
        self.assertEqual(front.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.source.read_bytes(), original)

    def test_conflicts_and_backend_browser_key_write_nothing(self):
        for change in (
            {"SUPABASE_URL": "https://other.supabase.co"},
            {"SUPABASE_PUBLISHABLE_KEY": "sb_secret_wrong"},
        ):
            with self.subTest(change=change):
                original = self.source.read_bytes()
                save_env(self.source, change)
                with self.assertRaises(projects.SetupError):
                    self.configure()
                self.assertFalse((self.root / ".env").exists())
                self.source.write_bytes(original)

    def test_existing_install_and_frontend_conflict_preserved(self):
        save_env(self.root / ".env", {"BASETEN_API_KEY": "original"})
        with self.assertRaises(projects.SetupError):
            self.configure()
        self.assertEqual(
            dotenv_values(self.root / ".env")["BASETEN_API_KEY"], "original"
        )
        (self.root / ".env").unlink()
        save_env(
            self.root / "frontend/.env.local", {"NEXT_PUBLIC_STORAGE_PROVIDER": "local"}
        )
        with self.assertRaises(projects.SetupError):
            self.configure()
        self.assertFalse((self.root / ".env").exists())

    def test_pooler_preferred_and_password_encoded(self):
        value = projects.database_url(
            {
                "SUPABASE_DB_URL": "postgres://direct/db",
                "SUPABASE_POOLER_URL": "postgres://user:[YOUR-PASSWORD]@pooler:6543/db",
                "DB_PASS": "a@b/$",
            }
        )
        self.assertEqual(value, "postgres://user:a%40b%2F%24@pooler:6543/db")

    def test_sql_secret_not_in_arguments_or_errors(self):
        save_env(self.source, {"SUPABASE_POOLER_URL": "postgres://u:secret@pooler/db"})
        with (
            patch.object(
                projects.subprocess,
                "run",
                return_value=Mock(returncode=1, stderr="secret"),
            ) as run,
            self.assertRaises(projects.SetupError) as caught,
        ):
            projects.bootstrap(self.source)
        self.assertNotIn("secret", str(caught.exception))
        self.assertNotIn("secret", str(run.call_args.args))
        self.assertEqual(run.call_args.kwargs["env"]["PGSSLMODE"], "require")
        self.assertEqual(run.call_args.kwargs["env"]["PGHOST"], "pooler")
        self.assertEqual(run.call_args.kwargs["env"]["PGDATABASE"], "db")
        self.assertEqual(run.call_args.kwargs["env"]["PGPASSWORD"], "secret")

    def test_bootstrap_decodes_uri_components_without_exposing_password(self):
        save_env(
            self.source,
            {
                "SUPABASE_POOLER_URL": "postgres://user%40ref:a%40b%2F%24@pooler:6543/db?sslmode=require"
            },
        )
        with patch.object(
            projects.subprocess, "run", return_value=Mock(returncode=0)
        ) as run:
            projects.bootstrap(self.source)
        env = run.call_args.kwargs["env"]
        self.assertEqual(env["PGUSER"], "user@ref")
        self.assertEqual(env["PGPASSWORD"], "a@b/$")
        self.assertEqual(env["PGPORT"], "6543")
        self.assertNotIn("a@b/$", str(run.call_args.args))

    def test_provider_prefixed_database_password_and_conflicting_alias(self):
        values = {
            "SUPABASE_POOLER_URL": "postgres://user:[YOUR-PASSWORD]@pooler:6543/db",
            "SUPABASE_DB_PASS": "a@b/$",
        }
        self.assertEqual(
            projects.database_url(values), "postgres://user:a%40b%2F%24@pooler:6543/db"
        )
        with self.assertRaises(projects.SetupError) as caught:
            projects.database_url({**values, "DB_PASS": "different-secret"})
        self.assertNotIn("different-secret", str(caught.exception))
        self.assertIn("Conflicting aliases", str(caught.exception))

    def test_supabase_cli_key_retrieval_captured(self):
        result = Mock(returncode=0, stdout='[{"api_key":"sb_secret_retrieved"}]')
        with patch.object(projects.subprocess, "run", return_value=result) as run:
            self.assertEqual(
                projects.fetch_backend_key("https://example.supabase.co"),
                "sb_secret_retrieved",
            )
        self.assertTrue(run.call_args.kwargs["capture_output"])

    def test_openrouter_does_not_inherit_baseten_key_or_model(self):
        with patch.dict(
            os.environ,
            {
                "INFERENCE_PROVIDER": "openrouter",
                "OPENROUTER_API_KEY": "router",
                "OPENROUTER_MODEL": "vision",
                "BASETEN_API_KEY": "old",
            },
            clear=True,
        ):
            client = create_vision_client()
        self.assertEqual(client.api_key, "router")
        self.assertEqual(client.model, "vision")
        self.assertEqual(client.session.headers["Authorization"], "Bearer router")

    def test_missing_inputs_return_safe_action(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = projects.main(
                [
                    "configure",
                    "--source",
                    str(self.root / "missing"),
                    "--camera-env",
                    str(self.camera),
                    "--model",
                    "vision",
                ]
            )
        self.assertEqual(result, 1)
        self.assertIn("action_required", output.getvalue())
