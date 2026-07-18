from dataclasses import dataclass


@dataclass(slots=True)
class AudioConfig:
    sample_rate: int = 16000
    channels: int = 1
    dtype: str = "float32"
    block_size: int = 512
    queue_size: int = 100

    # VAD
    speech_threshold: float = 0.5

    silence_chunks: int = 30

    min_speech_chunks: int = 5
