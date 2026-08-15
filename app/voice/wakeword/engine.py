from __future__ import annotations

import logging
from typing import Optional, Tuple
from app.voice.audio.audio_manager import AudioManager
from app.voice.wakeword.detector import WakeWordDetector
from app.voice.wakeword.listner import WakeWordListener

logger = logging.getLogger(__name__)


class WakeWordEngine:
    def __init__(self, audio_manager: AudioManager, detector: Optional[WakeWordDetector] = None) -> None:
        self.listener = WakeWordListener(audio_manager)
        self.detector = detector or WakeWordDetector()

    def wait_for_wakeword(self, max_iterations: Optional[int] = None) -> Tuple[bool, str, float]:
        """
        Polls audio chunks until the wake word is detected or max_iterations is reached.
        """
        logger.info("Waiting for wake word...")
        iterations = 0
        while max_iterations is None or iterations < max_iterations:
            chunk = self.listener.next_chunk()
            if chunk is None:
                iterations += 1
                continue

            detected, name, score = self.detector.detect(chunk)
            if detected:
                logger.info("Wake word detected: %s (score=%.2f)", name, score)
                return True, name, score
            iterations += 1

        return False, "", 0.0
