#!/usr/bin/env python3
"""
YouTube Subtitles - Android App with Kivy
Features: multiple videos, text view, copy all, open file
"""

import os
import sys
import time
import threading
from pathlib import Path

from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import StringProperty, ListProperty, BooleanProperty, NumericProperty
from kivy.core.clipboard import Clipboard
from kivy.utils import platform

if platform == 'android':
    try:
        from android.permissions import request_permissions, Permission
        from android.storage import primary_external_storage_path
        STORAGE_PATH = Path(primary_external_storage_path())
    except:
        STORAGE_PATH = Path.home()
else:
    STORAGE_PATH = Path.home()

KV = '''
#:import dp kivy.metrics.dp
#:import Clipboard kivy.core.clipboard.Clipboard

<ResultCard@BoxLayout>:
    orientation: 'vertical'
    size_hint_y: None
    height: dp(180)
    padding: dp(10)
    spacing: dp(5)
    canvas.before:
        Color:
            rgba: 0.1, 0.1, 0.15, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(10)]
    BoxLayout:
        size_hint_y: None
        height: dp(30)
        Label:
            text: root.title_text if hasattr(root, 'title_text') else ''
            bold: True
            font_size: dp(14)
            halign: 'left'
            text_size: self.size
            valign: 'middle'
        Button:
            text: 'Copy'
            size_hint_x: 0.2
            background_color: 0.2, 0.6, 0.9, 1
            on_press: app.copy_single(root.result_index if hasattr(root, 'result_index') else 0)
    ScrollView:
        Label:
            text: root.content_text if hasattr(root, 'content_text') else ''
            text_size: self.width, None
            size_hint_y: None
            height: self.texture_size[1]
            font_size: dp(12)
            halign: 'left'
            valign: 'top'

Screen:
    canvas.before:
        Color:
            rgba: 0.06, 0.06, 0.1, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        orientation: 'vertical'
        padding: dp(12)
        spacing: dp(10)

        # Header
        Label:
            text: 'YouTube Subtitles'
            font_size: dp(22)
            bold: True
            size_hint_y: None
            height: dp(35)
            color: 0.9, 0.3, 0.5, 1

        # URL Input
        BoxLayout:
            size_hint_y: None
            height: dp(45)
            spacing: dp(8)
            TextInput:
                id: url_input
                hint_text: 'YouTube URL'
                multiline: False
                font_size: dp(14)
                padding: [dp(10), dp(10)]
                background_color: 0.15, 0.15, 0.2, 1
                foreground_color: 1, 1, 1, 1
                cursor_color: 0.9, 0.3, 0.5, 1
            Button:
                text: 'Add'
                size_hint_x: 0.2
                background_color: 0.9, 0.3, 0.5, 1
                on_press: app.add_to_queue()

        # Language & Queue
        BoxLayout:
            size_hint_y: None
            height: dp(40)
            spacing: dp(8)
            Label:
                text: 'Lang:'
                size_hint_x: 0.15
            Spinner:
                id: lang_spinner
                text: 'ro'
                values: ['ro', 'en', 'de', 'fr', 'es', 'it', 'hu', 'bg', 'sr']
                size_hint_x: 0.35
                background_color: 0.2, 0.2, 0.3, 1
            Label:
                text: f'Queue: {len(app.queue)}'
                size_hint_x: 0.3
                font_size: dp(12)
            Button:
                text: 'Clear'
                size_hint_x: 0.2
                background_color: 0.4, 0.2, 0.2, 1
                on_press: app.clear_queue()

        # Status
        Label:
            id: status_label
            text: app.status_text
            size_hint_y: None
            height: dp(25)
            font_size: dp(12)
            color: 0.7, 0.7, 0.7, 1

        ProgressBar:
            value: app.progress
            size_hint_y: None
            height: dp(5)

        # Buttons
        BoxLayout:
            size_hint_y: None
            height: dp(45)
            spacing: dp(8)
            Button:
                text: 'START'
                background_color: 0.9, 0.3, 0.5, 1
                bold: True
                on_press: app.start_process()
                disabled: app.is_processing
            Button:
                text: 'Copy All'
                background_color: 0.2, 0.6, 0.9, 1
                on_press: app.copy_all()
            Button:
                text: 'Open Folder'
                background_color: 0.2, 0.5, 0.3, 1
                on_press: app.open_folder()

        # Results
        ScrollView:
            BoxLayout:
                id: results_box
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(8)
'''


