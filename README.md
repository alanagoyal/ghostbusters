# Doorstep Costume Classifier

Raspberry Pi edge computer vision system that watches a DoorBird doorbell camera on Halloween night, detects trick-or-treaters, classifies their costumes using AI, and displays live results on a public dashboard.

## 🎃 Tech Stack

- **Edge Compute:** Raspberry Pi 5 (8GB RAM)
- **Camera:** DoorBird doorbell (RTSP stream)
- **Person Detection:** YOLOv8n
- **Costume Classification:** Baseten API (vision-language model)
- **Database & Storage:** Supabase (with Realtime via WebSocket)
- **Frontend:** Next.js 16 + React 19 + TypeScript + Tailwind CSS v4
- **Hosting:** Vercel (dashboard)
- **Package Manager:** uv (by Astral) for Python, npm for JavaScript

## 📁 Project Structure

```
costume-classifier/
├── backend/                    # Python ML backend
│   ├── src/
│   │   └── clients/           # External service clients
│   │       ├── baseten_client.py    # Baseten API client
│   │       └── supabase_client.py   # Supabase client
│   ├── scripts/               # Entry point scripts
│   │   └── main.py            # Live detection script
│   └── tests/                 # Backend tests
│       ├── fixtures/          # Test images and data
│       └── integration/       # Integration tests
├── frontend/                   # Next.js dashboard
│   ├── app/                   # Next.js app directory
│   ├── components/            # React components
│   └── lib/                   # Frontend utilities
├── docs/                       # Documentation
│   ├── BASETEN_SETUP.md      # Vision model API setup
│   ├── DOORBIRD_SETUP.md     # Camera configuration
│   ├── SUPABASE_SETUP.md     # Database setup
│   ├── PROJECT_SPEC.md       # System architecture
│   └── BLOG_NOTES.md         # Implementation notes
└── Configuration files         # Root configs (pyproject.toml, etc.)
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- DoorBird camera on local network

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/alanagoyal/costume-classifier.git
   cd costume-classifier
   ```

2. **Install uv (if not already installed):**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Install dependencies:**
   ```bash
   uv sync
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

### Testing

**Test Baseten API connection:**
```bash
uv run backend/tests/integration/test_baseten_connection.py
```

**Test with single-person costume images:**
```bash
uv run backend/tests/integration/test_costume_detection.py
```
This processes the test images in `backend/tests/fixtures/`, classifies costumes with Baseten, and uploads to Supabase.

**Test multi-person detection:**
```bash
uv run backend/tests/integration/test_multiple_people.py
```
This uses YOLOv8n to detect ALL people in each frame (including test-6.png and test-7.png with 3 kids each), processes each person separately, and creates individual database entries. Perfect for testing group scenarios like multiple trick-or-treaters arriving together.

**Test DoorBird camera connection:**
```bash
uv run backend/tests/integration/test_doorbird_connection.py
```

**Test Supabase integration:**
```bash
uv run backend/tests/integration/test_supabase_connection.py
```

**Run live person detection (see Production Deployment below for long-running setup):**
```bash
uv run backend/scripts/main.py
```
Watches the RTSP stream, detects all people in each frame, classifies their costumes, and uploads to Supabase. Handles multiple people in the same frame automatically.

## 🥧 Raspberry Pi Management

### Connecting to Your Pi

**SSH into the Pi:**
```bash
ssh pi@halloween-pi.local
```

**When you're done working:**
```bash
# Simply exit the SSH session
exit
# OR press Ctrl+D
```

### Power Management

**When to shut down:**
- Not using the Pi for several hours/days
- Moving the Pi to a different location
- Before unplugging power

**How to safely shut down:**
```bash
# Shut down (safe to unplug after LED stops blinking)
sudo shutdown -h now

# OR
sudo poweroff
```

**How to reboot:**
```bash
sudo reboot
```

**Leaving the Pi running:**
- ✅ Safe to leave running 24/7 (designed for it)
- ✅ Uses ~3-5W of power when idle
- ✅ SSH sessions can be closed without affecting the Pi
- ✅ Good practice if you'll use it again within a few hours

**Best practice:**
- Exit SSH when done (keeps connection clean)
- Leave Pi powered on if using it regularly
- Only shut down if not using for extended periods or moving hardware

### Monitoring Pi Health

**Check temperature:**
```bash
vcgencmd measure_temp
# Normal: 40-60°C idle, up to 70°C under load
# Warning: 80°C+ (check cooling)
```

**Check disk space:**
```bash
df -h
```

**Update system packages:**
```bash
sudo apt update && sudo apt upgrade -y
```

## 🎃 Production Deployment (Halloween Night)

For long-running detection (6+ hours), the system includes production-ready features:

### Production Features

- **Auto-reconnection:** RTSP stream reconnects automatically on failure
- **Periodic reconnection:** Full reconnect every hour to prevent memory leaks
- **Disk management:** Local images auto-deleted after Supabase upload
- **Health monitoring:** Stats printed every 5 minutes (uptime, detections, failures)
- **Systemd service:** Auto-restart on crash, survives SSH disconnection

### Option 1: Run Manually (Testing/Development)

```bash
ssh pi@halloween-pi
cd ~/projects/costume-classifier
uv run backend/scripts/main.py
```

This will show live output with:
- Detection notifications
- Health checks every 5 minutes
- Reconnection status
- Costume classifications

Press `Ctrl+C` to stop.

### Option 2: Run as Service (Production/Halloween Night)

**Setup (one-time):**
```bash
ssh pi@halloween-pi
cd ~/projects/costume-classifier
sudo ./setup-service.sh
```

**Start the service:**
```bash
sudo systemctl start costume-detector
```

**Monitor live activity:**
```bash
# Watch main log (detections, health checks)
tail -f ~/costume-detector.log

