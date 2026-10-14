try:
    from app.voice.bus.subscriber import AudioSubscriber
except ImportError:
    from .subscriber import AudioSubscriber

class PrintSubscriber(AudioSubscriber):

    def receive(self, audio_chunk):

        print(audio_chunk.shape)
