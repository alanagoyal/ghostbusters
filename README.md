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

### Running the Test Script

Test your DoorBird connection:

```bash
uv run python test_doorbird_connection.py
```

## 📖 Documentation

- [DoorBird Setup Guide](DOORBIRD_SETUP.md) - Camera configuration and RTSP setup
- [Project Specification](PROJECT_SPEC.md) - Complete system architecture
- [Blog Notes](BLOG_NOTES.md) - Implementation journey and decisions

## 🛠️ Development

This project uses [uv](https://docs.astral.sh/uv/) for fast, reliable Python dependency management:

```bash
# Add a new dependency
uv add package-name

# Run a script
uv run python script.py

# Sync dependencies after pulling changes
uv sync
```

## 📝 License

MIT
