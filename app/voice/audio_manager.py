from voice.Microphpone import Microphpone

class AudioManager:

    def __init__(self):

        self.microphone.start()
    
    def start(self):

        self.microphone.start()

        print("Microphone started")
    
    def stop(self):

        self.microphone.stop()

        print("Microphone stopped")
    
    def read(self):

        return self.microphone.get_audio()
    