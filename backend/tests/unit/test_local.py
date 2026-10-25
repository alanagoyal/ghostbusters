"""Offline regressions for durable local processing and private API boundaries."""

import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

from backend.src.local.pipeline import worker_once
from backend.src.local.server import make_server
from backend.src.local.store import Store
from backend.src.local.vision import parse_result


class LocalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def add(self, **kwargs):
        return self.store.add(b"jpeg", 0.8, [1, 2, 3, 4], **kwargs)

    def test_restart_recovers_and_bounds_crash_retries(self):
        ident = self.add()
        for _ in range(3):
            self.assertEqual(Store(self.temp.name).claim(lease_seconds=-1)["id"], ident)
        self.assertIsNone(self.store.claim())
        self.assertEqual(self.store.snapshot()["detections"][0]["state"], "failed")
        self.assertTrue((self.store.images / (ident + ".jpg")).exists())

    def test_queue_pressure_saves_record_and_image(self):
        self.add(queue_limit=1)
        ident = self.add(queue_limit=1)
        rows = {r["id"]: r for r in self.store.snapshot()["detections"]}
        self.assertEqual(rows[ident]["state"], "queue_full")
        self.assertEqual(self.store.snapshot()["total"], 2)

    def test_worker_replacement_releases_leases_before_loading(self):
        ident = self.add()
        for duration in (-1, 120, -1):
            self.assertEqual(self.store.claim(lease_seconds=duration)["id"], ident)
            self.store.recover_worker()
            with self.store.db() as db:
                self.assertEqual(
                    db.execute(
                        "SELECT count(*) FROM detections WHERE state='processing'"
                    ).fetchone()[0],
                    0,
                )
        self.assertIsNone(self.store.claim())
        row = self.store.snapshot()["detections"][0]
        self.assertEqual(row["state"], "failed")
        self.assertEqual(row["attempts"], 3)

    def test_transient_model_failure_survives_restart(self):
        self.add()
        model = Mock()
        model.classify.side_effect = RuntimeError("secret")
        worker_once(self.store, model)
        self.assertEqual(self.store.snapshot()["detections"][0]["state"], "retry")
        with self.store.db() as db:
            db.execute("UPDATE detections SET due=0")
        model.classify.side_effect = None
        model.classify.return_value = {
            "costume": "owl",
            "description": "Feathered vest",
            "confidence": 0.8,
        }
        worker_once(Store(self.temp.name), model)
        row = self.store.snapshot()["detections"][0]
        self.assertEqual(row["state"], "complete")
        self.assertEqual(row["attempts"], 2)
        self.assertNotIn("secret", json.dumps(self.store.snapshot()))

    def test_retention_removes_active_job_safely_and_orphans(self):
        ident = self.add()
        self.store.claim()
        self.store.retain(max_bytes=0, min_free=0)
        self.store.finish(
            ident, result={"costume": "owl", "description": "vest", "confidence": 0.8}
        )
        self.assertEqual(Store(self.temp.name).snapshot()["total"], 0)
        self.assertFalse((self.store.images / (ident + ".jpg")).exists())

    def test_retention_age_and_recent_count(self):
        self.add()
        self.add()
        with self.store.db() as db:
            db.execute(
                (
                    "UPDATE detections SET created=? WHERE id=(SELECT id FROM "
                    "detections LIMIT 1)"
                ),
                (time.time() - 86400 * 8,),
            )
        self.assertEqual(self.store.snapshot()["recent"], 1)
        self.store.retain(days=7, min_free=0)
        self.assertEqual(self.store.snapshot()["total"], 1)

    def test_inflatable_candidate_rejected_when_no_costume(self):
        ident = self.add(detection_type="inflatable_candidate")
        self.store.claim()
        self.store.finish(
            ident,
            result={
                "costume": "No costume",
                "description": "A real dog",
                "confidence": 0.9,
            },
        )
        self.assertEqual(
            self.store.snapshot(include_rejected=True)["detections"][0]["state"],
            "rejected",
        )

    def test_parse_strict_schema(self):
        for text in (
            "{}",
            "[]",
            '{"costume":"owl","description":"vest","confidence":true}',
            '{"costume":"owl","description":"vest","confidence":NaN}',
        ):
            with self.assertRaises(ValueError):
                parse_result(text)
        self.assertEqual(
            parse_result(
                '```json\n{"costume":"owl","description":"vest","confidence":0.8}\n```'
            )["costume"],
            "owl",
        )

    def test_api_auth_images_events_and_traversal(self):
        config = {"port": 0, "token": "a-private-test-token", "installation": "test"}
        server = make_server(config, self.store)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = "http://127.0.0.1:" + str(server.server_port)
        client = requests.Session()
        client.trust_env = False
        try:
            self.assertEqual(client.get(base + "/api/status").status_code, 401)
            self.assertEqual(
                client.post(base + "/api/session", json=[]).status_code, 400
            )
            self.assertEqual(
                client.post(base + "/api/session", json={"token": "wrong"}).status_code,
                401,
            )
            self.assertEqual(
                client.post(
                    base + "/api/session", json={"token": config["token"]}
                ).status_code,
                200,
            )
            ident = self.add()
            self.assertEqual(
                client.get(base + "/api/images/" + ident + ".jpg").content, b"jpeg"
            )
            self.assertEqual(client.get(base + "/api/status").json()["total"], 1)
            with client.get(base + "/api/events", stream=True, timeout=5) as stream:
                lines = stream.iter_lines(chunk_size=1)
                self.assertEqual(next(lines), b"event: status")
                self.assertEqual(json.loads(next(lines)[6:])["total"], 1)
            self.assertEqual(
                client.get(base + "/%2e%2e/pyproject.toml").status_code, 404
            )
        finally:
            client.close()
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()


