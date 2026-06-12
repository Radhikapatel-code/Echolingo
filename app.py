"""Streamlit frontend for Echolingo AI video dubbing.

Provides a web interface for uploading videos, selecting dub/caption languages,
and downloading the dubbed output. Uses ``@st.cache_resource`` to keep the
Whisper model loaded across reruns for fast repeated processing.
"""

from __future__ import annotations

import logging
import os
import tempfile

import streamlit as st
import whisper

from echolingo import (
    SUPPORTED_LANGUAGES,
    MAX_UPLOAD_SIZE_MB,
    DubbingError,
    dub_video,
)

# ── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Page Config ─────────────────────────────────────────────────────────────

st.set_page_config(page_title="Echolingo AI", page_icon="🎙️")


# ── Cached Model Loading ───────────────────────────────────────────────────


@st.cache_resource
def load_whisper_model() -> whisper.Whisper:
    """Load and cache the Whisper 'base' model across Streamlit reruns.

    The model (~150 MB) is downloaded on first run and kept in memory
    for all subsequent button clicks, avoiding 5-10s reload per request.
    """
    logger.info("Loading Whisper model (cached via @st.cache_resource)")
    return whisper.load_model("base")


# ── UI Layout ───────────────────────────────────────────────────────────────

st.title("🎙️ Echolingo – AI Video Dubber")
st.markdown("Dub your video into **36 languages** and optionally add translated captions.")

# ── File Upload ─────────────────────────────────────────────────────────────

uploaded_file = st.file_uploader("Upload MP4 Video", type=["mp4"])

if uploaded_file:
    # ── File size validation ────────────────────────────────
    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > MAX_UPLOAD_SIZE_MB:
        st.error(
            f"❌ File too large ({file_size_mb:.1f} MB). "
            f"Maximum allowed: {MAX_UPLOAD_SIZE_MB} MB."
        )
        st.stop()

    # ── Save to unique temp path (no collisions) ────────────
    upload_dir = tempfile.mkdtemp(prefix="echolingo_upload_")
    input_path = os.path.join(upload_dir, "input.mp4")
    output_path = os.path.join(upload_dir, "output.mp4")

    with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.video(input_path)

    # ── Language selection ──────────────────────────────────
    lang_options = {f"{name} ({code})": code for code, name in SUPPORTED_LANGUAGES.items()}

    target_display = st.selectbox("Select Dub Language", list(lang_options.keys()), index=9)
    target_lang = lang_options[target_display]

    # ── Caption options ─────────────────────────────────────
    add_captions = st.checkbox("📝 Add captions to video")

    caption_lang = target_lang
    if add_captions:
        caption_display = st.selectbox("Select Caption Language", list(lang_options.keys()))
        caption_lang = lang_options[caption_display]

    # ── Process ─────────────────────────────────────────────
    if st.button("🎙️ Generate Dubbed Video"):
        model = load_whisper_model()

        with st.spinner("Echolingo is processing... please wait"):
            try:
                dub_video(
                    video_path=input_path,
                    target_lang=target_lang,
                    output_path=output_path,
                    captions=add_captions,
                    caption_lang=caption_lang,
                    whisper_model=model,
                )

                st.success("✅ Dubbing completed!")
                st.video(output_path)

                with open(output_path, "rb") as f:
                    st.download_button(
                        "⬇️ Download Video",
                        f,
                        file_name="echolingo_dubbed.mp4",
                    )

            except DubbingError as e:
                st.error(f"❌ Dubbing failed: {e}")
                logger.exception("DubbingError during pipeline execution")
            except Exception as e:
                st.error(f"❌ Unexpected error: {e}")
                logger.exception("Unexpected error during pipeline execution")
