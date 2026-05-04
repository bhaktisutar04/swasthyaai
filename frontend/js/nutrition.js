requireAuth();
resetIdleTimer();
document.getElementById("bottom-nav").innerHTML = renderBottomNav("home");

const sessionId = localStorage.getItem("current_session_id");
let currentDay = 0;
let mealPlan = [];

async function loadNutrition() {
  try {
    // Load trends
    const trendsRes = await apiFetch("/nutrition/trends?days=7");
    if (trendsRes) {
      const trendsData = await trendsRes.json();
      if (trendsData.success) {
        renderNutritionChart(
          trendsData.data.labels,
          trendsData.data.scores
        );
      }
    }

    // Load from report if session exists
    if (sessionId) {
      const reportRes = await apiFetch(
        `/consultation/report/${sessionId}`
      );
      if (reportRes) {
        const reportData = await reportRes.json();
        if (reportData.success) {
          const n = reportData.data.nutrition;
          renderFocus(n);
          renderDeficiencies(n);
          if (n && n.meal_plan && n.meal_plan.length > 0) {
            mealPlan = n.meal_plan;
            renderMealPlan();
          } else {
            document.getElementById("meal-plan-content").innerHTML =
              `<div class="empty-state" style="padding:24px;">
                <div class="empty-state-icon">🥗</div>
                <div class="empty-state-title">No Meal Plan Yet</div>
                <div class="empty-state-text">
                  Complete a consultation to get your personalized 
                  Indian meal plan.
                </div>
                <button class="btn btn-primary"
                        style="margin-top:16px;max-width:200px;"
                        onclick="window.location.href='consultation.html'">
                  Start Consultation
                </button>
              </div>`;
          }
        }
      }
    }
  } catch(err) {
    console.error("Nutrition load error:", err);
    // Replace skeletons with empty states on error
    document.getElementById("focus-content").innerHTML = 
      '<div class="text-muted">Complete a consultation to see your nutrition focus.</div>';
    document.getElementById("deficiency-content").innerHTML = 
      '<div class="text-muted">No data available.</div>';
    document.getElementById("meal-plan-content").innerHTML = 
      '<div class="text-muted">No meal plan available.</div>';
  }
}

function renderFocus(n) {
  document.getElementById("focus-content").innerHTML = n?.nutritional_focus
    ? `<div style="font-size:16px;font-weight:500;color:var(--primary);">
         ${n.nutritional_focus}
       </div>
       ${(n.nutrition_tips || []).map(tip =>
         `<div style="font-size:13px;color:var(--text-muted);
                      margin-top:8px;">💡 ${tip}</div>`
       ).join("")}`
    : `<div class="text-muted">
         Complete a consultation to see your nutrition focus.
       </div>`;
}

function renderDeficiencies(n) {
  const deficiencies = n?.deficiencies || [];
  document.getElementById("deficiency-content").innerHTML =
    deficiencies.length === 0
      ? `<div style="color:var(--success);font-size:14px;">
           ✅ No significant deficiencies detected.
         </div>`
      : deficiencies.map(d => `
          <div style="display:flex;justify-content:space-between;
                      align-items:center;padding:12px 0;
                      border-bottom:1px solid var(--border);">
            <div>
              <div style="font-weight:600;font-size:14px;">
                ${d.nutrient || d.title || d}
              </div>
              <div style="font-size:12px;color:var(--text-muted);">
                Needs improvement — follow your meal plan
              </div>
            </div>
            <span class="badge badge-warning">Low</span>
          </div>
        `).join("");
}

function renderNutritionChart(labels, scores) {
  const ctx = document.getElementById("nutrition-chart").getContext("2d");
  new Chart(ctx, {
    type: "line",
    data: {
      labels: labels || [],
      datasets: [{
        label: "Score",
        data: scores || [],
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

function renderMealPlan() {
  const day = mealPlan[currentDay];
  if (!day) return;

  const slots = ["breakfast","mid_morning","lunch","evening_snack","dinner"];
  const labels = {
    breakfast: "🌅 Breakfast",
    mid_morning: "🍎 Mid Morning",
    lunch: "🍛 Lunch",
    evening_snack: "☕ Evening Snack",
    dinner: "🌙 Dinner"
  };

  document.getElementById("meal-plan-content").innerHTML = `
    <div style="display:flex;align-items:center;
                justify-content:space-between;margin-bottom:16px;">
      <button onclick="prevDay()"
              ${currentDay === 0 ? "disabled" : ""}
              style="padding:8px 16px;border:1.5px solid var(--primary);
                     color:var(--primary);background:white;
                     border-radius:8px;cursor:pointer;font-weight:600;">
        ← Prev
      </button>
      <span style="font-weight:700;font-size:15px;">
        Day ${day.day} — ${day.day_name}
      </span>
      <button onclick="nextDay()"
              ${currentDay === mealPlan.length-1 ? "disabled" : ""}
              style="padding:8px 16px;border:1.5px solid var(--primary);
                     color:var(--primary);background:white;
                     border-radius:8px;cursor:pointer;font-weight:600;">
        Next →
      </button>
    </div>
    ${slots.map(slot => {
      const meal = day[slot];
      if (!meal) return "";
      return `
        <div style="background:var(--bg);border-radius:10px;
                    padding:12px 16px;margin-bottom:10px;">
          <div style="font-size:11px;font-weight:700;
                      color:var(--text-muted);text-transform:uppercase;
                      letter-spacing:0.5px;">${labels[slot]}</div>
          <div style="font-size:14px;margin-top:4px;">
            ${(meal.items || []).join(", ")}
          </div>
          ${meal.nutrients ? `
            <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">
              ${Object.entries(meal.nutrients)
                .map(([k,v]) => `${k}: ${v}`)
                .join(" • ")}
            </div>` : ""}
        </div>
      `;
    }).join("")}
  `;
}

function prevDay() {
  if (currentDay > 0) { currentDay--; renderMealPlan(); }
}
function nextDay() {
  if (currentDay < mealPlan.length-1) { currentDay++; renderMealPlan(); }
}

loadNutrition();