class LifecycleAndDiscoveryTests(unittest.TestCase):
    def test_process_identity_rejects_pid_reuse_and_other_install(self):
        import psutil

        from backend.src.local import lifecycle

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "process.json").write_text(
                json.dumps({"pid": 123, "created": 10, "installation": "one"})
            )
            process = Mock()
            process.is_running.return_value = True
            process.create_time.return_value = 20
            with (
                patch.object(lifecycle, "home", return_value=path),
                patch.object(lifecycle, "load", return_value={"installation": "one"}),
                patch.object(psutil, "Process", return_value=process),
            ):
                self.assertFalse(lifecycle.alive())
                process.create_time.return_value = 10
                self.assertTrue(lifecycle.alive())
                with patch.object(
                    lifecycle, "load", return_value={"installation": "other"}
                ):
                    self.assertFalse(lifecycle.alive())

    def test_refresh_uses_identity_not_old_ip(self):
        from backend.src.local.cameras import CameraError, refresh

        camera = {"kind": "doorbird", "identity": "mac:one", "host": "192.168.1.2"}
        with patch(
            "backend.src.local.cameras.discover",
            return_value=[{"identity": "mac:one", "host": "192.168.1.9"}],
        ):
            self.assertEqual(refresh(camera)["host"], "192.168.1.9")
        with (
            patch(
                "backend.src.local.cameras.discover",
                return_value=[{"identity": "mac:other", "host": "192.168.1.2"}],
            ),
            self.assertRaises(CameraError),
        ):
            refresh(camera)

    def test_identification_never_authenticates_unconfirmed_kind(self):
        from backend.src.local.cameras import identify_doorbird

        session = Mock()
        session.get.return_value.status_code = 200
        session.get.return_value.json.return_value = {"BHA": {}}
        selected = {"kind": "doorbird", "host": "192.168.1.2", "port": 80}
        with patch("backend.src.local.cameras.requests.Session", return_value=session):
            result = identify_doorbird(
                [
                    {"kind": "unknown"},
                    selected,
                    {"kind": "doorbird", "host": "192.168.1.3", "port": 80},
                ],
                {"username": "user", "password": "test"},
            )
        self.assertEqual(result, selected)
        self.assertEqual(session.get.call_count, 1)
        self.assertFalse(session.get.call_args.kwargs["allow_redirects"])

    def test_inflatable_yolo_class_enters_durable_validation(self):
        import numpy as np

        from backend.src.local.pipeline import process_frame

        with tempfile.TemporaryDirectory() as directory:
            store = Store(directory)
            box = Mock()
            box.cls = [16]
            box.conf = [0.8]
            box.xyxy = [[0, 0, 10, 10]]
            result = Mock()
            result.boxes = [box]
            model = Mock(return_value=[result])
            ids = process_frame(
                np.zeros((20, 20, 3), dtype=np.uint8),
                model,
                store,
                {"roi": [0, 1, 0, 1], "queue_limit": 2},
            )
            self.assertEqual(len(ids), 1)
            self.assertEqual(store.claim()["detection_type"], "inflatable_candidate")


