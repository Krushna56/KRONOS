from voice.Wakeword.detector import WakeWordDetector
from voice.wakeword.listner import WakeWordListner 

class WakeWordengine():

    def __init__(self):

        self.listner = WakeWordListner()

        self.detector =  WakeWordDetector()

    def wait_for_wakeword(self):

        print("waiting....")

        while True:

            chunk = self.listner.next_chunk()

            detected, name, score = self.detector.detect(chunk)

            if detected:

                print(f"{name} detected")

                return 
