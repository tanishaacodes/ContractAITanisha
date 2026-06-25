/**
 * Tender Intelligence API Service
 * Handles all API calls for tender intelligence features
 */
import axios from 'axios';
import useAuthStore from '../store/authStore';

const API_BASE = `${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/tenders`;

/**
 * Get authentication headers
 */
const getAuthHeaders = () => {
  const token = useAuthStore.getState().token;
  return {
    'Authorization': `Bearer ${token}`,
  };
};

const tenderService = {
  /**
   * Upload and analyze tender PDF
   */
  uploadAndAnalyze: async (file, title) => {
    const formData = new FormData();
    formData.append('pdf_file', file);
    formData.append('title', title || file.name);

    const response = await axios.post(`${API_BASE}/tenders/upload_and_analyze/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        ...getAuthHeaders(),
      },
    });

    return response.data;
  },

  /**
   * Get all tenders
   */
  getAllTenders: async () => {
    const response = await axios.get(`${API_BASE}/tenders/`, {
      headers: getAuthHeaders(),
    });
    return response.data;
  },

  /**
   * Get tender details
   */
  getTenderDetails: async (tenderId) => {
    const response = await axios.get(`${API_BASE}/tenders/${tenderId}/`, {
      headers: getAuthHeaders(),
    });
    return response.data;
  },

  /**
   * Check eligibility
   */
  checkEligibility: async (tenderId) => {
    const response = await axios.post(`${API_BASE}/tenders/${tenderId}/check_eligibility/`, {}, {
      headers: getAuthHeaders(),
    });
    return response.data;
  },

  /**
   * Generate proposal
   */
  generateProposal: async (tenderId) => {
    const response = await axios.post(`${API_BASE}/tenders/${tenderId}/generate_proposal/`, {}, {
      headers: getAuthHeaders(),
    });
    return response.data;
  },

  /**
   * Optimize margin
   */
  optimizeMargin: async (tenderId, marginRange = [5, 25], step = 5) => {
    const response = await axios.post(`${API_BASE}/tenders/${tenderId}/optimize_margin/`, {
      margin_range: marginRange,
      step: step,
    }, {
      headers: getAuthHeaders(),
    });
    return response.data;
  },

  /**
   * Simulate win probability
   */
  simulateWinProbability: async (tenderId) => {
    const response = await axios.post(`${API_BASE}/tenders/${tenderId}/simulate_win_probability/`, {}, {
      headers: getAuthHeaders(),
    });
    return response.data;
  },

  /**
   * Generate negotiations
   */
  generateNegotiations: async (tenderId) => {
    const response = await axios.post(`${API_BASE}/tenders/${tenderId}/generate_negotiations/`, {}, {
      headers: getAuthHeaders(),
    });
    return response.data;
  },

  /**
   * Company Profile APIs
   */
  getCompanyProfile: async () => {
    const response = await axios.get(`${API_BASE}/company-profile/`, {
      headers: getAuthHeaders(),
    });
    return response.data;
  },

  createCompanyProfile: async (profileData) => {
    const response = await axios.post(`${API_BASE}/company-profile/`, profileData, {
      headers: getAuthHeaders(),
    });
    return response.data;
  },

  updateCompanyProfile: async (profileId, profileData) => {
    const response = await axios.put(`${API_BASE}/company-profile/${profileId}/`, profileData, {
      headers: getAuthHeaders(),
    });
    return response.data;
  },

  /**
   * Export tender report as downloadable text file
   */
  exportReport: async (tenderId) => {
    const response = await axios.get(`${API_BASE}/tenders/${tenderId}/export_report/`, {
      headers: getAuthHeaders(),
      responseType: 'blob',
    });
    // Trigger browser download
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    const disposition = response.headers['content-disposition'] || '';
    const match = disposition.match(/filename="([^"]+)"/);
    link.setAttribute('download', match ? match[1] : `Tender_Report_${tenderId}.txt`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  /**
   * Upload an amended version of a tender PDF
   */
  uploadAmendment: async (tenderId, file, amendmentNote = '') => {
    const formData = new FormData();
    formData.append('pdf_file', file);
    formData.append('amendment_note', amendmentNote);
    const response = await axios.post(`${API_BASE}/tenders/${tenderId}/upload_amendment/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        ...getAuthHeaders(),
      },
    });
    return response.data;
  },

  /**
   * Get amendment history for a tender
   */
  getAmendments: async (tenderId) => {
    const response = await axios.get(`${API_BASE}/tenders/${tenderId}/amendments/`, {
      headers: getAuthHeaders(),
    });
    return response.data;
  },

  /**
   * Re-parse PDF and re-run all intelligence engines
   */
  reanalyze: async (tenderId) => {
    const response = await axios.post(`${API_BASE}/tenders/${tenderId}/reanalyze/`, {}, {
      headers: getAuthHeaders(),
    });
    return response.data;
  },

  /**
   * Delete a tender
   */
  deleteTender: async (tenderId) => {
    const response = await axios.delete(`${API_BASE}/tenders/${tenderId}/`, {
      headers: getAuthHeaders(),
    });
    return response.data;
  },

  // ─── Bid Management API ─────────────────────────────────────────────────

  /**
   * Generate BidActionItems from existing tender data (BOQ, risks, negotiations…)
   * @param {boolean} regenerate - If true, clears existing items first
   */
  generateBidActions: async (tenderId, regenerate = false) => {
    const response = await axios.post(
      `${API_BASE}/tenders/${tenderId}/bid/generate-actions/`,
      { regenerate },
      { headers: getAuthHeaders() },
    );
    return response.data;
  },

  /**
   * List action items for a tender
   * @param {object} filters - { department, priority, status, search }
   */
  getBidActions: async (tenderId, filters = {}) => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => { if (v) params.append(k, v); });
    const response = await axios.get(
      `${API_BASE}/tenders/${tenderId}/bid/actions/?${params}`,
      { headers: getAuthHeaders() },
    );
    return response.data;
  },

  /**
   * Update a single action item's status/priority/due_date
   */
  updateBidAction: async (tenderId, itemId, data) => {
    const response = await axios.patch(
      `${API_BASE}/tenders/${tenderId}/bid/actions/${itemId}/`,
      data,
      { headers: getAuthHeaders() },
    );
    return response.data;
  },

  /**
   * Get bid readiness index + steps
   */
  getBidReadiness: async (tenderId) => {
    const response = await axios.get(
      `${API_BASE}/tenders/${tenderId}/bid/readiness/`,
      { headers: getAuthHeaders() },
    );
    return response.data;
  },

  /**
   * Run DFS cross-department risk propagation cascade
   */
  runRiskPropagation: async (tenderId) => {
    const response = await axios.post(
      `${API_BASE}/tenders/${tenderId}/bid/propagate-risk/`,
      {},
      { headers: getAuthHeaders() },
    );
    return response.data;
  },

  /**
   * Get stored risk cascade results per department
   */
  getRiskCascade: async (tenderId) => {
    const response = await axios.get(
      `${API_BASE}/tenders/${tenderId}/bid/risk-cascade/`,
      { headers: getAuthHeaders() },
    );
    return response.data;
  },

  /**
   * Get dependency graph (nodes + edges) for visualization
   */
  getDependencyGraph: async (tenderId) => {
    const response = await axios.get(
      `${API_BASE}/tenders/${tenderId}/bid/dependency-graph/`,
      { headers: getAuthHeaders() },
    );
    return response.data;
  },

  /**
   * Get executive dashboard summary
   */
  getBidDashboard: async (tenderId) => {
    const response = await axios.get(
      `${API_BASE}/tenders/${tenderId}/bid/dashboard/`,
      { headers: getAuthHeaders() },
    );
    return response.data;
  },

  /**
   * Get cross-tender portfolio dashboard
   */
  getPortfolioDashboard: async () => {
    const response = await axios.get(
      `${API_BASE}/tenders/bid/portfolio/`,
      { headers: getAuthHeaders() },
    );
    return response.data;
  },

  /**
   * Get readiness trend (historical snapshots)
   */
  getReadinessTrend: async (tenderId, limit = 10) => {
    const response = await axios.get(
      `${API_BASE}/tenders/${tenderId}/bid/readiness-trend/?limit=${limit}`,
      { headers: getAuthHeaders() },
    );
    return response.data;
  },

  /**
   * Save a readiness snapshot for trend tracking
   */
  saveReadinessSnapshot: async (tenderId) => {
    const response = await axios.post(
      `${API_BASE}/tenders/${tenderId}/bid/snapshot-readiness/`,
      {},
      { headers: getAuthHeaders() },
    );
    return response.data;
  },

  /**
   * List all departments
   */
  getBidDepartments: async () => {
    const response = await axios.get(
      `${API_BASE}/tenders/bid/departments/`,
      { headers: getAuthHeaders() },
    );
    return response.data;
  },
};

export default tenderService;
