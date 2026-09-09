"""
tests/test_golden_evaluation.py
Unit tests for Golden Evaluation Set, Data Leakage, Majority Baseline, and Judge Schema (Phase 18).
"""

import os
import pytest
import pandas as pd
from src.intents.majority_baseline import MajorityClassClassifier
from src.evaluation.judge import LLMJudge

@pytest.fixture
def golden_df():
    path = "data/golden_set.csv"
    assert os.path.exists(path), f"Golden set file missing: {path}"
    return pd.read_csv(path)

def test_golden_set_size_and_fields(golden_df):
    """Asserts 150-250 hand-reviewed golden examples and mandatory fields."""
    assert 150 <= len(golden_df) <= 250, f"Expected 150-250 examples, got {len(golden_df)}"
    mandatory_cols = ["conversation_id", "customer_message", "intent", "expected_action", "risk_level"]
    for col in mandatory_cols:
        assert col in golden_df.columns, f"Missing mandatory column {col}"
    # Verify no nulls in critical fields
    assert golden_df["customer_message"].isnull().sum() == 0
    assert golden_df["intent"].isnull().sum() == 0

def test_no_duplicate_conversations(golden_df):
    """Asserts all conversation IDs in golden set are unique."""
    assert len(golden_df["conversation_id"].unique()) == len(golden_df)

def test_zero_leakage_with_training():
    """Asserts 0% intersection between Golden Set and Train Set conversation IDs."""
    golden_df = pd.read_csv("data/golden_set.csv")
    train_df = pd.read_parquet("data/train_conversations.parquet")
    golden_ids = set(golden_df["conversation_id"])
    train_ids = set(train_df["conversation_id"])
    assert len(golden_ids.intersection(train_ids)) == 0, "Data leakage detected between Golden and Train sets!"

def test_majority_baseline():
    """Verifies majority baseline fits and predicts properly."""
    clf = MajorityClassClassifier()
    clf.fit(["DELIVERY_DELAY", "DELIVERY_DELAY", "ORDER_TRACKING_STATUS"])
    pred, conf = clf.predict("Where is my stuff?")
    assert pred == "DELIVERY_DELAY"
    assert 0.0 <= conf <= 1.0

def test_judge_output_schema():
    """Verifies Judge output follows structured JSON schema (1-5 scale) without chain-of-thought."""
    judge = LLMJudge()
    res = judge.evaluate_reply(
        customer_message="My package was delayed by 3 days.",
        retrieved_precedent="Please check your tracking link: [LINK]",
        agent_response="We apologize for the delay. You can track your parcel at [LINK]."
    )
    for dim in ["correctness", "groundedness", "relevance", "helpfulness", "safety", "overall"]:
        assert dim in res
        assert 1 <= res[dim] <= 5
    assert "justification" in res
    assert isinstance(res["justification"], str)
    assert len(res["justification"]) > 5
