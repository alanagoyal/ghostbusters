# Backend Setup Guide

This guide covers setting up the Python backend for person detection on your Raspberry Pi.

## Prerequisites

- Raspberry Pi 5 (8GB recommended)
- Python 3.10 or higher
- DoorBird camera configured ([see DoorBird Setup](doorbird.md))
- Supabase project created ([see Supabase Setup](supabase.md))

## Installation

### 1. Install uv (Python Package Manager)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone Repository

```bash
git clone <your-repo-url>
cd <repo-name>
```

### 3. Install Dependencies

```bash
cd backend
uv sync
```

This will install all dependencies specified in `pyproject.toml`:
- opencv-python (video capture)
- ultralytics (YOLOv8)
- supabase (database client)
- python-dotenv (environment variables)

## Configuration

### 1. Create Environment File

Create a `.env` file in the **project root** (not in `backend/`):

```bash
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` and add your credentials:

```env
# DoorBird Camera
DOORBIRD_USERNAME=your_api_username
DOORBIRD_PASSWORD=your_api_password
DOORBIRD_IP=192.168.1.xxx

# Supabase (Backend)
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Device Identification (optional)
HOSTNAME=front-door-pi
```

**Important Notes:**
- Use your DoorBird API user (not regular user)
- Use the **service role key** for backend (full access)
- HOSTNAME identifies this device in the database

## Testing

### Run All Tests (Recommended)

```bash
cd backend
uv run pytest
```

This will run all tests in the `tests/` directory with proper Python path configuration.

### Run Individual Tests

Test DoorBird connection:
```bash
cd backend
uv run pytest tests/test_doorbird.py -v
```

Expected output:
```
✅ Successfully connected to RTSP stream!
✅ Successfully captured frame!
   Frame size: 1920x1080
✅ Test frame saved to: test_doorbird_frame.jpg
🎉 DoorBird connection test PASSED!
```

Test Supabase connection:
```bash
cd backend
uv run pytest tests/test_supabase.py -v
```

Expected output:
```
✅ NEXT_PUBLIC_SUPABASE_URL: https://xxxxx.supabase.co
✅ SUPABASE_SERVICE_ROLE_KEY: eyJhbG...
✅ Client initialized successfully
✅ Test detection inserted successfully!
🎉 All Supabase tests PASSED!
```

## Running the Detection System

### Run Person Detection

```bash
cd backend
uv run python -m src.main
```

Expected output:
```
🚀 Starting person detection system...
📹 Connecting to DoorBird at 192.168.1.xxx
🤖 Loading yolov8n.pt model...
✅ Model loaded!
✅ Connected to Supabase (Device: front-door-pi)
✅ Connected to RTSP stream!

👁️  Watching for people...
Press Ctrl+C to stop
```

When a person is detected:
```
👤 Person detected! (#1)
   Saved locally: detection_20241027_143025.jpg
✅ Detection saved to Supabase (ID: abc123...)
   Image URL: https://xxxxx.supabase.co/storage/v1/object/public/...
```

### Run as Background Service (Optional)

For production deployment, create a systemd service:

1. Create service file:
```bash
sudo nano /etc/systemd/system/person-detection.service
```

2. Add configuration:
```ini
[Unit]
Description=Person Detection Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/costume-classifier/backend
ExecStart=/home/pi/.local/bin/uv run python -m src.main
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. Enable and start:
```bash
sudo systemctl enable person-detection
sudo systemctl start person-detection
sudo systemctl status person-detection
```

## Configuration Options

Edit `backend/src/config.py` to customize detection behavior:

```python
# Detection settings
FRAME_SKIP_INTERVAL = 30  # Process every Nth frame
CONFIDENCE_THRESHOLD = 0.5  # Minimum confidence (0.0-1.0)
DUPLICATE_DETECTION_TIMEOUT_SECONDS = 2  # Min time between detections

# YOLO model
YOLO_MODEL = "yolov8n.pt"  # Use yolov8s.pt for better accuracy
```

## Troubleshooting

### "Could not connect to DoorBird RTSP stream"
- Verify DoorBird IP address is correct
- Check API user has "API-Operator" and "Live Video" permissions
- Test network connectivity: `ping <doorbird-ip>`

### "Missing NEXT_PUBLIC_SUPABASE_URL"
- Ensure `.env` file exists in project root
- Check environment variables are set correctly
- Try running with: `uv run --env-file ../.env python ...`

### "Model download fails"
- Ensure internet connectivity
- Model downloads from Ultralytics on first run (~6MB)
- Check disk space: `df -h`

### "Import errors"
- Make sure you're in the `backend/` directory
- Use `uv run python -m backend.src...` format
- Reinstall dependencies: `uv sync --reinstall`

## Next Steps

- Set up the [Dashboard](../../dashboard/SETUP.md) to view detections
- Configure automatic startup with systemd
- Set up log rotation for production use
- Consider adding face blurring for privacy
