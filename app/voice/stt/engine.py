"""
Speech-To-Text (STT) Engine
Transcribes captured speech audio into text.
Supports:
1. Google Speech Recognition (free, built-in, supports Hinglish/Hindi/English)
2. Groq Whisper API (ultra-low latency ~200ms when configured)
3. Local Whisper / fallback
"""

import io
import os
import wave
import logging
from typing import List, Optional
import numpy as np
try:
    import speech_recognition as sr
    _SR_AVAILABLE = True
except Exception as e:
    _SR_AVAILABLE = False
    sr = None

logger = logging.getLogger(__name__)


class STTEngine:
    """
    Robust Speech-to-Text transcriber that converts numpy audio buffers
    into text transcripts with multi-engine fallback.
    """

    def __init__(self, sample_rate: int = 16000, default_language: str = "en-IN"):
        self.sample_rate = sample_rate
        self.default_language = default_language
        self.recognizer = sr.Recognizer() if _SR_AVAILABLE else None
        if self.recognizer:
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = False

    def chunks_to_pcm(self, chunks: List[np.ndarray]) -> bytes:
        """
        Concatenate float32 numpy audio chunks and convert to 16-bit PCM bytes.
        """
        if not chunks:
            return b""
        concatenated = np.concatenate(chunks)
        # Squeeze mono channel if needed (N, 1) -> (N,)
        if concatenated.ndim > 1:
            concatenated = concatenated.squeeze()
        # Clip values to [-1.0, 1.0] and scale to 16-bit signed integer
        clipped = np.clip(concatenated, -1.0, 1.0)
        pcm_data = (clipped * 32767).astype(np.int16).tobytes()
        return pcm_data

    def transcribe(
        self,
        audio_chunks: List[np.ndarray],
        language: Optional[str] = None
    ) -> Optional[str]:
        """
        Transcribe a list of audio chunks into text.
        """
        lang = language or self.default_language
        pcm_bytes = self.chunks_to_pcm(audio_chunks)
        if not pcm_bytes:
            return None

        # Build SpeechRecognition AudioData
        audio_data = sr.AudioData(
            pcm_bytes,
            sample_rate=self.sample_rate,
            sample_width=2  # 16-bit = 2 bytes per sample
        )

        # 1. Try Groq Whisper if API key is present
        groq_api_key = os.getenv("GROQ_API_KEY")
        if groq_api_key:
            try:
                transcript = self._transcribe_groq(pcm_bytes, groq_api_key)
                if transcript and transcript.strip():
                    logger.info(f"[STT:Groq] Transcribed: '{transcript.strip()}'")
                    return transcript.strip()
            except Exception as e:
                logger.warning(f"[STT:Groq] Failed, falling back to Google: {e}")

        # 2. Try Google Speech Recognition (free, supports en-IN & hi-IN)
        try:
            transcript = self.recognizer.recognize_google(audio_data, language=lang)
            logger.info(f"[STT:Google] Transcribed: '{transcript}'")
            return transcript
        except sr.UnknownValueError:
            logger.debug("[STT:Google] Speech unintelligible / silence")
            return None
        except sr.RequestError as e:
            logger.error(f"[STT:Google] API request failed: {e}")
            return None
        except Exception as e:
            logger.exception(f"[STT] Unexpected error during transcription: {e}")
            return None

    def _transcribe_groq(self, pcm_bytes: bytes, api_key: str) -> Optional[str]:
        """
        Fast Whisper transcription via Groq API.
        """
        import httpx

        # Pack raw PCM into in-memory WAV buffer
        wav_io = io.BytesIO()
        with wave.open(wav_io, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(pcm_bytes)
        wav_io.seek(0)

        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {api_key}"}
        files = {"file": ("audio.wav", wav_io, "audio/wav")}
        data = {"model": "whisper-large-v3", "temperature": "0.0"}

        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, headers=headers, files=files, data=data)
            response.raise_for_status()
            res_json = response.json()
            return res_json.get("text")


# Global singleton instance
_engine: Optional[STTEngine] = None


def get_stt_engine() -> STTEngine:
    global _engine
    if _engine is None:
        _engine = STTEngine()
    return _engine
