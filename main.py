#!/usr/bin/env python3
"""
YouTube Subtitles Android — Kivy app for transcribing YouTube videos
Requirements: kivy, pytubefix, requests, pydub
"""

import os
import threading
import time
from datetime import datetime

from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import StringProperty, ListProperty, BooleanProperty, NumericProperty
from kivy.core.clipboard import Clipboard
from kivy.utils import platform

if platform == 'android':
    from android.permissions import request_permissions, Permission
    from android.storage import primary_external_storage_path
    STORAGE_PATH = primary_external_storage_path()
else:
    STORAGE_PATH = os.path.expanduser("~")

KV = '''
#:import dp kivy.metrics.dp

<VideoItem@BoxLayout>:
    orientation: 'horizontal'
    size_hint_y: None
    height: dp(60)
    padding: dp(8)
    spacing: dp(8)
    canvas.before:
        Color:
            rgba: 0.12, 0.12, 0.18, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(8)]
    Label:
        text: root.title if hasattr(root, 'title') else ''
        text_size: self.size
        halign: 'left'
        valign: 'middle'
        shorten: True
        shorten_from: 'right'
        font_size: dp(14)
    Label:
        text: root.status if hasattr(root, 'status') else ''
        size_hint_x: 0.3
        font_size: dp(12)
        color: 0.6, 0.9, 0.6, 1

<ResultItem@BoxLayout>:
    orientation: 'vertical'
    size_hint_y: None
    height: dp(120)
    padding: dp(8)
    canvas.before:
        Color:
            rgba: 0.1, 0.1, 0.15, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(8)]
    BoxLayout:
        size_hint_y: 0.3
        Label:
            text: root.title if hasattr(root, 'title') else ''
            text_size: self.size
            halign: 'left'
            valign: 'middle'
            bold: True
            font_size: dp(14)
        Button:
            text: 'Copy'
            size_hint_x: 0.25
            background_color: 0.2, 0.6, 0.9, 1
            on_press: root.copy_text()
    ScrollView:
        Label:
            text: root.text if hasattr(root, 'text') else ''
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
        padding: dp(16)
        spacing: dp(12)

        # Header
        Label:
            text: 'YouTube Subtitles'
            font_size: dp(24)
            bold: True
            size_hint_y: None
            height: dp(40)
            color: 0.9, 0.3, 0.5, 1

        # URL Input
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            spacing: dp(8)

            TextInput:
                id: url_input
                hint_text: 'Paste YouTube URL here...'
                multiline: False
                font_size: dp(14)
                padding: [dp(12), dp(12)]
                background_color: 0.15, 0.15, 0.2, 1
                foreground_color: 1, 1, 1, 1
                cursor_color: 0.9, 0.3, 0.5, 1

            Button:
                text: '+ Add'
                size_hint_x: 0.25
                background_color: 0.9, 0.3, 0.5, 1
                on_press: app.add_video()

        # Language selector
        BoxLayout:
            size_hint_y: None
            height: dp(40)
            spacing: dp(8)
            Label:
                text: 'Language:'
                size_hint_x: 0.3
                font_size: dp(14)
            Spinner:
                id: lang_spinner
                text: 'ro'
                values: ['ro', 'en', 'de', 'fr', 'es', 'it', 'hu', 'bg', 'sr', 'hr']
                size_hint_x: 0.7
                background_color: 0.2, 0.2, 0.3, 1

        # Progress section
        BoxLayout:
            size_hint_y: None
            height: dp(30)
            Label:
                id: progress_label
                text: app.progress_text
                font_size: dp(12)
                color: 0.7, 0.7, 0.7, 1

        ProgressBar:
            id: progress_bar
            value: app.progress_value
            size_hint_y: None
            height: dp(6)

        # Start button
        Button:
            text: 'START TRANSCRIPTION'
            size_hint_y: None
            height: dp(50)
            background_color: 0.9, 0.3, 0.5, 1
            bold: True
            font_size: dp(16)
            on_press: app.start_processing()
            disabled: app.is_processing

        # Tabs
        BoxLayout:
            size_hint_y: None
            height: dp(40)
            spacing: dp(4)
            ToggleButton:
                text: 'Queue'
                state: 'down' if app.current_tab == 'queue' else 'normal'
                group: 'tabs'
                on_press: app.current_tab = 'queue'
                background_color: (0.9, 0.3, 0.5, 1) if app.current_tab == 'queue' else (0.15, 0.15, 0.2, 1)
            ToggleButton:
                text: 'Results'
                group: 'tabs'
                on_press: app.current_tab = 'results'
                background_color: (0.9, 0.3, 0.5, 1) if app.current_tab == 'results' else (0.15, 0.15, 0.2, 1)

        # Content area
        ScrollView:
            BoxLayout:
                id: content_box
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(8)
'''


