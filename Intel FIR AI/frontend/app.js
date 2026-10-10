/**
 * SMART FIR 360 - Main Application Controller
 */

// Global State
let currentUser = null;
let currentView = "landing";
let currentComplaintDetail = null;
let uploadedFilesCache = [];

// DOM Ready
document.addEventListener("DOMContentLoaded", async () => {
  initApp();
  setupEventListeners();
});

async function initApp() {
  currentUser = API.getUser();
  updateAuthUI();

  if (currentUser) {
    if (currentUser.role === "police_officer" || currentUser.role === "police_admin") {
      switchView("police");
    } else {
      switchView("citizen");
    }
  } else {
    switchView("landing");
    loadLandingStats();
  }
}

// ==========================================================================
// View Routing & UI State
// ==========================================================================

function switchView(viewName) {
  currentView = viewName;
  document.querySelectorAll(".view-section").forEach(sec => sec.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(item => item.classList.remove("active"));

  const targetSec = document.getElementById(`${viewName}View`);
  if (targetSec) targetSec.classList.add("active");

  const targetNav = document.getElementById(`nav-${viewName}`);
  if (targetNav) targetNav.classList.add("active");

  if (viewName === "police") {
    loadPoliceDashboard();
  } else if (viewName === "citizen") {
    loadCitizenDashboard();
  } else if (viewName === "landing") {
    loadLandingStats();
  }
}

function updateAuthUI() {
  const navAuthGuest = document.getElementById("navAuthGuest");
  const navAuthUser = document.getElementById("navAuthUser");
  const navPolice = document.getElementById("nav-police");
  const navCitizen = document.getElementById("nav-citizen");

  if (currentUser) {
    if (navAuthGuest) navAuthGuest.style.display = "none";
    if (navAuthUser) navAuthUser.style.display = "flex";

    document.getElementById("userNameBadge").textContent = currentUser.full_name;
    const roleTag = document.getElementById("userRoleTag");
    roleTag.textContent = currentUser.role === "police_officer" ? "POLICE OFFICER" : "CITIZEN";
    roleTag.className = `user-role-tag ${currentUser.role === "police_officer" ? "role-police" : "role-citizen"}`;

    if (currentUser.role === "police_officer" || currentUser.role === "police_admin") {
      if (navPolice) navPolice.style.display = "inline-block";
      if (navCitizen) navCitizen.style.display = "none";
    } else {
      if (navPolice) navPolice.style.display = "none";
      if (navCitizen) navCitizen.style.display = "inline-block";
    }
  } else {
    if (navAuthGuest) navAuthGuest.style.display = "flex";
    if (navAuthUser) navAuthUser.style.display = "none";
    if (navPolice) navPolice.style.display = "none";
    if (navCitizen) navCitizen.style.display = "none";
  }
}

function logout() {
  API.clearToken();
  currentUser = null;
  updateAuthUI();
  switchView("landing");
  showToast("Logged out successfully", "info");
}

window.onAuthExpired = () => {
  currentUser = null;
  updateAuthUI();
  switchView("landing");
  showToast("Session expired. Please log in again.", "error");
};

// ==========================================================================
// Landing Page Data
// ==========================================================================

async function loadLandingStats() {
  try {
    const stats = await API.stats.getDashboard();
    document.getElementById("statTotalComplaints").textContent = stats.total_complaints;
    document.getElementById("statPendingVerif").textContent = stats.pending_verification;
    document.getElementById("statPreliminaryInq").textContent = stats.under_preliminary_inquiry;
    document.getElementById("statFIRsRegistered").textContent = stats.firs_registered;
    document.getElementById("statResolved").textContent = stats.cases_resolved;
  } catch (err) {
    console.warn("Could not load stats:", err);
  }
}

async function quickTrack() {
  const input = document.getElementById("quickTrackInput").value.trim();
  if (!input) {
    showToast("Please enter a Complaint Number (e.g., COMP-2026-0001)", "error");
    return;
  }

  try {
    const complaint = await API.complaints.track(input);
    openCaseDetailModal(complaint);
  } catch (err) {
    showToast("Complaint not found. Please verify the reference number.", "error");
  }
}

// ==========================================================================
// Citizen Dashboard
// ==========================================================================

async function loadCitizenDashboard() {
  const listEl = document.getElementById("citizenComplaintList");
  listEl.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 2rem;">Loading your complaints...</td></tr>`;

  try {
    const complaints = await API.complaints.list();
    if (complaints.length === 0) {
      listEl.innerHTML = `<tr><td colspan="6" style="text-align:center; padding: 2rem; color:#9ca3af;">No complaints filed yet. Click "File New e-Complaint" above to file electronically under BNSS Section 173.</td></tr>`;
      return;
    }

    listEl.innerHTML = complaints.map(c => `
      <tr>
        <td style="font-weight: 700; color: #60a5fa;">${c.complaint_number}</td>
        <td>
          <div style="font-weight: 600;">${c.title}</div>
          <div style="font-size: 0.75rem; color: #9ca3af;">${c.category} • ${c.police_station}</div>
        </td>
        <td>${c.incident_date}</td>
        <td>${formatStatusBadge(c.status)}</td>
        <td>${formatBNSSDeadline(c)}</td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="openCaseDetail(${c.id})">Track / View</button>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    listEl.innerHTML = `<tr><td colspan="6" style="color:#ef4444; text-align:center;">Failed to load complaints: ${err.message}</td></tr>`;
  }
}

// ==========================================================================
// Police Dashboard
// ==========================================================================

async function loadPoliceDashboard() {
  loadPoliceMetrics();
  loadPoliceTable();
  loadGISMap();
}

async function loadPoliceMetrics() {
  try {
    const stats = await API.stats.getDashboard();
    document.getElementById("pStatTotal").textContent = stats.total_complaints;
    document.getElementById("pStatPendingVerif").textContent = stats.pending_verification;
    document.getElementById("pStatInquiry").textContent = stats.under_preliminary_inquiry;
    document.getElementById("pStatFIRs").textContent = stats.firs_registered;
    document.getElementById("pStatCritical").textContent = stats.critical_alerts;
  } catch (err) {
    console.error("Failed to load police stats:", err);
  }
}

async function loadPoliceTable() {
  const listEl = document.getElementById("policeCaseList");
  const statusFilter = document.getElementById("policeStatusFilter").value;
  const search = document.getElementById("policeSearchInput").value.trim();

  listEl.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 2rem;">Loading cases...</td></tr>`;

  try {
    const complaints = await API.complaints.list({
      status: statusFilter,
      search: search
    });

    if (complaints.length === 0) {
      listEl.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 2rem; color:#9ca3af;">No cases match the selected filter.</td></tr>`;
      return;
    }

    listEl.innerHTML = complaints.map(c => `
      <tr>
        <td style="font-weight: 700; color: #60a5fa;">${c.complaint_number}</td>
        <td>
          <div style="font-weight: 600;">${c.title}</div>
          <div style="font-size: 0.75rem; color: #9ca3af;">${c.category} • ${c.location_name}</div>
        </td>
        <td>${c.police_station}</td>
        <td>${c.incident_date}</td>
        <td>${formatStatusBadge(c.status)}</td>
        <td>${formatBNSSDeadline(c)}</td>
        <td>
          <button class="btn btn-primary btn-sm" onclick="openCaseDetail(${c.id})">Investigate</button>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    listEl.innerHTML = `<tr><td colspan="7" style="color:#ef4444; text-align:center;">Failed to load cases: ${err.message}</td></tr>`;
  }
}

async function loadGISMap() {
  try {
    const markers = await API.stats.getCrimeMap();
    MapService.initCrimeMap("crimeMap", markers);
  } catch (err) {
    console.error("Failed to load GIS crime markers:", err);
  }
}

window.viewCaseFromMap = (complaintId) => {
  openCaseDetail(complaintId);
};

// ==========================================================================
// Case Detail / Workspace Modal
// ==========================================================================

async function openCaseDetail(complaintId) {
  try {
    const complaint = await API.complaints.get(complaintId);
    openCaseDetailModal(complaint);
  } catch (err) {
    showToast(`Error opening case: ${err.message}`, "error");
  }
}

function openCaseDetailModal(complaint) {
  currentComplaintDetail = complaint;
  const isPolice = currentUser && (currentUser.role === "police_officer" || currentUser.role === "police_admin");

  document.getElementById("detailModalTitle").textContent = `${complaint.complaint_number} - Case Workspace`;
  
  // Render BNSS Stepper
  renderBNSSStepper(complaint.status);

  // Render Basic Details
  document.getElementById("detailTitle").textContent = complaint.title;
  document.getElementById("detailCategory").textContent = complaint.category;
  document.getElementById("detailStation").textContent = complaint.police_station;
  document.getElementById("detailLocation").textContent = `${complaint.location_name} (Lat: ${complaint.latitude}, Lng: ${complaint.longitude})`;
  document.getElementById("detailIncidentTime").textContent = `${complaint.incident_date} ${complaint.incident_time || ""}`;
  document.getElementById("detailStatusBadge").innerHTML = formatStatusBadge(complaint.status);
  document.getElementById("detailDescription").textContent = complaint.description;
  document.getElementById("detailAccused").textContent = complaint.accused_details || "None specified / Unknown";

  // Police Workflow Actions Panel
  const policeActionsPanel = document.getElementById("policeActionsPanel");
  if (isPolice) {
    policeActionsPanel.style.display = "block";
    setupPoliceActionButtons(complaint);
  } else {
    policeActionsPanel.style.display = "none";
  }

  // Citizen e-Verification Callout
  const citizenVerifyCallout = document.getElementById("citizenVerifyCallout");
  if (!isPolice && complaint.status === "submitted") {
    citizenVerifyCallout.style.display = "block";
  } else {
    citizenVerifyCallout.style.display = "none";
  }

  // FIR Details Box
  const firBox = document.getElementById("detailFIRBox");
  if (complaint.fir) {
    firBox.style.display = "block";
    document.getElementById("detailFIRNumber").textContent = complaint.fir.fir_number;
    document.getElementById("detailFIRSections").textContent = complaint.fir.bns_sections;
    document.getElementById("detailFIRStatus").textContent = complaint.fir.status.toUpperCase();
    document.getElementById("btnViewFIRReport").onclick = () => {
      window.open(API.firs.getReportUrl(complaint.fir.id), "_blank");
    };
  } else {
    firBox.style.display = "none";
  }

  // AI Insights Panel
  renderAIInsights(complaint.ai_analysis, complaint.id, isPolice);

  // Evidence List
  renderEvidenceList(complaint.evidences);

  // Timeline Stream
  renderTimelineStream(complaint.timeline);

  document.getElementById("caseDetailModal").classList.add("active");
}

function renderBNSSStepper(status) {
  const steps = [
    { id: "step-submitted", name: "e-Complaint Filed (Sec 173(1))" },
    { id: "step-verified", name: "3-Day Verification" },
    { id: "step-inquiry", name: "Preliminary Inquiry (14 Days)" },
    { id: "step-fir", name: "FIR Registered" },
    { id: "step-closed", name: "Investigation / Chargesheet" }
  ];

  const statusOrder = {
    "submitted": 1,
    "verified": 2,
    "preliminary_inquiry": 3,
    "fir_registered": 4,
    "closed": 5,
    "rejected": 5
  };

  const currentLevel = statusOrder[status] || 1;

  const stepperHtml = steps.map((s, idx) => {
    const stepNum = idx + 1;
    let stateClass = "";
    if (stepNum < currentLevel) stateClass = "completed";
    else if (stepNum === currentLevel) stateClass = "active";

    return `
      <div class="step-node ${stateClass}">
        <div class="step-circle">${stepNum < currentLevel ? "✓" : stepNum}</div>
        <div class="step-title">${s.name}</div>
      </div>
    `;
  }).join("");

  document.getElementById("bnssStepper").innerHTML = stepperHtml;
}

function renderAIInsights(ai, complaintId, isPolice) {
  const aiContainer = document.getElementById("detailAIPanel");
  
  if (!ai) {
    aiContainer.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
          <span class="ai-badge">🤖 AI Partner NLP Engine</span>
          <p style="font-size:0.85rem; color:#9ca3af; margin-top:0.4rem;">
            Complaint pending automated NLP classification, BNS legal section recommendation, and duplicate check.
          </p>
        </div>
        <button class="btn btn-accent btn-sm" onclick="triggerAIScan(${complaintId})">⚡ Run AI Analysis</button>
      </div>
    `;
    return;
  }

  const sectionsHtml = (ai.recommended_sections || []).map(s => `
    <div style="background: rgba(255,255,255,0.05); padding: 0.5rem 0.75rem; border-radius: 6px; margin-top: 0.4rem; border-left: 3px solid #3b82f6;">
      <div style="font-weight: 700; font-size: 0.85rem; color: #93c5fd;">${s.section} - ${s.title}</div>
      <div style="font-size: 0.75rem; color: #9ca3af;">Confidence: ${(s.confidence * 100).toFixed(1)}% • ${s.cognizable ? "Cognizable" : "Non-Cognizable"} • ${s.bailable ? "Bailable" : "Non-Bailable"}</div>
    </div>
  `).join("");

  const duplicatesHtml = (ai.duplicate_candidate_ids && ai.duplicate_candidate_ids.length > 0)
    ? `<div style="color: #f87171; font-weight: bold; font-size: 0.85rem; margin-top: 0.4rem;">⚠️ Potential Duplicate / Related Cases: ${ai.duplicate_candidate_ids.join(", ")} (Similarity Risk: ${ai.duplicate_risk_score}%)</div>`
    : `<div style="color: #34d399; font-size: 0.8rem; margin-top: 0.4rem;">✓ No critical duplicate complaints detected.</div>`;

  aiContainer.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 0.75rem;">
      <div style="display:flex; align-items:center; gap:0.5rem;">
        <span class="ai-badge">🤖 AI Partner NLP & Legal Assistant</span>
        <span class="urgency-badge urgency-${ai.urgency_level}">${ai.urgency_level} PRIORITY</span>
      </div>
      <button class="btn btn-secondary btn-sm" onclick="triggerAIScan(${complaintId})">🔄 Re-Scan</button>
    </div>

    <p style="font-size: 0.85rem; color: #e5e7eb; margin-bottom: 0.6rem; font-style: italic;">
      "${ai.complaint_summary || "Automated NLP summary generated."}"
    </p>

    <div style="margin-bottom: 0.75rem;">
      <div style="font-size: 0.8rem; font-weight: 700; color: #9ca3af; text-transform: uppercase;">Recommended Bharatiya Nyaya Sanhita (BNS) Sections:</div>
      ${sectionsHtml || "<span style='font-size:0.8rem; color:#9ca3af;'>No sections identified.</span>"}
    </div>

    ${duplicatesHtml}
  `;
}

async function triggerAIScan(complaintId) {
  try {
    showToast("Running AI / NLP Legal Analysis...", "info");
    const result = await API.ai.triggerMock(complaintId);
    showToast("AI Analysis completed successfully!", "success");
    openCaseDetail(complaintId);
  } catch (err) {
    showToast(`AI Scan failed: ${err.message}`, "error");
  }
}

function renderEvidenceList(evidences) {
  const container = document.getElementById("detailEvidenceList");
  if (!evidences || evidences.length === 0) {
    container.innerHTML = `<div style="font-size: 0.85rem; color: #9ca3af;">No digital evidence uploaded yet.</div>`;
    return;
  }

  container.innerHTML = evidences.map(e => `
    <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.03); border: 1px solid var(--border-color); border-radius: 6px; padding: 0.6rem 0.9rem; margin-bottom: 0.5rem;">
      <div>
        <div style="font-weight: 600; font-size: 0.85rem;">📁 ${e.file_name} <span style="font-size: 0.75rem; color: #9ca3af;">(${e.file_size_kb} KB)</span></div>
        <div style="font-size: 0.7rem; color: #6b7280; font-family: monospace;">SHA-256 Custody Hash: ${e.hash_sha256}</div>
      </div>
      <a href="${API.evidence.getFileUrl(e.id)}" target="_blank" class="btn btn-secondary btn-sm">Download</a>
    </div>
  `).join("");
}

function renderTimelineStream(timeline) {
  const container = document.getElementById("detailTimelineStream");
  if (!timeline || timeline.length === 0) {
    container.innerHTML = `<div style="font-size: 0.85rem; color: #9ca3af;">No events logged yet.</div>`;
    return;
  }

  container.innerHTML = timeline.map(t => `
    <div class="timeline-item">
      <div class="timeline-dot"></div>
      <div class="timeline-content">
        <div class="timeline-title">
          <span>${t.title}</span>
          <span class="timeline-time">${new Date(t.created_at).toLocaleString()}</span>
        </div>
        <div class="timeline-desc">${t.description}</div>
        <div style="font-size: 0.7rem; color: #6b7280; margin-top: 0.25rem;">Actor: ${t.actor_name}</div>
      </div>
    </div>
  `).join("");
}

function setupPoliceActionButtons(complaint) {
  const btnVerify = document.getElementById("btnPoliceVerify");
  const btnInquiry = document.getElementById("btnPoliceInquiry");
  const btnRegisterFIR = document.getElementById("btnPoliceRegisterFIR");
  const btnReject = document.getElementById("btnPoliceReject");

  // Reset displays
  btnVerify.style.display = complaint.status === "submitted" ? "inline-flex" : "none";
  btnInquiry.style.display = (complaint.status === "submitted" || complaint.status === "verified") ? "inline-flex" : "none";
  btnRegisterFIR.style.display = (complaint.status !== "fir_registered" && complaint.status !== "closed" && complaint.status !== "rejected") ? "inline-flex" : "none";
  btnReject.style.display = (complaint.status !== "fir_registered" && complaint.status !== "closed" && complaint.status !== "rejected") ? "inline-flex" : "none";

  btnVerify.onclick = async () => {
    try {
      await API.complaints.verify(complaint.id, {
        verification_type: "Physical_Officer_Verification",
        notes: "Complainant attended station and physically verified complaint details under BNSS 173(1)."
      });
      showToast("Complaint verified successfully under BNSS 173(1)", "success");
      openCaseDetail(complaint.id);
      loadPoliceDashboard();
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  btnInquiry.onclick = () => {
    document.getElementById("inquiryComplaintId").value = complaint.id;
    document.getElementById("preliminaryInquiryModal").classList.add("active");
  };

  btnRegisterFIR.onclick = () => {
    document.getElementById("firComplaintId").value = complaint.id;
    document.getElementById("firStationInput").value = complaint.police_station;
    document.getElementById("firPlaceInput").value = complaint.location_name;
    document.getElementById("firOccurrenceDateInput").value = complaint.incident_date;
    
    // Auto-fill BNS sections from AI if available
    if (complaint.ai_analysis && complaint.ai_analysis.recommended_sections) {
      const sects = complaint.ai_analysis.recommended_sections.map(s => `${s.section} [${s.title}]`).join(", ");
      document.getElementById("firSectionsInput").value = sects;
    } else {
      document.getElementById("firSectionsInput").value = "BNS Section 303(2) [Theft]";
    }

    document.getElementById("registerFIRModal").classList.add("active");
  };

  btnReject.onclick = async () => {
    const reason = prompt("Enter mandatory statutory reason for Non-Registration / Civil Closure under BNSS Section 173:");
    if (!reason) return;
    try {
      await API.complaints.reject(complaint.id, reason);
      showToast("Case marked as Non-Cognizable / Closed", "info");
      openCaseDetail(complaint.id);
      loadPoliceDashboard();
    } catch (err) {
      showToast(err.message, "error");
    }
  };
}

// ==========================================================================
// Formatting Helpers
// ==========================================================================

function formatStatusBadge(status) {
  switch (status) {
    case "submitted":
      return `<span class="badge badge-submitted">Submitted (e-FIR)</span>`;
    case "verified":
      return `<span class="badge badge-verified">Verified (Sec 173)</span>`;
    case "preliminary_inquiry":
      return `<span class="badge badge-inquiry">14-Day Prelim Inquiry</span>`;
    case "fir_registered":
      return `<span class="badge badge-fir">FIR Registered</span>`;
    case "closed":
      return `<span class="badge badge-closed">Closed</span>`;
    case "rejected":
      return `<span class="badge badge-rejected">Non-Cognizable</span>`;
    default:
      return `<span class="badge">${status}</span>`;
  }
}

function formatBNSSDeadline(c) {
  if (c.status === "submitted" && c.verification_deadline) {
    return `<span style="color:#fbbf24; font-size:0.75rem; font-weight:600;">⏱️ 3-day verification active</span>`;
  } else if (c.status === "preliminary_inquiry" && c.inquiry_deadline) {
    return `<span style="color:#f59e0b; font-size:0.75rem; font-weight:600;">⏱️ 14-day inquiry window</span>`;
  } else if (c.status === "fir_registered") {
    return `<span style="color:#a78bfa; font-size:0.75rem; font-weight:600;">⚖️ Formal FIR under BNSS</span>`;
  }
  return `<span style="color:#9ca3af; font-size:0.75rem;">Completed</span>`;
}

function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span>${type === "success" ? "✅" : type === "error" ? "❌" : "ℹ️"}</span>
    <span>${message}</span>
  `;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

// ==========================================================================
// Event Listeners Setup
// ==========================================================================

function setupEventListeners() {
  // Navigation Links
  document.querySelectorAll(".nav-link").forEach(link => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const target = link.getAttribute("data-view");
      if (target) switchView(target);
    });
  });

  // Modal Closers
  document.querySelectorAll(".modal-close, .modal-cancel").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".modal-backdrop").forEach(m => m.classList.remove("active"));
    });
  });

  // Auth Modal Triggers
  document.getElementById("btnOpenLogin")?.addEventListener("click", () => {
    document.getElementById("authModal").classList.add("active");
  });

  document.getElementById("btnLogout")?.addEventListener("click", logout);

  // Tab Switch in Auth Modal
  document.getElementById("authTabLogin")?.addEventListener("click", () => {
    document.getElementById("authTabLogin").classList.add("active");
    document.getElementById("authTabRegister").classList.remove("active");
    document.getElementById("loginFormContainer").style.display = "block";
    document.getElementById("registerFormContainer").style.display = "none";
  });

  document.getElementById("authTabRegister")?.addEventListener("click", () => {
    document.getElementById("authTabRegister").classList.add("active");
    document.getElementById("authTabLogin").classList.remove("active");
    document.getElementById("loginFormContainer").style.display = "none";
    document.getElementById("registerFormContainer").style.display = "block";
  });

  // Fast Demo Logins
  document.getElementById("demoPoliceLogin")?.addEventListener("click", async () => {
    document.getElementById("loginEmail").value = "inspector.sharma@police.gov.in";
    document.getElementById("loginPassword").value = "Police@123";
    handleLogin();
  });

  document.getElementById("demoCitizenLogin")?.addEventListener("click", async () => {
    document.getElementById("loginEmail").value = "rohit.verma@example.com";
    document.getElementById("loginPassword").value = "Citizen@123";
    handleLogin();
  });

  // Submit Login
  document.getElementById("formLogin")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    handleLogin();
  });

  // Submit Register
  document.getElementById("formRegister")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    handleRegister();
  });

  // New Complaint Modal Trigger
  document.getElementById("btnOpenNewComplaint")?.addEventListener("click", () => {
    if (!currentUser) {
      document.getElementById("authModal").classList.add("active");
      showToast("Please log in to submit a complaint.", "info");
      return;
    }
    document.getElementById("newComplaintModal").classList.add("active");
    uploadedFilesCache = [];
    document.getElementById("selectedFilesList").innerHTML = "";

    // Init Leaflet Picker Map
    MapService.initLocationPicker("pickerMap", (lat, lng) => {
      document.getElementById("cLatitude").value = lat;
      document.getElementById("cLongitude").value = lng;
    });
  });

  // File Upload Drop Area
  const fileInput = document.getElementById("evidenceFilesInput");
  fileInput?.addEventListener("change", (e) => {
    const files = Array.from(e.target.files);
    uploadedFilesCache.push(...files);
    renderFileQueue();
  });

  // Submit Complaint Form
  document.getElementById("formNewComplaint")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    handleCreateComplaint();
  });

  // Aadhaar OTP Verification for Citizen
  document.getElementById("btnCitizenVerifyNow")?.addEventListener("click", async () => {
    const otp = prompt("Enter 6-digit Aadhaar OTP sent to your registered mobile (Demo simulation - enter any 6 digits):", "654321");
    if (!otp) return;
    try {
      await API.complaints.verify(currentComplaintDetail.id, {
        verification_type: "Aadhaar_OTP_Electronic_Verification",
        notes: `Complainant verified identity via Aadhaar OTP token [Auth-Ref: AADHAAR-${otp}]. Section 173(1) BNSS requirement fulfilled.`
      });
      showToast("Aadhaar e-Verification complete!", "success");
      openCaseDetail(currentComplaintDetail.id);
      loadCitizenDashboard();
    } catch (err) {
      showToast(err.message, "error");
    }
  });

  // Form Preliminary Inquiry Submit
  document.getElementById("formPreliminaryInquiry")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = document.getElementById("inquiryComplaintId").value;
    const recommendation = document.getElementById("inquiryRecommendation").value;
    const notes = document.getElementById("inquiryNotes").value;
    const dyspRef = document.getElementById("inquiryDyspRef").value;

    try {
      await API.complaints.startInquiry(id, {
        officer_recommendation: recommendation,
        inquiry_notes: notes,
        approval_dysp_ref: dyspRef
      });
      showToast("Preliminary inquiry initiated under BNSS Section 173(3) (14-day clock active)", "success");
      document.getElementById("preliminaryInquiryModal").classList.remove("active");
      openCaseDetail(id);
      loadPoliceDashboard();
    } catch (err) {
      showToast(err.message, "error");
    }
  });

  // Form Register FIR Submit
  document.getElementById("formRegisterFIR")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const complaintId = parseInt(document.getElementById("firComplaintId").value);
    const station = document.getElementById("firStationInput").value;
    const sections = document.getElementById("firSectionsInput").value;
    const occurrenceDate = document.getElementById("firOccurrenceDateInput").value;
    const place = document.getElementById("firPlaceInput").value;
    const summary = document.getElementById("firSummaryInput").value;

    try {
      const newFir = await API.firs.register({
        complaint_id: complaintId,
        police_station: station,
        bns_sections: sections,
        date_of_occurrence: occurrenceDate,
        place_of_occurrence: place,
        investigation_summary: summary
      });

      showToast(`FIR ${newFir.fir_number} registered successfully!`, "success");
      document.getElementById("registerFIRModal").classList.remove("active");
      openCaseDetail(complaintId);
      loadPoliceDashboard();
    } catch (err) {
      showToast(err.message, "error");
    }
  });

  // Police Filters
  document.getElementById("policeStatusFilter")?.addEventListener("change", loadPoliceTable);
  document.getElementById("btnPoliceSearch")?.addEventListener("click", loadPoliceTable);
  document.getElementById("policeSearchInput")?.addEventListener("keyup", (e) => {
    if (e.key === "Enter") loadPoliceTable();
  });
}

