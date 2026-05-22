[app]

# App info
title = YouTube Subtitles
package.name = ytsubtitles
package.domain = org.ytsubtitles
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0.0

# Requirements
requirements = python3,kivy,pytubefix,faster-whisper,ctranslate2

# Android
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a

# Build
fullscreen = 0
orientation = portrait

[buildozer]
log_level = 2
warn_on_root = 1
