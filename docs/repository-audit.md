# Echolingo Repository Audit

## Project Overview
Echolingo is an AI-powered multilingual video dubbing pipeline that transcribes, translates, and re-dubs videos into target languages.

## Current Architecture

### File Structure
```
echolingo/
├── echolingo.py          # Core pipeline implementation
├── app.py                # Streamlit frontend
├── requirements.txt      # Python dependencies
├── requirements-cpu.txt # CPU-only torch variant
├── pyproject.toml       # Project configuration
├── .github/workflows/ci.yml  # CI/CD pipeline
└── README.md            # Documentation
```

### Actual Pipeline Implementation

**INPUT VIDEO**
↓
**VIDEO/AUDIO EXTRACTION** (`extract_audio()`)
- Uses MoviePy `VideoFileClip` to extract audio track
- Converts to 16 kHz mono WAV format
- Output: `extracted.wav`
↓
**SPEECH-TO-TEXT** (`transcribe()`)
- Uses OpenAI Whisper `base` model
- No Voice Activity Detection (VAD) - Whisper handles segmentation internally
- Output: List of segments with `start`, `end`, `text` keys
↓
**LANGUAGE DETECTION**
- NOT IMPLEMENTED - Assumes source language is detected by Whisper's `auto` mode
- No explicit language detection stage
↓
**TRANSLATION** (`translate_segments()`)
- Uses deep-translator (Google Translate API wrapper)
- Translates each segment individually (sequential API calls)
- Normalizes language codes for deep-translator compatibility
- Output: Segments with added `translated_text` key
↓
**TEXT-TO-SPEECH** (`generate_tts_audio()`)
- Uses gTTS (Google Text-to-Speech)
- Generates audio for each translated segment
- Applies smart speed adjustment using pydub's WSOLA algorithm
- Speed capped at 1.35× to maintain intelligibility
- Overlays TTS segments onto silent backbone matching original video duration
- Output: Complete dubbed audio track
↓
**VOICE/AUDIO ALIGNMENT**
- Handled by `fit_audio_smart()` function
- Uses pydub's `speedup()` with WSOLA algorithm
- Pads with silence if audio is shorter than target
- Truncates if still too long after max speedup
↓
**BACKGROUND AUDIO HANDLING**
- NOT IMPLEMENTED - Background audio is NOT preserved
- The entire original audio track is replaced with dubbed speech
- No source separation or background preservation
↓
**MIXING**
- NOT APPLICABLE - No mixing since background is discarded
↓
**VIDEO RECONSTRUCTION** (`compose_video()`)
- Uses MoviePy to replace audio track
- Optional subtitle burning via FFmpeg
- Output: Final dubbed video file
↓
**OUTPUT VIDEO**

### Key Findings

#### Missing Critical Features
1. **Background Audio Preservation**: The pipeline completely replaces the original audio, losing background music, ambient sounds, and intentional audio elements
2. **Noise Reduction**: No audio enhancement or noise reduction
3. **Language Detection**: No explicit language detection stage
4. **Speaker Diarization**: No multi-speaker handling
5. **Voice Cloning**: No preservation of speaker characteristics

#### Performance Characteristics
1. **Sequential Processing**: All operations are sequential
2. **No Batching**: Each segment processed individually
3. **No Caching**: Only Whisper model is cached (via Streamlit)
4. **No Parallelization**: No concurrent processing
5. **API Latency**: Translation and TTS require network calls per segment

#### Language Support
- **Claimed**: 65 languages
- **Actual**: 65 language codes defined in `SUPPORTED_LANGUAGES` dict
- **Validation**: No verification that all 65 work end-to-end
- **Source**: Intersection of gTTS and Google Translate support

#### Dependencies
- **STT**: OpenAI Whisper (base model, ~150MB)
- **Translation**: deep-translator (Google Translate API)
- **TTS**: gTTS (Google Text-to-Speech)
- **Audio Processing**: pydub, MoviePy
- **Video Processing**: MoviePy, FFmpeg
- **Frontend**: Streamlit

#### Engineering Quality
1. **Modular Design**: Good - 6 independent pipeline functions
2. **Error Handling**: Good - Custom `DubbingError` exception
3. **Temp File Management**: Good - Uses `tempfile.mkdtemp()` with cleanup
4. **Logging**: Good - Uses Python logging module
5. **Testing**: NONE - No test suite
6. **Benchmarking**: NONE - No performance measurement
7. **Documentation**: Basic - README exists but lacks technical depth

### Identified Bottlenecks (Hypothesis)
Based on code analysis, likely bottlenecks include:
1. **Whisper transcription**: CPU-intensive, scales with audio duration
2. **Translation API calls**: Network latency per segment
3. **TTS generation**: Network latency per segment
4. **Audio speed adjustment**: pydub processing overhead
5. **Video composition**: MoviePy encoding overhead

### Data Quality Issues
1. **No sample data**: No test videos in repository
2. **No ground truth**: No reference transcriptions or translations
3. **No quality metrics**: No STOI, PESQ, SI-SDR measurements
4. **No background reference**: No way to measure background preservation

### Infrastructure Gaps
1. **No benchmark framework**: No way to measure performance
2. **No test suite**: No automated testing
3. **No CI performance tests**: CI only checks linting and imports
4. **No language validation**: No verification of 65-language support
5. **No audio quality tests**: No objective quality measurements

## Next Steps
1. Create benchmark infrastructure
2. Establish baseline measurements
3. Validate language support
4. Implement background audio preservation
5. Add audio quality metrics
6. Optimize identified bottlenecks
