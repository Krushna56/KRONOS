from __future__ import annotations

import logging
from typing import Optional

import numpy as np

from app.voice.audio.config import AudioConfig
from app.voice.vad.vad_engine import VADEngine

logger = logging.getLogger(__name__)


class SpeechDetector:
    def __init__(self) -> None:
        self.config = AudioConfig()
        self.vad = VADEngine()
        self.is_recording = False
        self.audio_chunks: list[np.ndarray] = []
        self.silence_counter = 0
        self.speech_chunk_count = 0

    def reset(self):

        self.is_recording = False

        self.audio_chunks = []

        self.silence_counter = 0

        self.speech_chunk_count = 0
    
    def process_chunk(self, audio_chunk: np.ndarray) -> Optional[list[np.ndarray]]:

        speech_probability = (
            self.vad.get_speech_probability(
                audio_chunk
            )
        )

        speech_detected = (
            speech_probability
            >= self.config.speech_threshold
        )

        # state 1: waiting for speech 

        if not self.is_recording:
            if speech_detected:
                logger.info("VAD speech started (prob=%.2f)", speech_probability)
                self.is_recording = True
                self.audio_chunks = [audio_chunk.copy()]
                self.speech_chunk_count = 1
                self.silence_counter = 0
            return None

        # state 2: recording

        self.audio_chunks.append(
            audio_chunk.copy()
        )

        if speech_detected:

            self.speech_chunk_count += 1

            self.silence_counter = 0
    
        else:
            self.silence_counter += 1
        
        # state 3: end of speech 

        if self.silence_counter >= self.config.silence_chunks:
            logger.info("VAD speech ended")
            completed_audio = self.audio_chunks.copy()
            speech_chunks = self.speech_chunk_count
            self.reset()

            if speech_chunks < self.config.min_speech_chunks:
                logger.info("VAD very short audio event")
                return None
            return completed_audio
        return None




    