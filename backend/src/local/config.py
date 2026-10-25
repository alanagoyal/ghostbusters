"""Installation-local configuration. Never import baseline cloud environment."""

import json
import os
import secrets
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def home():
    return Path(
        os.environ.get("GHOSTBUSTERS_HOME", ROOT / ".ghostbusters/local")
    ).resolve()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temp = path.with_suffix(".tmp")
    with open(temp, "w", opener=lambda p, f: os.open(p, f, 0o600)) as out:
        json.dump(value, out, indent=2)
    temp.replace(path)
    path.chmod(0o600)


def load():
    return json.loads((home() / "config.json").read_text())


def initialize():
    directory = home()
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    directory.chmod(0o700)
    if (directory / "config.json").exists():
        return load()
    config = {
        "version": 1,
        "installation": uuid.uuid4().hex,
        "storage": "local",
        "inference": "local",
        "token": secrets.token_urlsafe(32),
        "port": 3327,
        "retention_days": 7,
        "max_image_bytes": 2_000_000_000,
        "min_free_bytes": 500_000_000,
        "queue_limit": 32,
        "cooldown_seconds": 30,
        "roi": [0, 1, 0, 1],
        "model": str(ROOT / ".ghostbusters/models/vision-qwen3"),
        "yolo": str(ROOT / ".ghostbusters/models/yolov8n.pt"),
        "camera": None,
    }
    write_json(directory / "config.json", config)
    return config
