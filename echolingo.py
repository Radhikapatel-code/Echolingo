"""Echolingo — AI-powered multilingual video dubbing pipeline.

Provides a modular pipeline for transcribing, translating, and re-dubbing
video files into target languages with optional burned-in captions.

Pipeline stages:
    1. extract_audio    — Pull audio track from video as 16 kHz WAV
    2. transcribe       — Run Whisper speech-to-text on the audio
    3. translate_segments — Translate each segment to the target language
    4. generate_tts_audio — Synthesize dubbed audio via gTTS with timing sync
    5. generate_srt     — (optional) Create subtitle file for captions
    6. compose_video    — Mux new audio + optional subtitles onto original video
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import whisper
from deep_translator import GoogleTranslator
from gtts import gTTS
from moviepy import AudioFileClip, VideoFileClip
from pydub import AudioSegment

logger = logging.getLogger(__name__)

# ── Pipeline Constants ──────────────────────────────────────────────────────

MAX_SPEED_FACTOR: float = 1.35
"""Upper bound for speech speedup — beyond 1.35x speech becomes uncomfortable
and difficult to understand for most listeners."""

SPEEDUP_CHUNK_SIZE: int = 50
"""Chunk size in ms for pydub's WSOLA-based speedup algorithm."""

SPEEDUP_CROSSFADE: int = 10
"""Crossfade duration in ms between chunks during speedup to avoid clicks."""

MAX_UPLOAD_SIZE_MB: int = 50
"""Maximum allowed upload file size in megabytes."""

WHISPER_SAMPLE_RATE: int = 16000
"""Audio sample rate expected by the Whisper model (16 kHz mono)."""

# ── Supported Languages ────────────────────────────────────────────────────

SUPPORTED_LANGUAGES: dict[str, str] = {
    "af": "Afrikaans",
    "ar": "Arabic",
    "bn": "Bengali",
    "bs": "Bosnian",
    "ca": "Catalan",
    "cs": "Czech",
    "da": "Danish",
    "de": "German",
    "el": "Greek",
    "en": "English",
    "es": "Spanish",
    "fi": "Finnish",
    "fr": "French",
    "hi": "Hindi",
    "hr": "Croatian",
    "hu": "Hungarian",
    "id": "Indonesian",
    "it": "Italian",
    "ja": "Japanese",
    "ko": "Korean",
    "ms": "Malay",
    "nl": "Dutch",
    "no": "Norwegian",
    "pl": "Polish",
    "pt": "Portuguese",
    "ro": "Romanian",
    "ru": "Russian",
    "sv": "Swedish",
    "ta": "Tamil",
    "te": "Telugu",
    "th": "Thai",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "vi": "Vietnamese",
    "zh-cn": "Chinese (Simplified)",
    "zh-tw": "Chinese (Traditional)",
}
"""Languages supported by both gTTS and deep-translator.
Constrained to the gTTS subset since it is the narrower API."""


# ── Custom Exception ────────────────────────────────────────────────────────


class DubbingError(Exception):
    """Raised when any stage of the dubbing pipeline fails."""


# ── Utility Functions ───────────────────────────────────────────────────────


