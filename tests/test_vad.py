import sys
from pathlib import Path
import numpy as np 

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.voice.vad.vad_engine import VADEngine

def test_silence_probability():

    vad = VADEngine()

    silence = np.zeros(
        (512, 1),
        dtype = np.float32
    )

    probability = (
        vad.get_speech_probability(
            silence
        )
    )

    print(
        f"silence probability: ",
        f"{probability}"
    )

    assert 0.0 <= probability <= 1.0 
