"""
src/intents/classifier.py
Implements Intent Classification models:
1. Baseline: TF-IDF + Logistic Regression with probability estimation.
2. Production: Retrieval-Augmented k-NN Classifier using   SentenceTransformers embeddings, an exact FAISS IndexFlatIP knowledge base,
   and weighted neighborhood cosine similarity for retrieval-derived confidence estimation.
"""

import os
import pickle
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sentence_transformers import SentenceTransformer

class TfidfLogisticClassifier:
    """Baseline 1: TF-IDF + Multinomial Logistic Regression."""
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), stop_words='english')
        self.model = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42)
        self.is_fitted = False

    def fit(self, texts: list, labels: list):
        X = self.vectorizer.fit_transform(texts)
        self.model.fit(X, labels)
        self.is_fitted = True

    def predict(self, text: str) -> Tuple[str, float]:
        if not self.is_fitted:
            raise ValueError("Classifier not trained yet.")
        X = self.vectorizer.transform([text])
        probs = self.model.predict_proba(X)[0]
        max_idx = np.argmax(probs)
        return self.model.classes_[max_idx], float(probs[max_idx])

    def save(self, filepath: str = "data/tfidf_classifier.pkl"):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "wb") as f:
            pickle.dump({"vectorizer": self.vectorizer, "model": self.model}, f)

    def load(self, filepath: str = "data/tfidf_classifier.pkl"):
        with open(filepath, "rb") as f:
            data = pickle.load(f)
            self.vectorizer = data["vectorizer"]
            self.model = data["model"]
            self.is_fitted = True


class RetrievalAugmentedClassifier:
    """
    Final Approach: Retrieval-assisted Intent Classification.
    Embeds incoming message using SentenceTransformer and performs distance-weighted
    k-Nearest Neighbor intent voting over historical labeled train cases.
    Computes retrieval-derived confidence score based on top neighbor consensus and cosine similarity.
    """
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", k: int = 5):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.k = k
        self.train_embeddings: Optional[np.ndarray] = None
        self.train_labels: Optional[np.ndarray] = None
        self.train_texts: Optional[list] = None

    def fit(self, texts: list, labels: list):
        print(f"Indexing {len(texts):,} labeled cases for retrieval-assisted classification...")
        self.train_texts = texts
        self.train_labels = np.array(labels)
        self.train_embeddings = self.model.encode(texts, batch_size=128, normalize_embeddings=True, show_progress_bar=False)
        print("Embedding index ready.")

    def predict(self, text: str) -> Dict[str, Any]:
        """
        Returns predicted intent, confidence score [0.0, 1.0], and top supporting neighbors.
        """
        query_emb = self.model.encode([text], normalize_embeddings=True)[0]
        sims = np.dot(self.train_embeddings, query_emb) # Cosine similarities
        top_k_indices = np.argsort(sims)[::-1][:self.k]
        
        top_intents = self.train_labels[top_k_indices]
        top_sims = sims[top_k_indices]
        
        # Weighted voting by similarity
        vote_weights = {}
        for intent, sim in zip(top_intents, top_sims):
            weight = max(float(sim), 0.0)
            vote_weights[intent] = vote_weights.get(intent, 0.0) + weight

        total_weight = sum(vote_weights.values()) or 1.0
        best_intent = max(vote_weights.items(), key=lambda x: x[1])[0]
        
        # Calibrate confidence: combination of top match similarity and vote consensus
        consensus_ratio = vote_weights[best_intent] / total_weight
        top_sim = float(top_sims[0])
        confidence = round(0.6 * top_sim + 0.4 * consensus_ratio, 3)
        confidence = min(max(confidence, 0.0), 1.0)

        supporting_examples = []
        for idx in top_k_indices[:3]:
            supporting_examples.append({
                "text": self.train_texts[idx],
                "intent": self.train_labels[idx],
                "similarity": round(float(sims[idx]), 3)
            })

        return {
            "intent": best_intent,
            "confidence": confidence,
            "top_similarity": round(top_sim, 3),
            "consensus": round(consensus_ratio, 3),
            "evidence": supporting_examples
        }

    def save(self, filepath: str = "data/retrieval_classifier.npz"):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        np.savez_compressed(
            filepath,
            embeddings=self.train_embeddings,
            labels=self.train_labels,
            texts=np.array(self.train_texts, dtype=object)
        )

    def load(self, filepath: str = "data/retrieval_classifier.npz"):
        data = np.load(filepath, allow_pickle=True)
        self.train_embeddings = data["embeddings"]
        self.train_labels = data["labels"]
        self.train_texts = data["texts"].tolist()
