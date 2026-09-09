"""
api/main.py
FastAPI backend service for the AI Customer Support Agent (Milestone 17).
Provides:
- POST /api/support/analyze: Full pipeline (Intent + Confidence, FAISS Retrieval, Grounded Response, Trust Gate Decision & Audit Trail)
- GET /api/support/metrics: Pre-computed evaluation metrics and baseline comparisons
- GET /api/support/examples: Curated customer inquiries for live demonstration
- GET /api/health: Service status
"""

import os
import sys
import json
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.intents.classifier import RetrievalAugmentedClassifier, TfidfLogisticClassifier
from src.retrieval.embeddings import CaseEmbedder
from src.retrieval.index import VectorIndex
from src.retrieval.retriever import CaseRetriever
from src.escalation.policy import TrustGatePolicy
from src.generation.responder import GroundedResponder

app = FastAPI(
    title="AI Customer Support Agent API",
    description="Grounded AI Support Agent with FAISS Precedent Retrieval and Multi-Signal Trust Gate",
    version="1.0.0"
)

# Enable CORS for local dev and frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model state
state: Dict[str, Any] = {}

class AnalyzeRequest(BaseModel):
    message: str

class AnalyzeResponse(BaseModel):
    intent: Dict[str, Any]
    evidence: List[Dict[str, Any]]
    response: Dict[str, Any]
    decision: Dict[str, Any]
    audit_trail: List[Dict[str, Any]]

@app.on_event("startup")
def load_models():
    print("Loading AI Support models on startup...")
    # Load classifiers
    retrieval_clf = RetrievalAugmentedClassifier()
    retrieval_clf.load("data/retrieval_classifier.npz")
    state["classifier"] = retrieval_clf

    # Load FAISS index & retriever
    embedder = CaseEmbedder()
    v_index = VectorIndex()
    v_index.load("data/faiss_index.bin", "data/faiss_metadata.parquet")
    retriever = CaseRetriever(embedder=embedder, index=v_index)
    state["retriever"] = retriever

    # Policy & Responder
    state["policy"] = TrustGatePolicy(confidence_threshold=0.75, similarity_threshold=0.62)
    state["responder"] = GroundedResponder(brand_name="AmazonHelp")
    print("All AI Support models loaded successfully!")

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "brand": "AmazonHelp", "models_loaded": "classifier" in state}

@app.post("/api/support/analyze", response_model=AnalyzeResponse)
def analyze_inquiry(req: AnalyzeRequest):
    message = req.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Inquiry message cannot be empty.")

    classifier: RetrievalAugmentedClassifier = state.get("classifier")
    retriever: CaseRetriever = state.get("retriever")
    policy: TrustGatePolicy = state.get("policy")
    responder: GroundedResponder = state.get("responder")

    if not classifier or not retriever:
        raise HTTPException(status_code=503, detail="Models are initializing. Please retry shortly.")

    # 1. Intent Classification with Confidence
    pred_res = classifier.predict(message)
    intent_name = pred_res["intent"]
    confidence = pred_res["confidence"]

    # 2. Historical Case Retrieval via FAISS
    ret_res = retriever.retrieve(message, top_k=5)
    cases = ret_res["cases"]

    # 3. Grounded Response Generation
    resp_res = responder.generate_response(message, intent_name, cases, confidence)
    unsupported_detected = not resp_res["is_grounded"]

    # 4. Multi-Signal Trust Gate Evaluation
    gate_res = policy.evaluate(
        intent=intent_name,
        confidence=confidence,
        retrieval_data=ret_res,
        unsupported_claims_detected=unsupported_detected
    )

    evidence_summary = []
    for c in cases[:3]:
        evidence_summary.append({
            "case_id": c["case_id"],
            "similarity": c["similarity"],
            "intent": c["intent"],
            "customer_inquiry": c["customer_inquiry"],
            "brand_resolution": c["brand_resolution"]
        })

    return {
        "intent": {
            "name": intent_name,
            "confidence": confidence,
            "top_similarity": pred_res.get("top_similarity", 0.0),
            "consensus": pred_res.get("consensus", 0.0)
        },
        "evidence": evidence_summary,
        "response": {
            "text": resp_res["text"],
            "is_grounded": resp_res["is_grounded"],
            "brand": resp_res["brand"],
            "source": resp_res["source"]
        },
        "decision": {
            "action": gate_res["action"],
            "reason_code": gate_res["reason_code"],
            "reason": gate_res["reason"]
        },
        "audit_trail": gate_res["audit_trail"]
    }

@app.get("/api/support/metrics")
def get_evaluation_metrics():
    eval_file = "data/evaluation_results.json"
    if os.path.exists(eval_file):
        with open(eval_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"status": "Evaluation pending"}

@app.get("/api/support/examples")
def get_demo_examples():
    return [
        {
            "category": "Standard Safe Inquiries (Auto-Handled)",
            "message": "Where is my package? The tracking number says in transit but hasn't updated in 2 days.",
            "expected_intent": "ORDER_TRACKING_STATUS",
            "expected_action": "AUTO"
        },
        {
            "category": "Standard Safe Inquiries (Auto-Handled)",
            "message": "My order was supposed to arrive yesterday and is now delayed. Can you help?",
            "expected_intent": "DELIVERY_DELAY",
            "expected_action": "AUTO"
        },
        {
            "category": "Standard Safe Inquiries (Auto-Handled)",
            "message": "How do I return this sweater that is too small? Can I drop it off at a locker?",
            "expected_intent": "RETURN_EXCHANGE_INQUIRY",
            "expected_action": "AUTO"
        },
        {
            "category": "Ambiguous / Low Confidence (Escalated)",
            "message": "Hey someone check this thing right now it looks weird.",
            "expected_intent": "OTHER",
            "expected_action": "ESCALATE",
            "expected_reason": "LOW_CONFIDENCE"
        },
        {
            "category": "Financial Dispute (Escalated to Human)",
            "message": "I see two separate $75 charges on my card for the same order! Please refund the duplicate one immediately.",
            "expected_intent": "PAYMENT_AND_BILLING_ISSUE",
            "expected_action": "ESCALATE",
            "expected_reason": "PAYMENT_DISPUTE"
        },
        {
            "category": "Critical Security & Fraud (Escalated to Human)",
            "message": "My credit card was stolen and someone placed a $500 order on Amazon without my permission!",
            "expected_intent": "UNAUTHORIZED_TRANSACTION_FRAUD",
            "expected_action": "ESCALATE",
            "expected_reason": "HIGH_RISK"
        }
    ]

# Serve frontend static assets
if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
