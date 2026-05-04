requireAuth();
resetIdleTimer();
document.getElementById("bottom-nav").innerHTML = renderBottomNav("history");

let allConsultations = [];
let currentPage = 1;
let totalPages = 1;
let nutritionTrendChart = null;
let expenseTrendChart = null;

// Tab switching
function switchTab(tab) {
  document.getElementById("timeline-section").style.display =
    tab === "timeline" ? "block" : "none";
  document.getElementById("trends-section").style.display =
    tab === "trends" ? "block" : "none";
  document.getElementById("tab-timeline").className =
    "tab" + (tab === "timeline" ? " active" : "");
  document.getElementById("tab-trends").className =
    "tab" + (tab === "trends" ? " active" : "");

  if (tab === "trends") loadTrends();
}

// Load consultation history
async function loadHistory(reset = true) {
  if (reset) {
    currentPage = 1;
    allConsultations = [];
  }

  try {
    const status = document.getElementById("filter-status").value;
    let url = `/history?page=${currentPage}&limit=10`;
    if (status) url += `&condition=${status}`;

    const res = await apiFetch(url);
    if (!res) return;
    const data = await res.json();

    if (data.success) {
      const consultations = data.data.consultations || [];
      totalPages = data.data.total_pages || 1;

      if (reset) {
        allConsultations = consultations;
      } else {
        allConsultations = [...allConsultations, ...consultations];
      }

      // Update stats
      document.getElementById("total-count").textContent =
        data.data.total || 0;
      document.getElementById("completed-count").textContent =
        consultations.filter(c => c.status === "completed").length;
      document.getElementById("followup-count").textContent =
        consultations.filter(
          c => c.status === "follow_up_pending"
        ).length;

      renderTimeline(allConsultations);

      // Show/hide load more
      document.getElementById("load-more-btn").style.display =
        currentPage < totalPages ? "block" : "none";
    }
  } catch(err) {
    console.error("History load error:", err);
    document.getElementById("timeline-list").innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">📋</div>
        <div class="empty-state-title">No History Yet</div>
        <div class="empty-state-text">
          Complete your first consultation to see it here.
        </div>
        <button class="btn btn-primary"
                style="margin-top:16px;max-width:200px;"
                onclick="window.location.href='consultation.html'">
          Start Consultation
        </button>
      </div>
    `;
  }
}

function renderTimeline(consultations) {
  const el = document.getElementById("timeline-list");

  if (consultations.length === 0) {
    el.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">📋</div>
        <div class="empty-state-title">No Consultations Found</div>
        <div class="empty-state-text">
          Try adjusting your filters or start a new consultation.
        </div>
        <button class="btn btn-primary"
                style="margin-top:16px;max-width:200px;"
                onclick="window.location.href='consultation.html'">
          Start Consultation
        </button>
      </div>
    `;
    return;
  }

  el.innerHTML = consultations.map(c => {
    const statusColors = {
      "completed": "badge-success",
      "follow_up_pending": "badge-warning",
      "in_progress": "badge-primary"
    };
    const statusLabels = {
      "completed": "✅ Completed",
      "follow_up_pending": "⏰ Follow-up Pending",
      "in_progress": "🔄 In Progress"
    };
    const severityClass = getSeverityBadgeClass(c.severity_flag);

    return `
      <div class="timeline-item">
        <div class="timeline-date">
          📅 ${formatDate(c.session_date)}
        </div>
        <div class="timeline-condition">
          ${c.primary_condition || "Health Consultation"}
        </div>
        <div class="timeline-meta">
          <span class="badge ${statusColors[c.status] || 'badge-primary'}">
            ${statusLabels[c.status] || c.status}
          </span>
          ${c.severity_flag ?
            `<span class="badge ${severityClass}">
              ${c.severity_flag}
            </span>` : ""}
          ${c.pdf_available ?
            `<span class="badge badge-success">📄 PDF Ready</span>` : ""}
        </div>
        <div style="display:flex;gap:8px;">
          <button class="btn btn-primary btn-sm"
                  onclick="viewReport('${c.consultation_id}')">
            View Report →
          </button>
          ${c.pdf_available ?
            `<button class="btn btn-outline btn-sm"
                     onclick="downloadPDF('${c.consultation_id}')">
              📥 PDF
            </button>` : ""}
        </div>
      </div>
    `;
  }).join("");
}

