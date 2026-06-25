/**
 * Advanced AI Features API Service
 *
 * Provides API methods for:
 * - Contract Counterfactual Engine (CCE)
 * - Autonomous Contract Drift Detection (ACDD)
 */

import api from '../utils/api';

// ============================================================================
// COUNTERFACTUAL ENGINE API
// ============================================================================

export const counterfactualAPI = {
  /**
   * Run a counterfactual simulation
   * @param {Object} payload - Simulation parameters
   * @param {string} payload.contract_id - Contract identifier
   * @param {string} payload.contract_text - Full contract text
   * @param {string} payload.original_clause - Original clause
   * @param {string} payload.modified_clause - Modified clause to test
   * @param {Object} payload.filters - Optional filters (contract_type, industry)
   * @returns {Promise<Object>} Simulation results
   */
  simulate: async (payload) => {
    try {
      const response = await api.post('/counterfactual/simulate/', payload);
      return response.data;
    } catch (error) {
      console.error('Error running counterfactual simulation:', error);
      throw error;
    }
  },

  /**
   * Compare multiple counterfactual scenarios
   * @param {Object} payload - Comparison parameters
   * @param {string} payload.contract_id - Contract identifier
   * @param {string} payload.contract_text - Full contract text
   * @param {string} payload.original_clause - Original clause
   * @param {Array<string>} payload.modified_clauses - Array of alternative clauses
   * @returns {Promise<Object>} Comparison results with ranked scenarios
   */
  compare: async (payload) => {
    try {
      const response = await api.post('/counterfactual/compare/', payload);
      return response.data;
    } catch (error) {
      console.error('Error comparing scenarios:', error);
      throw error;
    }
  },

  /**
   * Get user's counterfactual scenario history
   * @param {string} contractId - Optional contract ID filter
   * @param {number} limit - Maximum number of results (default: 10)
   * @returns {Promise<Object>} Scenario history
   */
  getHistory: async (contractId = null, limit = 10) => {
    try {
      const params = { limit };
      if (contractId) params.contract_id = contractId;

      const response = await api.get('/counterfactual/history/', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching scenario history:', error);
      throw error;
    }
  },

  /**
   * Get detailed information about a specific scenario
   * @param {number} scenarioId - Scenario ID
   * @returns {Promise<Object>} Detailed scenario data
   */
  getScenario: async (scenarioId) => {
    try {
      const response = await api.get(`/counterfactual/scenario/${scenarioId}/`);
      return response.data;
    } catch (error) {
      console.error('Error fetching scenario details:', error);
      throw error;
    }
  },

  /**
   * Get historical contract outcomes
   * @param {number} limit - Maximum number of results
   * @param {string} contractType - Optional contract type filter
   * @returns {Promise<Object>} Historical outcomes
   */
  getHistoricalOutcomes: async (limit = 20, contractType = null) => {
    try {
      const params = { limit };
      if (contractType) params.contract_type = contractType;

      const response = await api.get('/counterfactual/outcomes/', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching historical outcomes:', error);
      throw error;
    }
  },

  /**
   * Add a new historical outcome for learning
   * @param {Object} outcome - Outcome data
   * @returns {Promise<Object>} Created outcome
   */
  addHistoricalOutcome: async (outcome) => {
    try {
      const response = await api.post('/counterfactual/outcomes/', outcome);
      return response.data;
    } catch (error) {
      console.error('Error adding historical outcome:', error);
      throw error;
    }
  },
};

// ============================================================================
// CLAUSE REWRITE API
// ============================================================================

export const clauseRewriteAPI = {
  /**
   * Rewrite a risky clause to reduce legal / financial risk.
   * @param {string} clauseText   – Original clause text
   * @param {string} riskReason   – Risk category (e.g. "unlimited_liability")
   * @returns {Promise<Object>}   – { original_clause, rewritten_clause, method, confidence }
   */
  rewrite: async (clauseText, riskReason) => {
    const response = await api.post('/clause-rewrite/', {
      clause_text: clauseText,
      risk_reason: riskReason,
    });
    return response.data;
  },
};

// ============================================================================
// COUNTER-PROPOSAL API
// ============================================================================

export const counterProposalAPI = {
  /**
   * Generate a negotiation counter-proposal clause.
   * @param {string} originalClause        – Current clause text
   * @param {string} counterpartyPosition  – What the other side wants
   * @param {string} riskTolerance         – "low" | "medium" | "high"
   * @returns {Promise<Object>}            – { counter_proposal, method, confidence, negotiation_tips }
   */
  generate: async (originalClause, counterpartyPosition, riskTolerance = 'medium') => {
    const response = await api.post('/counter-proposal/', {
      original_clause: originalClause,
      counterparty_position: counterpartyPosition,
      risk_tolerance: riskTolerance,
    });
    return response.data;
  },
};

// ============================================================================
// ADVANCED WHAT-IF API  (remove / add / counterfactual_add)
// ============================================================================

export const advancedWhatIfAPI = {
  /**
   * Run an advanced what-if simulation on a contract.
   * @param {string} contractId  – UUID of the contract
   * @param {Object} payload     – { action, clause_keyword?, clause_text?, counterfactual_objective?, contract_value? }
   * @returns {Promise<Object>}  – Full simulation result
   */
  simulate: async (contractId, payload) => {
    const response = await api.post(`/contracts/${contractId}/advanced-what-if/`, payload);
    return response.data;
  },
};

// ============================================================================
// DRIFT DETECTION API
// ============================================================================

export const driftAPI = {
  /**
   * Detect contract drift
   * @param {Object} payload - Drift detection parameters
   * @param {string} payload.contract_id - Contract identifier
   * @param {string} payload.contract_terms - Original contract terms
   * @param {string} payload.observed_behavior - Observed behavior
   * @param {Object} payload.behavior_context - Optional context
   * @param {string} payload.data_source - Data source (crm, billing, support, etc.)
   * @returns {Promise<Object>} Drift detection results
   */
  detect: async (payload) => {
    try {
      const response = await api.post('/drift/detect/', payload);
      return response.data;
    } catch (error) {
      console.error('Error detecting drift:', error);
      throw error;
    }
  },

  /**
   * Analyze drift patterns over time
   * @param {string} contractId - Contract identifier
   * @param {number} lookbackDays - Number of days to analyze (default: 90)
   * @returns {Promise<Object>} Drift pattern analysis
   */
  analyze: async (contractId, lookbackDays = 90) => {
    try {
      const response = await api.get('/drift/analysis/', {
        params: { contract_id: contractId, lookback_days: lookbackDays }
      });
      return response.data;
    } catch (error) {
      console.error('Error analyzing drift patterns:', error);
      throw error;
    }
  },

  /**
   * Get list of drift records with optional filters
   * @param {Object} filters - Filter parameters
   * @param {string} filters.contract_id - Optional contract ID filter
   * @param {string} filters.status - Optional status filter
   * @param {number} filters.min_severity - Optional minimum severity (1-10)
   * @param {number} filters.limit - Maximum results (default: 20)
   * @returns {Promise<Object>} Drift list
   */
  list: async (filters = {}) => {
    try {
      const response = await api.get('/drift/list/', { params: filters });
      return response.data;
    } catch (error) {
      console.error('Error fetching drift list:', error);
      throw error;
    }
  },

  /**
   * Get detailed information about a drift record
   * @param {number} driftId - Drift ID
   * @returns {Promise<Object>} Detailed drift data
   */
  getDrift: async (driftId) => {
    try {
      const response = await api.get(`/drift/${driftId}/`);
      return response.data;
    } catch (error) {
      console.error('Error fetching drift details:', error);
      throw error;
    }
  },

  /**
   * Update drift status
   * @param {number} driftId - Drift ID
   * @param {string} status - New status
   * @param {string} remediationTaken - Optional remediation description
   * @returns {Promise<Object>} Update result
   */
  updateStatus: async (driftId, status, remediationTaken = null) => {
    try {
      const payload = { status };
      if (remediationTaken) payload.remediation_taken = remediationTaken;

      const response = await api.put(`/drift/${driftId}/status/`, payload);
      return response.data;
    } catch (error) {
      console.error('Error updating drift status:', error);
      throw error;
    }
  },

  /**
   * Get unread drift alerts
   * @param {number} limit - Maximum number of alerts (default: 10)
   * @returns {Promise<Object>} Unread alerts
   */
  getAlerts: async (limit = 10) => {
    try {
      const response = await api.get('/drift/alerts/', { params: { limit } });
      return response.data;
    } catch (error) {
      console.error('Error fetching alerts:', error);
      throw error;
    }
  },

  /**
   * Mark an alert as read
   * @param {number} alertId - Alert ID
   * @returns {Promise<Object>} Update result
   */
  markAlertRead: async (alertId) => {
    try {
      const response = await api.put(`/drift/alerts/${alertId}/read/`);
      return response.data;
    } catch (error) {
      console.error('Error marking alert as read:', error);
      throw error;
    }
  },

  /**
   * Batch detect drift from behavior logs
   * @param {string} contractId - Contract identifier
   * @param {Array<Object>} behaviorLogs - Array of behavior log objects
   * @returns {Promise<Object>} Batch processing results
   */
  batchDetect: async (contractId, behaviorLogs) => {
    try {
      const response = await api.post('/drift/batch-detect/', {
        contract_id: contractId,
        behavior_logs: behaviorLogs
      });
      return response.data;
    } catch (error) {
      console.error('Error in batch drift detection:', error);
      throw error;
    }
  },

  /**
   * Get drift detection dashboard metrics
   * @returns {Promise<Object>} Dashboard data
   */
  getDashboard: async () => {
    try {
      const response = await api.get('/drift/dashboard/');
      return response.data;
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      throw error;
    }
  },
};

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Get severity color based on severity level
 * @param {number} severity - Severity level (1-10)
 * @returns {string} Color code
 */
export const getSeverityColor = (severity) => {
  if (severity >= 9) return '#dc2626'; // Red - Critical
  if (severity >= 7) return '#ea580c'; // Orange - High
  if (severity >= 4) return '#eab308'; // Yellow - Medium
  return '#16a34a'; // Green - Low
};

/**
 * Get risk level color
 * @param {string} riskLevel - Risk level (LOW, MEDIUM, HIGH)
 * @returns {string} Color code
 */
export const getRiskColor = (riskLevel) => {
  const colors = {
    LOW: '#16a34a',
    MEDIUM: '#eab308',
    HIGH: '#dc2626',
  };
  return colors[riskLevel] || '#6b7280';
};

/**
 * Format risk delta as percentage
 * @param {number} delta - Risk delta (-1.0 to 1.0)
 * @returns {string} Formatted string
 */
export const formatRiskDelta = (delta) => {
  const percentage = Math.abs(delta * 100).toFixed(0);
  const direction = delta < 0 ? 'safer' : delta > 0 ? 'riskier' : 'neutral';
  return `${percentage}% ${direction}`;
};

/**
 * Get drift status badge style
 * @param {string} status - Drift status
 * @returns {Object} Style object
 */
export const getDriftStatusStyle = (status) => {
  const styles = {
    detected: { bg: '#fef3c7', text: '#92400e' },
    acknowledged: { bg: '#dbeafe', text: '#1e40af' },
    remediation_planned: { bg: '#e0e7ff', text: '#3730a3' },
    remediation_in_progress: { bg: '#fce7f3', text: '#831843' },
    resolved: { bg: '#dcfce7', text: '#166534' },
    accepted: { bg: '#f3f4f6', text: '#374151' },
  };
  return styles[status] || styles.detected;
};

export default {
  counterfactualAPI,
  driftAPI,
  clauseRewriteAPI,
  counterProposalAPI,
  advancedWhatIfAPI,
  getSeverityColor,
  getRiskColor,
  formatRiskDelta,
  getDriftStatusStyle,
};
