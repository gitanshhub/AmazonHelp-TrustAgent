"""
src/generation/responder.py
Grounded response generator strictly adhering to historical brand resolutions.
Prioritizes historically retrieved precedents over static templates.
Enforces anti-hallucination policies: prohibits fake backend actions, invented refunds, or false claims.
"""

import re
from typing import Dict, Any, List, Optional

# Forbidden phrases that represent hallucinated system capabilities
FORBIDDEN_PROMISE_PATTERNS = [
    re.compile(r'\b(i have|i\'ve) (refunded|issued|canceled|cancelled|processed the refund)\b', re.IGNORECASE),
    re.compile(r'\b(i have|i\'ve) (credited|accessed your account|reset your password)\b', re.IGNORECASE),
    re.compile(r'\b(i have|i\'ve) (updated your address|reshipped|sent a replacement)\b', re.IGNORECASE),
    re.compile(r'\b(we have issued a full refund of \$\d+)\b', re.IGNORECASE),
]

# Conservative fallback guidance used only when no relevant historical precedent exists
CONSERVATIVE_FALLBACK_TEMPLATES = {
    "ORDER_TRACKING_STATUS": "You can check real-time carrier tracking and transit updates directly under 'Your Orders' here: [LINK]. If tracking shows no movement, please reach out with your order details so our team can investigate.",
    "DELIVERY_DELAY": "We apologize for the delivery delay. Carrier updates and revised delivery estimates can be reviewed via your tracking link: [LINK]. If your parcel does not arrive within the revised window, please contact support for further assistance.",
    "PACKAGE_DELIVERED_NOT_RECEIVED": "If your tracking indicates delivered but the parcel has not arrived, carriers occasionally mark packages early or place them in secure areas nearby. Please check around your delivery location. If it has not arrived by tomorrow, please contact support with your order number.",
    "DAMAGED_OR_DEFECTIVE_ITEM": "We are very sorry your item arrived damaged. You can initiate a replacement or return request directly through our Online Returns Center at [LINK].",
    "WRONG_ITEM_RECEIVED": "We apologize for the incorrect item. You can arrange a return and replacement through 'Your Orders' at [LINK] by selecting 'Wrong item sent'.",
    "REFUND_NOT_RECEIVED": "Refund status and processing timelines can be reviewed directly under your order invoice and payment details at [LINK].",
    "RETURN_EXCHANGE_INQUIRY": "To review return eligibility and generate a return shipping label or QR drop-off code, please visit our Returns Center at [LINK].",
    "CANCELLATION_REQUEST": "Order cancellation requests can be submitted through 'Your Orders' at [LINK] if the order has not yet entered dispatch. Once dispatched, you may return the item upon arrival.",
    "PRIME_MEMBERSHIP_INQUIRY": "For inquiries regarding Amazon Prime membership, benefits, or billing settings, you can manage your membership preferences at [LINK].",
    "DIGITAL_SERVICES_AND_DEVICE": "For digital services and device support, please verify your network connection, ensure your app is updated to the latest version, or consult our Digital Services Help Center at [LINK]."
}

class GroundedResponder:
    def __init__(self, brand_name: str = "AmazonHelp"):
        self.brand_name = brand_name

    def validate_groundedness(self, draft_text: str) -> bool:
        """
        Scans draft for forbidden capability hallucinations.
        Returns True if safe and grounded, False if hallucinated actions detected.
        """
        for pattern in FORBIDDEN_PROMISE_PATTERNS:
            if pattern.search(draft_text):
                return False
        return True

    def generate_response(
        self,
        customer_message: str,
        intent: str,
        retrieved_cases: List[Dict[str, Any]],
        confidence: float
    ) -> Dict[str, Any]:
        """
        Synthesizes a precedent-grounded response.
        PRIMARY: Grounded directly in the top retrieved historical precedent resolution.
        FALLBACK: Used ONLY when no relevant historical precedent exists.
        """
        draft: Optional[str] = None
        source_type: str = "fallback_escalation"
        source_case_ids: List[str] = []
        top_sim: float = 0.0

        # 1. Primary Grounding: Extract and adapt top retrieved historical precedent
        if retrieved_cases and len(retrieved_cases) > 0:
            top_case = retrieved_cases[0]
            top_sim = float(top_case.get("similarity", 0.0))
            hist_resolution = str(top_case.get("brand_resolution", "")).strip()
            case_id = str(top_case.get("case_id", top_case.get("conversation_id", "")))

            # Use historical resolution if similarity is sufficient and text is non-trivial
            if top_sim >= 0.55 and len(hist_resolution) > 15:
                draft = hist_resolution
                source_type = "retrieved_historical_case"
                if case_id:
                    source_case_ids = [case_id]

        # 2. Fallback: Used only when no usable historical precedent exists
        if not draft:
            if intent in CONSERVATIVE_FALLBACK_TEMPLATES:
                draft = CONSERVATIVE_FALLBACK_TEMPLATES[intent]
                source_type = "conservative_fallback_template"
            else:
                draft = "Thank you for contacting support. To ensure your request is handled securely, please reach out with your order details at [LINK] so a specialist can assist you."
                source_type = "fallback_escalation"

        # 3. Post-generation Groundedness & Anti-Hallucination Validation
        is_grounded = self.validate_groundedness(draft)

        return {
            "text": draft,
            "is_grounded": is_grounded,
            "brand": self.brand_name,
            "source": source_type,
            "source_case_ids": source_case_ids,
            "grounding_similarity": round(top_sim, 4)
        }
