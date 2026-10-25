# Legacy cloud service on macOS

For account-free local inference, use [LOCAL_SETUP.md](LOCAL_SETUP.md). The commands below manage the older Baseten/Supabase service, not the local supervisor. Do not use its dependency sync command in a local-vision installation.

A Mac can run the same backend as the Raspberry Pi. Keep it on a network that can reach the camera. Install Python dependencies from the repository root:

```sh
uv sync --frozen --python 3.11
cp .env.example .env  # Only for a new setup; preserve an existing .env.
# Configure the camera and optional cloud services.
uv run python -m backend.scripts.check_camera
uv run python -m backend.scripts.main
```

Stop the foreground detector with Ctrl+C before installing the service. Preserve other installations; investigate camera stream limits if simultaneous capture fails.

## Automatic startup and restart

From the repository root, as your normal user (without sudo):

```sh
.venv/bin/python scripts/setup_macos_service.py
```

This installs and starts `~/Library/LaunchAgents/com.ghostbusters.detector.plist`, using the checkout's `.venv/bin/python`. The agent starts at **user login**, restarts after exits, and keeps the Mac from idle-sleeping while running via `caffeinate -i`. It does not prevent manual sleep, shutdown, or laptop lid sleep. After a restart, log in to start the agent; this does not enable automatic login or bypass FileVault. Keep the checkout and interpreter at their installed paths, and rerun the installer if they move.

```sh
# Status
launchctl print "gui/$(id -u)/com.ghostbusters.detector"

# Live log
tail -f ~/Library/Logs/Ghostbusters/detector.log

# Stop (including its current detector process)
launchctl bootout "gui/$(id -u)/com.ghostbusters.detector"

# Start again
launchctl bootstrap "gui/$(id -u)" ~/Library/LaunchAgents/com.ghostbusters.detector.plist

# Restart a running service
launchctl kickstart -k "gui/$(id -u)/com.ghostbusters.detector"
```

`bootout` stops the service for the current login session. To disable future login starts too, run `launchctl disable "gui/$(id -u)/com.ghostbusters.detector"`; the installer re-enables it when run again.

Detector logs rotate at 10 MB with five backups. Launcher diagnostics use separate `launcher.log` and `launcher-error.log` files. Logs redact credential-bearing HTTP/RTSP URLs, but review other content before sharing. Saved local captures are not rotated automatically; monitor disk space, particularly during cloud outages.

The Next.js dashboard can remain on its existing hosting: it reads Supabase independently of the backend machine. For local dashboard development, follow the frontend setup guide.
