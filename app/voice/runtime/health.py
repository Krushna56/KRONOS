from __future__ import annotations

from threading import Lock
from typing import Dict

from app.voice.audio.microphone import Microphone
from app.voice.bus.bus_manager import BusManager
from app.voice.runtime.voice_runtime import VoiceRuntime


class HealthMonitor:
    def __init__(
        self,
        microphone: Microphone,
        bus_manager: BusManager,
        runtime: VoiceRuntime,
    ) -> None:
        self._lock = Lock()
        self.microphone = microphone
        self.bus_manager = bus_manager
        self.runtime = runtime

    def check_microphone(self) -> bool:
        return self.microphone.is_running

    def check_workers(self) -> Dict[str, bool]:
        return {
            name: worker.is_alive()
            for name, worker in self.bus_manager.list_workers().items()
        }

    def check_runtime(self) -> bool:
        return getattr(self.runtime, "is_running", False)

    def status(self) -> Dict[str, object]:
        with self._lock:
            return {
                "microphone": self.check_microphone(),
                "workers": self.check_workers(),
                "runtime": self.check_runtime(),
            }

    def restart(self) -> None:
        self.runtime.stop()
        self.runtime.start()
