// Auth guard
requireAuth();
resetIdleTimer();

// Render bottom nav
document.getElementById("bottom-nav").innerHTML = renderBottomNav("home");

// Set greeting and date
document.getElementById("greeting-text").textContent =
  `${getGreeting()}, ${getUserName()} 👋`;
document.getElementById("date-text").textContent = getCurrentDateString();

// Set user initial in avatar
const userName = getUserName();
document.getElementById("user-initial").textContent =
  userName ? userName.charAt(0).toUpperCase() : "U";

let nutritionChart = null;

async function loadDashboard() {
  try {
    const res = await apiFetch("/dashboard");
    if (!res) return;
    const data = await res.json();

    if (!data.success) {
      showEmptyState("consultation-card",
        "📋", "No consultations yet",
        "Start your first consultation to see your health summary here.");
      return;
    }

    const d = data.data;

    // Update greeting with actual name
    document.getElementById("greeting-text").textContent =
      `${getGreeting()}, ${d.greeting_name} 👋`;

    // Nutrition score
    const nsEl = document.getElementById("nutrition-score");
    nsEl.textContent = d.nutrition_score_this_week + "%";
    const nChange = d.nutrition_score_this_week - d.nutrition_score_last_week;
    document.getElementById("nutrition-change").innerHTML =
      nChange >= 0
        ? `<span class="text-success">↑ ${nChange}% from last week</span>`
        : `<span class="text-danger">↓ ${Math.abs(nChange)}% from last week</span>`;

    // Expense total
    document.getElementById("expense-total").textContent =
      formatRupee(d.monthly_expense_total);
    const eChange = d.expense_change_percent;
    document.getElementById("expense-change").innerHTML =
      eChange <= 0
        ? `<span class="text-success">↓ ${Math.abs(eChange)}% vs last month</span>`
        : `<span class="text-danger">↑ ${eChange}% vs last month</span>`;

    // Latest consultation card
    if (d.latest_consultation) {
      const c = d.latest_consultation;
      document.getElementById("consultation-content").innerHTML = `
        <div class="condition-badge">${c.primary_condition || "Unknown"}</div>
        <div style="font-size:13px;color:var(--text-muted);margin-bottom:8px;">
          ${formatDate(c.session_date)} •
          <span class="${getSeverityBadgeClass(c.severity_flag)} badge">
            ${c.severity_flag || "mild"}
          </span>
        </div>
        ${c.see_doctor ? `
          <div class="disclaimer" style="margin-bottom:8px;">
            👨⚕️ Recommended: Visit ${c.specialist_type || "a doctor"}
            within ${c.follow_up_days} days
          </div>` : ""}
        <button class="btn btn-outline btn-sm"
                onclick="window.location.href='report.html?id=${c.consultation_id}'">
          View Full Report →
        </button>
      `;
    } else {
      document.getElementById("consultation-content").innerHTML = `
        <div class="empty-state" style="padding:24px 0;">
          <div class="empty-state-icon">🩺</div>
          <div class="empty-state-text">
            No consultations yet. Start your first one!
          </div>
        </div>
      `;
    }

    // Nutrition chart
    renderNutritionChart(d.nutrition_labels, d.nutrition_scores);

    // Notifications
    renderNotifications(d.notifications);

  } catch (err) {
    console.error("Dashboard error:", err);
    document.getElementById("consultation-content").innerHTML =
      `<div class="text-muted">Unable to load data. 
       <span style="color:var(--primary);cursor:pointer"
             onclick="loadDashboard()">Retry</span></div>`;
  }
}

function renderNutritionChart(labels, scores) {
  const canvas = document.getElementById("nutrition-chart");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (nutritionChart) nutritionChart.destroy();
  nutritionChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels || [],
      datasets: [{
        label: "Nutrition Score",
        data: scores || [],
        borderColor: "#2D7DD2",
        backgroundColor: "rgba(45,125,210,0.08)",
        tension: 0.4,
        fill: true,
        pointBackgroundColor: "#2D7DD2",
        pointRadius: 4
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        y: {
          min: 0, max: 100,
          ticks: { callback: v => v + "%" }
        },
        x: { grid: { display: false } }
      }
    }
  });
}

function renderNotifications(notifications) {
  const el = document.getElementById("notifications-list");
  if (!notifications || notifications.length === 0) {
    el.innerHTML = `<div class="text-muted" style="padding:8px 0;">
      No reminders right now. You're all caught up! ✅</div>`;
    return;
  }
  el.innerHTML = notifications.map(n => `
    <div class="notification-item">
      <div class="notif-icon">
        ${n.type === "follow_up" ? "👨⚕️" :
      n.type === "refill" ? "💊" : "🔔"}
      </div>
      <div>
        <div class="notif-message">${n.message}</div>
        ${n.due_date ?
      `<div class="notif-date">Due: ${formatDate(n.due_date)}</div>` : ""}
      </div>
    </div>
  `).join("");
}

// Load dashboard data
loadDashboard();