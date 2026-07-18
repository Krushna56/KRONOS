from .microphone import Microphone

class AudioManager:

    def __init__(self):

        self.microphone = Microphone()
        self.microphone.start()
    
    def start(self):

        self.microphone.start()

        print("Microphone started")
    
    def stop(self):

        self.microphone.stop()

        print("Microphone stopped")
    
    def read(self):

        return self.microphone.get_audio()
    