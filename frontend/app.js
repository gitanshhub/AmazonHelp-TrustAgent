// frontend/app.js

const API_BASE = window.location.origin;

const sampleInquiries = {
  tracking: "Where is my package? The tracking number says in transit but hasn't updated in 2 days.",
  delay: "My order was supposed to arrive yesterday and is now delayed. Can you help?",
  return: "How do I return this sweater that is too small? Can I drop it off at an Amazon Locker?",
  dispute: "I see two separate $75 charges on my card for the same order! Please refund the duplicate one immediately.",
  fraud: "My credit card was stolen and someone placed a $500 order on Amazon without my permission!",
  ambiguous: "Hey someone check this thing right now it looks weird."
};

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("analyze-form");
  const inputEl = document.getElementById("customer-input");
  const pills = document.querySelectorAll(".pill");
  const retryBtn = document.getElementById("retry-health-btn");
  const retryAnalysisBtn = document.getElementById("btn-retry-analysis");
  const inputErrorMsg = document.getElementById("input-error-msg");

  // Handle pill selection
  pills.forEach(pill => {
    pill.addEventListener("click", () => {
      pills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      const key = pill.dataset.type;
      if (sampleInquiries[key]) {
        inputEl.value = sampleInquiries[key];
        clearInputError();
        analyzeMessage(inputEl.value);
      }
    });
  });

  // Clear input error on typing
  inputEl.addEventListener("input", () => {
    if (inputEl.value.trim().length > 0) {
      clearInputError();
    }
  });

  // Handle form submit
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = inputEl.value.trim();
    if (!query) {
      showInputError("Enter a customer message.");
      return;
    }
    clearInputError();
    await analyzeMessage(query);
  });

  // Retry buttons
  if (retryBtn) {
    retryBtn.addEventListener("click", () => {
      checkBackendHealth();
    });
  }

  if (retryAnalysisBtn) {
    retryAnalysisBtn.addEventListener("click", () => {
      const query = inputEl.value.trim();
      if (query) {
        analyzeMessage(query);
      }
    });
  }

  // Initial load
  checkBackendHealth();
  loadMetrics();
  
  // Auto-analyze default message
  if (inputEl.value.trim()) {
    analyzeMessage(inputEl.value.trim());
  }
});

function showInputError(msg) {
  const inputEl = document.getElementById("customer-input");
  const inputErrorMsg = document.getElementById("input-error-msg");
  if (inputEl) inputEl.classList.add("input-invalid");
  if (inputErrorMsg) {
    const textSpan = inputErrorMsg.querySelector(".error-text");
    if (textSpan) textSpan.textContent = msg;
    inputErrorMsg.style.display = "flex";
  }
}

function clearInputError() {
  const inputEl = document.getElementById("customer-input");
  const inputErrorMsg = document.getElementById("input-error-msg");
  if (inputEl) inputEl.classList.remove("input-invalid");
  if (inputErrorMsg) inputErrorMsg.style.display = "none";
}

function showApiError(title, detail) {
  const errorCard = document.getElementById("api-error-card");
  const errorTitle = document.getElementById("api-error-title");
  const errorDetail = document.getElementById("api-error-detail");
  if (errorTitle) errorTitle.textContent = title;
  if (errorDetail) errorDetail.textContent = detail;
  if (errorCard) errorCard.style.display = "flex";
}

function hideApiError() {
  const errorCard = document.getElementById("api-error-card");
  if (errorCard) errorCard.style.display = "none";
}

async function checkBackendHealth() {
  const healthEl = document.getElementById("system-health");
  const offlineBanner = document.getElementById("offline-banner");
  
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    if (res.ok) {
      const data = await res.json();
      if (data.models_loaded) {
        if (healthEl) {
          healthEl.className = "badge badge-status";
          healthEl.textContent = "🟢 Backend Online · Models Loaded";
        }
        if (offlineBanner) offlineBanner.style.display = "none";
      } else {
        if (healthEl) {
          healthEl.className = "badge badge-status offline";
          healthEl.textContent = "🟡 Initializing Models...";
        }
        if (offlineBanner) offlineBanner.style.display = "flex";
      }
    } else {
      markBackendOffline();
    }
  } catch (e) {
    markBackendOffline();
  }
}

