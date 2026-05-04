requireAuth();
resetIdleTimer();
document.getElementById("bottom-nav").innerHTML = renderBottomNav("expenses");

// Set today's date as default
document.getElementById("exp-date").valueAsDate = new Date();

async function loadExpenses() {
  try {
    const res = await apiFetch("/finance/summary");
    if (!res) return;
    const data = await res.json();

    if (data.success) {
      const d = data.data;

      // Monthly summary
      const changeColor = d.change_percent <= 0 ?
        "var(--success)" : "var(--danger)";
      const changeArrow = d.change_percent <= 0 ? "↓" : "↑";
      document.getElementById("monthly-summary").innerHTML = `
        <div style="font-size:36px;font-weight:800;color:var(--primary);">
          ${formatRupee(d.monthly_total)}
        </div>
        <div style="font-size:13px;color:${changeColor};margin-top:4px;">
          ${changeArrow} ${Math.abs(d.change_percent)}% vs last month
        </div>
      `;

      // Savings
      if (d.savings_estimate > 0) {
        document.getElementById("savings-section").style.display = "block";
        document.getElementById("savings-amount").textContent =
          formatRupee(d.savings_estimate);
      }

      // Pie chart
      renderPieChart(d.breakdown);

      // Bar chart
      renderBarChart(d.monthly_trend);

      // Recent expenses list (from breakdown)
      renderExpensesList(d.breakdown);
    }
  } catch(err) {
    console.error("Expenses load error:", err);
  }
}

function renderPieChart(breakdown) {
  const labels = Object.keys(breakdown || {});
  const values = Object.values(breakdown || {});
  const colors = ["#1A73E8","#E8A838","#34A853","#EA4335","#9334E6"];

  const ctx = document.getElementById("pie-chart").getContext("2d");
  new Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: colors,
        borderWidth: 2,
        borderColor: "white"
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: "bottom",
                  labels: { font: { size: 11 } } }
      }
    }
  });
}

function renderBarChart(trend) {
  if (!trend || trend.length === 0) return;
  
  // Only show months with actual data
  const realData = trend.filter(t => t.total > 0);
  
  if (realData.length === 0) {
    document.getElementById("bar-chart")
      .parentElement.innerHTML = 
      '<div class="text-muted" style="padding:16px;">No expense data yet.</div>';
    return;
  }

  const ctx = document.getElementById("bar-chart").getContext("2d");
  new Chart(ctx, {
    type: "bar",
    data: {
      labels: realData.map(t => t.month),
      datasets: [{
        label: "Rs. Spent",
        data: realData.map(t => t.total),
        backgroundColor: "rgba(26,115,232,0.7)",
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        y: { ticks: { callback: v => "Rs." + v } },
        x: { grid: { display: false } }
      }
    }
  });
}

function renderExpensesList(breakdown) {
  const el = document.getElementById("expenses-list");
  const entries = Object.entries(breakdown || {})
    .filter(([,v]) => v > 0);

  if (entries.length === 0) {
    el.innerHTML = `
      <div class="empty-state" style="padding:24px 0;">
        <div class="empty-state-icon">💰</div>
        <div class="empty-state-title">No Expenses Yet</div>
        <div class="empty-state-text">
          Log your first medical expense above.
        </div>
      </div>`;
    return;
  }

  el.innerHTML = entries.map(([cat, amt]) => `
    <div class="expense-item">
      <div>
        <span class="expense-category">${cat}</span>
        <div style="font-size:13px;color:var(--text-muted);margin-top:4px;">
          This month
        </div>
      </div>
      <div style="font-size:16px;font-weight:700;">
        ${formatRupee(amt)}
      </div>
    </div>
  `).join("");
}

function toggleExpenseForm() {
  const form = document.getElementById("expense-form");
  form.classList.toggle("visible");
  hideError("expense-error");
}

async function saveExpense() {
  const date = document.getElementById("exp-date").value;
  const category = document.getElementById("exp-category").value;
  const amount = parseFloat(document.getElementById("exp-amount").value);
  const description = document.getElementById("exp-description").value;

  if (!date) {
    showError("expense-error", "Please select a date."); return;
  }
  if (!amount || amount <= 0) {
    showError("expense-error", "Please enter a valid amount."); return;
  }

  try {
    const res = await apiFetch("/finance/add-expense", {
      method: "POST",
      body: JSON.stringify({
        expense_date: date,
        category,
        amount,
        description: description || null
      })
    });
    if (!res) return;
    const data = await res.json();

    if (data.success) {
      toggleExpenseForm();
      document.getElementById("exp-amount").value = "";
      document.getElementById("exp-description").value = "";
      loadExpenses(); // Reload
    } else {
      showError("expense-error", data.message || "Failed to save expense.");
    }
  } catch(err) {
    showError("expense-error", "Network error. Please try again.");
  }
}

loadExpenses();

