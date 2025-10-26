# Doorstep Costume Classifier

Raspberry Pi edge computer vision system that watches a DoorBird doorbell camera on Halloween night, detects trick-or-treaters, classifies their costumes using AI, and displays live results on a public dashboard.

## 🎃 Tech Stack

- **Edge Compute:** Raspberry Pi 5 (8GB RAM)
- **Camera:** DoorBird doorbell (RTSP stream)
- **Person Detection:** YOLOv8n
- **Costume Classification:** Baseten API (vision-language model)
- **Database:** Supabase (with Realtime)
- **Frontend:** Next.js on Vercel
- **Package Manager:** uv (by Astral)

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

### Running the Scripts

**Test your DoorBird connection:**
```bash
uv run python test_doorbird_connection.py
```

**Test person detection:**
```bash
uv run python detect_people.py
```

**Test Baseten model (after deployment):**
```bash
uv run python test_baseten_model.py
```

**Run costume classifier:**
```bash
uv run python classify_costumes.py
```

## 🎭 Costume Classification Setup

### 1. Deploy Qwen-VL to Baseten

See [BASETEN_DEPLOYMENT.md](BASETEN_DEPLOYMENT.md) for detailed instructions.

Quick version:
```bash
# Install Truss
uv pip install --upgrade truss

# Clone examples
cd ~/Developer
git clone https://github.com/basetenlabs/truss-examples.git
cd truss-examples/qwen/qwen-vl

# Deploy
truss push
```

### 2. Configure Baseten URL

After deployment, update your `.env`:
```bash
BASETEN_MODEL_URL=https://model-<YOUR_ID>.api.baseten.co/development/predict
```

### 3. Test and Run

```bash
# Test the model
uv run python test_baseten_model.py

# Start classifying costumes
uv run python classify_costumes.py
```

## 🎨 Prompt Templates

The system includes multiple prompt templates for different use cases:

- **standard** - Basic costume classification (default)
- **detailed** - Detailed costume analysis
- **fun** - Fun, encouraging descriptions
- **multi** - Multi-person detection
- **category** - Costume category classification
- **safety** - Safety analysis
- **group** - Group costume analysis
- **quality** - Quality assessment

See [`costume_prompts.py`](costume_prompts.py) for all available prompts.

**Example:**
```python
from baseten_client import BasetenClient
from costume_prompts import get_prompt

client = BasetenClient()
prompt = get_prompt("fun")  # Use fun, encouraging prompt
result = client.classify_costume("costume.jpg", prompt=prompt)
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

- [DoorBird Setup Guide](DOORBIRD_SETUP.md) - Camera configuration and RTSP setup
- [Project Specification](PROJECT_SPEC.md) - Complete system architecture
- [Blog Notes](BLOG_NOTES.md) - Implementation journey and decisions

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
