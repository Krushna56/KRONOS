"""
Wake Word Detector
Detects wake words in real-time audio using openwakeword or a
keyword-energy fallback when openwakeword is not available.

Primary model: openwakeword (hey_jarvis / alexa / custom ONNX model)
Fallback:      Simple keyword-energy-based detection using speech_recognition
"""

import logging
import numpy as np
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# ── openwakeword lazy import ────────────────────────────────────────────────
_OWW_AVAILABLE = False
try:
    from openwakeword.model import Model as OWWModel
    _OWW_AVAILABLE = True
    logger.info("[WakeWordDetector] openwakeword available.")
except ImportError:
    logger.warning(
        "[WakeWordDetector] 'openwakeword' not installed — "
        "using energy-based keyword fallback.\n"
        "Install: pip install openwakeword"
    )

# ── speech_recognition for keyword fallback ─────────────────────────────────
_SR_AVAILABLE = False
try:
    import speech_recognition as sr
    _SR_AVAILABLE = True
except ImportError:
    pass


class WakeWordDetector:
    """
    Detects wake words in audio chunks.

    Supports two backends:
    1. openwakeword — production-grade, ONNX-based wake word detection.
       Detects built-in models: 'hey_jarvis', 'alexa', 'hey_mycroft', etc.
    2. Keyword energy fallback — uses Google STT on short chunks to check
       for the keyword in transcribed text.

    Usage:
        detector = WakeWordDetector(wake_words=["hey jarvis", "kronos"])
        detected, name, score = detector.detect(audio_chunk_float32)
        if detected:
            print(f"Wake word '{name}' detected with score {score:.2f}")
    """

    # openwakeword built-in model names to try (in preference order)
    OWW_MODEL_NAMES = ["hey_jarvis", "alexa", "hey_mycroft"]

    def __init__(
        self,
        wake_words: Optional[list] = None,
        threshold: float = 0.5,
        sample_rate: int = 16000,
    ):
        """
        Args:
            wake_words:   List of keyword strings for the fallback detector.
                          For openwakeword, the built-in model vocabulary is used.
            threshold:    Confidence threshold (0.0–1.0) for triggering detection.
            sample_rate:  Audio sample rate in Hz.
        """
        self.wake_words = [w.lower() for w in (wake_words or ["hey jarvis", "kronos"])]
        self.threshold = threshold
        self.sample_rate = sample_rate

        self._oww_model = None
        self._recognizer = None

        self._init_backend()

    def _init_backend(self) -> None:
        """Initialize the best available detection backend."""
        if _OWW_AVAILABLE:
            try:
                # Load openwakeword with default built-in models
                self._oww_model = OWWModel(
                    wakeword_models=self.OWW_MODEL_NAMES,
                    inference_framework="onnx",
                )
                logger.info(
                    f"[WakeWordDetector] openwakeword models loaded: "
                    f"{list(self._oww_model.models.keys())}"
                )
                return
            except Exception as e:
                logger.warning(
                    f"[WakeWordDetector] openwakeword model init failed: {e}. "
                    "Falling back to keyword energy detector."
                )

        # Fallback: speech_recognition keyword energy
        if _SR_AVAILABLE:
            self._recognizer = sr.Recognizer()
            self._recognizer.energy_threshold = 300
            self._recognizer.dynamic_energy_threshold = False
            logger.info(
                "[WakeWordDetector] Using keyword energy fallback "
                f"for wake words: {self.wake_words}"
            )
        else:
            logger.error(
                "[WakeWordDetector] No detection backend available. "
                "Install openwakeword or speech_recognition."
            )

    def detect(self, audio_chunk: np.ndarray) -> Tuple[bool, str, float]:
        """
        Run wake word detection on an audio chunk.

        Args:
            audio_chunk: float32 numpy array of audio samples at self.sample_rate.

        Returns:
            (detected, wake_word_name, confidence_score)
            - detected:         True if a wake word was found above threshold.
            - wake_word_name:   Name of the detected model/word, or "" if not detected.
            - confidence_score: Float 0.0–1.0 confidence.
        """
        if self._oww_model is not None:
            return self._detect_oww(audio_chunk)

        if self._recognizer is not None:
            return self._detect_keyword_energy(audio_chunk)

        return False, "", 0.0

    def _detect_oww(self, audio_chunk: np.ndarray) -> Tuple[bool, str, float]:
        """openwakeword-based detection."""
        try:
            audio = audio_chunk.squeeze().astype(np.float32)

            # openwakeword expects float32 audio
            prediction = self._oww_model.predict(audio)

            best_name = ""
            best_score = 0.0

            for model_name, score in prediction.items():
                score_val = float(score)
                if score_val > best_score:
                    best_score = score_val
                    best_name = model_name

            if best_score >= self.threshold:
                logger.info(
                    f"[WakeWordDetector] '{best_name}' detected "
                    f"(score={best_score:.3f})"
                )
                return True, best_name, best_score

        except Exception as e:
            logger.debug(f"[WakeWordDetector] OWW prediction error: {e}")

        return False, "", 0.0

    def _detect_keyword_energy(self, audio_chunk: np.ndarray) -> Tuple[bool, str, float]:
        """
        Keyword energy fallback: convert chunk to PCM, run Google STT,
        check if any wake word appears in the transcript.
        """
        try:
            # Convert float32 → 16-bit PCM bytes
            audio = audio_chunk.squeeze()
            clipped = np.clip(audio, -1.0, 1.0)
            pcm_bytes = (clipped * 32767).astype(np.int16).tobytes()

            audio_data = sr.AudioData(pcm_bytes, self.sample_rate, 2)
            try:
                text = self._recognizer.recognize_google(audio_data, language="en-IN").lower()
            except (sr.UnknownValueError, sr.RequestError):
                return False, "", 0.0

            for word in self.wake_words:
                if word in text:
                    logger.info(
                        f"[WakeWordDetector] Keyword '{word}' found in transcript: '{text}'"
                    )
                    return True, word, 1.0  # Binary detection

        except Exception as e:
            logger.debug(f"[WakeWordDetector] Keyword fallback error: {e}")

        return False, "", 0.0

    @property
    def is_ready(self) -> bool:
        """True if any backend is available."""
        return self._oww_model is not None or self._recognizer is not None
