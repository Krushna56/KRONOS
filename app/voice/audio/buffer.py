from __future__ import annotations

from collections import deque
from threading import Lock
from typing import Deque, List

import numpy as np


class AudioBuffer:
    """Thread-safe reusable audio buffer."""

    def __init__(self, max_chunks: int = 1000) -> None:
        self._chunks: Deque[np.ndarray] = deque(maxlen=max_chunks)
        self._lock = Lock()
        self._max_chunks = max_chunks

    def append(self, chunk: np.ndarray) -> None:
        with self._lock:
            self._chunks.append(chunk.copy())

    def reset(self) -> None:
        with self._lock:
            self._chunks.clear()

    def get_all(self) -> List[np.ndarray]:
        with self._lock:
            return list(self._chunks)

    def duration(self, sample_rate: int) -> float:
        with self._lock:
            total_frames = sum(chunk.shape[0] for chunk in self._chunks)
        return float(total_frames) / float(sample_rate) if sample_rate else 0.0

    def __len__(self) -> int:
        with self._lock:
            return len(self._chunks)

    @property
    def max_size(self) -> int:
        return self._max_chunks

