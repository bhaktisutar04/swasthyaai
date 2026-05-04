# SwasthyaAI — UI Design
**Version:** 1.0  
**Date:** 2026  
**Author:** Solo Developer  
**Document:** SDD Section 5 of 7

---

## 1. Overview

SwasthyaAI has 7 HTML screens. Each screen is a separate `.html` file with its own `.js` file. They share one `style.css`. Communication with the backend is via `fetch()` API calls. JWT tokens are stored in `localStorage`.

**Frontend stack:** Plain HTML + CSS + JavaScript (no frameworks, no build step)  
**Chart library:** Chart.js (via CDN)  
**Font:** Inter (via Google Fonts)  
**Hosting:** Static files served from GitHub Pages or Render static site

---

## 2. Global Design Tokens

```css
/* css/style.css — global variables */
:root {
    --primary:      #2D7DD2;   /* Blue — main CTA buttons */
    --success:      #3BB273;   /* Green — mild severity, completed */
    --warning:      #F4A261;   /* Amber — moderate, follow-up */
    --danger:       #E63946;   /* Red — severe, emergency */
    --neutral:      #6B7280;   /* Gray — less likely, secondary text */
    --bg:           #F8FAFC;   /* Page background */
    --card-bg:      #FFFFFF;   /* Card background */
    --text-primary: #1A1A2E;   /* Main text */
    --text-muted:   #6B7280;   /* Secondary text */
    --border:       #E5E7EB;   /* Borders */
    --font:         'Inter', sans-serif;
    --radius:       12px;      /* Card border radius */
    --shadow:       0 2px 8px rgba(0,0,0,0.08);
}
```

---

## 3. Screen 1 — Login / Register (`index.html`)

### Purpose
First screen. Handles both sign up and sign in. Tab toggle between forms.

### API Calls
| Action | Endpoint |
|---|---|
| Register | `POST /auth/register` |
| Login | `POST /auth/login` |

### Components

```
┌─────────────────────────────────────┐
│         SwasthyaAI Logo             │
│    AI Health Companion for India    │
│                                     │
│  [  Login  ]  [  Register  ]  ← tabs│
│                                     │
│  ── LOGIN FORM ──                   │
│  Email: [_________________________] │
│  Password: [____________________]👁 │
│  Forgot Password?                   │
│  [        LOGIN        ]            │
│  Don't have an account? Sign Up     │
│                                     │
│  ── REGISTER FORM ──                │
│  Full Name: [_____________________] │
│  Age: [___]  Gender: [▼ Select   ] │
│  City: [__________________________] │
│  Dietary: ( )Veg  ( )Non-Veg  ( )Vegan│
│  Language: [▼ English             ] │
│  Email: [_________________________] │
│  Password: [____________________]👁 │
│  ☐ I agree to Terms & Privacy       │
│  [      CREATE ACCOUNT      ]       │
└─────────────────────────────────────┘
```

### JS Logic (`js/auth.js`)

```javascript
// auth.js

const API_BASE = "http://localhost:8000";

// Tab toggle
document.getElementById("tab-login").onclick = () => showForm("login");
document.getElementById("tab-register").onclick = () => showForm("register");

// Login handler
async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById("login-email").value;
    const password = document.getElementById("login-password").value;

    try {
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();

        if (data.success) {
            localStorage.setItem("access_token", data.data.access_token);
            localStorage.setItem("refresh_token", data.data.refresh_token);
            localStorage.setItem("user_name", data.data.name);
            window.location.href = "dashboard.html";
        } else {
            showError("login-error", data.message);
        }
    } catch (err) {
        showError("login-error", "Network error. Please try again.");
    }
}

// Register handler — similar pattern, calls /auth/register

// Guard: if already logged in, redirect
if (localStorage.getItem("access_token")) {
    window.location.href = "dashboard.html";
}
```

### Validation Rules (client-side)
- Name: 2–50 chars
- Age: 1–120
- Email: regex `/^[^\s@]+@[^\s@]+\.[^\s@]+$/`
- Password: min 8 chars, uppercase + lowercase + digit + special char
- Terms checkbox: must be checked

---

## 4. Screen 2 — Dashboard (`dashboard.html`)

