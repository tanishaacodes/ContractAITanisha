/**
 * Negotiation Service
 * ===================
 * API client for MCTS, Multi-Agent, RL, and Legal Precedent features
 */

import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const negotiationService = {
  /**
   * Run MCTS Negotiation Tree Search
   * @param {Object} contractData - Contract parameters
   * @param {number} maxIterations - Number of MCTS iterations (default: 500)
   * @param {number} maxDepth - Max tree depth (default: 5)
   * @returns {Promise<Object>} MCTS result with tree, best_state, best_score
   */
  async runMCTS(contractData, maxIterations = 500, maxDepth = 5) {
    try {
      const response = await axios.post(`${API_BASE}/api/dispute/mcts-negotiation/`, {
        contract: contractData,
        max_iterations: maxIterations,
        max_depth: maxDepth,
      });
      return response.data;
    } catch (error) {
      console.error('MCTS negotiation error:', error);
      throw error;
    }
  },

  /**
   * Run Multi-Agent Negotiation
   * @param {Object} contractData - Contract parameters
   * @param {number} maxRounds - Number of negotiation rounds (default: 5)
   * @returns {Promise<Object>} Multi-agent result with agent_decisions, final_contract
   */
  async runMultiAgent(contractData, maxRounds = 5) {
    try {
      const response = await axios.post(`${API_BASE}/api/dispute/multi-agent-negotiation/`, {
        contract: contractData,
        max_rounds: maxRounds,
      });
      return response.data;
    } catch (error) {
      console.error('Multi-agent negotiation error:', error);
      throw error;
    }
  },

  /**
   * Optimize contract using RL agent
   * @param {Object} contractData - Contract parameters
   * @returns {Promise<Object>} RL result with optimized_contract, dispute_risk, actions_taken
   */
  async optimizeWithRL(contractData) {
    try {
      const response = await axios.post(`${API_BASE}/api/dispute/rl-optimize/`, {
        contract: contractData,
      });
      return response.data;
    } catch (error) {
      console.error('RL optimization error:', error);
      throw error;
    }
  },

  /**
   * Train RL model (admin only - long-running operation)
   * @param {number} numEpisodes - Number of training episodes (default: 1000)
   * @param {number} batchSize - Batch size for training (default: 64)
   * @returns {Promise<Object>} Training result with message, episodes, history
   */
  async trainRL(numEpisodes = 1000, batchSize = 64) {
    try {
      const response = await axios.post(`${API_BASE}/api/dispute/train-rl/`, {
        num_episodes: numEpisodes,
        batch_size: batchSize,
      });
      return response.data;
    } catch (error) {
      console.error('RL training error:', error);
      throw error;
    }
  },

  /**
   * Match contract with legal precedents
   * @param {string} contractText - Contract text for embedding
   * @param {number} contractValue - Contract value
   * @param {string} disputeType - Type of dispute (e.g., 'construction', 'commercial')
   * @param {string} jurisdiction - Jurisdiction (e.g., 'US', 'UK')
   * @param {number} topK - Number of similar precedents to return (default: 5)
   * @returns {Promise<Object>} Precedent matching result with similar_precedents, prediction
   */
  async matchPrecedents(contractText, contractValue, disputeType, jurisdiction, topK = 5) {
    try {
      const response = await axios.post(`${API_BASE}/api/dispute/match-precedents/`, {
        contract_text: contractText,
        contract_value: contractValue,
        dispute_type: disputeType,
        jurisdiction: jurisdiction,
        top_k: topK,
      });
      return response.data;
    } catch (error) {
      console.error('Precedent matching error:', error);
      throw error;
    }
  },

  /**
   * Get precedent graph data for visualization
   * @returns {Promise<Object>} Graph data with nodes and edges
   */
  async getPrecedentGraph() {
    try {
      const response = await axios.get(`${API_BASE}/api/dispute/precedent-graph/`);
      return response.data;
    } catch (error) {
      console.error('Precedent graph error:', error);
      throw error;
    }
  },
};

export default negotiationService;
