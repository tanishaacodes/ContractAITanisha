import axios from 'axios';

const API_BASE_URL = (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));

const getAuthHeaders = () => ({
  Authorization: `Bearer ${localStorage.getItem('token')}`,
});

// Feature 3: Contract Strategy Memory

export const buildStrategyMemory = async () => {
  const response = await axios.post(
    `${API_BASE_URL}/api/contract-suite/memory/build/`,
    {},
    { headers: getAuthHeaders() }
  );
  return response.data;
};

export const getMemoryInsights = async (clauseId) => {
  const response = await axios.get(
    `${API_BASE_URL}/api/contract-suite/memory/insights/`,
    {
      params: { clause_id: clauseId },
      headers: getAuthHeaders(),
    }
  );
  return response.data;
};

export const searchMemory = async (query, limit = 10) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/contract-suite/memory/search/`,
    { query, limit },
    { headers: getAuthHeaders() }
  );
  return response.data;
};

// Feature 6: Real-Time Contract Monitoring

export const createMonitorEvent = async ({ eventType, headline, contractIds = [] }) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/contract-suite/monitor/events/`,
    { event_type: eventType, headline, contract_ids: contractIds },
    { headers: getAuthHeaders() }
  );
  return response.data;
};

export const getMonitorAlerts = async (contractId = null) => {
  const params = contractId ? { contract_id: contractId } : {};
  const response = await axios.get(
    `${API_BASE_URL}/api/contract-suite/monitor/alerts/`,
    { params, headers: getAuthHeaders() }
  );
  return response.data;
};

export const scanForEvents = async () => {
  const response = await axios.post(
    `${API_BASE_URL}/api/contract-suite/monitor/scan/`,
    {},
    { headers: getAuthHeaders() }
  );
  return response.data;
};

// Feature 7: Self-Learning RL

export const recordOutcome = async ({ contractId, action, profit, dispute, delayDays, riskBucket, clauseCategory, region, supplierRiskScore }) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/contract-suite/rl/record/`,
    {
      contract_id: contractId,
      action,
      profit,
      dispute,
      delay_days: delayDays,
      risk_bucket: riskBucket || 'medium',
      clause_category: clauseCategory || 'general',
      region: region || 'global',
      supplier_risk_score: supplierRiskScore ?? 0.5,
    },
    { headers: getAuthHeaders() }
  );
  return response.data;
};

export const getRLRecommendation = async ({ riskBucket = 'medium', clauseCategory = 'general', region = 'global' } = {}) => {
  const response = await axios.get(
    `${API_BASE_URL}/api/contract-suite/rl/recommend/`,
    {
      params: { risk_bucket: riskBucket, clause_category: clauseCategory, region },
      headers: getAuthHeaders(),
    }
  );
  return response.data;
};

export const getRLExperiences = async () => {
  const response = await axios.get(
    `${API_BASE_URL}/api/contract-suite/rl/experiences/`,
    { headers: getAuthHeaders() }
  );
  return response.data;
};

export const getRLInsights = async () => {
  const response = await axios.get(
    `${API_BASE_URL}/api/contract-suite/rl/insights/`,
    { headers: getAuthHeaders() }
  );
  return response.data;
};

// RLHF: Expert Feedback
export const submitRLHFFeedback = async ({ actionType, rating, comment, expertName }) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/contract-suite/rl/feedback/`,
    { action_type: actionType, rating, comment, expert_name: expertName },
    { headers: getAuthHeaders() }
  );
  return response.data;
};

export const getRLHFFeedback = async () => {
  const response = await axios.get(
    `${API_BASE_URL}/api/contract-suite/rl/feedback/`,
    { headers: getAuthHeaders() }
  );
  return response.data;
};

// Industry Benchmarking
// params: { mode: 'portfolio'|'single'|'compare', contract_id?, compare_ids? }
export const getIndustryBenchmarking = async (params = {}) => {
  const qp = new URLSearchParams();
  if (params.mode) qp.set('mode', params.mode);
  if (params.contract_id) qp.set('contract_id', params.contract_id);
  if (params.compare_ids) qp.set('compare_ids', params.compare_ids);
  const query = qp.toString() ? `?${qp.toString()}` : '';
  const response = await axios.get(
    `${API_BASE_URL}/api/contract-suite/benchmarking/${query}`,
    { headers: getAuthHeaders() }
  );
  return response.data;
};

export const getBenchmarkingContracts = async () => {
  const response = await axios.get(
    `${API_BASE_URL}/api/contract-suite/benchmarking/contracts/`,
    { headers: getAuthHeaders() }
  );
  return response.data;
};

