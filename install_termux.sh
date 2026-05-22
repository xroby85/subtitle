#!/bin/bash
# YouTube Subtitles - Termux Installer
# Run this in Termux

echo "========================================="
echo "  YouTube Subtitles - Termux Setup"
echo "========================================="
echo

# Update packages
echo "[1/4] Updating packages..."
pkg update -y

# Install dependencies
echo "[2/4] Installing Python & FFmpeg..."
pkg install -y python ffmpeg

# Install Python packages
echo "[3/4] Installing Python packages..."
pip install --upgrade pip
pip install pytubefix faster-whisper

# Create shortcut
echo "[4/4] Creating shortcut..."
cat > $PREFIX/bin/ytsubs << 'EOF'
#!/bin/bash
cd $HOME
python $HOME/YouTubeSubtitles/yt_subtitles.py
EOF
chmod +x $PREFIX/bin/ytsubs

# Copy script to home
mkdir -p $HOME/YouTubeSubtitles
cp yt_subtitles.py $HOME/YouTubeSubtitles/

echo
echo "========================================="
echo "  Installation complete!"
echo "========================================="
echo
echo "To run: ytsubs"
echo "Or: python ~/YouTubeSubtitles/yt_subtitles.py"
echo
