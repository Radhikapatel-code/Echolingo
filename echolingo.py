import whisper
import moviepy.editor as mp
from moviepy.config import change_settings
from googletrans import Translator
from gtts import gTTS
import os
from datetime import timedelta
import srt
from pathlib import Path

# Configure ImageMagick path for moviepy
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})

def extract_audio(video_path, audio_path):
    """Extract audio from video."""
    video = mp.VideoFileClip(video_path)
    video.audio.write_audiofile(audio_path)
    video.audio.close()
    video.close()

def transcribe_audio(audio_path):
    """Convert audio to text using Whisper, optimized for Hindi."""
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, language="es", verbose=False)
    return result["segments"]

def translate_text(segments, target_lang):
    """Translate text to target language."""
    translator = Translator()
    translated_segments = []
    for segment in segments:
        translated_text = translator.translate(segment["text"], dest=target_lang).text
        translated_segments.append({
            "start": segment["start"],
            "end": segment["end"],
            "text": translated_text
        })
    return translated_segments

def generate_dubbed_audio(segments, target_lang, audio_output):
    """Create dubbed audio from text."""
    tts_clips = []
    for segment in segments:
        tts = gTTS(text=segment["text"], lang=target_lang, slow=False)
        temp_audio = f"temp_{segment['start']}.mp3"
        tts.save(temp_audio)
        audio_clip = mp.AudioFileClip(temp_audio).subclip(0, segment["end"] - segment["start"])
        tts_clips.append((audio_clip, segment["start"]))
        audio_clip.close()  # Close clip before deleting file
        try:
            os.remove(temp_audio)
        except PermissionError:
            print(f"Warning: Could not delete {temp_audio} (file in use). It will be cleaned up later.")
    
    # Create a silent audio clip for the full duration
    full_duration = max(segment["end"] for segment in segments)
    silent_audio = mp.AudioClip(lambda t: [0, 0], duration=full_duration, fps=44100)
    
    # Composite audio clips with proper timing
    audio_clips = [silent_audio] + [clip.set_start(start) for clip, start in tts_clips]
    final_audio = mp.CompositeAudioClip(audio_clips)
    final_audio.write_audiofile(audio_output, fps=44100)
    
    # Clean up
    silent_audio.close()
    final_audio.close()
    for clip, _ in tts_clips:
        clip.close()

def generate_subtitles(segments, subtitle_path):
    """Create SRT subtitle file."""
    subtitles = []
    for i, segment in enumerate(segments, 1):
        start = timedelta(seconds=segment["start"])
        end = timedelta(seconds=segment["end"])
        subtitle = srt.Subtitle(index=i, start=start, end=end, content=segment["text"])
        subtitles.append(subtitle)
    
    with open(subtitle_path, "w", encoding="utf-8") as f:
        f.write(srt.compose(subtitles))

def merge_video_audio_subtitles(video_path, dubbed_audio_path, subtitle_path, output_path):
    """Combine video, dubbed audio, and subtitles."""
    video = mp.VideoFileClip(video_path)
    dubbed_audio = mp.AudioFileClip(dubbed_audio_path)
    video = video.set_audio(dubbed_audio)
    
    subtitle_clips = []
    for i, subtitle in enumerate(srt.parse(Path(subtitle_path).read_text(encoding="utf-8")), 1):
        try:
            txt_clip = mp.TextClip(
                subtitle.content,
                fontsize=24,
                color="white",
                stroke_color="black",
                stroke_width=1,
                font="Arial",
                size=video.size
            )
            txt_clip = txt_clip.set_position(("center", video.h - 50)).set_start(subtitle.start.total_seconds()).set_end(subtitle.end.total_seconds())
            subtitle_clips.append(txt_clip)
        except Exception as e:
            print(f"Warning: Failed to create subtitle clip {i}: {e}")
    
    final_video = mp.CompositeVideoClip([video] + subtitle_clips)
    final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")
    
    # Clean up
    video.close()
    dubbed_audio.close()
    for clip in subtitle_clips:
        clip.close()

def process_video(video_path, target_lang, output_path):
    """Process the video through all steps."""
    audio_path = "temp_audio.wav"
    dubbed_audio_path = "dubbed_audio.mp3"
    subtitle_path = "subtitles.srt"
    
    try:
        print("Extracting audio...")
        extract_audio(video_path, audio_path)
        print("Transcribing audio...")
        segments = transcribe_audio(audio_path)
        print("Translating text...")
        translated_segments = translate_text(segments, target_lang)
        print("Generating dubbed audio...")
        generate_dubbed_audio(translated_segments, target_lang, dubbed_audio_path)
        print("Generating subtitles...")
        generate_subtitles(translated_segments, subtitle_path)
        print("Merging video, audio, and subtitles...")
        merge_video_audio_subtitles(video_path, dubbed_audio_path, subtitle_path, output_path)
        print(f"Done! Output saved to {output_path}")
    
    finally:
        # Clean up temporary files
        for path in [audio_path, dubbed_audio_path, subtitle_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except PermissionError:
                    print(f"Warning: Could not delete {path} (file in use). Try closing other programs or retrying.")
        # Clean up any remaining temp_*.mp3 files
        for temp_file in Path(".").glob("temp_*.mp3"):
            try:
                temp_file.unlink()
            except PermissionError:
                print(f"Warning: Could not delete {temp_file} (file in use). Try closing other programs or retrying.")

if __name__ == "__main__":
    video_input = "sample_video.mp4"  # Replace with your Hindi video file name
    target_language = "en"  # Translate and dub to English
    video_output = "output_video.mp4"
    
    if not os.path.exists(video_input):
        print(f"Error: Video file {video_input} not found.")
    else:
        process_video(video_input, target_language, video_output)