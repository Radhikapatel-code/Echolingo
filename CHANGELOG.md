# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Production CI Pipeline**: Added a GitHub Actions workflow (`ci.yml`) to automatically lint and check formatting using Ruff.
- **Dependency Tracking**: Added `packages.txt` for FFmpeg installation support on HuggingFace Spaces.
- **Documentation**: Added `CHANGELOG.md`, `CONTRIBUTING.md`, and `.env.example`.
- **Python 3.13 Support**: Added `audioop-lts` to `requirements.txt` to support `pydub` on Python 3.13+, and pinned `openai-whisper` to a stable commit from `main` that fixes PEP 517 build errors.
- **File Management**: `app.py` now aggressively cleans up the temporary upload directory after serving the generated video.

### Changed
- **Pipeline Architecture**: Refactored the monolithic script into isolated, testable pipeline stages (`extract_audio`, `transcribe`, `translate_segments`, `generate_tts_audio`, `compose_video`).
- **Temporary Files**: Eliminated hardcoded file names in the working directory. All intermediate files are now written to isolated directories created via `tempfile.mkdtemp()`.
- **Whisper Initialization**: Cached the Whisper model in Streamlit using `@st.cache_resource` so it only loads once per session rather than on every button click.
- **Audio Processing**: Defined hardcoded limits (e.g., `MAX_SPEED_FACTOR=1.35`) as named constants.
- **Requirements**: Pinned `torch` to `2.9.1+cpu` to ensure compatibility and stability across environments.

### Fixed
- **FFmpeg Subtitle Escaping**: Fixed a bug on Windows where FFmpeg misinterpreted absolute file paths with colons (`C:\...`) as filtergraph arguments.
- **Git Hygiene**: Removed all tracked binaries (`.mp4`, `.wav`, `.exe`) and coverage files from the git repository.
