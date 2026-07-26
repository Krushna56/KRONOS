from .microphone import Microphone

class AudioManager:

    def __init__(self):

        self.microphone = Microphone()
    
    
    def start(self):

        self.microphone.start()

        print("Microphone started")
    
    def stop(self):

        self.microphone.stop()

        print("Microphone stopped")
    
    def subscribe(self, subscriber):

        self.microphone.publisher.subscribe(
            subscriber
        )
    
    def unsubscribe(self, subscriber):

        self.microphone.publisher.unsubscribe(
            subscriber
        )