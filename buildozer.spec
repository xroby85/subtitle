[app]

title = YouTube Subtitles
package.name = ytsubtitles
package.domain = org.ytsubtitles
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0.0

requirements = python3,kivy,pytubefix,faster-whisper,ctranslate2

android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 24
android.ndk = 28c
android.archs = arm64-v8a
android.accept_sdk_license = True
android.skip_update = True

fullscreen = 0
orientation = portrait
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
