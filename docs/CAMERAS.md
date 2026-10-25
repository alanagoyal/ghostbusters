# Camera sources for the legacy cloud backend

For local DoorBird discovery, USB or ONVIF setup, follow [LOCAL_SETUP.md](LOCAL_SETUP.md). The `.env` and ROI behavior below applies only to the older Baseten/Supabase runner.

The backend needs frames readable by OpenCV on the machine running it. Set `CAMERA_SOURCE` in `.env`; this takes precedence over DoorBird variables. Start with `uv run python -m backend.scripts.check_camera` from the repository root.

| Source | Configuration | Status |
| --- | --- | --- |
| DoorBird | Three `DOORBIRD_*` variables; leave `CAMERA_SOURCE` blank | Original hardware integration |
| USB webcam | `CAMERA_SOURCE=0` (or another device index) | Implemented; verify on your hardware |
| RTSP camera or NVR | `CAMERA_SOURCE=rtsp://…` | Implemented through OpenCV/FFmpeg; model-specific URLs |
| HTTP video stream | `CAMERA_SOURCE=http://…` | Requires a continuous stream OpenCV can decode, not a snapshot page |
| Recorded video | `CAMERA_SOURCE=/absolute/path/clip.mp4` | Useful for a rehearsal; live runner reconnects/replays at EOF |

## DoorBird

Follow [DoorBird setup](DOORBIRD_SETUP.md). Existing installations can keep their `.env` unchanged. Their original x=0..0.7 region remains the default.

## Reolink and other RTSP cameras

Enable RTSP if your model supports it and use the manufacturer's stream URL. Reolink documents stream configuration and compatibility in its [RTSP guide](https://support.reolink.com/articles/900000630706-Introduction-to-RTSP/). Support varies by camera and whether an NVR/hub is involved. These devices have not been hardware-tested with this repo. Start with a lower-resolution H.264 stream if decoding is slow.

For any other brand, copy its documented RTSP URL into `CAMERA_SOURCE`. URL-encode special characters in the username/password. An app's ability to show live video does not establish that it exports a compatible local stream. Cloud-only doorbells need a separately configured bridge that exports a compatible stream; this project does not implement vendor account login or cloud-stream discovery. A USB webcam is the simplest path without that integration.

## USB and Raspberry Pi cameras

A USB camera must be attached to the backend machine. On Linux, inspect `/dev/video*` and ensure your user can access the device (often through the `video` group). Browser camera permissions are unrelated. A Raspberry Pi CSI camera may need a libcamera/Picamera2 adapter; that adapter is not included.

## Frame your doorstep

Set bounds between 0 and 1; x increases left-to-right, y top-to-bottom:

```dotenv
ROI_X_MIN=0.1
ROI_X_MAX=0.8
ROI_Y_MIN=0.2
ROI_Y_MAX=1.0
```

A detection qualifies when its bounding-box center is inside the region. ROI filters detections, not pixels: saved images still contain the full scene. It also does not prevent all classifier calls outside the ROI during inflatable validation. Use camera framing to exclude areas you do not want captured.

## Troubleshooting

- Verify the camera is powered and reachable from the backend machine.
- Test the URL locally with a video player; avoid posting credential-bearing URLs or logs.
- Use a camera account with live-view access; verify RTSP is enabled and connection limits are not exhausted.
- Network streams use FFmpeg with 10-second open/read timeouts and RTSP-over-TCP. Unsupported codecs/backends may fail to open.
- For USB, try another index and close other applications using the device.
