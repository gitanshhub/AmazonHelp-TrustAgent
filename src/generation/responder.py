"""
src/generation/responder.py
Grounded response generator strictly adhering to historical brand resolutions.
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

# Standard grounded response templates adapted from historical AmazonHelp resolutions
GROUNDED_INTENT_TEMPLATES = {
    "ORDER_TRACKING_STATUS": "I'd be glad to help check on your shipment. You can track real-time carrier updates directly under 'Your Orders' here: [LINK]. If tracking shows no movement for 48 hours, please send us a DM with your order details so we can investigate.",
    "DELIVERY_DELAY": "We're sorry for the delay in receiving your package. Shipments may occasionally experience transit delays due to carrier volume. Please check your tracking link for the revised delivery window: [LINK]. If it has not arrived within 24 hours of the revised date, reach out via DM so our team can assist.",
    "PACKAGE_DELIVERED_NOT_RECEIVED": "We understand how concerning it is when tracking shows delivered but the parcel isn't there. Carriers occasionally mark items delivered a few hours early or place them in secure porch/neighbor areas. Please check around your delivery location and with neighbors. If it still hasn't turned up by end of day tomorrow, send us a DM with your order number.",
    "DAMAGED_OR_DEFECTIVE_ITEM": "We're very sorry to hear your item arrived in that condition. You can request a free replacement or return label directly through our Online Returns Center at [LINK]. Select your order and choose 'Item arrived damaged'. If you run into any trouble, please let us know!",
    "WRONG_ITEM_RECEIVED": "We apologize for the mix-up with your order! You can arrange an immediate return and replacement through 'Your Orders' at [LINK] by selecting 'Wrong item sent'. Our team will ship the correct item promptly once initiated.",
    "REFUND_NOT_RECEIVED": "We understand you're waiting for your refund. Refunds typically take 3-5 business days to post to your original payment method once processed by our fulfillment center. You can view the exact refund status under your order invoice: [LINK].",
    "RETURN_EXCHANGE_INQUIRY": "Returning or exchanging an item is straightforward. Visit our Returns Center at [LINK], select the item, and print your prepaid return shipping label or choose a QR code drop-off location. Return windows are typically 30 days from delivery.",
    "CANCELLATION_REQUEST": "You can request to cancel an order directly from 'Your Orders' at [LINK] as long as it has not entered the shipping process. If the order has already dispatched, you can simply refuse the delivery or return it once it arrives for a full refund.",
    "PRIME_MEMBERSHIP_INQUIRY": "For inquiries regarding Amazon Prime membership, benefits, or subscription management, you can review and manage your settings anytime under 'Manage Prime Membership' at [LINK].",
    "DIGITAL_SERVICES_AND_DEVICE": "For digital streaming or device issues, we recommend restarting your device, ensuring the app is updated to the latest version, and verifying your network connection. Detailed troubleshooting steps are available at our Help Center: [LINK]."
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
        Synthesizes a brand-consistent grounded response.
        If strong historical precedent exists, aligns with the proven resolution.
        """
        # Select best template or historical resolution reference
        if intent in GROUNDED_INTENT_TEMPLATES:
            draft = GROUNDED_INTENT_TEMPLATES[intent]
        elif retrieved_cases and retrieved_cases[0]["similarity"] >= 0.70:
            # Adapt the historically proven response
            hist_resolution = retrieved_cases[0]["brand_resolution"]
            draft = f"Thanks for reaching out. Based on our support guidelines: {hist_resolution}"
        else:
            draft = "Thank you for contacting customer support. We want to ensure this is handled properly. Please DM us your order details or reach out to our support team at [LINK] so a specialist can assist you."

        is_grounded = self.validate_groundedness(draft)
        
        return {
            "text": draft,
            "is_grounded": is_grounded,
            "brand": self.brand_name,
            "source": "grounded_template" if intent in GROUNDED_INTENT_TEMPLATES else "retrieved_historical_case"
        }
