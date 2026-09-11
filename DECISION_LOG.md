# Engineering Decision Log

This log documents **15 key engineering decisions, rationales, alternatives considered, and trade-offs** made during the design, implementation, and evaluation of the AmazonHelp AI Customer Support Agent.

---

### Decision 1: Target Brand Selection (AmazonHelp)
- **Decision**: Selected `AmazonHelp` from the 108 brands in `twcs.csv` as the primary support system domain.
- **Why**: Empirical exploration revealed AmazonHelp had the highest support volume (169,840 outbound tweets) and the highest multi-turn dialog density (85,274 multi-turn interactions, >50.2% multi-turn reply rate). E-commerce provides clear, natural boundaries between safe automated inquiries (tracking, return windows) and high-risk human-only escalations (stolen credit cards, fraudulent charges).
- **Alternative Considered**: `AppleSupport` (106,860 tweets) or `SpotifyCares` (43,265 tweets).
- **Trade-Off**: AmazonHelp features multi-lingual queries (English, Japanese, German, Spanish); required an explicit language filtering stage to isolate high-quality English support dialogues.

---

### Decision 2: Conversation-Level Partitioning
- **Decision**: Partitioned data strictly by unique `conversation_id` (70% Train, 15% Val, 15% Test) rather than random tweet-level shuffling.
- **Why**: Random tweet splitting causes severe data leakage where an agent sees customer tweets during test time whose resolution was included in the training set.
- **Alternative Considered**: Standard `train_test_split` on individual tweets.
- **Trade-Off**: Reduces total independent data points compared to raw tweet shuffling, but guarantees valid, leakage-free evaluation.

---

### Decision 3: 15-Intent Taxonomy Granularity
- **Decision**: Established a 15-intent domain taxonomy (`DELIVERY_DELAY`, `ORDER_TRACKING_STATUS`, `PACKAGE_DELIVERED_NOT_RECEIVED`, `UNAUTHORIZED_TRANSACTION_FRAUD`, etc.).
- **Why**: 15 intents provide sufficient resolution to distinguish actionable operational paths (e.g. tracking advice vs damaged item replacement vs card fraud) without creating excessive class fragmentation.
- **Alternative Considered**: Coarse 5-intent scheme (e.g. Delivery, Billing, Technical, General, Other) or Banking77-style 50+ intent scheme.
- **Trade-Off**: A coarse scheme would obscure safety-critical distinctions (e.g. grouping card theft with standard billing questions); a 50+ scheme suffers from extreme data sparsity on rare classes.

---

### Decision 4: Data-Derived Intent Discovery
- **Decision**: Discovered intents using sentence embeddings and clustering over real customer inquiries rather than imposing arbitrary labels.
- **Why**: Customer support inquiries reflect authentic user language ("where's my parcel", "tracking says delivered but nothing on porch") rather than synthetic corporate taxonomies.
- **Alternative Considered**: Adopting a generic intent taxonomy (e.g. Banking77 or standard ATIS).
- **Trade-Off**: Required building an ingestion, cleaning, and clustering pipeline before labeling could begin.

---

### Decision 5: Historical Resolution Retrieval (Case-Level RAG)
- **Decision**: Indexed full historical resolutions (`customer_inquiry` + `brand_resolution`) rather than isolated tweets or raw FAQ documents.
- **Why**: Real brand precedents capture the exact historical policy and conversational tone proven to resolve inquiries.
- **Alternative Considered**: Zero-shot LLM response generation relying solely on parametric knowledge.
- **Trade-Off**: Retrieved responses depend on the quality and timeliness of historical Twitter responses.

---

### Decision 6: Embedding Model (`sentence-transformers/all-MiniLM-L6-v2`)
- **Decision**: Deployed `all-MiniLM-L6-v2` (384 dimensions) for sentence embeddings.
- **Why**: Delivers strong semantic retrieval performance with exceptionally low latency (sub-5ms on CPU) and compact memory footprint (~80MB), allowing rapid local execution without expensive GPU infrastructure.
- **Alternative Considered**: OpenAI `text-embedding-3-small` or large 1024-dim cross-encoders.
- **Trade-Off**: Slightly lower retrieval recall on long-tail phrasing compared to 1B+ parameter models, but completely eliminates external network dependencies and API costs.

---

### Decision 7: FAISS `IndexFlatIP` Vector Index
- **Decision**: Implemented exact inner-product search (`IndexFlatIP`) on L2-normalized embeddings.
- **Why**: For 8,399 support cases, exact cosine similarity search takes < 1ms on CPU and provides exact nearest-neighbor search without approximation-induced recall loss (distinct from task-level Precedent Recall@5 of 89.78%, which measures whether the retrieved cases contain the correct intent precedent).
- **Alternative Considered**: Approximate Nearest Neighbor (ANN) index like `IndexHNSWFlat` or `IndexIVFFlat`.
- **Trade-Off**: Does not scale to 10M+ vectors without clustering/quantization, but is mathematically optimal for the 10,000-case enterprise regime.

---

### Decision 8: Retrieval-Augmented k-NN Intent Classification
- **Decision**: Built the production intent classifier using distance-weighted k-NN voting ($k=5$) over labeled training embeddings.
- **Why**: Naturally outputs a retrieval-derived confidence score derived from neighborhood consensus and top-1 cosine similarity ($0.6 \cdot S_{top} + 0.4 \cdot R_{consensus}$), avoiding the arbitrary overconfidence common in softmax neural networks.
- **Alternative Considered**: Fine-tuned BERT sequence classification or zero-shot LLM prompting.
- **Trade-Off**: Inference scales with training set size (mitigated by FAISS indexing), but offers complete interpretability via nearest neighbors.

