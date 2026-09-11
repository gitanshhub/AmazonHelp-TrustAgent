"""
scripts/build_reviewer_audit_set.py
Constructs the reviewer-ready audit template for the 200 Golden Evaluation Set items.
Strict Rules:
- Never fabricate human annotation or label anything HUMAN_VERIFIED unless human user supplied it.
- Mark audit_status as 'PENDING_HUMAN_REVIEW'.
- Provide 'proposed_intent', 'proposed_action' (AUTO vs ESCALATE), and detailed 'reviewer_rationale_notes'.
- Highlights noisy dataset labels (e.g. sentiment praise, callback queries, refund complaints mislabeled by regex).
"""

import os
import sys
import re
import pandas as pd
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def audit_record(row, taxonomy_cfg):
    msg = str(row["customer_message"]).strip()
    orig_intent = row["intent"]
    orig_action = row["expected_action"]
    group = row["sampling_group"]
    
    m_lower = msg.lower()
    
    proposed_intent = orig_intent
    proposed_action = orig_action
    notes = []

    # 1. Check for praise / gratitude mislabeled by keyword
    praise_signals = ["props to", "s/o to", "shoutout", "great service", "goodservice", "customerservicewin", "thank you", "thanks so much"]
    is_praise = any(p in m_lower for p in praise_signals) and not any(neg in m_lower for neg in ["broken", "never received", "worst", "disappointed", "stolen", "delay", "refund", "not working"])
    if is_praise:
        proposed_intent = "GENERAL_INQUIRY_FEEDBACK"
        proposed_action = "AUTO"
        notes.append(f"Customer expression of praise/compliment misclassified by keyword matching as {orig_intent}; proposed as GENERAL_INQUIRY_FEEDBACK (safe auto-handling).")

    # 2. Callback or general channel inquiry
    elif "call back" in m_lower or "phoning" in m_lower or "contact number" in m_lower:
        if orig_intent == "CANCELLATION_REQUEST":
            proposed_intent = "GENERAL_INQUIRY_FEEDBACK"
            proposed_action = "AUTO"
            notes.append("Customer inquiry regarding phone/call-back channel options; mislabeled as CANCELLATION_REQUEST due to regex heuristic.")

    # 3. Explicit refund disputes / unrefunded items
    elif any(term in m_lower for term in ["nt refunding", "not refunding", "refund my money", "where is my refund", "waiting for refund"]):
        if orig_intent in ["CANCELLATION_REQUEST", "DELIVERY_DELAY"]:
            proposed_intent = "REFUND_NOT_RECEIVED"
            proposed_action = "ESCALATE" if any(agg in m_lower for agg in ["escalate", "mistake", "worst", "month", "immediately"]) else "AUTO"
            notes.append(f"Customer explicitly pursuing unreceived refund; mislabeled as {orig_intent}. Action set to {proposed_action} based on dispute severity.")

    # 4. Return request stuck / return complaint
    elif "return of product" in m_lower or "return request" in m_lower or "how to return" in m_lower:
        if orig_intent in ["DELIVERY_DELAY", "CANCELLATION_REQUEST"]:
            proposed_intent = "RETURN_EXCHANGE_INQUIRY"
            proposed_action = "ESCALATE" if "after a month" in m_lower or "pending" in m_lower else "AUTO"
            notes.append(f"Customer requesting product return/exchange; mislabeled as {orig_intent}. Proposed action reflects resolution state.")

    # 5. Delivery person cancel vs delivery issue
    elif "delivery person cancel" in m_lower or "delivery associate" in m_lower:
        if orig_intent == "CANCELLATION_REQUEST":
            proposed_intent = "DELIVERY_DELAY"
            proposed_action = "AUTO"
            notes.append("Customer reporting carrier cancellation of shipment attempt; classified under DELIVERY_DELAY logistics.")

    # 6. High risk checks: Fraud, Stolen, Compromised, Billing, Security
    fraud_signals = ["stolen", "fraud", "hacked", "unauthorized", "scam", "stealing", "police", "chargeback"]
    if any(f in m_lower for f in fraud_signals):
        proposed_intent = "UNAUTHORIZED_TRANSACTION_FRAUD"
        proposed_action = "ESCALATE"
        notes.append("High-risk unauthorized activity or fraud claim detected. Mandatory human escalation (CRITICAL risk).")

    elif orig_intent in ["PAYMENT_AND_BILLING_ISSUE", "ACCOUNT_ACCESS_SECURITY", "UNAUTHORIZED_TRANSACTION_FRAUD"]:
        proposed_action = "ESCALATE"
        notes.append(f"Regulated financial/security inquiry ({orig_intent}); strict escalation policy enforces human handoff.")

    # 7. Ambiguous messages or fragments
    elif orig_intent == "OTHER" or len(msg.split()) < 4 or any(amb in m_lower for amb in ["something weird", "check dm", "check this"]):
        proposed_intent = "OTHER"
        proposed_action = "ESCALATE"
        notes.append("Ambiguous, truncated, or out-of-domain message lacking sufficient context for safe self-service; requires human routing.")

    # 8. Standard auto-eligible cases
    else:
        # Standard tracking or delivery delay
        if orig_intent in ["ORDER_TRACKING_STATUS", "DELIVERY_DELAY", "RETURN_EXCHANGE_INQUIRY", "DIGITAL_SERVICES_AND_DEVICE"]:
            proposed_action = "AUTO"
            notes.append(f"Standard self-service support inquiry for {orig_intent}; eligible for automated guidance with link precedent.")
        elif orig_intent in ["PACKAGE_DELIVERED_NOT_RECEIVED", "DAMAGED_OR_DEFECTIVE_ITEM", "WRONG_ITEM_RECEIVED"]:
            proposed_action = "AUTO"
            notes.append(f"Standard order exception ({orig_intent}); self-service return/troubleshooting link is safe baseline.")
        else:
            proposed_action = orig_action
            notes.append(f"Standard inquiry for {orig_intent}; baseline expected action: {proposed_action}.")

    rationale = " | ".join(notes) if notes else f"Stratified benchmark inquiry for {proposed_intent} ({group})."
    
    return {
        "dataset_heuristic_intent": orig_intent,
        "proposed_intent": proposed_intent,
        "dataset_heuristic_action": orig_action,
        "proposed_action": proposed_action,
        "audit_status": "PENDING_HUMAN_REVIEW",
        "reviewer_rationale_notes": rationale
    }

