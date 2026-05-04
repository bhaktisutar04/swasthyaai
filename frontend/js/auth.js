// Redirect if already logged in
if (getToken()) {
  window.location.href = "dashboard.html";
}

// Tab switching
function switchTab(tab) {
  document.getElementById("login-form").style.display =
    tab === "login" ? "block" : "none";
  document.getElementById("register-form").style.display =
    tab === "register" ? "block" : "none";
  document.getElementById("tab-login").className =
    "tab" + (tab === "login" ? " active" : "");
  document.getElementById("tab-register").className =
    "tab" + (tab === "register" ? " active" : "");
  hideError("login-error");
  hideError("register-error");
}

// Toggle password visibility
function togglePassword(inputId) {
  const input = document.getElementById(inputId);
  input.type = input.type === "password" ? "text" : "password";
}

// Client-side validation
function validateLogin() {
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    showError("login-error", "Please enter a valid email address.");
    return false;
  }
  if (!password) {
    showError("login-error", "Please enter your password.");
    return false;
  }
  return true;
}

function validateRegister() {
  const name = document.getElementById("reg-name").value.trim();
  const age = parseInt(document.getElementById("reg-age").value);
  const gender = document.getElementById("reg-gender").value;
  const city = document.getElementById("reg-city").value.trim();
  const email = document.getElementById("reg-email").value.trim();
  const password = document.getElementById("reg-password").value;
  const terms = document.getElementById("reg-terms").checked;

  if (!name || name.length < 2) {
    showError("register-error", "Name must be at least 2 characters.");
    return false;
  }
  if (!age || age < 1 || age > 120) {
    showError("register-error", "Please enter a valid age (1-120).");
    return false;
  }
  if (!gender) {
    showError("register-error", "Please select your gender.");
    return false;
  }
  if (!city || city.length < 2) {
    showError("register-error", "Please enter your city.");
    return false;
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    showError("register-error", "Please enter a valid email address.");
    return false;
  }
  if (password.length < 8) {
    showError("register-error", "Password must be at least 8 characters.");
    return false;
  }
  if (!/[A-Z]/.test(password)) {
    showError("register-error", "Password must contain an uppercase letter.");
    return false;
  }
  if (!/[0-9]/.test(password)) {
    showError("register-error", "Password must contain a number.");
    return false;
  }
  if (!/[!@#$%^&*]/.test(password)) {
    showError("register-error", "Password must contain a special character (!@#$%^&*).");
    return false;
  }
  if (!terms) {
    showError("register-error", "Please accept the Terms & Conditions.");
    return false;
  }
  return true;
}

// Login handler
async function handleLogin() {
  hideError("login-error");
  if (!validateLogin()) return;
  setLoading("login-btn", true, "Login");

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: document.getElementById("login-email").value.trim().toLowerCase(),
        password: document.getElementById("login-password").value
      })
    });
    const data = await res.json();

    if (data.success) {
      localStorage.setItem("access_token", data.data.access_token);
      localStorage.setItem("refresh_token", data.data.refresh_token);
      localStorage.setItem("user_name", data.data.name);
      localStorage.setItem("user_id", data.data.user_id);
      window.location.href = "dashboard.html";
    } else {
      showError("login-error", data.message || "Invalid email or password.");
    }
  } catch(err) {
    showError("login-error", "Network error. Please check your connection.");
  } finally {
    setLoading("login-btn", false, "Login");
  }
}

// Register handler
async function handleRegister() {
  hideError("register-error");
  if (!validateRegister()) return;
  setLoading("register-btn", true, "Create Account");

  const diet_pref = document.querySelector('input[name="diet"]:checked').value;

  try {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: document.getElementById("reg-name").value.trim(),
        email: document.getElementById("reg-email").value.trim().toLowerCase(),
        password: document.getElementById("reg-password").value,
        age: parseInt(document.getElementById("reg-age").value),
        gender: document.getElementById("reg-gender").value,
        city: document.getElementById("reg-city").value.trim(),
        diet_pref: diet_pref,
        language: document.getElementById("reg-language").value,
        allergies: [],
        terms_accepted: true
      })
    });
    const data = await res.json();

    if (data.success) {
      localStorage.setItem("access_token", data.data.access_token);
      localStorage.setItem("refresh_token", data.data.refresh_token);
      localStorage.setItem("user_name", data.data.name);
      localStorage.setItem("user_id", data.data.user_id);
      window.location.href = "dashboard.html";
    } else {
      const msg = data.message || "Registration failed. Please try again.";
      showError("register-error", msg);
    }
  } catch(err) {
    showError("register-error", "Network error. Please check your connection.");
  } finally {
    setLoading("register-btn", false, "Create Account");
  }
}

// Allow Enter key to submit
document.addEventListener("keypress", function(e) {
  if (e.key === "Enter") {
    const loginVisible =
      document.getElementById("login-form").style.display !== "none";
    if (loginVisible) handleLogin();
    else handleRegister();
  }
});

