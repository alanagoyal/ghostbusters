# Ghostbusters 👻

Watch for trick-or-treaters, classify their costumes, and show detections on a live dashboard. Built for a Raspberry Pi 5 and DoorBird doorbell on Halloween 2025; now accepts a generic camera stream or USB webcam too.

YOLO detects people locally, Baseten names their costumes, and Supabase Storage and Realtime feed a live Next.js dashboard. The supported setup path uses all three.

## Get started

You need a camera with a local RTSP/HTTP stream or a USB webcam, a Mac or Linux computer (including a 64-bit Raspberry Pi), a [Baseten account](https://app.baseten.co), and a [Supabase project](https://supabase.com/dashboard). Install Python 3.11, [uv](https://docs.astral.sh/uv/getting-started/installation/), and Node.js 22 for the dashboard.

```sh
git clone https://github.com/alanagoyal/ghostbusters.git
cd ghostbusters
uv sync --frozen --python 3.11
uv run ghostbusters setup
```

The wizard asks for your camera, Baseten API key, and Supabase URL and keys. It writes `.env` and `frontend/.env.local`, hides credential input, preserves unrelated settings, and rejects backend keys in browser configuration. Nothing starts during setup. For Baseten it offers the hosted vision Model API, so you don't have to provision a dedicated GPU. See [Baseten setup](docs/BASETEN_SETUP.md) for model access and custom endpoints.

**Create the Supabase tables and image bucket:** follow [Supabase setup](docs/SUPABASE_SETUP.md), including the SQL bootstrap and grants. The wizard does not provision accounts or run database SQL. This project uses a public gallery; choose a dedicated project you intend to use for it.

```sh
uv run ghostbusters doctor
```

Doctor checks a camera frame, one small billed Baseten vision request using a synthetic blank image, Supabase backend table access, the public storage bucket, and dashboard read access. It saves no camera image or database record. Each failure includes the relevant next step. It does not prove uploads or Realtime delivery; finish with a real walk-through.

Start the dashboard in a separate terminal:

```sh
cd frontend
npm ci
npm run dev
```

Open `http://localhost:3000/ghostbusters`. Setup already created its environment file. See [dashboard hosting](frontend/SETUP.md) to deploy it; set `NEXT_PUBLIC_BASE_PATH=` before building to serve `/` instead.

Start capture from the repository root:

```sh
uv run ghostbusters start
uv run ghostbusters status
# When Halloween is over:
uv run ghostbusters stop
```

On macOS, `start` installs/enables a launch agent and starts capture, with automatic restart and startup at user login. On Linux, first run `sudo ./setup-service.sh` once; `start` enables/starts that systemd service. `stop` stops the service **and disables automatic startup** until the next `start`. These commands manage the detector, not the dashboard server or your cloud subscriptions. Keep the checkout in place after installation.

For a terminal-only rehearsal use `uv run ghostbusters start --foreground` instead; Ctrl+C stops it. `status` and `stop` manage background services only. Do not run foreground and background capture together. Walk in view of the camera for several seconds, then confirm the photo and classification appear in the dashboard.

See [command reference](docs/CLI.md), [camera setup](docs/CAMERAS.md), [macOS service details](docs/MACOS_SETUP.md), and [Pi deployment](docs/DEPLOYMENT.md).

The detector downloads YOLO weights on first use. It samples every 30 frames, requires two consecutive detections, and waits 30 seconds between captures. These are capture counts, not unique visitor counts. Low-frame-rate cameras take longer to trigger. Generic cameras use the full image; legacy DoorBird configuration defaults to the left 70%. Set normalized `ROI_*` bounds in `.env` to adjust the detection area.

## Images and privacy

When configured, Baseten receives **unblurred person crops**, including crops of possible inflatable costumes. Local saved images and Supabase images blur the detected person's region, but this is not guaranteed anonymization: missed detections and bystanders can remain visible. The existing dashboard/storage design publishes images. Review your framing and sharing settings before running it around visitors.

Successful uploads remove the local image only after all corresponding records are saved. Failed uploads and local-only captures remain on disk; there is no automatic retry queue or retention policy. Monitor disk usage and delete captures when no longer needed. The camera check reads a frame in memory only, though native camera libraries can include connection details in their error messages; redact logs before sharing.

## Run on a Raspberry Pi

See [deployment and recovery](docs/DEPLOYMENT.md) for SSH checks, systemd installation, logs, and a Halloween rehearsal. Install OpenCV runtime libraries on Raspberry Pi OS if needed:

```sh
sudo apt update
sudo apt install -y libgl1 libglib2.0-0 ffmpeg
```

## Development and tests

```sh
uv sync --frozen --python 3.11
uv run python -m unittest discover -s backend/tests/unit -v
uv run ruff check backend/src/camera.py backend/scripts/check_camera.py backend/tests/unit
```

Offline tests use mocks; they do not require a camera, cloud keys, or model weights. The scripts under `backend/tests/integration/` are **manual live checks**, not an offline test suite. Some incur inference charges and write images/rows to the configured database. Use a separate test project and review each script before running it. Fixture images are not bundled; provide your own consented images in the documented fixture folders. To check only Baseten connectivity:

```sh
uv run python -m backend.tests.integration.test_baseten_connection
```

See [CONTRIBUTING.md](CONTRIBUTING.md), [security reporting](SECURITY.md), and the [roadmap](docs/ROADMAP.md). The [original specification](docs/PROJECT_SPEC.md) and [implementation notes](docs/IMPLEMENTATION_NOTES.md) describe the 2025 build; this README describes current setup.

## License

Original project code is MIT licensed; see [LICENSE](LICENSE). Dependencies and model weights retain their own licenses. In particular, Ultralytics YOLO uses AGPL-3.0 or a commercial license; see [third-party notices](THIRD_PARTY_NOTICES.md) before distributing a combined application.
