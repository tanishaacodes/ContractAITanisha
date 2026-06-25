/**
 * Negotiation Intelligence API Service
 *
 * Provides API methods for:
 * - Negotiation Outcome Prediction
 * - Counterparty Behavior Analysis
 * - Multi-Clause Negotiation Simulation
 * - Silent Risk Detection
 */

import api from '../utils/api';

// ============================================================================
// NEGOTIATION PREDICTION API
// ============================================================================

export const negotiationPredictionAPI = {
  /**
   * Predict outcome for a single clause
   * @param {Object} payload - Prediction parameters
   * @param {string} payload.clause_text - The clause text
   * @param {string} payload.clause_type - Type of clause (e.g., "IP Ownership")
   * @param {string|number} payload.counterparty - Counterparty name or ID
   * @returns {Promise<Object>} Prediction results
   */
  predictClause: async (payload) => {
    try {
      const response = await api.post('/negotiation/predict', payload);
      return response.data;
    } catch (error) {
      console.error('Error predicting clause outcome:', error);
      throw error;
    }
  },

  /**
   * Predict outcomes for multiple clauses
   * @param {Object} payload - Prediction parameters
   * @param {Array<Object>} payload.clauses - Array of {clause_type, text}
   * @param {string|number} payload.counterparty - Counterparty name or ID
   * @returns {Promise<Object>} Multi-clause prediction results
   */
  predictMultiple: async (payload) => {
    try {
      const response = await api.post('/negotiation/predict-multiple', payload);
      return response.data;
    } catch (error) {
      console.error('Error predicting multiple clauses:', error);
      throw error;
    }
  },
};

// ============================================================================
// COUNTERPARTY API
// ============================================================================

export const counterpartyAPI = {
  /**
   * Get all counterparties with behavior summaries
   * @returns {Promise<Object>} List of counterparties
   */
  listAll: async () => {
    try {
      const response = await api.get('/negotiation/counterparties');
      return response.data;
    } catch (error) {
      console.error('Error fetching counterparties:', error);
      throw error;
    }
  },

  /**
   * Create a new counterparty
   * @param {Object} payload - Counterparty data
   * @param {string} payload.name - Counterparty name
   * @param {string} payload.industry - Industry (optional)
   * @returns {Promise<Object>} Created counterparty
   */
  create: async (payload) => {
    try {
      const response = await api.post('/negotiation/counterparties', payload);
      return response.data;
    } catch (error) {
      console.error('Error creating counterparty:', error);
      throw error;
    }
  },

  /**
   * Get detailed behavior analysis for a counterparty
   * @param {string} counterpartyId - Counterparty ID
   * @returns {Promise<Object>} Behavior metrics and analysis
   */
  getBehavior: async (counterpartyId) => {
    try {
      const response = await api.get(`/negotiation/counterparty/${counterpartyId}/behavior`);
      return response.data;
    } catch (error) {
      console.error('Error fetching counterparty behavior:', error);
      throw error;
    }
  },
};

// ============================================================================
// NEGOTIATION SIMULATION API
// ============================================================================

export const simulationAPI = {
  /**
   * Get cached simulation for a contract-counterparty pair
   * @param {string} contractId - Contract ID
   * @param {string|number} counterpartyId - Counterparty ID or name
   * @returns {Promise<Object>} Cached simulation results
   */
  getSimulation: async (contractId, counterpartyId) => {
    try {
      const response = await api.get(`/negotiation/simulate/${contractId}/${counterpartyId}`);
      return response.data;
    } catch (error) {
      // Cache miss is expected - don't log as error
      throw error;
    }
  },

  /**
   * Simulate multi-clause negotiation
   * @param {Object} payload - Simulation parameters
   * @param {string} payload.contract_id - Contract ID (for caching)
   * @param {string|number} payload.counterparty - Counterparty name or ID
   * @param {Array<Object>} payload.clauses - Array of {clause_type, text}
   * @param {boolean} payload.force_refresh - Force new simulation (ignore cache)
   * @returns {Promise<Object>} Simulation results and strategy
   */
  simulate: async (payload) => {
    try {
      const response = await api.post('/negotiation/simulate', payload);
      return response.data;
    } catch (error) {
      console.error('Error running negotiation simulation:', error);
      throw error;
    }
  },
};

// ============================================================================
// SILENT RISK DETECTION API
// ============================================================================

export const silentRiskAPI = {
  /**
   * Detect silent risks in a contract
   * @param {string} contractId - Contract ID
   * @returns {Promise<Object>} Detected silent risks
   */
  detectRisks: async (contractId) => {
    try {
      const response = await api.get(`/negotiation/silent-risk/${contractId}`);
      return response.data;
    } catch (error) {
      console.error('Error detecting silent risks:', error);
      throw error;
    }
  },

  /**
   * Get heatmap data for silent risk visualization
   * @param {string} contractId - Contract ID
   * @param {boolean} forceRefresh - Force regeneration (ignore cache)
   * @returns {Promise<Object>} Heatmap data with clauses and risk matrix
   */
  getHeatmap: async (contractId, forceRefresh = false) => {
    try {
      const url = `/negotiation/silent-risk/${contractId}/heatmap${forceRefresh ? '?force_refresh=true' : ''}`;
      const response = await api.get(url);
      return response.data;
    } catch (error) {
      console.error('Error fetching silent risk heatmap:', error);
      throw error;
    }
  },

  /**
   * Get detailed explanation for a silent risk
   * @param {Object} payload - Risk data
   * @param {string} payload.risk_type - Type of risk
   * @param {number} payload.financial_exposure - Financial exposure amount
   * @param {Array<string>} payload.clause_pair - Array of clause types
   * @returns {Promise<Object>} Detailed risk explanation
   */
  explainRisk: async (payload) => {
    try {
      const response = await api.post('/negotiation/silent-risk/explain', payload);
      return response.data;
    } catch (error) {
      console.error('Error explaining silent risk:', error);
      throw error;
    }
  },
};

// ============================================================================
// EXCULPATORY CLAUSE ANALYSIS API
// ============================================================================

export const exculpatoryAPI = {
  /**
   * Get cached exculpatory analysis for a contract
   * @param {string} contractId - Contract ID
   * @param {boolean} forceRefresh - Force re-analysis (ignore cache)
   * @returns {Promise<Object>} Analysis results with clauses and summary
   */
  getAnalysis: async (contractId, forceRefresh = false) => {
    try {
      const url = `/negotiation/exculpatory/${contractId}${forceRefresh ? '?force_refresh=true' : ''}`;
      const response = await api.get(url);
      return response.data;
    } catch (error) {
      console.error('Error fetching exculpatory analysis:', error);
      throw error;
    }
  },

  /**
   * Run exculpatory clause analysis on a contract
   * @param {string} contractId - Contract ID
   * @param {boolean} forceRefresh - Force new analysis (ignore cache)
   * @returns {Promise<Object>} Complete analysis with clause-level details
   */
  analyzeContract: async (contractId, forceRefresh = false) => {
    try {
      const response = await api.post('/negotiation/exculpatory/analyze', {
        contract_id: contractId,
        force_refresh: forceRefresh
      });
      return response.data;
    } catch (error) {
      console.error('Error analyzing contract for exculpatory clauses:', error);
      throw error;
    }
  },
};

// ============================================================================
// COMBINED EXPORT
// ============================================================================

const negotiationAPI = {
  prediction: negotiationPredictionAPI,
  counterparty: counterpartyAPI,
  simulation: simulationAPI,
  silentRisk: silentRiskAPI,
  exculpatory: exculpatoryAPI,
};

export default negotiationAPI;
