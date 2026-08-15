from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import wave
from typing import List, Optional

import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class Recorder:
    output_directory: Path = Path("recordings")

    def __post_init__(self) -> None:
        self.output_directory.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        audio_chunks: List[np.ndarray],
        sample_rate: int,
        filename: Optional[str] = None,
    ) -> Path:
        if not audio_chunks:
            raise ValueError("No audio chunks provided")

        if filename is None:
            timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
            filename = f"speech_{timestamp}.wav"

        filepath = self.output_directory / filename
        audio = np.concatenate(audio_chunks, axis=0)
        audio = np.clip(audio, -1.0, 1.0)
        audio = (audio * 32767).astype(np.int16)

        with wave.open(str(filepath), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio.tobytes())

        logger.info("Saved audio recording: %s", filepath)
        return filepath

