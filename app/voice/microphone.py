from sqlite3 import Blob
from queue import Queue
import sounddevice as sd 

from voice.config import AudioConfig

class Microphpone:

    def __init__(self):
        self.config = AudioConfig()

        self.audio_queue = Queue(
            maxsize = self.config.queue_size
        )

        self.stream = None
    
    def callback(self, indata, frames, time, status):
        if status:
            print(status)
        
        self.audio_queue.put(indata.copy())

    
    def start(self):

        self.stream = sd.InputStream(
            samplerate= self.config.sample_rate,
            channels= self.config.channels,
            dtype= self.config.dtype,
            blocksize= self.config.block_size,
            callback= self.callback
        )

        self.stream.start()

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
    
    def get_audio(self):
        return self.audio_queue.get()
        
