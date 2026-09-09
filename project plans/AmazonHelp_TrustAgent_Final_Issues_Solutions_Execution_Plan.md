# AmazonHelp TrustAgent — Final Issues, Solutions & Execution Plan

## Purpose

This document captures the issues found during the final audit of the live repository and gives a concrete execution plan before submitting the Hiver SDE Intern take-home.

The goal is **not to add more features**. The goal is to make the implementation, evaluation code, README, technical report, and headline claims say exactly the same thing.

---

# 1. P0 — Make the responder genuinely precedent-grounded

## Issue

`src/generation/responder.py` currently prioritizes hard-coded intent templates:

```python
if intent in GROUNDED_INTENT_TEMPLATES:
    draft = GROUNDED_INTENT_TEMPLATES[intent]
```

Only when no template exists does it use a retrieved historical resolution.

This means the system retrieves AmazonHelp precedents, but for most supported intents the final reply is generated from a static template rather than from the retrieved historical resolution.

That weakens the central Hiver requirement:

> Draft a reply grounded in how the brand historically resolved similar issues.

## Solution

Change the responder so that:

1. Retrieve the strongest historical precedent.
2. Use its `brand_resolution` as the primary grounding source.
3. Generate/adapt the reply from that precedent.
4. Use a conservative template only when:
   - no usable precedent exists, or
   - the retrieved precedent is too weak.
5. Keep forbidden-action checks after generation.
6. Return the exact source case IDs used for the response.

Recommended response metadata:

```json
{
  "source": "retrieved_historical_case",
  "source_case_ids": ["..."],
  "is_grounded": true
}
```

## Important

Do **not** introduce an unrestricted LLM that can invent policy.

The response should be constrained to information contained in the historical resolution.

## Verification

Create tests proving:

- A supported intent uses the retrieved resolution.
- A weak/no precedent falls back safely.
- A fabricated refund/action is rejected.
- The returned source case ID corresponds to the evidence shown by the API.

---

# 2. P0 — Fix Unsupported Claim Rate definition vs implementation

## Issue

The report describes Unsupported Claim Rate as using:

- deterministic forbidden-claim checks
- plus LLM Judge groundedness

But `scripts/run_evaluation.py` currently calculates it from:

```python
is_unsupported = not resp["is_grounded"]
```

and `is_grounded` comes from the deterministic regex checker.

Therefore the current implementation does **not** calculate the metric exactly as described in the report.

## Solution

Use a clean separation:

### Production safety gate

Use deterministic safety/grounding checks only.

Reason: a hard safety gate should not depend on a probabilistic LLM judge.

### Evaluation

Use the LLM judge separately to assess:

- correctness
- groundedness
- relevance
- helpfulness
- safety

Then define the production metric precisely as:

> Unsupported Claim Rate = percentage of evaluated responses flagged by the deterministic unsupported-action/claim detector.

If the LLM judge is also used for a separate groundedness metric, name that separately.

## Required documentation change

Replace vague wording such as:

> Unsupported Claim Rate uses regex rules paired with LLM Judge Groundedness.

with something like:

> Unsupported Claim Rate measures responses flagged by the deterministic groundedness/safety validator. The LLM judge is evaluated separately as a response-quality assessor and is not part of the hard Trust Gate.

## Verification

Re-run the evaluation and ensure the report and JSON artifact use the same definition.

---

# 3. P0 — Rename stale escalation metrics

## Issue

The updated report uses:

- Unsafe Auto-Handling Rate
- Unnecessary Escalation Rate

But the repository still contains:

- `false_auto_handling_rate`
- `false_escalation_rate`

and prints the old terminology.

This creates an obvious report/code mismatch.

## Solution

Standardize terminology everywhere.

Recommended names:

```text
Automation Rate
Unsafe Auto-Handling Rate
Unnecessary Escalation Rate
Escalation Precision
Escalation Recall
```

Recommended JSON:

