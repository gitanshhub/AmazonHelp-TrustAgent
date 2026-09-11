"""
src/retrieval/embeddings.py
Generates normalized embeddings using SentenceTransformer for historical support cases and incoming inquiries.
"""

import os

if "HF_HUB_OFFLINE" not in os.environ:
    os.environ["HF_HUB_OFFLINE"] = "1"
if "TRANSFORMERS_OFFLINE" not in os.environ:
    os.environ["TRANSFORMERS_OFFLINE"] = "1"

import numpy as np
from typing import List, Union
from sentence_transformers import SentenceTransformer

class CaseEmbedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed_texts(self, texts: List[str], batch_size: int = 128) -> np.ndarray:
        """Embeds a list of texts and returns normalized 2D numpy array (L2 normalized for cosine similarity)."""
        return self.model.encode(texts, batch_size=batch_size, normalize_embeddings=True, show_progress_bar=False)

    def embed_query(self, query: str) -> np.ndarray:
        """Embeds a single query string and returns a 1D normalized numpy array."""
        return self.model.encode([query], normalize_embeddings=True)[0]
