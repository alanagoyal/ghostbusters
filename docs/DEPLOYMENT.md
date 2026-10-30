# Cloud service on Linux / Raspberry Pi

This runs camera capture and YOLO with cloud classification. Full local vision
requires a supported Mac; see [local setup](LOCAL_SETUP.md). Validate camera and
YOLO performance on your hardware before relying on it.

Follow the [cloud CLI guide](CLI.md) for configuration and daily start/status/stop
commands. After installing dependencies and configuring `.env`, install the
systemd service from the normal checkout owner's account:

```sh
sudo ./setup-service.sh
```

The installer uses the current checkout and invoking user. It enables startup on
boot but does not start capture. Start with `uv run --no-sync ghostbusters start`.

## Diagnostics and recovery

```sh
systemctl status costume-detector --no-pager
systemctl cat costume-detector
journalctl -u costume-detector -n 50 --no-pager
```

Older installations may instead log to `~/costume-detector.log` and
`~/costume-detector-error.log`. Review logs before sharing and redact credentials
and camera URLs.

Before changing a working installation, record its commit and service configuration
and preserve `.env`. Stop capture before manual camera checks to avoid competing
stream connections. If moving checkouts, stop the old service, then rerun the
installer from the configured new checkout.

## Rehearse before Halloween

- Verify a walkthrough, gallery update, and recovery after a network interruption.
- Test after dark with your actual lighting and a group arrival.
- Check disk space, CPU temperature, logs and cloud usage.
- Reboot and confirm automatic startup if enabled.

Failed captures remain on disk and are not retried automatically. Stop capture
after the event and manage local/cloud image retention explicitly.
