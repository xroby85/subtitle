#!/usr/bin/env python3
"""
Simple Termux version - works without Kivy
Uses pytubefix + faster-whisper
"""

import os
import sys
import time
from pathlib import Path

def get_storage_path():
    """Get Termux storage path"""
    home = Path.home()
    storage = home / "storage" / "shared"
    if storage.exists():
        return storage
    return home

def download_video(url, output_path):
    """Download audio from YouTube"""
    try:
        from pytubefix import YouTube
    except ImportError:
        print("Install pytubefix: pip install pytubefix")
        return None

    print(f"Downloading: {url[:50]}...")
    yt = YouTube(url)

    # Get audio stream
    audio = yt.streams.filter(only_audio=True).first()
    if not audio:
        print("No audio stream found!")
        return None

    # Download
    filename = audio.download(output_path=str(output_path), filename_prefix="yt_")
    print(f"Downloaded: {os.path.basename(filename)}")
    return filename

def transcribe_audio(audio_path, language="ro"):
    """Transcribe audio using Whisper"""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("Install faster-whisper: pip install faster-whisper")
        return None

    print("Loading Whisper model...")
    model = WhisperModel("base", device="cpu", compute_type="int8")

    print("Transcribing...")
    segments, info = model.transcribe(audio_path, language=language)

    text_parts = []
    for segment in segments:
        text_parts.append(segment.text.strip())
        print(f"\rProgress: {int(segment.end / info.duration * 100)}%", end="", flush=True)

    print()
    return " ".join(text_parts)

def save_text(text, filename):
    """Save text to file"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Saved: {filename}")

def main():
    storage = get_storage_path()
    output_dir = storage / "YouTubeSubtitles"
    output_dir.mkdir(exist_ok=True)

    print(f"Output directory: {output_dir}")
    print()

    while True:
        print("=" * 50)
        print("YouTube Subtitles - Termux")
        print("=" * 50)
        print("1. Transcribe video")
        print("2. Exit")
        print()

        choice = input("Choice: ").strip()

        if choice == "1":
            url = input("YouTube URL: ").strip()
            if not url:
                continue

            lang = input("Language (ro/en/de): ").strip() or "ro"

            try:
                # Download
                audio_file = download_video(url, output_dir)
                if not audio_file:
                    continue

                # Transcribe
                text = transcribe_audio(audio_file, lang)
                if not text:
                    continue

                # Save
                filename = output_dir / f"transcript_{int(time.time())}.txt"
                save_text(text, filename)

                # Cleanup audio
                if os.path.exists(audio_file):
                    os.remove(audio_file)

                print(f"\nDone! File: {filename}")
                print(f"Text preview: {text[:100]}...")

            except Exception as e:
                print(f"Error: {e}")

        elif choice == "2":
            break

        print()

if __name__ == "__main__":
    main()
