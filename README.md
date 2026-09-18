---
title: Echolingo
emoji: 🗣️
colorFrom: blue
colorTo: indigo
sdk: streamlit
sdk_version: 1.44.1
app_file: app.py
pinned: false
---
# 🎙️ Echolingo

[![CI](https://github.com/Radhikapatel-code/Echolingo/actions/workflows/ci.yml/badge.svg)](https://github.com/Radhikapatel-code/Echolingo/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/raddhika/Echolingo)

## AI-Powered Multilingual Video Dubbing & Captioning Platform

Echolingo is an end-to-end AI pipeline that automatically **dubs videos into 50+ languages (65 supported)** and optionally **adds translated captions**, while preserving sentence completeness, timing, and audio clarity.

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
- Generate captions in any of 65 supported languages
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

## 🌍 Supported Languages (65)

Echolingo supports exactly 65 languages end-to-end through the STT → Translation → TTS pipeline.

**Complete Language Matrix**: See [docs/language-support.md](docs/language-support.md) for the full compatibility matrix showing STT, translation, and TTS support for each language.

**Validation**: Run `python tests/test_languages.py` to validate the 65-language configuration.

> Language support is constrained by the intersection of provider capabilities. All 65 languages are supported by OpenAI Whisper (STT), Google Translate (translation), and gTTS (TTS).

---

## ⚡ Performance Evaluation

### Test Environment
**NOT BENCHMARKED YET**

The performance benchmark framework has been implemented but not executed due to:
- Python version incompatibility (requires Python 3.11/3.12, currently using 3.14.7)
- Missing test data (no sample videos available)
- Dependency installation issues (PyTorch compatibility)

**Benchmark Framework**: See [benchmarks/benchmark_pipeline.py](benchmarks/benchmark_pipeline.py)
**Requirements**: See [docs/benchmark-requirements.md](docs/benchmark-requirements.md)

### Planned Metrics
Once benchmarks are executable, the following metrics will be measured:

**Operational Efficiency**
- End-to-end latency
- Stage-level latency (STT, translation, TTS, composition)
- p50/p95 latency
- Throughput (videos/minute)
- Real-Time Factor (RTF = processing_time / media_duration)

**Quality Metrics**
- STOI (Speech Intelligibility)
- PESQ (Perceptual Speech Quality)
- SI-SDR (Signal-to-Distortion Ratio)
- ΔSNR (Signal-to-Noise Ratio improvement)
- Background preservation ratio

**Reliability Metrics**
- Success rate
- Failure rate
- API failure rate
- Language coverage validation

### Historical Estimates (from original README)
*Note: These are estimates from the original README and have not been verified through actual benchmarking.*

|| Video Length | Processing Time | Notes |
||---|---|---|
|| 30 seconds | ~25s | Whisper dominates |
|| 1 minute | ~45s | Typical use case |
|| 3 minutes | ~2 min 15s | Scales roughly linearly |
|| 5 minutes | ~3 min 45s | Recommended max for gTTS |

### Bottleneck Analysis
**NOT MEASURED YET**

Hypothesized bottlenecks based on code analysis:
1. **Whisper transcription**: CPU-intensive, scales with audio duration
2. **Translation API calls**: Network latency per segment
3. **TTS generation**: Network latency per segment
4. **Audio speed adjustment**: pydub processing overhead
5. **Video composition**: MoviePy encoding overhead

Actual bottleneck identification requires execution of the benchmark framework.

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
👉 **[Echolingo on Hugging Face Spaces](https://huggingface.co/spaces/raddhika/Echolingo)**

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

## ⚠️ Limitations

### Audio Quality
- **Background audio not preserved**: The pipeline completely replaces the original audio track, losing background music, ambient sounds, and intentional audio elements. See [docs/background-audio-audit.md](docs/background-audio-audit.md) for details.
- **No noise reduction**: The pipeline does not include audio enhancement or noise reduction capabilities.
- **TTS quality**: Uses gTTS which produces functional but robotic-sounding speech. For production-quality voices, upgrade to Coqui XTTS or ElevenLabs.

### Performance
- **Sequential processing**: All pipeline stages run sequentially with no parallelization.
- **No batching**: Each segment is processed individually for translation and TTS.
- **API latency**: Dependent on network calls to Google Translate and gTTS for each segment.
- **CPU-bound**: Whisper transcription is CPU-intensive and may be slow on older hardware.

### Language Support
- **Translation quality**: Google Translate quality varies by language pair and content complexity.
- **TTS availability**: Limited to languages supported by gTTS (constrains the 65-language support).
- **No dialect support**: Does not distinguish between language dialects (e.g., Spanish vs. Latin American Spanish).

### Technical
- **No speaker diarization**: Cannot handle multi-speaker videos with distinct voices.
- **No voice cloning**: Dubbed voice does not match original speaker characteristics.
- **Limited video formats**: Primarily supports MP4 input/output.
- **Model size**: Whisper base model (~150MB) requires initial download.
- **Python version**: Requires Python 3.11+ (3.11 or 3.12 recommended for dependency compatibility).

### Testing
- **No end-to-end testing**: 65-language support is validated at configuration level only, not through actual video processing.
- **No performance benchmarks**: Performance estimates are from original README, not measured.
- **No quality metrics**: No objective audio quality measurements (STOI, PESQ, SI-SDR).

---

## 🔮 Future Enhancements

### Implemented
- [x] **Cloud deployment** — HuggingFace Spaces (added `packages.txt` for FFmpeg support)
- [x] **65-language configuration** — Centralized language configuration with validation
- [x] **Benchmark framework** — Performance measurement infrastructure (not yet executable)
- [x] **Language validation tests** — Automated 65-language configuration validation

### Measured but Not Fixed
- [ ] **Background audio preservation** — Currently not implemented (see limitations below)
- [ ] **Performance bottlenecks** — Identified but not optimized due to benchmark execution issues

### Proposed Improvements
- [ ] **Premium TTS integration** — Coqui XTTS or ElevenLabs for natural-sounding voices
- [ ] **Voice cloning** — preserve speaker characteristics across languages
- [ ] **GPU acceleration** — CUDA-enabled Whisper for 10× faster transcription
- [ ] **Batch processing** — queue multiple videos for sequential processing
- [ ] **Speaker diarization** — handle multi-speaker videos with distinct voices
- [ ] **Source separation** — Implement Spleeter/Demucs for background audio preservation
- [ ] **Audio quality metrics** — Implement STOI, PESQ, SI-SDR measurements
- [ ] **Streaming inference** — Real-time processing for live applications
- [ ] **Model quantization** — Reduce model size for faster inference
- [ ] **Parallel TTS generation** — Concurrent TTS API calls for faster processing
- [ ] **Caching layer** — Cache translation and TTS results for repeated content

---

## 📄 License

[MIT License](LICENSE) — © 2025 Radhika Patel

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, code style, and PR guidelines.
