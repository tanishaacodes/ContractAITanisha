import api from '../utils/api';

const BASE = '/acl';

const advancedClauseLibraryService = {
  seedTaxonomy: () => api.post(`${BASE}/seed/`),

  getTree: () => api.get(`${BASE}/tree/`),

  getAnalytics: () => api.get(`${BASE}/analytics/`),

  processContract: (contractId) => api.post(`${BASE}/process/${contractId}/`),

  search: (query, topK = 20) =>
    api.post(`${BASE}/search/`, { query, top_k: topK }),

  cleanTaxonomy: () => api.post(`${BASE}/clean/`),

  getCategories: () => api.get(`${BASE}/categories/`),

  getClausesInCategory: (categoryName) =>
    api.get(`${BASE}/clauses/${encodeURIComponent(categoryName)}/`),

  getGraph: (limit = 150) =>
    api.get(`${BASE}/graph/?limit=${limit}`),

  getInsights: (categoryName) =>
    api.get(`${BASE}/insights/${encodeURIComponent(categoryName)}/`),

  scoreRisk: (text) =>
    api.post(`${BASE}/score-risk/`, { text }),

  negotiate: (text, mode) =>
    api.post(`${BASE}/negotiate/`, { text, mode }),

  getContractRisk: () =>
    api.get(`${BASE}/contract-risk/`),

  processAll: () =>
    api.post(`${BASE}/process-all/`),
};

export default advancedClauseLibraryService;
