# Legacy cloud deployment on Linux / Raspberry Pi

This is the Baseten/Supabase path, not local vision. Full local classification requires a supported Mac; see [LOCAL_SETUP.md](LOCAL_SETUP.md).

## Recover an existing installation

Power on the Pi and confirm it is connected to the same network as your SSH client. A powered-off Pi cannot be recovered through SSH. If its `.local` name does not resolve, find its current address in your router's client list.

```sh
ssh YOUR_USER@YOUR_PI_ADDRESS
hostname
uptime
df -h /
systemctl status costume-detector --no-pager
systemctl is-enabled costume-detector
journalctl -u costume-detector -n 50 --no-pager
```

Older installations write `~/costume-detector.log` and `~/costume-detector-error.log` instead of journald. Inspect those too. Don't paste unredacted credentials or camera URLs into issues.

Before changing an existing installation, record `git status --short`, its current commit (`git rev-parse HEAD`), and service configuration (`systemctl cat costume-detector`). Preserve its `.env`. Stop the detector before a manual camera test to avoid competing stream connections:

```sh
sudo systemctl stop costume-detector
cd /path/to/ghostbusters
uv sync --frozen --python 3.11
uv run python -m unittest discover -s backend/tests/unit -v
uv run python -m backend.scripts.check_camera
```

## Install the service

Run as the normal account that owns the checkout, after installing dependencies and configuring `.env`:

```sh
sudo ./setup-service.sh
sudo systemctl start costume-detector
sudo systemctl status costume-detector --no-pager
sudo journalctl -u costume-detector -f
```

The installer generates the service using your current checkout and invoking user. It enables startup on boot but does not start the detector.

```sh
sudo systemctl stop costume-detector
sudo systemctl restart costume-detector
sudo systemctl disable costume-detector  # Prevent startup on the next boot
```

## Rehearse before Halloween

- Run the frame check, then test with an adult volunteer or a consented recording.
- Confirm the ROI, two consecutive detections, cooldown, costume response, and dashboard update.
- Test after dark with your actual lighting and a group arrival.
- Confirm network interruption recovery and that failed uploads leave local files.
- Check disk space, CPU temperature (`vcgencmd measure_temp`), service logs, and cloud usage.
- Reboot and confirm the service starts if enabled. Keep the previously working commit available for rollback.

The current backend keeps local failed captures but does not retry them automatically. Stop the service after the event and manage local/cloud image retention explicitly.
