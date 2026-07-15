import wave
import numpy as np 

class Recorder:
    
    def save(self, filename, audio_chunks, sample_rate):

        audio = np.concatenate(audio_chunks)

        audio = (audio * 32627).astype(np.int16)

        with wave.open(filename, "wb") as wf:

            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio.tobytes())

            