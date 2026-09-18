# Background Audio Preservation Audit

## Current Implementation Status

**BACKGROUND AUDIO PRESERVATION: NOT IMPLEMENTED**

## Current Behavior

The Echolingo pipeline currently **discards all background audio** during the dubbing process:

1. **Audio Extraction**: `extract_audio()` extracts the complete audio track from the video
2. **Speech Processing**: The entire audio is processed by Whisper for transcription
3. **Audio Replacement**: `compose_video()` completely replaces the original audio with the dubbed TTS audio
4. **No Background Preservation**: There is no mechanism to:
   - Separate speech from background audio
   - Preserve background music, ambient sounds, or intentional audio elements
   - Mix background audio back into the final output

## Code Evidence

### In `echolingo.py` - `compose_video()` function (lines 380-452):

```python
def compose_video(
    video_path: str,
    audio_segment: AudioSegment,
    output_path: str,
    work_dir: str,
    srt_path: str | None = None,
) -> str:
    """Combine original video with new dubbed audio and optional subtitles.

    Exports the dubbed audio as WAV, muxes it with the original video
    via MoviePy, and optionally burns subtitles using FFmpeg.
    """
    # ... code ...
    video = VideoFileClip(video_path)
    dubbed_audio = AudioFileClip(final_audio_path)
    video = video.with_audio(dubbed_audio)  # COMPLETE REPLACEMENT
    # ... code ...
```

The line `video = video.with_audio(dubbed_audio)` completely replaces the original audio track with the dubbed audio. There is no mixing or preservation of the original background audio.

### In `echolingo.py` - `generate_tts_audio()` function (lines 281-335):

```python
def generate_tts_audio(
    segments: list[dict],
    target_lang: str,
    duration_ms: int,
    work_dir: str,
) -> AudioSegment:
    """Generate a full dubbed audio track from translated segments.

    Synthesizes TTS for each segment via gTTS, fits it to the original
    timing window using smart speed adjustment, and assembles a complete
    audio track matching the original video duration.
    """
    backbone = AudioSegment.silent(duration=duration_ms)  # SILENT BACKBONE
    # ... code overlays TTS onto silence ...
```

The function creates a silent backbone and overlays TTS segments onto it. There is no attempt to preserve or mix with the original background audio.

## Impact

### What is Lost
- Background music
- Ambient environmental sounds
- Sound effects
- Intentional audio elements that are part of the original video experience
- Music in music videos
- Background conversations in multi-speaker scenarios
- Any non-speech audio content

### What is Preserved
- Nothing from the original audio track is preserved
- The output contains ONLY the dubbed speech

## Comparison with Expected Behavior

### Expected Behavior (per requirements):
```
ORIGINAL AUDIO
↓
SOURCE / SPEECH SEPARATION
↓
SPEECH COMPONENT ─────→ STT → Translation → TTS
↓
BACKGROUND COMPONENT
↓
ALIGNMENT / MIXING
↓
FINAL AUDIO
```

### Actual Behavior:
```
ORIGINAL AUDIO
↓
COMPLETE EXTRACTION
↓
STT → Translation → TTS
↓
COMPLETE AUDIO REPLACEMENT
↓
FINAL AUDIO (speech only)
```

## Technical Limitations

1. **No Source Separation**: The pipeline does not use any source separation technique (e.g., Spleeter, Demucs)
2. **No Audio Mixing**: No mixing logic to combine dubbed speech with background audio
3. **No Background Detection**: No mechanism to identify or preserve background audio
4. **No Audio Alignment**: No timing alignment between dubbed speech and background audio

## Recommendations

### Option 1: Source Separation (Recommended)
Implement audio source separation to isolate speech from background:
- Use Spleeter (Deezer's source separation library)
- Use Demucs (Facebook's source separation model)
- Separate audio into: vocals, drums, bass, other
- Process vocals for dubbing, preserve other components

### Option 2: Voice Activity Detection (VAD)
Use VAD to identify speech segments and preserve non-speech segments:
- Use WebRTC VAD or similar
- Detect speech vs non-speech regions
- Replace speech regions with dubbed audio
- Preserve non-speech regions

### Option 3: Audio Mixing
Implement audio mixing to combine dubbed speech with original background:
- Extract background audio from original
- Apply audio ducking to background during speech
- Mix dubbed speech with ducked background
- Ensure proper timing alignment

### Option 4: User-Configurable Background
Allow users to specify background audio handling:
- Option to preserve background
- Option to replace background
- Option to mix with configurable levels
- Option to add custom background music

## Current Status

**Status**: ❌ **NOT IMPLEMENTED**

**Impact**: High - all background audio is lost during dubbing

**Priority**: High - critical for preserving video quality and user experience

**Implementation Effort**: Medium - requires source separation or audio mixing infrastructure

**Recommended Action**: Implement Option 1 (Source Separation) for best quality
