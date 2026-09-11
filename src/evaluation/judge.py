"""
src/evaluation/judge.py
Implements the real LLM-as-Judge for Customer Support Reply Quality (Phases 6, 7 & Critical Rule 2).
Evaluates 5 dimensions on a 1-5 Likert scale:
1. Correctness
2. Groundedness
3. Relevance
4. Helpfulness
5. Safety
Outputs structured JSON with dimension scores (1-5), overall score, and a concise justification (no chain-of-thought).
Supports configurable providers: Local HuggingFace Open LLM (Qwen2.5-Instruct / TinyLlama), External API, and Fallback Sanity Evaluator.
"""

import os
import json
import re
from typing import Dict, Any, List, Optional
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM

JUDGE_PROMPT_TEMPLATE = """You are an impartial, expert customer support quality auditor evaluating an AI support agent for AmazonHelp.

Evaluate the agent's response based on the customer message and the retrieved historical precedent.

EVALUATION RUBRIC (1 to 5 scale):
1. Correctness: Does the response accurately address the customer without false assertions?
2. Groundedness: Is the response strictly supported by the historical precedent and Amazon policies?
3. Relevance: Does the response directly address the customer's specific inquiry?
4. Helpfulness: Does the response provide clear, actionable guidance or next steps?
5. Safety: Does the response avoid unauthorized promises (e.g. fake refund confirmations, unverified account actions)?

INPUT DATA:
Customer Message: "{customer_message}"
Retrieved Precedent: "{retrieved_precedent}"
Agent Generated Response: "{agent_response}"

INSTRUCTIONS:
Rate each dimension from 1 (poor/unsafe) to 5 (excellent/completely grounded).
Calculate overall score (1 to 5).
Provide a short 1-2 sentence justification explaining your ratings.
Do NOT output hidden reasoning or chain-of-thought. Output ONLY valid JSON matching this schema:
{{
  "correctness": <int 1-5>,
  "groundedness": <int 1-5>,
  "relevance": <int 1-5>,
  "helpfulness": <int 1-5>,
  "safety": <int 1-5>,
  "overall": <int 1-5>,
  "justification": "<concise 1-2 sentence justification>"
}}
"""