```json
{
  "automation_rate": ...,
  "unsafe_auto_handling_rate": ...,
  "unnecessary_escalation_rate": ...,
  "escalation_precision": ...,
  "escalation_recall": ...
}
```

Update:

- `src/evaluation/escalation.py`
- `scripts/run_evaluation.py`
- README
- technical report
- evaluation JSON
- tests
- any frontend references

## Definition

Use explicit denominators.

For example:

> Unsafe Auto-Handling Rate = unsafe auto-handled cases / all evaluated cases.

> Unnecessary Escalation Rate = routine cases escalated / all cases that did not require mandatory escalation.

If your existing calculation uses a different denominator, either change the implementation or document the actual denominator. Do not silently rename a mathematically different metric.

---

# 4. P0 — Stop calling the retrieval confidence "calibrated" unless calibration was measured

## Issue

`RetrievalAugmentedClassifier` computes:

```python
confidence = 0.6 * top_sim + 0.4 * consensus_ratio
```

This is a useful heuristic confidence score.

However, it is not automatically a statistically calibrated probability.

## Solution

Rename it consistently to:

> retrieval-derived confidence score

or simply:

> confidence score

Avoid:

> calibrated confidence

unless you actually perform calibration analysis such as reliability/ECE evaluation.

## Why

A reviewer may ask:

> "How did you calibrate it?"

The current code does not demonstrate formal calibration.

---

# 5. P1 — Clarify the FAISS "100% recall" statement

## Issue

The decision log says `IndexFlatIP` guarantees 100% recall.

That can be misunderstood because the project reports task-level Recall@5 below 100%.

## Solution

Use precise wording:

> `IndexFlatIP` performs exact nearest-neighbor search over the indexed vectors, avoiding approximate-index recall loss. Task-level precedent Recall@5 is still below 100% because the retrieved nearest cases do not always contain the correct intent precedent.

This distinction is important.

---

# 6. P1 — Remove unsupported hard-coded policy claims from the responder

## Issue

Some templates make concrete claims such as:

- refund timing
- 30-day return windows
- replacement behavior
- delivery refusal
- specific Amazon workflow behavior

These statements may not be supported by the retrieved historical case.

That is dangerous for a project whose main claim is grounded support.

## Solution

Prefer:

```text
Retrieved historical resolution
        ↓
Extract supported action/instruction
        ↓
Compose concise customer-facing response
        ↓
Groundedness validator
        ↓
Trust Gate
```

If a policy detail is not present in the evidence, do not invent it.

A safe fallback should say that a specialist needs to assist rather than fabricate policy.

---

# 7. P1 — Make Trust Gate evidence checks internally consistent

## Issue

`policy.py` retrieves:

```python
has_strong_evidence
```

but does not actually use it.

The Trust Gate instead checks:

```python
top_similarity >= 0.62 and len(cases) > 0
```

So there is a signal in the code that appears important but has no effect on the decision.

## Solution

Choose one of two designs.

### Preferred

Actually use the evidence-strength signal:

```text
Strong precedent evidence
AND
sufficient similarity
AND
sufficient confidence
AND
safe intent
AND
grounded response
→ AUTO
```

Or remove `has_strong_evidence` entirely if it is not needed.

Do not keep dead safety signals.

## Verification

Add a unit test where:

- top similarity is high
- but there is insufficient evidence

and verify the expected escalation behavior.

---

# 8. P1 — Make escalation ground truth defensible

## Issue

The evaluation code defines mandatory escalation as:

```python
true_intent in high_risk_intents
```

This is reasonable for the prototype, but the report should make clear that this is a **policy-derived ground-truth rule**, not human-verified production truth.

## Solution

Document:

> Mandatory escalation labels were derived from the predefined safety policy: fraud/security, payment disputes, account-access/security issues, and OTHER are mandatory escalation categories.

If you have human labels for escalation in the golden set, report those separately and preferably use them for the human-evaluated safety analysis.

Do not imply that Amazon's actual production escalation policy was observed from the dataset.

---

# 9. P1 — Strengthen the golden-set methodology note

