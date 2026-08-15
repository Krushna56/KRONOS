from __future__ import annotations

import logging
from typing import Optional

import numpy as np

from app.voice.audio.buffer import AudioBuffer
from app.voice.audio.config import AudioConfig
from app.voice.audio.microphone import Microphone
from app.voice.bus.bus_manager import BusManager
from app.voice.bus.subscriber import AudioSubscriber

logger = logging.getLogger(__name__)


class AudioManager:
    def __init__(
        self,
        config: Optional[AudioConfig] = None,
        bus_manager: Optional[BusManager] = None,
    ) -> None:
        self.config = config or AudioConfig()
        self.bus_manager = bus_manager or BusManager(queue_size=self.config.queue_size)
        self.publisher = self.bus_manager.publisher
        self.microphone = Microphone(self.config, self.publisher)
        self.buffer = AudioBuffer(max_chunks=self.config.queue_size)
        self.is_running = False

    def start(self) -> None:
        if self.is_running:
            return
        self.microphone.start()
        self.is_running = True
        logger.info("Audio manager started")

    def stop(self) -> None:
        if not self.is_running:
            return
        self.microphone.stop()
        self.bus_manager.stop_all()
        self.is_running = False
        logger.info("Audio manager stopped")

    def subscribe(self, name: str, subscriber: AudioSubscriber) -> None:
        self.bus_manager.register_subscriber(name, subscriber)

    def unsubscribe(self, name: str) -> None:
        self.bus_manager.unregister_subscriber(name)

    def read(self, timeout: Optional[float] = None) -> np.ndarray:
        return self.microphone.get_audio(timeout=timeout)
    