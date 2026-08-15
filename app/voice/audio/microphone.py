from __future__ import annotations

from queue import Full, Queue
from threading import RLock
from typing import Optional

import sounddevice as sd

from app.voice.audio.config import AudioConfig
from app.voice.bus.publisher import AudioPublisher
import logging
import numpy as np

logger = logging.getLogger(__name__)


class Microphone:
    def __init__(
        self,
        config: AudioConfig,
        publisher: AudioPublisher,
    ) -> None:
        self.config = config
        self.publisher = publisher
        self.audio_queue: Queue[np.ndarray] = Queue(maxsize=self.config.queue_size)
        self.stream: Optional[sd.InputStream] = None
        self._lock = RLock()
        self.is_running = False

    def callback(self, indata: np.ndarray, frames: int, time, status) -> None:
        if status:
            logger.warning("Microphone stream status: %s", status)

        audio_chunk = indata.copy()
        self.publisher.publish(audio_chunk)

        try:
            self.audio_queue.put_nowait(audio_chunk)
        except Full:
            try:
                self.audio_queue.get_nowait()
            except Exception:
                logger.debug("Microphone queue flush failed", exc_info=True)
            try:
                self.audio_queue.put_nowait(audio_chunk)
            except Full:
                logger.warning("Microphone queue full, dropping audio chunk")

    def start(self) -> None:
        with self._lock:
            if self.stream is not None:
                return

            self.stream = sd.InputStream(
                samplerate=self.config.sample_rate,
                channels=self.config.channels,
                dtype=self.config.dtype,
                blocksize=self.config.block_size,
                callback=self.callback,
            )
            self.stream.start()
            self.is_running = True
            logger.info("Microphone started")

    def stop(self) -> None:
        with self._lock:
            if self.stream is None:
                return

            self.stream.stop()
            self.stream.close()
            self.stream = None
            self.is_running = False
            logger.info("Microphone stopped")

    def get_audio(self, timeout: Optional[float] = None) -> np.ndarray:
        return self.audio_queue.get(timeout=timeout)