def format_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp format ``HH:MM:SS,mmm``.

    Args:
        seconds: Time value in fractional seconds.

    Returns:
        Formatted SRT timestamp string, e.g. ``00:01:23,456``.
    """
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02}:{mins:02}:{secs:02},{millis:03}"


def fit_audio_smart(audio: AudioSegment, target_ms: int) -> AudioSegment:
    """Fit an audio segment to a target duration using speed adjustment.

    Strategy:
        - If the audio is shorter than the target, pad with silence.
        - If longer, speed up (capped at ``MAX_SPEED_FACTOR`` to stay
          intelligible) and pad/trim to exact length.

    Args:
        audio: Source audio segment to fit.
        target_ms: Desired duration in milliseconds.

    Returns:
        Audio segment with duration exactly equal to *target_ms*.
    """
    current_ms = len(audio)

    if current_ms <= target_ms:
        return audio + AudioSegment.silent(duration=target_ms - current_ms)

    speed_factor = min(current_ms / target_ms, MAX_SPEED_FACTOR)

    audio = audio.speedup(
        playback_speed=speed_factor,
        chunk_size=SPEEDUP_CHUNK_SIZE,
        crossfade=SPEEDUP_CROSSFADE,
    )

    if len(audio) <= target_ms:
        return audio + AudioSegment.silent(duration=target_ms - len(audio))

    return audio[:target_ms]


# ── Pipeline Stage Functions ────────────────────────────────────────────────


def extract_audio(video_path: str, work_dir: str) -> str:
    """Extract audio track from a video file as 16 kHz mono WAV.

    Args:
        video_path: Path to the source video file.
        work_dir: Temporary working directory for intermediate files.

    Returns:
        Absolute path to the extracted WAV file.

    Raises:
        DubbingError: If audio extraction fails (e.g. no audio stream).
    """
    output_path = os.path.join(work_dir, "extracted.wav")
    try:
        video = VideoFileClip(video_path)
        if video.audio is None:
            video.close()
            raise DubbingError("Video has no audio track to extract.")
        video.audio.write_audiofile(
            output_path,
            fps=WHISPER_SAMPLE_RATE,
            nbytes=2,
            codec="pcm_s16le",
            logger=None,
        )
        video.close()
        logger.info("Extracted audio -> %s", output_path)
        return output_path
    except DubbingError:
        raise
    except Exception as e:
        raise DubbingError(f"Audio extraction failed: {e}") from e


def transcribe(audio_path: str, model: whisper.Whisper) -> list[dict]:
    """Transcribe audio using a pre-loaded Whisper model.

    Args:
        audio_path: Path to the 16 kHz WAV audio file.
        model: A pre-loaded ``whisper.Whisper`` model instance.

    Returns:
        List of segment dicts, each containing ``start`` (float),
        ``end`` (float), and ``text`` (str) keys.

    Raises:
        DubbingError: If Whisper transcription fails.
    """
    try:
        result = model.transcribe(audio_path, fp16=False)
        segments = result["segments"]
        logger.info("Transcribed %d segments", len(segments))
        return segments
    except Exception as e:
        raise DubbingError(f"Transcription failed: {e}") from e


def translate_segments(
    segments: list[dict],
    target_lang: str,
) -> list[dict]:
    """Translate transcribed segments to the target language.

    Each segment dict is shallow-copied and augmented with a
    ``translated_text`` key containing the translated string.

    Args:
        segments: Whisper segment dicts with ``text`` key.
        target_lang: Target language code (e.g. ``'es'``, ``'fr'``).

    Returns:
        New list of segment dicts, each with an added ``translated_text`` key.

    Raises:
        DubbingError: If translation fails for any segment.
    """
    translator = GoogleTranslator(source="auto", target=target_lang)
    translated: list[dict] = []
    i = 0

    try:
        for i, seg in enumerate(segments):
            text = seg["text"].strip()
            if not text:
                translated.append({**seg, "translated_text": ""})
                continue

            result = translator.translate(text)
            translated.append({**seg, "translated_text": result})
            logger.debug("Segment %d translated: %s -> %s", i, text[:40], result[:40])

        logger.info("Translated %d segments -> %s", len(translated), target_lang)
        return translated
    except Exception as e:
        raise DubbingError(f"Translation failed at segment {i}: {e}") from e


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

    Args:
        segments: Translated segment dicts with timing and ``translated_text``.
        target_lang: Language code for TTS synthesis (e.g. ``'es'``).
        duration_ms: Total duration of the original video in milliseconds.
        work_dir: Temp directory for intermediate TTS clips.

    Returns:
        Complete ``AudioSegment`` matching the original video duration.

    Raises:
        DubbingError: If TTS generation fails for any segment.
    """
    backbone = AudioSegment.silent(duration=duration_ms)
    i = 0

    try:
        for i, seg in enumerate(segments):
            start_ms = int(seg["start"] * 1000)
            end_ms = int(seg["end"] * 1000)
            target_ms = end_ms - start_ms
            if target_ms <= 0:
                continue

            text = seg.get("translated_text", "").strip()
            if not text:
                continue

            tts_path = os.path.join(work_dir, f"tts_{i}.mp3")
            gTTS(text=text, lang=target_lang).save(tts_path)

            speech = AudioSegment.from_mp3(tts_path)
            speech = fit_audio_smart(speech, target_ms)
            backbone = backbone.overlay(speech, position=start_ms)

            os.remove(tts_path)
            logger.debug("TTS segment %d: %dms -> fitted to %dms", i, len(speech), target_ms)

        logger.info("Generated dubbed audio track (%d ms)", len(backbone))
        return backbone
    except DubbingError:
        raise
    except Exception as e:
        raise DubbingError(f"TTS generation failed at segment {i}: {e}") from e