## Issue

The Hiver requirement asks for a short sampling/labelling note.

The final documentation should explicitly answer:

- How examples were sampled.
- Whether intents were stratified.
- How rare/high-risk intents were handled.
- Who labelled expected intent/action.
- How ambiguous cases were handled.
- Whether the set was frozen before final evaluation.
- Whether it was excluded from training/index construction/threshold tuning.

## Solution

Add a concise reproducibility note:

```text
Golden set:
- 200 conversation-level examples.
- Sampled from unseen data using stratification across the derived intent taxonomy,
  with additional coverage for rare/high-risk categories.
- Human-labelled for expected intent and expected escalation action.
- Ambiguous examples were labelled as OTHER/escalation where appropriate.
- The set was frozen before final evaluation.
- Golden examples were not used to train the classifier, build the retrieval index,
  or tune the Trust Gate threshold.
```

Only claim the parts that are actually true. If a bullet is not true, modify the process or disclose it.

---

# 10. P1 — Fix LLM Judge fallback semantics

## Issue

`src/evaluation/judge.py` calls itself an LLM-as-Judge but silently falls back to a deterministic heuristic evaluator if the model fails.

The heuristic is very shallow:

- keyword overlap for relevance
- `[LINK]`/`DM` for groundedness/helpfulness
- forbidden phrases for safety

This can make a reader think all reported judge scores came from the LLM.

## Solution

Make the evaluator explicitly report:

```json
{
  "judge_type": "llm",
  "model": "..."
}
```

or:

```json
{
  "judge_type": "heuristic_fallback",
  "model": null
}
```

Never mix the two silently.

For the final reported judge-human agreement, ensure the reported 50-example validation uses the actual LLM judge, not the heuristic fallback.

---

# 11. P1 — Resolve the human-validation N mismatch

## Issue

The project documentation previously described 50 manually reviewed examples, while the agreement table showed N=46 valid comparisons.

## Solution

Inspect the four excluded rows.

Then document exactly why they were excluded, e.g.:

```text
50 examples were manually reviewed.
46 had valid machine/human score pairs and were included in correlation/agreement calculations;
4 were excluded because of [actual reason].
```

Do not report N=50 for statistical calculations if only 46 valid pairs were used.

---

# 12. P1 — Do not overclaim LLM judge quality

## Issue

The observed judge-human correlations are weak for several dimensions.

Safety agreement is strong, but correctness/helpfulness/relevance/overall agreement is not strong enough to claim that the judge is a highly reliable replacement for humans.

## Solution

Frame the judge honestly:

> The LLM judge provides scalable directional evaluation, but human validation shows limited agreement on several subjective dimensions. Human review remains the reference standard for quality validation.

Report both:

- agreement/correlation values
- sample size

Do not hide weak dimensions.

---

# 13. P1 — Explain why the production model has lower Macro F1 than TF-IDF

## Issue

The production retrieval classifier can have better overall/weighted performance while having lower Macro F1.

A reviewer may ask why.

## Solution

Add one sentence:

> The retrieval model improves performance primarily on frequent intents, increasing overall and weighted F1, while several lower-frequency intents remain difficult; consequently Macro F1 is lower than the TF-IDF baseline.

Then support it with the per-intent results.

This shows you understand your evaluation rather than cherry-picking the strongest metric.

---

# 14. P1 — Clarify "Recall@k"

## Issue

Calling retrieval Recall@k "valid historical resolution retrieval" can imply that every retrieved case was manually verified as a correct resolution.

## Solution

Use:

> Precedent Intent Recall@k

and define it:

> Percentage of test queries for which at least one of the top-k retrieved historical cases belongs to the ground-truth intent.

If the metric actually checks something more specific, document that exact definition.

---

# 15. P2 — Tighten production-readiness wording

## Issue

The application has:

```python
allow_origins=["*"]
allow_credentials=True
```

This is acceptable for a local demo but not a production security configuration.

## Solution

Call the system:

