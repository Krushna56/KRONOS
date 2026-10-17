"""
Wake Word Engine
Orchestrates the wake word detection loop:
  Microphone/Audio stream → WakeWordDetector → Trigger callback
"""

import logging
import threading
from typing import Optional, Callable

import numpy as np

from app.voice.wakeword.detector import WakeWordDetector
from app.voice.wakeword.listner import WakeWordListener
from app.voice.wakeword.state import AssistantState

logger = logging.getLogger(__name__)


class WakeWordEngine:
    """
    Continuously listens for a wake word and triggers a callback when detected.

    Usage:
        engine = WakeWordEngine(on_detected=lambda: print("Wake word!"))
        engine.start()
        # ... later ...
        engine.stop()
    """

    def __init__(
        self,
        wake_words: Optional[list] = None,
        on_detected: Optional[Callable] = None,
        threshold: float = 0.5,
    ):
        self.state = AssistantState.SLEEPING
        self.on_detected = on_detected
        self._detector = WakeWordDetector(wake_words=wake_words, threshold=threshold)
        self._listener = WakeWordListener()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the wake word detection loop in a background thread."""
        if self._running:
            logger.warning("[WakeWordEngine] Already running.")
            return

        if not self._detector.is_ready:
            logger.error("[WakeWordEngine] No detector backend available. Cannot start.")
            return

        self._running = True
        self.state = AssistantState.LISTENING
        self._thread = threading.Thread(
            target=self._run_loop,
            name="wakeword_engine",
            daemon=True,
        )
        self._thread.start()
        logger.info("[WakeWordEngine] Listening for wake word...")

    def stop(self) -> None:
        """Stop the detection loop."""
        self._running = False
        self.state = AssistantState.SLEEPING
        logger.info("[WakeWordEngine] Stopped.")

    def wait_for_wakeword(self) -> str:
        """
        Blocking call: waits until a wake word is detected, then returns its name.
        Used for one-shot detection flows.
        """
        logger.info("[WakeWordEngine] Waiting for wake word (blocking)...")
        self.state = AssistantState.LISTENING

        while True:
            chunk = self._listener.next_chunk()
            if chunk is None:
                continue

            detected, name, score = self._detector.detect(chunk)
            if detected:
                logger.info(f"[WakeWordEngine] '{name}' detected (score={score:.2f})")
                self.state = AssistantState.THINKING
                return name

    def _run_loop(self) -> None:
        """Internal detection loop running in background thread."""
        while self._running:
            try:
                chunk = self._listener.next_chunk()
                if chunk is None:
                    continue

                detected, name, score = self._detector.detect(chunk)
                if detected:
                    logger.info(
                        f"[WakeWordEngine] '{name}' detected (score={score:.2f})"
                    )
                    self.state = AssistantState.THINKING

                    if self.on_detected:
                        try:
                            self.on_detected(name)
                        except Exception as e:
                            logger.error(f"[WakeWordEngine] on_detected callback error: {e}")

            except Exception as e:
                logger.error(f"[WakeWordEngine] Loop error: {e}")
