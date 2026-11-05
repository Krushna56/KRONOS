import unittest
from unittest.mock import patch

from app.ingestion.embedder import EMBEDDING_DIMENSION, generate_embedding


class FakeEmbedding:
    def tolist(self):
        return [0.25] * EMBEDDING_DIMENSION


class FakeModel:
    def encode(self, text, normalize_embeddings=True):
        self.text = text
        self.normalize_embeddings = normalize_embeddings
        return FakeEmbedding()


class EmbedderTests(unittest.TestCase):
    def test_generates_expected_dimension(self):
        model = FakeModel()
        with patch("app.ingestion.embedder._get_model", return_value=model):
            vector = generate_embedding("remember this preference")

        self.assertEqual(len(vector), EMBEDDING_DIMENSION)
        self.assertTrue(all(isinstance(value, float) for value in vector))
        self.assertTrue(model.normalize_embeddings)

    def test_rejects_empty_input(self):
        with self.assertRaises(ValueError):
            generate_embedding("   ")

    def test_does_not_silently_return_zero_vector_when_model_is_unavailable(self):
        with patch(
            "app.ingestion.embedder._get_model",
            side_effect=RuntimeError("model unavailable"),
        ):
            with self.assertRaises(RuntimeError):
                generate_embedding("some memory")