function markBackendOffline() {
  const healthEl = document.getElementById("system-health");
  const offlineBanner = document.getElementById("offline-banner");
  if (healthEl) {
    healthEl.className = "badge badge-status offline";
    healthEl.textContent = "🔴 Offline · Server Not Started";
  }
  if (offlineBanner) {
    offlineBanner.style.display = "flex";
  }
}

async function analyzeMessage(text) {
  const submitBtn = document.getElementById("submit-btn");
  const spinner = document.getElementById("loading-spinner");
  const overlay = document.getElementById("loading-overlay");
  const stageLabel = document.getElementById("loading-stage-label");
  const statusLabel = document.getElementById("pipeline-status");

  // Stepper elements
  const steps = [
    document.getElementById("step-intent"),
    document.getElementById("step-retrieval"),
    document.getElementById("step-grounding"),
    document.getElementById("step-decision")
  ];
  const connectors = [
    document.getElementById("connector-1"),
    document.getElementById("connector-2"),
    document.getElementById("connector-3")
  ];

  hideApiError();

  try {
    if (submitBtn) submitBtn.disabled = true;
    if (spinner) spinner.style.display = "inline-block";
    if (overlay) overlay.style.display = "flex";
    if (statusLabel) statusLabel.textContent = "Evaluating Pipeline...";

    // Reset stepper UI
    steps.forEach(s => {
      if (s) {
        s.className = "step";
        s.classList.remove("active", "processing", "step-auto", "step-escalate");
      }
    });
    connectors.forEach(c => {
      if (c) c.classList.remove("passed");
    });

    // Animate stage 1
    if (stageLabel) stageLabel.textContent = "Step 1/4: Classifying Intent & Risk Profile...";
    if (steps[0]) steps[0].classList.add("processing");

    // Perform API call
    const fetchPromise = fetch(`${API_BASE}/api/support/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    });

    // Provide progressive visual feedback through stages
    await new Promise(r => setTimeout(r, 120));
    if (steps[0]) {
      steps[0].classList.remove("processing");
      steps[0].classList.add("active");
    }
    if (connectors[0]) connectors[0].classList.add("passed");
    if (steps[1]) steps[1].classList.add("processing");
    if (stageLabel) stageLabel.textContent = "Step 2/4: Retrieving Top Historical Precedents (FAISS)...";

    await new Promise(r => setTimeout(r, 120));
    if (steps[1]) {
      steps[1].classList.remove("processing");
      steps[1].classList.add("active");
    }
    if (connectors[1]) connectors[1].classList.add("passed");
    if (steps[2]) steps[2].classList.add("processing");
    if (stageLabel) stageLabel.textContent = "Step 3/4: Drafting Grounded Brand Response...";

    const response = await fetchPromise;

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Server error (${response.status})`);
    }

    if (steps[2]) {
      steps[2].classList.remove("processing");
      steps[2].classList.add("active");
    }
    if (connectors[2]) connectors[2].classList.add("passed");
    if (steps[3]) steps[3].classList.add("processing");
    if (stageLabel) stageLabel.textContent = "Step 4/4: Multi-Signal Trust Gate Verification...";

    await new Promise(r => setTimeout(r, 100));

    const data = await response.json();
    renderResults(data);

    if (statusLabel) {
      statusLabel.textContent = `Completed (${data.decision.action})`;
    }
  } catch (err) {
    console.error("Analysis failed:", err);
    showApiError("Inquiry Analysis Failed", err.message || "Failed to communicate with backend service.");
    if (statusLabel) statusLabel.textContent = "Pipeline Error";
    markBackendOffline();
  } finally {
    if (submitBtn) submitBtn.disabled = false;
    if (spinner) spinner.style.display = "none";
    if (overlay) overlay.style.display = "none";
  }
}

