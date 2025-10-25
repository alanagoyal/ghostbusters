# Astral Python Tools Integration

This project uses Astral's high-performance Python tooling for development.

## Tools Included

### uv - Package Management
[uv](https://github.com/astral-sh/uv) is an extremely fast Python package installer and resolver, written in Rust. It's 10-100x faster than pip.

### ruff - Linting and Formatting
[ruff](https://github.com/astral-sh/ruff) is an extremely fast Python linter and code formatter, written in Rust. It replaces multiple tools (flake8, black, isort, etc.) with a single, blazing-fast tool.

## Installation

### Install uv

```bash
# macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

## Usage

### Package Management with uv

```bash
# Create a new virtual environment and install dependencies
uv sync

# Install dependencies including dev tools
uv sync --all-extras

# Add a new dependency
uv add package-name

# Add a dev dependency
uv add --dev package-name

# Run a command in the virtual environment
uv run python script.py

# Install a specific Python version
uv python install 3.10
```

### Linting and Formatting with ruff

```bash
# Install ruff (already included in dev dependencies)
uv sync --all-extras

# Run linter
uv run ruff check .

# Run linter and auto-fix issues
uv run ruff check --fix .

# Run formatter
uv run ruff format .

# Check formatting without making changes
uv run ruff format --check .

# Run both linter and formatter
uv run ruff check --fix . && uv run ruff format .
```

## Migration from Traditional Tools

### From requirements.txt to pyproject.toml
We've migrated from `requirements.txt` to `pyproject.toml`. The old `requirements.txt` can be kept for reference, but uv will use `pyproject.toml`.

### From venv to uv
Instead of:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Now use:
```bash
uv sync
uv run python script.py
```

## CI/CD Integration

This project uses GitHub Actions with Astral tools. See `.github/workflows/ci.yml` for the configuration.

The CI pipeline:
1. Uses `astral-sh/setup-uv` action for fast dependency installation
2. Runs `ruff check` for linting
3. Runs `ruff format --check` for formatting validation

## Configuration

### ruff Configuration
Ruff is configured in `pyproject.toml` under `[tool.ruff]`. Current settings:
- Line length: 100 characters
- Target Python version: 3.10+
- Enabled rules: extensive set including pycodestyle, Pyflakes, isort, and many more
- Code style: Google docstring convention

### Python Version
Python version is specified in `.python-version` file (3.10) for consistency across environments.

## Benefits

1. **Speed**: uv is 10-100x faster than pip; ruff is 10-100x faster than traditional linters
2. **Single Tool**: ruff replaces flake8, black, isort, pyupgrade, and more
3. **Rust-Powered**: Both tools are written in Rust for maximum performance
4. **Modern Standards**: Automatic enforcement of modern Python best practices
5. **Easy CI/CD**: Simple integration with GitHub Actions

## Resources

- [uv Documentation](https://docs.astral.sh/uv/)
- [ruff Documentation](https://docs.astral.sh/ruff/)
- [Astral Blog](https://astral.sh/blog)