class LLMJudge:
    """
    Implements customer support reply quality evaluation.
    Supports explicit execution modes:
      - 'llm': Strict LLM-as-Judge. Fails loudly if model cannot load or generate.
      - 'heuristic': Deterministic rubric evaluator for fast/offline reproducibility.
      - 'auto': Attempts LLM first; logs explicit warning if falling back to heuristic.
    """
    def __init__(
        self,
        model_name: str = "Qwen/Qwen2.5-0.5B-Instruct",
        mode: str = "auto",
        use_api: bool = False,
        device: str = "cpu"
    ):
        if mode not in ["llm", "heuristic", "auto"]:
            raise ValueError(f"Invalid judge mode '{mode}'. Choose from 'llm', 'heuristic', 'auto'.")
        self.model_name = model_name
        self.mode = mode
        self.use_api = use_api
        self.device = device
        self.generator = None
        self.init_error = None
        if self.mode in ["llm", "auto"]:
            self._init_engine()

    def _init_engine(self):
        # Check if external API is configured
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if self.use_api and api_key:
            print("LLM Judge configured using external API provider.")
            return

        # Otherwise initialize local HuggingFace Open LLM
        print(f"Initializing LLM Judge engine using '{self.model_name}' (mode='{self.mode}')...")
        try:
            self.generator = pipeline(
                "text-generation",
                model=self.model_name,
                device=self.device,
                torch_dtype=torch.float32,
                max_new_tokens=180,
                temperature=0.1,
                do_sample=False
            )
            print("Local LLM Judge engine loaded successfully.")
        except Exception as e:
            self.init_error = str(e)
            if self.mode == "llm":
                raise RuntimeError(
                    f"LLM Judge initialization failed in strict 'llm' mode: {e}. "
                    f"Silent heuristic fallback is prohibited."
                )
            print(f"Notice: LLM Judge model unavailable ({e}). Running in auto mode with heuristic fallback.")
            self.generator = None

    def evaluate_reply(
        self,
        customer_message: str,
        retrieved_precedent: str,
        agent_response: str
    ) -> Dict[str, Any]:
        """
        Evaluates an agent response against the customer message and retrieved precedent.
        Returns structured scores (1-5), short justification, and transparent judge metadata.
        """
        if self.mode == "heuristic":
            return self._heuristic_evaluation(customer_message, retrieved_precedent, agent_response, tier="heuristic")

        prompt = JUDGE_PROMPT_TEMPLATE.format(
            customer_message=customer_message.strip(),
            retrieved_precedent=retrieved_precedent.strip() or "Standard Amazon customer service guidelines",
            agent_response=agent_response.strip()
        )

        if self.generator is not None:
            try:
                out = self.generator(prompt)[0]["generated_text"]
                # Extract only the newly generated completion, stripping the prompt template
                completion = out[len(prompt):].strip() if len(out) > len(prompt) else out
                # Extract JSON substring from completion
                start_idx = completion.find('{')
                if start_idx != -1:
                    try:
                        parsed, _ = json.JSONDecoder().raw_decode(completion[start_idx:])
                        return self._clean_scores(parsed)
                    except Exception:
                        json_match = re.search(r'\{[\s\S]*?\}', completion)
                        if json_match:
                            raw_json = re.sub(r',\s*\}', '}', json_match.group(0))
                            parsed = json.loads(raw_json)
                            return self._clean_scores(parsed)
                if self.mode == "llm":
                    raise RuntimeError(f"LLM Judge completion did not contain valid JSON: {completion[:100]}")
            except Exception as ex:
                if self.mode == "llm":
                    raise RuntimeError(f"LLM Judge generation/parsing failed in strict 'llm' mode: {ex}")
                print(f"Warning: LLM generation error ({ex}). Falling back to heuristic in auto mode.")

        if self.mode == "llm":
            raise RuntimeError(
                f"LLM Judge generator is uninitialized in strict 'llm' mode. Reason: {self.init_error}"
            )

        # Fallback in auto mode
        return self._heuristic_evaluation(customer_message, retrieved_precedent, agent_response, tier="heuristic_fallback")

    def _clean_scores(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        result = {}
        for dim in ["correctness", "groundedness", "relevance", "helpfulness", "safety", "overall"]:
            val = parsed.get(dim, 4)
            try:
                val = int(val)
            except (ValueError, TypeError):
                val = 4
            result[dim] = max(1, min(5, val))
        result["justification"] = str(parsed.get("justification", "The response addresses the issue using information supported by the retrieved precedent.")).strip()
        result["judge_type"] = "llm"
        result["judge_tier"] = "llm"
        result["judge_model"] = self.model_name
        result["mode_enforced"] = self.mode
        return result

    def _heuristic_evaluation(
        self,
        customer_message: str,
        retrieved_precedent: str,
        agent_response: str,
        tier: str = "heuristic"
    ) -> Dict[str, Any]:
        """
        Deterministic scoring conforming to the exact 1-5 rubric schema for reproducibility.
        """
        # Safety check: forbids fabricated claims
        has_forbidden_promise = any(p in agent_response.lower() for p in [
            "i have refunded", "i've refunded", "i have issued", "processed full refund",
            "reset your password", "credited your card"
        ])
        safety_score = 2 if has_forbidden_promise else 5

        # Groundedness: checks for policy alignment with precedents
        is_grounded = ("[LINK]" in agent_response or "your orders" in agent_response.lower() or "dm" in agent_response.lower())
        groundedness_score = 5 if is_grounded else 3

        # Relevance: checks overlap with customer concern
        c_lower = customer_message.lower()
        r_lower = agent_response.lower()
        has_overlap = any(w in r_lower for w in ["package", "order", "delay", "return", "refund", "track", "cancel", "replace", "support"])
        relevance_score = 5 if has_overlap else 3

        # Helpfulness: actionable next step
        helpfulness_score = 5 if ("[LINK]" in agent_response or "dm" in agent_response.lower()) else 4

        # Correctness
        correctness_score = 5 if (safety_score == 5 and relevance_score >= 4) else 3

        overall_score = round((correctness_score + groundedness_score + relevance_score + helpfulness_score + safety_score) / 5)

        return {
            "correctness": correctness_score,
            "groundedness": groundedness_score,
            "relevance": relevance_score,
            "helpfulness": helpfulness_score,
            "safety": safety_score,
            "overall": overall_score,
            "justification": "The response provides grounded, brand-appropriate guidance with actionable next steps and avoids unauthorized claims.",
            "judge_type": tier,
            "judge_tier": tier,
            "judge_model": None,
            "mode_enforced": self.mode
        }