class YouTubeSubtitlesApp(App):
    progress_text = StringProperty('')
    progress_value = NumericProperty(0)
    is_processing = BooleanProperty(False)
    current_tab = StringProperty('queue')
    video_queue = ListProperty([])
    results = ListProperty([])

    def build(self):
        if platform == 'android':
            request_permissions([
                Permission.INTERNET,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE
            ])
        return Builder.load_string(KV)

    def add_video(self):
        url = self.root.ids.url_input.text.strip()
        if url and url not in [v['url'] for v in self.video_queue]:
            self.video_queue.append({
                'url': url,
                'title': url[:40] + '...' if len(url) > 40 else url,
                'status': 'Pending'
            })
            self.root.ids.url_input.text = ''
            self.update_display()

    def start_processing(self):
        if not self.video_queue:
            self.progress_text = 'Add a video first!'
            return
        self.is_processing = True
        threading.Thread(target=self.process_queue, daemon=True).start()

    def process_queue(self):
        lang = self.root.ids.lang_spinner.text
        for i, video in enumerate(self.video_queue):
            if video['status'] == 'Done':
                continue
            Clock.schedule_once(lambda dt, idx=i: self.update_status(idx, 'Downloading...'))
            try:
                result = self.download_and_transcribe(video['url'], lang, i)
                if result:
                    Clock.schedule_once(lambda dt, idx=i: self.update_status(idx, 'Done'))
                    self.results.append({
                        'title': video['title'],
                        'text': result,
                        'timestamp': datetime.now().strftime('%H:%M')
                    })
            except Exception as e:
                Clock.schedule_once(lambda dt, idx=i, err=str(e): self.update_status(idx, f'Error: {err[:20]}'))
        Clock.schedule_once(lambda dt: self.finish_processing())

    def download_and_transcribe(self, url, lang, index):
        try:
            from pytubefix import YouTube
            import whisper
        except ImportError:
            Clock.schedule_once(lambda dt: self.set_progress('Install: pip install pytubefix openai-whisper'))
            return None

        # Download audio
        yt = YouTube(url, on_progress_callback=lambda stream, chunk, bytes_remaining: self.update_download_progress(stream, bytes_remaining))
        Clock.schedule_once(lambda dt: self.set_progress(f'Downloading: {yt.title[:30]}...'))

        audio_stream = yt.streams.filter(only_audio=True).first()
        temp_file = audio_stream.download(output_path=STORAGE_PATH, filename_prefix='yt_sub_')

        # Convert to wav
        Clock.schedule_once(lambda dt: self.set_progress('Converting audio...'))
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(temp_file)
            wav_file = temp_file.replace('.mp4', '.wav')
            audio.export(wav_file, format='wav')
            os.remove(temp_file)
        except:
            wav_file = temp_file

        # Transcribe
        Clock.schedule_once(lambda dt: self.set_progress('Transcribing with AI...'))
        model = whisper.load_model('base')
        result = model.transcribe(wav_file, language=lang)

        # Cleanup
        if os.path.exists(wav_file):
            os.remove(wav_file)

        return result['text']

    def update_download_progress(self, stream, bytes_remaining):
        total = stream.filesize
        downloaded = total - bytes_remaining
        pct = int((downloaded / total) * 100)
        Clock.schedule_once(lambda dt: self.set_progress(f'Downloading: {pct}%'))

    def set_progress(self, text):
        self.progress_text = text

    def update_status(self, index, status):
        if index < len(self.video_queue):
            self.video_queue[index]['status'] = status
            self.update_display()

    def update_display(self):
        self.root.ids.content_box.clear_widgets()
        if self.current_tab == 'queue':
            for v in self.video_queue:
                item = Builder.load_string(f'''
BoxLayout:
    orientation: 'horizontal'
    size_hint_y: None
    height: dp(50)
    padding: dp(8)
    canvas.before:
        Color:
            rgba: 0.12, 0.12, 0.18, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(8)]
    Label:
        text: "{v['title']}"
        text_size: self.size
        halign: 'left'
        valign: 'middle'
        shorten: True
    Label:
        text: "{v['status']}"
        size_hint_x: 0.3
        font_size: dp(11)
        color: (0.6, 0.9, 0.6, 1) if '{v['status']}' == 'Done' else (0.9, 0.6, 0.3, 1)
''')
                self.root.ids.content_box.add_widget(item)
        else:
            for r in self.results:
                box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(150), padding=dp(8))
                with box.canvas.before:
                    from kivy.graphics import Color, RoundedRectangle
                    Color(0.1, 0.1, 0.15, 1)
                    RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(8)])

                header = BoxLayout(size_hint_y=0.3)
                header.add_widget(Label(text=r['title'], bold=True, font_size=dp(13)))
                copy_btn = Button(text='Copy All', size_hint_x=0.25, background_color=(0.2, 0.6, 0.9, 1))
                copy_btn.bind(on_press=lambda dt, txt=r['text']: self.copy_text(txt))
                header.add_widget(copy_btn)
                box.add_widget(header)

                scroll = ScrollView()
                lbl = Label(text=r['text'], text_size=(None, None), font_size=dp(11), halign='left', valign='top')
                lbl.bind(texture_size=lambda instance, size: setattr(instance, 'height', size[1]))
                lbl.bind(width=lambda instance, width: setattr(instance, 'text_size', (width, None)))
                scroll.add_widget(lbl)
                box.add_widget(scroll)

                self.root.ids.content_box.add_widget(box)

    def copy_text(self, text):
        Clipboard.copy(text)
        self.progress_text = 'Text copied to clipboard!'

    def finish_processing(self):
        self.is_processing = False
        self.progress_text = 'All done!'
        self.progress_value = 100


if __name__ == '__main__':
    YouTubeSubtitlesApp().run()
