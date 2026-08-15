from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Protocol

import numpy as np


class PipelineStage(Protocol):
    def process(self, payload: Any) -> Any:
        ...


@dataclass
class BaseStage:
    name: str

    def process(self, payload: Any) -> Any:
        return payload


class WakeWordStage(BaseStage):
    def process(self, payload: Any) -> Any:
        return payload


class VADStage(BaseStage):
    def __init__(self, vad_processor: Any) -> None:
        super().__init__(name="VAD")
        self.vad_processor = vad_processor

    def process(self, payload: np.ndarray) -> Any:
        return self.vad_processor.process_chunk(payload)


class SpeechBufferStage(BaseStage):
    def __init__(self, buffer: Any) -> None:
        super().__init__(name="SpeechBuffer")
        self.buffer = buffer

    def process(self, payload: Any) -> Any:
        if isinstance(payload, list):
            for chunk in payload:
                self.buffer.append(chunk)
        elif payload is not None:
            self.buffer.append(payload)
        return payload


class RecorderStage(BaseStage):
    def __init__(self, recorder: Any, sample_rate: int) -> None:
        super().__init__(name="Recorder")
        self.recorder = recorder
        self.sample_rate = sample_rate

    def process(self, payload: Any) -> Any:
        if isinstance(payload, list):
            self.recorder.save(audio_chunks=payload, sample_rate=self.sample_rate)
        return payload


class WhisperStage(BaseStage):
    def process(self, payload: Any) -> Any:
        return payload


class IntentRouterStage(BaseStage):
    def process(self, payload: Any) -> Any:
        return payload


class PersonaStage(BaseStage):
    def process(self, payload: Any) -> Any:
        return payload


class TTSStage(BaseStage):
    def process(self, payload: Any) -> Any:
        return payload


class UIStage(BaseStage):
    def process(self, payload: Any) -> Any:
        return payload


class Pipeline:
    def __init__(self, stages: List[PipelineStage] | None = None) -> None:
        self._stages: List[PipelineStage] = list(stages or [])

    def add_stage(self, stage: PipelineStage) -> None:
        self._stages.append(stage)

    def insert_stage(self, index: int, stage: PipelineStage) -> None:
        self._stages.insert(index, stage)

    def execute(self, payload: Any) -> Any:
        result = payload
        for stage in self._stages:
            if result is None:
                return None
            result = stage.process(result)
        return result

    @property
    def stages(self) -> List[PipelineStage]:
        return list(self._stages)
