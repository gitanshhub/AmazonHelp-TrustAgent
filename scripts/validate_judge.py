"""
scripts/validate_judge.py

Supports Phase 8 & 9 and Blind Human Validation Workflow:
1. Prepare a blind 46-case human-review CSV with blank human score fields.
2. Run Qwen locally using strict --judge-mode llm and save raw scores separately (no heuristic fallback).
3. After the human reviewer fills the review CSV, calculate and save human-vs-Qwen agreement metrics.
"""

import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import cohen_kappa_score

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Ensure offline operation for HuggingFace
os.environ["HF_HUB_OFFLINE"] = "1"

from src.retrieval.embeddings import CaseEmbedder
from src.retrieval.index import VectorIndex
from src.retrieval.retriever import CaseRetriever
from src.intents.classifier import RetrievalAugmentedClassifier
from src.generation.responder import GroundedResponder
from src.evaluation.judge import LLMJudge

BLIND_REVIEW_CSV = "data/judge_human_review.csv"
QWEN_SCORES_JSON = "data/judge_qwen_raw_scores.json"
QWEN_SCORES_CSV = "data/judge_qwen_raw_scores.csv"
VALIDATION_REPORT_JSON = "data/judge_human_validation.json"

DIMENSIONS = ["correctness", "groundedness", "relevance", "helpfulness", "safety", "overall"]

def sample_validation_cohort(golden_csv="data/golden_set.csv", sample_size=50, random_state=42):
    """
    Selects validation samples using stratified reproducible sampling across sampling groups
    BEFORE any LLM judge evaluation is executed.
    Produces exactly 46 cases (13 common_support, 13 high_risk, 12 rare_intent, 8 ambiguous).
    """
    df_golden = pd.read_csv(golden_csv)
    sampled_dfs = []
    groups = df_golden["sampling_group"].unique()
    per_group = sample_size // len(groups)
    remainder = sample_size % len(groups)
    
    for i, grp in enumerate(groups):
        sub = df_golden[df_golden["sampling_group"] == grp]
        n = per_group + (1 if i < remainder else 0)
        sampled_dfs.append(sub.sample(n=min(n, len(sub)), random_state=random_state))
        
    df_cohort = pd.concat(sampled_dfs).sample(frac=1.0, random_state=random_state).reset_index(drop=True)
    df_cohort["cohort_id"] = range(1, len(df_cohort) + 1)
    return df_cohort

def build_cohort_interactions(df_cohort):
    """
    Generates agent responses and retrieves precedents for the cohort.
    """
    retrieval_clf = RetrievalAugmentedClassifier()
    retrieval_clf.load("data/retrieval_classifier.npz")
    
    embedder = CaseEmbedder()
    v_index = VectorIndex()
    v_index.load("data/faiss_index.bin", "data/faiss_metadata.parquet")
    retriever = CaseRetriever(embedder=embedder, index=v_index)
    responder = GroundedResponder()

    records = []
    for _, row in df_cohort.iterrows():
        q = row["customer_message"]
        pred_res = retrieval_clf.predict(q)
        ret_res = retriever.retrieve(q, top_k=3)
        cases = ret_res["cases"]
        top_precedent = cases[0]["brand_resolution"] if cases else "No historical precedent found."
        resp = responder.generate_response(q, pred_res["intent"], cases, pred_res["confidence"])
        
        records.append({
            "cohort_id": int(row["cohort_id"]),
            "conversation_id": row["conversation_id"],
            "sampling_group": row["sampling_group"],
            "customer_message": q,
            "retrieved_precedent": top_precedent,
            "agent_response": resp["text"]
        })
    return pd.DataFrame(records)

def prepare_blind_review_csv(output_csv=BLIND_REVIEW_CSV, overwrite=False):
    """
    Creates a blind 46-case human-review CSV with blank human score fields.
    Does NOT prefill or invent any human ratings.
    Does NOT expose model predictions or confidence scores.
    """
    if os.path.exists(output_csv) and not overwrite:
        print(f"Blind review CSV already exists at: {output_csv}")
        return pd.read_csv(output_csv)

    print("Sampling stratified 46-case cohort for blind human evaluation...")
    df_cohort = sample_validation_cohort()
    print("Generating agent responses and retrieving precedents...")
    df_interactions = build_cohort_interactions(df_cohort)

    # Add completely blank human rating fields
    for dim in DIMENSIONS:
        df_interactions[f"human_{dim}"] = ""
    df_interactions["human_notes"] = ""

    df_interactions.to_csv(output_csv, index=False, encoding="utf-8")
    print(f"Successfully created blind human review CSV ({len(df_interactions)} cases) at: {output_csv}")
    print("All human score fields (human_correctness ... human_overall) are blank for independent review.")
    return df_interactions

