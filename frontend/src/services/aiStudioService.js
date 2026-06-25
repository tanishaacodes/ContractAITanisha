import axios from 'axios';

const API_BASE_URL = (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));

const getAuthHeaders = () => ({
  Authorization: `Bearer ${localStorage.getItem('token')}`,
});

// Feature 1: Autonomous Redlining AI

export const generateRedlines = async (contractId, jurisdiction = 'india') => {
  const response = await axios.post(
    `${API_BASE_URL}/api/ai-studio/redline/`,
    { contract_id: contractId, jurisdiction },
    { headers: getAuthHeaders() }
  );
  return response.data;
};

export const acceptRedline = async (redlineId, redlineStatus) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/ai-studio/redline/accept/`,
    { redline_id: redlineId, status: redlineStatus },
    { headers: getAuthHeaders() }
  );
  return response.data;
};

// Feature 2: Negotiation Agents (basic)

export const startNegotiation = async (contractId, clauseText, rounds = 3) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/ai-studio/negotiate/`,
    { contract_id: contractId, clause_text: clauseText, rounds },
    { headers: getAuthHeaders() }
  );
  return response.data;
};

// Feature 2b: Advanced Multi-Agent Negotiation Engine

export const startAdvancedNegotiation = async ({
  clauseText,
  contractId = null,
  rounds = 3,
  riskWeight = 0.30,
  financialWeight = 0.35,
  complianceWeight = 0.20,
  balanceWeight = 0.15,
}) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/ai-studio/negotiate-advanced/`,
    {
      clause_text:       clauseText,
      contract_id:       contractId,
      rounds,
      risk_weight:       riskWeight,
      financial_weight:  financialWeight,
      compliance_weight: complianceWeight,
      balance_weight:    balanceWeight,
    },
    { headers: getAuthHeaders() }
  );
  return response.data;
};

export const getNegotiationHistory = async (contractId = null, limit = 20, offset = 0) => {
  const params = { limit, offset };
  if (contractId) params.contract_id = contractId;
  const response = await axios.get(
    `${API_BASE_URL}/api/ai-studio/negotiation-history/`,
    { params, headers: getAuthHeaders() }
  );
  return response.data;
};

export const evaluateNegotiationOutcome = async ({
  sessionId,
  dealOutcome,
  profitMargin = 0,
  delayDays = 0,
  disputeCount = 0,
}) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/ai-studio/evaluate-outcome/`,
    {
      session_id:    sessionId,
      deal_outcome:  dealOutcome,
      profit_margin: profitMargin,
      delay_days:    delayDays,
      dispute_count: disputeCount,
    },
    { headers: getAuthHeaders() }
  );
  return response.data;
};

// Feature 4: CFO Simulator

export const runCFOSimulation = async ({ contractId, oilShock, inflation, fxRate, simulations = 1000 }) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/ai-studio/cfo-simulate/`,
    {
      contract_id: contractId,
      oil_shock: oilShock,
      inflation: inflation,
      fx_rate: fxRate,
      simulations,
    },
    { headers: getAuthHeaders() }
  );
  return response.data;
};

// Feature 4b: Contract-Aware CFO Engine (Advanced)

export const simulateContract = async ({
  contractId, contractValue, durationMonths, paymentTermsDays,
  penaltyRateDaily, maxPenaltyCap, costBaseRatio, delayProbability,
  avgDelayDays, currency, oilShock, inflation, fxShock, simulations = 2000,
}) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/ai-studio/simulate-contract/`,
    {
      contract_id: contractId,
      contract_value: contractValue,
      duration_months: durationMonths,
      payment_terms_days: paymentTermsDays,
      penalty_rate_daily: penaltyRateDaily,
      max_penalty_cap: maxPenaltyCap,
      cost_base_ratio: costBaseRatio,
      delay_probability: delayProbability,
      avg_delay_days: avgDelayDays,
      currency,
      oil_shock: oilShock,
      inflation,
      fx_shock: fxShock,
      simulations,
    },
    { headers: getAuthHeaders() }
  );
  return response.data;
};

