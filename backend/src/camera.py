"""Camera selection shared by the live detector and the connection check."""

import os
from urllib.parse import quote


def camera_source(env=None):
    """Prefer a generic stream/device, falling back to legacy DoorBird settings."""
    env = os.environ if env is None else env
    source = env.get("CAMERA_SOURCE", "").strip()
    if source:
        return int(source) if source.isdecimal() else source
    required = ("DOORBIRD_USERNAME", "DOORBIRD_PASSWORD", "DOORBIRD_IP")
    if not all(env.get(key) for key in required):
        raise ValueError("Set CAMERA_SOURCE or all three DOORBIRD_* settings in .env")
    user, password, host = (env[key] for key in required)
    credentials = f"{quote(user, safe='')}:{quote(password, safe='')}"
    return f"rtsp://{credentials}@{host}/mpeg/media.amp"


def region_of_interest(env=None):
    """Validate normalized bounds; preserve the legacy DoorBird default."""
    env = os.environ if env is None else env
    default_right = "1.0" if env.get("CAMERA_SOURCE", "").strip() else "0.7"
    keys = ("ROI_X_MIN", "ROI_X_MAX", "ROI_Y_MIN", "ROI_Y_MAX")
    values = tuple(
        float(env.get(k, d))
        for k, d in zip(keys, ("0", default_right, "0", "1"), strict=True)
    )
    left, right, top, bottom = values
    if not (0 <= left < right <= 1 and 0 <= top < bottom <= 1):
        raise ValueError("ROI bounds must satisfy 0 <= min < max <= 1")
    return values


def open_camera(source):
    """Set FFmpeg network timeouts at open time, where OpenCV accepts them."""
    import cv2

    if isinstance(source, str) and source.startswith(
        ("rtsp://", "rtsps://", "http://", "https://")
    ):
        os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp")
        cap = cv2.VideoCapture(
            source,
            cv2.CAP_FFMPEG,
            [
                cv2.CAP_PROP_OPEN_TIMEOUT_MSEC,
                10000,
                cv2.CAP_PROP_READ_TIMEOUT_MSEC,
                10000,
            ],
        )
    else:
        cap = cv2.VideoCapture(source)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap
