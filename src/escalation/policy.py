"""
src/escalation/policy.py
Implements the multi-signal Trust Gate and Escalation Policy (Milestones 14, 15, 20).
Combines classification confidence, retrieval quality, intent risk level, account-action requirements,
and groundedness checks to determine whether to AUTO-HANDLE or ESCALATE TO HUMAN.
"""

from typing import Dict, Any, List, Optional
from src.intents.taxonomy import IntentTaxonomy

class TrustGatePolicy:
    def __init__(
        self,
        confidence_threshold: float = 0.75,
        similarity_threshold: float = 0.62,
        taxonomy_path: str = "configs/intents.yaml"
    ):
        self.confidence_threshold = confidence_threshold
        self.similarity_threshold = similarity_threshold
        self.taxonomy = IntentTaxonomy(taxonomy_path)

    def evaluate(
        self,
        intent: str,
        confidence: float,
        retrieval_data: Dict[str, Any],
        unsupported_claims_detected: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluates all safety and reliability signals to decide AUTO vs ESCALATE.
        Returns decision, reason_code, explanation, and an audit trail for the 'Why?' section.
        """
        audit_trail: List[Dict[str, Any]] = []
        
        risk_level = self.taxonomy.get_risk_level(intent)
        is_auto_eligible = self.taxonomy.is_auto_eligible(intent)
        top_similarity = retrieval_data.get("top_similarity", 0.0)
        has_strong_evidence = retrieval_data.get("has_strong_evidence", False)
        cases = retrieval_data.get("cases", [])

        # 1. Check: Intent Risk & Financial / Security Disputes
        if risk_level == "CRITICAL" or intent == "UNAUTHORIZED_TRANSACTION_FRAUD":
            audit_trail.append({"check": "Risk Assessment", "status": "FAIL", "detail": "Critical fraud or security issue detected."})
            return {
                "action": "ESCALATE",
                "reason_code": "HIGH_RISK",
                "reason": "Security or fraudulent activity reports must be handled immediately by human fraud specialists.",
                "audit_trail": audit_trail
            }
        elif intent == "PAYMENT_AND_BILLING_ISSUE":
            audit_trail.append({"check": "Payment Verification", "status": "FAIL", "detail": "Financial / billing dispute requiring transaction lookup."})
            return {
                "action": "ESCALATE",
                "reason_code": "PAYMENT_DISPUTE",
                "reason": "Financial discrepancies and duplicate charges require specialized human verification.",
                "audit_trail": audit_trail
            }
        elif intent == "ACCOUNT_ACCESS_SECURITY":
            audit_trail.append({"check": "Account Access Check", "status": "FAIL", "detail": "Account recovery or OTP credential action required."})
            return {
                "action": "ESCALATE",
                "reason_code": "ACCOUNT_SPECIFIC_ACTION",
                "reason": "Account recovery and credential resets require human-verified authentication.",
                "audit_trail": audit_trail
            }
        else:
            audit_trail.append({"check": "Risk Assessment", "status": "PASS", "detail": f"Intent {intent} is categorized as {risk_level} risk."})

        # 2. Check: Classification Confidence Threshold
        conf_passed = confidence >= self.confidence_threshold
        if not conf_passed or intent == "OTHER":
            audit_trail.append({"check": "Classification Confidence", "status": "FAIL", "detail": f"Confidence {confidence:.2f} is below threshold {self.confidence_threshold:.2f}."})
            return {
                "action": "ESCALATE",
                "reason_code": "LOW_CONFIDENCE",
                "reason": f"Predicted intent confidence ({confidence:.1%}) is insufficient for autonomous handling.",
                "audit_trail": audit_trail
            }
        audit_trail.append({"check": "Classification Confidence", "status": "PASS", "detail": f"Confidence {confidence:.2f} satisfies >= {self.confidence_threshold:.2f}."})

        # 3. Check: Historical Retrieval Relevance & Evidence
        retrieval_passed = top_similarity >= self.similarity_threshold and len(cases) > 0
        if not retrieval_passed:
            audit_trail.append({"check": "Historical Case Evidence", "status": "FAIL", "detail": f"Top similarity {top_similarity:.2f} is below relevance threshold {self.similarity_threshold:.2f}."})
            return {
                "action": "ESCALATE",
                "reason_code": "NO_SIMILAR_CASE",
                "reason": "No historically verified precedent with sufficient similarity was found to ground the response.",
                "audit_trail": audit_trail
            }
        audit_trail.append({"check": "Historical Case Evidence", "status": "PASS", "detail": f"Found {len(cases)} similar historical cases (top similarity: {top_similarity:.2f})."})

        # 4. Check: Unsupported Claims / Hallucination Detection
        if unsupported_claims_detected:
            audit_trail.append({"check": "Groundedness Verification", "status": "FAIL", "detail": "Draft response contained claims unsupported by retrieved cases."})
            return {
                "action": "ESCALATE",
                "reason_code": "CONFLICTING_EVIDENCE",
                "reason": "Response verification flagged potential unsupported claims.",
                "audit_trail": audit_trail
            }
        audit_trail.append({"check": "Groundedness Verification", "status": "PASS", "detail": "Response draft is fully grounded in historical brand precedents."})

        # 5. Check: Auto-Eligibility Flag in Taxonomy
        if not is_auto_eligible:
            audit_trail.append({"check": "Policy Eligibility", "status": "FAIL", "detail": "Intent is configured to require agent review."})
            return {
                "action": "ESCALATE",
                "reason_code": "ACCOUNT_SPECIFIC_ACTION",
                "reason": "Brand policy designates this inquiry type for human agent handling.",
                "audit_trail": audit_trail
            }
        audit_trail.append({"check": "Policy Eligibility", "status": "PASS", "detail": "Inquiry qualifies for automated self-service guidance."})

        # ALL CHECKS PASSED -> AUTO-HANDLE
        return {
            "action": "AUTO",
            "reason_code": "CONFIDENT_GROUNDED",
            "reason": "High intent confidence, strong historical grounding, and standard low-risk inquiry.",
            "audit_trail": audit_trail
        }