async function handleLogin() {
  const email = document.getElementById("loginEmail").value;
  const password = document.getElementById("loginPassword").value;
  try {
    const data = await API.auth.login(email, password);
    currentUser = data.user;
    updateAuthUI();
    document.getElementById("authModal").classList.remove("active");
    showToast(`Welcome, ${currentUser.full_name}!`, "success");

    if (currentUser.role === "police_officer" || currentUser.role === "police_admin") {
      switchView("police");
    } else {
      switchView("citizen");
    }
  } catch (err) {
    showToast(`Login failed: ${err.message}`, "error");
  }
}

async function handleRegister() {
  const email = document.getElementById("regEmail").value;
  const password = document.getElementById("regPassword").value;
  const fullName = document.getElementById("regFullName").value;
  const phone = document.getElementById("regPhone").value;
  const aadhar = document.getElementById("regAadhar").value;
  const role = document.getElementById("regRole").value;

  try {
    const data = await API.auth.register({
      email,
      password,
      full_name: fullName,
      phone,
      aadhar_last4: aadhar,
      role
    });
    currentUser = data.user;
    updateAuthUI();
    document.getElementById("authModal").classList.remove("active");
    showToast(`Registration complete! Welcome, ${currentUser.full_name}`, "success");

    if (currentUser.role === "police_officer") {
      switchView("police");
    } else {
      switchView("citizen");
    }
  } catch (err) {
    showToast(`Registration failed: ${err.message}`, "error");
  }
}

