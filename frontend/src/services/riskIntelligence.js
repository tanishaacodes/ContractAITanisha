/**
 * Risk Intelligence API Service
 * ==============================
 * Client for graph-based risk intelligence endpoints
 */

import api from '../utils/api';

/**
 * Run Monte Carlo exposure simulation
 */
export const runMonteCarloSimulation = async (contractId, iterations = 5000) => {
  const response = await api.post('/risk-intelligence/monte-carlo', {
    contract_id: contractId,
    iterations,
  });
  return response.data;
};

/**
 * Calculate Value at Risk (VaR)
 */
export const calculateVaR = async (contractId, confidenceLevel = 0.95) => {
  const response = await api.post('/risk-intelligence/var', {
    contract_id: contractId,
    confidence_level: confidenceLevel,
  });
  return response.data;
};

/**
 * Run stress test scenarios
 */
export const runStressTest = async (contractId) => {
  const response = await api.post('/risk-intelligence/stress-test', {
    contract_id: contractId,
  });
  return response.data;
};

/**
 * Get risk subgraph for visualization
 */
export const getRiskSubgraph = async (contractId) => {
  const response = await api.get(`/risk-intelligence/risk-subgraph/${contractId}/`);
  return response.data;
};

/**
 * Search for similar clauses
 */
export const searchSimilarClauses = async (params) => {
  const response = await api.post('/risk-intelligence/similar-clauses', params);
  return response.data;
};

/**
 * Analyze risk propagation
 */
export const analyzeRiskPropagation = async (contractId, sourceClauseId = null) => {
  const response = await api.post('/risk-intelligence/propagate', {
    contract_id: contractId,
    source_clause_id: sourceClauseId,
  });
  return response.data;
};

/**
 * Setup graph schema (one-time initialization)
 */
export const setupGraphSchema = async (options = {}) => {
  const response = await api.post('/risk-intelligence/setup-graph', {
    apply_schema: options.applySchema !== false,
    seed_risks: options.seedRisks !== false,
    seed_jurisdictions: options.seedJurisdictions !== false,
  });
  return response.data;
};

/**
 * Get cascading risk impacts using multi-hop traversal
 */
export const getCascadingRisks = async (riskId, maxDepth = 3) => {
  const response = await api.get(`/risk-intelligence/cascading-risks/${riskId}/?max_depth=${maxDepth}`);
  return response.data;
};

/**
 * Calculate blast radius for all risks in contract
 */
export const getBlastRadius = async (contractId, maxHops = 3) => {
  const response = await api.get(`/risk-intelligence/blast-radius/${contractId}/?max_hops=${maxHops}`);
  return response.data;
};

/**
 * Get risk subgraph with multi-hop edges for visualization
 */
export const getRiskSubgraphMultihop = async (contractId, maxHops = 2) => {
  const response = await api.get(`/risk-intelligence/risk-subgraph-multihop/${contractId}/?max_hops=${maxHops}`);
  return response.data;
};

export default {
  runMonteCarloSimulation,
  calculateVaR,
  runStressTest,
  getRiskSubgraph,
  searchSimilarClauses,
  analyzeRiskPropagation,
  setupGraphSchema,
  getCascadingRisks,
  getBlastRadius,
  getRiskSubgraphMultihop,
};