// Filter timeline
function filterTimeline() {
  const search = document.getElementById("search-input")
    .value.toLowerCase();
  const status = document.getElementById("filter-status").value;

  const filtered = allConsultations.filter(c => {
    const matchSearch = !search ||
      (c.primary_condition || "").toLowerCase().includes(search);
    const matchStatus = !status || c.status === status;
    return matchSearch && matchStatus;
  });

  renderTimeline(filtered);
}

// Load more pagination
function loadMore() {
  currentPage++;
  loadHistory(false);
}

// View report
function viewReport(consultationId) {
  localStorage.setItem("current_session_id", consultationId);
  window.location.href = `report.html?id=${consultationId}`;
}

// Download PDF
async function downloadPDF(consultationId) {
  try {
    const res = await apiFetch(
      `/consultation/report/${consultationId}/pdf`
    );
    if (!res) return;
    if (res.status === 404) {
      alert("PDF not available for this consultation.");
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `SwasthyaAI_Report_${consultationId}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  } catch(err) {
    alert("Could not download PDF.");
  }
}

// Load trend charts
async function loadTrends() {
  const range = document.getElementById("trend-range").value;

  try {
    // Nutrition trends
    const nutRes = await apiFetch(
      `/history/analytics/nutrition?range=${range}`
    );
    if (nutRes) {
      const nutData = await nutRes.json();
      if (nutData.success) {
        renderNutritionTrendChart(nutData.data);
        document.getElementById("nutrition-trend-summary").textContent =
          `Current Score: ${nutData.data.current_score}% • ` +
          `Change vs last week: ${nutData.data.change_vs_last_week > 0 ?
            '+' : ''}${nutData.data.change_vs_last_week}%`;
      }
    }

    // Expense trends
    const expRes = await apiFetch(
      `/history/analytics/expenses?range=${range}`
    );
    if (expRes) {
      const expData = await expRes.json();
      if (expData.success) {
        renderExpenseTrendChart(expData.data);
        document.getElementById("expense-trend-summary").textContent =
          `Current Month: ${formatRupee(expData.data.current_month)} • ` +
          `Trend: ${expData.data.trend}`;
      }
    }
  } catch(err) {
    console.error("Trends load error:", err);
  }
}

function renderNutritionTrendChart(data) {
  const ctx = document.getElementById("nutrition-trend-chart")
    .getContext("2d");
  if (nutritionTrendChart) nutritionTrendChart.destroy();
  nutritionTrendChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: data.labels || [],
      datasets: [{
        label: "Nutrition Score",
        data: data.scores || [],
        borderColor: "#1E8E3E",
        backgroundColor: "rgba(30,142,62,0.08)",
        tension: 0.4,
        fill: true,
        pointBackgroundColor: "#1E8E3E",
        pointRadius: 5
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        y: { min: 0, max: 100,
             ticks: { callback: v => v + "%" } },
        x: { grid: { display: false } }
      }
    }
  });
}

function renderExpenseTrendChart(data) {
  const ctx = document.getElementById("expense-trend-chart")
    .getContext("2d");
  if (expenseTrendChart) expenseTrendChart.destroy();
  expenseTrendChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: data.labels || [],
      datasets: [{
        label: "Monthly Expenses",
        data: data.totals || [],
        backgroundColor: "rgba(26,115,232,0.7)",
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        y: { ticks: { callback: v => "₹" + v } },
        x: { grid: { display: false } }
      }
    }
  });
}

// Initial load
loadHistory();

