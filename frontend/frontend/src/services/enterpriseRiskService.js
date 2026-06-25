import api from '../utils/api';

/**
 * Enterprise Risk & Profitability Intelligence Service
 * Handles all API calls for CFO-grade analytics
 */

class EnterpriseRiskService {

  /**
   * Get comprehensive risk dashboard data for a contract
   */
  async getDashboardData(contractId) {
    try {
      const response = await api.get(`/enterprise/dashboard/${contractId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      throw error;
    }
  }

  /**
   * Get visual graph data (nodes + edges) for contract knowledge graph
   */
  async getContractGraph(contractId) {
    try {
      const response = await api.get(`/enterprise/graph/${contractId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching contract graph:', error);
      throw error;
    }
  }

  /**
   * Get supply chain risk analysis
   */
  async getSupplyChainRisk(contractId) {
    try {
      const response = await api.get(`/enterprise/supply-chain/${contractId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching supply chain risk:', error);
      throw error;
    }
  }

  /**
   * Get geo-political risk data with country coordinates
   */
  async getGeoPoliticalRisk(contractId) {
    try {
      const response = await api.get(`/enterprise/geo-risk/${contractId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching geo-political risk:', error);
      throw error;
    }
  }

  /**
   * Get commodity price forecast simulation
   */
  async getCommodityForecast(contractId, params = {}) {
    try {
      const response = await api.get(`/enterprise/commodity-forecast/${contractId}`, { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching commodity forecast:', error);
      throw error;
    }
  }

  /**
   * Run Monte Carlo simulation for VaR analysis
   */
  async runMonteCarloSimulation(contractId, iterations = 30000) {
    try {
      const response = await api.post(`/enterprise/monte-carlo/${contractId}`, {
        iterations
      });
      return response.data;
    } catch (error) {
      console.error('Error running Monte Carlo simulation:', error);
      throw error;
    }
  }

  /**
   * Get margin sensitivity analysis (tornado chart data)
   */
  async getMarginSensitivity(contractId) {
    try {
      const response = await api.get(`/enterprise/margin-sensitivity/${contractId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching margin sensitivity:', error);
      throw error;
    }
  }

  /**
   * Get portfolio-level VaR aggregation
   */
  async getPortfolioVaR() {
    try {
      const response = await api.get('/enterprise/portfolio-var');
      return response.data;
    } catch (error) {
      console.error('Error fetching portfolio VaR:', error);
      throw error;
    }
  }

  /**
   * Get exposure waterfall data
   */
  async getExposureWaterfall(contractId) {
    try {
      const response = await api.get(`/enterprise/exposure-waterfall/${contractId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching exposure waterfall:', error);
      throw error;
    }
  }

  /**
   * Simulate systemic shocks
   */
  async simulateSystemicShock(contractId, shockParams) {
    try {
      const response = await api.post(`/enterprise/simulate-shock/${contractId}`, shockParams);
      return response.data;
    } catch (error) {
      console.error('Error simulating systemic shock:', error);
      throw error;
    }
  }

  /**
   * Get all contracts for portfolio analysis
   */
  async getPortfolioContracts() {
    try {
      const response = await api.get('/enterprise/portfolio/contracts');
      return response.data;
    } catch (error) {
      console.error('Error fetching portfolio contracts:', error);
      throw error;
    }
  }
}

export default new EnterpriseRiskService();
