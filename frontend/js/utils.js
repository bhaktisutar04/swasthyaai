const API_BASE = "https://swasthyaai-nkvc.onrender.com";
//const API_BASE = "https://swasthyaai-backend.onrender.com";
//const API_BASE = "http://localhost:8000";
function getToken() {
  return localStorage.getItem("access_token");
}

function getRefreshToken() {
  return localStorage.getItem("refresh_token");
}

function getUserName() {
  return localStorage.getItem("user_name") || "User";
}

function setTokens(access_token, refresh_token) {
  localStorage.setItem("access_token", access_token);
  localStorage.setItem("refresh_token", refresh_token);
}

function requireAuth() {
  const token = getToken();
  if (!token) {
    window.location.href = "index.html";
    return false;
  }
  return true;
}

async function logout() {
  try {
    const refresh_token = getRefreshToken();
    if (refresh_token) {
      await fetch(`${API_BASE}/auth/logout`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${getToken()}`
        },
        body: JSON.stringify({ refresh_token })
      });
    }
  } catch (e) { }
  finally {
    localStorage.clear();
    window.location.href = "index.html";
  }
}

async function apiFetch(endpoint, options = {}) {
  if (endpoint.startsWith('http')) {
    return fetch(endpoint, options);
  }
  const token = getToken();
  const headers = {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}`,
    ...options.headers
  };
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers
  });
  if (response.status === 401) {
    const refreshed = await tryRefreshToken();
    if (!refreshed) {
      logout();
      return null;
    }
    return apiFetch(endpoint, options);
  }
  return response;
}

async function tryRefreshToken() {
  try {
    const refresh_token = getRefreshToken();
    if (!refresh_token) return false;
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token })
    });
    const data = await res.json();
    if (data.success) {
      localStorage.setItem("access_token", data.data.access_token);
      return true;
    }
    return false;
  } catch (e) {
    return false;
  }
}

function showError(elementId, message) {
  const el = document.getElementById(elementId);
  if (el) {
    el.textContent = message;
    el.style.display = "block";
  }
}

function hideError(elementId) {
  const el = document.getElementById(elementId);
  if (el) el.style.display = "none";
}

function setLoading(buttonId, isLoading, originalText) {
  const btn = document.getElementById(buttonId);
  if (!btn) return;
  btn.disabled = isLoading;
  btn.textContent = isLoading ? "Please wait..." : originalText;
}

function formatDate(dateStr) {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-IN", {
    day: "numeric", month: "long", year: "numeric"
  });
}

function formatDateShort(dateStr) {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-IN", {
    day: "numeric", month: "short"
  });
}

function getCurrentTime() {
  return new Date().toLocaleTimeString("en-IN", {
    hour: "2-digit", minute: "2-digit"
  });
}

function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "Good Morning";
  if (hour < 17) return "Good Afternoon";
  return "Good Evening";
}

function formatRupee(amount) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0
  }).format(amount);
}

function getSeverityColor(severity_flag) {
  const map = {
    "mild": "var(--success)",
    "moderate": "var(--warning)",
    "severe": "var(--danger)"
  };
  return map[severity_flag] || "var(--neutral)";
}

function getSeverityBadgeClass(severity_flag) {
  const map = {
    "mild": "badge-success",
    "moderate": "badge-warning",
    "severe": "badge-danger"
  };
  return map[severity_flag] || "badge-primary";
}

function showSkeleton(containerId, count = 3) {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = Array(count).fill(
    `<div class="skeleton skeleton-card"></div>`
  ).join("");
}

function showEmptyState(containerId, icon, title, message) {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = `
    <div class="empty-state">
      <div class="empty-state-icon">${icon}</div>
      <div class="empty-state-title">${title}</div>
      <div class="empty-state-text">${message}</div>
    </div>
  `;
}

function renderBottomNav(activePage) {
  const pages = [
    { icon: "🏠", label: "Home", href: "dashboard.html", key: "home" },
    { icon: "🩺", label: "Consult", href: "consultation.html", key: "consult" },
    { icon: "💰", label: "Expenses", href: "expenses.html", key: "expenses" },
    { icon: "📊", label: "History", href: "history.html", key: "history" },
    { icon: "👤", label: "Profile", href: "#", key: "profile", onclick: "logout()" }
  ];
  return `
    <nav class="bottom-nav">
      ${pages.map(p => `
        <div class="nav-item ${p.key === activePage ? 'active' : ''}"
             onclick="${p.onclick || `window.location.href='${p.href}'`}">
          <span class="nav-icon">${p.icon}</span>
          <span>${p.label}</span>
        </div>
      `).join("")}
    </nav>
  `;
}

let idleTimer;
function resetIdleTimer() {
  clearTimeout(idleTimer);
  idleTimer = setTimeout(() => {
    alert("Your session has expired due to inactivity. Please log in again.");
    logout();
  }, 30 * 60 * 1000);
}
["mousemove", "keydown", "click", "scroll", "touchstart"].forEach(event => {
  document.addEventListener(event, resetIdleTimer, true);
});

function getCurrentDateString() {
  return new Date().toLocaleDateString("en-IN", {
    weekday: "long", year: "numeric",
    month: "long", day: "numeric"
  });
}
