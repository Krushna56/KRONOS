from typing import List 
import numpy as np 
from voice.bus.subscriber import AudioSubscriber

class AudioPublisher:

    def __init__(self):

        self._subscribers: List[AudioSubscriber] = []
    
    def subscribe(self, subscriber: AudioSubscriber):

        if subscriber not in self._subscribers:
            self._subscribers.append(subscriber)

    def unsubscribe(self, subscriber: AudioSubscriber):

        if subscriber in self._subscribers:
            self._subscribers.remove(subscriber)

    def publish(self, audio_chunk: np.ndarray):

        for subscribe in self._subscribers:
            subscribe.receive(audio_chunk)
                  
