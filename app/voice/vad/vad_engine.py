import numpy as np 
import torch

from silero_vad import load_silero_vad
from app.voice.config import AudioConfig

class VADEngine:
    
    def __init__(self):

        self.config = AudioConfig()

        print("[VAD] loading silero VAD model...")

        self.model = load_silero_vad()

        print("[VAD] model loaded")
    
    def get_speech_probability(self, audio_chunk:np.ndarray) -> float:

        """ microphone return (512,1) silero expect mono (512)"""

        audio = audio_chunk.squeeze()

        # ensure float
        audio = audio.astype(
            np.float32,
            copy=False
        )

        # convert numpy array into pytorch tensor
        tensor = torch.from_numpy(audio)

        with torch.no_grad():

            probability = self.model(
                tensor,
                self.config.sample_rate
            ).item()
            return probability
    
    def is_speech(self, audio_chunk:np.ndarray) -> bool:
        
        probability = self.get_speech_probability(
            audio_chunk
        )

        return(
            probability >= self.config.speech_threshold
        )
