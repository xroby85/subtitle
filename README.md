# YouTube Subtitles Android

Android app for transcribing YouTube videos using AI.

## Features
- Download audio from YouTube
- Transcribe using Whisper AI
- Multiple language support
- Copy text to clipboard
- Queue multiple videos

## Install on Android

### Option 1: Build with Buildozer
```bash
pip install buildozer
buildozer android debug
```

### Option 2: Use Termux
```bash
pkg install python ffmpeg
pip install pytubefix openai-whisper pydub
python main.py
```

## Requirements
- Python 3.8+
- FFmpeg (for audio conversion)
