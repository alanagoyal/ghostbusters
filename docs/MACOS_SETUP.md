# Cloud service on macOS

For account-free local inference, use [local setup](LOCAL_SETUP.md). For cloud
configuration and daily start/status/stop commands, use the [cloud CLI guide](CLI.md).

The cloud CLI installs the per-user `com.ghostbusters.detector` launch agent using
this checkout's `.venv/bin/python`. It starts at **user login**, restarts after
exits, and uses `caffeinate -i` to prevent idle sleep. It does not prevent manual
sleep, shutdown or laptop lid sleep, and does not bypass FileVault.

Keep the checkout and interpreter at their installed paths. When moving checkouts,
stop the service from the old checkout, then start it from the configured new one.
Stop foreground capture with Ctrl+C before starting the background service.

## Diagnostics and recovery

```sh
launchctl print "gui/$(id -u)/com.ghostbusters.detector"
tail -f ~/Library/Logs/Ghostbusters/detector.log
```

Detector logs rotate at 10 MB with five backups. Launcher diagnostics use separate
`launcher.log` and `launcher-error.log` files. Review logs before sharing; saved
captures from failed cloud uploads are not rotated automatically.

If installation needs repair, run from the configured checkout as your normal
user, without sudo:

```sh
.venv/bin/python scripts/setup_macos_service.py
```

This replaces and starts the launch agent. The hosted gallery runs independently;
see [frontend setup](../frontend/SETUP.md).
