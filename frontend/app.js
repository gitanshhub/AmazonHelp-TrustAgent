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
  const spinner = document.getElementById("loading-spinner");
  const btnText = document.querySelector(".btn-text");

  // Handle pill clicks
  pills.forEach(pill => {
    pill.addEventListener("click", () => {
      pills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      const key = pill.dataset.type;
      if (sampleInquiries[key]) {
        inputEl.value = sampleInquiries[key];
        analyzeMessage(inputEl.value);
      }
    });
  });

  // Handle form submit
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = inputEl.value.trim();
    if (!query) return;
    await analyzeMessage(query);
  });

  // Initial load
  checkBackendHealth();
  loadMetrics();
  // Auto-analyze default message
  analyzeMessage(inputEl.value);
});

async function checkBackendHealth() {
  const healthEl = document.getElementById("system-health");
  if (!healthEl) return;
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    if (res.ok) {
      const data = await res.json();
      if (data.models_loaded) {
        healthEl.className = "badge badge-status";
        healthEl.textContent = "🟢 Backend Online · Models Loaded";
      } else {
        healthEl.className = "badge badge-status offline";
        healthEl.textContent = "🟡 Initializing Models...";
      }
    } else {
      healthEl.className = "badge badge-status offline";
      healthEl.textContent = "🔴 Offline · Server Not Started";
    }
  } catch (e) {
    healthEl.className = "badge badge-status offline";
    healthEl.textContent = "🔴 Offline · Server Not Started";
  }
}

async function analyzeMessage(text) {
  const submitBtn = document.getElementById("submit-btn");
  const steps = [
    document.getElementById("step-intent"),
    document.getElementById("step-retrieval"),
    document.getElementById("step-grounding"),
    document.getElementById("step-decision")
  ];

  try {
    submitBtn.disabled = true;
    steps.forEach(s => s.classList.add("active"));

    const response = await fetch(`${API_BASE}/api/support/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    renderResults(data);
  } catch (err) {
    console.error("Analysis failed:", err);
    alert("Could not analyze inquiry. Make sure the FastAPI backend is running.");
  } finally {
    submitBtn.disabled = false;
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

  const respBody = document.getElementById("response-body");
  const groundedBadge = document.getElementById("grounded-badge");
  const auditList = document.getElementById("audit-list");
  const casesList = document.getElementById("cases-list");
  const evidenceCount = document.getElementById("evidence-count");

  // 1. Decision Banner
  const isAuto = data.decision.action === "AUTO";
  banner.className = isAuto ? "decision-banner" : "decision-banner escalate";
  badge.className = isAuto ? "decision-badge badge-auto" : "decision-badge badge-escalate";
  badge.textContent = isAuto ? "AUTO-HANDLE" : "ESCALATE TO HUMAN";
  reasonTag.textContent = data.decision.reason_code;
  explanation.textContent = data.decision.reason;

  // Stepper outcome update for step 4 (Trust Gate)
  const stepDecision = document.getElementById("step-decision");
  if (stepDecision) {
    const stepCircle = stepDecision.querySelector(".step-circle");
    const stepLabel = stepDecision.querySelector(".step-label");
    stepDecision.classList.remove("step-auto", "step-escalate");
    if (isAuto) {
      stepDecision.classList.add("step-auto");
      if (stepCircle) stepCircle.textContent = "✓";
      if (stepLabel) stepLabel.textContent = "Trust Gate: AUTO";
    } else {
      stepDecision.classList.add("step-escalate");
      if (stepCircle) stepCircle.textContent = "⚠";
      if (stepLabel) stepLabel.textContent = "Trust Gate: ESCALATE";
    }
  }

  // 2. Intent & Confidence
  intentName.textContent = data.intent.name;
  const pct = (data.intent.confidence * 100).toFixed(1);
  confBadge.textContent = `${pct}% Confidence`;
  confBar.style.width = `${pct}%`;

  // 3. Grounded Response & Precedent Provenance Badge
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

  // 4. Audit Trail (Why section)
  auditList.innerHTML = "";
  data.audit_trail.forEach(item => {
    const li = document.createElement("li");
    const isPass = item.status === "PASS";
    li.className = isPass ? "audit-item pass" : "audit-item fail";
    li.innerHTML = `
      <span class="audit-icon">${isPass ? "✓" : "⚠"}</span>
      <span class="audit-text"><strong>${item.check}:</strong> ${item.detail}</span>
    `;
    auditList.appendChild(li);
  });

  // 5. Retrieved Evidence Cases
  casesList.innerHTML = "";
  evidenceCount.textContent = `${data.evidence.length} Cases Retrieved`;
  data.evidence.forEach(c => {
    const div = document.createElement("div");
    div.className = "case-item";
    div.innerHTML = `
      <div class="case-header">
        <span class="case-id">#${c.case_id} (${c.intent})</span>
        <span class="case-sim">${(c.similarity * 100).toFixed(1)}% match</span>
      </div>
      <div class="case-query">" ${escapeHtml(c.customer_inquiry)} "</div>
      <div class="case-res"><strong>Resolution:</strong> ${escapeHtml(c.brand_resolution)}</div>
    `;
    casesList.appendChild(div);
  });
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

    // 2. Precedent Recall@5
    const recallEl = document.getElementById("metric-recall");
    if (recallEl && data.retrieval && data.retrieval.recall_at_5 !== undefined) {
      recallEl.textContent = `${(data.retrieval.recall_at_5 * 100).toFixed(1)}%`;
    }

    // 3. Unsafe Auto-Handling Rate
    const unsafeEl = document.getElementById("metric-false-auto");
    if (unsafeEl && data.trust_gate_safety) {
      const unsafeRate = data.trust_gate_safety.unsafe_auto_handling_rate !== undefined
        ? data.trust_gate_safety.unsafe_auto_handling_rate
        : data.trust_gate_safety.false_auto_handling_rate;
      unsafeEl.textContent = `${(unsafeRate * 100).toFixed(2)}%`;
    }

    // 4. Automation Coverage
    const autoEl = document.getElementById("metric-automation");
    if (autoEl) {
      autoEl.textContent = `${autoCov.toFixed(2)}%`;
    }
  } catch (e) {
    // defaults remain
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
