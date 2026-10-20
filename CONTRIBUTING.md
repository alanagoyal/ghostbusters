# Contributing

Small, focused fixes and reproducible camera setup reports are welcome. Open an issue before a large integration so we can agree on scope.

## Local checks

Use Python 3.11, `uv sync --frozen`, and run:

```sh
uv run python -m unittest discover -s backend/tests/unit -v
uv run ruff check backend/src/camera.py backend/scripts/check_camera.py backend/tests/unit
cd frontend
npm ci
npm run typecheck
npm run build
```

The legacy backend has existing lint debt; keep new modules clean. Add offline regression tests for behavior changes. Do not make CI depend on live cameras, cloud credentials, paid inference, or a production database. Manual integration scripts may upload images and create records; use a separate test project.

## Pull requests

Explain the problem, behavior change, and validation. For camera support, include model, firmware, OS, transport/codec, and whether a full detection was tested. Redact credentials, IPs, tokens, and private footage. Use synthetic or explicitly consented fixtures, and record their source/license. Do not contribute identifiable visitor images.

Keep `.env`, captures, model weights, and local tooling files out of commits. Follow the existing Python/TypeScript style. Treat contributors respectfully and focus feedback on the code. Contributions of original code are under the project's MIT license; third-party dependencies retain their licenses.
