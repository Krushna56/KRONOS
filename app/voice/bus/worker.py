from __future__ import annotations

from queue import Empty, Queue
from threading import Event, Thread
from typing import Any
import logging

from app.voice.bus.subscriber import AudioSubscriber

logger = logging.getLogger(__name__)


class AudioWorker(Thread):
    def __init__(self, subscriber: AudioSubscriber, queue_size: int = 100) -> None:
        super().__init__(daemon=True)
        self.subscriber = subscriber
        self.queue: Queue[Any] = Queue(maxsize=queue_size)
        self._stop_event = Event()

    def submit(self, audio_chunk: Any) -> None:
        if self.queue.full():
            try:
                self.queue.get_nowait()
            except Empty:
                logger.debug("Worker queue was full and could not be trimmed")
        self.queue.put_nowait(audio_chunk)

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        while not self._stop_event.is_set():
            try:
                chunk = self.queue.get(timeout=0.2)
            except Empty:
                continue

            try:
                self.subscriber.receive(chunk)
            except Exception:
                logger.exception(
                    "Subscriber crashed: %s",
                    self.subscriber.__class__.__name__,
                )


