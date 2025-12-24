import streamlit as st
import os
from echolingo import dub_video

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(page_title="Echolingo AI", page_icon="🎙️")
st.title("🎙️ Echolingo – AI Video Dubber")
st.markdown("Dub your video and optionally add translated captions.")

# --------------------------------------------------
# FILE UPLOAD
# --------------------------------------------------
uploaded_file = st.file_uploader("Upload MP4 Video", type=["mp4"])

if uploaded_file:
    with open("input.mp4", "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.video("input.mp4")

    # --------------------------------------------------
    # LANGUAGE SELECTION
    # --------------------------------------------------
    target_lang = st.selectbox(
        "Select Dub Language",
        ["en", "hi", "es", "fr", "de"]
    )

    # --------------------------------------------------
    # CAPTION OPTIONS
    # --------------------------------------------------
    add_captions = st.checkbox("📝 Add captions to video")

    caption_lang = "en"
    if add_captions:
        caption_lang = st.selectbox(
            "Select Caption Language",
            ["en", "hi", "es", "fr", "de"]
        )

    # --------------------------------------------------
    # RUN PROCESS
    # --------------------------------------------------
    if st.button("🎙️ Generate Dubbed Video"):
        with st.spinner("Echolingo is processing... please wait"):
            try:
                dub_video(
                    video_path="input.mp4",
                    target_lang=target_lang,
                    output_path="output.mp4",
                    captions=add_captions,
                    caption_lang=caption_lang
                )

                st.success("✅ Dubbing completed!")
                st.video("output.mp4")

                with open("output.mp4", "rb") as f:
                    st.download_button(
                        "⬇️ Download Video",
                        f,
                        file_name="echolingo_dubbed.mp4"
                    )

            except Exception as e:
                st.error(f"❌ Error: {e}")