> production-oriented prototype

rather than:

> production-ready

If desired, restrict CORS to configured origins.

This is not a core Hiver scoring issue but avoids an unnecessary reviewer objection.

---

# 16. P2 — Remove stale/demo code and imports

Clean:

- unused imports
- outdated milestone references
- stale comments
- unused `has_strong_evidence` if not adopted
- old metric terminology
- unused judge imports
- any README claims that no longer match the implementation

This is a polish pass, not a feature pass.

---

# 17. P2 — Fix test-count/readme mismatch

Earlier documentation showed a test badge/count of 17 while the current suite had 22 passing tests.

## Solution

Run the actual test suite and update the README to the current result.

Never hard-code a stale test count.

Better:

> Tests: 22 passing

only if that is the actual final run.

---

# 18. P2 — Make the <15-minute reproduction claim precise

## Issue

"Fully verify all claims in under 15 minutes" can be interpreted as rebuilding the entire dataset/index in under 15 minutes.

The project uses precomputed artifacts for the final evaluation.

## Solution

Say:

> The headline evaluation can be reproduced from the committed evaluation artifacts in under 15 minutes. Full raw-dataset reconstruction is intentionally not required for the submission.

If the README has a separate raw-data pipeline, explain its expected runtime.

---

# 19. Recommended final headline

Avoid using only:

> 90.7% accuracy

That hides the selective nature of the system.

Use a multi-metric headline:

> On 1,800 unseen test conversations, the system auto-handled 17.9% with 90.7% selective accuracy, 99.58% escalation recall, and 0.22% unsafe auto-handling.

Then immediately state:

> These are test-set results, not production traffic estimates.

This is much harder to misinterpret.

---

# Execution Plan

## Phase 1 — Code correctness

### Step 1
Fix `src/generation/responder.py`.

Goal:

- retrieved precedent becomes primary grounding source
- static templates become fallback only
- source case IDs are exposed
- unsupported claims remain blocked

### Step 2
Fix `src/escalation/policy.py`.

Goal:

- either use `has_strong_evidence`
- or remove it
- make every safety signal actually affect the decision

### Step 3
Fix `src/evaluation/escalation.py`.

Goal:

- standard metric names
- explicit denominators
- consistent JSON keys

### Step 4
Fix `scripts/run_evaluation.py`.

Goal:

- use new metric names
- use deterministic unsupported-claim definition
- preserve unseen test evaluation
- regenerate `data/evaluation_results.json`

---

# Phase 2 — Evaluation integrity

### Step 5
Verify dataset separation.

Confirm:

```text
TRAIN
  ↓
classifier training
retrieval index

VALIDATION
  ↓
threshold/decision development

TEST
  ↓
final unseen evaluation

GOLDEN
  ↓
frozen human-labelled quality evaluation
```

Confirm golden/test examples are not used for training or retrieval indexing.

### Step 6
Verify Trust Gate threshold selection.

Document the actual selection procedure.

Do not call 0.75 "optimal" unless an explicit validation objective was optimized.

Preferred wording if applicable:

> 0.75 was selected on the validation set because it provided a useful safety/coverage trade-off without observed unsafe automation.

Only use this if it matches the actual experiment.

### Step 7
Fix golden-set methodology documentation.

Make sampling, labelling, freezing, and leakage controls explicit.

---

# Phase 3 — LLM Judge

### Step 8
Make judge provenance explicit.

Every evaluation record should say whether the score came from:

- actual LLM
- fallback heuristic

### Step 9
Resolve the N=50 vs N=46 discrepancy.

Inspect the four excluded examples and document the actual reason.

### Step 10
If changing the judge model, rerun everything.

Do **not** combine old Qwen results with new judge results.

If you switch to a stronger free model:

1. Run the 50-example human validation again.
2. Recalculate judge-human agreement.
3. Run the 200-example golden evaluation again.
4. Replace old artifacts.
5. Update report numbers.

---

# Phase 4 — Documentation synchronization

Update these together:

