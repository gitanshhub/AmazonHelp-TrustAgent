"""
src/retrieval/index.py
Builds and manages a FAISS vector index of historical support resolutions.
Only indexes conversations from the training set to prevent evaluation leakage.
"""

import os
import faiss
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from src.retrieval.embeddings import CaseEmbedder

class VectorIndex:
    def __init__(self, embedding_dim: int = 384):
        self.embedding_dim = embedding_dim
        # IndexFlatIP with normalized vectors computes exact cosine similarity
        self.index: Optional[faiss.IndexFlatIP] = None
        self.metadata: Optional[pd.DataFrame] = None

    def build_from_dataframe(
        self,
        df_train: pd.DataFrame,
        embedder: CaseEmbedder,
        text_column: str = "customer_inquiry"
    ):
        """
        Builds FAISS index using customer inquiry embeddings and stores conversation metadata.
        """
        print(f"Building FAISS vector index for {len(df_train):,} historical cases...")
        texts = df_train[text_column].tolist()
        embeddings = embedder.embed_texts(texts)
        
        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embeddings.astype(np.float32))

        # Store metadata mapping vector IDs -> conversation details
        metadata_cols = ["conversation_id", "intent", "customer_inquiry", "brand_resolution", "num_turns"]
        available_cols = [c for c in metadata_cols if c in df_train.columns]
        self.metadata = df_train[available_cols].copy().reset_index(drop=True)
        print(f"Index built successfully with {self.index.ntotal:,} vectors.")

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Searches index for top_k nearest neighbors.
        Returns list of matching cases with metadata and cosine similarity score.
        """
        if self.index is None or self.metadata is None:
            raise ValueError("Index is not loaded or built.")

        query_2d = np.ascontiguousarray([query_vector], dtype=np.float32)
        scores, indices = self.index.search(query_2d, top_k)

        results = []
        for rank, (idx, score) in enumerate(zip(indices[0], scores[0])):
            if idx < 0 or idx >= len(self.metadata):
                continue
            row = self.metadata.iloc[idx].to_dict()
            results.append({
                "rank": rank + 1,
                "similarity": round(float(score), 4),
                "case_id": row.get("conversation_id", f"case_{idx}"),
                "intent": row.get("intent", "UNKNOWN"),
                "customer_inquiry": row.get("customer_inquiry", ""),
                "brand_resolution": row.get("brand_resolution", ""),
                "num_turns": row.get("num_turns", 2)
            })
        return results

    def save(self, index_file: str = "data/faiss_index.bin", meta_file: str = "data/faiss_metadata.parquet"):
        """Saves FAISS index binary and metadata parquet."""
        os.makedirs(os.path.dirname(index_file), exist_ok=True)
        faiss.write_index(self.index, index_file)
        self.metadata.to_parquet(meta_file, index=False)
        print(f"Saved FAISS index to {index_file} and metadata to {meta_file}")

    def load(self, index_file: str = "data/faiss_index.bin", meta_file: str = "data/faiss_metadata.parquet"):
        """Loads FAISS index and metadata."""
        if not os.path.exists(index_file) or not os.path.exists(meta_file):
            raise FileNotFoundError("FAISS index or metadata file missing.")
        self.index = faiss.read_index(index_file)
        self.metadata = pd.read_parquet(meta_file)
        print(f"Loaded FAISS index with {self.index.ntotal:,} cases.")
