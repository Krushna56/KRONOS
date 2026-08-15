"""
Sentence embedding generation using sentence-transformers.
Model is loaded lazily on first use to avoid blocking server startup.
Falls back to a deterministic hash-based pseudo-embedding when the library
or model weights are unavailable (useful in CI / lightweight environments).
"""
from __future__ import annotations

import hashlib
import math
from loguru import logger

_EMBEDDING_DIM = 384

_st_model = None
_model_failed = False


def _load_model():
    """Attempt to load the SentenceTransformer model once."""
    global _st_model, _model_failed
    if _st_model is not None or _model_failed:
        return
    try:
        from sentence_transformers import SentenceTransformer
        _st_model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("SentenceTransformer model loaded successfully.")
    except Exception as exc:  # noqa: BLE001
        _model_failed = True
        logger.warning(
            f"SentenceTransformer unavailable ({exc}); using hash-based fallback."
        )


def _hash_embedding(text: str) -> list[float]:
    """
    Produce a deterministic unit-vector pseudo-embedding from *text*.
    Not semantically meaningful, but keeps the pipeline functional.
    """
    raw = hashlib.sha512(text.encode()).digest()
    # Convert bytes to floats in [-1, 1]
    floats: list[float] = []
    for i in range(0, len(raw), 2):
        val = (raw[i] * 256 + raw[i + 1]) / 32767.5 - 1.0
        floats.append(val)
    # Pad or truncate to _EMBEDDING_DIM
    floats = (floats * math.ceil(_EMBEDDING_DIM / len(floats)))[:_EMBEDDING_DIM]
    # Normalize to unit vector
    magnitude = math.sqrt(sum(x * x for x in floats)) or 1.0
    return [x / magnitude for x in floats]


def generate_embedding(text: str) -> list[float]:
    """Return a float list embedding of length 384 for *text*."""
    _load_model()
    if _st_model is not None:
        try:
            embedding = _st_model.encode(text)
            return embedding.tolist()
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"SentenceTransformer encode failed: {exc}")
    return _hash_embedding(text)
