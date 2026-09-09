"""
src/retrieval/retriever.py
End-to-end historical resolution retriever.
Embeds customer queries, queries the FAISS index, and computes quality signals
(max similarity, top-3 mean similarity, intent consistency).
"""

from typing import List, Dict, Any, Optional
import numpy as np
from src.retrieval.embeddings import CaseEmbedder
from src.retrieval.index import VectorIndex

class CaseRetriever:
    def __init__(
        self,
        embedder: Optional[CaseEmbedder] = None,
        index: Optional[VectorIndex] = None,
        index_file: str = "data/faiss_index.bin",
        meta_file: str = "data/faiss_metadata.parquet"
    ):
        self.embedder = embedder or CaseEmbedder()
        self.index = index or VectorIndex()
        if self.index.index is None:
            self.index.load(index_file, meta_file)

    def retrieve(self, query: str, top_k: int = 5, min_similarity: float = 0.40) -> Dict[str, Any]:
        """
        Retrieves relevant historical cases and calculates retrieval quality metrics.
        """
        query_vec = self.embedder.embed_query(query)
        candidates = self.index.search(query_vec, top_k=top_k)

        # Filter and score
        valid_cases = [c for c in candidates if c["similarity"] >= min_similarity]
        
        if not candidates:
            return {
                "cases": [],
                "quality_score": 0.0,
                "top_similarity": 0.0,
                "intent_consensus": 0.0,
                "has_strong_evidence": False
            }

        top_similarity = candidates[0]["similarity"]
        top_3_sims = [c["similarity"] for c in candidates[:3]]
        avg_top_sim = float(np.mean(top_3_sims)) if top_3_sims else top_similarity
        
        # Intent consistency among top 3
        top_intents = [c["intent"] for c in candidates[:3]]
        most_common_count = max(top_intents.count(i) for i in set(top_intents)) if top_intents else 0
        intent_consensus = most_common_count / len(top_intents) if top_intents else 0.0

        # Quality score combines similarity and neighbor intent agreement
        quality_score = round(0.7 * avg_top_sim + 0.3 * intent_consensus, 3)
        has_strong_evidence = (top_similarity >= 0.65 and len(valid_cases) >= 2)

        return {
            "cases": candidates,
            "quality_score": quality_score,
            "top_similarity": round(top_similarity, 3),
            "intent_consensus": round(intent_consensus, 3),
            "has_strong_evidence": has_strong_evidence
        }
