# Making Halloween setup easier

## Implemented in this cleanup

- Generic stream URL and USB camera index alongside legacy DoorBird settings.
- A one-frame connectivity check that does not save or upload images.
- Configurable detection region, network timeouts, preservation of failed uploads.
- Portable service installation, offline tests, and public setup/contribution docs.
- Guided setup and doctor checks for camera, Baseten and Supabase.
- Start/status/stop commands for macOS and Linux services; stopping disables startup.

## Next useful improvements

1. **Fresh-account rehearsal:** walk through setup with a new Supabase project and Baseten account, verify upload/Realtime delivery, and eliminate manual permission fixes.
2. **Setup refinements:** camera preview and visual detection-region selection, clearer authentication/network diagnostics, and an explicit temporary upload check with cleanup. Keep Baseten and Supabase the primary path.
3. **Camera recipes backed by hardware tests:** Reolink/NVR streams, USB webcams, and a Picamera2 adapter. Track exact model/firmware/codec combinations; avoid claiming brand-wide support.
4. **Privacy controls:** optional blur before inference, private storage/signed URLs, a configurable retention period, and cropped output that excludes bystanders.
5. **Event handling:** time-based frame sampling, bounding-box tracking to reduce duplicate counts, and a durable upload retry queue with disk limits.
6. **Release rehearsal:** test a fresh 64-bit Pi install, a night-time stream, network loss, reboot recovery, and a long-running session. Record resource use and known limitations.

Cloud-only doorbell bridges add account/session maintenance and vendor-specific failure modes. Prioritize direct local streams and USB cameras first, then add bridges only with an actively maintained adapter and reproducible tests.
