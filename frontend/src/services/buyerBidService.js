import axios from 'axios';

const API_BASE_URL = (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));

const authHeaders = () => ({
  headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
});

// ── Vendor ────────────────────────────────────────────────────────────────
export const getVendors = () =>
  axios.get(`${API_BASE_URL}/api/tenders/buyer/vendors/`, authHeaders());

export const createVendor = (data) =>
  axios.post(`${API_BASE_URL}/api/tenders/buyer/vendors/`, data, authHeaders());

// ── Bids ──────────────────────────────────────────────────────────────────
export const getBids = (tenderId) =>
  axios.get(`${API_BASE_URL}/api/tenders/tenders/${tenderId}/buyer/bids/`, authHeaders());

export const submitBid = (tenderId, data) =>
  axios.post(`${API_BASE_URL}/api/tenders/tenders/${tenderId}/buyer/bids/`, data, authHeaders());

export const deleteBid = (tenderId, bidId) =>
  axios.delete(`${API_BASE_URL}/api/tenders/tenders/${tenderId}/buyer/bids/${bidId}/`, authHeaders());

// ── Clause ────────────────────────────────────────────────────────────────
export const submitClause = (tenderId, bidId, data) =>
  axios.post(`${API_BASE_URL}/api/tenders/tenders/${tenderId}/buyer/bids/${bidId}/clauses/`, data, authHeaders());

// ── Dashboard ─────────────────────────────────────────────────────────────
export const getBuyerDashboard = (tenderId) =>
  axios.get(`${API_BASE_URL}/api/tenders/tenders/${tenderId}/buyer/dashboard/`, authHeaders());

// ── Winner ────────────────────────────────────────────────────────────────
export const getWinnerRecommendation = (tenderId) =>
  axios.get(`${API_BASE_URL}/api/tenders/tenders/${tenderId}/buyer/winner/`, authHeaders());

// ── Collusion ─────────────────────────────────────────────────────────────
export const getCollusionAnalysis = (tenderId, params = {}) =>
  axios.get(`${API_BASE_URL}/api/tenders/tenders/${tenderId}/buyer/collusion/`, {
    ...authHeaders(),
    params,
  });

// ── Legal Heatmap ─────────────────────────────────────────────────────────
export const getLegalGrid = (tenderId) =>
  axios.get(`${API_BASE_URL}/api/tenders/tenders/${tenderId}/buyer/legal-grid/`, authHeaders());

// ── Seed Demo Data ────────────────────────────────────────────────────────
export const seedDemoData = (tenderId, params = { num_vendors: 6, num_rounds: 3 }) =>
  axios.post(`${API_BASE_URL}/api/tenders/tenders/${tenderId}/buyer/seed-demo/`, params, authHeaders());