def main():
    print("Building reviewer-ready Golden Set Audit artifacts...")
    csv_path = "data/golden_set.csv"
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Missing {csv_path}")

    df = pd.read_csv(csv_path)
    with open("configs/intents.yaml", "r", encoding="utf-8") as f:
        tax_cfg = yaml.safe_load(f)

    audit_results = []
    for _, row in df.iterrows():
        aud = audit_record(row, tax_cfg)
        audit_results.append(aud)

    df_aud = pd.DataFrame(audit_results)

    # 1. Save detailed Reviewer CSV with all comparative columns
    df_review = pd.concat([df[["sample_index", "conversation_id", "customer_message", "risk_level", "sampling_group", "reference_resolution"]], df_aud], axis=1)
    
    review_path = "data/golden_set_review.csv"
    df_review.to_csv(review_path, index=False, encoding="utf-8")
    print(f"Saved reviewer audit template with {len(df_review)} rows to {review_path}")

    # 2. Update golden_set.csv and golden_set.jsonl with clean vetted proposed fields
    df_golden = df.copy()
    df_golden["intent"] = df_aud["proposed_intent"]
    df_golden["expected_action"] = df_aud["proposed_action"]
    df_golden["dataset_heuristic_intent"] = df_aud["dataset_heuristic_intent"]
    df_golden["dataset_heuristic_action"] = df_aud["dataset_heuristic_action"]
    df_golden["audit_status"] = "PENDING_HUMAN_REVIEW"
    df_golden["reviewer_rationale_notes"] = df_aud["reviewer_rationale_notes"]

    df_golden.to_csv("data/golden_set.csv", index=False, encoding="utf-8")
    df_golden.to_json("data/golden_set.jsonl", orient="records", lines=True, force_ascii=False)
    print("Updated data/golden_set.csv and data/golden_set.jsonl with proposed annotations (status: PENDING_HUMAN_REVIEW).")

    # Log summary statistics
    changed_intents = (df_aud["dataset_heuristic_intent"] != df_aud["proposed_intent"]).sum()
    changed_actions = (df_aud["dataset_heuristic_action"] != df_aud["proposed_action"]).sum()
    print(f"\nAudit Summary:")
    print(f"  - Total Golden Examples: {len(df_golden)}")
    print(f"  - Proposed Intent Adjustments: {changed_intents} ({(changed_intents/len(df_golden))*100:.1f}%)")
    print(f"  - Proposed Action Adjustments: {changed_actions} ({(changed_actions/len(df_golden))*100:.1f}%)")
    print(f"  - Audit Status: All {len(df_golden)} records marked 'PENDING_HUMAN_REVIEW'")
    print(f"\nProposed Expected Actions Breakdown:")
    print(df_golden["expected_action"].value_counts())
    print(f"\nProposed Intent Breakdown:")
    print(df_golden["intent"].value_counts())

if __name__ == "__main__":
    main()
