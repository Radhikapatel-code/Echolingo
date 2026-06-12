# 🎙️ Echolingo

[![CI](https://github.com/Radhikapatel-code/Echolingo/actions/workflows/ci.yml/badge.svg)](https://github.com/Radhikapatel-code/Echolingo/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/Radhikapatel-code/Echolingo)

## AI-Powered Multilingual Video Dubbing & Captioning Platform

Echolingo is an end-to-end AI pipeline that automatically **dubs videos into 36 languages** and optionally **adds translated captions**, while preserving sentence completeness, timing, and audio clarity.

Unlike simple AI demos, Echolingo tackles **real-world engineering challenges** in audio-video processing — synchronization, timing mismatches from translation expansion, and robust temp file management for concurrent usage.

> **⚠️ TTS Quality Note:** The current version uses **gTTS** (Google Text-to-Speech) for zero-cost, zero-API-key deployment. gTTS produces functional but robotic-sounding speech. For production-quality natural voices, upgrade to [Coqui XTTS](https://github.com/coqui-ai/TTS) or [ElevenLabs](https://elevenlabs.io/) — see [Future Enhancements](#-future-enhancements) below.

---

## 🚀 Problem Statement

When dubbing videos into other languages:

- Translated speech is often **longer** than the original (e.g., English → German)
- Naive approaches **cut sentences**, **overlap audio**, or **distort pitch**
- Subtitle rendering frequently breaks due to font and platform issues
- Audio/video pipelines fail silently due to temp file collisions and missing cleanup

**Echolingo solves these with a production-grade, modular pipeline.**

---

## ✨ Key Features

### 🎧 AI Video Dubbing
- Automatic speech transcription via **OpenAI Whisper** (base model)
- Sentence-level translation via **Google Translate** (deep-translator)
- AI-generated speech via **gTTS** (Text-to-Speech)

### ⏱️ Smart Audio Synchronization
- Dynamically adjusts speech speed within human-safe limits (capped at 1.35×)
- Ensures **complete sentences fit original time slots** — no truncation
- Prevents audio overlap and pitch distortion using WSOLA-based speedup

### 📝 Optional Multi-Language Captions
- Generate captions in any of 36 supported languages
- Subtitles are **burned directly into the video** via FFmpeg
- Works on all video players (no external subtitle files needed)

### 🛡️ Production-Grade Engineering
- **Modular pipeline** — 6 independent, testable functions
- **Temp file isolation** — each run uses a unique `tempfile.mkdtemp()` directory
- **Automatic cleanup** — `finally` blocks ensure no orphaned files, even on crash
- **File size validation** — rejects uploads over 50 MB before processing
- **Whisper model caching** — `@st.cache_resource` avoids reloading per click
- **Custom error handling** — `DubbingError` with clear stage-specific messages

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        dub_video()                           │
│  Orchestrates the full pipeline with cleanup guarantees      │
├──────────┬───────────┬───────────┬────────────┬─────────────┤
│ extract  │transcribe │ translate │ generate   │  compose    │
│ _audio() │   ()      │_segments()│ _tts_audio │  _video()   │
│          │           │           │    ()      │             │
│ VideoFile│  Whisper   │  Google   │   gTTS +   │  MoviePy +  │
│  Clip    │   base    │ Translate │ fit_audio  │   FFmpeg    │
│ → WAV    │  → segs   │  → text   │  → audio   │  → MP4     │
└──────────┴───────────┴───────────┴────────────┴─────────────┘
              All temp files in tempfile.mkdtemp()
              Cleaned up in finally: shutil.rmtree()
```

---

## 🌍 Supported Languages (36)

| | | | |
|---|---|---|---|
| Afrikaans (af) | Arabic (ar) | Bengali (bn) | Bosnian (bs) |
| Catalan (ca) | Chinese Simplified (zh-cn) | Chinese Traditional (zh-tw) | Croatian (hr) |
| Czech (cs) | Danish (da) | Dutch (nl) | English (en) |
| Finnish (fi) | French (fr) | German (de) | Greek (el) |
| Hindi (hi) | Hungarian (hu) | Indonesian (id) | Italian (it) |
| Japanese (ja) | Korean (ko) | Malay (ms) | Norwegian (no) |
| Polish (pl) | Portuguese (pt) | Romanian (ro) | Russian (ru) |
| Spanish (es) | Swedish (sv) | Tamil (ta) | Telugu (te) |
| Thai (th) | Turkish (tr) | Ukrainian (uk) | Vietnamese (vi) |

> Language support is constrained to the **gTTS** subset (the narrower API). All languages are also supported by deep-translator for subtitle generation.

---

## ⚡ Performance Benchmarks

Measured on a standard CPU machine (no GPU), using Whisper `base` model:

| Video Length | Processing Time | Notes |
|---|---|---|
| 30 seconds | ~25s | Whisper dominates |
| 1 minute | ~45s | Typical use case |
| 3 minutes | ~2 min 15s | Scales roughly linearly |
| 5 minutes | ~3 min 45s | Recommended max for gTTS |

> **Note:** First run downloads the Whisper `base` model (~150 MB). Subsequent runs use the cached model. Processing time depends on speech density, target language, and network speed (for gTTS and translation API calls).

---

## 🛠️ Tech Stack

| Category | Tool | Purpose |
|---|---|---|
| Speech Recognition | OpenAI Whisper | Audio → text transcription |
| Translation | deep-translator | Google Translate wrapper |
| Text-to-Speech | gTTS | Text → speech synthesis |
| Audio Processing | Pydub | Speed adjustment, mixing |
| Video Processing | MoviePy + FFmpeg | Audio muxing, subtitle burn |
| Frontend | Streamlit | Interactive web UI |
| CI | GitHub Actions + Ruff | Lint, format, import checks |
| Language | Python 3.11 | Core runtime |

## 🌐 Live Demo

Try the live version of Echolingo deployed on Hugging Face Spaces:  
👉 **[Echolingo on Hugging Face Spaces](https://huggingface.co/spaces/Radhikapatel-code/Echolingo)**

*(Note: The live demo runs on CPU, so processing times will be slower than a local GPU setup.)*

---

## 🧩 High-Level Architecture

```
Input Video
↓
FFmpeg → Audio Extraction
↓
Whisper → Transcription
↓
Translation
↓
Text-to-Speech
↓
Smart Speed Adjustment
↓
Audio Overlay
↓
Optional Subtitle Generation (SRT)
↓
FFmpeg Subtitle Burn-in
↓
Final Dubbed Video
```

---

## 📺 Preview

**Original Video**  
https://github.com/user-attachments/assets/0921af69-d25e-4523-8e70-78e2f7a4228e

**Interface**  
<img width="1912" height="943" alt="image" src="https://github.com/user-attachments/assets/08227d52-ee42-4aeb-a5d7-cca39931e306" />
<img width="1919" height="606" alt="image" src="https://github.com/user-attachments/assets/155aadd5-b0d5-4ebb-b2af-81956b36feaf" />
<img width="1898" height="877" alt="image" src="https://github.com/user-attachments/assets/bdc0c09d-953e-4826-a6cf-350cc900be82" />

**Dubbed Video**  
https://github.com/user-attachments/assets/71aac386-b4c2-4883-b54f-a329afd79c22

---

## 📦 Quick Start

### Prerequisites

- **Python 3.11+**
- **FFmpeg** installed and on PATH ([download](https://ffmpeg.org/download.html))

### Installation

```bash
# Clone the repository
git clone https://github.com/Radhikapatel-code/Echolingo.git
cd Echolingo

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Install CPU-only torch (~200MB instead of ~2GB CUDA)
pip install -r requirements-cpu.txt

# Install project dependencies
pip install -r requirements.txt
```

> **GPU users:** Skip `requirements-cpu.txt` and install your CUDA-compatible torch version manually before `requirements.txt`.

### Run

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

### Docker

```bash
docker build -t echolingo .
docker run -p 8501:8501 echolingo
```

---

## 🧠 Engineering Design Decisions

- **Modular pipeline functions** instead of one monolithic function — each stage is independently testable and debuggable
- **`tempfile.mkdtemp()` per session** — two simultaneous users can't corrupt each other's intermediate files
- **`finally: shutil.rmtree()`** — temp files are always cleaned up, even if the pipeline crashes midway
- **`@st.cache_resource`** for Whisper — the model loads once and persists across Streamlit reruns
- **Named constants** (`MAX_SPEED_FACTOR`, `SPEEDUP_CHUNK_SIZE`, etc.) — no magic numbers floating in the code
- **`DubbingError`** custom exception — clean error messages with stage identification instead of raw tracebacks
- **No media files in repository** — all video/audio artifacts are gitignored; the repo stays lightweight

---

## 🔮 Future Enhancements

- [ ] **Premium TTS integration** — Coqui XTTS or ElevenLabs for natural-sounding voices
- [ ] **Voice cloning** — preserve speaker characteristics across languages
- [ ] **GPU acceleration** — CUDA-enabled Whisper for 10× faster transcription
- [ ] **Batch processing** — queue multiple videos for sequential processing
- [x] **Cloud deployment** — HuggingFace Spaces (added `packages.txt` for FFmpeg support)
- [ ] **Speaker diarization** — handle multi-speaker videos with distinct voices

---

## 📄 License

[MIT License](LICENSE) — © 2025 Radhika Patel

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, code style, and PR guidelines.