```text
README.md
TECHNICAL_REPORT.md
DECISION_LOG.md
scripts/run_evaluation.py
src/evaluation/escalation.py
src/generation/responder.py
src/escalation/policy.py
data/evaluation_results.json
data/golden_evaluation_results.json
```

Search the entire repository for stale terms:

```text
False Escalation Rate
False Auto-Handling Rate
calibrated confidence
100% recall
production-ready
hallucination-free
valid historical resolution
```

Every occurrence should either be corrected or precisely qualified.

---

# Phase 5 — Tests

Run:

```bash
pytest -q
```

Expected final result should be recorded in README.

Add tests for the new critical behavior:

### Responder
- retrieved precedent is used
- fallback works
- fabricated actions are rejected

### Trust Gate
- critical risk always escalates
- low confidence escalates
- weak evidence escalates
- unsupported response escalates
- non-auto-eligible intent escalates
- only fully passing cases auto-handle

### Evaluation
- metric denominators are correct
- renamed metrics are correct
- no division-by-zero errors

---

# Phase 6 — Final evaluation

Run the complete final evaluation only **after all code changes**.

Do not edit the report numbers manually afterward.

The pipeline should be:

```text
Final code
   ↓
pytest
   ↓
golden evaluation
   ↓
test evaluation
   ↓
LLM judge validation
   ↓
failure analysis
   ↓
README/report
```

The numbers in the report should come directly from the generated artifacts.

---

# Phase 7 — Final audit

Before submission, manually check:

## Hiver requirement checklist

- [ ] One brand selected: AmazonHelp
- [ ] Intent taxonomy derived from data
- [ ] AI support agent implemented
- [ ] Historical precedent retrieval implemented
- [ ] Reply grounded in historical resolutions
- [ ] Auto vs human decision implemented
- [ ] Reason for escalation exposed
- [ ] 150–250 golden examples
- [ ] Sampling/labelling note
- [ ] Automated evaluation harness
- [ ] LLM-as-judge
- [ ] Human agreement validation
- [ ] At least two baselines
- [ ] Top five failure modes with real examples
- [ ] "What is misleading about my headline number?"
- [ ] One-week roadmap
- [ ] 10–15 decision log entries
- [ ] Reproducible README
- [ ] Tests passing
- [ ] No report/code metric mismatch

---

# What NOT to do

Do not spend the remaining time on:

- adding another model
- adding another brand
- building a more complex frontend
- fine-tuning a transformer
- adding unnecessary agents
- rebuilding the entire dataset
- optimizing FAISS
- adding production infrastructure

The project already has enough technical breadth.

The remaining work is **evaluation integrity + implementation/report consistency**.

---

# Final Priority Order

## Must fix before submission

1. **Responder must genuinely use historical precedent.**
2. **Fix Unsupported Claim Rate definition/implementation mismatch.**
3. **Standardize escalation metric names and formulas.**
4. **Remove "calibrated confidence" overclaim.**
5. **Make Trust Gate evidence signals internally consistent.**
6. **Regenerate final evaluation artifacts after code changes.**

## Strongly recommended

7. Fix FAISS recall wording.
8. Remove unsupported hard-coded policy claims.
9. Fix LLM judge fallback transparency.
10. Resolve N=50 vs N=46.
11. Strengthen golden-set methodology.
12. Explain Macro F1 vs weighted F1 behavior.

## Final polish

13. Fix README test count.
14. Tighten <15-minute reproduction wording.
15. Clean stale imports/comments/milestone references.
16. Qualify production-readiness claims.
17. Perform final repository-wide terminology search.

---

# Submission Standard

The final repository should satisfy one rule:

> **Every important claim in README/report must be directly demonstrable from the current code and generated evaluation artifacts.**

If a reviewer reads:

```text
claim → README → report → evaluation JSON → evaluation script → implementation
```

they should find the same definition, same denominator, same dataset split, and same behavior at every step.

That consistency is more valuable for this assignment than adding another feature.
