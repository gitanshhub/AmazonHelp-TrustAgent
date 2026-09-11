"""
scripts/build_golden_set.py
Constructs the 200-example Golden Evaluation Set from unseen AmazonHelp conversations.
Enforces:
1. Zero leakage: strictly drawn from unseen conversations not in train_conversations.parquet.
2. Stratified sampling: guarantees representation across all 15 intents, including rare,
   high-risk disputes (fraud, payment), ambiguous queries, and multi-turn dialogues.
3. Standardized schema matching Hiver requirements.
"""

import os
import sys
import json
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.intents.taxonomy import IntentTaxonomy

def build_golden_set(
    test_parquet="data/test_conversations.parquet",
    train_parquet="data/train_conversations.parquet",
    target_count=200,
    random_state=42
):
    print(f"Loading unseen candidate conversations from {test_parquet}...")
    df_test = pd.read_parquet(test_parquet)
    df_train = pd.read_parquet(train_parquet)
    
    train_ids = set(df_train["conversation_id"])
    test_ids = set(df_test["conversation_id"])
    
    # Assert zero leakage at candidate level
    overlap = train_ids.intersection(test_ids)
    assert len(overlap) == 0, f"Critical Leakage! {len(overlap)} conversations overlap with train set!"
    print("Pre-sampling leakage check passed: 0% overlap with training conversations.")

    taxonomy = IntentTaxonomy("configs/intents.yaml")
    all_intents = taxonomy.get_all_intents()

    # Define target allocation per intent for 200 items:
    # Balancing real-world volume with guaranteed representation of rare & high-risk intents
    # High-risk & Rare intents need at least 6-12 samples to test safety thoroughly
    intent_quotas = {
        "DELIVERY_DELAY": 23,
        "PACKAGE_DELIVERED_NOT_RECEIVED": 19,
        "ORDER_TRACKING_STATUS": 18,
        "CANCELLATION_REQUEST": 14,
        "DIGITAL_SERVICES_AND_DEVICE": 14,
        "DAMAGED_OR_DEFECTIVE_ITEM": 14,
        "WRONG_ITEM_RECEIVED": 14,
        "PRIME_MEMBERSHIP_INQUIRY": 12,
        "REFUND_NOT_RECEIVED": 12,
        "UNAUTHORIZED_TRANSACTION_FRAUD": 12, # High-Risk
        "PAYMENT_AND_BILLING_ISSUE": 12,      # High-Risk
        "ACCOUNT_ACCESS_SECURITY": 10,        # High-Risk
        "GENERAL_INQUIRY_FEEDBACK": 10,
        "RETURN_EXCHANGE_INQUIRY": 8,         # Rare
        "OTHER": 8                            # Ambiguous
    }

    assert sum(intent_quotas.values()) == target_count, f"Total quota {sum(intent_quotas.values())} != {target_count}"

    sampled_rows = []
    np.random.seed(random_state)

    for intent, quota in intent_quotas.items():
        subset = df_test[df_test["intent"] == intent]
        if len(subset) < quota:
            print(f"Warning: Intent {intent} has only {len(subset)} test samples; using all.")
            chosen = subset
        else:
            chosen = subset.sample(n=quota, random_state=random_state)
            
        for _, row in chosen.iterrows():
            risk = taxonomy.get_risk_level(intent)
            is_auto = taxonomy.is_auto_eligible(intent)
            
            # Categorize sampling group
            if intent in ["UNAUTHORIZED_TRANSACTION_FRAUD", "PAYMENT_AND_BILLING_ISSUE", "ACCOUNT_ACCESS_SECURITY"]:
                group = "high_risk"
            elif intent in ["RETURN_EXCHANGE_INQUIRY", "GENERAL_INQUIRY_FEEDBACK"]:
                group = "rare_intent"
            elif intent == "OTHER":
                group = "ambiguous"
            else:
                group = "common_support"

            # Determine expected action based on safety taxonomy
            expected_action = "AUTO" if (is_auto and risk in ["LOW", "MEDIUM"] and intent != "OTHER") else "ESCALATE"

            # Context summary
            num_turns = int(row.get("num_turns", 2))
            context_snippet = f"{num_turns}-turn Twitter exchange"

            sampled_rows.append({
                "conversation_id": row["conversation_id"],
                "customer_message": row["customer_inquiry"].strip(),
                "intent": intent,
                "expected_action": expected_action,
                "risk_level": risk,
                "sampling_group": group,
                "conversation_context": context_snippet,
                "reference_resolution": str(row.get("brand_resolution", "")).strip(),
                "notes": f"Stratified sample for {group} category; baseline expected action: {expected_action}"
            })

    df_golden = pd.DataFrame(sampled_rows)
    # Shuffle for evaluation presentation
    df_golden = df_golden.sample(frac=1.0, random_state=random_state).reset_index(drop=True)
    df_golden["sample_index"] = range(1, len(df_golden) + 1)

    # Reorder columns
    cols = [
        "sample_index", "conversation_id", "customer_message", "intent", 
        "expected_action", "risk_level", "sampling_group", 
        "reference_resolution", "conversation_context", "notes"
    ]
    df_golden = df_golden[cols]

    os.makedirs("data", exist_ok=True)
    csv_path = "data/golden_set.csv"
    jsonl_path = "data/golden_set.jsonl"
    review_path = "data/golden_set_review.csv"

    df_golden.to_csv(csv_path, index=False, encoding="utf-8")
    df_golden.to_json(jsonl_path, orient="records", lines=True, force_ascii=False)
    
    # Review format with explicit audit columns marked PENDING_HUMAN_REVIEW
    df_review = df_golden.copy()
    df_review["dataset_heuristic_intent"] = df_review["intent"]
    df_review["proposed_intent"] = df_review["intent"]
    df_review["dataset_heuristic_action"] = df_review["expected_action"]
    df_review["proposed_action"] = df_review["expected_action"]
    df_review["audit_status"] = "PENDING_HUMAN_REVIEW"
    df_review["reviewer_rationale_notes"] = df_review["notes"]
    df_review.to_csv(review_path, index=False, encoding="utf-8")

    print(f"\nConstructed Golden Set with {len(df_golden)} examples.")
    print(f"Saved to:")
    print(f"  - CSV:   {csv_path}")
    print(f"  - JSONL: {jsonl_path}")
    print(f"  - Reviewer Audit Template: {review_path} (status: PENDING_HUMAN_REVIEW)")

    print("\n--- Golden Set Intent Distribution ---")
    print(df_golden["intent"].value_counts())
    print("\n--- Expected Action Distribution ---")
    print(df_golden["expected_action"].value_counts())
    print("\n--- Risk Level Distribution ---")
    print(df_golden["risk_level"].value_counts())

if __name__ == "__main__":
    build_golden_set()
