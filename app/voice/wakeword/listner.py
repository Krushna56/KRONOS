from voice.audio_manager import AudioManager

class WakeWordListner:

    def __init__(self):
        self.audio = AudioManager

    def next_chunk(self):
        return self.audio.read()

    