"""Per-install supervisor. No global labels, service managers or process-name kills."""

import fcntl
import json
import os
import signal
import subprocess
import sys
import threading
import time

from backend.src.local.config import ROOT, home, load, write_json
from backend.src.local.store import Store


def alive():
    import psutil

    try:
        state = json.loads((home() / "process.json").read_text())
        process = psutil.Process(state["pid"])
        return (
            process.is_running()
            and abs(process.create_time() - state["created"]) < 0.01
            and state["installation"] == load()["installation"]
        )
    except (OSError, ValueError, KeyError, psutil.Error):
        return False


def stop():
    if not alive():
        return
    state = json.loads((home() / "process.json").read_text())
    os.kill(state["pid"], signal.SIGTERM)
    for _ in range(100):
        if not alive():
            return
        time.sleep(0.1)
    raise RuntimeError("stop_timeout")


def supervise():
    import psutil

    from backend.src.local.server import make_server

    os.umask(0o077)
    config = load()
    directory = home()
    with open(directory / "service.lock", "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        store = Store(directory)
        server = make_server(
            config, store
        )  # Bind before recording a running installation.
        write_json(
            directory / "process.json",
            {
                "pid": os.getpid(),
                "created": psutil.Process().create_time(),
                "installation": config["installation"],
            },
        )
        stopping = threading.Event()
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, lambda *_: stopping.set())
        threading.Thread(target=server.serve_forever, daemon=True).start()
        children = {}
        starts = {}
        launched = {}
        failures = {}
        maintenance = 0
        worker_initialized = False
        initialization_failures = 0
        # Native camera libraries can print credential-bearing URLs. Drop child output;
        # only allowlisted structured health enters SQLite/UI.
        try:
            while not stopping.wait(0.5):
                for role in ("capture", "worker"):
                    if role == "worker" and initialization_failures >= 3:
                        continue
                    child = children.get(role)
                    if child and child.poll() is None:
                        if role == "capture":
                            health = store.snapshot()["health"].get("capture", {})
                            if (
                                time.time()
                                - max(
                                    health.get("last_frame", 0),
                                    launched.get(role, time.time()),
                                )
                                > 45
                            ):
                                child.kill()
                                child.wait()
                                store.health(
                                    "capture", "restarting", reason="frame_timeout"
                                )
                                continue
                        if role == "worker":
                            health = store.snapshot()["health"].get("model", {})
                            # Only a report from this launch can establish readiness.
                            # A previous worker's persisted ready state is not evidence.
                            if health.get("updated", 0) >= launched[
                                role
                            ] and health.get("state") in ("ready", "retrying"):
                                worker_initialized = True
                                initialization_failures = 0
                            if (
                                not worker_initialized
                                and time.time() - launched[role] > 180
                            ):
                                child.kill()
                                child.wait()
                                initialization_failures += 1
                                store.health(
                                    "model",
                                    "failed"
                                    if initialization_failures >= 3
                                    else "restarting",
                                    reason="initialization_timeout",
                                    attempts=initialization_failures,
                                    action=(
                                        "Model load exceeded 180 seconds. "
                                        "Check model files, memory and Metal access; "
                                        "use stop/up after three timeouts to retry."
                                    ),
                                )
                                continue
                            with store.db() as db:
                                expired = db.execute(
                                    "SELECT count(*) FROM detections "
                                    "WHERE state='processing' AND lease<?",
                                    (time.time(),),
                                ).fetchone()[0]
                            if expired:
                                child.kill()
                                child.wait()
                                store.health(
                                    "model", "restarting", reason="job_timeout"
                                )
                        continue
                    if time.time() < starts.get(role, 0):
                        continue
                    if role == "worker":
                        # The old child has exited. Release its leases before model
                        # loading, or the watchdog can kill every replacement before
                        # it reaches claim() to recover the interrupted job.
                        store.recover_worker()
                        worker_initialized = False
                    failures[role] = failures.get(role, 0) + 1
                    store.health(
                        "capture" if role == "capture" else "model",
                        "starting" if failures[role] == 1 else "restarting",
                        starts=failures[role],
                    )
                    env = {
                        k: v
                        for k, v in os.environ.items()
                        if not any(s in k for s in ("SUPABASE", "BASETEN", "HF_TOKEN"))
                    }
                    env.update(
                        GHOSTBUSTERS_HOME=str(directory),
                        HF_HUB_OFFLINE="1",
                        PYTHONPATH=str(ROOT),
                        YOLO_CONFIG_DIR=str(directory / "yolo-config"),
                    )
                    launched[role] = time.time()
                    children[role] = subprocess.Popen(
                        [sys.executable, "-m", "backend.src.local.pipeline", role],
                        cwd=ROOT,
                        env=env,
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    starts[role] = time.time() + min(30, 2 ** min(failures[role], 5))
                if time.monotonic() - maintenance > 30:
                    store.retain(
                        config["retention_days"],
                        config["max_image_bytes"],
                        config["min_free_bytes"],
                    )
                    maintenance = time.monotonic()
                store.health("service", "running")
        finally:
            for child in children.values():
                if child.poll() is None:
                    child.terminate()
            for child in children.values():
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait()
            store.health("service", "stopped")
            store.health("capture", "stopped")
            store.health("model", "stopped")
            server.shutdown()
            server.server_close()
            (directory / "process.json").unlink(missing_ok=True)


def start(foreground=False):
    if alive():
        return
    if foreground:
        return supervise()
    with open(home() / "service.log", "ab") as log:
        subprocess.Popen(
            [sys.executable, "-m", "backend.src.local.cli", "serve"],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            start_new_session=True,
        )
    for _ in range(100):
        if alive():
            return
        time.sleep(0.1)
    raise RuntimeError("start_failed: port may be in use; check private service.log")
