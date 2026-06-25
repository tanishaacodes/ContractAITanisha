/**
 * CUAD Graph Intelligence API Service
 * =====================================
 * Client for the Contract Differential Intelligence Engine (CDIE).
 *
 * Endpoints:
 *   POST /cuad-graph/ingest/{contractId}/   — Ingest contract into Neo4j
 *   GET  /cuad-graph/compare/               — Differential graph comparison
 *   GET  /cuad-graph/pagerank/{contractId}/ — Clause PageRank influence
 *   POST /cuad-graph/similarity/            — Structural similarity
 *   POST /cuad-graph/gnn-score/             — GNN risk/stability score
 */

import api from '../utils/api';

/**
 * Ingest a contract into Neo4j with full CUAD schema.
 * Builds 13 node types: Contract, Clause, ClauseType, Party,
 * Jurisdiction, Obligation, Risk, Industry + relationships.
 *
 * @param {string} contractId
 * @returns {Promise<{success, nodes_created, relationships_created, clauses_processed, mode}>}
 */
export const ingestContractGraph = async (contractId) => {
  const res = await api.post(`/cuad-graph/ingest/${contractId}/`);
  return res.data;
};

/**
 * Compare two contracts and return a React Flow compatible diff graph.
 * Nodes are color-coded by diff status:
 *   Green  = same clause type, similar risk
 *   Yellow = same clause type, risk differs
 *   Red    = clause missing from contract2
 *   Blue   = new clause only in contract2
 *
 * @param {string} c1Id - Contract A UUID
 * @param {string} c2Id - Contract B UUID
 * @param {number} riskWeight - Weight for risk score (0–5, default 1.0)
 * @param {number} obligationWeight - Weight for obligation density (0–5, default 1.0)
 * @returns {Promise<{nodes, edges, diff_score, diff_summary, contract1, contract2}>}
 */
export const compareContractGraph = async (c1Id, c2Id, riskWeight = 1.0, obligationWeight = 1.0) => {
  const res = await api.get('/cuad-graph/compare/', {
    params: {
      c1: c1Id,
      c2: c2Id,
      risk_weight: riskWeight,
      obligation_weight: obligationWeight,
    },
  });
  return res.data;
};

/**
 * Get PageRank-based clause influence scores for a contract.
 * Higher score = clause is more central in the risk network.
 *
 * @param {string} contractId
 * @returns {Promise<{pagerank: Array<{clause_id, clause_name, clause_type, pagerank_score, risk_score}>, node_count, edge_count}>}
 */
export const getPageRank = async (contractId) => {
  const res = await api.get(`/cuad-graph/pagerank/${contractId}/`);
  return res.data;
};

/**
 * Compute structural similarity between two contracts.
 * Uses Jaccard (clause type overlap) + cosine (risk vector) hybrid.
 *
 * @param {string} c1Id
 * @param {string} c2Id
 * @returns {Promise<{similarity_score, jaccard_similarity, cosine_similarity, clause_overlap}>}
 */
export const getContractSimilarity = async (c1Id, c2Id) => {
  const res = await api.post('/cuad-graph/similarity/', {
    contract1_id: c1Id,
    contract2_id: c2Id,
  });
  return res.data;
};

/**
 * Score a contract using Graph Neural Network (GCN).
 * Falls back to rule-based scoring if PyTorch unavailable.
 *
 * @param {string} contractId
 * @returns {Promise<{risk_score, stability_score, top_risky_clauses, method, node_count, edge_count}>}
 */
export const getGNNScore = async (contractId) => {
  const res = await api.post('/cuad-graph/gnn-score/', {
    contract_id: contractId,
  });
  return res.data;
};

/**
 * Compare 2–5 contracts in a single portfolio graph.
 * Clause coverage status:
 *   Green  (universal) = present in ALL contracts
 *   Yellow (common)    = present in majority (>50%)
 *   Orange (partial)   = present in minority (≤50%)
 *   Blue   (unique)    = present in exactly 1 contract
 *
 * @param {string[]} contractIds - Array of 2–5 contract UUIDs
 * @param {number} riskWeight - Risk weight (0–5, default 1.0)
 * @param {number} obligationWeight - Obligation weight (0–5, default 1.0)
 * @returns {Promise<{nodes, edges, contracts, coverage_summary, total_clause_types, contract_count, coverage_legend}>}
 */
export const compareMultiContractGraph = async (contractIds, riskWeight = 1.0, obligationWeight = 1.0) => {
  const res = await api.post('/cuad-graph/compare-multi/', {
    contract_ids: contractIds,
    risk_weight: riskWeight,
    obligation_weight: obligationWeight,
  });
  return res.data;
};
