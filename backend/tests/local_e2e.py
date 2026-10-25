"""Opt-in offline real-model acceptance: video -> YOLO -> jobs -> vision -> SSE.

Run with Python 3.11 after local model downloads. No cloud credentials/config read.
Creates a disposable private installation; never opens a household camera.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import cv2
import requests

from backend.src.local.config import ROOT, initialize, write_json


def run(model, report_path, yolo=None):
    with tempfile.TemporaryDirectory(prefix="ghostbusters-e2e-") as temporary:
        directory = Path(temporary)
        os.environ["GHOSTBUSTERS_HOME"] = str(directory)
        config = initialize()
        import socket

        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        video = directory / "fixture.avi"
        writer = cv2.VideoWriter(
            str(video), cv2.VideoWriter_fourcc(*"MJPG"), 10, (640, 480)
        )
        for number in (2, 1, 3):
            frame = cv2.imread(str(ROOT / f"backend/tests/fixtures/local/{number}.jpg"))
            frame = cv2.resize(frame, (640, 480))
            for _ in range(80):
                writer.write(frame)
        writer.release()
        config.update(
            model=str(Path(model).resolve()),
            yolo=str(Path(yolo).resolve()) if yolo else config["yolo"],
            port=port,
            camera={
                "kind": "fixture",
                "path": str(video),
                "identity": "licensed-fixture",
            },
            cooldown_seconds=3,
        )
        write_json(directory / "config.json", config)
        env = {
            k: v
            for k, v in os.environ.items()
            if not any(word in k for word in ("SUPABASE", "BASETEN", "HF_TOKEN"))
        }
        env.update(
            HF_HUB_OFFLINE="1",
            GHOSTBUSTERS_HOME=str(directory),
            PYTHONPATH=str(ROOT),
            YOLO_CONFIG_DIR=str(directory / "yolo"),
        )
        process = subprocess.Popen(
            [sys.executable, "-m", "backend.src.local.cli", "serve"],
            cwd=ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        client = requests.Session()
        client.trust_env = False
        base = f"http://127.0.0.1:{port}"
        report = {
            "source": "licensed fixture video",
            "cloud_environment_keys": [
                k for k in env if any(w in k for w in ("SUPABASE", "BASETEN"))
            ],
            "events": 0,
            "classified": 0,
            "passed": False,
        }
        try:
            deadline = time.monotonic() + 180
            while time.monotonic() < deadline:
                try:
                    response = client.post(
                        base + "/api/session",
                        json={"token": config["token"]},
                        timeout=2,
                    )
                    if response.ok:
                        break
                except requests.RequestException:
                    time.sleep(0.2)
            with client.get(base + "/api/events", stream=True, timeout=15) as response:
                for line in response.iter_lines(chunk_size=1):
                    if not line.startswith(b"data: "):
                        continue
                    value = json.loads(line[6:])
                    report["events"] += 1
                    completed = [
                        r for r in value["detections"] if r["state"] == "complete"
                    ]
                    report["classified"] = len(completed)
                    if len(completed) >= 5:
                        report["snapshot"] = value
                        for row in completed:
                            image = client.get(base + row["image_url"], timeout=5)
                            assert (
                                image.status_code == 200 and len(image.content) > 1000
                            )
                        break
                    if time.monotonic() > deadline:
                        raise AssertionError(
                            "No completed real model pipeline within 180 seconds"
                        )
            assert report["classified"] >= 5
            process.terminate()
            process.wait(timeout=15)
            # Restart preserves records, installation ID and private auth.
            process = subprocess.Popen(
                [sys.executable, "-m", "backend.src.local.cli", "serve"],
                cwd=ROOT,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            restart_deadline = time.monotonic() + 15
            while True:
                try:
                    response = client.get(base + "/api/status", timeout=2)
                    response.raise_for_status()
                    status = response.json()
                    break
                except requests.RequestException:
                    if time.monotonic() >= restart_deadline:
                        raise
                    time.sleep(0.2)
            report["restart_persisted"] = (
                status["total"] >= report["classified"]
                and status["installation"] == config["installation"]
            )
            assert report["restart_persisted"], (
                "Records or installation lost on restart"
            )
            report["passed"] = True
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            client.close()
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--yolo", type=Path, help="Optional existing YOLO weights")
    args = parser.parse_args()
    run(args.model, args.report, args.yolo)
