import logging

logger = logging.getLogger(__name__)
_model = None
EMBEDDING_DIMENSION = 384


def _get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer

            _model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception as exc:
            logger.exception("[Embedder] SentenceTransformer could not be loaded")
            raise RuntimeError(
                "The sentence-transformer model is unavailable; memory embeddings cannot be generated."
            ) from exc
    return _model


def generate_embedding(text: str) -> list[float]:
    """Generate a 384-dimensional embedding; never silently return a zero vector."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Embedding input must be a non-empty string.")

    model = _get_model()
    embedding = model.encode(text.strip(), normalize_embeddings=True)
    vector = embedding.tolist() if hasattr(embedding, "tolist") else list(embedding)

    if len(vector) != EMBEDDING_DIMENSION:
        raise ValueError(
            f"Expected {EMBEDDING_DIMENSION} embedding dimensions, received {len(vector)}."
        )
    return [float(value) for value in vector]
