from typing import Optional
import numpy as np 

from app.voice.config import AudioConfig
from app.voice.vad.vad_engine import VADEngine


class SpeechDetector:
    
    def __init__(self):

        self.config = AudioConfig()

        self.vad = VADEngine()

        self.is_recording = False

        self.audio_chunks = []

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

                print(
                    f"[VAD] speech started"
                    f"(prob={speech_probability:.2f})"
                )

                self.is_recording= True

                self.audio_chunks = [
                    audio_chunk.copy()
                ]

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

        if(self.silence_counter >= self.config.silence_chunks):
            print("[VAD] speech ended")

            completed_audio = (
                self.audio_chunks.copy()
            )

            speech_chunks = (
                self.speech_chunk_count
            )

            self.reset()

            # ignore accidental clicks/noise

            if (speech_chunks < self.config.min_speech_chunks):

                print("[VAD] very short"
                        "audio event"
                )

                return None 
            return completed_audio
        return None




    