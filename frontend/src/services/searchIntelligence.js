import axios from 'axios';

const API_BASE_URL = (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));

const getAuthHeader = () => ({
  Authorization: `Bearer ${localStorage.getItem('token')}`,
});

export const getPrebuiltSearches = () =>
  axios.get(`${API_BASE_URL}/api/search-intelligence/prebuilt/`, { headers: getAuthHeader() }).then(r => r.data);

export const runPrebuiltSearch = (searchType, limit = 20) =>
  axios.post(`${API_BASE_URL}/api/search-intelligence/prebuilt/run/`, { search_type: searchType, limit }, { headers: getAuthHeader() }).then(r => r.data);

export const semanticSearch = (query, filters = {}, limit = 20) =>
  axios.post(`${API_BASE_URL}/api/search-intelligence/semantic/`, { query, filters, limit }, { headers: getAuthHeader() }).then(r => r.data);

export const aiAgentSearch = (query) =>
  axios.post(`${API_BASE_URL}/api/search-intelligence/agent/`, { query }, { headers: getAuthHeader(), timeout: 60000 }).then(r => r.data);

export const getSearchAnalytics = () =>
  axios.get(`${API_BASE_URL}/api/search-intelligence/analytics/`, { headers: getAuthHeader() }).then(r => r.data);

// #9 multi-clause: pass clauses array for multi-clause mode
export const runNegotiationAgents = (clauseText, clauseType = 'General', rounds = 3, contractId = null, clauses = null, buyerMode = 'balanced', supplierMode = 'balanced') =>
  axios.post(`${API_BASE_URL}/api/search-intelligence/negotiate/`,
    { clause_text: clauseText, clause_type: clauseType, rounds, contract_id: contractId, clauses, buyer_mode: buyerMode, supplier_mode: supplierMode },
    { headers: getAuthHeader(), timeout: 120000 }
  ).then(r => r.data);

export const getContractStats = () =>
  axios.get(`${API_BASE_URL}/api/search-intelligence/stats/`, { headers: getAuthHeader() }).then(r => r.data);

// #4: Auto clause extraction → Neo4j
export const buildContractGraph = (contractId, useLlm = true) =>
  axios.post(`${API_BASE_URL}/api/search-intelligence/graph-build/`, { contract_id: contractId, use_llm: useLlm }, { headers: getAuthHeader(), timeout: 90000 }).then(r => r.data);

export const buildAllGraphs = () =>
  axios.get(`${API_BASE_URL}/api/search-intelligence/graph-build/`, { headers: getAuthHeader(), timeout: 180000 }).then(r => r.data);

// #3: Force Majeure risk scorer
export const scoreForceMajeure = (text = null, contractId = null) =>
  axios.post(`${API_BASE_URL}/api/search-intelligence/fm-score/`, { text, contract_id: contractId }, { headers: getAuthHeader() }).then(r => r.data);

// #8: Negotiation memory
export const getNegotiationMemory = (clauseType = null) =>
  axios.get(`${API_BASE_URL}/api/search-intelligence/memory/`, { headers: getAuthHeader(), params: clauseType ? { clause_type: clauseType } : {} }).then(r => r.data);

export const clearNegotiationMemory = (clauseType = null) =>
  axios.delete(`${API_BASE_URL}/api/search-intelligence/memory/`, { headers: getAuthHeader(), data: clauseType ? { clause_type: clauseType } : {} }).then(r => r.data);

// Multi-hop graph queries
export const graphMultiHop = (queryType, contractId = null, nodeId = null, depth = 2) =>
  axios.post(`${API_BASE_URL}/api/search-intelligence/graph-multihop/`,
    { query_type: queryType, contract_id: contractId, node_id: nodeId, depth },
    { headers: getAuthHeader(), timeout: 30000 }
  ).then(r => r.data);

// Graph node expand (click node → neighbors)
export const graphNodeExpand = (nodeId) =>
  axios.get(`${API_BASE_URL}/api/search-intelligence/graph-expand/${nodeId}/`, { headers: getAuthHeader() }).then(r => r.data);

// Clause benchmarking against industry templates
export const benchmarkClause = (clauseText, clauseType = 'force_majeure') =>
  axios.post(`${API_BASE_URL}/api/search-intelligence/benchmark/`,
    { clause_text: clauseText, clause_type: clauseType },
    { headers: getAuthHeader() }
  ).then(r => r.data);

// ─── New Advanced Features ────────────────────────────────────────

// Legal-BERT clause classification
export const classifyClauseWithLegalBERT = (clauseText, topK = 3) =>
  axios.post(`${API_BASE_URL}/api/search-intelligence/legal-bert/`,
    { clause_text: clauseText, top_k: topK },
    { headers: getAuthHeader() }
  ).then(r => r.data);

// Node2Vec graph-based recommendations
export const getNode2VecRecommendations = (nodeId, topK = 5) =>
  axios.post(`${API_BASE_URL}/api/search-intelligence/node2vec/`,
    { node_id: nodeId, top_k: topK },
    { headers: getAuthHeader() }
  ).then(r => r.data);

// LangChain ReAct agent search
export const langchainAgentSearch = (query) =>
  axios.post(`${API_BASE_URL}/api/search-intelligence/langchain-agent/`,
    { query },
    { headers: getAuthHeader(), timeout: 90000 }
  ).then(r => r.data);

// Temporal risk analysis
export const getTemporalAnalysis = (contractId, action = 'trend', daysBack = 90, daysForward = 30) =>
  axios.post(`${API_BASE_URL}/api/search-intelligence/temporal/`,
    { contract_id: contractId, action, days_back: daysBack, days_forward: daysForward },
    { headers: getAuthHeader() }
  ).then(r => r.data);

// Anomaly detection
export const detectAnomalies = () =>
  axios.post(`${API_BASE_URL}/api/search-intelligence/anomaly/`,
    {},
    { headers: getAuthHeader(), timeout: 60000 }
  ).then(r => r.data);

// Real-time graph sync
export const syncGraphRealtime = (contractId) =>
  axios.post(`${API_BASE_URL}/api/search-intelligence/realtime-sync/`,
    { contract_id: contractId },
    { headers: getAuthHeader() }
  ).then(r => r.data);

// CFO Financial Risk Metrics
export const getCFOMetrics = (action = 'report', contractId = null) =>
  axios.post(`${API_BASE_URL}/api/search-intelligence/cfo-metrics/`,
    { action, contract_id: contractId },
    { headers: getAuthHeader(), timeout: 30000 }
  ).then(r => r.data);

// Party Attribution
export const getPartyAttribution = (clauseText = null, contractId = null, clauseType = null) =>
  axios.post(`${API_BASE_URL}/api/search-intelligence/party-attribution/`,
    { clause_text: clauseText, contract_id: contractId, clause_type: clauseType },
    { headers: getAuthHeader() }
  ).then(r => r.data);

// Bulk reclassify all contracts with improved classifier
export const bulkReclassify = () =>
  axios.post(`${API_BASE_URL}/api/search-intelligence/reclassify/`, {}, { headers: getAuthHeader() }).then(r => r.data);
