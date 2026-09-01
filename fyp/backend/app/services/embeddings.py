
from typing import List

import numpy as np

from app.core.config import settings

EMBED_DIM_TFIDF = 128

# Shared in-process cache so the (large) HF model is loaded into memory
# once, not once per user -- SentenceTransformerBackend instances only
# store the model *name*, not the model itself, when pickled.
_MODEL_CACHE: dict = {}


def _get_shared_model(model_name: str):
    if model_name not in _MODEL_CACHE:
        from sentence_transformers import SentenceTransformer

        _MODEL_CACHE[model_name] = SentenceTransformer(model_name)
    return _MODEL_CACHE[model_name]


class SentenceTransformerBackend:
    """Hugging Face sentence-transformers embeddings (default backend)."""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL

    def _model(self):
        return _get_shared_model(self.model_name)

    def fit(self, texts: List[str]) -> np.ndarray:
        # "fit" here just means "embed the corpus" -- no training happens,
        # the pretrained HF model is used as-is (kept as `fit` to match the
        # interface vector_store.py already calls).
        vectors = self._model().encode(
            texts, normalize_embeddings=True, show_progress_bar=False
        )
        return np.asarray(vectors, dtype="float32")

    def embed_query(self, text: str) -> np.ndarray:
        vector = self._model().encode(
            [text], normalize_embeddings=True, show_progress_bar=False
        )[0]
        return np.asarray(vector, dtype="float32")

    def __getstate__(self):
        # Only pickle the model name -- never the (large) loaded model.
        # On unpickle, embed_query()/fit() will fetch it from the shared
        # in-process cache (or load it fresh if this is a new process).
        return {"model_name": self.model_name}

    def __setstate__(self, state):
        self.model_name = state["model_name"]


class TfidfEmbeddingBackend:
    """Lightweight fallback: TF-IDF + SVD -> dense vectors. No torch needed."""

    def __init__(self, dim: int = EMBED_DIM_TFIDF):
        self.dim = dim
        self.vectorizer = None
        self.svd = None

    def fit(self, texts: List[str]) -> np.ndarray:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD

        self.vectorizer = TfidfVectorizer(
            stop_words="english", max_features=20000, ngram_range=(1, 2)
        )
        tfidf_matrix = self.vectorizer.fit_transform(texts)
        n_components = min(self.dim, max(2, tfidf_matrix.shape[1] - 1), tfidf_matrix.shape[0] - 1)
        n_components = max(n_components, 2)
        self.svd = TruncatedSVD(n_components=n_components, random_state=42)
        dense = self.svd.fit_transform(tfidf_matrix)
        return self._normalize(dense)

    def embed_query(self, text: str) -> np.ndarray:
        if self.vectorizer is None or self.svd is None:
            raise RuntimeError("Embedding backend not fitted yet")
        tfidf_vec = self.vectorizer.transform([text])
        dense = self.svd.transform(tfidf_vec)
        return self._normalize(dense)[0]

    @staticmethod
    def _normalize(matrix: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1e-9
        return (matrix / norms).astype("float32")


def get_embedding_backend():
    backend = settings.EMBEDDING_BACKEND.lower()
    if backend == "tfidf":
        return TfidfEmbeddingBackend()
    return SentenceTransformerBackend()
