#!/usr/bin/env python3
"""
YouTube Subtitles - Android App
Works with Termux or as Kivy app
"""

import os
import sys
import time
import threading
from pathlib import Path

# Try Kivy first, fall back to terminal
try:
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.button import Button
    from kivy.uix.textinput import TextInput
    from kivy.uix.label import Label
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.spinner import Spinner
    from kivy.clock import Clock
    from kivy.core.clipboard import Clipboard
    HAS_KIVY = True
except ImportError:
    HAS_KIVY = False

class Transcriber:
    """Core transcription logic"""

    def __init__(self):
        self.storage_path = self._get_storage_path()
        self.output_dir = self.storage_path / "YouTubeSubtitles"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _get_storage_path(self):
        if sys.platform == "linux" and "ANDROID_DATA" in os.environ:
            home = Path.home()
            storage = home / "storage" / "shared"
            if storage.exists():
                return storage
        return Path.home() / "YouTubeSubtitles"

    def download_video(self, url, callback=None):
        try:
            from pytubefix import YouTube
        except ImportError:
            raise ImportError("pip install pytubefix")

        if callback:
            callback("Downloading...")

        yt = YouTube(url)
        audio = yt.streams.filter(only_audio=True).first()

        if not audio:
            raise ValueError("No audio stream found")

        filename = audio.download(output_path=str(self.output_dir), filename_prefix="yt_")
        return filename

    def transcribe(self, audio_path, language="ro", callback=None):
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise ImportError("pip install faster-whisper")

        if callback:
            callback("Loading model...")

        model = WhisperModel("base", device="cpu", compute_type="int8")

        if callback:
            callback("Transcribing...")

        segments, info = model.transcribe(audio_path, language=language)

        text_parts = []
        for segment in segments:
            text_parts.append(segment.text.strip())
            if callback:
                pct = int(segment.end / info.duration * 100)
                callback(f"Transcribing: {pct}%")

        return " ".join(text_parts)

    def process_video(self, url, language="ro", callback=None):
        # Download
        audio_file = self.download_video(url, callback)

        try:
            # Transcribe
            text = self.transcribe(audio_file, language, callback)

            # Save
            filename = self.output_dir / f"transcript_{int(time.time())}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(text)

            return text, filename
        finally:
            # Cleanup audio
            if os.path.exists(audio_file):
                os.remove(audio_file)


class TerminalApp:
    """Terminal version for Termux"""

    def __init__(self):
        self.transcriber = Transcriber()

    def run(self):
        print(f"Output: {self.transcriber.output_dir}")
        print()

        while True:
            print("=" * 50)
            print("YouTube Subtitles")
            print("=" * 50)
            print("1. Transcribe video")
            print("2. Exit")
            print()

            choice = input("Choice: ").strip()

            if choice == "1":
                url = input("YouTube URL: ").strip()
                if not url:
                    continue

                lang = input("Language (ro/en/de) [ro]: ").strip() or "ro"

                try:
                    def status(msg):
                        print(f"\r{msg}", end="", flush=True)

                    text, filename = self.transcriber.process_video(url, lang, status)
                    print(f"\n\nDone! Saved: {filename}")
                    print(f"Preview: {text[:200]}...")

                except Exception as e:
                    print(f"\nError: {e}")

            elif choice == "2":
                break

            print()


class KivyApp(App):
    """Kivy version for Android"""

    def build(self):
        self.transcriber = Transcriber()
        self.results = []

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Title
        title = Label(text='YouTube Subtitles', font_size=24, size_hint_y=0.1)
        layout.add_widget(title)

        # URL input
        self.url_input = TextInput(
            hint_text='YouTube URL',
            multiline=False,
            size_hint_y=0.08
        )
        layout.add_widget(self.url_input)

        # Language selector
        lang_layout = BoxLayout(size_hint_y=0.08)
        lang_layout.add_widget(Label(text='Language:', size_hint_x=0.3))
        self.lang_spinner = Spinner(
            text='ro',
            values=['ro', 'en', 'de', 'fr', 'es', 'it', 'hu'],
            size_hint_x=0.7
        )
        lang_layout.add_widget(self.lang_spinner)
        layout.add_widget(lang_layout)

        # Status
        self.status_label = Label(text='Ready', size_hint_y=0.06)
        layout.add_widget(self.status_label)

        # Transcribe button
        self.btn = Button(
            text='TRANSCRIBE',
            size_hint_y=0.1,
            background_color=[0.9, 0.3, 0.5, 1]
        )
        self.btn.bind(on_press=self.start_transcribe)
        layout.add_widget(self.btn)

        # Results
        scroll = ScrollView(size_hint_y=0.5)
        self.results_box = BoxLayout(orientation='vertical', size_hint_y=None)
        self.results_box.bind(minimum_height=self.results_box.setter('height'))
        scroll.add_widget(self.results_box)
        layout.add_widget(scroll)

        # Copy all button
        copy_btn = Button(text='Copy All Text', size_hint_y=0.08)
        copy_btn.bind(on_press=self.copy_all)
        layout.add_widget(copy_btn)

        return layout

    def start_transcribe(self, instance):
        url = self.url_input.text.strip()
        if not url:
            self.status_label.text = 'Enter a URL!'
            return

        self.btn.disabled = True
        self.status_label.text = 'Starting...'
        threading.Thread(target=self.do_transcribe, args=(url,), daemon=True).start()

    def do_transcribe(self, url):
        try:
            lang = self.lang_spinner.text
            text, filename = self.transcriber.process_video(
                url, lang,
                lambda msg: Clock.schedule_once(lambda dt: self.update_status(msg))
            )

            Clock.schedule_once(lambda dt: self.show_result(text, filename))

        except Exception as e:
            Clock.schedule_once(lambda dt: self.update_status(f'Error: {str(e)[:50]}'))
        finally:
            Clock.schedule_once(lambda dt: self.enable_button())

    def update_status(self, msg):
        self.status_label.text = msg

    def enable_button(self):
        self.btn.disabled = False

    def show_result(self, text, filename):
        self.results.append(text)
        self.status_label.text = f'Done! Saved: {filename.name}'

        # Add to results view
        box = BoxLayout(size_hint_y=None, height=100, padding=5)
        box.add_widget(Label(text=text[:100] + '...', text_size=(None, None)))
        self.results_box.add_widget(box)

    def copy_all(self, instance):
        all_text = '\n\n---\n\n'.join(self.results)
        Clipboard.copy(all_text)
        self.status_label.text = 'Copied to clipboard!'


def main():
    if HAS_KIVY and len(sys.argv) > 1 and sys.argv[1] == '--kivy':
        KivyApp().run()
    else:
        TerminalApp().run()


if __name__ == '__main__':
    main()