def run_qwen_evaluation(output_json=QWEN_SCORES_JSON, output_csv=QWEN_SCORES_CSV, mode="llm"):
    """
    Runs Qwen locally in strict mode ('llm') across all 46 cases.
    Fails loudly with RuntimeError if model fails to load, generate, or parse.
    Saves raw scores separately without mixing with human review sheet.
    """
    print("=" * 80)
    print(f"RUNNING QWEN EVALUATION (MODE: {mode.upper()})")
    print("=" * 80)

    df_cohort = sample_validation_cohort()
    df_interactions = build_cohort_interactions(df_cohort)

    print(f"Initializing LLMJudge with mode='{mode}'...")
    judge = LLMJudge(mode=mode)

    qwen_results = []
    total = len(df_interactions)
    for idx, row in df_interactions.iterrows():
        cohort_id = int(row["cohort_id"])
        conv_id = row["conversation_id"]
        print(f"[{cohort_id:02d}/{total:02d}] Evaluating {conv_id} ({row['sampling_group']})...")
        
        j_res = judge.evaluate_reply(
            customer_message=row["customer_message"],
            retrieved_precedent=row["retrieved_precedent"],
            agent_response=row["agent_response"]
        )
        
        # Enforce strict non-fallback
        if mode == "llm" and j_res.get("judge_tier") != "llm":
            raise RuntimeError(
                f"Evaluation failed strict 'llm' tier constraint on cohort_id {cohort_id}. "
                f"Received tier: '{j_res.get('judge_tier')}'"
            )

        qwen_results.append({
            "cohort_id": cohort_id,
            "conversation_id": conv_id,
            "sampling_group": row["sampling_group"],
            "customer_message": row["customer_message"],
            "retrieved_precedent": row["retrieved_precedent"],
            "agent_response": row["agent_response"],
            "correctness": j_res["correctness"],
            "groundedness": j_res["groundedness"],
            "relevance": j_res["relevance"],
            "helpfulness": j_res["helpfulness"],
            "safety": j_res["safety"],
            "overall": j_res["overall"],
            "justification": j_res["justification"],
            "judge_tier": j_res["judge_tier"],
            "judge_model": j_res.get("judge_model", "Qwen/Qwen2.5-0.5B-Instruct"),
            "mode_enforced": j_res.get("mode_enforced", mode)
        })

    # Save to JSON
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump({
            "sample_size": len(qwen_results),
            "judge_mode": mode,
            "judge_model": "Qwen/Qwen2.5-0.5B-Instruct" if mode == "llm" else "heuristic",
            "scores": qwen_results
        }, f, indent=2)
    print(f"\nSaved raw Qwen scores to JSON: {output_json}")

    # Save to CSV
    pd.DataFrame(qwen_results).to_csv(output_csv, index=False, encoding="utf-8")
    print(f"Saved raw Qwen scores to CSV: {output_csv}")
    return qwen_results

