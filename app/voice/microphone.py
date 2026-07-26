from sqlite3 import Blob
from queue import Queue, Full
import sounddevice as sd 

from .config import AudioConfig
from voice.bus.publisher import AudioPublisher 

class Microphone:

    def __init__(self):
        self.config = AudioConfig()

        self.audio_queue = Queue(
            maxsize = self.config.queue_size
        )

        self.publisher = AudioPublisher()

        self.stream = None
    
    def callback(self, indata, frames, time, status):
        if status:
            print(f"[Microphone] Status: {status}")
        
        self.publisher.publish(
            indata.copy()
        )
        
        try:
            self.audio_queue.put_nowait(
                indata.copy()
            )
        
        except Full:
            try:
                self.audio_queue.get_nowait()
            except Exception:
                pass

            try:
                self.audio_queue.put_nowait(
                    indata.copy()
                )
            except Full:
                pass

        
        # self.audio_queue.put(indata.copy())

    
    def start(self):

        if self.stream is not None:
            return

        self.stream = sd.InputStream(
            samplerate= self.config.sample_rate,
            channels= self.config.channels,
            dtype= self.config.dtype,
            blocksize= self.config.block_size,
            callback= self.callback
        )

        self.stream.start()

    def stop(self):
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()

            self.stream = None

    def get_audio(self):
        return self.audio_queue.get()
        
