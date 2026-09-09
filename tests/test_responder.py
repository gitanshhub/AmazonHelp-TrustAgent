"""
tests/test_responder.py
Unit tests for GroundedResponder:
1. Verifies that strong historical precedents are used as the primary grounding source.
2. Verifies safe fallback when no precedent exists.
3. Verifies that forbidden promises / hallucinated actions are flagged.
"""

import pytest
from src.generation.responder import GroundedResponder

@pytest.fixture
def responder():
    return GroundedResponder(brand_name="AmazonHelp")

def test_responder_uses_retrieved_precedent(responder):
    """When a strong historical precedent exists, the responder must adapt it and expose source case IDs."""
    retrieved_cases = [{
        "case_id": "case_amazon_9981",
        "similarity": 0.81,
        "intent": "DELIVERY_DELAY",
        "customer_inquiry": "My package was supposed to arrive yesterday.",
        "brand_resolution": "I'm sorry for the delay! You can check your latest carrier delivery window here: [LINK]"
    }]
    resp = responder.generate_response(
        customer_message="Where is my parcel?",
        intent="DELIVERY_DELAY",
        retrieved_cases=retrieved_cases,
        confidence=0.85
    )
    assert resp["source"] == "retrieved_historical_case"
    assert resp["source_case_ids"] == ["case_amazon_9981"]
    assert "carrier delivery window" in resp["text"]
    assert resp["is_grounded"] is True

def test_responder_safe_fallback_when_no_precedent(responder):
    """When no precedent is retrieved, the responder falls back safely to policy guidance."""
    resp = responder.generate_response(
        customer_message="Random query with zero matches",
        intent="ORDER_TRACKING_STATUS",
        retrieved_cases=[],
        confidence=0.70
    )
    assert resp["source"] == "conservative_fallback_template"
    assert resp["source_case_ids"] == []
    assert resp["is_grounded"] is True
    assert "[LINK]" in resp["text"]

def test_responder_flags_forbidden_hallucinated_claims(responder):
    """Validates that fabricated refund or account access claims fail the groundedness check."""
    fake_claim_1 = "I have refunded $50.00 to your credit card right away."
    assert responder.validate_groundedness(fake_claim_1) is False

    fake_claim_2 = "I've reset your password and accessed your account."
    assert responder.validate_groundedness(fake_claim_2) is False

    safe_claim = "You can view your refund status in Your Account under Order History: [LINK]"
    assert responder.validate_groundedness(safe_claim) is True
