from time import time
from queue import Queue, Empty
from threading import Thread 
import logging 

logger = logging.getLogger(__name__)

class AudioWorker(Thread):

    def __init__(self, subscriber, queue_size=100):

        super().__init__(daemon=True)
        
        self.subscriber = subscriber

        self.queue = Queue(maxsize = queue_size)

        self.running = False 
    
    def submit(self, audio_chunk):

        if self.queue.full():

            try:
                self.queue.get_nowait()
            except Empty:
                pass
        
        self.queue.put_nowait(audio_chunk)
    
    def stop(self):

        self.running = False
    
    def run(self):
        
        self.running = True

        while self.running:

            try:
                chunk = self.queue.get(timeout=0.2)
            except Empty:
                continue
            
            try:
                self.subscriber.receive(chunk)
            except Exception:

                logger.exception(
                    "Subscriber crashed: %s",
                    self.subscriber.__class__.__name__
                )