function renderResults(data) {
  const banner = document.getElementById("decision-banner");
  const badge = document.getElementById("decision-badge");
  const reasonTag = document.getElementById("reason-code-tag");
  const explanation = document.getElementById("decision-explanation");

  const intentName = document.getElementById("intent-name");
  const confBadge = document.getElementById("confidence-badge");
  const confBar = document.getElementById("confidence-bar-fill");
  const riskBadge = document.getElementById("risk-tier-badge");

  const respBody = document.getElementById("response-body");
  const groundedBadge = document.getElementById("grounded-badge");
  const auditList = document.getElementById("audit-list");
  const auditSummaryPill = document.getElementById("audit-summary-pill");
  const casesList = document.getElementById("cases-list");
  const evidenceCount = document.getElementById("evidence-count");

  // 1. Decision Banner (Unmistakable AUTO vs ESCALATE)
  const isAuto = data.decision.action === "AUTO";
  banner.className = isAuto ? "decision-banner" : "decision-banner escalate";
  badge.className = isAuto ? "decision-badge badge-auto" : "decision-badge badge-escalate";
  badge.textContent = isAuto ? "AUTO-HANDLE" : "ESCALATE TO HUMAN";
  reasonTag.textContent = data.decision.reason_code;
  explanation.textContent = data.decision.reason;

  // Stepper outcome update for step 4 (Trust Gate)
  const stepDecision = document.getElementById("step-decision");
  if (stepDecision) {
    const stepCircle = document.getElementById("circle-decision");
    const stepSub = document.getElementById("sub-decision");
    stepDecision.classList.remove("processing", "step-auto", "step-escalate");
    if (isAuto) {
      stepDecision.classList.add("step-auto");
      if (stepCircle) stepCircle.textContent = "✓";
      if (stepSub) stepSub.textContent = "AUTO: Passed";
    } else {
      stepDecision.classList.add("step-escalate");
      if (stepCircle) stepCircle.textContent = "⚠";
      if (stepSub) stepSub.textContent = `ESCALATE: ${data.decision.reason_code}`;
    }
  }

  // 2. Intent, Confidence, and Risk Profile
  intentName.textContent = data.intent.name;
  const pct = (data.intent.confidence * 100).toFixed(1);
  confBadge.textContent = `${pct}% Confidence`;
  confBar.style.width = `${pct}%`;

  // Infer risk tier from audit trail / reason code
  if (riskBadge) {
    const isHighRisk = data.decision.reason_code === "HIGH_RISK" || 
                       data.decision.reason_code === "PAYMENT_DISPUTE" ||
                       data.intent.name === "CRITICAL_SECURITY_FRAUD" ||
                       data.intent.name === "PAYMENT_BILLING_DISPUTE";
    const isMedRisk = data.decision.reason_code === "LOW_CONFIDENCE" || 
                      data.decision.reason_code === "NO_SIMILAR_CASE";

    if (isHighRisk) {
      riskBadge.className = "risk-tier-badge high";
      riskBadge.textContent = "HIGH RISK / FINANCIAL";
    } else if (isMedRisk) {
      riskBadge.className = "risk-tier-badge medium";
      riskBadge.textContent = "UNCERTAIN RISK";
    } else {
      riskBadge.className = "risk-tier-badge";
      riskBadge.textContent = "LOW RISK / SELF-SERVICE";
    }
  }

  // 3. Grounded Draft Response & Provenance Badge
  respBody.textContent = `"${data.response.text}"`;
  if (groundedBadge) {
    if (data.response && data.response.source === "retrieved_historical_case" && data.evidence && data.evidence.length > 0) {
      groundedBadge.className = "grounded-badge";
      groundedBadge.textContent = `✓ Adapted from Precedent #${data.evidence[0].case_id}`;
    } else if (data.response && data.response.source === "conservative_fallback") {
      groundedBadge.className = "grounded-badge fallback";
      groundedBadge.textContent = "⚠ Conservative Policy Guidance";
    } else {
      groundedBadge.className = "grounded-badge";
      groundedBadge.textContent = "✓ Grounded in Historical Cases";
    }
  }

  // 4. Top 3 Precedent Cards (Readable & Provenanced)
  casesList.innerHTML = "";
  const precedentCount = data.evidence ? data.evidence.length : 0;
  evidenceCount.textContent = `${precedentCount} Precedents Retrieved`;

  if (data.evidence && data.evidence.length > 0) {
    data.evidence.slice(0, 3).forEach((c, idx) => {
      const div = document.createElement("div");
      div.className = "case-item";
      div.innerHTML = `
        <div class="case-item-header">
          <div class="case-identity">
            <span class="case-rank">#${idx + 1}</span>
            <span class="case-id">Case #${escapeHtml(String(c.case_id))}</span>
            <span class="case-intent-chip">${escapeHtml(c.intent || "SUPPORT_QUERY")}</span>
          </div>
          <span class="case-sim">${(c.similarity * 100).toFixed(1)}% match</span>
        </div>
        <div class="case-query-box">
          <div class="case-field-lbl">Customer Inquiry:</div>
          <div class="case-query">"${escapeHtml(c.customer_inquiry)}"</div>
        </div>
        <div class="case-res-box">
          <div class="case-field-lbl">Amazon Historical Resolution:</div>
          <div class="case-res">${escapeHtml(c.brand_resolution)}</div>
        </div>
      `;
      casesList.appendChild(div);
    });
  } else {
    casesList.innerHTML = `<div class="case-item" style="color: var(--text-muted); font-size: 0.82rem;">No relevant historical precedents found in FAISS index above similarity threshold.</div>`;
  }

  // 5. Audit Trail
  auditList.innerHTML = "";
  let passCount = 0;
  data.audit_trail.forEach(item => {
    const li = document.createElement("li");
    const isPass = item.status === "PASS";
    if (isPass) passCount++;
    li.className = isPass ? "audit-item pass" : "audit-item fail";
    li.innerHTML = `
      <span class="audit-icon">${isPass ? "✓" : "⚠"}</span>
      <span class="audit-text"><strong>${escapeHtml(item.check)}:</strong> ${escapeHtml(item.detail)}</span>
    `;
    auditList.appendChild(li);
  });
  if (auditSummaryPill) {
    auditSummaryPill.textContent = `${passCount} / ${data.audit_trail.length} Checks Passed`;
  }
}

