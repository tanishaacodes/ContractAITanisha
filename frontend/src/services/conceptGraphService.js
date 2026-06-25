/**
 * Concept Correlation Graph Engine — API Service
 * Endpoints for Contract Concept Risk Topology Engine.
 */

import api from '../utils/api';

const BASE = '/concept-graph';

/** Fetch all 5 archetype graphs + global graph in one call */
export const getAllConceptGraphs = () =>
  api.get(`${BASE}/all/`).then(r => r.data);

/**
 * Fetch graph for a specific archetype.
 * @param {string} contractType  MSA | SaaS | NDA | Employment | EPC | ALL
 */
export const getConceptGraphByType = (contractType) =>
  api.get(`${BASE}/${contractType}/`).then(r => r.data);

/** Fetch the raw Pearson correlation matrix */
export const getCorrelationMatrix = () =>
  api.get(`${BASE}/matrix/`).then(r => r.data);

/** Fetch per-concept strength summary across archetypes */
export const getConceptSummary = () =>
  api.get(`${BASE}/summary/`).then(r => r.data);

// ============================================================================
// NEW: Real Contract Data Extraction APIs
// ============================================================================

/**
 * Fetch concept graph for a specific contract (extracted from real clauses).
 * @param {string} contractId - Contract UUID
 * @returns {Promise} Graph with nodes, edges, concept_strengths
 */
export const getContractConceptGraph = (contractId) =>
  api.get(`${BASE}/contract/${contractId}/`).then(r => r.data);

/**
 * Compare concept profiles between two contracts.
 * @param {string} contractId1 - First contract UUID
 * @param {string} contractId2 - Second contract UUID
 * @returns {Promise} Concept differences and major changes
 */
export const compareContracts = (contractId1, contractId2) =>
  api.post(`${BASE}/compare/`, {
    contract_id_1: contractId1,
    contract_id_2: contractId2
  }).then(r => r.data);

// ============================================================================
// NEW: Advanced Analytics APIs
// ============================================================================

/**
 * Compute centrality metrics for concept graph.
 * @param {string} contractType - Optional (MSA/SaaS/NDA/Employment/EPC/ALL)
 * @returns {Promise} Centrality metrics and rankings
 */
export const getConceptCentrality = (contractType = 'ALL') =>
  api.get(`${BASE}/analytics/centrality/`, {
    params: { contract_type: contractType }
  }).then(r => r.data);

/**
 * Detect concept communities using Louvain algorithm.
 * @param {string} contractType - Optional (MSA/SaaS/NDA/Employment/EPC/ALL)
 * @returns {Promise} Communities, modularity score, descriptions
 */
export const getConceptCommunities = (contractType = 'ALL') =>
  api.get(`${BASE}/analytics/communities/`, {
    params: { contract_type: contractType }
  }).then(r => r.data);

/**
 * Track concept evolution across contract versions.
 * @param {string} contractId - Contract UUID
 * @returns {Promise} Evolution timeline with snapshots
 */
export const getConceptEvolution = (contractId) =>
  api.get(`${BASE}/analytics/evolution/${contractId}/`).then(r => r.data);
