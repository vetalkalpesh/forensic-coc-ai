"""
ai/embeddings.py
Embeddings engine wrapper for local vector generation.
Uses sentence-transformers (all-MiniLM-L6-v2) with fallback to local mock/TF-IDF.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai.config import EMBEDDING_MODEL


class EmbeddingEngine:

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        self.model_name = model_name
        self._model = None
        self._load_model()

    def _load_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            self._mode = "sentence_transformers"
        except Exception:
            # Fallback for environments without sentence-transformers installed yet
            self._mode = "fallback"
            print(f"[EmbeddingEngine] Warning: sentence-transformers not available. Operating in fallback vector mode.")

    def embed_texts(self, texts: list) -> list:
        """Embed a list of text strings into vector floats."""
        if not texts:
            return []

        if self._mode == "sentence_transformers":
            embeddings = self._model.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()
        else:
            # Fallback deterministic pseudo-vector (384 dimensions) for local testing
            vectors = []
            for text in texts:
                vec = [0.0] * 384
                # Hash words to dimensions
                words = text.lower().split()
                for i, w in enumerate(words):
                    idx = abs(hash(w)) % 384
                    vec[idx] += 1.0 / (i + 1)
                # L2 normalize
                norm = sum(v * v for v in vec) ** 0.5
                if norm > 0:
                    vec = [v / norm for v in vec]
                vectors.append(vec)
            return vectors

    def embed_query(self, query: str) -> list:
        """Embed a single query string into a vector float list."""
        res = self.embed_texts([query])
        return res[0] if res else [0.0] * 384
