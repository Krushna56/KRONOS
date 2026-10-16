"""
Text-To-Speech (TTS) Engine
Synthesizes speech audio from generated text responses.
Supports:
1. pyttsx3 (local offline speech synthesis)
2. WAV/PCM audio stream generation for Mini Robot Speaker & Telephony Call output
"""

import io
import os
import wave
import logging
from typing import Optional
try:
    import pyttsx3
    _PYTTSX3_AVAILABLE = True
except ImportError:
    _PYTTSX3_AVAILABLE = False
    pyttsx3 = None

logger = logging.getLogger(__name__)


class TTSEngine:
    """
    Speech synthesizer for voice responses.
    """

    def __init__(self, rate: int = 175, volume: float = 1.0):
        self.rate = rate
        self.volume = volume
        self.engine = None
        self._init_engine()

    def _init_engine(self):
        if not _PYTTSX3_AVAILABLE:
            logger.warning("[TTS] pyttsx3 not installed. Speech output will be muted until installed ('pip install pyttsx3').")
            return
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", self.rate)
            self.engine.setProperty("volume", self.volume)
            logger.info("pyttsx3 TTS engine initialized.")
        except Exception as e:
            logger.warning(f"Could not initialize pyttsx3 engine: {e}")
            self.engine = None

    def speak(self, text: str) -> None:
        """
        Speak text immediately through local audio output.
        """
        if not text or not text.strip():
            return
        if self.engine is None:
            self._init_engine()
        if self.engine:
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                logger.error(f"Error during TTS speak: {e}")

    def synthesize_to_wav(self, text: str, output_path: str) -> bool:
        """
        Save synthesized speech to a WAV file on disk.
        """
        if not text or not text.strip():
            return False
        if self.engine is None:
            self._init_engine()
        if self.engine:
            try:
                self.engine.save_to_file(text, output_path)
                self.engine.runAndWait()
                return os.path.exists(output_path)
            except Exception as e:
                logger.error(f"Error saving TTS to file: {e}")
                return False
        return False

    def synthesize_pcm(self, text: str) -> bytes:
        """
        Synthesize text directly into PCM audio bytes for streaming over WebSocket (Robot / Twilio).
        """
        temp_wav = "temp_tts_stream.wav"
        try:
            success = self.synthesize_to_wav(text, temp_wav)
            if success and os.path.exists(temp_wav):
                with wave.open(temp_wav, "rb") as wf:
                    pcm_bytes = wf.readframes(wf.getnframes())
                os.remove(temp_wav)
                return pcm_bytes
        except Exception as e:
            logger.error(f"Failed to synthesize PCM: {e}")
            if os.path.exists(temp_wav):
                os.remove(temp_wav)
        return b""


_tts_instance: Optional[TTSEngine] = None


def get_tts_engine() -> TTSEngine:
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = TTSEngine()
    return _tts_instance