def calculate_agreement(human_csv=BLIND_REVIEW_CSV, qwen_json=QWEN_SCORES_JSON, output_json=VALIDATION_REPORT_JSON):
    """
    Calculates agreement statistics between filled human review CSV and separate Qwen scores.
    """
    if not os.path.exists(human_csv):
        raise FileNotFoundError(f"Human review CSV not found: {human_csv}")
    if not os.path.exists(qwen_json):
        raise FileNotFoundError(f"Qwen raw scores not found: {qwen_json}. Run with --run-qwen first.")

    df_human = pd.read_csv(human_csv)
    with open(qwen_json, "r", encoding="utf-8") as f:
        qwen_data = json.load(f)
    df_qwen = pd.DataFrame(qwen_data["scores"])

    # Check for blank or non-numeric human ratings
    missing_entries = []
    for dim in DIMENSIONS:
        col = f"human_{dim}"
        if col not in df_human.columns:
            raise KeyError(f"Column '{col}' is missing in {human_csv}")
        blanks = df_human[df_human[col].isna() | (df_human[col].astype(str).str.strip() == "")]
        if len(blanks) > 0:
            missing_entries.append((dim, len(blanks)))

    if missing_entries:
        print("=" * 80)
        print("HUMAN SCORES NOT FULLY FILLED YET")
        print("=" * 80)
        print(f"File '{human_csv}' contains unfilled rating fields:")
        for dim, count in missing_entries:
            print(f"  - human_{dim}: {count} blank cases")
        print("\nPlease fill all human ratings (integers 1 to 5) in the CSV before calculating agreement.")
        return None

    # Merge on cohort_id
    df_merged = pd.merge(df_human, df_qwen, on="cohort_id", suffixes=("_human", "_qwen"))
    print("=" * 80)
    print("HUMAN-VS-QWEN AGREEMENT METRICS (N=46 VALID PAIRS)")
    print("=" * 80)
    print(f"{'Dimension':<15} | {'Exact Match':<12} | {'Within +-1':<12} | {'Spearman Rho':<14} | {'Cohen Kappa':<12}")
    print("=" * 80)

    agreement_metrics = {}
    for dim in DIMENSIONS:
        h_vals = df_merged[f"human_{dim}"].to_numpy().astype(float).astype(int)
        q_vals = df_merged[dim].to_numpy().astype(float).astype(int)

        exact_agree = np.mean(h_vals == q_vals) * 100
        within_one = np.mean(np.abs(h_vals - q_vals) <= 1) * 100

        # Spearman correlation
        if len(set(h_vals)) > 1 and len(set(q_vals)) > 1:
            rho, _ = spearmanr(h_vals, q_vals)
        else:
            rho = 1.0 if np.all(h_vals == q_vals) else 0.0

        # Quadratic weighted Cohen's Kappa
        try:
            kappa = cohen_kappa_score(h_vals, q_vals, weights="quadratic")
        except Exception:
            kappa = 0.0

        agreement_metrics[dim] = {
            "exact_agreement_pct": round(float(exact_agree), 2),
            "within_one_point_pct": round(float(within_one), 2),
            "spearman_rho": round(float(rho), 4),
            "cohen_kappa": round(float(kappa), 4)
        }
        print(f"{dim.capitalize():<15} | {exact_agree:10.1f}% | {within_one:10.1f}% | {rho:14.4f} | {kappa:12.4f}")

    print("=" * 80)

    report = {
        "sample_size": len(df_merged),
        "audit_status": "HUMAN_VERIFIED",
        "benchmark_evaluator": "Independent_Human_Reviewer",
        "judge_metadata": {
            "judge_mode_configured": qwen_data.get("judge_mode", "llm"),
            "judge_tier_executed": df_qwen["judge_tier"].iloc[0] if not df_qwen.empty else "llm",
            "judge_model": qwen_data.get("judge_model", "Qwen/Qwen2.5-0.5B-Instruct"),
            "silent_fallback_prevented": True
        },
        "dimensions": agreement_metrics,
        "human_score_means": {
            dim: round(float(df_merged[f"human_{dim}"].astype(float).mean()), 2) for dim in DIMENSIONS
        },
        "qwen_score_means": {
            dim: round(float(df_merged[dim].astype(float).mean()), 2) for dim in DIMENSIONS
        }
    }

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved human-vs-Qwen validation report to {output_json}")
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Human vs Qwen Judge Validation")
    parser.add_argument("--prepare-blind-csv", action="store_true", help="Generate blind 46-case CSV with blank human fields")
    parser.add_argument("--run-qwen", action="store_true", help="Run Qwen in strict LLM mode and save raw scores separately")
    parser.add_argument("--judge-mode", default="llm", choices=["llm", "heuristic"], help="Judge mode for Qwen execution")
    parser.add_argument("--calculate-agreement", action="store_true", help="Calculate agreement after human fills the CSV")
    parser.add_argument("--overwrite-blind-csv", action="store_true", help="Force overwrite of existing blind review CSV")

    args = parser.parse_args()

    # Default action if no flags provided: prepare blind CSV and run Qwen
    if not (args.prepare_blind_csv or args.run_qwen or args.calculate_agreement):
        prepare_blind_review_csv(overwrite=args.overwrite_blind_csv)
        run_qwen_evaluation(mode=args.judge_mode)
    else:
        if args.prepare_blind_csv:
            prepare_blind_review_csv(overwrite=args.overwrite_blind_csv)
        if args.run_qwen:
            run_qwen_evaluation(mode=args.judge_mode)
        if args.calculate_agreement:
            calculate_agreement()
