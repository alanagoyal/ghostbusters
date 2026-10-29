"""Rerunnable thumbnail backfill for an existing configured cloud gallery."""

import argparse
import json
import re
from urllib.parse import unquote, urlparse

from backend.src.clients.supabase_client import SupabaseClient


def object_path(value: str, project_url: str) -> str | None:
    if "://" in value:
        url = urlparse(value)
        base = urlparse(project_url)
        prefix = "/storage/v1/object/public/detection-images/"
        if (url.scheme, url.netloc) != (
            base.scheme,
            base.netloc,
        ) or not url.path.startswith(prefix):
            return None
        value = unquote(url.path[len(prefix) :])
    if (
        not value
        or value.startswith("/")
        or ".." in value
        or re.search(r"[?#\\\x00-\x1f]", value)
    ):
        return None
    return value


def backfill(client: SupabaseClient, limit: int = 200, dry_run: bool = False) -> dict:
    # Page through all rows in scope, with a stable order and no photo URLs in output.
    rows = (
        client.client.table("person_detections")
        .select("id,image_url")
        .order("timestamp", desc=True)
        .order("id", desc=True)
        .limit(limit)
        .execute()
        .data
    )
    counts = {"examined": len(rows), "updated": 0, "skipped": 0, "failed": 0}
    uploaded = {}
    for row in rows:
        value = row.get("image_url")
        path = object_path(value, client.url) if value else None
        if not path or re.search(r"/gallery-v1/[a-f0-9]{64}/original\.jpg$", path):
            counts["skipped"] += 1
            continue
        if dry_run:
            counts["updated"] += 1
            continue
        try:
            if path not in uploaded:
                image = client.client.storage.from_(client.bucket_name).download(path)
                uploaded[path] = client.upload_detection_bytes(image)
            media = uploaded[path]
            if not media or not client.update_detection_media(row["id"], value, media):
                counts["failed"] += 1
            else:
                counts["updated"] += 1
        except Exception:
            counts["failed"] += 1
    return {**counts, "dry_run": dry_run}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--limit", type=int, default=200, help="Latest records to examine (1–1000)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Count candidates without downloads or writes",
    )
    args = parser.parse_args()
    if not 1 <= args.limit <= 1000:
        parser.error("--limit must be between 1 and 1000")
    result = backfill(SupabaseClient(), args.limit, args.dry_run)
    print(json.dumps(result))
    return 1 if result["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
