import logging

logger = logging.getLogger(__name__)
_model = None


def _get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception as e:
            logger.warning(f"[Embedder] SentenceTransformer unavailable: {e}")
            _model = None
    return _model


def generate_embedding(text):
    model = _get_model()
    if model is None:
        # Return zero-vector fallback so server keeps running
        return [0.0] * 384
    embedding = model.encode(text)
    return embedding.tolist()