---

### Decision 9: Multi-Signal Trust Gate
- **Decision**: Arbitrated automation using multiple distinct signals (Confidence $\ge 0.75$, Precedent similarity $\ge 0.62$, Intent risk level, Groundedness check) rather than a single confidence threshold.
- **Why**: High confidence on an intrinsically dangerous inquiry (e.g. 98% confident it is credit card fraud) must NEVER lead to automated handling. Risk assessment must supersede confidence.
- **Alternative Considered**: Simple confidence threshold (`if confidence >= 0.7: auto()`).
- **Trade-Off**: Slightly increases policy logic complexity, but reduces the False Auto-Handling Rate to an enterprise-safe **0.22%**.

---

### Decision 10: Mandatory Escalation for Financial & Security Inquiries
- **Decision**: Configured `UNAUTHORIZED_TRANSACTION_FRAUD`, `PAYMENT_AND_BILLING_ISSUE`, and `ACCOUNT_ACCESS_SECURITY` for unconditional human escalation with explicit reason codes (`HIGH_RISK`, `PAYMENT_DISPUTE`, `ACCOUNT_SPECIFIC_ACTION`).
- **Why**: Automated bots lack authenticated transaction lookup access; pretending to resolve card fraud creates acute legal, financial, and trust liability.
- **Alternative Considered**: Attempting automated deflection with self-serve links.
- **Trade-Off**: Sacrifices ~15% potential automation coverage to guarantee 100% human safety on sensitive interactions.

---

### Decision 11: Strict Anti-Hallucination Output Constraints
- **Decision**: Enforced regex-backed guardrails prohibiting fabricated capabilities (e.g. *"I have issued your refund"*, *"I cancelled your order"*, *"I accessed your account"*).
- **Why**: In commercial support, customer trust is permanently destroyed if an AI makes promises the backend systems cannot fulfill.
- **Alternative Considered**: Relying purely on system prompt instructions to prevent hallucination.
- **Trade-Off**: Requires maintaining a forbidden promise pattern registry, but drove the measured Unsupported Claim Rate to **0.00%**.

---

### Decision 12: Independent 200-Example Golden Evaluation Set
- **Decision**: Constructed an explicitly isolated 200-example Golden Evaluation Set with stratified sampling across common, rare, high-risk, and ambiguous queries, strictly audited for zero data leakage (`Golden ∩ Train = EMPTY`).
- **Why**: Satisfies Hiver's requirement that evaluation must be conducted on a hand-reviewed, representative benchmark rather than relying solely on automated splits.
- **Alternative Considered**: Re-using the automated 1,800-case test partition as the golden set.
- **Trade-Off**: Required building dedicated extraction, leakage auditing, and human review verification templates.

---

### Decision 13: Real LLM-as-Judge Without Hidden Chain-of-Thought
- **Decision**: Implemented `LLMJudge` using an actual instruction-tuned open LLM (`Qwen/Qwen2.5-0.5B-Instruct`), evaluating 5 dimensions (Correctness, Groundedness, Relevance, Helpfulness, Safety) with short 1-2 sentence justifications without hidden chain-of-thought.
- **Why**: Direct compliance with Critical Rules 2 & 3. Structured JSON scoring allows automated parsing while short justifications maintain transparency without token bloat.
- **Alternative Considered**: Deterministic rule scoring or long multi-paragraph chain-of-thought reasoning.
- **Trade-Off**: Slower execution on CPU than heuristic evaluators (~2s per sample), but provides genuine contextual comprehension.

---

### Decision 14: Independent Human Validation Protocol
- **Decision**: Conducted a blind human evaluation across 46 representative validation cases (`data/judge_human_review.csv`, status `HUMAN_VERIFIED`, reviewer: Ansh), keeping human ratings completely blind from model predictions, and evaluated `Qwen/Qwen2.5-0.5B-Instruct` in strict `mode="llm"` with no heuristic fallback.
- **Why**: Eliminates selection bias in judge validation and establishes genuine empirical alignment between human support evaluators and open-source local LLM judges.
- **Alternative Considered**: Evaluating benchmark scores using synthetic heuristics or cases where the model was confident.
- **Trade-Off & Outcome**: Exposes that agreement is weak (near-zero Cohen's Kappa, weak/negative rank correlation, exact match 8.7%–32.6%). Consequently, **Qwen-0.5B is NOT validated as a replacement for human evaluation** and its scores are not used as a headline quality claim; human review remains the sole reference standard for ground truth.

---

### Decision 15: Selective Prediction (Accuracy over Coverage)
- **Decision**: Tuned the default Trust Gate threshold to **0.75 confidence** using the 1,801-case validation partition, yielding **16.44% automation coverage** ($N=296$) with **90.88% selective accuracy** on the 1,800 unseen test set, and **22.00% coverage** ($N=44$) with **81.82% selective accuracy** on the 200 hard Golden set (while confidence alone at $\tau \ge 0.75$ yielded 17.89% and 24.5% coverage respectively).
- **Why**: An autonomous support agent must prioritize precision over raw deflection. A >90% accurate bot that answers ~16% of inquiries safely is infinitely more valuable to an enterprise than a 68% accurate bot that attempts 100% of inquiries and misinforms one out of three customers.
- **Alternative Considered**: Optimizing for maximum coverage (e.g. threshold 0.50 with 51% coverage but 59% accuracy).
- **Trade-Off**: Human agents must still handle ~84% of inquiries, but the business guarantees near-zero catastrophic automated blunders on critical customer interactions (0.22% unsafe rate).
