# AmazonHelp TrustAgent — Final Frontend Polish Plan

## Repo Audit Result

The current frontend is structurally strong and already demonstrates the core Hiver requirements:

- Intent classification
- Historical precedent retrieval
- Grounded response drafting
- Trust Gate decision
- Explicit escalation reason
- Retrieved evidence
- Benchmark/demo cases
- FastAPI integration

The frontend should **not** be rebuilt. The remaining work is a focused accuracy, evidence, and UX-truthfulness pass.

---

## P0 — Must Fix

### 1. Fix Selective Accuracy Binding

**File:** `frontend/app.js`

The element labeled **Selective Accuracy** is currently populated from:

```js
data.intent_classification.production_retrieval.accuracy
```

That is overall intent-classification accuracy (**68.44%**), not selective accuracy.

The current held-out test evaluation reports **90.68% selective accuracy** at Trust Gate threshold `0.75`, with **17.89% automation coverage**.

Bind the UI to the `threshold = 0.75` entry in:

```text
data.selective_prediction_curve
```

using:

```text
safe_accuracy = 0.9068
```

Alternatively, display both:

- Overall Intent Accuracy: 68.4%
- Selective Accuracy: 90.7%

Never label 68.4% as Selective Accuracy.

### 2. Fix Precedent Recall@5 Placeholder

**File:** `frontend/index.html`

The HTML currently contains a stale `93.3%` placeholder.

The current held-out test artifact reports:

> **Recall@5: 89.78%**

Therefore the frontend should display **89.8%**. The JavaScript already reads `data.retrieval.recall_at_5`; update the static fallback too.

### 3. Rename the Misleading Metric DOM ID

**Files:** `frontend/index.html`, `frontend/app.js`

The current ID `metric-macro-f1` is used to display accuracy. Rename it to something explicit, such as:

```text
metric-selective-accuracy
```

Update the JavaScript reference accordingly. This is only a naming/maintainability fix.

### 4. Eliminate Stale Hardcoded Metrics

Search the frontend for stale values such as:

```text
93.3
68.4
17.4
```

Ensure visible metrics are dynamically populated from `/api/support/metrics`, or use correct fallback values matching the current evaluation artifact.

---

## P1 — Strongly Recommended

### 5. Add a Dynamic Historical Precedent Source Badge

**Files:** `frontend/app.js`, optionally `frontend/index.html`

Important: the current backend does **not** return `response.source_case_ids`.

Do not write frontend code expecting that field.

The API already returns `response.source` and evidence records containing `case_id`.

If:

```text
data.response.source === "retrieved_historical_case"
```

and evidence exists, use:

```js
data.evidence[0].case_id
```

to display:

```text
✓ Adapted from Precedent #<actual-case-id>
```

If:

```text
data.response.source === "conservative_fallback"
```

display:

```text
⚠ Conservative Policy Guidance
```

Never invent a case ID and do not claim every response is historically grounded.

### 6. Make the Trust Gate Stepper Reflect the Actual Decision

**File:** `frontend/app.js`

Currently all four pipeline steps are marked active immediately when analysis starts.

After the API response:

**AUTO**

```text
✓ AUTO
```

Use the existing positive/success visual treatment.

**ESCALATE**

```text
⚠ ESCALATE
```

Use the existing warning/escalation treatment.

The state must be driven by:

```js
data.decision.action
```

not hardcoded.

### 7. Add a Real Backend Health Indicator

**File:** `frontend/app.js`

The backend exposes:

```text
GET /api/health
```

and returns status information including `status` and `models_loaded`.

Recommended UI:

Healthy:

```text
🟢 Backend Online · Models Loaded
```

Unreachable:

```text
🔴 Offline · Server Not Started
```

Do not claim `FAISS Active · 8,399 Dialogues` from `/api/health`, because the endpoint does not explicitly return those fields.

---

## Do NOT Change

This frontend pass must not modify:

- Intent taxonomy
- Classifier model
- Retrieval model
- FAISS index
- Trust Gate threshold (`0.75`)
- Similarity threshold (`0.62`)
- Golden set
- Test set
- Evaluation methodology
- Evaluation artifacts
- Benchmark results
- Backend decision logic

Do not introduce React, npm, webpack, a new frontend framework, or unrelated UI features.

The goal is **truthful presentation of the already-validated system**, not another architecture change.

---

## Final Frontend Acceptance Checklist

### Metrics

- [ ] Selective Accuracy displays **90.7%**
- [ ] Overall Intent Accuracy, if shown, displays **68.4%**
- [ ] Precedent Recall@5 displays **89.8%**
- [ ] Unsafe Auto-Handling displays **0.22%**
- [ ] Automation Coverage/Rate matches the intended metric and current artifact
- [ ] No stale `93.3%` placeholder remains
- [ ] No stale `17.4%` value remains
- [ ] No metric is displayed under an incorrect label
- [ ] DOM IDs match the metrics they represent

### Response Grounding

- [ ] Historical responses identify the actual retrieved precedent when available
- [ ] Fallback responses explicitly say **Conservative Policy Guidance**
- [ ] No fabricated case IDs
- [ ] No claim that every response is historically grounded

### Trust Gate

- [ ] AUTO result visibly shows `✓ AUTO`
- [ ] ESCALATE result visibly shows `⚠ ESCALATE`
- [ ] Step 4 is driven by the real API decision
- [ ] Trust Gate reason code remains visible
- [ ] Audit trail remains visible

### Backend Status

- [ ] `/api/health` is checked
- [ ] Online state is shown when healthy
- [ ] Offline state is shown when unreachable
- [ ] Health UI does not make unsupported claims

### Regression Safety

- [ ] Existing API integration still works
- [ ] All benchmark pills still work
- [ ] Retrieved evidence still renders correctly
- [ ] Existing tests remain passing
- [ ] No backend/evaluation behavior changed

---

## Final Recommendation

This is the correct final frontend step for the Hiver submission.

The current frontend already has the right architecture and demo surface. The remaining work is primarily:

1. Correct metrics
2. Accurate evidence/source display
3. Clear Trust Gate outcome
4. Reliable backend status

Once these are implemented and verified, **stop feature development** and move to the final submission/demo review.