### Purpose
Home screen after login. Shows summary of last consultation, nutrition score, expenses, and notifications.

### API Calls
| Action | Endpoint |
|---|---|
| Load dashboard | `GET /dashboard` |

### Layout

```
┌─────────────────────────────────────┐
│ SwasthyaAI        👤 Rahul   ☰     │
├─────────────────────────────────────┤
│  👋 Good Morning, Rahul Kumar       │
│  Tuesday, April 21, 2026            │
├─────────────────────────────────────┤
│  🩺 QUICK ACTIONS                   │
│  [+ START NEW CONSULTATION]         │
│  [📍 FIND DOCTORS NEAR ME]          │
├─────────────────────────────────────┤
│  📋 LATEST CONSULTATION             │
│  Date: April 18, 2026               │
│  Condition: Common Cold             │
│  Status: Follow-up in 5 days        │
│  [View Full Report →]               │
├─────────────────────────────────────┤
│  📊 HEALTH AT A GLANCE              │
│  Nutrition Score: 85% ↑             │
│  [line chart — 7 days]              │
│  💰 Expenses (April): ₹4,500 ↓10%  │
├─────────────────────────────────────┤
│  🔔 REMINDERS (2)                   │
│  ! Follow-up with GP in 5 days      │
│  💊 Iron supplement refill tomorrow │
├─────────────────────────────────────┤
│  🏠  🩺  💰  📊  👤                │  ← bottom nav
└─────────────────────────────────────┘
```

### JS Logic (`js/dashboard.js`)

```javascript
async function loadDashboard() {
    const token = localStorage.getItem("access_token");
    if (!token) { window.location.href = "index.html"; return; }

    showSkeletonLoaders();

    try {
        const res = await fetch(`${API_BASE}/dashboard`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        const data = await res.json();

        if (res.status === 401) { handleTokenExpiry(); return; }

        if (data.success) {
            renderGreeting(data.data.greeting_name);
            renderLatestConsultation(data.data.latest_consultation);
            renderNutritionChart(data.data);
            renderExpenses(data.data);
            renderNotifications(data.data.notifications);
        }
    } catch (err) {
        showError("Unable to load dashboard. Retry?");
    }
}

// Nutrition Score Chart using Chart.js
function renderNutritionChart(data) {
    const ctx = document.getElementById("nutrition-chart").getContext("2d");
    new Chart(ctx, {
        type: "line",
        data: {
            labels: data.nutrition_labels,
            datasets: [{
                label: "Nutrition Score",
                data: data.nutrition_scores,
                borderColor: "#2D7DD2",
                tension: 0.4,
                fill: false
            }]
        },
        options: { responsive: true, scales: { y: { min: 0, max: 100 } } }
    });
}
```

### States
- **Loading state:** Skeleton loaders on all cards
- **Empty state:** "Welcome! Start your first consultation" if no history
- **Error state:** "Unable to load data. [Retry]" button

---

## 5. Screen 3 — Consultation Chat (`consultation.html`)

### Purpose
Chat interface for the patient to talk with the agents. Shows typing indicators, handles emergencies.

### API Calls
| Action | Endpoint |
|---|---|
| Start consultation | `POST /consultation/start` |
| Send message | `POST /consultation/message` |

### Layout

```
┌─────────────────────────────────────┐
│ ← Back   🩺 AI Consultation   [ X ] │
├─────────────────────────────────────┤
│                                     │
│  AI: Namaste Rahul! How are you     │  ← AI bubble (left)
│  feeling today?        10:30 AM     │
│                                     │
│    I have a cough and fever.        │  ← User bubble (right)
│                        10:31 AM     │
│                                     │
│  AI: How long have you had          │
│  these symptoms?       10:31 AM     │
│                                     │
│  🤖 Agent is typing...              │  ← typing indicator
│                                     │
├─────────────────────────────────────┤
│  [Type your message...      ] [Send]│
│  [    END CONSULTATION    ]         │
└─────────────────────────────────────┘

── EMERGENCY MODAL (overlays screen) ──
┌─────────────────────────────────────┐
│  ⚠️ EMERGENCY ALERT                 │
│  Symptoms may need immediate care   │
│                                     │
│  1. City General Hospital           │
│     1.2 km · 📞 [Call Now]         │
│     [Get Directions →]              │
│  2. CarePlus Medical Center         │
│     2.5 km · 📞 [Call Now]         │
│     [Get Directions →]              │
│  3. Emergency Care Clinic           │
│     3.1 km · 📞 [Call Now]         │
│     [Get Directions →]              │
│                                     │
│  [📞 CALL 108]                      │
│  [I UNDERSTAND — DISMISS]           │
└─────────────────────────────────────┘
```