def generate_srt(
    segments: list[dict],
    target_lang: str,
    srt_path: str,
) -> None:
    """Generate an SRT subtitle file from translated segments.

    If segments already contain ``translated_text`` and *target_lang*
    matches the translation language, uses existing translations.
    Otherwise, translates fresh for the requested caption language.

    Args:
        segments: Segment dicts with timing keys and text.
        target_lang: Language code for the subtitle text.
        srt_path: Output path for the ``.srt`` file.

    Raises:
        DubbingError: If subtitle generation fails.
    """
    translator = GoogleTranslator(source="auto", target=target_lang)

    try:
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, seg in enumerate(segments, start=1):
                start = format_timestamp(seg["start"])
                end = format_timestamp(seg["end"])

                # Use pre-translated text if available for this language
                if "translated_text" in seg and seg.get("translated_text"):
                    text = seg["translated_text"]
                else:
                    text = translator.translate(seg["text"])

                f.write(f"{i}\n")
                f.write(f"{start} --> {end}\n")
                f.write(f"{text}\n\n")

        logger.info("Generated SRT subtitle file -> %s", srt_path)
    except Exception as e:
        raise DubbingError(f"Subtitle generation failed: {e}") from e


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

    Args:
        video_path: Path to the original input video.
        audio_segment: The full dubbed audio track.
        output_path: Desired path for the final output video.
        work_dir: Temp directory for intermediate files.
        srt_path: Path to ``.srt`` file to burn in, or ``None``.

    Returns:
        Absolute path to the output video file.

    Raises:
        DubbingError: If video composition or subtitle burning fails.
    """
    final_audio_path = os.path.join(work_dir, "final.wav")
    temp_video_path = os.path.join(work_dir, "temp_video.mp4")

    try:
        # Export dubbed audio to WAV
        audio_segment.export(final_audio_path, format="wav")

        # Mux audio with video
        video = VideoFileClip(video_path)
        dubbed_audio = AudioFileClip(final_audio_path)
        video = video.with_audio(dubbed_audio)

        video.write_videofile(
            temp_video_path,
            codec="libx264",
            audio_codec="aac",
            fps=video.fps,
            logger=None,
        )

        video.close()
        dubbed_audio.close()

        # Burn subtitles if requested
        if srt_path and os.path.exists(srt_path):
            # Normalize path for FFmpeg subtitle filter (forward slashes, escape colons and spaces)
            srt_ffmpeg = srt_path.replace("\\", "/").replace(":", "\\\\:").replace(" ", "\\\\ ")
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    temp_video_path,
                    "-vf",
                    f"subtitles={srt_ffmpeg}",
                    output_path,
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            logger.info("Burned subtitles into video -> %s", output_path)
        else:
            shutil.copy2(temp_video_path, output_path)
            logger.info("Composed video (no subtitles) -> %s", output_path)

        return output_path

    except subprocess.CalledProcessError as e:
        raise DubbingError(f"FFmpeg subtitle burn failed: {e.stderr}") from e
    except Exception as e:
        raise DubbingError(f"Video composition failed: {e}") from e


# ── Main Entry Point ────────────────────────────────────────────────────────


def dub_video(
    video_path: str,
    target_lang: str,
    output_path: str = "output.mp4",
    captions: bool = False,
    caption_lang: str = "en",
    whisper_model: whisper.Whisper | None = None,
) -> str:
    """Run the full dubbing pipeline on a video file.

    Creates a temporary working directory, runs all pipeline stages,
    and cleans up intermediate files regardless of success or failure.

    Args:
        video_path: Path to the input video.
        target_lang: Language code for dubbed audio (e.g. ``'es'``).
        output_path: Path for the output video file.
        captions: Whether to burn subtitles into the video.
        caption_lang: Language for subtitle text (can differ from dub).
        whisper_model: Pre-loaded Whisper model instance. If ``None``,
            a new ``base`` model is loaded (slow -- avoid in production).

    Returns:
        Absolute path to the output dubbed video.

    Raises:
        DubbingError: If any pipeline stage fails.
        FileNotFoundError: If the input video file doesn't exist.
        ValueError: If the target language is not supported.
    """
    # ── Input validation ────────────────────────────────────
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")
    if target_lang not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language: '{target_lang}'. "
            f"Choose from: {', '.join(sorted(SUPPORTED_LANGUAGES))}"
        )
    if captions and caption_lang not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported caption language: '{caption_lang}'.")

    work_dir = tempfile.mkdtemp(prefix="echolingo_")
    logger.info("Pipeline started -- work_dir=%s", work_dir)

    try:
        # 1. Load model if not provided
        if whisper_model is None:
            logger.warning(
                "Loading Whisper model on-the-fly. "
                "Pass a pre-loaded model via whisper_model= for better performance."
            )
            whisper_model = whisper.load_model("base")

        # 2. Extract audio
        audio_path = extract_audio(video_path, work_dir)

        # 3. Transcribe
        segments = transcribe(audio_path, whisper_model)
        if not segments:
            raise DubbingError("No speech detected in the video.")

        # 4. Translate
        translated = translate_segments(segments, target_lang)

        # 5. Get video duration for audio backbone
        video = VideoFileClip(video_path)
        duration_ms = int(video.duration * 1000)
        video.close()

        # 6. Generate dubbed TTS audio
        dubbed_audio = generate_tts_audio(translated, target_lang, duration_ms, work_dir)

        # 7. Generate SRT if captions requested
        srt_path = None
        if captions:
            srt_path = os.path.join(work_dir, "subtitles.srt")
            # If caption language differs from dub language, re-translate for subtitles
            if caption_lang == target_lang:
                generate_srt(translated, caption_lang, srt_path)
            else:
                generate_srt(segments, caption_lang, srt_path)

        # 8. Compose final video
        result = compose_video(video_path, dubbed_audio, output_path, work_dir, srt_path)
        logger.info("Pipeline completed -- output=%s", result)
        return result

    except (FileNotFoundError, ValueError):
        raise
    except DubbingError:
        raise
    except Exception as e:
        raise DubbingError(f"Pipeline failed unexpectedly: {e}") from e
    finally:
        # ALWAYS clean up temp directory -- even on crash
        shutil.rmtree(work_dir, ignore_errors=True)
        logger.info("Cleaned up working directory: %s", work_dir)
