"""
src/intents/majority_baseline.py
Implements the Trivial Baseline: predicts the most frequent majority intent from the training data.
Used to demonstrate non-trivial skill in the simple and production classifiers.
"""

from collections import Counter
from typing import List, Tuple, Dict, Any
import numpy as np
from sklearn.metrics import accuracy_score, f1_score

class MajorityClassClassifier:
    """Trivial Baseline: Predicts dominant class for all inputs."""
    def __init__(self):
        self.majority_intent: str = "DELIVERY_DELAY"
        self.is_fitted: bool = False
        self.train_distribution: Dict[str, int] = {}

    def fit(self, labels: List[str]):
        counts = Counter(labels)
        self.train_distribution = dict(counts)
        self.majority_intent = counts.most_common(1)[0][0]
        self.is_fitted = True
        print(f"MajorityClassClassifier fitted. Dominant class: '{self.majority_intent}' ({counts[self.majority_intent]} occurrences)")

    def predict(self, text: str) -> Tuple[str, float]:
        """Returns majority class with empirical base rate as confidence."""
        total = sum(self.train_distribution.values()) or 1
        base_rate = self.train_distribution.get(self.majority_intent, 1) / total
        return self.majority_intent, round(base_rate, 4)

    def evaluate(self, ground_truth: List[str]) -> Dict[str, float]:
        """Evaluates baseline against ground truth."""
        preds = [self.majority_intent] * len(ground_truth)
        acc = accuracy_score(ground_truth, preds)
        macro_f1 = f1_score(ground_truth, preds, average="macro", zero_division=0)
        return {
            "majority_intent": self.majority_intent,
            "accuracy": round(acc, 4),
            "macro_f1": round(macro_f1, 4)
        }
