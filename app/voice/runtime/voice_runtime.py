from __future__ import annotations

import logging
from threading import Event, Thread
from typing import Optional

from app.voice.audio.audio_manager import AudioManager
from app.voice.audio.config import AudioConfig
from app.voice.audio.recorder import Recorder
from app.voice.audio.buffer import AudioBuffer
from app.voice.runtime.pipeline import (
    Pipeline,
    VADStage,
    SpeechBufferStage,
    RecorderStage,
    WakeWordStage,
)
from app.voice.runtime.state_manager import AssistantState, StateManager
from app.voice.vad.speech_detector import SpeechDetector

logger = logging.getLogger(__name__)


class VoiceRuntime:
    def __init__(
        self,
        config: Optional[AudioConfig] = None,
        audio_manager: Optional[AudioManager] = None,
        state_manager: Optional[StateManager] = None,
        pipeline: Optional[Pipeline] = None,
        recorder: Optional[Recorder] = None,
    ) -> None:
        self.config = config or AudioConfig()
        self.state_manager = state_manager or StateManager()
        self.audio_manager = audio_manager or AudioManager(config=self.config)
        self.recorder = recorder or Recorder()
        self.buffer = AudioBuffer(max_chunks=self.config.queue_size)
        self.pipeline = pipeline or self._default_pipeline()
        self._stop_event = Event()
        self._thread: Optional[Thread] = None
        self.is_running = False

    def _default_pipeline(self) -> Pipeline:
        return Pipeline(
            [
                WakeWordStage(name="WakeWord"),
                VADStage(vad_processor=SpeechDetector()),
                SpeechBufferStage(buffer=self.buffer),
                RecorderStage(recorder=self.recorder, sample_rate=self.config.sample_rate),
            ]
        )

    def start(self) -> None:
        if self.is_running:
            return

        self.audio_manager.start()
        self._stop_event.clear()
        self._thread = Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self.is_running = True
        logger.info("Voice runtime started")

    def stop(self) -> None:
        if not self.is_running:
            return

        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)

        self.audio_manager.stop()
        self.is_running = False
        self.state_manager.reset()
        logger.info("Voice runtime stopped")

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                audio_chunk = self.audio_manager.read(timeout=0.5)
            except Exception as exc:
                logger.debug("Audio read timeout or error: %s", exc)
                continue

            self.state_manager.set_state(AssistantState.LISTENING)
            result = self.pipeline.execute(audio_chunk)

            if result is None:
                continue

            self.state_manager.set_state(AssistantState.PROCESSING)
            logger.info("Pipeline processed audio payload")
            self.state_manager.set_state(AssistantState.IDLE)

    def register_subscriber(self, name: str, subscriber: object) -> None:
        self.audio_manager.subscribe(name, subscriber)

    def unregister_subscriber(self, name: str) -> None:
        self.audio_manager.unsubscribe(name)

    def status(self) -> dict[str, object]:
        return {
            "running": self.is_running,
            "state": self.state_manager.get_state().value,
            "audio": self.audio_manager.is_running,
        }
