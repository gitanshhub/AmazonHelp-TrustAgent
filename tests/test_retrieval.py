"""
tests/test_retrieval.py
Unit tests for FAISS vector index and CaseRetriever.
"""

import pytest
import numpy as np
import pandas as pd
from src.retrieval.embeddings import CaseEmbedder
from src.retrieval.index import VectorIndex
from src.retrieval.retriever import CaseRetriever

def test_case_embedder():
    embedder = CaseEmbedder()
    vec = embedder.embed_query("Where is my shipment?")
    assert isinstance(vec, np.ndarray)
    assert len(vec) == 384
    # Check L2 normalization (norm should be ~1.0)
    norm = np.linalg.norm(vec)
    assert abs(norm - 1.0) < 1e-3

def test_vector_index_build_and_search():
    df_sample = pd.DataFrame([
        {
            "conversation_id": "c1",
            "intent": "ORDER_TRACKING_STATUS",
            "customer_inquiry": "Where is my package?",
            "brand_resolution": "You can track your order here: [LINK]",
            "num_turns": 2
        },
        {
            "conversation_id": "c2",
            "intent": "CANCELLATION_REQUEST",
            "customer_inquiry": "Cancel my order please",
            "brand_resolution": "Visit Your Orders to cancel before dispatch.",
            "num_turns": 2
        }
    ])
    embedder = CaseEmbedder()
    v_index = VectorIndex()
    v_index.build_from_dataframe(df_sample, embedder)
    
    q_vec = embedder.embed_query("Where is my delivery tracking?")
    results = v_index.search(q_vec, top_k=2)
    assert len(results) == 2
    assert results[0]["case_id"] == "c1"
    assert results[0]["similarity"] > results[1]["similarity"]
