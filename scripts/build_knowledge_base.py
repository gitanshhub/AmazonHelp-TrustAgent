"""
scripts/build_knowledge_base.py
Executes Milestone 9, 10, 11:
1. Trains TF-IDF + Logistic Regression baseline classifier on train set.
2. Builds RetrievalAugmentedClassifier index.
3. Builds FAISS vector index of historical support resolutions.
"""

import os
import sys
import time
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.retrieval.embeddings import CaseEmbedder
from src.retrieval.index import VectorIndex
from src.intents.classifier import TfidfLogisticClassifier, RetrievalAugmentedClassifier

def main():
    start = time.time()
    train_path = "data/train_conversations.parquet"
    print(f"Loading training data from {train_path}...")
    df_train = pd.read_parquet(train_path)
    print(f"Total training conversations: {len(df_train):,}")

    texts = df_train["customer_inquiry"].tolist()
    labels = df_train["intent"].tolist()

    # 1. Train Baseline 1: TF-IDF + Logistic Regression
    print("\n--- Training Baseline 1 (TF-IDF + Logistic Regression) ---")
    tfidf_clf = TfidfLogisticClassifier()
    tfidf_clf.fit(texts, labels)
    tfidf_clf.save("data/tfidf_classifier.pkl")
    print("Baseline 1 model saved to data/tfidf_classifier.pkl")

    # 2. Build Production Retrieval-Augmented Classifier
    print("\n--- Building Retrieval-Augmented Intent Classifier ---")
    retrieval_clf = RetrievalAugmentedClassifier()
    retrieval_clf.fit(texts, labels)
    retrieval_clf.save("data/retrieval_classifier.npz")
    print("Retrieval classifier saved to data/retrieval_classifier.npz")

    # 3. Build FAISS Historical Resolution Index
    print("\n--- Building FAISS Historical Resolution Vector Index ---")
    embedder = CaseEmbedder()
    vector_index = VectorIndex()
    vector_index.build_from_dataframe(df_train, embedder, text_column="customer_inquiry")
    vector_index.save("data/faiss_index.bin", "data/faiss_metadata.parquet")

    print(f"\nKnowledge Base & Classifiers built in {time.time() - start:.1f}s!")

if __name__ == "__main__":
    main()
