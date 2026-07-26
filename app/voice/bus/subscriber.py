from abc import ABC, abstractmethod
import numpy as np 

class AudioSubscriber(ABC):

    @abstractmethod
    def receive(self,audio_chunk : np.ndarray) -> None:
        
        # called whenever new microphone chunks receive 
        raise NotImplementedError



class CounterSubscriber(AudioSubscriber):

    def __init__(self):

        self.count = 0

    def receive(self, chunk):
        
        self.count += 1

        if self.count % 100 == 0:
            print(self.count)