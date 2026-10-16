"""
VAD Audio Subscriber
Connects the SpeechDetector to the Audio Bus.
Buffers audio chunks during speech and fires a callback when speech ends.
"""

import logging
from typing import Callable, List, Optional
import numpy as np

try:
    from app.voice.bus.subscriber import AudioSubscriber
    from app.voice.vad.speech_detector import SpeechDetector
except ImportError:
    from ..bus.subscriber import AudioSubscriber
    from .speech_detector import SpeechDetector

logger = logging.getLogger(__name__)


class VADAudioSubscriber(AudioSubscriber):
    """
    AudioSubscriber that feeds the real-time VAD engine.
    Whenever a complete utterance (sentence/command) is detected,
    it triggers `on_speech_detected(audio_chunks: List[np.ndarray])`.
    """

    def __init__(self, on_speech_detected: Optional[Callable[[List[np.ndarray]], None]] = None):
        self.detector = SpeechDetector()
        self.on_speech_detected = on_speech_detected

    def receive(self, audio_chunk: np.ndarray) -> None:
        """
        Process incoming audio chunk from the AudioWorker thread.
        """
        completed_audio = self.detector.process_chunk(audio_chunk)

        if completed_audio is not None:
            logger.info(f"VAD detected complete speech event ({len(completed_audio)} chunks).")
            if self.on_speech_detected:
                try:
                    self.on_speech_detected(completed_audio)
                except Exception:
                    logger.exception("Error in VAD on_speech_detected callback")

    def reset(self) -> None:
        self.detector.reset()
