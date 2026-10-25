# Test fixtures

The tracked, redistributable local release fixtures are in [local/](local/README.md).
They are public licensed photographs, not owner doorstep footage. All five JPEGs
are explicitly included by .gitignore and survive a source clone.

After downloading the local model and building the frontend, run the real offline
pipeline test from the repo root:

```sh
uv run --no-sync python -m backend.tests.local_e2e --model .ghostbusters/models/vision-qwen3 --report /private/path/e2e.json
```

This creates and removes a disposable fixture-video installation, runs actual YOLO
and local vision, verifies SQLite/images/live events and restart persistence, and
never reads cloud configuration or opens the household camera. Metal GPU access
and the supported Mac hardware are required. Unit tests remain offline and mocked.

Private owner photographs are not distributed. Do not copy camera captures into this collection. The public stills allow model testing before camera setup; they do not prove detection quality on a real doorstep.
