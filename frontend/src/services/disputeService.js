/**
 * Dispute Predictor & Simulator API Service
 * ==========================================
 * API_BASE_URL: http://localhost:8002
 */

import axios from 'axios';

const API_BASE_URL = (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));

const getAuthHeaders = () => ({
  headers: {
    Authorization: `Bearer ${localStorage.getItem('token')}`,
    'Content-Type': 'application/json',
  },
});

/**
 * Run full dispute prediction on contract text + optional signals.
 */
export const predictDispute = async ({
  contractText = '',
  contractValue = 1000000,
  contractId = '',
  contractTitle = '',
  manualSignals = {},
  generateExplanation = true,
}) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/dispute-predictor/predict/`,
    {
      contract_text: contractText,
      contract_value: contractValue,
      contract_id: contractId,
      contract_title: contractTitle,
      manual_signals: manualSignals,
      generate_explanation: generateExplanation,
    },
    getAuthHeaders()
  );
  return response.data;
};

/**
 * Run scenario simulation (what-if analysis).
 */
export const simulateDisputeScenarios = async ({
  contractId = 'manual',
  baseSignals = {},
  scenarios = [],
  contractValue = 1000000,
}) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/dispute-predictor/simulate/`,
    {
      contract_id: contractId,
      base_signals: baseSignals,
      scenarios,
      contract_value: contractValue,
    },
    getAuthHeaders()
  );
  return response.data;
};

/**
 * Get the full 60-node Bayesian risk graph structure.
 * @param {Object} signals - Optional live evidence signals
 */
export const getDisputeGraph = async (signals = {}) => {
  const params = Object.keys(signals).length
    ? `?signals=${encodeURIComponent(JSON.stringify(signals))}`
    : '';
  const response = await axios.get(
    `${API_BASE_URL}/api/dispute-predictor/graph/${params}`,
    getAuthHeaders()
  );
  return response.data;
};

/**
 * List recent dispute predictions.
 */
export const listPredictions = async () => {
  const response = await axios.get(
    `${API_BASE_URL}/api/dispute-predictor/predictions/`,
    getAuthHeaders()
  );
  return response.data;
};

/**
 * Get single prediction detail.
 */
export const getPrediction = async (predictionId) => {
  const response = await axios.get(
    `${API_BASE_URL}/api/dispute-predictor/predictions/${predictionId}/`,
    getAuthHeaders()
  );
  return response.data;
};

/**
 * Delete a prediction.
 */
export const deletePrediction = async (predictionId) => {
  const response = await axios.delete(
    `${API_BASE_URL}/api/dispute-predictor/predictions/${predictionId}/`,
    getAuthHeaders()
  );
  return response.data;
};

/**
 * Analyse an existing contract from the database.
 */
export const predictFromContract = async (contractId, contractValue = null) => {
  const body = contractValue ? { contract_value: contractValue } : {};
  const response = await axios.post(
    `${API_BASE_URL}/api/dispute-predictor/predict-from-contract/${contractId}/`,
    body,
    getAuthHeaders()
  );
  return response.data;
};

/**
 * Get pre-built scenario templates.
 */
export const getPrebuiltScenarios = async () => {
  const response = await axios.get(
    `${API_BASE_URL}/api/dispute-predictor/prebuilt-scenarios/`,
    getAuthHeaders()
  );
  return response.data;
};

/**
 * BM25+BERT RAG — retrieve similar clauses from the clause library.
 */
export const getSimilarClauses = async (contractText, topK = 5) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/dispute-predictor/similar-clauses/`,
    { contract_text: contractText, top_k: topK },
    getAuthHeaders()
  );
  return response.data;
};

/**
 * Get AI component availability status (GNN / LegalBERT / RAG / Bayesian).
 */
export const getAIStatus = async () => {
  const response = await axios.get(
    `${API_BASE_URL}/api/dispute-predictor/ai-status/`,
    getAuthHeaders()
  );
  return response.data;
};

/**
 * Get clause-by-clause risk table (risk vs counterfactual vs what-if).
 * @param {string} contractText - Contract text to analyze
 * @param {number} contractValue - Contract value in USD
 */
export const getClauseRiskTable = async (contractText, contractValue = 1000000) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/dispute-predictor/clause-risk-table/`,
    { contract_text: contractText, contract_value: contractValue },
    getAuthHeaders()
  );
  return response.data;
};

/**
 * Get clause risk table for an existing contract by ID.
 */
export const getClauseRiskTableByContract = async (contractId, contractValue = 1000000) => {
  const response = await axios.get(
    `${API_BASE_URL}/api/dispute-predictor/clause-risk-table/${contractId}/?contract_value=${contractValue}`,
    getAuthHeaders()
  );
  return response.data;
};

