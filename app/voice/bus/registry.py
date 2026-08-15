from __future__ import annotations

from typing import Dict, Optional

from app.voice.bus.exceptions import SubscriberAlreadyExists, SubscriberNotFound


class SubscriberRegistry:
    def __init__(self) -> None:
        self._subscribers: Dict[str, object] = {}

    def add(self, name: str, worker: object) -> None:
        if name in self._subscribers:
            raise SubscriberAlreadyExists(name)
        self._subscribers[name] = worker

    def remove(self, name: str) -> None:
        if name not in self._subscribers:
            raise SubscriberNotFound(name)
        del self._subscribers[name]

    def get(self, name: str) -> Optional[object]:
        return self._subscribers.get(name)

    def exists(self, name: str) -> bool:
        return name in self._subscribers

    def values(self):
        return self._subscribers.values()

    def names(self):
        return self._subscribers.keys()

    def all(self) -> Dict[str, object]:
        return dict(self._subscribers)
        