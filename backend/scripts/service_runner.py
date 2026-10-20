"""Run the detector with bounded logs and clean service shutdown."""

import logging
import os
import re
import signal
import subprocess
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def redact(message):
    """Native video backends may include credential-bearing URLs in errors."""
    return re.sub(r"(rtsps?|https?)://[^\s/]*@", r"\1://[redacted]@", message)


def main():
    log_dir = Path(os.environ.get("GHOSTBUSTERS_LOG_DIR", "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("ghostbusters")
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(
        log_dir / "detector.log", maxBytes=10_000_000, backupCount=5
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    logger.addHandler(handler)
    child = subprocess.Popen(
        [sys.executable, "-u", "-m", "backend.scripts.main"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    stopping = False

    def stop(signum, frame):
        nonlocal stopping
        stopping = True
        if child.poll() is None:
            child.send_signal(signal.SIGINT)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    inhibitor = None
    if sys.platform == "darwin":
        inhibitor = subprocess.Popen(
            ["/usr/bin/caffeinate", "-i", "-w", str(os.getpid())]
        )
    logger.info("Starting detector (pid %s)", child.pid)
    try:
        for line in child.stdout:
            logger.info(redact(line.rstrip()))
        result = child.wait()
        logger.info("Detector exited with status %s", result)
        return 0 if stopping else result
    finally:
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
        if inhibitor:
            inhibitor.terminate()
            inhibitor.wait()
        handler.close()


if __name__ == "__main__":
    raise SystemExit(main())
