from __future__ import annotations

import logging
import numpy as np
from app.voice.audio.config import AudioConfig

logger = logging.getLogger(__name__)


class VADEngine:
    def __init__(self) -> None:
        self.config = AudioConfig()
        self.model = None

        try:
            import torch
            from silero_vad import load_silero_vad
            logger.info("Loading Silero VAD model...")
            self.model = load_silero_vad()
            self._torch = torch
            logger.info("Silero VAD model loaded successfully.")
        except Exception as e:
            logger.info(f"Silero VAD model unavailable ({e}), using energy-based VAD fallback.")
            self.model = None

    def get_speech_probability(self, audio_chunk: np.ndarray) -> float:
        """Microphone returns (512,1) or (512,); expects mono."""
        if audio_chunk is None or len(audio_chunk) == 0:
            return 0.0

        audio = audio_chunk.squeeze().astype(np.float32, copy=False)

        # 1. Use Silero VAD neural network if loaded
        if self.model is not None:
            try:
                tensor = self._torch.from_numpy(audio)
                with self._torch.no_grad():
                    probability = self.model(
                        tensor,
                        self.config.sample_rate
                    ).item()
                    return float(probability)
            except Exception as exc:
                logger.debug(f"Silero VAD execution error: {exc}")

        # 2. Energy-based fallback estimation
        rms = np.sqrt(np.mean(audio ** 2))
        probability = min(1.0, float(rms * 15.0))
        return probability

    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        probability = self.get_speech_probability(audio_chunk)
        return probability >= self.config.speech_threshold