# Watch error log
tail -f ~/costume-detector-error.log
```

**Control the service:**
```bash
# Stop the service
sudo systemctl stop costume-detector

# Restart the service
sudo systemctl restart costume-detector

# Check status
sudo systemctl status costume-detector

# Disable auto-start on boot
sudo systemctl disable costume-detector
```

### Service Benefits

✅ Runs in background (SSH can disconnect)
✅ Auto-restarts if it crashes
✅ Starts automatically on Pi reboot
✅ Logs saved to files for review

### Monitoring During Halloween

**Check if running:**
```bash
sudo systemctl status costume-detector
```

**See recent activity:**
```bash
tail -20 ~/costume-detector.log
```

**Monitor live:**
```bash
tail -f ~/costume-detector.log
```

**Health check output (every 5 minutes):**
```
📊 Health Check (Uptime: 125.3 min)
   Frames processed: 225450
   Detections: 47
   Failed frames: 3
```

**See all detections today:**
```bash
grep "person(s) detected" ~/costume-detector.log
```

### Troubleshooting

**Service fails to start (exit code 127):**
```bash
sudo systemctl status costume-detector
# Shows: "Main process exited, code=exited, status=127"
```

**Problem:** systemd can't find `uv` command

**Solution:** The service file needs the full path to uv:
1. Find where uv is installed: `which uv` or `ls ~/.local/bin/uv`
2. Service file should use: `ExecStart=/home/pi/.local/bin/uv run backend/scripts/main.py`
3. And set PATH: `Environment="PATH=/home/pi/.local/bin:/usr/local/sbin:..."`

**No output in logs:**

**Problem:** Python buffers output when not running in a terminal

**Solution:** Service file needs: `Environment="PYTHONUNBUFFERED=1"`

**Service running but failing:**
```bash
# Check error log
cat ~/costume-detector-error.log

# Check system journal
sudo journalctl -u costume-detector -n 50
```

**Stop endless restart loop:**
```bash
# If service is crashing and restarting constantly
sudo systemctl stop costume-detector
sudo systemctl disable costume-detector  # Prevents auto-start on boot
```

## 📖 Documentation

- [Baseten Setup Guide](docs/BASETEN_SETUP.md) - Vision model API configuration for costume classification
- [DoorBird Setup Guide](docs/DOORBIRD_SETUP.md) - Camera configuration and RTSP setup
- [Supabase Setup Guide](docs/SUPABASE_SETUP.md) - Database and storage configuration
- [Project Specification](docs/PROJECT_SPEC.md) - Complete system architecture
- [Blog Notes](docs/BLOG_NOTES.md) - Implementation journey and decisions

## 📊 Dashboard

The project includes a real-time Next.js dashboard for monitoring detections live.

### Dashboard Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env.local
   # Add your Supabase credentials
   ```

4. **Run development server:**
   ```bash
   npm run dev
   ```

5. **Open dashboard:**
   Visit [http://localhost:3000](http://localhost:3000)

### How Realtime Works

The dashboard uses Supabase Realtime to show new detections instantly:

1. **Enable Realtime** for the `person_detections` table (run in Supabase SQL Editor):
   ```sql
   alter publication supabase_realtime add table person_detections;
   ```

2. The dashboard subscribes to changes via WebSocket
3. New detections appear immediately without page refresh
4. Sub-second latency from detection to display

See [frontend/SETUP.md](frontend/SETUP.md) for detailed instructions.

## 🛠️ Development

This project uses modern Python tooling from [Astral](https://astral.sh/):
- **uv** - Fast, reliable package management
- **ruff** - Lightning-fast linting and formatting

### Package Management

```bash
# Install dependencies
uv sync

# Add a new dependency
uv add package-name

# Add a dev dependency
uv add --dev package-name

# Run a script
uv run python script.py
```

### Code Quality

```bash
# Check code with linter
uv run ruff check .

# Auto-fix linting issues
uv run ruff check . --fix

# Format code
uv run ruff format .

# Run both linting and formatting
uv run ruff check . --fix && uv run ruff format .
```

## 📝 License

MIT
