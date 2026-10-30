"""Reload the cloud publishing switch without restarting capture."""

import os
from pathlib import Path

from dotenv import dotenv_values


def publishing_enabled(env_path: Path) -> bool:
    # Preserve legacy behavior when unset. Explicit/invalid values fail closed.
    # Read the file each capture so a scheduled toggle needs no service restart.
    try:
        settings = dotenv_values(env_path, interpolate=False)
    except OSError:
        return False
    value = settings.get(
        "PUBLISH_DETECTIONS", os.environ.get("PUBLISH_DETECTIONS", "true")
    )
    return isinstance(value, str) and value.strip().lower() == "true"
