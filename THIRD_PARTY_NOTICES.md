# Third-party licenses and assets

The MIT license covers original project code. It does not relicense dependencies, model weights, or third-party images.

- **Ultralytics / YOLOv8**: upstream offers AGPL-3.0 and commercial licensing. Review [Ultralytics licensing](https://www.ultralytics.com/license) for the obligations of a combined application. Do not assume the repository's MIT license makes the YOLO-based stack MIT-only.
- **Other dependencies**: their licenses accompany the installed packages; see `uv.lock` and `frontend/package-lock.json` for resolved versions.
- **Costume fixtures**: images in local development checkouts are not included in version control. Their provenance and redistribution rights have not been established by this cleanup. Before publishing a fixture collection, document its source and permission. New fixtures should be synthetic or explicitly consented and licensed.

Model weights are downloaded separately and excluded from version control.
