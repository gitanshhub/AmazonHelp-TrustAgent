"""
src/evaluation/classification.py
Calculates intent classification metrics on the unseen test set:
Accuracy, Macro F1, Weighted F1, Precision, Recall, and Per-Intent breakdown.
"""

from typing import Dict, Any, List
import pandas as pd
from sklearn.metrics import classification_report, accuracy_score, f1_score

def evaluate_classifier(predictions: List[str], ground_truth: List[str]) -> Dict[str, Any]:
    """
    Computes rigorous classification metrics.
    """
    acc = accuracy_score(ground_truth, predictions)
    macro_f1 = f1_score(ground_truth, predictions, average="macro", zero_division=0)
    weighted_f1 = f1_score(ground_truth, predictions, average="weighted", zero_division=0)
    
    report_dict = classification_report(
        ground_truth,
        predictions,
        output_dict=True,
        zero_division=0
    )

    per_intent = {}
    for intent, scores in report_dict.items():
        if isinstance(scores, dict):
            per_intent[intent] = {
                "precision": round(scores["precision"], 3),
                "recall": round(scores["recall"], 3),
                "f1_score": round(scores["f1-score"], 3),
                "support": int(scores["support"])
            }

    return {
        "accuracy": round(acc, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "per_intent": per_intent
    }
