# Third-party licenses and assets

The MIT license covers original project code. It does not relicense dependencies, model weights, or third-party images.

- **Ultralytics / YOLOv8**: upstream offers AGPL-3.0 and commercial licensing. Review [Ultralytics licensing](https://www.ultralytics.com/license) for the obligations of a combined application. Do not assume the repository's MIT license makes the YOLO-based stack MIT-only.
- **Other dependencies**: their licenses accompany the installed packages; see `uv.lock` and `frontend/package-lock.json` for resolved versions.
- **Test photographs**: the five redistributable JPEGs in [backend/tests/fixtures/local](backend/tests/fixtures/local/README.md) have individual source, author and license notices. Their licenses cover those images, not the code. Private owner/camera fixtures are excluded. No subject model releases are claimed.

Model weights are downloaded separately and excluded from version control.

## Local-first vision and fixtures

Local model: Qwen3-VL-4B-Instruct, quantized by mlx-community, Apache License 2.0.
Pinned public revision and benchmark details: docs/LOCAL_BENCHMARK.md. MLX and
MLX-VLM are separate dependencies; retain their installed license files.
Ultralytics YOLOv8n remains the detector; its AGPL/commercial licensing applies.
Photographic fixture authors, source pages, licenses and resize modifications are
listed in backend/tests/fixtures/local/README.md. The held-out witch derivative is
CC BY-SA 3.0; other fixtures retain their individually stated licenses.