### JS Logic (`js/consultation.js`)

```javascript
let sessionId = null;

async function startConsultation() {
    const res = await fetch(`${API_BASE}/consultation/start`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${getToken()}` }
    });
    const data = await res.json();
    sessionId = data.data.session_id;
    appendMessage("ai", data.data.greeting);
}

async function sendMessage() {
    const input = document.getElementById("chat-input");
    const message = input.value.trim();
    if (!message) return;

    appendMessage("user", message);
    input.value = "";
    showTypingIndicator();

    const res = await fetch(`${API_BASE}/consultation/message`, {
        method: "POST",
        headers: {
            "Authorization": `Bearer ${getToken()}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ session_id: sessionId, message })
    });
    const data = await res.json();
    hideTypingIndicator();

    if (data.data.emergency_detected) {
        showEmergencyModal(data.data.hospitals);
        return;
    }

    appendMessage("ai", data.data.response);

    if (data.data.consultation_complete) {
        setTimeout(() => {
            window.location.href = `report.html?id=${sessionId}`;
        }, 1500);
    }
}

function showEmergencyModal(hospitals) {
    document.getElementById("emergency-modal").style.display = "flex";
    const list = document.getElementById("hospital-list");
    hospitals.forEach((h, i) => {
        list.innerHTML += `
            <div class="hospital-card">
                <strong>${i + 1}. ${h.name}</strong>
                <a href="${h.maps_link}" target="_blank">Get Directions →</a>
            </div>`;
    });
}

function appendMessage(role, text) {
    const chat = document.getElementById("chat-window");
    const div = document.createElement("div");
    div.className = `message ${role}`;
    div.innerHTML = `<p>${text}</p><span class="timestamp">${getTime()}</span>`;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}
```

---

## 6. Screen 4 — Health Report (`report.html`)

### Purpose
Shows the full 4-section report after consultation. Download PDF button.

### API Calls
| Action | Endpoint |
|---|---|
| Load report | `GET /consultation/report/{session_id}` |
| Download PDF | `GET /consultation/report/{session_id}/pdf` |

### Layout

```
┌─────────────────────────────────────┐
│ ← Dashboard  📄 Health Report       │
│ Consultation #CNS-2026-04-001       │
│ April 21, 2026                      │
├─────────────────────────────────────┤
│ 👤 Rahul Kumar · 32 · Male · Pune   │
├─────────────────────────────────────┤
│ ▼ 1. SYMPTOM SUMMARY          [▼] │
│   Cough, fever · 3 days · 6/10     │
│   No emergency                      │
├─────────────────────────────────────┤
│ ▼ 2. DIAGNOSIS                [▼] │
│  🟢 Common Cold       75%          │
│  🟡 Allergic Rhinitis 15%          │
│  ⚪ Mild Bronchitis   10%          │
│  Specialist: General Physician      │
│  💊 Paracetamol · Cetirizine        │
│  ⚠️ Consult doctor before use       │
├─────────────────────────────────────┤
│ ▼ 3. 7-DAY NUTRITION PLAN     [▼] │
│  Focus: Vitamin C + Zinc            │
│  Day 1: Poha · Palak Dal...         │
│  [View Full Plan →]                 │
├─────────────────────────────────────┤
│ ▼ 4. FINANCIAL SUMMARY        [▼] │
│  Spent: ₹4,500 · Savings: ₹1,200   │
│  [View Breakdown →]                 │
├─────────────────────────────────────┤
│ ▼ 5. NEXT STEPS               [▼] │
│  ✓ Follow nutrition plan            │
│  ✓ Monitor symptoms 5-7 days        │
│  ✓ See GP if symptoms worsen        │
├─────────────────────────────────────┤
│  ⚠️ AI analysis — not medical advice│
├─────────────────────────────────────┤
│  [📥 DOWNLOAD PDF]                  │
│  [📧 EMAIL] [📱 SHARE] [🖨️ PRINT]  │
└─────────────────────────────────────┘
```

### Collapsible Sections

```javascript
document.querySelectorAll(".section-header").forEach(header => {
    header.onclick = () => {
        const body = header.nextElementSibling;
        body.style.display = body.style.display === "none" ? "block" : "none";
        header.querySelector(".toggle-icon").textContent =
            body.style.display === "none" ? "▶" : "▼";
    };
});
```

### PDF Download

```javascript
async function downloadPDF() {
    const sessionId = new URLSearchParams(window.location.search).get("id");
    const res = await fetch(`${API_BASE}/consultation/report/${sessionId}/pdf`, {
        headers: { "Authorization": `Bearer ${getToken()}` }
    });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `SwasthyaAI_Report_${sessionId}.pdf`;
    a.click();
}
```

---

## 7. Screen 5 — Nutrition Dashboard (`nutrition.html`)

### Purpose
Shows the 7-day meal plan, deficiency indicators, and weekly trends.

### API Calls
| Action | Endpoint |
|---|---|
| Get trends | `GET /nutrition/trends` |
| Log meal | `POST /nutrition/log-meal` |

### Layout

```
┌─────────────────────────────────────┐
│ 🥗 NUTRITION DASHBOARD              │
├─────────────────────────────────────┤
│ 📊 Nutrition Focus:                 │
│ Increasing Iron & Vitamin B12       │
│ Target: Iron 18mg/day               │
├─────────────────────────────────────┤
│ [Weekly Score Chart — line chart]   │
│ Current: 85% ↑ +5% from last week  │
├─────────────────────────────────────┤
│ 📅 DAY 1 — Monday                   │
│ 🌅 Breakfast: Poha with Peanuts     │
│    → Iron 3mg, Vitamin C            │
│ 🍛 Lunch: Palak Dal + Jowar Roti    │
│    → Iron 5mg, Fiber                │
│ 🌙 Dinner: Moong Dal Khichdi        │
│    → Iron 4mg, Probiotics           │
├─────────────────────────────────────┤
│ [← Day]  Day 1 of 7  [Day →]       │
├─────────────────────────────────────┤
│ [+ LOG TODAY'S MEALS]               │
│ [🔄 REGENERATE PLAN]                │
│ [📥 DOWNLOAD PDF]                   │
└─────────────────────────────────────┘
```

### Day Navigator
```javascript
let currentDay = 0;
const mealPlan = JSON.parse(localStorage.getItem("meal_plan") || "[]");

function showDay(index) {
    currentDay = index;
    const day = mealPlan[index];
    document.getElementById("day-title").textContent = `Day ${day.day} — ${day.day_name}`;
    renderMeals(day);
    document.getElementById("prev-btn").disabled = index === 0;
    document.getElementById("next-btn").disabled = index === 6;
}
```

---

## 8. Screen 6 — Expense Tracker (`expenses.html`)

### Purpose
View and add medical expenses. Charts showing monthly trends and category breakdown.

### API Calls
| Action | Endpoint |
|---|---|
| Get summary | `GET /finance/summary` |
| Add expense | `POST /finance/add-expense` |

### Layout

```
┌─────────────────────────────────────┐
│ 💰 MEDICAL EXPENSES                 │
├─────────────────────────────────────┤
│ April 2026: ₹4,500 ↓ 10% vs March  │
├─────────────────────────────────────┤
│ [Pie Chart — category breakdown]    │
│ Medicine 64% · Consult 24% · Lab 12%│
├─────────────────────────────────────┤
│ [Bar Chart — 6 month trend]         │
├─────────────────────────────────────┤
│ 💡 Savings Estimate: ₹1,600/month   │
│ (If nutrition plan is followed)     │
│ ⚠️ Estimated projection             │
├─────────────────────────────────────┤
│ [+ LOG NEW EXPENSE]                 │
├─────────────────────────────────────┤
│ ADD EXPENSE FORM (shown on click):  │
│ Date: [DD/MM/YYYY]                  │
│ Category: [▼ Select]                │
│ Amount (₹): [_______]               │
│ Description: [optional]             │
│ [CANCEL]  [SAVE EXPENSE]            │
└─────────────────────────────────────┘
```

### Amount Formatting (Indian Rupee)
```javascript
function formatRupee(amount) {
    return new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 0
    }).format(amount);
    // Output: ₹4,500 or ₹1,00,000
}
```

---

## 9. Screen 7 — History & Trends (`history.html`)

### Purpose
Timeline of all past consultations. Trend charts for nutrition and expenses.

### API Calls
| Action | Endpoint |
|---|---|
| Get history | `GET /history` |
| Nutrition trends | `GET /history/analytics/nutrition` |
| Expense trends | `GET /history/analytics/expenses` |

### Layout

```
┌─────────────────────────────────────┐
│ 📊 HISTORY & TRENDS                 │
│ [Timeline]  [Trends]                │ ← tab toggle
├─────────────────────────────────────┤
│ Filters: [Last 6 months ▼] [All ▼] │
│ Search: [_____________________] 🔍  │
├─────────────────────────────────────┤
│ ── April 21, 2026 ──                │
│ 🟢 Completed                        │
│ Common Cold (Viral URTI)            │
│ Follow-up: in 5 days                │
│ [VIEW FULL REPORT →]                │
│                                     │
│ ── April 5, 2026 ──                 │
│ 🟡 Follow-up Pending               │
│ Fatigue (Iron Deficiency)           │
│ [VIEW FULL REPORT →]                │
├─────────────────────────────────────┤
│ [LOAD MORE ↓]                       │
└─────────────────────────────────────┘
```

### Status Badge Colours
```javascript
const STATUS_COLORS = {
    "completed":        "var(--success)",
    "follow_up_pending": "var(--warning)",
    "in_progress":      "var(--primary)"
};
```

### Pagination
```javascript
let page = 1;

async function loadHistory() {
    const res = await fetch(`${API_BASE}/history?page=${page}&limit=10`, {
        headers: { "Authorization": `Bearer ${getToken()}` }
    });
    const data = await res.json();
    renderTimeline(data.data.consultations);
    if (page >= data.data.total_pages) {
        document.getElementById("load-more").style.display = "none";
    }
}

document.getElementById("load-more").onclick = () => { page++; loadHistory(); };
```

---

## 10. Shared JS Utilities (`js/utils.js`)

```javascript
// utils.js — shared across all pages

const API_BASE = "http://localhost:8000";

function getToken() {
    return localStorage.getItem("access_token");
}

function logout() {
    localStorage.clear();
    window.location.href = "index.html";
}

function requireAuth() {
    if (!getToken()) {
        window.location.href = "index.html";
    }
}

function showError(elementId, message) {
    const el = document.getElementById(elementId);
    if (el) { el.textContent = message; el.style.display = "block"; }
}

function getTime() {
    return new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
}

// Auto-refresh token before expiry
async function refreshToken() {
    const refresh = localStorage.getItem("refresh_token");
    if (!refresh) { logout(); return; }
    const res = await fetch(`${API_BASE}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refresh })
    });
    const data = await res.json();
    if (data.success) {
        localStorage.setItem("access_token", data.data.access_token);
    } else {
        logout();
    }
}

// Idle logout — 30 minutes
let idleTimer;
function resetIdleTimer() {
    clearTimeout(idleTimer);
    idleTimer = setTimeout(() => {
        alert("Session expired due to inactivity.");
        logout();
    }, 30 * 60 * 1000);
}
document.addEventListener("mousemove", resetIdleTimer);
document.addEventListener("keypress", resetIdleTimer);
```

---

## 11. Screen Navigation Map

```
index.html (Login/Register)
    │ on success
    ▼
dashboard.html
    ├── [Start Consultation] → consultation.html
    │                               │ on complete
    │                               ▼
    │                          report.html
    │
    ├── [View Report →] → report.html?id=xxx
    ├── [Nutrition] → nutrition.html
    ├── [Expenses] → expenses.html
    └── [History] → history.html
                        └── [View Full Report →] → report.html?id=xxx
```

---

*Previous: [04_api_design.md](./04_api_design.md)*  
*Next: [06_security_design.md](./06_security_design.md)*
