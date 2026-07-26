from sqlalchemy import TIMESTAMP
from pathlib import Path
from datetime import datetime 
import wave
import numpy as np 

class Recorder:

    def __init__(self, output_directory:str = "recordings"):

        self.output_directory = Path(
            output_directory
        )

        self.output_directory.mkdir(
            parents = True,
            exist_ok=True
        )
    
    def save(self, audio_chunks: list[np.ndarray], sample_rate: int, filename: str | None = None) -> Path:

        if not audio_chunks:
            raise ValueError(
                "No audio chunks provided"
            )
        
        if filename is None:

            timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
            
            filename = (
                f"speech_{timestamp}.wav"
            )

        filepath = (
            self.output_directory / filename 
        )



        audio = np.concatenate(audio_chunks, axis=0)

        # conver float32  [-1, 1]
        # to signed 16bit PCM.

        audio = np.clip(
            audio,
            -1.0,
            

        )

        audio = (audio * 32627).astype(np.int16)

        with wave.open(filename, "wb") as wf:

            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio.tobytes())

        return filepath 

        
