"""Bounded probe isolated from native-library diagnostics; frames stay private."""

import json
import sys
import time

from backend.src.local.cameras import refresh, stream
from backend.src.local.config import home, load


def main():
    config = load()
    camera = refresh(config["camera"])
    path = home() / "camera-secret.json"
    credentials = json.loads(path.read_text()) if path.exists() else {}
    if credentials and credentials.get("identity") != camera["identity"]:
        raise ValueError("credential_identity_mismatch")
    start = time.monotonic()
    count = 0
    frame = None
    duration = int(sys.argv[1])
    completed = False
    for frame in stream(camera, credentials):  # noqa: B007 - final frame used below
        count += 1
        if time.monotonic() - start >= duration:
            completed = True
            break
    if not completed:
        print(
            json.dumps(
                {
                    "status": "action_required",
                    "reason": "stream_ended_early",
                    "frames": count,
                    "seconds": time.monotonic() - start,
                    "requested_seconds": duration,
                    "action": (
                        "Check camera availability and local streaming; "
                        "stream ended before the requested duration."
                    ),
                }
            )
        )
        return 2
    if frame is None or count < 2:
        raise ValueError("no_continuous_frames")
    if sys.argv[2] == "1":
        import cv2

        cv2.imwrite(str(home() / "preview.jpg"), frame)
        (home() / "preview.jpg").chmod(0o600)
    print(
        json.dumps(
            {
                "status": "ok",
                "frames": count,
                "seconds": time.monotonic() - start,
                "width": frame.shape[1],
                "height": frame.shape[0],
                "preview_saved": sys.argv[2] == "1",
            }
        )
    )


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        print(
            json.dumps(
                {
                    "status": "action_required",
                    "action": (
                        "Check camera credentials, streaming permission, "
                        "LAN reachability and camera availability."
                    ),
                }
            )
        )
        sys.exit(2)
