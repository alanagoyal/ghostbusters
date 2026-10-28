"""Guided setup and seasonal operation for a Ghostbusters checkout."""

import argparse
import base64
import getpass
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from dotenv import dotenv_values, load_dotenv, set_key

from backend.src.camera import camera_source, region_of_interest
from backend.src.clients.vision import request_options, vision_settings

ROOT = Path(__file__).resolve().parents[2]
LABEL = "com.ghostbusters.detector"
UNIT = "costume-detector.service"
MODEL = "nvidia/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B"
ENDPOINT = "https://inference.baseten.co/v1/chat/completions"


def public_key(value):
    """Accept only explicitly public key types before writing browser config."""
    if value.startswith("sb_publishable_"):
        return True
    try:
        payload = value.split(".")[1]
        return (
            json.loads(
                base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
            ).get("role")
            == "anon"
        )
    except (ValueError, IndexError, UnicodeError):
        return False


def save_env(path, values):
    """Preserve unrelated settings/comments; replace atomically with mode 0600."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".ghostbusters-config-")
    temporary = Path(name)
    try:
        with os.fdopen(fd, "w") as output:
            output.write(path.read_text() if path.exists() else "")
        for key, value in values.items():
            set_key(temporary, key, value)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def prompt(label, current="", secret=False):
    suffix = " [Enter to keep existing/default]" if current else ""
    read = getpass.getpass if secret else input
    while True:
        value = read(f"{label}{suffix}: ").strip() or current
        if value and not any(char in value for char in "\r\n\x00"):
            return value
        print("A value is required (one line). Ctrl+C cancels without saving.")


def setup():
    if not sys.stdin.isatty():
        print("Run setup in an interactive terminal; credentials are hidden prompts.")
        return 1
    old = dotenv_values(ROOT / ".env")
    front = dotenv_values(ROOT / "frontend/.env.local")
    print("Connect your camera → Baseten → Supabase. Nothing starts during setup.")
    print("Images/costume crops go to Baseten; the Supabase gallery is public.")
    print("Camera help: docs/CAMERAS.md")
    kind = input("Camera: [1] USB/RTSP/HTTP [2] DoorBird (default 1): ").strip()
    values = {"INFERENCE_PROVIDER": "baseten", "STORAGE_PROVIDER": "supabase"}
    if kind == "2":
        values["CAMERA_SOURCE"] = ""
        for key in ("DOORBIRD_IP", "DOORBIRD_USERNAME", "DOORBIRD_PASSWORD"):
            values[key] = prompt(key, old.get(key) or "", secret="PASSWORD" in key)
    else:
        values["CAMERA_SOURCE"] = prompt(
            "Camera index (e.g. 0) or full stream URL (hidden)",
            old.get("CAMERA_SOURCE") or "",
            secret=True,
        )
    values["DEVICE_ID"] = prompt("Device name", old.get("DEVICE_ID") or "front-door")
    print("Baseten: create an API key at https://app.baseten.co/settings/api_keys")
    values["BASETEN_API_KEY"] = prompt(
        "Baseten API key", old.get("BASETEN_API_KEY") or "", secret=True
    )
    print(f"Default hosted endpoint: {ENDPOINT}\nDefault vision model: {MODEL}")
    values["BASETEN_MODEL_URL"] = prompt(
        "Baseten endpoint", old.get("BASETEN_MODEL_URL") or ENDPOINT
    )
    values["BASETEN_MODEL"] = prompt("Vision model", old.get("BASETEN_MODEL") or MODEL)
    default_auth = "Bearer" if values["BASETEN_MODEL_URL"] == ENDPOINT else "Api-Key"
    values["BASETEN_AUTH_SCHEME"] = prompt(
        "Auth scheme (Bearer or Api-Key)",
        old.get("BASETEN_AUTH_SCHEME") or default_auth,
    )
    if values["BASETEN_AUTH_SCHEME"] not in {"Bearer", "Api-Key"}:
        raise ValueError("Auth scheme must be Bearer or Api-Key; nothing saved.")
    print("Supabase: create a project at https://supabase.com/dashboard")
    print("Copy its URL and keys from the project's Connect dialog / API Keys.")
    values["NEXT_PUBLIC_SUPABASE_URL"] = prompt(
        "Supabase project URL",
        old.get("NEXT_PUBLIC_SUPABASE_URL") or old.get("SUPABASE_URL") or "",
    )
    if urlparse(values["NEXT_PUBLIC_SUPABASE_URL"]).scheme != "https":
        raise ValueError("Use the HTTPS project URL; nothing saved.")
    values["SUPABASE_SERVICE_ROLE_KEY"] = prompt(
        "Backend secret key (or legacy service_role key)",
        old.get("SUPABASE_SERVICE_ROLE_KEY") or "",
        secret=True,
    )
    browser_key = prompt(
        "Frontend publishable key (or legacy anon key)",
        front.get("NEXT_PUBLIC_SUPABASE_ANON_KEY") or "",
        secret=True,
    )
    if not public_key(browser_key):
        raise ValueError("Frontend requires a publishable/anon key; nothing saved.")
    camera_source(values)
    region_of_interest({**old, **values})
    save_env(ROOT / ".env", values)
    save_env(
        ROOT / "frontend/.env.local",
        {
            "NEXT_PUBLIC_SUPABASE_URL": values["NEXT_PUBLIC_SUPABASE_URL"],
            "NEXT_PUBLIC_SUPABASE_ANON_KEY": browser_key,
        },
    )
    print("Saved .env and frontend/.env.local with private file permissions.")
    print("Next: run backend/migrations/supabase_migration.sql in Supabase SQL Editor.")
    print("Follow docs/SUPABASE_SETUP.md for table grants and Realtime setup.")
    print("Then: uv run ghostbusters doctor")
    print("Dashboard: cd frontend && npm ci && npm run dev")
    return 0


def check(name, action, remedy):
    try:
        action()
    except Exception as error:
        # SDK/native errors may embed API keys, camera passwords, or URLs.
        response = getattr(error, "response", None)
        code = f" (HTTP {response.status_code})" if response is not None else ""
        print(f"FAIL {name}{code}: {remedy}")
        return False
    print(f"OK   {name}")
    return True


def doctor(skip_camera=False):
    import requests

    env = os.environ
    results = []
    api_key, endpoint, model, auth = vision_settings(env)

    def config():
        if not api_key or not endpoint or not model:
            raise ValueError("Missing vision configuration")
        camera_source()
        region_of_interest()
        for key in (
            "SUPABASE_SERVICE_ROLE_KEY",
            "NEXT_PUBLIC_SUPABASE_URL",
        ):
            if not env.get(key):
                raise ValueError(key)

    results.append(check("Configuration", config, "Run uv run ghostbusters setup."))
    if not skip_camera:

        def camera():
            result = subprocess.run(
                [sys.executable, "-m", "backend.scripts.check_camera"],
                cwd=ROOT,
                capture_output=True,
                timeout=30,
            )
            if result.returncode:
                raise ValueError("No frame")

        results.append(
            check(
                "Camera frame (not saved/uploaded)",
                camera,
                "Check power, local network, stream URL and credentials; "
                "see docs/CAMERAS.md.",
            )
        )

    def vision():
        # Synthetic image exercises vision without sending a household image.
        import cv2
        import numpy as np

        _, image = cv2.imencode(".jpg", np.zeros((64, 64, 3), dtype=np.uint8))
        data = base64.b64encode(image).decode()
        response = requests.post(
            endpoint,
            headers={"Authorization": f"{auth} {api_key}"},
            json={
                **request_options(env),
                "model": model,
                "max_tokens": 16,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Name the image color."},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{data}"},
                            },
                        ],
                    }
                ],
            },
            timeout=(10, 60),
        )
        response.raise_for_status()
        if not response.json().get("choices"):
            raise ValueError("No completion")

    print(
        "Cloud vision check makes one small billed vision request using a blank image."
    )
    results.append(
        check(
            "Cloud vision inference",
            vision,
            "Check API key, model access, credits, URL and auth scheme; "
            "see docs/STRIPE_PROJECTS.md or docs/BASETEN_SETUP.md.",
        )
    )

    url = env.get("NEXT_PUBLIC_SUPABASE_URL", "").rstrip("/")
    key = env.get("SUPABASE_SERVICE_ROLE_KEY", "")

    def request(path, api_key):
        response = requests.get(
            url + path,
            headers={
                "apikey": api_key,
                **(
                    {"Authorization": f"Bearer {api_key}"}
                    if not api_key.startswith("sb_")
                    else {}
                ),
            },
            timeout=(10, 20),
        )
        response.raise_for_status()
        return response.json()

    table_path = (
        "/rest/v1/person_detections?select=id,image_url,costume_classification&limit=0"
    )
    results.append(
        check(
            "Supabase backend table access",
            lambda: request(table_path, key),
            "Check backend key and run the SQL setup/grants in docs/SUPABASE_SETUP.md.",
        )
    )

    def bucket():
        info = request("/storage/v1/bucket/detection-images", key)
        expected_public = env.get("GALLERY_ACCESS") != "private"
        if info.get("public") != expected_public:
            raise ValueError("Bucket visibility does not match gallery configuration")

    results.append(
        check(
            "Supabase image bucket visibility",
            bucket,
            "Create detection-images using the Supabase setup SQL.",
        )
    )

    def frontend():
        front = dotenv_values(ROOT / "frontend/.env.local")
        browser_key = front.get("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")
        if front.get("NEXT_PUBLIC_SUPABASE_URL", "").rstrip("/") != url:
            raise ValueError("Project mismatch")
        if not public_key(browser_key):
            raise ValueError("Not a public key")
        if env.get("GALLERY_ACCESS") == "private":
            if front.get("NEXT_PUBLIC_GALLERY_ACCESS") != "private":
                raise ValueError("Private gallery requires matching frontend config")
            try:
                request(table_path, browser_key)
            except requests.HTTPError as error:
                if error.response.status_code in (401, 403):
                    return
                raise
            raise ValueError("Anonymous table access must be denied")
        request(table_path, browser_key)

    results.append(
        check(
            "Dashboard access policy",
            frontend,
            "Check gallery mode, matching frontend settings and Supabase grants/RLS.",
        )
    )
    print(
        "Read checks do not prove uploads or Realtime delivery. Finish with a real "
        "walk-through and confirm the photo appears in the dashboard."
    )
    return 0 if all(results) else 1


def service(action):
    if sys.platform == "darwin":
        target = f"gui/{os.getuid()}/{LABEL}"
        if action == "start":
            running = subprocess.run(
                ["launchctl", "print", target], capture_output=True
            )
            if running.returncode == 0:
                print("Service loaded. Run status; use stop then start to restart.")
                return 0
            return subprocess.call(
                [sys.executable, str(ROOT / "scripts/setup_macos_service.py")]
            )
        if action == "stop":
            subprocess.run(["launchctl", "disable", target], check=True)
            subprocess.run(["launchctl", "bootout", target], capture_output=True)
            result = subprocess.run(["launchctl", "print", target], capture_output=True)
            if result.returncode == 0:
                print(
                    "Stop requested; shutdown is still in progress. Run status shortly."
                )
            else:
                print("Stopped. Automatic login startup disabled until you run start.")
            return 0
        result = subprocess.run(
            ["launchctl", "print", target], capture_output=True, text=True
        )
        if result.returncode:
            print("Stopped (service not loaded). Start: uv run ghostbusters start")
        else:
            for line in result.stdout.splitlines():
                if line.strip().startswith(("state =", "pid =", "last exit code =")):
                    print(line.strip())
        print("Logs: ~/Library/Logs/Ghostbusters/detector.log")
        return 0
    if sys.platform.startswith("linux"):
        if action == "status":
            result = subprocess.run(
                [
                    "systemctl",
                    "show",
                    UNIT,
                    "--property=LoadState,ActiveState,SubState,MainPID,UnitFileState",
                ],
                check=False,
            )
            print("Logs: sudo journalctl -u costume-detector -f")
            return result.returncode
        if action == "start":
            loaded = subprocess.run(
                ["systemctl", "show", UNIT, "--property=LoadState", "--value"],
                capture_output=True,
                text=True,
            )
            if loaded.stdout.strip() != "loaded":
                print("Install first: sudo ./setup-service.sh\nThen run start again.")
                return 1
        return subprocess.call(
            [
                "sudo",
                "systemctl",
                "enable" if action == "start" else "disable",
                "--now",
                UNIT,
            ]
        )
    print(
        "Background services support macOS and Linux. Use start --foreground elsewhere."
    )
    return 1


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "projects":
        from backend.scripts.projects import main as projects_main

        return projects_main(argv[1:])
    # Explicit local commands never load legacy cloud .env credentials.
    if argv and argv[0] == "local":
        from backend.src.local.cli import main as local_main

        return local_main(argv[1:])
    # Fresh clones default local; existing configured cloud installs keep behavior.
    legacy = {**dotenv_values(ROOT / ".env"), **os.environ}
    local_selected = legacy.get("STORAGE_PROVIDER") == "local"
    cloud_selected = legacy.get("STORAGE_PROVIDER") == "supabase" or any(
        legacy.get(k) for k in ("BASETEN_API_KEY", "SUPABASE_SERVICE_ROLE_KEY")
    )
    if (
        argv
        and argv[0] in {"setup", "up", "start", "status", "stop", "doctor"}
        and not any(
            arg == "--provider" or arg.startswith("--provider=") for arg in argv
        )
        and (local_selected or not cloud_selected)
    ):
        from backend.src.local.cli import main as local_main

        return local_main(argv)
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    setup_parser = commands.add_parser(
        "setup", help="Configure camera, Baseten and Supabase interactively"
    )
    setup_parser.add_argument(
        "--provider",
        choices=("baseten",),
        help="Explicitly select legacy Baseten setup",
    )
    doctor_parser = commands.add_parser(
        "doctor", help="Check camera/cloud; one small billed request"
    )
    doctor_parser.add_argument(
        "--skip-camera",
        action="store_true",
        help="Check cloud/config only (e.g. while camera is in use)",
    )
    start = commands.add_parser(
        "start", help="Start background service and enable automatic startup"
    )
    start.add_argument(
        "--foreground", action="store_true", help="Run in this terminal; Ctrl+C stops"
    )
    commands.add_parser(
        "status", help="Show native background service status and log location"
    )
    commands.add_parser(
        "stop", help="Stop background service and disable automatic startup"
    )
    args = parser.parse_args(argv)
    os.chdir(ROOT)
    load_dotenv(ROOT / ".env")
    try:
        if args.command == "setup":
            return setup()
        if args.command == "doctor":
            return doctor(args.skip_camera)
        if args.command == "start":
            camera_source()
            region_of_interest()
            required = (
                "SUPABASE_SERVICE_ROLE_KEY",
                "NEXT_PUBLIC_SUPABASE_URL",
            )
            key, endpoint, model, _ = vision_settings()
            if not all((key, endpoint, model)) or any(
                not os.environ.get(key) for key in required
            ):
                print("Complete setup first: uv run ghostbusters setup")
                return 1
        if args.command == "start" and args.foreground:
            print("Foreground mode: Ctrl+C stops. Stop any background service first.")
            return subprocess.call(
                [sys.executable, "-m", "backend.scripts.service_runner", "--foreground"]
            )
        return service(args.command)
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        return 130
    except ValueError as error:
        print(str(error))
        return 1
    except (OSError, subprocess.SubprocessError):
        print("Command failed. Check service permissions and the setup guide.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