// These extract sub-fields from the unified benchmarking response
export const getBenchmarkingInsights = async (params = {}) => {
  const d = await getIndustryBenchmarking(params);
  return {
    insights: d.ai_insights || [],
    insight_count: d.insight_count || 0,
    portfolio_health: d.portfolio_health || 'unknown',
    health_score: d.health_score || 50,
    critical_issues: d.critical_issues || 0,
  };
};

export const getBenchmarkingClauses = async (params = {}) => {
  const d = await getIndustryBenchmarking(params);
  return {
    clauses: d.clause_benchmarks || [],
    total_clause_types_found: d.total_clause_types_found || 0,
    total_clause_types_missing: d.total_clause_types_missing || 0,
  };
};

export const getBenchmarkingRecommendations = async (params = {}) => {
  const d = await getIndustryBenchmarking(params);
  return {
    recommendations: d.recommendations || [],
    total_recommendations: d.total_recommendations || 0,
    critical_count: d.rec_critical_count || 0,
    high_count: d.rec_high_count || 0,
    estimated_risk_reduction: d.estimated_risk_reduction || '~0%',
  };
};

// Temporal Evolution
export const getTemporalEvolution = async () => {
  const response = await axios.get(
    `${API_BASE_URL}/api/contract-suite/memory/temporal/`,
    { headers: getAuthHeaders() }
  );
  return response.data;
};

// Dashboards
export const getRiskMarginFrontier = async () => {
  const response = await axios.get(
    `${API_BASE_URL}/api/contract-suite/dashboards/risk-margin/`,
    { headers: getAuthHeaders() }
  );
  return response.data;
};

export const getSupplierHeatmap = async () => {
  const response = await axios.get(
    `${API_BASE_URL}/api/contract-suite/dashboards/supplier-heatmap/`,
    { headers: getAuthHeaders() }
  );
  return response.data;
};

export const getDisputeTimeline = async () => {
  const response = await axios.get(
    `${API_BASE_URL}/api/contract-suite/dashboards/dispute-timeline/`,
    { headers: getAuthHeaders() }
  );
  return response.data;
};

// ERP Execution
export const getERPContracts = async () => {
  const response = await axios.get(
    `${API_BASE_URL}/api/erp/contracts/`,
    { headers: getAuthHeaders() }
  );
  return response.data;
};

export const triggerERPAction = async ({ contractId, triggerType, reason }) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/erp/auto-trigger/`,
    { contract_id: contractId, trigger_type: triggerType, reason },
    { headers: getAuthHeaders() }
  );
  return response.data;
};

export const getERPExecutionLog = async () => {
  const response = await axios.get(
    `${API_BASE_URL}/api/erp/execution-log/`,
    { headers: getAuthHeaders() }
  );
  return response.data;
};

export const bulkERPExecute = async ({ contractIds, action, reason }) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/erp/bulk-execute/`,
    { contract_ids: contractIds, action, reason },
    { headers: getAuthHeaders() }
  );
  return response.data;
};

// RL Train Model
export const trainRLModel = async () => {
  const response = await axios.post(
    `${API_BASE_URL}/api/contract-suite/rl/train/`,
    {},
    { headers: getAuthHeaders() }
  );
  return response.data;
};

// Clause Volatility Index
export const getClauseVolatility = async () => {
  const response = await axios.get(
    `${API_BASE_URL}/api/contract-suite/benchmarking/`,
    { headers: getAuthHeaders() }
  );
  // Volatility data is inside the benchmarking response
  return {
    clause_volatility: response.data.clause_volatility || [],
    total_clauses: response.data.user_stats?.total_clauses || 0,
    error: response.data.error || null,
  };
};

// Auto-Action Engine
export const triggerAutoAction = async ({ event_type, headline, contract_id, execute = false }) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/contract-suite/monitor/auto-action/`,
    { event_type, headline, contract_id, execute },
    { headers: getAuthHeaders() }
  );
  return response.data;
};

export const getAutoActionLog = async ({ contract_id, event_type } = {}) => {
  const params = {};
  if (contract_id) params.contract_id = contract_id;
  if (event_type) params.event_type = event_type;
  const response = await axios.get(
    `${API_BASE_URL}/api/contract-suite/monitor/auto-actions/`,
    { params, headers: getAuthHeaders() }
  );
  return response.data;
};

export const bulkAutoAction = async ({ event_type, headline }) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/contract-suite/monitor/auto-action/bulk/`,
    { event_type, headline },
    { headers: getAuthHeaders() }
  );
  return response.data;
};
