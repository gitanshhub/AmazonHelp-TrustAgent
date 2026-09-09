"""
tests/test_escalation.py
Unit tests for Trust Gate and Escalation Policy (Milestones 14, 15, 19).
"""

import pytest
from src.escalation.policy import TrustGatePolicy

@pytest.fixture
def policy():
    return TrustGatePolicy(confidence_threshold=0.75, similarity_threshold=0.62)

def test_auto_handle_standard_case(policy):
    """Confident low-risk intent with strong historical precedent should AUTO-HANDLE."""
    retrieval_data = {
        "cases": [{"case_id": "c1", "similarity": 0.85, "intent": "ORDER_TRACKING_STATUS"}],
        "top_similarity": 0.85,
        "has_strong_evidence": True
    }
    decision = policy.evaluate(
        intent="ORDER_TRACKING_STATUS",
        confidence=0.92,
        retrieval_data=retrieval_data,
        unsupported_claims_detected=False
    )
    assert decision["action"] == "AUTO"
    assert decision["reason_code"] == "CONFIDENT_GROUNDED"

def test_escalate_low_confidence(policy):
    """Low confidence should trigger ESCALATE with LOW_CONFIDENCE."""
    retrieval_data = {
        "cases": [{"case_id": "c1", "similarity": 0.70, "intent": "DELIVERY_DELAY"}],
        "top_similarity": 0.70,
        "has_strong_evidence": True
    }
    decision = policy.evaluate(
        intent="DELIVERY_DELAY",
        confidence=0.45,
        retrieval_data=retrieval_data,
        unsupported_claims_detected=False
    )
    assert decision["action"] == "ESCALATE"
    assert decision["reason_code"] == "LOW_CONFIDENCE"

def test_escalate_no_similar_case(policy):
    """Lack of historical precedent should trigger ESCALATE with NO_SIMILAR_CASE."""
    retrieval_data = {
        "cases": [],
        "top_similarity": 0.35,
        "has_strong_evidence": False
    }
    decision = policy.evaluate(
        intent="DELIVERY_DELAY",
        confidence=0.88,
        retrieval_data=retrieval_data,
        unsupported_claims_detected=False
    )
    assert decision["action"] == "ESCALATE"
    assert decision["reason_code"] == "NO_SIMILAR_CASE"

def test_escalate_critical_fraud(policy):
    """Stolen cards or fraud MUST ESCALATE immediately with HIGH_RISK."""
    retrieval_data = {
        "cases": [{"case_id": "c1", "similarity": 0.90, "intent": "UNAUTHORIZED_TRANSACTION_FRAUD"}],
        "top_similarity": 0.90,
        "has_strong_evidence": True
    }
    decision = policy.evaluate(
        intent="UNAUTHORIZED_TRANSACTION_FRAUD",
        confidence=0.98,
        retrieval_data=retrieval_data,
        unsupported_claims_detected=False
    )
    assert decision["action"] == "ESCALATE"
    assert decision["reason_code"] == "HIGH_RISK"

def test_escalate_payment_dispute(policy):
    """Duplicate billing or payment disputes must escalate with PAYMENT_DISPUTE."""
    retrieval_data = {
        "cases": [{"case_id": "c1", "similarity": 0.88, "intent": "PAYMENT_AND_BILLING_ISSUE"}],
        "top_similarity": 0.88,
        "has_strong_evidence": True
    }
    decision = policy.evaluate(
        intent="PAYMENT_AND_BILLING_ISSUE",
        confidence=0.91,
        retrieval_data=retrieval_data,
        unsupported_claims_detected=False
    )
    assert decision["action"] == "ESCALATE"
    assert decision["reason_code"] == "PAYMENT_DISPUTE"

def test_escalate_unsupported_claims(policy):
    """Hallucinated claims detected should block auto-handling."""
    retrieval_data = {
        "cases": [{"case_id": "c1", "similarity": 0.85, "intent": "ORDER_TRACKING_STATUS"}],
        "top_similarity": 0.85,
        "has_strong_evidence": True
    }
    decision = policy.evaluate(
        intent="ORDER_TRACKING_STATUS",
        confidence=0.95,
        retrieval_data=retrieval_data,
        unsupported_claims_detected=True
    )
    assert decision["action"] == "ESCALATE"
    assert decision["reason_code"] == "CONFLICTING_EVIDENCE"
