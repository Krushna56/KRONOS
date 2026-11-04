import unittest
import numpy as np
from app.voice.audio.buffer import AudioBuffer
from app.voice.runtime.pipeline import Pipeline, BaseStage, SpeechBufferStage
from app.voice.wakeword.detector import WakeWordDetector


class TestVoicePipeline(unittest.TestCase):
    def test_audio_buffer(self):
        buffer = AudioBuffer(max_chunks=5)
        for i in range(7):
            chunk = np.zeros((512,), dtype=np.float32)
            buffer.append(chunk)

        # Should be capped at max_chunks=5
        self.assertEqual(len(buffer), 5)
        all_chunks = buffer.get_all()
        self.assertEqual(len(all_chunks), 5)

    def test_wakeword_detector_fallback(self):
        detector = WakeWordDetector(threshold=0.5)
        silence = np.zeros((512,), dtype=np.float32)
        detected, name, score = detector.detect(silence)
        self.assertFalse(detected)
        self.assertEqual(score, 0.0)

    def test_pipeline_execution(self):
        buffer = AudioBuffer(max_chunks=10)
        pipeline = Pipeline([
            BaseStage(name="EchoStage"),
            SpeechBufferStage(buffer=buffer)
        ])

        chunk = np.ones((256,), dtype=np.float32)
        result = pipeline.execute(chunk)
        self.assertIsNotNone(result)
        self.assertEqual(len(buffer), 1)


if __name__ == "__main__":
    unittest.main()
