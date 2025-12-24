# 🎙️ Echolingo  
## AI-Powered Multilingual Video Dubbing & Captioning Platform

Echolingo is an end-to-end AI application that automatically **dubs videos into multiple languages** and optionally **adds translated captions**, while preserving sentence completeness, timing, and audio clarity.

Unlike simple AI demos, Echolingo focuses on **real-world engineering challenges** in audio-video processing such as synchronization, timing mismatches, and sentence expansion during translation.

---

## 🚀 Problem Statement

When dubbing videos into other languages:

- Translated speech is often **longer** than the original
- Naive approaches **cut sentences**, **overlap audio**, or **distort pitch**
- Subtitle rendering frequently breaks due to font and platform issues
- Audio/video pipelines fail due to OS-level dependencies

**Echolingo solves these issues using a production-style pipeline.**

---

## ✨ Key Features

### 🎧 AI Video Dubbing
- Automatic speech transcription using Whisper
- Language translation with sentence-level accuracy
- AI-generated speech using Text-to-Speech

### ⏱️ Smart Audio Synchronization
- Dynamically adjusts speech speed within human-safe limits
- Ensures **complete sentences fit original time slots**
- Prevents audio overlap and pitch distortion

### 📝 Optional Multi-Language Captions
- Generate captions in any supported language
- Subtitles are **burned directly into the video** using FFmpeg
- Works on all video players (no external subtitle files needed)

### 🎛️ Interactive Frontend
- Simple Streamlit UI
- Independent selection of:
  - Dub language
  - Caption language
- One-click video generation and download

---

## 🧠 Engineering Highlights

This project demonstrates **applied AI + systems engineering**, including:

- Handling variable-length translations
- Designing non-overlapping audio pipelines
- Avoiding pitch distortion during speed adjustment
- Managing large media files safely
- Integrating multiple AI components into a stable workflow
- Solving real OS, FFmpeg, and dependency issues

---

## 🛠️ Tech Stack

| Category | Tools |
|--------|------|
Speech Recognition | OpenAI Whisper |
Translation | Google Translator (deep-translator) |
Text-to-Speech | gTTS |
Audio Processing | Pydub |
Video Processing | MoviePy, FFmpeg |
Frontend | Streamlit |
Language | Python 3.11 |

---

## 🧩 High-Level Architecture

