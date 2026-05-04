requireAuth();
resetIdleTimer();

let sessionId = null;
let consultationComplete = false;
let isSending = false;

// Clean start every time
localStorage.removeItem("current_session_id");

function addMessage(text, sender, time) {
  const container = document.getElementById("chat-messages");
  const wrapper = document.createElement("div");
  wrapper.className = sender === "ai" ? "bubble-wrapper-ai" : "bubble-wrapper-user";
  const t = time || getCurrentTime();
  wrapper.innerHTML = `
    <div>
      <div class="bubble ${sender === 'ai' ? 'bubble-ai' : 'bubble-user'}">${text}</div>
      <div class="bubble-meta ${sender === 'ai' ? 'bubble-meta-ai' : 'bubble-meta-user'}">${t}</div>
    </div>`;
  container.appendChild(wrapper);
  container.scrollTop = container.scrollHeight;
}

function showTyping() {
  removeTyping();
  const container = document.getElementById("chat-messages");
  const div = document.createElement("div");
  div.id = "typing-indicator";
  div.className = "typing-wrapper";
  div.innerHTML = `<div class="bubble bubble-ai"><div class="typing-indicator">
    <div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>
  </div></div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function removeTyping() {
  const el = document.getElementById("typing-indicator");
  if (el) el.remove();
}

async function startConsultation() {
  showTyping();
  try {
    const res = await apiFetch("/consultation/start", { method: "POST" });
    removeTyping();
    if (!res) { addMessage("Unable to connect. Please refresh.", "ai"); return; }
    const data = await res.json();
    if (data.success) {
      sessionId = data.data.session_id;
      document.getElementById("session-id-display").textContent = sessionId;
      localStorage.setItem("current_session_id", sessionId);
      addMessage(data.data.greeting, "ai");
    } else {
      addMessage("Could not start consultation. Please refresh.", "ai");
    }
  } catch(e) {
    removeTyping();
    addMessage("Connection error. Is the backend running?", "ai");
  }
}

async function sendMessage() {
  if (isSending || consultationComplete || !sessionId) return;
  const input = document.getElementById("message-input");
  const message = input.value.trim();
  if (!message) return;

  isSending = true;
  addMessage(message, "user");
  input.value = "";
  document.getElementById("send-btn").disabled = true;
  showTyping();

  try {
    const res = await apiFetch("/consultation/message", {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId, message })
    });
    removeTyping();
    document.getElementById("send-btn").disabled = false;

    if (!res) { addMessage("Connection error. Please try again.", "ai"); isSending = false; return; }
    if (res.status === 404) {
      addMessage("Session expired. Please refresh to start a new consultation.", "ai");
      isSending = false; return;
    }

    const data = await res.json();
    if (!data.success) { addMessage("Something went wrong. Please try again.", "ai"); isSending = false; return; }

    const d = data.data;

    if (d.emergency_detected) {
      showEmergencyModal(d.hospitals || []);
      addMessage(d.response, "ai");
      isSending = false; return;
    }

    addMessage(d.response, "ai");

    if (d.consultation_complete) {
      consultationComplete = true;
      document.getElementById("agent-status").textContent = "● Preparing Report...";
      document.getElementById("agent-status").style.color = "var(--warning)";
      document.getElementById("message-input").disabled = true;
      document.getElementById("send-btn").disabled = true;
      document.getElementById("message-input").placeholder = "Consultation ended";

      const container = document.getElementById("chat-messages");
      const banner = document.createElement("div");
      banner.className = "completion-banner";
      banner.innerHTML = `
        ✅ <strong>Consultation Complete!</strong><br>
        Your report is being prepared (takes ~1-2 minutes for full analysis).<br><br>
        <button class="btn btn-primary btn-sm" style="margin-top:8px;"
                onclick="viewReport()">View Report →</button>`;
      container.appendChild(banner);
      container.scrollTop = container.scrollHeight;

      // Auto-update status after 90 seconds
      setTimeout(() => {
        document.getElementById("agent-status").textContent = "● Analysis Complete";
        document.getElementById("agent-status").style.color = "var(--success)";
      }, 90000);
    }
  } catch(e) {
    removeTyping();
    document.getElementById("send-btn").disabled = false;
    addMessage("Network error. Please try again.", "ai");
  } finally {
    isSending = false;
  }
}

function handleKeyPress(e) {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
}

function showEmergencyModal(hospitals) {
  document.getElementById("emergency-modal").classList.add("active");
  const list = document.getElementById("hospitals-list");
  list.innerHTML = hospitals.length > 0
    ? `<div style="font-size:13px;font-weight:600;margin-bottom:8px;">Nearest Hospitals:</div>
       ${hospitals.map(h => `<div class="hospital-item">
         <div class="hospital-name">${h.name}</div>
         <div class="hospital-address">${h.address || ""}</div>
         <a href="${h.maps_link}" target="_blank" class="hospital-link">📍 Open in Maps</a>
       </div>`).join("")}`
    : `<div class="text-muted">Call 108 for emergency ambulance.</div>`;
}

function closeEmergencyModal() {
  document.getElementById("emergency-modal").classList.remove("active");
}

function viewReport() {
  if (sessionId) window.location.href = `report.html?id=${sessionId}`;
}

function endConsultation() {
  if (consultationComplete) { viewReport(); return; }
  if (confirm("End consultation? Progress will be saved.")) {
    window.location.href = "dashboard.html";
  }
}

// Start only once
startConsultation();

