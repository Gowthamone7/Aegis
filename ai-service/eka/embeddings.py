"""
EKA Embedding Providers
  - hashing: SHA-256 → 128-dim float vector (zero deps beyond stdlib)
  - fastembed: BAAI/bge-small-en-v1.5 via fastembed (ONNX, Python 3.14 safe)

cosine_similarity(a, b) → float is exported from here.
"""
from __future__ import annotations

import hashlib
import math
from abc import ABC, abstractmethod
from typing import List

from .config import settings


# ─────────────────────────── cosine similarity ───────────────────────────────

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Return cosine similarity in [−1, 1]. Returns 0.0 for zero vectors."""
    if len(a) != len(b):
        raise ValueError(f"Vector length mismatch: {len(a)} vs {len(b)}")
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


# ─────────────────────────── base interface ───────────────────────────────────

class EmbeddingProvider(ABC):
    """Abstract embedding provider."""

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Embed a single text string → float list."""

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts. Default: sequential calls to embed()."""
        return [self.embed(t) for t in texts]

    @property
    @abstractmethod
    def dim(self) -> int:
        """Embedding dimension."""


# ─────────────────────────── hashing provider ────────────────────────────────

class HashingEmbedder(EmbeddingProvider):
    """
    Deterministic 128-dim embedding via SHA-256 bit scatter.
    No external dependencies.  Good for unit tests and offline demos.
    """

    _DIM = 128

    @property
    def dim(self) -> int:
        return self._DIM

    def embed(self, text: str) -> List[float]:
        # We produce multiple SHA-256 digests by salting with an index
        # to fill 128 floats (each digest gives 32 bytes = 32 floats per pass,
        # so 4 passes → 128).
        raw_bytes: list[float] = []
        idx = 0
        while len(raw_bytes) < self._DIM:
            salted = f"{idx}:{text}".encode("utf-8")
            digest = hashlib.sha256(salted).digest()
            for byte in digest:
                raw_bytes.append(float(byte))
                if len(raw_bytes) == self._DIM:
                    break
            idx += 1

        # Normalize to unit vector
        magnitude = math.sqrt(sum(v * v for v in raw_bytes))
        if magnitude == 0.0:
            return [0.0] * self._DIM
        return [v / magnitude for v in raw_bytes]


# ─────────────────────────── fastembed provider ───────────────────────────────

class FastEmbedEmbedder(EmbeddingProvider):
    """
    fastembed-based embedder using BAAI/bge-small-en-v1.5 (384-dim, ONNX).
    Lazy-loads the model on first use to avoid import-time overhead.
    """

    _MODEL = "BAAI/bge-small-en-v1.5"
    _DIM = 384

    def __init__(self) -> None:
        self._model = None  # lazy

    def _get_model(self):
        if self._model is None:
            try:
                from fastembed import TextEmbedding  # type: ignore
                self._model = TextEmbedding(model_name=self._MODEL)
            except ImportError as exc:
                raise RuntimeError(
                    "fastembed is not installed. "
                    "Install it with: pip install fastembed"
                ) from exc
        return self._model

    @property
    def dim(self) -> int:
        return self._DIM

    def embed(self, text: str) -> List[float]:
        model = self._get_model()
        # fastembed returns a generator of numpy arrays
        result = list(model.embed([text]))
        vec = result[0].tolist()
        return vec

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        model = self._get_model()
        return [v.tolist() for v in model.embed(texts)]


# ─────────────────────────── factory ─────────────────────────────────────────

_embedder_instance: EmbeddingProvider | None = None


def get_embedder() -> EmbeddingProvider:
    """Return (and cache) the configured embedding provider."""
    global _embedder_instance
    if _embedder_instance is not None:
        return _embedder_instance

    mode = settings.embeddings
    if mode == "fastembed":
        _embedder_instance = FastEmbedEmbedder()
    else:  # default to hashing
        _embedder_instance = HashingEmbedder()

    return _embedder_instance
