"""
Wake Word Listener
Feeds audio chunks from the microphone into the WakeWordDetector.
Uses the existing AudioManager/Microphone infrastructure.
"""

import logging
import queue
import threading
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# Chunk size: 1280 samples at 16kHz = 80ms (openwakeword's expected chunk size)
CHUNK_SAMPLES = 1280
SAMPLE_RATE = 16000


class WakeWordListener:
    """
    Captures audio chunks from the microphone for wake word detection.

    Maintains an internal queue so the detector thread can consume
    chunks at its own pace without blocking the audio capture thread.
    """

    def __init__(self, chunk_samples: int = CHUNK_SAMPLES):
        self.chunk_samples = chunk_samples
        self._queue: queue.Queue = queue.Queue(maxsize=30)
        self._stream = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._init_stream()

    def _init_stream(self) -> None:
        """Open the microphone audio stream via PyAudio."""
        try:
            import pyaudio
            self._pa = pyaudio.PyAudio()
            self._stream = self._pa.open(
                rate=SAMPLE_RATE,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.chunk_samples,
                stream_callback=self._audio_callback,
            )
            self._stream.start_stream()
            logger.info("[WakeWordListener] Microphone stream opened.")
        except ImportError:
            logger.warning(
                "[WakeWordListener] PyAudio not installed — using null audio source. "
                "Run: pip install pyaudio"
            )
            self._stream = None
        except Exception as e:
            logger.warning(f"[WakeWordListener] Could not open microphone: {e}")
            self._stream = None

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """PyAudio callback — converts PCM bytes to float32 and enqueues."""
        import pyaudio
        try:
            audio = (
                np.frombuffer(in_data, dtype=np.int16).astype(np.float32) / 32767.0
            )
            if not self._queue.full():
                self._queue.put_nowait(audio)
        except Exception:
            pass
        return (None, pyaudio.paContinue)

    def next_chunk(self) -> Optional[np.ndarray]:
        """
        Block until the next audio chunk is available from the microphone.

        Returns:
            float32 numpy array of shape (CHUNK_SAMPLES,), or None if unavailable.
        """
        if self._stream is None:
            # No microphone — return silence so detector doesn't block forever
            return np.zeros(self.chunk_samples, dtype=np.float32)

        try:
            return self._queue.get(timeout=1.0)
        except queue.Empty:
            return None

    def close(self) -> None:
        """Release the microphone stream."""
        try:
            if self._stream:
                self._stream.stop_stream()
                self._stream.close()
            if hasattr(self, "_pa"):
                self._pa.terminate()
            logger.info("[WakeWordListener] Microphone stream closed.")
        except Exception as e:
            logger.debug(f"[WakeWordListener] Close error: {e}")


# Backward-compatible alias (old code used WakeWordListner with typo)
WakeWordListner = WakeWordListener