from __future__ import annotations

from typing import Optional

from .voice_runtime import VoiceRuntime


class LifecycleManager:
    def __init__(self, runtime: VoiceRuntime) -> None:
        self.runtime = runtime

    def start(self) -> None:
        self.runtime.start()

    def stop(self) -> None:
        self.runtime.stop()

    async def shutdown(self) -> None:
        self.runtime.stop()

    def status(self) -> Optional[str]:
        return getattr(self.runtime, "status", None)
