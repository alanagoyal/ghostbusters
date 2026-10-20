# DoorBird setup

The original deployment used a DoorBird D1101KV-F-V2A. Other models need a compatible RTSP live stream.

1. Connect the backend computer and DoorBird to a network where they can reach each other.
2. Find the doorbell's current local IP address in your router or DoorBird administration settings. A DHCP reservation helps keep it stable.
3. Create a dedicated camera user with API-Operator/live-video access using your device's administration interface.
4. Leave `CAMERA_SOURCE` blank and set these values in `.env`:

   ```dotenv
   DOORBIRD_IP=192.168.1.50
   DOORBIRD_USERNAME=your-camera-user
   DOORBIRD_PASSWORD=your-camera-password
   ```

5. From the repository root, run:

   ```sh
   uv run python -m backend.scripts.check_camera
   ```

The backend builds `rtsp://<username>:<password>@<ip>/mpeg/media.amp`, encoding credentials automatically. The check reads one frame without saving it. If it fails, check permissions, network reachability, credentials, and whether another client is using the stream.

Set `ROI_*` explicitly for your camera's view; the legacy default covers the left 70% of the image. See [camera configuration](CAMERAS.md).
