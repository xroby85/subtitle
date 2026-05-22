#!/usr/bin/env python3
"""
YouTube Subtitles - Simple Android/Termux version
pip install pytubefix faster-whisper
"""

import os
import sys
import time
from pathlib import Path

def get_output_dir():
    """Get output directory"""
    if "ANDROID_DATA" in os.environ:
        storage = Path.home() / "storage" / "shared" / "YouTubeSubtitles"
    else:
        storage = Path.home() / "YouTubeSubtitles"
    storage.mkdir(parents=True, exist_ok=True)
    return storage

def download_audio(url, output_dir):
    """Download audio from YouTube"""
    from pytubefix import YouTube

    print(f"\n[1/3] Downloading...")
    yt = YouTube(url)
    print(f"  Title: {yt.title}")

    audio = yt.streams.filter(only_audio=True).first()
    if not audio:
        raise ValueError("No audio found")

    filename = audio.download(output_path=str(output_dir), filename_prefix="yt_")
    print(f"  Downloaded: {os.path.basename(filename)}")
    return filename, yt.title

def transcribe(audio_path, language="ro"):
    """Transcribe audio with Whisper"""
    from faster_whisper import WhisperModel

    print(f"\n[2/3] Loading Whisper model (base)...")
    model = WhisperModel("base", device="cpu", compute_type="int8")

    print(f"[3/3] Transcribing ({language})...")
    segments, info = model.transcribe(audio_path, language=language)

    text_parts = []
    for segment in segments:
        text_parts.append(segment.text.strip())
        pct = int(segment.end / info.duration * 100)
        print(f"\r  Progress: {pct}%", end="", flush=True)

    print()
    return " ".join(text_parts)

def save_result(text, title, output_dir):
    """Save transcription to file"""
    safe_title = "".join(c for c in title if c.isalnum() or c in " _-")[:30]
    filename = output_dir / f"{safe_title}.txt"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)

    return filename

def main():
    output_dir = get_output_dir()
    print(f"YouTube Subtitles")
    print(f"Output: {output_dir}")
    print()

    while True:
        print("-" * 40)
        print("1. Transcribe video")
        print("2. Open output folder")
        print("3. Exit")

        choice = input("\nChoice: ").strip()

        if choice == "1":
            url = input("YouTube URL: ").strip()
            if not url:
                continue

            lang = input("Language [ro]: ").strip() or "ro"

            try:
                audio_path, title = download_audio(url, output_dir)

                text = transcribe(audio_path, lang)

                filename = save_result(text, title, output_dir)

                # Cleanup
                if os.path.exists(audio_path):
                    os.remove(audio_path)

                print(f"\nDone! Saved: {filename}")
                print(f"Text length: {len(text)} chars")
                print(f"Preview: {text[:150]}...")

            except Exception as e:
                print(f"\nError: {e}")

        elif choice == "2":
            if sys.platform == "linux" and "ANDROID_DATA" in os.environ:
                os.system(f"termux-open {output_dir}")
            else:
                print(f"Path: {output_dir}")

        elif choice == "3":
            break

        print()

if __name__ == "__main__":
    main()
