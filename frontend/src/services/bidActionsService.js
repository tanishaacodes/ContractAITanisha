/**
 * Bid Actions Service
 * API client for bid action management
 */

const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));

const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  };
};

const handleResponse = async (response) => {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  return response.json();
};

// ===========================
// Departments
// ===========================

export const getDepartments = async () => {
  const response = await fetch(`${API_BASE}/api/bid-actions/departments/`, {
    headers: getAuthHeaders()
  });
  return handleResponse(response);
};

export const getDepartmentKeywords = async () => {
  const response = await fetch(`${API_BASE}/api/bid-actions/departments/keywords/`, {
    headers: getAuthHeaders()
  });
  return handleResponse(response);
};

// ===========================
// Action Items
// ===========================

export const getActionItems = async (params = {}) => {
  const queryParams = new URLSearchParams(params).toString();
  const url = `${API_BASE}/api/bid-actions/actions/${queryParams ? '?' + queryParams : ''}`;

  const response = await fetch(url, {
    headers: getAuthHeaders()
  });
  return handleResponse(response);
};

export const getActionItem = async (actionId) => {
  const response = await fetch(`${API_BASE}/api/bid-actions/actions/${actionId}/`, {
    headers: getAuthHeaders()
  });
  return handleResponse(response);
};

export const createActionItem = async (data) => {
  const response = await fetch(`${API_BASE}/api/bid-actions/actions/`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data)
  });
  return handleResponse(response);
};

export const updateActionItem = async (actionId, data) => {
  const response = await fetch(`${API_BASE}/api/bid-actions/actions/${actionId}/`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify(data)
  });
  return handleResponse(response);
};

export const updateActionStatus = async (actionId, status) => {
  const response = await fetch(`${API_BASE}/api/bid-actions/actions/${actionId}/update_status/`, {
    method: 'PATCH',
    headers: getAuthHeaders(),
    body: JSON.stringify({ status })
  });
  return handleResponse(response);
};

export const bulkUpdateStatus = async (actionIds, status) => {
  const response = await fetch(`${API_BASE}/api/bid-actions/actions/bulk_update_status/`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ action_ids: actionIds, status })
  });
  return handleResponse(response);
};

export const getDelayPrediction = async (actionId) => {
  const response = await fetch(`${API_BASE}/api/bid-actions/actions/${actionId}/delay_prediction/`, {
    headers: getAuthHeaders()
  });
  return handleResponse(response);
};

// ===========================
// Tender-Specific Actions
// ===========================

export const getTenderActions = async (tenderId) => {
  const response = await fetch(`${API_BASE}/api/bid-actions/tenders/${tenderId}/actions/`, {
    headers: getAuthHeaders()
  });
  return handleResponse(response);
};

export const generateTenderActions = async (tenderId) => {
  const response = await fetch(`${API_BASE}/api/bid-actions/tenders/${tenderId}/generate-actions/`, {
    method: 'POST',
    headers: getAuthHeaders()
  });
  return handleResponse(response);
};

export const regenerateTenderActions = async (tenderId) => {
  const response = await fetch(`${API_BASE}/api/bid-actions/tenders/${tenderId}/regenerate-actions/`, {
    method: 'POST',
    headers: getAuthHeaders()
  });
  return handleResponse(response);
};

export const getTenderDashboard = async (tenderId) => {
  const response = await fetch(`${API_BASE}/api/bid-actions/tenders/${tenderId}/dashboard/`, {
    headers: getAuthHeaders()
  });
  return handleResponse(response);
};

export const getRiskPropagation = async (tenderId) => {
  const response = await fetch(`${API_BASE}/api/bid-actions/tenders/${tenderId}/risk-propagation/`, {
    headers: getAuthHeaders()
  });
  return handleResponse(response);
};

export const getDependencyGraph = async (tenderId) => {
  const response = await fetch(`${API_BASE}/api/bid-actions/tenders/${tenderId}/dependency-graph/`, {
    headers: getAuthHeaders()
  });
  return handleResponse(response);
};

export const getCriticalPath = async (tenderId) => {
  const response = await fetch(`${API_BASE}/api/bid-actions/tenders/${tenderId}/critical-path/`, {
    headers: getAuthHeaders()
  });
  return handleResponse(response);
};

// ===========================
// Portfolio
// ===========================

export const getPortfolioDashboard = async () => {
  const response = await fetch(`${API_BASE}/api/bid-actions/portfolio/dashboard/`, {
    headers: getAuthHeaders()
  });
  return handleResponse(response);
};

export const getDepartmentHeatmap = async () => {
  const response = await fetch(`${API_BASE}/api/bid-actions/portfolio/department_heatmap/`, {
    headers: getAuthHeaders()
  });
  return handleResponse(response);
};

export default {
  // Departments
  getDepartments,
  getDepartmentKeywords,

  // Action Items
  getActionItems,
  getActionItem,
  createActionItem,
  updateActionItem,
  updateActionStatus,
  bulkUpdateStatus,
  getDelayPrediction,

  // Tender Actions
  getTenderActions,
  generateTenderActions,
  regenerateTenderActions,
  getTenderDashboard,
  getRiskPropagation,
  getDependencyGraph,
  getCriticalPath,

  // Portfolio
  getPortfolioDashboard,
  getDepartmentHeatmap
};
