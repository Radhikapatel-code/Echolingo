import os
import whisper
import subprocess
from moviepy import VideoFileClip, AudioFileClip
from pydub import AudioSegment
from gtts import gTTS
from deep_translator import GoogleTranslator


# --------------------------------------------------
# Timestamp formatter for SRT
# --------------------------------------------------
def format_timestamp(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02}:{mins:02}:{secs:02},{millis:03}"


# --------------------------------------------------
# Generate SRT file
# --------------------------------------------------
def generate_srt(segments, target_lang, srt_path):
    translator = GoogleTranslator(source="auto", target=target_lang)

    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, start=1):
            start = format_timestamp(seg["start"])
            end = format_timestamp(seg["end"])
            text = translator.translate(seg["text"])

            f.write(f"{i}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{text}\n\n")


# --------------------------------------------------
# Smart audio fitting (speed-aware)
# --------------------------------------------------
def fit_audio_smart(audio: AudioSegment, target_ms: int) -> AudioSegment:
    current_ms = len(audio)

    if current_ms <= target_ms:
        return audio + AudioSegment.silent(target_ms - current_ms)

    speed_factor = min(current_ms / target_ms, 1.35)

    audio = audio.speedup(
        playback_speed=speed_factor,
        chunk_size=50,
        crossfade=10
    )

    if len(audio) <= target_ms:
        return audio + AudioSegment.silent(target_ms - len(audio))

    return audio[:target_ms]


# --------------------------------------------------
# MAIN FUNCTION
# --------------------------------------------------
def dub_video(
    video_path: str,
    target_lang: str,
    output_path: str = "output.mp4",
    captions: bool = False,
    caption_lang: str = "en"
):
    video = VideoFileClip(video_path)
    duration_ms = int(video.duration * 1000)

    backbone = AudioSegment.silent(duration=duration_ms)

    extracted_audio = "extracted.wav"
    video.audio.write_audiofile(
        extracted_audio,
        fps=16000,
        nbytes=2,
        codec="pcm_s16le",
        logger=None
    )

    model = whisper.load_model("base")
    result = model.transcribe(extracted_audio, fp16=False)
    segments = result["segments"]

    srt_file = None
    if captions:
        srt_file = "subtitles.srt"
        generate_srt(segments, caption_lang, srt_file)

    for i, seg in enumerate(segments):
        start_ms = int(seg["start"] * 1000)
        end_ms = int(seg["end"] * 1000)
        target_ms = end_ms - start_ms
        if target_ms <= 0:
            continue

        translated = GoogleTranslator(
            source="auto",
            target=target_lang
        ).translate(seg["text"])

        tts_file = f"tts_{i}.mp3"
        gTTS(text=translated, lang=target_lang).save(tts_file)

        speech = AudioSegment.from_mp3(tts_file)
        speech = fit_audio_smart(speech, target_ms)

        backbone = backbone.overlay(speech, position=start_ms)
        os.remove(tts_file)

    final_audio = "final.wav"
    backbone.export(final_audio, format="wav")

    dubbed_audio = AudioFileClip(final_audio)
    video = video.with_audio(dubbed_audio)
    temp_video = "temp_video.mp4"

    video.write_videofile(
        temp_video,
        codec="libx264",
        audio_codec="aac",
        fps=video.fps,
        logger=None
    )

    video.close()
    dubbed_audio.close()

    # --------------------------------------------------
    # Burn subtitles with FFmpeg (SAFE WAY)
    # --------------------------------------------------
    if captions and srt_file:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i", temp_video,
                "-vf", f"subtitles={srt_file}",
                output_path
            ],
            check=True
        )
        os.remove(temp_video)
        os.remove(srt_file)
    else:
        os.rename(temp_video, output_path)

    os.remove(final_audio)
    os.remove(extracted_audio)
