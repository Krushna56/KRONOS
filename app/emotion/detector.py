import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

MODEL_ID = "j-hartmann/emotion-english-distilroberta-base"


@lru_cache(maxsize=1)
def _get_pipeline():
    """Lazy-load the classifier on first use (not at import) so the server
    starts fast and still runs offline / without `transformers` installed."""
    try:
        from transformers import pipeline

        return pipeline("text-classification", model=MODEL_ID)
    except Exception as e:  # missing dep, no network, etc.
        logger.warning(f"[Emotion] classifier unavailable, defaulting to 'neutral': {e}")
        return None


def detect_emotion(text: str) -> str:
    classifier = _get_pipeline()
    if classifier is None or not text:
        return "neutral"
    return classifier(text)[0]["label"]
