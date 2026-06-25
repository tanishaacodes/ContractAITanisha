import api from '../utils/api';

/**
 * Run full legal review pipeline for a contract.
 * POST /api/legal-review/contracts/:contractId/analyze
 */
export const runLegalReview = async (contractId) => {
  const response = await api.post(`/legal-review/contracts/${contractId}/analyze`);
  return response.data;
};

/**
 * Get LLM explanation for a single clause.
 * POST /api/legal-review/explain
 */
export const explainClause = async (clauseText, risk, cases) => {
  const response = await api.post('/legal-review/explain', {
    clause_text: clauseText,
    risk,
    cases,
  });
  return response.data;
};

/**
 * Get Adv. Legal Review system stats.
 * GET /api/legal-review/stats
 */
export const getLegalReviewStats = async () => {
  const response = await api.get('/legal-review/stats');
  return response.data;
};

/**
 * Browse case law store.
 * GET /api/legal-review/case-law?search=...
 */
export const getCaseLaw = async (search = '') => {
  const response = await api.get('/legal-review/case-law', {
    params: search ? { search } : {},
  });
  return response.data;
};

/**
 * RAG-based clause analysis.
 * POST /api/legal-review/rag
 */
export const ragSearch = async (query, contractId = null) => {
  const response = await api.post('/legal-review/rag', {
    query,
    contract_id: contractId,
  });
  return response.data;
};

/**
 * GraphRAG entity-aware analysis.
 * POST /api/legal-review/graphrag
 */
export const graphRagSearch = async (query, contractId = null) => {
  const response = await api.post('/legal-review/graphrag', {
    query,
    contract_id: contractId,
  });
  return response.data;
};

/**
 * Legal Co-Pilot 3-agent query.
 * POST /api/legal-review/copilot
 */
export const queryCopilot = async (query, contractId = null, clauseText = '') => {
  const response = await api.post('/legal-review/copilot', {
    query,
    contract_id: contractId,
    clause_text: clauseText,
  });
  return response.data;
};

/**
 * Get live legal events feed.
 * GET /api/legal-review/live-events?jurisdiction=...&limit=...
 */
export const getLiveEvents = async (jurisdiction = '', limit = 20) => {
  const response = await api.get('/legal-review/live-events', {
    params: { jurisdiction, limit },
  });
  return response.data;
};

/**
 * Process / crawl a live legal event.
 * POST /api/legal-review/events/process
 */
export const processEvent = async (eventData) => {
  const response = await api.post('/legal-review/events/process', eventData);
  return response.data;
};

/**
 * Find precedent similar cases (Westlaw-style).
 * POST /api/legal-review/precedents/similar
 */
export const findPrecedents = async (clauseText, jurisdiction = '', topK = 5) => {
  const response = await api.post('/legal-review/precedents/similar', {
    clause_text: clauseText,
    jurisdiction,
    top_k: topK,
  });
  return response.data;
};

/**
 * Update CPT from litigation outcome (online learning).
 * POST /api/legal-review/cpt/update
 */
export const updateCPT = async (outcomeData) => {
  const response = await api.post('/legal-review/cpt/update', outcomeData);
  return response.data;
};

/**
 * Get Neo4j graph for a contract.
 * GET /api/legal-review/neo4j/graph/:contractId
 */
export const getNeo4jGraph = async (contractId) => {
  const response = await api.get(`/legal-review/neo4j/graph/${contractId}`);
  return response.data;
};

/**
 * Trigger live crawler for a jurisdiction / source.
 * POST /api/legal-review/crawler/trigger
 */
export const triggerCrawler = async (jurisdiction = 'IN', source = '') => {
  const response = await api.post('/legal-review/crawler/trigger', {
    jurisdiction,
    source,
  });
  return response.data;
};

/**
 * Poll SSE broadcast queue for new events pushed since `since` offset.
 * GET /api/legal-review/sse-events?since=<index>
 */
export const pollSSEEvents = async (since = 0) => {
  const response = await api.get('/legal-review/sse-events', { params: { since } });
  return response.data;
};

/**
 * Run auto what-if simulation for an event against clause types.
 * POST /api/legal-review/simulate-event
 */
export const simulateEvent = async (eventDescription, eventType = 'regulatory', clauseTypes = [], contractId = '') => {
  const response = await api.post('/legal-review/simulate-event', {
    event_description: eventDescription,
    event_type: eventType,
    clause_types: clauseTypes,
    contract_id: contractId,
  });
  return response.data;
};

/**
 * Auto-Redline: batch rewrite all HIGH/MEDIUM clauses for a contract.
 * POST /api/legal-review/auto-redline
 */
export const autoRedline = async (contractId) => {
  const response = await api.post('/legal-review/auto-redline', {
    contract_id: contractId,
  });
  return response.data;
};
