from __future__ import annotations

import logging
from typing import Dict, Optional

from app.voice.bus.publisher import AudioPublisher
from app.voice.bus.registry import SubscriberRegistry
from app.voice.bus.subscriber import AudioSubscriber
from app.voice.bus.worker import AudioWorker

logger = logging.getLogger(__name__)


class BusManager:
    def __init__(self, queue_size: int = 100) -> None:
        self.publisher = AudioPublisher()
        self.registry = SubscriberRegistry()
        self.queue_size = queue_size

    def register_subscriber(self, name: str, subscriber: AudioSubscriber) -> None:
        if self.registry.exists(name):
            logger.warning("Subscriber already exists: %s", name)
            return

        worker = AudioWorker(subscriber, queue_size=self.queue_size)
        worker.start()
        self.registry.add(name, worker)
        self.publisher.register(name, worker)
        logger.info("Registered subscriber: %s", name)

    def unregister_subscriber(self, name: str) -> None:
        worker = self.registry.get(name)
        if worker is None:
            logger.warning("Subscriber not found: %s", name)
            return

        worker.stop()
        self.registry.remove(name)
        self.publisher.unregister(name)
        logger.info("Unregistered subscriber: %s", name)

    def publish(self, audio_chunk: object) -> None:
        self.publisher.publish(audio_chunk)

    def list_workers(self) -> Dict[str, AudioWorker]:
        return self.registry.all()

    def stop_all(self) -> None:
        for worker in self.registry.all().values():
            worker.stop()
        logger.info("Stopped all workers")

