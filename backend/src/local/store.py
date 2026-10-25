"""SQLite v1, private images and crash-recoverable bounded classification jobs."""

import contextlib
import json
import os
import shutil
import sqlite3
import time
import uuid
from pathlib import Path


class Store:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.images = self.root / "images"
        self.images.mkdir(exist_ok=True, mode=0o700)
        with self.db() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS detections (
                    id TEXT PRIMARY KEY, created REAL NOT NULL,
                    confidence REAL NOT NULL,
                    bbox TEXT NOT NULL, state TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    due REAL NOT NULL DEFAULT 0, lease REAL NOT NULL DEFAULT 0,
                    costume TEXT, description TEXT, model_confidence REAL,
                    error TEXT,
                    detection_type TEXT NOT NULL DEFAULT 'person');
                CREATE INDEX IF NOT EXISTS jobs ON detections(state,due);
                CREATE TABLE IF NOT EXISTS meta(
                    key TEXT PRIMARY KEY,value TEXT NOT NULL);
                INSERT OR IGNORE INTO meta VALUES ('revision','0');
                PRAGMA user_version=1;
            """)
            columns = {r[1] for r in db.execute("PRAGMA table_info(detections)")}
            if "detection_type" not in columns:
                db.execute(
                    "ALTER TABLE detections ADD COLUMN detection_type TEXT "
                    "NOT NULL DEFAULT 'person'"
                )
        os.chmod(self.root / "gallery.sqlite3", 0o600)

    @contextlib.contextmanager
    def db(self):
        db = sqlite3.connect(self.root / "gallery.sqlite3", timeout=15)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def changed(db):
        db.execute(
            "UPDATE meta SET value=CAST(value AS INTEGER)+1 WHERE key='revision'"
        )

    def health(self, component, state, **details):
        with self.db() as db:
            db.execute(
                "INSERT OR REPLACE INTO meta VALUES (?,?)",
                (
                    "health." + component,
                    json.dumps(dict(state=state, updated=time.time(), **details)),
                ),
            )

    def add(self, jpeg, confidence, bbox, queue_limit=32, detection_type="person"):
        ident = uuid.uuid4().hex
        temporary = self.images / (ident + ".tmp")
        temporary.write_bytes(jpeg)
        temporary.chmod(0o600)
        temporary.replace(self.images / (ident + ".jpg"))
        try:
            with self.db() as db:
                db.execute("BEGIN IMMEDIATE")
                count = db.execute(
                    "SELECT count(*) FROM detections WHERE state IN "
                    "('pending','processing','retry')"
                ).fetchone()[0]
                state = "pending" if count < queue_limit else "queue_full"
                db.execute(
                    (
                        "INSERT INTO "
                        "detections(id,created,confidence,bbox,state,detection_type)"
                        " VALUES (?,?,?,?,?,?)"
                    ),
                    (
                        ident,
                        time.time(),
                        confidence,
                        json.dumps(bbox),
                        state,
                        detection_type,
                    ),
                )
                self.changed(db)
        except Exception:
            (self.images / (ident + ".jpg")).unlink(missing_ok=True)
            raise
        return ident

    def recover_worker(self):
        """Release leases only after the supervisor has confirmed worker death.

        A replacement must not inherit a lease that can expire during model load.
        Attempt counts survive restarts, so repeated crashes still terminate.
        """
        with self.db() as db:
            recovered = db.execute(
                "UPDATE detections SET state=CASE WHEN attempts>=3 THEN "
                "'failed' ELSE 'retry' END,"
                "error='worker_interrupted',lease=0 WHERE state='processing'"
            )
            if recovered.rowcount:
                self.changed(db)

    def claim(self, lease_seconds=120):
        now = time.time()
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            recovered = db.execute(
                (
                    "UPDATE detections SET state=CASE WHEN attempts>=3 THEN "
                    "'failed' ELSE 'retry' END,error='worker_interrupted' WHERE "
                    "state='processing' AND lease<?"
                ),
                (now,),
            )
            if recovered.rowcount:
                self.changed(db)
            row = db.execute(
                (
                    "SELECT * FROM detections WHERE state IN ('pending','retry') "
                    "AND due<=? ORDER BY created LIMIT 1"
                ),
                (now,),
            ).fetchone()
            if row is None:
                return None
            db.execute(
                (
                    "UPDATE detections SET "
                    "state='processing',attempts=attempts+1,lease=? WHERE id=?"
                ),
                (now + lease_seconds, row["id"]),
            )
            self.changed(db)
            return dict(row)

    def finish(self, ident, result=None, error=None):
        with self.db() as db:
            row = db.execute(
                "SELECT attempts,detection_type FROM detections WHERE id=?", (ident,)
            ).fetchone()
            if not row:
                return
            if error:
                attempts = row[0]
                db.execute(
                    "UPDATE detections SET state=?,error=?,due=?,lease=0 WHERE id=?",
                    (
                        "failed" if attempts >= 3 else "retry",
                        error,
                        time.time() + min(60, 2**attempts),
                        ident,
                    ),
                )
            else:
                state = (
                    "rejected"
                    if row["detection_type"] == "inflatable_candidate"
                    and result["costume"].lower() in ("no costume", "unknown")
                    else "complete"
                )
                db.execute(
                    (
                        "UPDATE detections SET "
                        "state=?,costume=?,description=?,model_confidence=?,error=NULL,lease=0"
                        " WHERE id=?"
                    ),
                    (
                        state,
                        result["costume"],
                        result["description"],
                        result["confidence"],
                        ident,
                    ),
                )
            self.changed(db)

    def snapshot(self, include_rejected=False):
        condition = "1=1" if include_rejected else "state!='rejected'"
        with self.db() as db:
            rows = [
                dict(r)
                for r in db.execute(
                    "SELECT * FROM detections WHERE "
                    + condition
                    + " ORDER BY created DESC LIMIT 200"
                )
            ]
            total = db.execute(
                "SELECT count(*) FROM detections WHERE " + condition
            ).fetchone()[0]
            recent = db.execute(
                "SELECT count(*) FROM detections WHERE " + condition + " AND created>?",
                (time.time() - 300,),
            ).fetchone()[0]
            meta = dict(db.execute("SELECT key,value FROM meta"))
        health = {
            k[7:]: json.loads(v) for k, v in meta.items() if k.startswith("health.")
        }
        capture = health.get("capture", {})
        if (
            capture.get("state") == "streaming"
            and time.time() - capture.get("last_frame", 0) > 15
        ):
            capture["state"] = "stale"
            capture["action"] = (
                "No recent frame; waiting for camera reconnect/watchdog."
            )
        for row in rows:
            row["image_url"] = "/api/images/" + row["id"] + ".jpg"
            row["bbox"] = json.loads(row["bbox"])
        return {
            "detections": rows,
            "total": total,
            "recent": recent,
            "revision": int(meta["revision"]),
            "health": health,
        }

    def retain(self, days=7, max_bytes=2_000_000_000, min_free=500_000_000):
        """Evict oldest records/images, including queued work, to keep disk bounded."""
        now = time.time()
        removed = 0
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            rows = list(
                db.execute("SELECT id,created FROM detections ORDER BY created")
            )
            sizes = {p.stem: p.stat().st_size for p in self.images.glob("*.jpg")}
            total = sum(sizes.values())
            free = shutil.disk_usage(self.root).free
            for row in rows:
                if (
                    row["created"] >= now - days * 86400
                    and total <= max_bytes
                    and free >= min_free
                ):
                    continue
                size = sizes.get(row["id"], 0)
                (self.images / (row["id"] + ".jpg")).unlink(missing_ok=True)
                db.execute("DELETE FROM detections WHERE id=?", (row["id"],))
                total -= size
                free += size
                removed += 1
            # Reconcile crash-created orphans; do not race a newly written image.
            ids = {r[0] for r in db.execute("SELECT id FROM detections")}
            for path in self.images.iterdir():
                if path.stem not in ids and path.stat().st_mtime < now - 300:
                    path.unlink()
            if removed:
                self.changed(db)
        ok = shutil.disk_usage(self.root).free >= min_free
        self.health(
            "storage",
            "ready" if ok else "disk_full",
            image_bytes=total,
            retention_days=days,
            removed=removed,
        )
        return ok
