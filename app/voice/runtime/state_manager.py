from __future__ import annotations

from enum import Enum
from threading import Lock
from typing import Optional


class AssistantState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"


class StateManager:
    """Thread-safe state machine for voice assistant."""

    def __init__(self) -> None:
        self._state = AssistantState.IDLE
        self._lock = Lock()

    def get_state(self) -> AssistantState:
        with self._lock:
            return self._state

    def set_state(self, new_state: AssistantState) -> None:
        with self._lock:
            self._state = new_state

    def transition(self, new_state: AssistantState) -> AssistantState:
        with self._lock:
            self._state = new_state
            return self._state

    def reset(self) -> None:
        with self._lock:
            self._state = AssistantState.IDLE
