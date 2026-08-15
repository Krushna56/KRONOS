from voice.bus.subscriber import AudioSubscriber

class PrintSubscriber(AudioSubscriber):

    def receive(self, audio_chunk):

        print(audio_chunk.shape)
