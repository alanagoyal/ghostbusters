# Backend - Person Detection System

Python backend for real-time person detection using YOLOv8 on DoorBird RTSP stream.

## Quick Start

```bash
# Install dependencies (including dev dependencies like pytest)
uv sync

# Run all tests with pytest (recommended)
uv run pytest

# Or run individual test files
uv run pytest tests/test_doorbird.py
uv run pytest tests/test_supabase.py

# Run person detection
uv run python -m src.main
```

## Project Structure

```
backend/
├── src/
│   ├── detection/
│   │   └── person_detector.py    # Main detection loop
│   ├── storage/
│   │   └── supabase_client.py    # Database client
│   ├── utils/                     # Utility modules
│   ├── config.py                  # Configuration constants
│   └── main.py                    # Entry point
├── tests/
│   ├── test_doorbird.py          # DoorBird connection test
│   └── test_supabase.py          # Supabase integration test
├── pyproject.toml                 # Dependencies & config
└── README.md                      # This file
```

## Configuration

All configuration is managed through:
1. **Environment variables** - See `../.env.example` in project root
2. **Constants** - See `src/config.py` for detection parameters

### Key Configuration Options

Edit `src/config.py` to customize:

```python
FRAME_SKIP_INTERVAL = 30                    # Process every Nth frame
CONFIDENCE_THRESHOLD = 0.5                  # Minimum detection confidence
DUPLICATE_DETECTION_TIMEOUT_SECONDS = 2     # Min time between detections
YOLO_MODEL = "yolov8n.pt"                  # YOLO model (n=nano, s=small, m=medium)
```

## Dependencies

- **opencv-python** - Video capture from RTSP stream
- **ultralytics** - YOLOv8 person detection
- **supabase** - Database and storage client
- **python-dotenv** - Environment variable management

## Development

### Code Quality

```bash
# Run linter
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

### Testing

```bash
# Test DoorBird connection
uv run python tests/test_doorbird.py

# Test Supabase integration
uv run python tests/test_supabase.py
```

## Documentation

See `../docs/` for complete documentation:
- [Setup Guide](../docs/setup/backend.md) - Detailed installation instructions
- [Architecture](../docs/architecture.md) - System design and data flow
- [Quick Reference](../docs/QUICK_REFERENCE.md) - Overview and troubleshooting

## Deployment

For production deployment on Raspberry Pi, see [Backend Setup Guide](../docs/setup/backend.md#run-as-background-service-optional).