class HealthTests(unittest.TestCase):
    def test_quiet_model_is_healthy_but_old_frame_is_not(self):
        from backend.src.local.cli import live_issues

        now = time.time()
        snapshot = {
            "health": {
                key: {"state": state, "updated": now}
                for key, state in [
                    ("service", "running"),
                    ("capture", "streaming"),
                    ("model", "ready"),
                    ("storage", "ready"),
                ]
            }
        }
        snapshot["health"]["model"]["last_success"] = now - 3600
        snapshot["health"]["capture"]["last_frame"] = now
        self.assertEqual(live_issues(snapshot, True), [])
        snapshot["health"]["capture"]["last_frame"] = now - 16
        self.assertTrue(
            any("capture" in issue for issue in live_issues(snapshot, True))
        )
        self.assertTrue(live_issues(snapshot, False))

    def test_api_derives_stale_frame_even_if_capture_process_frozen(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(directory)
            store.health("capture", "streaming", last_frame=time.time() - 30)
            self.assertEqual(store.snapshot()["health"]["capture"]["state"], "stale")


class SetupRegressionTests(unittest.TestCase):
    def test_explicit_cloud_provider_accepts_both_argparse_forms(self):
        from backend.scripts import cli

        for provider in ("baseten",):
            for args in (
                ["setup", "--provider", provider],
                ["setup", "--provider=" + provider],
            ):
                with (
                    patch.object(cli, "dotenv_values", return_value={}),
                    patch.object(cli, "setup", return_value=0) as setup,
                    patch.object(cli.os, "chdir"),
                ):
                    self.assertEqual(cli.main(args), 0)
                    setup.assert_called_once_with()

    def test_secret_handoff_keeps_dollar_brace_literals(self):
        import contextlib
        import io
        import os

        from backend.src.local import cli, config

        with (
            tempfile.TemporaryDirectory() as directory,
            patch.dict(os.environ, {"GHOSTBUSTERS_HOME": directory}),
        ):
            c = config.initialize()
            c["camera"] = {"kind": "doorbird", "identity": "selected"}
            config.write_json(Path(directory) / "config.json", c)
            secret = Path(directory) / "handoff.env"
            secret.write_text(
                "DOORBIRD_USERNAME='local-user'\n"
                "DOORBIRD_PASSWORD='literal${HOME}password'\n"
            )
            with (
                patch.object(cli, "checks", return_value=[]),
                patch("backend.src.local.lifecycle.alive", return_value=False),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(
                    cli.main(["setup", "--credentials-file", str(secret)]), 0
                )
            saved = json.loads((Path(directory) / "camera-secret.json").read_text())
            self.assertEqual(saved["password"], "literal${HOME}password")


class CaptureCooldownTests(unittest.TestCase):
    def test_parked_car_cooldown_does_not_hide_a_brief_person_visit(self):
        import numpy as np

        from backend.src.local.pipeline import process_frame

        def result(*classes):
            boxes = []
            for cls in classes:
                box = Mock()
                box.cls = [cls]
                box.conf = [0.9]
                box.xyxy = [[0, 0, 10, 10]]
                boxes.append(box)
            detection = Mock()
            detection.boxes = boxes
            return [detection]

        model = Mock(
            side_effect=[result(2), result(2, 0, 0), result(2, 0), result(2, 0)]
        )
        config = {"roi": [0, 1, 0, 1], "queue_limit": 32, "cooldown_seconds": 30}
        saved = {}
        frame = np.zeros((20, 20, 3), dtype=np.uint8)
        with tempfile.TemporaryDirectory() as directory:
            store = Store(directory)
            self.assertEqual(
                len(process_frame(frame, model, store, config, saved, now=0)), 1
            )
            # Two people entering one second later both survive candidate cooldown.
            self.assertEqual(
                len(process_frame(frame, model, store, config, saved, now=1)), 2
            )
            self.assertEqual(
                len(process_frame(frame, model, store, config, saved, now=2)), 0
            )
            self.assertEqual(
                len(process_frame(frame, model, store, config, saved, now=31)), 2
            )
            self.assertEqual(model.call_count, 4)
            with store.db() as db:
                count = db.execute(
                    "SELECT count(*) FROM detections WHERE detection_type='person'"
                ).fetchone()[0]
            self.assertEqual(count, 3)
