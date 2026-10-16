import logging
import numpy as np
from app.voice.config import AudioConfig

logger = logging.getLogger(__name__)

# Attempt to load Silero VAD, or gracefully fall back to Energy VAD
_SILERO_AVAILABLE = False
try:
    import torch
    from silero_vad import load_silero_vad
    _SILERO_AVAILABLE = True
except Exception as e:
    logger.warning(f"[VAD] Silero VAD / PyTorch unavailable ({e}). Using robust Energy-based VAD.")


class VADEngine:
    def __init__(self):
        self.config = AudioConfig()
        self.use_silero = False
        self.model = None

        if _SILERO_AVAILABLE:
            try:
                logger.info("[VAD] Loading Silero VAD model...")
                self.model = load_silero_vad()
                self.use_silero = True
                logger.info("[VAD] Silero VAD loaded successfully.")
            except Exception as e:
                logger.warning(f"[VAD] Failed to initialize Silero VAD ({e}), falling back to Energy VAD.")
                self.use_silero = False
        else:
            logger.info("[VAD] Initialized high-performance Energy-based VAD.")

    def get_speech_probability(self, audio_chunk: np.ndarray) -> float:
        """Calculate speech probability using Silero or RMS energy."""
        audio = audio_chunk.squeeze()
        audio = audio.astype(np.float32, copy=False)

        if self.use_silero and self.model is not None:
            try:
                tensor = torch.from_numpy(audio)
                with torch.no_grad():
                    prob = self.model(tensor, self.config.sample_rate).item()
                    return float(prob)
            except Exception:
                pass

        # Energy / RMS-based fallback
        # Normalize RMS between 0.0 and 1.0 (typical speech RMS is > 0.01 to 0.05)
        rms = np.sqrt(np.mean(audio ** 2)) if audio.size > 0 else 0.0
        # Map rms to 0..1 probability with threshold around 0.015
        prob = min(1.0, float(rms / 0.03))
        return prob

    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        probability = self.get_speech_probability(audio_chunk)
        return probability >= self.config.speech_threshold
