# Standard Python Practices Applied

**Date:** October 27, 2025
**Status:** ✅ Complete

## Summary

Fixed the project to follow **standard Python best practices** for package structure, testing, and imports.

## The Python Standard: pytest + src layout

The Python community standard is:
1. **pytest** for testing (not running scripts directly)
2. **src/** directory with package code
3. **tests/** directory separate from source
4. **pyproject.toml** with pytest configuration
5. **Imports from package root** via pytest's pythonpath

## What Changed

### 1. Added pytest Configuration ✅

**File:** `backend/pyproject.toml`

```toml
[dependency-groups]
dev = [
    "ruff>=0.14.2",
    "pytest>=8.3.0",  # ← Added pytest
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
pythonpath = ["src"]  # ← Adds src/ to Python path
```

**Benefits:**
- pytest automatically configures Python path
- No need for complex sys.path hacks
- Standard test discovery
- Professional Python project structure

### 2. Fixed Test Imports ✅

**File:** `backend/tests/test_supabase.py`

```python
# OLD (wrong - requires complex path manipulation)
from backend.src.storage.supabase_client import SupabaseClient

# NEW (standard - works with pytest pythonpath)
from storage.supabase_client import SupabaseClient
```

**How it works:**
- pytest reads `pythonpath = ["src"]` from config
- Adds `backend/src/` to Python path automatically
- Tests can import using `from storage.supabase_client import ...`
- Clean, simple, standard

### 3. Updated All Commands ✅

**OLD (non-standard):**
```bash
# Running tests as scripts
uv run python tests/test_doorbird.py
uv run python tests/test_supabase.py

# Running detector with long module path
uv run python -m backend.src.detection.person_detector
```

**NEW (standard):**
```bash
# Running tests with pytest
cd backend
uv run pytest                           # All tests
uv run pytest tests/test_doorbird.py    # Individual test

# Running detector with clean module path
cd backend
uv run python -m src.main
```

### 4. Package Structure Already Correct ✅

```
backend/
├── src/                    ✅ Source code directory
│   ├── detection/         ✅ Organized by module
│   ├── storage/
│   ├── config.py
│   └── main.py
├── tests/                  ✅ Separate from src
│   ├── test_doorbird.py
│   └── test_supabase.py
├── pyproject.toml          ✅ With pytest config
└── README.md
```

This is the **PEP 517/518 standard** Python package layout.

## Why This is Standard

### 1. pytest is the Industry Standard
- Used by 95%+ of Python projects
- More powerful than unittest
- Better test discovery
- Rich plugin ecosystem
- Clearer output

### 2. src/ Layout is Best Practice
- Prevents accidental imports from development directory
- Forces proper packaging
- Cleaner imports in tests
- Standard in modern Python

### 3. pythonpath Configuration
- No more `sys.path.insert(0, ...)`
- No more relative import hacks
- pytest handles it automatically
- Works in CI/CD environments

## How It Works

### When you run `uv run pytest`:

1. **pytest reads pyproject.toml:**
   ```toml
   pythonpath = ["src"]
   ```

2. **pytest adds `backend/src/` to Python path**

3. **Tests can import cleanly:**
   ```python
   from storage.supabase_client import SupabaseClient
   from config import FRAME_SKIP_INTERVAL
   ```

4. **Source code uses relative imports:**
   ```python
   # In person_detector.py
   from ..config import CONFIDENCE_THRESHOLD
   from ..storage.supabase_client import SupabaseClient
   ```

### When you run `uv run python -m src.main`:

1. **Python treats src/ as a package**
2. **Loads src/main.py**
3. **Imports work with relative paths:**
   ```python
   from detection import person_detector
   ```

## Documentation Updated

All documentation now shows standard commands:

### Main README.md
```bash
cd backend
uv run pytest                    # Run tests
uv run python -m src.main        # Run detector
```

### backend/README.md
```bash
uv run pytest                    # All tests
uv run pytest tests/test_*.py    # Individual tests
uv run python -m src.main        # Run detector
```

### docs/setup/backend.md
```bash
# Run All Tests (Recommended)
cd backend
uv run pytest

# Run Individual Tests
uv run pytest tests/test_doorbird.py -v
uv run pytest tests/test_supabase.py -v

# Run Person Detection
cd backend
uv run python -m src.main
```

## Comparison: Before vs After

### Running Tests

| Aspect | Before (Non-standard) | After (Standard) |
|--------|----------------------|------------------|
| **Command** | `python tests/test_file.py` | `pytest tests/test_file.py` |
| **Imports** | `from backend.src.module import ...` | `from module import ...` |
| **Path setup** | Manual `sys.path` manipulation | Automatic via pytest |
| **Discovery** | Must specify each file | `pytest` finds all tests |
| **Output** | Basic print statements | Rich pytest output |
| **CI/CD** | Complex setup | Standard pytest commands |

### Running Code

| Aspect | Before | After |
|--------|--------|-------|
| **Command** | `python -m backend.src.detection.person_detector` | `python -m src.main` |
| **Working dir** | From project root | From backend/ |
| **Clarity** | Long module paths | Clean, short paths |

## Benefits

### For Development
- ✅ Standard commands everyone knows
- ✅ Better test discovery
- ✅ Cleaner imports
- ✅ Professional structure

### For CI/CD
- ✅ Standard pytest commands work
- ✅ No custom path configuration needed
- ✅ Industry best practice
- ✅ Works with coverage tools

### For Contributors
- ✅ Familiar structure
- ✅ No learning custom patterns
- ✅ Standard Python conventions
- ✅ Easy onboarding

## Next Steps

To use the new standard structure:

1. **Install dependencies (including pytest):**
   ```bash
   cd backend
   uv sync
   ```

2. **Run tests:**
   ```bash
   uv run pytest
   ```

3. **Run detector:**
   ```bash
   uv run python -m src.main
   ```

## References

This follows established Python standards:
- **PEP 517/518** - Modern Python packaging
- **pytest documentation** - Standard testing practices
- **Python Packaging User Guide** - src/ layout pattern
- **PyPA recommendations** - Project structure

## Migration Note

If you have any scripts or documentation still using old paths, update them to:
- Use `pytest` instead of `python test_*.py`
- Use `python -m src.main` instead of `python -m backend.src...`
- Import from module root: `from storage.supabase_client` not `from backend.src.storage...`

---

**All changes follow Python community standards!** 🐍✨