async function loadMetrics() {
  try {
    const res = await fetch(`${API_BASE}/api/support/metrics`);
    if (!res.ok) return;
    const data = await res.json();

    // 1. Full Multi-Signal Trust Gate metrics on Unseen Test Set (N=1,800)
    let selAcc = 90.88;
    let autoCov = 16.44;
    if (data.trust_gate_safety) {
      if (data.trust_gate_safety.selective_accuracy_on_automated_cohort !== undefined) {
        selAcc = data.trust_gate_safety.selective_accuracy_on_automated_cohort * 100;
      }
      if (data.trust_gate_safety.automation_rate !== undefined) {
        autoCov = data.trust_gate_safety.automation_rate * 100;
      }
    }
    const selAccEl = document.getElementById("metric-selective-accuracy");
    if (selAccEl) selAccEl.textContent = `${selAcc.toFixed(2)}%`;

    // 2. Automation Coverage
    const autoEl = document.getElementById("metric-automation");
    if (autoEl) autoEl.textContent = `${autoCov.toFixed(2)}%`;

    // 3. Precedent Recall@5
    const recallEl = document.getElementById("metric-recall");
    if (recallEl && data.retrieval && data.retrieval.recall_at_5 !== undefined) {
      recallEl.textContent = `${(data.retrieval.recall_at_5 * 100).toFixed(1)}%`;
    }

    // 4. Unsafe Auto-Handling Rate
    const unsafeEl = document.getElementById("metric-false-auto");
    if (unsafeEl && data.trust_gate_safety) {
      const unsafeRate = data.trust_gate_safety.unsafe_auto_handling_rate !== undefined
        ? data.trust_gate_safety.unsafe_auto_handling_rate
        : data.trust_gate_safety.false_auto_handling_rate;
      unsafeEl.textContent = `${(unsafeRate * 100).toFixed(2)}%`;
    }
  } catch (e) {
    // defaults remain intact (16.44% and 90.88%)
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
