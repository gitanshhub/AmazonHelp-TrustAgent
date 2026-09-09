"""
scripts/run_evaluation.py
Executes Milestone 16, 23, 24, 25, 26, 27, 28:
Runs comprehensive evaluation on the completely unseen TEST set:
1. Intent Classification: Baseline (TF-IDF) vs Production (Retrieval-Augmented)
2. Retrieval Quality: Recall@1, Recall@3, Recall@5, MRR
3. Safety & Trust Gate: False Auto-Handling Rate, False Escalation Rate, Automation Rate
4. Selective Prediction: Accuracy vs Automation Rate across confidence thresholds
Saves results to data/evaluation_results.json.
"""

import os
import sys
import json
import time
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.intents.classifier import TfidfLogisticClassifier, RetrievalAugmentedClassifier
from src.retrieval.embeddings import CaseEmbedder
from src.retrieval.index import VectorIndex
from src.retrieval.retriever import CaseRetriever
from src.escalation.policy import TrustGatePolicy
from src.generation.responder import GroundedResponder
from src.evaluation.classification import evaluate_classifier
from src.evaluation.retrieval import evaluate_retrieval
from src.evaluation.escalation import evaluate_escalation

def main():
    start_time = time.time()
    test_path = "data/test_conversations.parquet"
    print(f"Loading unseen test set from {test_path}...")
    df_test = pd.read_parquet(test_path)
    print(f"Loaded {len(df_test):,} unseen test conversations.")

    # 1. Load Classifiers & Models
    print("\n--- Loading Classifiers and FAISS Knowledge Base ---")
    tfidf_clf = TfidfLogisticClassifier()
    tfidf_clf.load("data/tfidf_classifier.pkl")

    retrieval_clf = RetrievalAugmentedClassifier()
    retrieval_clf.load("data/retrieval_classifier.npz")

    embedder = CaseEmbedder()
    vector_index = VectorIndex()
    vector_index.load("data/faiss_index.bin", "data/faiss_metadata.parquet")
    retriever = CaseRetriever(embedder=embedder, index=vector_index)

    policy = TrustGatePolicy(confidence_threshold=0.75, similarity_threshold=0.62)
    responder = GroundedResponder(brand_name="AmazonHelp")

    # 2. Run Evaluation on Test Set
    test_queries = df_test["customer_inquiry"].tolist()
    ground_truth_intents = df_test["intent"].tolist()

    print(f"\nEvaluating models on {len(test_queries):,} test cases...")
    tfidf_preds = []
    retrieval_preds = []
    retrieval_confs = []
    retrieval_outputs = []
    decisions = []
    reason_codes = []
    must_escalate_labels = []
    unsupported_claim_count = 0

    high_risk_intents = {"UNAUTHORIZED_TRANSACTION_FRAUD", "PAYMENT_AND_BILLING_ISSUE", "ACCOUNT_ACCESS_SECURITY", "OTHER"}

    for idx, (query, true_intent) in enumerate(zip(test_queries, ground_truth_intents)):
        # Baseline 1
        tf_pred, _ = tfidf_clf.predict(query)
        tfidf_preds.append(tf_pred)

        # Production Retrieval-Augmented
        pred_res = retrieval_clf.predict(query)
        pred_intent = pred_res["intent"]
        confidence = pred_res["confidence"]
        retrieval_preds.append(pred_intent)
        retrieval_confs.append(confidence)

        # Retrieve historical resolution cases
        ret_res = retriever.retrieve(query, top_k=5)
        retrieval_outputs.append(ret_res)

        # Generate grounded response
        resp = responder.generate_response(query, pred_intent, ret_res["cases"], confidence)
        is_unsupported = not resp["is_grounded"]
        if is_unsupported:
            unsupported_claim_count += 1

        # Ground truth escalation requirement
        # Should escalate if intent is high-risk or ambiguous (OTHER)
        must_escalate = (true_intent in high_risk_intents)
        must_escalate_labels.append(must_escalate)

        # Trust Gate decision
        gate_res = policy.evaluate(pred_intent, confidence, ret_res, unsupported_claims_detected=is_unsupported)
        decisions.append(gate_res["action"])
        reason_codes.append(gate_res["reason_code"])

        if (idx + 1) % 500 == 0:
            print(f"Evaluated {idx + 1:,} test cases...")

    # 3. Compute Metrics
    print("\n" + "="*80)
    print("EVALUATION RESULTS REPORT")
    print("="*80)

    # Intent Classification Metrics
    tfidf_metrics = evaluate_classifier(tfidf_preds, ground_truth_intents)
    prod_metrics = evaluate_classifier(retrieval_preds, ground_truth_intents)

    print(f"\n[1. Intent Classification]")
    print(f"Baseline (TF-IDF + Logistic Reg)  -> Accuracy: {tfidf_metrics['accuracy']:.4f} | Macro F1: {tfidf_metrics['macro_f1']:.4f}")
    print(f"Production (Retrieval-Augmented) -> Accuracy: {prod_metrics['accuracy']:.4f} | Macro F1: {prod_metrics['macro_f1']:.4f}")

    # Retrieval Metrics
    retrieval_metrics = evaluate_retrieval(retrieval_outputs, ground_truth_intents)
    print(f"\n[2. Historical Resolution Retrieval]")
    print(f"Recall@1: {retrieval_metrics['recall_at_1']:.4f}")
    print(f"Recall@3: {retrieval_metrics['recall_at_3']:.4f}")
    print(f"Recall@5: {retrieval_metrics['recall_at_5']:.4f}")
    print(f"MRR:      {retrieval_metrics['mrr']:.4f}")

    # Trust Gate / Escalation Metrics
    safety_metrics = evaluate_escalation(decisions, must_escalate_labels)
    print(f"\n[3. Trust Gate & Safety Policy]")
    print(f"Automation Rate:             {safety_metrics['automation_rate'] * 100:.1f}%")
    print(f"Unsafe Auto-Handling Rate:   {safety_metrics['unsafe_auto_handling_rate'] * 100:.2f}% (Safety Critical)")
    print(f"Unnecessary Escalation Rate: {safety_metrics['unnecessary_escalation_rate'] * 100:.1f}%")
    print(f"Escalation Precision:        {safety_metrics['escalation_precision']:.4f}")
    print(f"Escalation Recall:           {safety_metrics['escalation_recall']:.4f}")

    # Hallucination / Unsupported Claim Rate
    unsupported_rate = unsupported_claim_count / len(test_queries)
    print(f"\n[4. Groundedness / Hallucination]")
    print(f"Unsupported Claim Rate:   {unsupported_rate * 100:.2f}%")

    # Selective Prediction Curve across confidence thresholds
    print(f"\n[5. Selective Prediction Analysis (Automation vs Accuracy)]")
    selective_curve = []
    for th in [0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90]:
        auto_mask = [c >= th and p not in high_risk_intents for c, p in zip(retrieval_confs, retrieval_preds)]
        auto_cnt = sum(auto_mask)
        auto_rate = auto_cnt / len(test_queries)
        if auto_cnt > 0:
            auto_acc = sum(p == t for p, t, m in zip(retrieval_preds, ground_truth_intents, auto_mask) if m) / auto_cnt
        else:
            auto_acc = 1.0
        selective_curve.append({
            "threshold": th,
            "automation_rate": round(auto_rate, 4),
            "safe_accuracy": round(auto_acc, 4)
        })
        print(f"Threshold >= {th:.2f} -> Automation Rate: {auto_rate*100:5.1f}% | Accuracy on Automated: {auto_acc*100:5.1f}%")

    # Reason code distribution
    reason_code_counts = pd.Series(reason_codes).value_counts().to_dict()
    print(f"\nEscalation Reason Code Distribution: {reason_code_counts}")

    results_payload = {
        "dataset_size": len(test_queries),
        "intent_classification": {
            "baseline_tfidf": tfidf_metrics,
            "production_retrieval": prod_metrics
        },
        "retrieval": retrieval_metrics,
        "trust_gate_safety": safety_metrics,
        "unsupported_claim_rate": round(unsupported_rate, 4),
        "selective_prediction_curve": selective_curve,
        "escalation_reason_codes": reason_code_counts
    }

    out_file = "data/evaluation_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results_payload, f, indent=2)
    print(f"\nSaved comprehensive evaluation report to {out_file} in {time.time() - start_time:.1f}s!")

if __name__ == "__main__":
    main()
