import numpy as np
from typing import List, Tuple

class InMemoryVectorStore:
    """Simple in‑memory vector store.
    Stores embeddings and the corresponding text chunks.
    Provides a `add` method for ingestion and a `search` method
    that returns the top `k` most similar texts using cosine similarity.
    """

    def __init__(self):
        self.embeddings: List[np.ndarray] = []  # list of 1‑D arrays
        self.texts: List[str] = []

    def add(self, embeddings: np.ndarray, texts: List[str]) -> None:
        """Add a batch of embeddings and their texts.
        `embeddings` must be a 2‑D NumPy array with shape (n, dim).
        """
        for i in range(embeddings.shape[0]):
            self.embeddings.append(embeddings[i])
            self.texts.append(texts[i])

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))

    def search(self, query_vec: np.ndarray, top_k: int = 5) -> List[Tuple[str, float]]:
        """Return the `top_k` most similar text chunks.
        Returns a list of tuples `(text, similarity_score)` sorted
        by decreasing similarity.
        """
        if not self.embeddings:
            return []
        scores = [(text, self._cosine_similarity(query_vec, emb))
                  for emb, text in zip(self.embeddings, self.texts)]
        # Sort by score descending and take top_k
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def save_to_disk(self, filepath: str) -> None:
        """Save the current embeddings and texts to a compressed .npz file."""
        if not self.embeddings:
            return
        np.savez_compressed(
            filepath,
            embeddings=np.array(self.embeddings),
            texts=np.array(self.texts, dtype=object)
        )

    def load_from_disk(self, filepath: str) -> bool:
        """Load embeddings and texts from a compressed .npz file.
        Returns True if successful, False otherwise.
        """
        import os
        if not os.path.exists(filepath):
            return False
        try:
            data = np.load(filepath, allow_pickle=True)
            self.embeddings = list(data["embeddings"])
            self.texts = list(data["texts"])
            return True
        except Exception as e:
            print(f"Error loading vector store from disk: {e}")
            return False

