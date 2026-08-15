from __future__ import annotations

from abc import ABC, abstractmethod
import logging
import numpy as np
from typing import Any

logger = logging.getLogger(__name__)


class AudioSubscriber(ABC):
    @abstractmethod
    def receive(self, audio_chunk: np.ndarray) -> None:
        raise NotImplementedError


class CounterSubscriber(AudioSubscriber):
    def __init__(self) -> None:
        self.count = 0

    def receive(self, chunk: Any) -> None:
        self.count += 1
        if self.count % 100 == 0:
            logger.info("Processed %d audio chunks", self.count)


class PrintSubscriber(AudioSubscriber):
    """Debug subscriber that logs the shape/size of each received chunk."""

    def receive(self, chunk: Any) -> None:
        try:
            size = len(chunk)
        except TypeError:
            size = "?"
        logger.debug("PrintSubscriber received chunk of size %s", size)