export const getRiskInsights = async ({
  contractId, contractValue, durationMonths, costBaseRatio, delayProbability,
  oilShock, inflation, fxShock,
}) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/ai-studio/risk-insights/`,
    {
      contract_id: contractId,
      contract_value: contractValue,
      duration_months: durationMonths,
      cost_base_ratio: costBaseRatio,
      delay_probability: delayProbability,
      oil_shock: oilShock,
      inflation,
      fx_shock: fxShock,
    },
    { headers: getAuthHeaders() }
  );
  return response.data;
};

export const runScenarioAnalysis = async ({ contractId, contractValue, durationMonths, costBaseRatio }) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/ai-studio/scenario-analysis/`,
    {
      contract_id: contractId,
      contract_value: contractValue,
      duration_months: durationMonths,
      cost_base_ratio: costBaseRatio,
    },
    { headers: getAuthHeaders() }
  );
  return response.data;
};

// Feature 5: Legal Reasoning Engine

export const analyzeLegalClause = async (clauseText, jurisdiction = 'india') => {
  const response = await axios.post(
    `${API_BASE_URL}/api/ai-studio/legal-analyze/`,
    { clause_text: clauseText, jurisdiction },
    { headers: getAuthHeaders() }
  );
  return response.data;
};

// Fetch contracts list (reuse existing endpoint)
export const fetchContracts = async () => {
  const response = await axios.get(
    `${API_BASE_URL}/api/contracts/list/`,
    { headers: getAuthHeaders() }
  );
  return response.data;
};

// ── Contract Intelligence Orchestrator (primary, contract-first) ─────────────

/**
 * analyzeContract – calls POST /api/analyze-contract/
 *
 * Accepts one of:
 *   contractId  – existing contract UUID in the DB
 *   document    – File object (uploaded .txt / .pdf)
 *   rawText     – pasted contract text
 *
 * Results are persisted to the database automatically.
 */
export const analyzeContract = async ({
  contractId = null,
  document = null,
  rawText = null,
  jurisdiction = 'india',
  contractValue = 100000,
  durationMonths = 12,
  clauses = null,
}) => {
  // Use FormData so we can attach a file if provided
  const form = new FormData();
  if (contractId)     form.append('contract_id',     contractId);
  if (document)       form.append('document',         document);
  if (rawText)        form.append('raw_text',          rawText);
  if (clauses)        form.append('clauses',           JSON.stringify(clauses));
  form.append('jurisdiction',    jurisdiction);
  form.append('contract_value',  String(contractValue));
  form.append('duration_months', String(durationMonths));

  const response = await axios.post(
    `${API_BASE_URL}/api/analyze-contract/`,
    form,
    {
      headers: {
        ...getAuthHeaders(),
        // Let axios set the correct multipart boundary automatically
      },
    }
  );
  return response.data;
};

/**
 * getStoredAnalysis – retrieve a persisted analysis result by ID.
 */
export const getStoredAnalysis = async (analysisId) => {
  const response = await axios.get(
    `${API_BASE_URL}/api/analyze-contract/${analysisId}/`,
    { headers: getAuthHeaders() }
  );
  return response.data;
};

/**
 * getContractLatestAnalysis – get the most recent analysis for a contract.
 * Used by Benchmarking, Volatility, Risk vs Margin and other modules.
 */
export const getContractLatestAnalysis = async (contractId) => {
  const response = await axios.get(
    `${API_BASE_URL}/api/analyze-contract/contract/${contractId}/latest/`,
    { headers: getAuthHeaders() }
  );
  return response.data;
};

// ── Contract Intelligence Orchestrator (legacy) ───────────────────────────────

export const runFullAnalysis = async ({
  contractId = null,
  jurisdiction = 'india',
  contractValue = 100000,
  durationMonths = 12,
  clauses = null,
  rawText = null,
}) => {
  const response = await axios.post(
    `${API_BASE_URL}/api/ai-studio/full-analysis/`,
    {
      contract_id:     contractId,
      jurisdiction,
      contract_value:  contractValue,
      duration_months: durationMonths,
      clauses:         clauses || undefined,
      raw_text:        rawText || undefined,
    },
    { headers: getAuthHeaders() }
  );
  return response.data;
};

export const getAnalysisResult = async (analysisId) => {
  const response = await axios.get(
    `${API_BASE_URL}/api/ai-studio/analysis-result/${analysisId}/`,
    { headers: getAuthHeaders() }
  );
  return response.data;
};
