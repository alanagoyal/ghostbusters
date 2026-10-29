"""Publish detector liveness without photos, camera details, or database changes."""

import json
import time
from datetime import datetime, timezone

from supabase import ClientOptions, create_client

STATUS_PATH = "_system/detector-status.json"
HEARTBEAT_INTERVAL = 15


class DetectorHeartbeat:
    def __init__(self, url, key, bucket_name="detection-images"):
        # A status outage must not hold up capture for the normal storage timeout.
        client = create_client(url, key, options=ClientOptions(storage_client_timeout=5))
        self.bucket = client.storage.from_(bucket_name)
        self.last_attempt = float("-inf")
        self.last_state = None

    def report(self, running):
        """Call with True only after YOLO successfully processes a camera frame."""
        now = time.monotonic()
        if running == self.last_state and now - self.last_attempt < HEARTBEAT_INTERVAL:
            return
        self.last_attempt = now
        self.last_state = running
        payload = json.dumps({
            "running": running,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).encode()
        try:
            self.bucket.upload(STATUS_PATH, payload, file_options={
                "content-type": "application/json",
                "cache-control": "0",
                "upsert": "true",
            })
        except Exception:
            # Do not print SDK errors: these can contain credentials or URLs.
            print("⚠️ Could not update detector status; the gallery will show offline if it expires")
