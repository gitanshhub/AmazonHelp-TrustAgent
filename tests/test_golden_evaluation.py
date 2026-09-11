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
    judge = LLMJudge(mode="heuristic")
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
    assert res["judge_tier"] == "heuristic"
    assert res["mode_enforced"] == "heuristic"

def test_judge_strict_mode_prevents_silent_fallback():
    """Verifies that mode='llm' strictly raises RuntimeError on failure rather than silently degrading."""
    # An invalid model name in strict llm mode MUST raise RuntimeError
    with pytest.raises(RuntimeError):
        LLMJudge(model_name="nonexistent/fake_model_to_test_failure", mode="llm")

def test_judge_invalid_mode_raises_value_error():
    """Verifies that invalid judge mode raises ValueError."""
    with pytest.raises(ValueError):
        LLMJudge(mode="nonexistent_mode")

def test_golden_set_audit_status_and_rationale(golden_df):
    """Verifies that golden set audit template has PENDING_HUMAN_REVIEW and rationale notes."""
    review_path = "data/golden_set_review.csv"
    assert os.path.exists(review_path), f"Missing review CSV: {review_path}"
    df_rev = pd.read_csv(review_path)
    assert "audit_status" in df_rev.columns
    assert df_rev["audit_status"].isin(["HUMAN_VERIFIED", "PENDING_HUMAN_REVIEW"]).all(), "Audit status must be valid"
    assert "reviewer_rationale_notes" in df_rev.columns
    assert df_rev["reviewer_rationale_notes"].isnull().sum() == 0, "All items must have reviewer rationale notes"
    assert "proposed_intent" in df_rev.columns
    assert "proposed_action" in df_rev.columns
