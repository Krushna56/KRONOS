import unittest
import numpy as np
from app.voice.vad.vad_engine import VADEngine


class TestVADEngine(unittest.TestCase):
    def test_silence_probability(self):
        vad = VADEngine()
        silence = np.zeros((512, 1), dtype=np.float32)
        probability = vad.get_speech_probability(silence)
        print(f"VAD silence probability: {probability}")
        self.assertGreaterEqual(probability, 0.0)
        self.assertLessEqual(probability, 1.0)


if __name__ == "__main__":
    unittest.main()
