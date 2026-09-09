"""
src/evaluation/escalation.py
Evaluates Trust Gate and safety policy metrics on unseen test conversations:
False Auto-Handling Rate, False Escalation Rate, Automation Rate, and Selective Prediction Thresholds.
"""

from typing import List, Dict, Any

def evaluate_escalation(decisions: List[str], ground_truth_escalate: List[bool]) -> Dict[str, Any]:
    """
    Evaluates Trust Gate decisions against ground truth safety labels.
    - True positive: Escalate when human is required.
    - False auto-handling (most dangerous failure): Auto-handled when human was required.
    - False escalation: Escalated when it could have been safely auto-handled.
    """
    total = len(decisions)
    if total == 0:
        return {}

    tp = 0 # should escalate & escalated
    fp = 0 # should auto & escalated
    tn = 0 # should auto & auto-handled
    fn = 0 # should escalate & auto-handled (CRITICAL RISK)

    for dec, must_escalate in zip(decisions, ground_truth_escalate):
        is_escalated = (dec == "ESCALATE")
        if must_escalate and is_escalated:
            tp += 1
        elif not must_escalate and is_escalated:
            fp += 1
        elif not must_escalate and not is_escalated:
            tn += 1
        elif must_escalate and not is_escalated:
            fn += 1

    automation_rate = (tn + fn) / total
    false_auto_rate = fn / total
    false_escalation_rate = fp / total
    escalation_precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    escalation_recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    return {
        "total_cases": total,
        "automation_rate": round(automation_rate, 4),
        "false_auto_handling_rate": round(false_auto_rate, 4),
        "false_escalation_rate": round(false_escalation_rate, 4),
        "escalation_precision": round(escalation_precision, 4),
        "escalation_recall": round(escalation_recall, 4),
        "confusion_matrix": {
            "true_escalations": tp,
            "false_escalations": fp,
            "safe_auto_handled": tn,
            "unsafe_auto_handled": fn
        }
    }
