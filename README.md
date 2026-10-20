# Ghostbusters 👻

Ghostbusters is a small edge inference system to detect & classify trick-or-treaters at your front door. Originally built for Halloween 2025.

I built it with a Raspberry Pi and DoorBird doorbell. You can use a Mac or 64-bit Linux computer that runs Python 3.11, OpenCV, and PyTorch, with a USB webcam or an OpenCV-compatible local RTSP/HTTP camera stream. It needs access to the camera and an internet connection for Baseten and Supabase.

YOLO detects people, [Baseten](https://app.baseten.co) classifies costumes, and [Supabase](https://supabase.com/dashboard) powers the live gallery.

## Setup

You'll need:

- A Mac, Linux computer, or 64-bit Raspberry Pi
- A USB webcam or camera with a local RTSP/HTTP stream ([camera guide](docs/CAMERAS.md))
- Python 3.11, [uv](https://docs.astral.sh/uv/getting-started/installation/), and Node.js 22
- Baseten and Supabase accounts

```sh
git clone https://github.com/alanagoyal/ghostbusters.git
cd ghostbusters
uv sync --frozen --python 3.11
uv run ghostbusters setup
```

`setup` asks for your camera and API keys, then writes the backend and dashboard config. It uses [Baseten's hosted API](docs/BASETEN_SETUP.md); no dedicated GPU needed.

Next, run the SQL and grants in the [Supabase guide](docs/SUPABASE_SETUP.md) to create the tables and image bucket. Then check your connections:

```sh
uv run ghostbusters doctor
```

This checks the camera, Baseten, and Supabase. It makes one small billed inference request using a blank image; it doesn't save or upload camera footage.

## Run it

Start the dashboard in a separate terminal:

```sh
cd frontend
npm ci
npm run dev
```

Open [localhost:3000/ghostbusters](http://localhost:3000/ghostbusters). To publish it, follow the [hosting guide](frontend/SETUP.md).

From the repo root:

```sh
# Linux only: install the service once
sudo ./setup-service.sh

# Start capture
uv run ghostbusters start
uv run ghostbusters status

# Done for the night
uv run ghostbusters stop
```

`start` runs in the background and enables startup at login on Mac or boot on Linux. `stop` disables automatic startup too. These commands control capture, not the dashboard or cloud resources.

Walk in front of the camera for several seconds and check that your photo and classification appear in the gallery. This verifies uploads and live updates beyond what `doctor` checks.

For a foreground run, use `uv run ghostbusters start --foreground` and stop with Ctrl+C. Don't run both modes at once. More: [commands](docs/CLI.md) · [Mac](docs/MACOS_SETUP.md) · [Pi/Linux](docs/DEPLOYMENT.md).

## Before Halloween

- **Framing:** set `ROI_*` in `.env` to choose the detection area. Saved images still include the full frame.
- **Timing:** detection requires two samples, taken every 30 frames, with a 30-second capture cooldown. Counts aren't unique visitors.
- **Images:** Baseten receives unblurred person crops. The gallery is public. Saved photos blur detected people, but may still show bystanders or missed detections.
- **Storage:** failed uploads stay on disk. There's no automatic retry or retention policy.
- **Credentials:** keep backend keys out of the frontend and redact logs before sharing. Cloud usage may incur charges.

## Development

```sh
uv run python -m unittest discover -s backend/tests/unit -v
```

Unit tests run offline. Integration scripts use live services and may incur charges or create records; use a test project.

[Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Roadmap](docs/ROADMAP.md)

## License

[MIT](LICENSE) for original code. Dependencies and model weights have separate terms, including Ultralytics' AGPL/commercial license. See [third-party notices](THIRD_PARTY_NOTICES.md).