class YouTubeSubtitlesApp(App):
    status_text = StringProperty('Ready')
    progress = NumericProperty(0)
    is_processing = BooleanProperty(False)
    queue = ListProperty([])
    results = ListProperty([])

    def build(self):
        if platform == 'android':
            try:
                request_permissions([
                    Permission.INTERNET,
                    Permission.WRITE_EXTERNAL_STORAGE,
                    Permission.READ_EXTERNAL_STORAGE
                ])
            except:
                pass

        self.output_dir = STORAGE_PATH / "YouTubeSubtitles"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        return Builder.load_string(KV)

    def add_to_queue(self):
        url = self.root.ids.url_input.text.strip()
        if url and url not in self.queue:
            self.queue.append(url)
            self.root.ids.url_input.text = ''
            self.status_text = f'Added to queue ({len(self.queue)} videos)'

    def clear_queue(self):
        self.queue.clear()
        self.status_text = 'Queue cleared'

    def start_process(self):
        if not self.queue:
            self.status_text = 'Add videos first!'
            return
        self.is_processing = True
        self.results.clear()
        threading.Thread(target=self.process_all, daemon=True).start()

    def process_all(self):
        lang = self.root.ids.lang_spinner.text
        total = len(self.queue)

        for i, url in enumerate(self.queue):
            Clock.schedule_once(lambda dt, idx=i: self.update_status(f'Processing {idx+1}/{total}...'))

            try:
                text, title = self.process_single(url, lang)
                self.results.append({'title': title, 'text': text})

                # Save to file
                filename = self.output_dir / f"{title[:30]}.txt"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(text)

                Clock.schedule_once(lambda dt: self.refresh_results())

            except Exception as e:
                Clock.schedule_once(lambda dt, err=str(e): self.update_status(f'Error: {err[:40]}'))

        Clock.schedule_once(lambda dt: self.finish())

    def process_single(self, url, lang):
        from pytubefix import YouTube

        # Download
        Clock.schedule_once(lambda dt: self.update_status('Downloading...'))
        yt = YouTube(url)
        title = yt.title or "Unknown"

        audio = yt.streams.filter(only_audio=True).first()
        if not audio:
            raise ValueError("No audio stream")

        audio_file = audio.download(output_path=str(self.output_dir), filename_prefix="yt_")

        try:
            # Transcribe
            from faster_whisper import WhisperModel

            Clock.schedule_once(lambda dt: self.update_status('Loading model...'))
            model = WhisperModel("base", device="cpu", compute_type="int8")

            Clock.schedule_once(lambda dt: self.update_status('Transcribing...'))
            segments, info = model.transcribe(audio_file, language=lang)

            text_parts = []
            for segment in segments:
                text_parts.append(segment.text.strip())
                pct = int(segment.end / info.duration * 100)
                Clock.schedule_once(lambda dt, p=pct: setattr(self, 'progress', p))

            return " ".join(text_parts), title

        finally:
            if os.path.exists(audio_file):
                os.remove(audio_file)

    def update_status(self, msg):
        self.status_text = msg

    def refresh_results(self):
        self.root.ids.results_box.clear_widgets()

        for i, r in enumerate(self.results):
            card = Builder.load_string(f'''
ResultCard:
    title_text: "{r['title'][:40]}"
    content_text: """{r['text'][:500]}"""
    result_index: {i}
''')
            self.root.ids.results_box.add_widget(card)

    def finish(self):
        self.is_processing = False
        self.progress = 100
        self.status_text = f'Done! {len(self.results)} videos transcribed'
        self.queue.clear()

    def copy_single(self, index):
        if index < len(self.results):
            Clipboard.copy(self.results[index]['text'])
            self.status_text = 'Copied to clipboard!'

    def copy_all(self):
        if not self.results:
            self.status_text = 'No results to copy'
            return

        all_text = '\n\n===\n\n'.join(
            f"--- {r['title']} ---\n{r['text']}"
            for r in self.results
        )
        Clipboard.copy(all_text)
        self.status_text = f'Copied all {len(self.results)} results!'

    def open_folder(self):
        if platform == 'android':
            try:
                from android.storage import primary_external_storage_path
                os.system(f"termux-open {self.output_dir}")
            except:
                self.status_text = f'Path: {self.output_dir}'
        else:
            self.status_text = f'Path: {self.output_dir}'


if __name__ == '__main__':
    YouTubeSubtitlesApp().run()