function renderFileQueue() {
  const listEl = document.getElementById("selectedFilesList");
  listEl.innerHTML = uploadedFilesCache.map((f, i) => `
    <div style="font-size: 0.8rem; background: rgba(255,255,255,0.05); padding: 0.3rem 0.6rem; border-radius: 4px; display: flex; justify-content: space-between; margin-top: 0.3rem;">
      <span>📎 ${f.name} (${Math.round(f.size/1024)} KB)</span>
      <span style="color: #ef4444; cursor: pointer;" onclick="removeCachedFile(${i})">✕</span>
    </div>
  `).join("");
}

window.removeCachedFile = (index) => {
  uploadedFilesCache.splice(index, 1);
  renderFileQueue();
};

async function handleCreateComplaint() {
  const title = document.getElementById("cTitle").value;
  const category = document.getElementById("cCategory").value;
  const station = document.getElementById("cStation").value;
  const incidentDate = document.getElementById("cIncidentDate").value;
  const incidentTime = document.getElementById("cIncidentTime").value;
  const locationName = document.getElementById("cLocationName").value;
  const lat = parseFloat(document.getElementById("cLatitude").value) || 28.6139;
  const lng = parseFloat(document.getElementById("cLongitude").value) || 77.2090;
  const description = document.getElementById("cDescription").value;
  const accused = document.getElementById("cAccused").value;
  const witness = document.getElementById("cWitness").value;

  try {
    showToast("Submitting e-Complaint under BNSS Section 173...", "info");
    const complaint = await API.complaints.submit({
      title,
      category,
      police_station: station,
      incident_date: incidentDate,
      incident_time: incidentTime,
      location_name: locationName,
      latitude: lat,
      longitude: lng,
      description,
      accused_details: accused,
      witness_details: witness,
      is_e_complaint: true
    });

    // Upload cached evidence files if any
    for (const file of uploadedFilesCache) {
      await API.evidence.upload(complaint.id, file, "Complainant digital attachment");
    }

    // Trigger AI Scan automatically in background
    API.ai.triggerMock(complaint.id).catch(console.warn);

    showToast(`Complaint ${complaint.complaint_number} lodged successfully!`, "success");
    document.getElementById("newComplaintModal").classList.remove("active");
    document.getElementById("formNewComplaint").reset();
    uploadedFilesCache = [];

    // Switch to Citizen view & open detail
    switchView("citizen");
    openCaseDetail(complaint.id);
  } catch (err) {
    showToast(`Failed to lodge complaint: ${err.message}`, "error");
  }
}
