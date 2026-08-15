from __future__ import annotations

from app.voice.audio.audio_manager import AudioManager


class WakeWordListener:
    def __init__(self, audio_manager: AudioManager) -> None:
        self.audio_manager = audio_manager

    def next_chunk(self):
        return self.audio_manager.read()

    