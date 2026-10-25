"""Independent capture and classification processes, supervised by the local app."""

import json
import os
import threading
import time

from backend.src.local.config import home, load
from backend.src.local.store import Store


def process_frame(frame, model, store, config, last_saved=None, now=None):
    import cv2

    h, w = frame.shape[:2]
    left, right, top, bottom = config["roi"]
    region = frame[int(top * h) : int(bottom * h), int(left * w) : int(right * w)]
    ids = []
    now = time.monotonic() if now is None else now
    saved_types = set()
    for result in model(region, verbose=False):
        for box in result.boxes:
            if int(box.cls[0]) not in (0, 2, 14, 16, 17) or float(box.conf[0]) < 0.5:
                continue
            detection_type = (
                "person" if int(box.cls[0]) == 0 else "inflatable_candidate"
            )
            # Suppress repeated saves, never person detection itself. A parked car
            # candidate must not hide a person entering during its cooldown.
            if (
                last_saved is not None
                and now - last_saved.get(detection_type, float("-inf"))
                < config["cooldown_seconds"]
            ):
                continue
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            crop = region[
                max(0, y1) : min(region.shape[0], y2),
                max(0, x1) : min(region.shape[1], x2),
            ]
            if not crop.size:
                continue
            ok, jpeg = cv2.imencode(".jpg", crop)
            if ok:
                ids.append(
                    store.add(
                        jpeg.tobytes(),
                        float(box.conf[0]),
                        [
                            x1 + int(left * w),
                            y1 + int(top * h),
                            x2 + int(left * w),
                            y2 + int(top * h),
                        ],
                        config["queue_limit"],
                        detection_type,
                    )
                )
                saved_types.add(detection_type)
    if last_saved is not None:
        for detection_type in saved_types:
            last_saved[detection_type] = now
    return ids


def capture():
    from ultralytics import YOLO

    from backend.src.local.cameras import refresh, stream

    config = load()
    store = Store(home())
    store.health("capture", "starting")
    model = YOLO(config["yolo"])
    credentials = (
        json.loads((home() / "camera-secret.json").read_text())
        if (home() / "camera-secret.json").exists()
        else {}
    )
    latest = [None, 0]
    lock = threading.Lock()

    def read():
        failures = 0
        while True:
            try:
                camera = refresh(config["camera"])
                if credentials and credentials.get("identity") != camera["identity"]:
                    raise ValueError("credential_identity_mismatch")
                for frame in stream(camera, credentials):
                    with lock:
                        latest[:] = [frame, time.time()]
                    failures = 0
                raise RuntimeError("disconnected")
            except Exception:
                failures += 1
                store.health(
                    "capture",
                    "reconnecting",
                    failures=failures,
                    action=(
                        "Check power, LAN, camera permission and local streaming."
                        " Run camera-check when stopped."
                    ),
                )
                time.sleep(min(30, 2 ** min(failures, 5)))

    threading.Thread(target=read, daemon=True).start()
    last_saved = {}
    sampled_frames = 0
    seen = 0
    while True:
        with lock:
            frame, stamp = latest
        if frame is None or time.time() - stamp > 15:
            store.health(
                "capture",
                "stale",
                last_frame=stamp,
                action="No recent frame; reconnecting. Check LAN/camera access.",
            )
            time.sleep(1)
            continue
        if stamp == seen:
            time.sleep(0.2)
            continue
        seen = stamp
        import shutil

        if shutil.disk_usage(home()).free < config["min_free_bytes"]:
            store.health("storage", "disk_full")
            time.sleep(5)
            continue
        process_frame(frame, model, store, config, last_saved=last_saved)
        sampled_frames += 1
        store.health(
            "capture",
            "streaming",
            last_frame=stamp,
            last_scan=time.time(),
            sampled_frames=sampled_frames,
        )
        time.sleep(0.5)


def worker_once(store, classifier):
    job = store.claim()
    if job is None:
        return False
    try:
        result = classifier.classify((store.images / (job["id"] + ".jpg")).read_bytes())
        store.finish(job["id"], result=result)
        store.health("model", "ready", last_success=time.time())
    except Exception:
        # Do not persist SDK messages (could contain image data/credentials).
        store.finish(job["id"], error="classification_failed")
        store.health(
            "model",
            "retrying",
            action=(
                "Check model files and available memory; three attempts per detection."
            ),
        )
    return True


def worker():
    from backend.src.local.vision import LocalVision

    os.environ["HF_HUB_OFFLINE"] = "1"
    config = load()
    store = Store(home())
    store.health("model", "loading")
    classifier = LocalVision(config["model"])
    store.health("model", "ready")
    heartbeat = 0
    while True:
        if not worker_once(store, classifier):
            if time.monotonic() - heartbeat > 10:
                store.health("model", "ready")
                heartbeat = time.monotonic()
            time.sleep(0.5)


if __name__ == "__main__":
    import fcntl
    import sys

    # Exclusive child lock also protects restart after abrupt supervisor death.
    with open(home() / (sys.argv[1] + ".lock"), "w") as child_lock:
        fcntl.flock(child_lock, fcntl.LOCK_EX)
        parent = os.getppid()

        def watch_parent():
            while True:
                time.sleep(2)
                if os.getppid() != parent:
                    os._exit(1)

        threading.Thread(target=watch_parent, daemon=True).start()
        {"capture": capture, "worker": worker}[sys.argv[1]]()
