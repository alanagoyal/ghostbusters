# Ghostbusters — local-first Halloween 2026

Clone the repository, open it with your coding agent, and say:

```sh
git clone https://github.com/alanagoyal/ghostbusters.git
cd ghostbusters
```

> Get Ghostbusters working with my doorbell. It is a <brand/model> on the Wi-Fi network this computer is on.

The default is a private costume gallery on your computer: YOLO detection, local
vision classification, SQLite records, local photos and live updates. No account,
credit card or Docker. The agent follows [the complete local setup runbook](docs/LOCAL_SETUP.md).
You may need to enter your camera login privately, enable local streaming, allow
camera/network access, or choose a device.

**Tested hosts:** Apple M4 Mac mini (16 GB) and M2 MacBook Air (24 GB), Python 3.11. Full local vision uses
Apple's Metal GPU; Linux, Windows and Raspberry Pi full-local inference are not
supported by this release. [Model measurements and limits](docs/LOCAL_BENCHMARK.md).

**Cameras:** DoorBird local API, USB adapter, and discoverable ONVIF/RTSP adapter.
See the runbook for the distinction between implemented and hardware-tested support.
Vendor-cloud-only doorbells need a separate adapter; compatibility is not universal.

```sh
uv sync --frozen --python 3.11 --extra local
uv run --no-sync ghostbusters local setup --brand doorbird
uv run --no-sync ghostbusters local models
uv run --no-sync ghostbusters local build
uv run --no-sync ghostbusters local camera-check --seconds 15
uv run --no-sync ghostbusters local up
uv run --no-sync ghostbusters local link
```

Setup is resumable and emits JSON actions; provide credentials only through a private
file as described in the runbook. `local status` reports health; `local stop` stops
only this install. Photos stay private and unblurred locally, are deleted under the
retention/disk policy, and require the private gallery access link. Costume guesses
can be wrong, and counts represent detections rather than unique visitors.

Existing Baseten/Supabase installs keep their configured behavior.
Manual cloud setup is explicit: `uv run --no-sync ghostbusters setup --provider baseten`.
See [legacy cloud CLI operation](docs/CLI.md).

[Test stills and camera-free verification](backend/tests/fixtures/README.md) · [Contributing](CONTRIBUTING.md) · [Privacy](SECURITY.md)
