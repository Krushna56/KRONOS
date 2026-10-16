"""
Voice Pipeline
Orchestrates the complete audio perception pipeline:
Microphone / Audio Stream -> AudioBusRuntime -> VAD Worker -> STT Engine -> Transcript Event.
Can receive audio from local microphone, Mini Robot WebSocket, or Telephony Call streams.
"""

import logging
from typing import Callable, List, Optional
import numpy as np
from concurrent.futures import ThreadPoolExecutor

from app.voice.bus.runtime import AudioBusRuntime
from app.voice.vad.subscriber import VADAudioSubscriber
from app.voice.stt.engine import STTEngine, get_stt_engine
from app.voice.microphone import Microphone

logger = logging.getLogger(__name__)


class VoicePipeline:
    """
    End-to-end voice hearing pipeline.
    """

    def __init__(
        self,
        on_transcript: Optional[Callable[[str], None]] = None,
        use_microphone: bool = True
    ):
        self.bus_runtime = AudioBusRuntime()
        self.stt_engine: STTEngine = get_stt_engine()
        self.on_transcript = on_transcript
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="VoiceSTT")

        # 1. Create VAD subscriber connected to our speech handler
        self.vad_subscriber = VADAudioSubscriber(
            on_speech_detected=self._handle_speech_detected
        )

        # 2. Register VAD into the non-blocking audio bus
        self.bus_runtime.register("vad_detector", self.vad_subscriber, queue_size=120)

        # 3. Optional local microphone
        self.mic: Optional[Microphone] = None
        if use_microphone:
            try:
                self.mic = Microphone()
                # Hook microphone audio chunks directly into our AudioBusRuntime
                self.mic.publisher.subscribe(self._AudioChunkBridge(self.bus_runtime))
            except Exception as e:
                logger.warning(f"Local microphone not initialized: {e}")

        self._is_running = False

    class _AudioChunkBridge:
        def __init__(self, runtime: AudioBusRuntime):
            self.runtime = runtime

        def receive(self, audio_chunk: np.ndarray) -> None:
            self.runtime.dispatch(audio_chunk)

    def _handle_speech_detected(self, audio_chunks: List[np.ndarray]) -> None:
        """
        Called by VAD worker thread when an utterance completes.
        Offloads STT transcription to thread pool so VAD keeps listening.
        """
        self.executor.submit(self._run_transcription, audio_chunks)

    def _run_transcription(self, audio_chunks: List[np.ndarray]) -> None:
        try:
            transcript = self.stt_engine.transcribe(audio_chunks)
            if transcript and transcript.strip():
                logger.info(f"🗣️ [VoicePipeline] Transcribed: \"{transcript.strip()}\"")
                if self.on_transcript:
                    self.on_transcript(transcript.strip())
        except Exception:
            logger.exception("Error in VoicePipeline transcription worker")

    def feed_audio(self, audio_chunk: np.ndarray) -> None:
        """
        Feed audio from external sources (Mini Robot WebSocket stream or Telephony stream).
        """
        self.bus_runtime.dispatch(audio_chunk)

    def start(self) -> None:
        """Start the audio bus runtime and microphone."""
        self._is_running = True
        self.bus_runtime.start()
        if self.mic:
            try:
                self.mic.start()
                logger.info("🎤 Local microphone listening started.")
            except Exception as e:
                logger.error(f"Failed to start local microphone: {e}")
        logger.info("⚡ VoicePipeline active.")

    def stop(self) -> None:
        """Stop microphone, bus runtime, and executor."""
        self._is_running = False
        if self.mic:
            try:
                self.mic.stop()
            except Exception:
                pass
        self.bus_runtime.stop()
        self.executor.shutdown(wait=False)
        logger.info("🛑 VoicePipeline stopped.")
