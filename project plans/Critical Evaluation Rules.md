# Critical Evaluation Rules

## 1. Human Evidence Must Be Real

Never fabricate:

- Human labels
- Human ratings
- Human-vs-LLM agreement
- Correlations
- Cohen's kappa
- Failure-analysis examples

The coding agent may prepare templates and candidate samples, but actual human evaluation must be completed by the human reviewer.

---

## 2. Use a Real LLM for the Primary Judge

The primary reply-quality judge must be an actual LLM.

Do not use:

- Embedding similarity
- Keyword heuristics
- Rule-based scoring
- Deterministic heuristics

as a substitute for the LLM judge.

A deterministic evaluator may exist as a supplementary offline sanity check, but it must not be presented as the required LLM-as-judge.

The implementation should support a configurable LLM provider/model so the judge model can be changed without modifying the evaluation pipeline.

---

## 3. Do Not Request Chain-of-Thought

The judge should return structured scores and a short justification.

Do not request or store hidden chain-of-thought.

Example:

```json
{
  "correctness": 4,
  "groundedness": 5,
  "relevance": 5,
  "helpfulness": 4,
  "safety": 5,
  "overall": 5,
  "justification": "The response addresses the issue using information supported by the retrieved precedent."
}
```

---

## 4. Do Not Assume the Best Threshold

The current threshold is 0.75.

Treat this as the current operating point, not as a known optimum.

Evaluate:

```text
0.60
0.70
0.75
0.80
0.90
```

Compare:

- Automation coverage
- Selective accuracy
- False auto-handling rate
- Escalation rate

Select the final threshold based on the measured safety/coverage trade-off.

---

## 5. Select Human Judge-Validation Samples Before Seeing Judge Scores

Do not select validation examples based on the LLM judge's scores.

Use a reproducible sampling strategy such as:

- Common intents
- Rare intents
- High-risk cases
- Low-confidence cases
- Random/general cases

The final 50 examples must be selected before reviewing their LLM judge scores.

Then independently:

```text
50 examples
   ↓
Human rating
   +
LLM judge rating
   ↓
Agreement analysis
```

---

## 6. Preserve Evaluation Separation

Maintain clear separation between:

```text
Training
Validation
Test
Golden Evaluation
```

Verify that golden examples do not appear in the training/retrieval index.

Do not use the golden set to repeatedly tune the system and then present the resulting score as an untouched final evaluation.

If the golden set is used during development, document the iteration and freeze a final evaluation set before reporting final results.

---

## 7. Discover Failure Modes From Data

Do not predefine the top five failure modes.

Run the evaluation first.

Then:

```text
Actual failures
     ↓
Group by root cause
     ↓
Count frequency
     ↓
Select top 5
     ↓
Analyze real examples
```

Any hypotheses must be clearly identified as hypotheses.

---

## 8. Every Reported Number Must Have a Definition

For every metric, document:

- Numerator
- Denominator
- Population
- Inclusion/exclusion criteria
- Whether the metric is calculated on the test set or golden set

Never report a percentage without making its population clear.

---

## 9. Prefer Honest Results Over Attractive Results

Do not modify evaluation methodology simply because it produces a worse number.

Unexpected or weak results should be investigated and reported.

The objective is to demonstrate sound engineering judgment and evaluation methodology, not to manufacture a high score.

---

## 10. No Unnecessary Features

The current agent architecture is sufficient.

Do not add:

- Additional UI features
- Unnecessary API endpoints
- Extra model architectures
- Full-dataset processing
- Complex production infrastructure

unless a concrete evaluation requirement requires them.

The remaining work should focus on:

**Golden Set → Baselines → LLM Judge → Human Validation → Evaluation → Threshold Analysis → Failure Analysis → Report.**