"""
tests/test_classifier.py
Unit tests for intent classification and taxonomy.
"""

import pytest
from src.intents.taxonomy import IntentTaxonomy
from src.intents.classifier import TfidfLogisticClassifier

def test_intent_taxonomy_loading():
    tax = IntentTaxonomy("configs/intents.yaml")
    intents = tax.get_all_intents()
    assert len(intents) >= 10
    assert "ORDER_TRACKING_STATUS" in intents
    assert "UNAUTHORIZED_TRANSACTION_FRAUD" in intents
    assert tax.get_risk_level("UNAUTHORIZED_TRANSACTION_FRAUD") == "CRITICAL"
    assert tax.is_auto_eligible("ORDER_TRACKING_STATUS") is True

def test_tfidf_classifier_fit_and_predict():
    texts = [
        "Where is my package? It is late.",
        "Track my delivery please.",
        "I need to cancel my order now.",
        "Please cancel my purchase."
    ]
    labels = ["ORDER_TRACKING_STATUS", "ORDER_TRACKING_STATUS", "CANCELLATION_REQUEST", "CANCELLATION_REQUEST"]
    clf = TfidfLogisticClassifier()
    clf.fit(texts, labels)
    pred, conf = clf.predict("Can you track my package?")
    assert pred in ["ORDER_TRACKING_STATUS", "CANCELLATION_REQUEST"]
    assert 0.0 <= conf <= 1.0
