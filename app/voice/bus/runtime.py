"""
Audio Bus Runtime
Coordinates audio subscribers, isolated worker threads, and event dispatching.
Ensures non-blocking streaming audio between Microphone/Robot/Telephony and subscribers
(VAD, WakeWord, STT, Network Bridges) without dropping audio frames.
"""

import logging
from typing import Dict, List, Optional
import numpy as np

try:
    from app.voice.bus.exceptions import SubscriberAlreadyExists, SubscriberNotFound
    from app.voice.bus.registry import SubscriberRegistry
    from app.voice.bus.subscriber import AudioSubscriber
    from app.voice.bus.worker import AudioWorker
except ImportError:
    from .exceptions import SubscriberAlreadyExists, SubscriberNotFound
    from .registry import SubscriberRegistry
    from .subscriber import AudioSubscriber
    from .worker import AudioWorker

logger = logging.getLogger(__name__)


class AudioBusRuntime:
    """
    Central runtime coordinator for the decoupled audio bus.
    Each subscriber receives its own background AudioWorker thread
    so that heavy ML processing (VAD, Whisper STT, WakeWord) never
    blocks the raw audio ingestion stream.
    """

    def __init__(self):
        self.registry = SubscriberRegistry()
        self._workers: Dict[str, AudioWorker] = {}
        self._is_running: bool = False

    @property
    def is_running(self) -> bool:
        return self._is_running

    def register(
        self,
        name: str,
        subscriber: AudioSubscriber,
        queue_size: int = 100
    ) -> AudioWorker:
        """
        Register a subscriber with its own dedicated worker thread.
        """
        if name in self._workers:
            raise SubscriberAlreadyExists(f"Subscriber '{name}' is already registered.")

        worker = AudioWorker(subscriber=subscriber, queue_size=queue_size)
        self._workers[name] = worker
        self.registry.add(name, worker)

        # If runtime is already active, start this worker immediately
        if self._is_running:
            worker.start()

        logger.info(f"Registered audio subscriber '{name}' with queue_size={queue_size}.")
        return worker

    def unregister(self, name: str) -> None:
        """
        Gracefully stop worker thread and unregister subscriber.
        """
        if name not in self._workers:
            raise SubscriberNotFound(f"Subscriber '{name}' not found.")

        worker = self._workers[name]
        worker.stop()
        self.registry.remove(name)
        del self._workers[name]
        logger.info(f"Unregistered audio subscriber '{name}'.")

    def start(self) -> None:
        """
        Start all worker threads in the registry.
        """
        self._is_running = True
        for name, worker in self._workers.items():
            if not worker.is_alive():
                worker.start()
        logger.info(f"AudioBusRuntime started with {len(self._workers)} active worker(s).")

    def stop(self) -> None:
        """
        Gracefully stop all worker threads.
        """
        self._is_running = False
        for name, worker in self._workers.items():
            worker.stop()
        logger.info("AudioBusRuntime stopped all workers.")

    def dispatch(self, audio_chunk: np.ndarray) -> None:
        """
        Submit incoming audio chunk to every registered subscriber's worker queue.
        Non-blocking: if a worker's queue is full, the oldest chunk is discarded.
        """
        for worker in self.registry.values():
            worker.submit(audio_chunk)

    def list_subscribers(self) -> List[str]:
        """
        Return list of active subscriber names.
        """
        return list(self.registry.names())
