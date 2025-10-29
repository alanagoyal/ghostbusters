# DoorBird Camera Setup - First Step Complete

## Summary

We've successfully completed the first step of integrating your DoorBird camera! Here's what was accomplished:

## ✅ Connection Details Configured

### DoorBird Device Information
- **Device Name:** Front door
- **Model:** DoorBird D1101KV-F-V2A
- **MAC Address:** [REDACTED]
- **IP Address:** [configured in .env]
- **Intercom ID:** [REDACTED]
- **Firmware Version:** 000150

### API User Created
- **Username:** [configured in .env as DOORBIRD_USERNAME]
- **Password:** [configured in .env as DOORBIRD_PASSWORD]
- **Permissions:** API-Operator enabled (required for RTSP access)

### RTSP URL Format
```
rtsp://<username>:<password>@<ip_address>/mpeg/media.amp
```
(Actual credentials are stored in `.env` file and loaded via environment variables)

## Network Architecture Discovered

Your setup includes:
- **2 physical DoorBird doorbells** (outdoor cameras at doors)
- **3 indoor display systems** (monitors showing doorbell feeds)
- **5 network devices** visible in Eero (all with `bha-` hostnames)

The devices appear to be connected via **Power over Ethernet (PoE)**, which is why:
- They don't show IP addresses directly in Eero
- They appear "offline" in the Eero app (they're behind a PoE switch)
- The DoorBird app works fine (connects directly to the devices)

## Next Steps

### For Raspberry Pi Deployment:

1. **Test RTSP Connection on Raspberry Pi**
   - The test script is ready: `test_doorbird_connection.py`
   - Run it from your Raspberry Pi 5 (which should be on the same network)
   - It will capture a test frame and save it

2. **Install uv (Python Package Manager):**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Install System Dependencies on Raspberry Pi:**
   ```bash
   sudo apt update
   sudo apt install -y python3-opencv gstreamer1.0-plugins-good \
       gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly \
       gstreamer1.0-libav ffmpeg
   ```

4. **Set Up Environment Variables:**
   Create a `.env` file on your Raspberry Pi (see `.env.example` for template):
   ```bash
   DOORBIRD_IP=your_doorbird_ip
   DOORBIRD_USERNAME=your_doorbird_username
   DOORBIRD_PASSWORD=your_doorbird_password

   # Add these when ready:
   BASETEN_API_KEY=your_baseten_key
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```

5. **Install Python Dependencies:**
   ```bash
   uv sync
   ```

6. **Test the Connection:**
   ```bash
   uv run python test_doorbird_connection.py
   ```

   If successful, you should see:
   - ✅ Successfully connected to RTSP stream!
   - ✅ Successfully captured frame!
   - A test frame saved as `test_doorbird_frame.jpg`

## Troubleshooting

### If Connection Fails on Raspberry Pi:

1. **Check Network Connectivity:**
   ```bash
   ping <your_doorbird_ip>
   ```

2. **Verify API Permissions in DoorBird App:**
   - Go to: Settings → Administration → Login → Users
   - Check that your API user has "API-Operator" permission enabled
   - Also ensure "Live Video" or "Video" permission is enabled

3. **Test with HTTP Snapshot (Alternative):**
   If RTSP doesn't work, you can use HTTP snapshots instead:
   ```
   http://<username>:<password>@<ip_address>/bha-api/image.cgi
   ```

## Additional DoorBird Devices

You have 4 other DoorBird devices on your network:
- bha-1CCAE376EB61 (wired)
- bha-1CCAE37770AB0 (wired)
- bha-1CCAE37717D1 (WiFi)
- bha-1CCAE37717D6 (wired)

To set these up later, you'll need to:
1. Identify which device is which (front door, back door, displays)
2. Create API users for each camera (if they're the outdoor doorbells)
3. Get their IP addresses using the same process

## Project Context

This setup is for your **Halloween Costume Classifier** project, which will:
1. Capture video from DoorBird when someone rings the doorbell
2. Detect people using YOLO
3. Send cropped images to Baseten for costume description
4. Log results to Supabase
5. Display live results on a Next.js dashboard

The complete system architecture is documented in `PROJECT_SPEC.md`.

## Status

✅ **FIRST STEP COMPLETE!**

You now have all the connection details needed to start capturing video from your DoorBird camera. The next step is to test this connection from your Raspberry Pi 5 (which should be on your home network with the DoorBird).
