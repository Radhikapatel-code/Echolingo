# Contributing to Echolingo

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.11+
- FFmpeg installed and available on PATH
- Git

### Local Installation

```bash
# Clone the repository
git clone https://github.com/Radhikapatel-code/Echolingo.git
cd Echolingo

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Install CPU-only torch (lightweight ~200MB)
pip install -r requirements-cpu.txt

# Install project dependencies
pip install -r requirements.txt

# Install development tools
pip install ruff
```

### Running Locally

```bash
streamlit run app.py
```

## Code Style

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting.

```bash
# Check for lint errors
ruff check .

# Auto-fix lint errors
ruff check --fix .

# Check formatting
ruff format --check .

# Apply formatting
ruff format .
```

All code must pass `ruff check` and `ruff format --check` before merging.

### Conventions

- **Type hints** on all function signatures
- **Docstrings** on all public functions (Google style)
- **Named constants** instead of magic numbers
- **Logging** via `logging.getLogger(__name__)` — not `print()`

## Pull Request Process

1. Fork the repository and create a feature branch from `main`
2. Make your changes with clear, descriptive commits
3. Ensure `ruff check .` and `ruff format --check .` pass
4. Verify the Streamlit app runs locally with `streamlit run app.py`
5. Update the README if your change affects user-facing behavior
6. Open a PR with a clear description of what and why

## Reporting Issues

- Use GitHub Issues for bug reports and feature requests
- Include reproduction steps, expected behavior, and actual behavior
- For video processing bugs, include the FFmpeg version (`ffmpeg -version`)

## Architecture

The codebase is organized as a pipeline:

```
echolingo.py  — Core dubbing pipeline (extract → transcribe → translate → TTS → compose)
app.py        — Streamlit frontend (file upload, settings, display)
```

Each pipeline stage is a separate function with clear inputs/outputs.
See the docstrings in `echolingo.py` for the full API.
