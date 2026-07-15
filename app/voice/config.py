from dataclasses import dataclass


@dataclass(slots=True)
class AudioConfig:
    sample_rate: int = 16000
    channels: int = 1
    dtype: str = "float32"
    block_size: int = 1024
    queue_size: int = 100

    