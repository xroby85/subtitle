#!/bin/bash
# Quick install for Termux - just the essentials

echo "Installing YouTube Subtitles..."

# Check if Termux
if [ -d "/data/data/com.termux" ]; then
    pkg update -y
    pkg install -y python ffmpeg
fi

# Install Python packages
pip install pytubefix faster-whisper

echo "Done! Run: python yt_subtitles.py"
