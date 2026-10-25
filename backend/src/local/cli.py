"""Resumable local workflow. JSON stdout; 0 success, 2 action required, 3 failure."""

import argparse
import contextlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

from backend.src.local.config import ROOT, home, initialize, write_json


def emit(state, **fields):
    print(json.dumps(dict(status=state, **fields)))
    return {"ok": 0, "action_required": 2, "error": 3}[state]


def checks(config):
    import importlib.util

    issues = []
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        issues.append(
            "Full local classification currently requires Apple Silicon "
            "macOS; other platforms are unverified/unsupported."
        )
    import psutil

    if psutil.virtual_memory().total < 15_000_000_000:
        issues.append("16 GB RAM required by the tested local profile.")
    if sys.version_info[:2] != (3, 11):
        issues.append("Use Python 3.11.")
    if importlib.util.find_spec("mlx_vlm") is None:
        issues.append(
            "Install local model runtime: uv sync --frozen --python 3.11 --extra local"
        )
    if (
        not (Path(config["model"]) / "model.safetensors").exists()
        or not Path(config["yolo"]).exists()
    ):
        issues.append("Run ghostbusters local models (public download, no account).")
    if config["camera"] is None:
        issues.append(
            "Run ghostbusters local setup --brand doorbird|usb|onvif; choose "
            "a device if requested."
        )
    if not (ROOT / "frontend/out/index.html").exists():
        issues.append("Run ghostbusters local build (Node 22+, npm required).")
    return issues


