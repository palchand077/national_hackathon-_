/**
 * SMART FIR 360 - Frontend API Client Layer
 */

const API_BASE = window.location.origin;

const API = {
  getToken() {
    return localStorage.getItem("smart_fir_token");
  },

  setToken(token) {
    localStorage.setItem("smart_fir_token", token);
  },

  clearToken() {
    localStorage.removeItem("smart_fir_token");
    localStorage.removeItem("smart_fir_user");
  },

  getUser() {
    try {
      return JSON.parse(localStorage.getItem("smart_fir_user"));
    } catch {
      return null;
    }
  },

  setUser(user) {
    localStorage.setItem("smart_fir_user", JSON.stringify(user));
  },

  async request(endpoint, options = {}) {
    const headers = options.headers || {};
    const token = this.getToken();

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }

    const config = {
      ...options,
      headers
    };

    try {
      const response = await fetch(`${API_BASE}${endpoint}`, config);
      
      if (response.status === 401) {
        // Token expired or invalid
        this.clearToken();
        if (window.onAuthExpired) window.onAuthExpired();
      }

      if (!response.ok) {
        const errData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errData.detail || `Request failed (${response.status})`);
      }

      return await response.json();
    } catch (err) {
      console.error(`API Error on [${options.method || "GET"} ${endpoint}]:`, err);
      throw err;
    }
  },

  // Auth Endpoints
  auth: {
    async login(email, password) {
      const data = await API.request("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password })
      });
      API.setToken(data.access_token);
      API.setUser(data.user);
      return data;
    },

    async register(payload) {
      const data = await API.request("/api/auth/register", {
        method: "POST",
        body: JSON.stringify(payload)
      });
      API.setToken(data.access_token);
      API.setUser(data.user);
      return data;
    },

    async getProfile() {
      return await API.request("/api/auth/me");
    }
  },

  // Complaint & BNSS Endpoints
  complaints: {
    async list(params = {}) {
      const query = new URLSearchParams(params).toString();
      return await API.request(`/api/complaints${query ? "?" + query : ""}`);
    },

    async get(id) {
      return await API.request(`/api/complaints/${id}`);
    },

    async track(number) {
      return await API.request(`/api/complaints/track/${encodeURIComponent(number)}`);
    },

    async submit(payload) {
      return await API.request("/api/complaints", {
        method: "POST",
        body: JSON.stringify(payload)
      });
    },

    async verify(id, payload = {}) {
      return await API.request(`/api/complaints/${id}/verify`, {
        method: "POST",
        body: JSON.stringify(payload)
      });
    },

    async startInquiry(id, payload) {
      return await API.request(`/api/complaints/${id}/preliminary-inquiry`, {
        method: "POST",
        body: JSON.stringify(payload)
      });
    },

    async reject(id, reason) {
      return await API.request(`/api/complaints/${id}/reject`, {
        method: "POST",
        body: JSON.stringify({ status: "rejected", notes: reason })
      });
    }
  },

  // FIR Endpoints
  firs: {
    async list(params = {}) {
      const query = new URLSearchParams(params).toString();
      return await API.request(`/api/firs${query ? "?" + query : ""}`);
    },

    async get(id) {
      return await API.request(`/api/firs/${id}`);
    },

    async register(payload) {
      return await API.request("/api/firs", {
        method: "POST",
        body: JSON.stringify(payload)
      });
    },

    async updateStatus(id, payload) {
      return await API.request(`/api/firs/${id}/status`, {
        method: "PATCH",
        body: JSON.stringify(payload)
      });
    },

    getReportUrl(firId) {
      return `${API_BASE}/api/firs/${firId}/report`;
    }
  },

  // Evidence Endpoints
  evidence: {
    async upload(complaintId, file, description, fileType) {
      const formData = new FormData();
      formData.append("file", file);
      if (description) formData.append("description", description);
      if (fileType) formData.append("file_type", fileType);

      return await API.request(`/api/evidence/upload/${complaintId}`, {
        method: "POST",
        body: formData
      });
    },

    async list(complaintId) {
      return await API.request(`/api/evidence/${complaintId}`);
    },

    getFileUrl(evidenceId) {
      return `${API_BASE}/api/evidence/file/${evidenceId}`;
    }
  },

  // AI & NLP Partner Endpoints
  ai: {
    async getPending() {
      return await API.request("/api/ai/pending-complaints");
    },

    async triggerMock(complaintId) {
      return await API.request(`/api/ai/mock-analyze/${complaintId}`, {
        method: "POST"
      });
    }
  },

  // Stats & GIS Map Endpoints
  stats: {
    async getDashboard() {
      return await API.request("/api/stats/dashboard");
    },

    async getCrimeMap() {
      return await API.request("/api/stats/crime-map");
    }
  }
};
