requireAuth();
resetIdleTimer();
document.getElementById("bottom-nav").innerHTML = renderBottomNav("history");

let allConsultations = [];
let currentPage = 1;
let totalPages = 1;




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
  } catch (err) {
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
                     onclick="downloadPDF('${c.pdf_path || c.consultation_id}')">
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
async function downloadPDF(pdfUrl) {
  if (pdfUrl && pdfUrl.startsWith('http')) {
    // For Cloudinary URLs, adding fl_attachment to the URL forces a download
    let downloadUrl = pdfUrl;
    if (pdfUrl.includes("cloudinary.com")) {
      downloadUrl = pdfUrl.replace("/upload/", "/upload/fl_attachment/");
    }
    
    const a = document.createElement("a");
    a.href = downloadUrl;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  } else {
    // Internal API endpoint - use apiFetch
    try {
      const res = await apiFetch(
        `/consultation/report/${pdfUrl}/pdf`
      );
      if (!res) return;
      if (res.status === 404) {
        alert("PDF not available for this consultation.");
        return;
      }

      // Check if response is JSON (contains Cloudinary URL)
      const contentType = res.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        const data = await res.json();
        if (data.url) {
          let downloadUrl = data.url;
          if (downloadUrl.includes("cloudinary.com")) {
            downloadUrl = downloadUrl.replace("/upload/", "/upload/fl_attachment/");
          }
          const a = document.createElement("a");
          a.href = downloadUrl;
          a.target = "_blank";
          a.rel = "noopener noreferrer";
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          return;
        }
      }

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `SwasthyaAI_Report_${pdfUrl}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert("Could not download PDF.");
    }
  }
}



// Initial load
loadHistory();

