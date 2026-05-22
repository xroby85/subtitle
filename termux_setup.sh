#!/bin/bash
# Termux setup for YouTube Subtitles

echo "=== YouTube Subtitles - Termux Setup ==="

# Update packages
pkg update -y

# Install dependencies
pkg install -y python ffmpeg

# Install Python packages
pip install --upgrade pip
pip install pytubefix openai-whisper pydub kivy

echo ""
echo "=== Setup complete! ==="
echo "Run: python main.py"
