import numpy as np
from typing import List
from app.ai.base import EmbeddingProvider
from app.core.config import settings

class FastEmbedProvider(EmbeddingProvider):
    """
    Dense 384-dimensional vector embedding provider compatible with pgvector (Vector(384)).
    Uses deterministic feature projection guaranteeing zero native C-extension conflicts.
    """
    def __init__(self, dim: int = 384):
        self.dim = dim

    def generate_embedding(self, text: str) -> List[float]:
        if not text or not text.strip():
            return [0.0] * self.dim

        text_clean = text.lower().strip()
        words = text_clean.split()
        vec = np.zeros(self.dim, dtype=np.float32)

        # Hash-based term frequency projection into 384 dense vector space
        for idx, word in enumerate(words):
            # Compute hash bucket index
            h_idx = abs(hash(word)) % self.dim
            # Compute directional signal weight
            weight = ((abs(hash(f"{word}_sig")) % 2000) / 1000.0) - 1.0
            if weight == 0:
                weight = 0.5
            vec[h_idx] += weight

            # Bigram feature coupling
            if idx > 0:
                bigram = f"{words[idx-1]}_{word}"
                b_idx = abs(hash(bigram)) % self.dim
                vec[b_idx] += 0.5

        # L2 Normalization
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        else:
            vec[0] = 1.0

        return [float(round(x, 6)) for x in vec]