/**
 * Time-Travel Risk Simulation — month-by-month risk evolution.
 * @param {string} contractText
 * @param {number} contractValue
 * @param {number} months - Number of months to simulate (3–24)
 */
export const getTimeTravelRisk = async (contractText, contractValue = 1000000, months = 12) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/dispute-predictor/time-travel/`,
    { contract_text: contractText, contract_value: contractValue, months },
    getAuthHeaders()
  );
  return response.data;
};

/**
 * Contract Digital Twin Simulation — full lifecycle state machine.
 * @param {number} contractValue
 * @param {number} months
 * @param {object} initialSignals - Bayesian node overrides
 * @param {string} contractText
 */
export const runDigitalTwin = async ({ contractValue = 120000000, months = 12, initialSignals = {}, contractText = '' }) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/dispute-predictor/digital-twin/simulate/`,
    { contract_value: contractValue, months, initial_signals: initialSignals, contract_text: contractText },
    getAuthHeaders()
  );
  return response.data;
};

/**
 * MCTS + RL 2-Agent Negotiation Simulator.
 * @param {number} contractValue
 * @param {object} initialState - {price, delivery_days, liability_cap, payment_terms, termination_penalty, force_majeure}
 * @param {number} rounds
 */
export const runNegotiationSimulator = async ({ contractValue = 5000000, initialState = {}, rounds = 10 }) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/dispute-predictor/negotiation/simulate/`,
    { contract_value: contractValue, initial_state: initialState, rounds },
    getAuthHeaders()
  );
  return response.data;
};

/**
 * 5-Agent Multi-Agent Negotiation System.
 * Agents: Buyer, Supplier, Regulator, Risk, Finance
 */
export const runMultiAgentNegotiation = async ({ contractValue = 5000000, initialState = {}, rounds = 5 }) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/dispute-predictor/multi-agent/negotiate/`,
    { contract_value: contractValue, initial_state: initialState, rounds },
    getAuthHeaders()
  );
  return response.data;
};

/**
 * Portfolio Dispute Heatmap — dispute risk across all contracts.
 */
export const getPortfolioDisputeHeatmap = async () => {
  const response = await axios.get(
    `${API_BASE_URL}/api/dispute-predictor/portfolio-heatmap/`,
    getAuthHeaders()
  );
  return response.data;
};

// ═══════════════════════════════════════════════════════════════
// NEW ADVANCED AI FEATURES (from 181-page spec)
// ═══════════════════════════════════════════════════════════════

/**
 * Run MCTS (Monte Carlo Tree Search) Negotiation Tree.
 * Returns tree structure for ReactFlow visualization.
 */
export const runMCTSNegotiation = async (contractData, maxIterations = 500, maxDepth = 5) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/dispute-predictor/mcts-negotiation/`,
    {
      contract: contractData,
      max_iterations: maxIterations,
      max_depth: maxDepth,
    },
    getAuthHeaders()
  );
  return response.data;
};

/**
 * Run NEW Multi-Agent Negotiation (5 agents with consensus).
 * Different from existing multi-agent system - uses MCTS + weighted consensus.
 */
export const runAdvancedMultiAgent = async (contractData, maxRounds = 5) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/dispute-predictor/multi-agent-negotiation/`,
    {
      contract: contractData,
      max_rounds: maxRounds,
    },
    getAuthHeaders()
  );
  return response.data;
};

/**
 * Optimize contract using Reinforcement Learning (Deep Q-Network).
 */
export const optimizeContractWithRL = async (contractData) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/dispute-predictor/rl-optimize/`,
    { contract: contractData },
    getAuthHeaders()
  );
  return response.data;
};

/**
 * Train RL model (admin only - long-running).
 */
export const trainRLModel = async (numEpisodes = 1000, batchSize = 64) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/dispute-predictor/train-rl/`,
    {
      num_episodes: numEpisodes,
      batch_size: batchSize,
    },
    getAuthHeaders()
  );
  return response.data;
};

/**
 * Match contract with legal precedents using LegalBERT embeddings.
 */
export const matchLegalPrecedents = async (contractText, contractValue, disputeType, jurisdiction, topK = 5) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/dispute-predictor/match-precedents/`,
    {
      contract_text: contractText,
      contract_value: contractValue,
      dispute_type: disputeType,
      jurisdiction: jurisdiction,
      top_k: topK,
    },
    getAuthHeaders()
  );
  return response.data;
};

/**
 * Get legal precedent graph data for visualization.
 */
export const getPrecedentGraph = async () => {
  const response = await axios.get(
    `${API_BASE_URL}/api/dispute-predictor/precedent-graph/`,
    getAuthHeaders()
  );
  return response.data;
};
