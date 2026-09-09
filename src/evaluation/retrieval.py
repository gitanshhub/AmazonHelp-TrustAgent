"""
src/evaluation/retrieval.py
Computes standard information retrieval metrics on unseen test cases:
Recall@1, Recall@3, Recall@5, and Mean Reciprocal Rank (MRR).
"""

from typing import List, Dict, Any

def evaluate_retrieval(retrieval_results: List[Dict[str, Any]], target_intents: List[str]) -> Dict[str, float]:
    """
    Evaluates whether the retrieved historical cases match the target case's intent and resolution type.
    """
    total = len(target_intents)
    if total == 0:
        return {"recall_at_1": 0.0, "recall_at_3": 0.0, "recall_at_5": 0.0, "mrr": 0.0}

    hits_at_1 = 0
    hits_at_3 = 0
    hits_at_5 = 0
    reciprocal_ranks = []

    for result, true_intent in zip(retrieval_results, target_intents):
        cases = result.get("cases", [])
        retrieved_intents = [c["intent"] for c in cases]
        
        # Recall@K
        if retrieved_intents and retrieved_intents[0] == true_intent:
            hits_at_1 += 1
        if any(i == true_intent for i in retrieved_intents[:3]):
            hits_at_3 += 1
        if any(i == true_intent for i in retrieved_intents[:5]):
            hits_at_5 += 1

        # MRR
        rr = 0.0
        for rank, intent in enumerate(retrieved_intents[:5], start=1):
            if intent == true_intent:
                rr = 1.0 / rank
                break
        reciprocal_ranks.append(rr)

    return {
        "recall_at_1": round(hits_at_1 / total, 4),
        "recall_at_3": round(hits_at_3 / total, 4),
        "recall_at_5": round(hits_at_5 / total, 4),
        "mrr": round(sum(reciprocal_ranks) / total, 4)
    }
