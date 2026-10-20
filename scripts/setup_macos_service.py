#!/usr/bin/env python3
"""Install a per-user launchd agent using this checkout's virtual environment."""

import argparse
import os
import plistlib
import subprocess
import sys
import time
from pathlib import Path

LABEL = "com.ghostbusters.detector"


def configuration(root, log_dir):
    return {
        "Label": LABEL,
        "ProgramArguments": [
            str(root / ".venv/bin/python"),
            "-m",
            "backend.scripts.service_runner",
        ],
        "WorkingDirectory": str(root),
        "EnvironmentVariables": {
            "PYTHONUNBUFFERED": "1",
            "GHOSTBUSTERS_LOG_DIR": str(log_dir),
        },
        "RunAtLoad": True,
        "KeepAlive": True,
        "ThrottleInterval": 15,
        "ExitTimeOut": 90,
        "ProcessType": "Background",
        "StandardOutPath": str(log_dir / "launcher.log"),
        "StandardErrorPath": str(log_dir / "launcher-error.log"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--print", action="store_true", help="Print plist without installing"
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    log_dir = Path.home() / "Library/Logs/Ghostbusters"
    plist = plistlib.dumps(configuration(root, log_dir))
    if args.print:
        sys.stdout.buffer.write(plist)
        return
    if sys.platform != "darwin" or os.getuid() == 0:
        parser.error("Run as your normal macOS user, without sudo")
    if not (root / ".venv/bin/python").is_file() or not (root / ".env").is_file():
        parser.error("Run uv sync and configure .env first")
    target = Path.home() / "Library/LaunchAgents" / f"{LABEL}.plist"
    target.parent.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    domain = f"gui/{os.getuid()}"
    subprocess.run(["launchctl", "bootout", f"{domain}/{LABEL}"], capture_output=True)
    # bootout returns before a running job has fully stopped. Wait before
    # bootstrapping the replacement, otherwise launchd can return error 5.
    deadline = time.monotonic() + 100
    while (
        subprocess.run(
            ["launchctl", "print", f"{domain}/{LABEL}"], capture_output=True
        ).returncode
        == 0
    ):
        if time.monotonic() >= deadline:
            raise RuntimeError("Previous detector is still stopping; try again later")
        time.sleep(0.25)
    target.write_bytes(plist)
    target.chmod(0o600)
    subprocess.run(["launchctl", "enable", f"{domain}/{LABEL}"], check=True)
    subprocess.run(["launchctl", "bootstrap", domain, str(target)], check=True)
    print(f"Installed and started {LABEL}; starts again at user login.")
    print(f"Detector logs: {log_dir / 'detector.log'}")


if __name__ == "__main__":
    main()
