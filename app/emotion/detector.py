"""
Emotion detection using HuggingFace transformers.
Model is loaded lazily on first use to avoid blocking server startup.
Falls back to a simple keyword heuristic when the model is unavailable.
"""
from loguru import logger

_emotion_pipeline = None
_pipeline_failed = False

# Basic keyword-based fallback when transformer model is not available
_KEYWORD_MAP = {
    "anger":   ["angry", "furious", "rage", "mad", "hate"],
    "disgust": ["disgusting", "gross", "nasty", "repulsive"],
    "fear":    ["afraid", "scared", "terrified", "fear", "anxious"],
    "joy":     ["happy", "glad", "excited", "great", "awesome", "love"],
    "neutral": [],
    "sadness": ["sad", "unhappy", "depressed", "cry", "miss"],
    "surprise":["wow", "amazing", "surprised", "unexpected", "astonishing"],
}


def _load_pipeline():
    """Attempt to load the HuggingFace emotion pipeline once."""
    global _emotion_pipeline, _pipeline_failed
    if _emotion_pipeline is not None or _pipeline_failed:
        return
    try:
        from transformers import pipeline as hf_pipeline
        _emotion_pipeline = hf_pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
        )
        logger.info("Emotion pipeline loaded successfully.")
    except Exception as exc:  # noqa: BLE001
        _pipeline_failed = True
        logger.warning(
            f"Emotion pipeline unavailable ({exc}); using keyword fallback."
        )


def _keyword_fallback(text: str) -> str:
    text_lower = text.lower()
    for emotion, keywords in _KEYWORD_MAP.items():
        if any(kw in text_lower for kw in keywords):
            return emotion
    return "neutral"


def detect_emotion(text: str) -> str:
    """Return the dominant emotion label for *text*."""
    _load_pipeline()
    if _emotion_pipeline is not None:
        try:
            result = _emotion_pipeline(text)
            return result[0]["label"]
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Emotion pipeline inference failed: {exc}")
    return _keyword_fallback(text)