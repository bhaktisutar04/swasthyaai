requireAuth();
resetIdleTimer();

document.getElementById("bottom-nav").innerHTML = renderBottomNav("history");

// Get session ID from URL params
const urlParams = new URLSearchParams(window.location.search);
const sessionId = urlParams.get("id") ||
  localStorage.getItem("current_session_id");

let reportData = null;
let currentDay = 0;

async function loadReport() {
  if (!sessionId) {
    document.getElementById("loading-state").innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">📋</div>
        <div class="empty-state-title">No Report Found</div>
        <div class="empty-state-text">
          Please complete a consultation first.
        </div>
        <button class="btn btn-primary" style="margin-top:16px;max-width:200px;"
                onclick="window.location.href='consultation.html'">
          Start Consultation
        </button>
      </div>
    `;
    return;
  }

  try {
    const res = await apiFetch(`/consultation/report/${sessionId}`);
    if (!res) return;
    const data = await res.json();

    document.getElementById("loading-state").style.display = "none";
    document.getElementById("report-content").style.display = "block";

    if (data.success) {
      reportData = data.data;
      renderReport(reportData);
    } else {
      showError("loading-state", "Failed to load report.");
    }
  } catch (err) {
    console.error("Report error:", err);
  }
}

function renderReport(d) {
  // Session badge
  document.getElementById("session-badge").textContent = d.session_id || "";

  // Report header
  const primaryCondition = d.diagnosis?.conditions?.[0]?.name || "Health Assessment";
  document.getElementById("report-title").textContent = primaryCondition;
  document.getElementById("report-subtitle").textContent =
    `${d.patient?.name || ""} • ${formatDate(d.session_date)} • ${d.patient?.city || ""}`;

  // Severity badge
  const sf = d.diagnosis?.severity_flag || "mild";
  const severityBadge = document.getElementById("severity-badge");
  severityBadge.textContent = sf.toUpperCase();
  severityBadge.className = `badge ${getSeverityBadgeClass(sf)}`;
  severityBadge.style.background = "rgba(255,255,255,0.2)";
  severityBadge.style.color = "white";

  // See doctor badge
  const seeDoctorBadge = document.getElementById("see-doctor-badge");
  if (d.diagnosis?.see_doctor) {
    seeDoctorBadge.textContent = "⚠️ Doctor Visit Recommended";
    seeDoctorBadge.style.background = "rgba(255,255,255,0.2)";
    seeDoctorBadge.style.color = "white";
  }

  renderSymptoms(d.symptoms);
  renderDiagnosis(d.diagnosis);
  renderNutrition(d.nutrition);
  renderFinance(d.finance, d.diagnosis?.medicines || []);
}

function renderSymptoms(s) {
  if (!s) return;
  document.getElementById("symptoms-content").innerHTML = `
    <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px;">
      ${(s.list || []).map(sym =>
    `<span class="badge badge-primary">${sym}</span>`
  ).join("")}
    </div>

    ${s.emergency_flag ?
      `<div class="disclaimer disclaimer-danger" style="margin-top:12px;">
        🚨 Emergency symptoms were detected during this consultation.
       </div>` : ""}
  `;
}

function renderDiagnosis(d) {
  if (!d) {
    document.getElementById("diagnosis-content").innerHTML =
      `<div class="text-muted">Diagnosis data not yet available.</div>`;
    return;
  }

  const conditions = (d.conditions || []).map(c => `
    <div class="condition-item" style="border-left-color: ${c.likelihood === 'most_likely' ? 'var(--primary)' :
      c.likelihood === 'possible' ? 'var(--warning)' : 'var(--neutral)'}">
      <div class="condition-name">${c.name}</div>
      <div class="condition-meta">
        <span class="badge ${c.likelihood === 'most_likely' ? 'badge-primary' :
      c.likelihood === 'possible' ? 'badge-warning' : ''}">
          ${c.likelihood?.replace('_', ' ') || ""}
        </span>
        <span style="font-size:12px;color:var(--text-muted);">
          ${c.confidence || 0}% confidence
        </span>
      </div>
      <div class="confidence-bar">
        <div class="confidence-fill"
             style="width:${c.confidence || 0}%"></div>
      </div>
      ${c.reasoning ?
      `<div style="font-size:12px;color:var(--text-muted);margin-top:8px;">
          ${c.reasoning}</div>` : ""}
    </div>
  `).join("");

  const medicines = (d.medicines || []).map(m => `
    <div class="medicine-item">
      <div class="medicine-icon">💊</div>
      <div>
        <div class="medicine-name">${m.name}</div>
        <div class="medicine-use">${m.use}</div>
      </div>
    </div>
  `).join("");

  const homeCare = (d.home_care || []).map(h =>
    `<div style="padding:6px 0;font-size:14px;">✅ ${h}</div>`
  ).join("");

  const redFlags = (d.red_flags || []).map(r =>
    `<div style="padding:6px 0;font-size:14px;color:var(--danger);">🚩 ${r}</div>`
  ).join("");

  document.getElementById("diagnosis-content").innerHTML = `
    ${conditions.length ? conditions :
      '<div class="text-muted">No conditions identified yet.</div>'}

    ${d.specialist_type ? `
      <div style="background:var(--primary-light);padding:12px;
                  border-radius:var(--radius-sm);margin:16px 0;">
        👨⚕️ <strong>Recommended Specialist:</strong> ${d.specialist_type}
      </div>` : ""}

    ${medicines.length ? `
      <div style="margin-top:16px;">
        <div style="font-size:13px;font-weight:700;margin-bottom:8px;
                    color:var(--text-muted);">MEDICINES (FOR REFERENCE ONLY)</div>
        <div class="disclaimer" style="margin-bottom:12px;">
          💊 Do NOT self-medicate. Consult a doctor before taking any medication.
        </div>
        ${medicines}
      </div>` : ""}

    ${homeCare ? `
      <div style="margin-top:16px;">
        <div style="font-size:13px;font-weight:700;margin-bottom:8px;
                    color:var(--text-muted);">HOME CARE</div>
        ${homeCare}
      </div>` : ""}

    ${redFlags ? `
      <div style="margin-top:16px;">
        <div style="font-size:13px;font-weight:700;margin-bottom:8px;
                    color:var(--danger);">RED FLAGS — SEEK IMMEDIATE CARE IF:</div>
        ${redFlags}
      </div>` : ""}
  `;
}

function renderNutrition(n) {
  if (!n || !n.meal_plan || n.meal_plan.length === 0) {
    document.getElementById("nutrition-content").innerHTML =
      `<div class="text-muted">
        Nutrition plan not yet generated.
        Complete a full consultation to get your meal plan.
       </div>`;
    return;
  }

  const deficiencies = (n.deficiencies || []).map(d => `
    <div class="deficiency-item">
      <div>
        <div class="deficiency-name">
          ${d.nutrient || d.title || d}
        </div>
        <div style="font-size:12px;color:var(--text-muted);">
          Needs improvement — follow your meal plan
        </div>
      </div>
      <span class="badge badge-warning">Low</span>
    </div>
  `).join("");

  document.getElementById("nutrition-content").innerHTML = `
    ${n.nutritional_focus ? `
      <div style="background:var(--primary-light);padding:12px;
                  border-radius:var(--radius-sm);margin-bottom:16px;
                  font-size:14px;color:var(--primary);font-weight:500;">
        🎯 ${n.nutritional_focus}
      </div>` : ""}

    ${deficiencies ? `
      <div style="margin-bottom:16px;">${deficiencies}</div>` : ""}

    <div class="day-nav">
      <button class="day-nav-btn" id="prev-day"
              onclick="changeDay(-1)" disabled>← Prev</button>
      <span style="font-weight:700;" id="day-label">Day 1 — Monday</span>
      <button class="day-nav-btn" id="next-day"
              onclick="changeDay(1)">Next →</button>
    </div>
    <div id="meal-plan-day"></div>
    <div class="disclaimer" style="margin-top:12px;">
      🥗 This meal plan is AI-generated.
      Consult a certified nutritionist for chronic conditions.
    </div>
  `;

  renderMealDay(0, n.meal_plan);
}

function renderMealDay(index, mealPlan) {
  currentDay = index;
  const day = mealPlan[index];
  if (!day) return;

  document.getElementById("day-label").textContent =
    `Day ${day.day} — ${day.day_name}`;
  document.getElementById("prev-day").disabled = index === 0;
  document.getElementById("next-day").disabled =
    index === mealPlan.length - 1;

  const slots = ["breakfast", "mid_morning", "lunch", "evening_snack", "dinner"];
  const labels = {
    breakfast: "🌅 Breakfast",
    mid_morning: "🍎 Mid Morning",
    lunch: "🍛 Lunch",
    evening_snack: "☕ Evening Snack",
    dinner: "🌙 Dinner"
  };

  document.getElementById("meal-plan-day").innerHTML = slots.map(slot => {
    const meal = day[slot];
    if (!meal) return "";
    return `
      <div class="meal-slot">
        <div class="meal-slot-label">${labels[slot]}</div>
        <div class="meal-slot-items">
          ${(meal.items || []).join(", ")}
        </div>
        ${meal.nutrients ? `
          <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">
            ${Object.entries(meal.nutrients)
          .map(([k, v]) => `${k}: ${v}`)
          .join(" • ")}
          </div>` : ""}
      </div>
    `;
  }).join("");
}

function changeDay(direction) {
  if (!reportData?.nutrition?.meal_plan) return;
  const newDay = currentDay + direction;
  if (newDay >= 0 && newDay < reportData.nutrition.meal_plan.length) {
    renderMealDay(newDay, reportData.nutrition.meal_plan);
  }
}

function renderFinance(f, medicines = []) {
  if (!f) {
    document.getElementById("finance-content").innerHTML =
      `<div class="text-muted">No expense data available.</div>`;
    return;
  }

  const breakdown = f.expense_breakdown || {};
  const rows = Object.entries(breakdown).map(([cat, amt]) => `
    <div class="finance-row">
      <div class="finance-label">${cat.charAt(0).toUpperCase() + cat.slice(1)}</div>
      <div class="finance-amount">${formatRupee(amt)}</div>
    </div>
  `).join("");

  document.getElementById("finance-content").innerHTML = `
    <div style="text-align:center;padding:16px 0;margin-bottom:16px;
                border-bottom:1px solid var(--border);">
      <div style="font-size:36px;font-weight:800;color:var(--primary);">
        ${formatRupee(f.monthly_total || 0)}
      </div>
      <div style="color:var(--text-muted);font-size:13px;">This Month Total</div>
    </div>

    ${rows}

    ${f.savings_estimate > 0 ? `
      <div style="background:#d1fae5;border-radius:var(--radius-sm);
                  padding:16px;margin-top:16px;">
        <div style="font-size:13px;font-weight:700;color:#065f46;">
          💡 ESTIMATED SAVINGS WITH NUTRITION PLAN
        </div>
        <div style="font-size:28px;font-weight:800;color:#065f46;margin-top:4px;">
          ${formatRupee(f.savings_estimate)}/month
        </div>
        <div style="font-size:11px;color:#065f46;margin-top:4px;opacity:0.8;">
          ${f.savings_disclaimer || "Estimated projection. Actual savings may vary."}
        </div>
      </div>` : ""}
  `;
}

// Collapsible sections
function toggleSection(section) {
  const body = document.getElementById(`body-${section}`);
  const arrow = document.getElementById(`arrow-${section}`);
  body.classList.toggle("open");
  arrow.classList.toggle("open");
}

// Download PDF
async function downloadPDF() {
  if (!sessionId) return;
  try {
    const res = await apiFetch(
      `/consultation/report/${sessionId}/pdf`
    );
    if (!res) return;

    if (res.status === 404) {
      alert("PDF not yet generated. Please complete the full consultation first.");
      return;
    }

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `SwasthyaAI_Report_${sessionId}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (err) {
    alert("Could not download PDF. Please try again.");
  }
}

loadReport();