def metal_available():
    """Probe in a child: unavailable Metal can abort native module imports."""
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import mlx.core as mx; "
                "raise SystemExit(0 if mx.metal.is_available() else 1)",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def live_issues(snapshot, running):
    if not running:
        return ["Local services are stopped; run local up."]
    problems = []
    for component, expected in (
        ("service", "running"),
        ("capture", "streaming"),
        ("model", "ready"),
        ("storage", "ready"),
    ):
        health = snapshot["health"].get(component, {})
        stamp = (
            health.get("last_frame", 0)
            if component == "capture"
            else health.get("updated", 0)
        )
        if health.get("state") != expected or time.time() - stamp > (
            15 if component == "capture" else 60
        ):
            problems.append(
                f"{component}: {health.get('state', 'not reported')}; "
                "check component health and recovery action."
            )
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    setup = sub.add_parser("setup")
    setup.add_argument("--brand")
    setup.add_argument("--select")
    setup.add_argument(
        "--credentials-file",
        type=Path,
        help=(
            "Private dotenv containing DOORBIRD_USERNAME/PASSWORD or "
            "CAMERA_USERNAME/PASSWORD; never pass values in argv"
        ),
    )
    setup.add_argument("--port", type=int)
    setup.add_argument(
        "--roi", nargs=4, type=float, metavar=("LEFT", "RIGHT", "TOP", "BOTTOM")
    )
    setup.add_argument("--retention-days", type=float)
    setup.add_argument("--max-image-mb", type=int)
    discover = sub.add_parser("discover")
    discover.add_argument("--brand", required=True)
    camera = sub.add_parser("camera-check")
    camera.add_argument("--seconds", type=int, default=10)
    camera.add_argument("--save-preview", action="store_true")
    for command in ("models", "build", "status", "doctor", "stop", "link", "serve"):
        sub.add_parser(command)
    for command in ("up", "start"):
        p = sub.add_parser(command)
        p.add_argument("--foreground", action="store_true")
    args = parser.parse_args(argv)
    os.umask(0o077)
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        return emit(
            "action_required",
            action=(
                "Full local setup requires Apple Silicon macOS with 16 GB RAM. "
                "Existing Baseten setup remains available through setup "
                "--provider baseten; no MLX download attempted."
            ),
        )
    try:
        import psutil

        from backend.src.local.lifecycle import alive, start, stop, supervise
        from backend.src.local.store import Store

        if (
            args.command in ("setup", "models")
            and psutil.virtual_memory().total < 15_000_000_000
        ):
            return emit(
                "action_required",
                action=(
                    "16 GB RAM required by the tested local profile; no model "
                    "download attempted."
                ),
            )
        config = initialize()
        store = Store(home())
        if args.command == "discover":
            from backend.src.local.discovery import discover

            devices = discover(args.brand)
            write_json(home() / "discovery.json", devices)
            return emit(
                "ok" if devices else "action_required",
                devices=[
                    {k: v for k, v in d.items() if k in ("id", "kind", "name")}
                    for d in devices
                ],
                action=None
                if devices
                else "Check same LAN, multicast, power and local streaming support.",
            )
        if args.command == "setup":
            if alive():
                return emit(
                    "action_required",
                    action="Stop this installation before changing configuration.",
                )
            if args.port is not None:
                if not 1024 <= args.port <= 65535:
                    raise ValueError("invalid_port")
                config["port"] = args.port
            if args.roi:
                left, right, top, bottom = args.roi
                if not 0 <= left < right <= 1 or not 0 <= top < bottom <= 1:
                    raise ValueError("invalid_roi")
                config["roi"] = args.roi
            if args.retention_days is not None:
                if args.retention_days <= 0:
                    raise ValueError("invalid_retention")
                config["retention_days"] = args.retention_days
            if args.max_image_mb is not None:
                if args.max_image_mb < 1:
                    raise ValueError("invalid_disk_limit")
                config["max_image_bytes"] = args.max_image_mb * 1_000_000
            if args.brand:
                from backend.src.local.discovery import discover

                devices = discover(args.brand)
                chosen = (
                    next((d for d in devices if d["id"] == args.select), None)
                    if args.select
                    else devices[0]
                    if len(devices) == 1
                    else None
                )
                if (
                    chosen is None
                    and args.brand.lower() == "doorbird"
                    and args.credentials_file
                    and not args.select
                ):
                    from dotenv import dotenv_values

                    from backend.src.local.cameras import identify_doorbird

                    values = dotenv_values(args.credentials_file, interpolate=False)
                    username = values.get("DOORBIRD_USERNAME")
                    password = values.get("DOORBIRD_PASSWORD")
                    if username and password:
                        chosen = identify_doorbird(
                            devices, {"username": username, "password": password}
                        )
                if chosen is None:
                    return emit(
                        "action_required",
                        action=(
                            "Choose device with --select, or check LAN/local "
                            "streaming if none found."
                        ),
                        devices=[
                            {k: v for k, v in d.items() if k in ("id", "name", "kind")}
                            for d in devices
                        ],
                    )
                if (
                    config["camera"]
                    and chosen["identity"] != config["camera"]["identity"]
                ):
                    (home() / "camera-secret.json").unlink(missing_ok=True)
                config["camera"] = chosen
            if args.credentials_file:
                from dotenv import dotenv_values

                values = dotenv_values(args.credentials_file, interpolate=False)
                user = values.get("DOORBIRD_USERNAME") or values.get("CAMERA_USERNAME")
                password = values.get("DOORBIRD_PASSWORD") or values.get(
                    "CAMERA_PASSWORD"
                )
                if not user or not password or not config["camera"]:
                    raise ValueError(
                        "credentials_require_selected_camera_and_both_fields"
                    )
                write_json(
                    home() / "camera-secret.json",
                    {
                        "username": user,
                        "password": password,
                        "identity": config["camera"]["identity"],
                    },
                )
            write_json(home() / "config.json", config)
            if (
                config["camera"]
                and config["camera"]["kind"] in ("doorbird", "onvif")
                and not (home() / "camera-secret.json").exists()
            ):
                return emit(
                    "action_required",
                    action=(
                        "Provide camera-local username/password in a private "
                        "dotenv file, then rerun setup --credentials-file PATH. "
                        "Enable watch-always/local streaming permissions."
                    ),
                )
            issues = checks(config)
            return emit(
                "action_required" if issues else "ok",
                installation=config["installation"],
                phase="configured",
                ready=False,
                actions=issues,
            )
        if args.command in ("models", "up", "start") and not metal_available():
            return emit(
                "action_required",
                action="Metal GPU access is unavailable. Install the local extra and "
                "run this command in a host terminal with GPU access; an agent sandbox "
                "may block Metal. No model download or service start attempted.",
            )
        if args.command == "models":
            from huggingface_hub import snapshot_download

            from backend.src.local.vision import MODEL_ID, MODEL_REVISION

            # Never reuse a global HF login; this public download needs no token.
            with contextlib.redirect_stdout(sys.stderr):
                snapshot_download(
                    MODEL_ID,
                    revision=MODEL_REVISION,
                    local_dir=config["model"],
                    token=False,
                )
                import requests

                target = Path(config["yolo"])
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.exists():
                    r = requests.get(
                        "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt",
                        timeout=60,
                    )
                    r.raise_for_status()
                    temp = target.with_suffix(".tmp")
                    temp.write_bytes(r.content)
                    temp.replace(target)
            return emit("ok", model=MODEL_ID)
        if args.command == "build":
            if not shutil.which("npm"):
                return emit("action_required", action="Install Node 22+ and npm.")
            env = dict(
                os.environ,
                NEXT_PUBLIC_STORAGE_PROVIDER="local",
                NEXT_PUBLIC_BASE_PATH="",
                NEXT_TELEMETRY_DISABLED="1",
            )
            for key in list(env):
                if "SUPABASE" in key:
                    del env[key]
            for command in (["npm", "ci"], ["npm", "run", "build"]):
                subprocess.run(
                    command,
                    cwd=ROOT / "frontend",
                    env=env,
                    stdout=sys.stderr,
                    check=True,
                )
            return emit("ok")
        if args.command == "camera-check":
            if alive():
                return emit(
                    "action_required",
                    action="Stop this installation before bounded camera probing.",
                )
            if not config["camera"]:
                return emit("action_required", action="Select a camera first.")
            # Native FFmpeg errors are discarded in a bounded subprocess, not stdout.
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "backend.src.local.probe",
                    str(max(1, min(args.seconds, 60))),
                    str(int(args.save_preview)),
                ],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                timeout=min(args.seconds, 60) + 25,
            )
            try:
                report = json.loads(result.stdout)
            except ValueError:
                report = {"status": "error", "reason": "camera_probe_failed"}
            print(json.dumps(report))
            return 0 if report["status"] == "ok" else 2
        if args.command in ("status", "doctor"):
            issues = checks(config)
            running = alive()
            snapshot = store.snapshot()
            health_issues = live_issues(snapshot, running)
            ready = not issues and not health_issues
            return emit(
                "action_required"
                if issues or (args.command == "doctor" and not ready)
                else "ok",
                running=running,
                ready=ready,
                phase="ready" if ready else "degraded" if running else "stopped",
                installation=config["installation"],
                gallery_url=f"http://127.0.0.1:{config['port']}",
                actions=issues + health_issues,
                **snapshot,
            )
        if args.command == "link":
            return emit(
                "ok",
                private_gallery_url=f"http://127.0.0.1:{config['port']}/#token={config['token']}",
            )
        if args.command == "stop":
            stop()
            return emit("ok", running=False)
        if args.command == "serve":
            supervise()
            return 0
        if args.command in ("up", "start"):
            issues = checks(config)
            if issues:
                return emit("action_required", actions=issues)
            start(args.foreground)
            deadline = time.monotonic() + (0 if args.foreground else 30)
            while (
                alive()
                and live_issues(store.snapshot(), True)
                and time.monotonic() < deadline
            ):
                time.sleep(0.5)
            ready = alive() and not live_issues(store.snapshot(), True)
            return emit(
                "ok" if ready else "action_required",
                phase="ready" if ready else "starting" if alive() else "stopped",
                ready=ready,
                running=alive(),
                gallery_url=f"http://127.0.0.1:{config['port']}",
                action="Open ghostbusters local link for the private access link.",
            )
    except (ValueError, RuntimeError) as error:
        return emit(
            "error",
            reason=str(error)
            if str(error).startswith(
                (
                    "invalid_",
                    "unsupported_camera",
                    "credentials_",
                    "start_failed",
                    "stop_timeout",
                )
            )
            else type(error).__name__,
            action="See docs/LOCAL_SETUP.md.",
        )
    except Exception as error:
        return emit(
            "error",
            reason=type(error).__name__,
            action=(
                "Check prerequisites and private config; no secret-bearing "
                "exception text is printed."
            ),
        )


if __name__ == "__main__":
    raise SystemExit(main())
