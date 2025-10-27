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

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- DoorBird camera on local network
- Supabase account

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

3. **Install backend dependencies:**
   ```bash
   cd backend
   uv sync
   ```

4. **Set up environment variables:**
   ```bash
   # From project root
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

### Testing

Test your DoorBird connection:

```bash
cd backend
uv run python tests/test_doorbird.py
```

Test your Supabase integration:

```bash
uv run python tests/test_supabase.py
```

Run person detection:

```bash
uv run python -m backend.src.detection.person_detector
```

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

## 📖 Documentation

- **[Documentation Index](docs/README.md)** - Complete documentation guide
- **Setup Guides:**
  - [DoorBird Setup](docs/setup/doorbird.md) - Camera configuration and RTSP setup
  - [Supabase Setup](docs/setup/supabase.md) - Database and storage configuration
  - [Backend Setup](docs/setup/backend.md) - Python backend installation
  - [Dashboard Setup](dashboard/SETUP.md) - Next.js frontend deployment
- **Architecture:**
  - [System Architecture](docs/architecture.md) - Complete system specification
  - [Quick Reference](docs/QUICK_REFERENCE.md) - File organization and tech stack
  - [Codebase Analysis](docs/CODEBASE_ANALYSIS.md) - Detailed technical analysis
- **Development:**
  - [Implementation Notes](docs/blog/implementation-notes.md) - Development journey and decisions

## 📊 Dashboard

The project includes a real-time Next.js dashboard for monitoring detections live.

### Dashboard Setup

1. **Navigate to dashboard directory:**
   ```bash
   cd dashboard
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

See [dashboard/SETUP.md](dashboard/SETUP.md) for detailed instructions.

## 📁 Project Structure

```
costume-classifier/
├── backend/                    # Python person detection system
│   ├── src/
│   │   ├── detection/         # Person detection logic
│   │   ├── storage/           # Supabase client
│   │   ├── utils/             # Utilities
│   │   ├── config.py          # Configuration constants
│   │   └── main.py            # Entry point
│   ├── tests/                 # Test scripts
│   ├── pyproject.toml         # Python dependencies
│   └── README.md
│
├── dashboard/                  # Next.js real-time dashboard
│   ├── app/                   # Next.js app router
│   ├── lib/                   # Supabase client
│   └── README.md
│
├── docs/                       # Documentation
│   ├── setup/                 # Setup guides
│   ├── blog/                  # Development notes
│   ├── architecture.md        # System design
│   └── README.md              # Documentation index
│
├── .env.example               # Environment template
├── supabase_migration.sql     # Database schema
└── README.md                  # This file
```

## 🛠️ Development

This project uses modern Python tooling from [Astral](https://astral.sh/):
- **uv** - Fast, reliable package management
- **ruff** - Lightning-fast linting and formatting

### Package Management

```bash
# Install dependencies
cd backend
uv sync

# Add a new dependency
uv add package-name

# Add a dev dependency
uv add --dev package-name

# Run detection system
uv run python -m backend.src.detection.person_detector
```

### Code Quality

```bash
cd backend

# Check code with linter
uv run ruff check .

# Auto-fix linting issues
uv run ruff check . --fix

# Format code
uv run ruff format .
```

## 📝 License

MIT
