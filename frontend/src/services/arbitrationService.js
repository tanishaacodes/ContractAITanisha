/**
 * Arbitration Risk Intelligence Service
 * ========================================
 * Enterprise API client for $100M+ EPC contract arbitration analysis.
 *
 * Endpoints:
 *   arbitrationAnalyze        — Full pipeline (clauses + MC + tribunal + graph)
 *   arbitrationMonteCarlo     — Correlated 50k-run Monte Carlo
 *   arbitrationScenarios      — Seat × tribunal × cost_rule scenarios
 *   arbitrationTribunal       — Monte Carlo tribunal simulation
 *   arbitrationExposure       — Exposure + settlement recommendation
 *   arbitrationOptimize       — Clause config optimizer
 *   arbitrationStrategies     — Legal strategy evaluator
 *   arbitrationKnowledgeGraph — Neo4j-style 32-node graph for a contract
 *   arbitrationCanonicalGraph — Static canonical graph (no contract needed)
 *   arbitrationExtractClauses — Clause extraction only
 */

import api from '../utils/api';

const BASE = '/arbitration';

/**
 * Run the full arbitration risk analysis pipeline.
 *
 * @param {Object} params
 * @param {string}  [params.contractId]      — existing contract UUID
 * @param {string}  [params.contractText]    — raw text override
 * @param {number}   params.contractValue    — e.g. 150_000_000
 * @param {number}  [params.settlementOffer] — optional settlement amount
 * @param {number}  [params.monteCarloRuns]  — default 50000
 * @param {number}  [params.tribunalRuns]    — default 5000
 */
export const arbitrationAnalyze = async ({
  contractId,
  contractText,
  contractValue,
  settlementOffer,
  monteCarloRuns = 50000,
  tribunalRuns   = 5000,
}) => {
  const body = { contract_value: contractValue, monte_carlo_runs: monteCarloRuns, tribunal_runs: tribunalRuns };
  if (contractId)      body.contract_id       = contractId;
  if (contractText)    body.contract_text      = contractText;
  if (settlementOffer !== undefined) body.settlement_offer = settlementOffer;

  const res = await api.post(`${BASE}/analyze`, body);
  return res.data;
};

/**
 * Standalone correlated Monte Carlo simulation.
 */
export const arbitrationMonteCarlo = async ({ contractId, contractValue, runs = 50000 }) => {
  const body = { contract_value: contractValue, runs };
  if (contractId) body.contract_id = contractId;
  const res = await api.post(`${BASE}/monte-carlo`, body);
  return res.data;
};

/**
 * Scenario engine — seat × tribunal × cost_rule cross-product.
 */
export const arbitrationScenarios = async ({ contractValue, topN = 10 }) => {
  const res = await api.post(`${BASE}/scenarios`, {
    contract_value: contractValue,
    top_n:          topN,
  });
  return res.data;
};

/**
 * Tribunal simulation.
 *
 * @param {Object} features  — { clause_strength, precedent_score, jurisdiction_score, claim_strength, delay_evidence }
 * @param {number} contractValue
 * @param {number} [runs=5000]
 */
export const arbitrationTribunal = async ({ features, contractValue, runs = 5000 }) => {
  const res = await api.post(`${BASE}/tribunal`, {
    features,
    contract_value: contractValue,
    runs,
  });
  return res.data;
};

/**
 * Arbitration exposure + optional settlement recommendation.
 */
export const arbitrationExposure = async ({
  contractValue,
  disputeProbability,
  tribunalResult,
  settlementOffer,
}) => {
  const body = {
    contract_value:      contractValue,
    dispute_probability: disputeProbability,
    tribunal_result:     tribunalResult,
  };
  if (settlementOffer !== undefined) body.settlement_offer = settlementOffer;
  const res = await api.post(`${BASE}/exposure`, body);
  return res.data;
};

/**
 * Negotiation optimizer — finds min-cost clause configuration.
 */
export const arbitrationOptimize = async ({ contractValue }) => {
  const res = await api.post(`${BASE}/optimize`, { contract_value: contractValue });
  return res.data;
};

/**
 * Legal strategy evaluator — compares 5 strategies by buyer win probability.
 */
export const arbitrationStrategies = async ({ features, contractValue, runs = 2000 }) => {
  const res = await api.post(`${BASE}/strategies`, {
    features,
    contract_value: contractValue,
    runs,
  });
  return res.data;
};

/**
 * Get 32-node arbitration knowledge graph for an existing contract.
 */
export const arbitrationKnowledgeGraph = async (contractId) => {
  const res = await api.get(`${BASE}/knowledge-graph/${contractId}/`);
  return res.data;
};

/**
 * Get the canonical 32-node arbitration graph (no contract needed).
 */
export const arbitrationCanonicalGraph = async () => {
  const res = await api.get(`${BASE}/canonical-graph/`);
  return res.data;
};

/**
 * Extract and score arbitration clauses from text or contract ID.
 */
export const arbitrationExtractClauses = async ({ contractId, contractText }) => {
  const body = {};
  if (contractId)   body.contract_id   = contractId;
  if (contractText) body.contract_text = contractText;
  const res = await api.post(`${BASE}/extract-clauses`, body);
  return res.data;
};

/**
 * Get arbitration analysis by ID (includes all persisted data).
 */
export const getArbitrationAnalysis = async (analysisId) => {
  const res = await api.get(`${BASE}/analysis/${analysisId}/`);
  return res.data;
};

/**
 * Get clause rewrites for an analysis.
 */
export const getClauseRewrites = async (analysisId) => {
  const res = await api.get(`${BASE}/rewrites/${analysisId}/`);
  return res.data;
};

/**
 * Get GNN prediction for an analysis.
 */
export const getGNNPrediction = async (analysisId) => {
  const res = await api.get(`${BASE}/gnn-prediction/${analysisId}/`);
  return res.data;
};

/**
 * Find semantically similar clauses.
 */
export const findSimilarClauses = async (clauseId, minSimilarity = 0.7) => {
  const res = await api.post(`${BASE}/similar-clauses/`, {
    clause_id: clauseId,
    min_similarity: minSimilarity,
  });
  return res.data;
};

/**
 * Get Neo4j graph for a contract.
 */
export const getNeo4jGraph = async (contractId) => {
  const res = await api.get(`${BASE}/neo4j-graph/${contractId}/`);
  return res.data;
};

/**
 * Rewrite a high-risk clause with AI.
 */
export const rewriteClause = async (clauseId, strategy = 'buyer_favorable') => {
  const res = await api.post(`${BASE}/rewrite-clause/`, {
    clause_id: clauseId,
    strategy: strategy,
  });
  return res.data;
};
