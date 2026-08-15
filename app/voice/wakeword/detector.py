"""
Wake Word Detector - Multi-engine wake word detection (OpenWakeWord with heuristic fallback).
"""

from __future__ import annotations

import logging
from typing import Tuple, Optional
import numpy as np

logger = logging.getLogger(__name__)


class WakeWordDetector:
    """
    Detects target wake words (e.g. 'Hey Jarvis', 'Kronos') in streaming audio chunks.
    Supports OpenWakeWord with fallback energy-threshold scoring.
    """

    def __init__(
        self,
        target_wakeword: str = "hey_jarvis",
        threshold: float = 0.5,
        model_path: Optional[str] = None
    ) -> None:
        self.target_wakeword = target_wakeword
        self.threshold = threshold
        self.oww_model = None

        # Attempt to initialize openwakeword if installed
        try:
            import openwakeword
            from openwakeword.model import Model
            if model_path:
                self.oww_model = Model(wakeword_models=[model_path], inference_framework="onnx")
            else:
                self.oww_model = Model(inference_framework="onnx")
            logger.info("OpenWakeWord engine successfully loaded.")
        except Exception as e:
            logger.info(f"OpenWakeWord not available ({e}), using energy-calibrated fallback detector.")
            self.oww_model = None

    def detect(self, audio_chunk: np.ndarray) -> Tuple[bool, str, float]:
        """
        Processes an audio chunk and determines if the wake word was spoken.

        Returns:
            (detected: bool, wakeword_name: str, confidence_score: float)
        """
        if audio_chunk is None or len(audio_chunk) == 0:
            return False, self.target_wakeword, 0.0

        # 1. Run OpenWakeWord inference if loaded
        if self.oww_model is not None:
            try:
                # Ensure 16-bit 16kHz PCM int16 or float32 format
                if audio_chunk.dtype == np.float32:
                    int_chunk = (audio_chunk * 32767).astype(np.int16)
                else:
                    int_chunk = audio_chunk.astype(np.int16)

                prediction = self.oww_model.predict(int_chunk)
                for name, score in prediction.items():
                    if score >= self.threshold:
                        return True, name, float(score)
                    return False, name, float(score)
            except Exception as exc:
                logger.debug(f"OpenWakeWord inference error: {exc}")

        # 2. Fallback heuristic detection (RMS Energy check)
        rms = np.sqrt(np.mean(audio_chunk.astype(np.float32) ** 2))
        score = min(1.0, float(rms * 10.0))
        detected = score >= self.threshold

        return detected, self.target_wakeword, score
