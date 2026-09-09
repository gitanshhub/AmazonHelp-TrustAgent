"""
src/intents/taxonomy.py
Manages the intent taxonomy defined in configs/intents.yaml.
Provides lookup for intent definitions, risk levels, and escalation eligibility.
"""

import os
import yaml
from typing import Dict, Any, List, Optional

class IntentTaxonomy:
    def __init__(self, config_path: str = "configs/intents.yaml"):
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Intents configuration not found at {config_path}")
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        self.intents: Dict[str, Dict[str, Any]] = data.get("intents", {})
        self.intent_names: List[str] = list(self.intents.keys())

    def get_description(self, intent: str) -> str:
        return self.intents.get(intent, {}).get("description", "Unknown intent")

    def get_risk_level(self, intent: str) -> str:
        return self.intents.get(intent, {}).get("risk_level", "HIGH")

    def is_auto_eligible(self, intent: str) -> bool:
        return self.intents.get(intent, {}).get("auto_eligible", False)

    def get_escalation_reason_code(self, intent: str) -> Optional[str]:
        return self.intents.get(intent, {}).get("escalation_reason_code", None)

    def get_examples(self, intent: str) -> List[str]:
        return self.intents.get(intent, {}).get("examples", [])

    def get_all_intents(self) -> List[str]:
        return self.intent_names
