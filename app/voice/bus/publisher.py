from __future__ import annotations

from typing import Dict
import logging

from app.voice.bus.registry import SubscriberRegistry
from app.voice.bus.subscriber import AudioSubscriber
from app.voice.bus.worker import AudioWorker

logger = logging.getLogger(__name__)


class AudioPublisher:
    def __init__(self) -> None:
        self.registry = SubscriberRegistry()

    def register(self, name: str, worker: AudioWorker) -> None:
        self.registry.add(name, worker)
        logger.debug("Registered worker for subscriber '%s'", name)

    def unregister(self, name: str) -> None:
        self.registry.remove(name)
        logger.debug("Unregistered worker for subscriber '%s'", name)

    def publish(self, chunk: object) -> None:
        for worker in self.registry.values():
            worker.submit(chunk)

    def list_workers(self) -> Dict[str, AudioWorker]:
        return self.registry.all()
















# from voice.bus.registry import SubscriberRegistry
# from voice.bus.worker import AudioWorker



# # class AudioPublisher

#     def __init__(self):

#         self._subscribers: List[AudioSubscriber] = []
#         self.registry  = SubscriberRegistry()
    
#     def subscribe(self, subscriber: AudioSubscriber):

#         if subscriber not in self._subscribers:
#             self._subscribers.append(subscriber)

#     def unsubscribe(self, subscriber: AudioSubscriber):

#         if subscriber in self._subscribers:
#             self._subscribers.remove(subscriber)

#     def publish(self, audio_chunk: np.ndarray):

#         for subscribe in self._subscribers:
#             subscribe.receive(audio_chunk)
                  
