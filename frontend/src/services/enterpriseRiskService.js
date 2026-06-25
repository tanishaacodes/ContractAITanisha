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
      const url = contractId && contractId !== 'CONTRACT_X'
        ? `/enterprise/dashboard/${contractId}`
        : '/enterprise/dashboard/';
      const response = await api.get(url);
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
      const url = contractId && contractId !== 'CONTRACT_X'
        ? `/enterprise/supply-chain/${contractId}`
        : '/enterprise/supply-chain/';
      const response = await api.get(url);
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
      // Geo-political risk is global — no need for contractId
      const response = await api.get('/enterprise/geo-risk/');
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
      const url = contractId
        ? `/enterprise/commodity-forecast/${contractId}/`
        : '/enterprise/commodity-forecast/';
      const response = await api.get(url, { params });
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
      const response = await api.post(`/enterprise/monte-carlo/${contractId}/`, {
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

  /**
   * Get real-time commodity price
   */
  async getRealTimeCommodityPrice(commodityName) {
    try {
      const response = await api.get(`/enterprise/commodity-prices/${commodityName}/`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching price for ${commodityName}:`, error);
      throw error;
    }
  }

  /**
   * Update all commodity prices from live APIs
   */
  async updateCommodityPrices() {
    try {
      const response = await api.post('/enterprise/commodity-prices/update/');
      return response.data;
    } catch (error) {
      console.error('Error updating commodity prices:', error);
      throw error;
    }
  }
}

export default new EnterpriseRiskService();
