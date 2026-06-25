/**
 * Force Majeure Intelligence Engine — API Service
 * All calls go to http://localhost:8002/api/force-majeure/
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || `${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api`;
const FM_BASE = `${API_BASE_URL}/force-majeure`;

const authHeaders = () => ({
  headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
});

// ─── Core Prediction ──────────────────────────────────────────────────────────

/**
 * Run FM risk prediction for a contract.
 * @param {object} payload - { contract_text, contract_id, contract_title, contract_value, jurisdiction, industry, evidence }
 */
export const predictFMRisk = async (payload) => {
  const res = await axios.post(`${FM_BASE}/predict/`, payload, authHeaders());
  return res.data;
};

// ─── Clause Audit ─────────────────────────────────────────────────────────────

/**
 * Audit FM clause coverage in a contract.
 * @param {object} payload - { contract_text, contract_id, contract_title }
 */
export const auditFMClause = async (payload) => {
  const res = await axios.post(`${FM_BASE}/audit-clause/`, payload, authHeaders());
  return res.data;
};

/**
 * Auto-correct (rewrite) FM clause using LLM.
 * @param {object} payload - { contract_text, contract_id, use_llm }
 */
export const autoCorrectFMClause = async (payload) => {
  const res = await axios.post(`${FM_BASE}/auto-correct/`, payload, authHeaders());
  return res.data;
};

// ─── War Risk ─────────────────────────────────────────────────────────────────

/**
 * Analyze war & geopolitical risk for a contract.
 * @param {object} payload - { contract_text, contract_id, contract_title, contract_value, project_location, supplier_locations, war_events }
 */
export const analyzeWarRisk = async (payload) => {
  const res = await axios.post(`${FM_BASE}/war-risk/`, payload, authHeaders());
  return res.data;
};

// ─── Scenario Simulation ──────────────────────────────────────────────────────

/**
 * Run Monte Carlo scenario simulation.
 * @param {object} payload - { contract_id, contract_value, scenario_type, scenario_name, input_params, iterations, scenario_template }
 */
export const simulateFMScenario = async (payload) => {
  const res = await axios.post(`${FM_BASE}/simulate-scenario/`, payload, authHeaders());
  return res.data;
};

// ─── Bulk Portfolio Audit ─────────────────────────────────────────────────────

/**
 * Bulk audit all contracts in portfolio for FM clause coverage.
 * @param {object} payload - { contracts: [{contract_id, contract_title, contract_text}] }
 */
export const bulkAuditContracts = async (payload = {}) => {
  const res = await axios.post(`${FM_BASE}/bulk-audit/`, payload, authHeaders());
  return res.data;
};

// ─── Data Retrieval ───────────────────────────────────────────────────────────

/** List all FM predictions */
export const getFMPredictions = async () => {
  const res = await axios.get(`${FM_BASE}/predictions/`, authHeaders());
  return res.data;
};

/** Get FM prediction detail by ID */
export const getFMPredictionDetail = async (predictionId) => {
  const res = await axios.get(`${FM_BASE}/predictions/${predictionId}/`, authHeaders());
  return res.data;
};

/** List all FM clause audits */
export const getFMClauseAudits = async () => {
  const res = await axios.get(`${FM_BASE}/clause-audits/`, authHeaders());
  return res.data;
};

// ─── Alerts ───────────────────────────────────────────────────────────────────

/** List active global FM alerts */
export const getFMAlerts = async () => {
  const res = await axios.get(`${FM_BASE}/alerts/`, authHeaders());
  return res.data;
};

/** Create a new FM global alert */
export const createFMAlert = async (payload) => {
  const res = await axios.post(`${FM_BASE}/alerts/create/`, payload, authHeaders());
  return res.data;
};

// ─── Visualization ────────────────────────────────────────────────────────────

/**
 * Get Bayesian graph data for visualization.
 * @param {string} evidence - Optional: "war:0.8,sanctions:0.7"
 */
export const getFMBayesianGraph = async (evidence = '') => {
  const params = evidence ? `?evidence=${evidence}` : '';
  const res = await axios.get(`${FM_BASE}/bayesian-graph/${params}`, authHeaders());
  return res.data;
};

// ─── Portfolio ────────────────────────────────────────────────────────────────

/** Get portfolio-wide FM risk summary */
export const getFMPortfolioSummary = async () => {
  const res = await axios.get(`${FM_BASE}/portfolio-summary/`, authHeaders());
  return res.data;
};

// ─── Scenario Templates ──────────────────────────────────────────────────────

export const FM_SCENARIO_TEMPLATES = [
  {
    id: 'war_escalation',
    name: 'War Escalation',
    description: 'Active military conflict with sanctions, port closures, and energy disruption',
    icon: '⚔️',
    color: '#F16667',
    params: { war: 0.80, trade_sanctions: 0.70, energy_crisis: 0.65, political_coup: 0.40 },
  },
  {
    id: 'financial_crisis',
    name: 'Financial Crisis',
    description: 'Economic collapse with currency volatility and market crash',
    icon: '📉',
    color: '#F79767',
    params: { economic_collapse: 0.75, currency_volatility: 0.80, financial_market_crash: 0.70 },
  },
  {
    id: 'supply_chain',
    name: 'Supply Chain Collapse',
    description: 'Multi-tier supplier failure with port and transport shutdown',
    icon: '🔗',
    color: '#FFD86E',
    params: { supplier_failure: 0.70, port_closure: 0.65, transport_shutdown: 0.60 },
  },
  {
    id: 'commodity_shock',
    name: 'Commodity Shock',
    description: 'Extraordinary commodity price spike — steel, fuel, rare materials',
    icon: '📦',
    color: '#9063CD',
    params: { commodity_price_shock: 0.75, energy_price_spike: 0.70 },
  },
  {
    id: 'pandemic',
    name: 'Pandemic',
    description: 'Global public health emergency with lockdowns and labor shortage',
    icon: '🦠',
    color: '#4C8EDA',
    params: { pandemic: 0.80, labor_shortage: 0.70, factory_shutdown: 0.60 },
  },
  {
    id: 'cyber_attack',
    name: 'Cyber Attack',
    description: 'Coordinated cyber warfare targeting critical infrastructure',
    icon: '💻',
    color: '#06B6D4',
    params: { cyber_attack: 0.75, infrastructure_failure: 0.65 },
  },
  {
    id: 'climate_disaster',
    name: 'Climate Disaster',
    description: 'Extreme weather events causing widespread disruption',
    icon: '🌪️',
    color: '#10B981',
    params: { extreme_weather: 0.70, flooding: 0.65, wildfire: 0.50 },
  },
  {
    id: 'base_case',
    name: 'Base Case',
    description: 'Standard risk environment — no extraordinary events',
    icon: '📋',
    color: '#68BC00',
    params: {},
  },
];

// ─── Live Radar API calls ─────────────────────────────────────────────────────

/** Get all live FM events from GDELT + USGS + ReliefWeb + NewsAPI */
export const getLiveEvents = async (source = 'all', eventType = '', minRisk = 0) => {
  const params = new URLSearchParams();
  if (source !== 'all') params.append('source', source);
  if (eventType) params.append('event_type', eventType);
  if (minRisk > 0) params.append('min_risk', minRisk);
  const res = await axios.get(`${FM_BASE}/radar/live-events/?${params}`, authHeaders());
  return res.data;
};

/** Get geospatial risk map data */
export const getRiskMapData = async () => {
  const res = await axios.get(`${FM_BASE}/radar/risk-map/`, authHeaders());
  return res.data;
};

/** Get live FM exposure for a contract */
export const getContractLiveExposure = async (payload) => {
  const res = await axios.post(`${FM_BASE}/radar/contract-exposure/`, payload, authHeaders());
  return res.data;
};

/** Get Bloomberg-style event ticker */
export const getEventStream = async () => {
  const res = await axios.get(`${FM_BASE}/radar/event-stream/`, authHeaders());
  return res.data;
};

/** Get live war & geopolitical intelligence */
export const getWarIntelligence = async () => {
  const res = await axios.get(`${FM_BASE}/radar/war-intelligence/`, authHeaders());
  return res.data;
};

/** Get portfolio-wide FM alerts from live events */
export const getPortfolioAlerts = async () => {
  const res = await axios.get(`${FM_BASE}/radar/portfolio-alerts/`, authHeaders());
  return res.data;
};

export const FM_EVENT_CATEGORIES = [
  'war', 'terrorism', 'cyber_warfare', 'trade_sanctions', 'embargo',
  'pandemic', 'epidemic', 'government_lockdown', 'supply_chain_disruption',
  'port_closure', 'airspace_closure', 'energy_shortages', 'commodity_shock',
  'satellite_disruption',
];

// ─── Advanced Features ────────────────────────────────────────────────────────

/** Counterfactual Risk Engine */
export const runCounterfactual = async (payload) => {
  const res = await axios.post(`${FM_BASE}/counterfactual/`, payload, authHeaders());
  return res.data;
};

/** Portfolio-Wide FM Simulation */
export const simulatePortfolio = async (payload) => {
  const res = await axios.post(`${FM_BASE}/portfolio-simulate/`, payload, authHeaders());
  return res.data;
};

/** FM Knowledge Graph */
export const getFMKnowledgeGraph = async (focus = 'all', depth = 3) => {
  const res = await axios.get(`${FM_BASE}/knowledge-graph/?focus=${focus}&depth=${depth}`, authHeaders());
  return res.data;
};

/** Contract Digital Twin */
export const runDigitalTwin = async (payload) => {
  const res = await axios.post(`${FM_BASE}/digital-twin/`, payload, authHeaders());
  return res.data;
};

/** Multi-Agent Clause Negotiation */
export const runMultiAgentNegotiate = async (payload) => {
  const res = await axios.post(`${FM_BASE}/multi-agent-negotiate/`, payload, authHeaders());
  return res.data;
};

/** Supply Chain Risk Map — contract-aware */
export const getSupplyChainMap = async (contractData = {}) => {
  const res = await axios.post(`${FM_BASE}/supply-chain-map/`, contractData, authHeaders());
  return res.data;
};

// ─── Phase-2 New Features ─────────────────────────────────────────────────────

/** Dynamic Bayesian Prior Update from live events */
export const getDynamicPriors = async () => {
  const res = await axios.get(`${FM_BASE}/dynamic-priors/`, authHeaders());
  return res.data;
};

/** 4-Stage Risk Cascade (React Flow graph) */
export const getRiskCascade = async (evidence, contractValue = 1000000) => {
  const res = await axios.post(`${FM_BASE}/risk-cascade/`, { evidence, contract_value: contractValue }, authHeaders());
  return res.data;
};

/** Counterfactual Clause Optimizer — tests protective clause additions */
export const runClauseOptimizer = async (evidence, contractValue = 1000000) => {
  const res = await axios.post(`${FM_BASE}/clause-optimizer/`, { evidence, contract_value: contractValue }, authHeaders());
  return res.data;
};

/** Temporal DBN 12-Month Forecast */
export const getTemporalForecast = async (evidence, startMonth = 1) => {
  const res = await axios.post(`${FM_BASE}/temporal-forecast/`, { evidence, start_month: startMonth }, authHeaders());
  return res.data;
};

/** Risk Formula Breakdown with per-event sensitivity */
export const getRiskFormula = async (evidence) => {
  const res = await axios.post(`${FM_BASE}/risk-formula/`, { evidence }, authHeaders());
  return res.data;
};

/** Real-Time Alert Engine — live events vs contracts */
export const getAlertEngine = async () => {
  const res = await axios.get(`${FM_BASE}/alert-engine/`, authHeaders());
  return res.data;
};

/** Baltic Dry Index with FM signal */
export const getBalticDry = async () => {
  const res = await axios.get(`${FM_BASE}/radar/baltic-dry/`, authHeaders());
  return res.data;
};

/** Bulk Clause Auto-Correct Grid */
export const bulkAutoCorrect = async (clauses) => {
  const res = await axios.post(`${FM_BASE}/bulk-auto-correct/`, { clauses }, authHeaders());
  return res.data;
};

// ─── NEW ADVANCED FEATURES ────────────────────────────────────────────────────

// ═══ LLM CLAUSE REWRITING ═══

/**
 * Rewrite weak FM clause using LLM (GPT-4)
 * @param {object} payload - { existing_clause, missing_events, weak_events, contract_value, jurisdiction }
 */
export const llmRewriteClause = async (payload) => {
  const res = await axios.post(`${FM_BASE}/llm-clause-rewrite/`, payload, authHeaders());
  return res.data;
};

/**
 * Generate new FM clause from scratch using LLM
 * @param {object} payload - { missing_events, contract_value, jurisdiction, industry_standard }
 */
export const llmGenerateClause = async (payload) => {
  const res = await axios.post(`${FM_BASE}/llm-generate-clause/`, payload, authHeaders());
  return res.data;
};

// ═══ WAR SUPPLY CHAIN ANALYSIS ═══

/**
 * Analyze war impact on contract supply chains
 * @param {object} payload - { war_event, dependencies, region, severity }
 */
export const analyzeWarSupplyChain = async (payload) => {
  const res = await axios.post(`${FM_BASE}/war-supply-chain/`, payload, authHeaders());
  return res.data;
};

/**
 * Simulate closure of critical shipping route
 * @param {object} payload - { route_id, closure_duration_days }
 */
export const simulateRouteClosure = async (payload) => {
  const res = await axios.post(`${FM_BASE}/route-closure/`, payload, authHeaders());
  return res.data;
};

// ═══ WAR LOSS PREDICTION ═══

/**
 * Predict financial losses from war events
 * @param {object} payload - { contract_value, war_event, duration_estimate_days, workforce_size, equipment_count, project_phase, location_risk }
 */
export const predictWarLoss = async (payload) => {
  const res = await axios.post(`${FM_BASE}/war-loss-prediction/`, payload, authHeaders());
  return res.data;
};

/**
 * Calculate war risk insurance premium
 * @param {object} payload - { contract_value, location_risk, war_probability, coverage_percentage }
 */
export const calculateWarInsurance = async (payload) => {
  const res = await axios.post(`${FM_BASE}/war-insurance-premium/`, payload, authHeaders());
  return res.data;
};

// ═══ ADVANCED DATA SOURCES ═══

/**
 * Get real-time shipping disruptions
 * @param {string} region - 'global' | 'asia' | 'europe' | 'middle_east'
 */
export const getShippingDisruptions = async (region = 'global') => {
  const res = await axios.get(`${FM_BASE}/shipping-disruptions/?region=${region}`, authHeaders());
  return res.data;
};

/**
 * Get commodity prices and shock probabilities
 * @param {string} commodities - comma-separated list: 'oil,gas,steel,copper'
 */
export const getCommodityPrices = async (commodities = 'oil,gas,steel,copper') => {
  const res = await axios.get(`${FM_BASE}/commodity-prices/?commodities=${commodities}`, authHeaders());
  return res.data;
};

/**
 * Check entity against sanctions lists
 * @param {object} payload - { entity_name, country }
 */
export const checkSanctions = async (payload) => {
  const res = await axios.post(`${FM_BASE}/sanctions-check/`, payload, authHeaders());
  return res.data;
};

/**
 * Get political risk index for country
 * @param {string} country - Country name
 */
export const getPoliticalRisk = async (country) => {
  const res = await axios.get(`${FM_BASE}/political-risk/?country=${country}`, authHeaders());
  return res.data;
};

/**
 * Get labor strike probability
 * @param {string} industry - Industry name
 * @param {string} region - Region name
 */
export const getLaborStrikeRisk = async (industry = 'construction', region = 'Global') => {
  const res = await axios.get(`${FM_BASE}/labor-strike-risk/?industry=${industry}&region=${region}`, authHeaders());
  return res.data;
};

// ═══ GEOPOLITICAL INFERENCE ═══

/**
 * Analyze geopolitical risks for project
 * @param {object} payload - { region, project_location, supply_chain_locations, time_horizon_days }
 */
export const analyzeGeopoliticalRisk = async (payload) => {
  const res = await axios.post(`${FM_BASE}/geopolitical-risk/`, payload, authHeaders());
  return res.data;
};

/**
 * Predict conflict escalation probability
 * @param {object} payload - { current_events, region, days_ahead }
 */
export const predictConflictEscalation = async (payload) => {
  const res = await axios.post(`${FM_BASE}/conflict-escalation/`, payload, authHeaders());
  return res.data;
};

/**
 * Assess diplomatic stability between countries
 * @param {object} payload - { countries, include_alliances }
 */
export const assessDiplomaticStability = async (payload) => {
  const res = await axios.post(`${FM_BASE}/diplomatic-stability/`, payload, authHeaders());
  return res.data;
};

// ═══ PORTFOLIO RISK SIMULATOR ═══

/**
 * Simulate correlated FM risks across portfolio
 * @param {object} payload - { contracts, n_simulations, confidence_level }
 */
export const simulatePortfolioRisk = async (payload) => {
  const res = await axios.post(`${FM_BASE}/portfolio-simulator/`, payload, authHeaders());
  return res.data;
};

// ═══════════════════════════════════════════════════════════════════════════════
// PHASE 4: ADVANCED ENGINES
// ═══════════════════════════════════════════════════════════════════════════════

// ═══ DYNAMIC BAYESIAN NETWORK (TEMPORAL) ═══

/**
 * Forecast FM risk evolution over time using Dynamic Bayesian Network
 * @param {object} payload - { initial_evidence, time_steps, time_unit, target_outcomes }
 * @returns {Promise} Temporal risk forecast with trajectories
 */
export const forecastTemporalRisk = async (payload) => {
  const res = await axios.post(`${FM_BASE}/temporal-forecast-advanced/`, payload, authHeaders());
  return res.data;
};

/**
 * Compare risk trajectories across multiple scenarios over time
 * @param {object} payload - { baseline_evidence, alternative_scenarios, time_steps }
 * @returns {Promise} Scenario comparison with best scenario identification
 */
export const compareRiskScenarios = async (payload) => {
  const res = await axios.post(`${FM_BASE}/scenario-comparison/`, payload, authHeaders());
  return res.data;
};

// ═══ CONTRACT DIGITAL TWIN ═══

/**
 * Create a digital twin for a contract
 * @param {object} payload - { contract_id, contract_data }
 * @returns {Promise} Created twin_id and status
 */
export const createContractTwin = async (payload) => {
  const res = await axios.post(`${FM_BASE}/digital-twin/create/`, payload, authHeaders());
  return res.data;
};

/**
 * Simulate FM scenario on contract digital twin
 * @param {object} payload - { twin_id, fm_scenario, simulation_params }
 * @returns {Promise} Simulation results with Monte Carlo analysis
 */
export const simulateDigitalTwin = async (payload) => {
  const res = await axios.post(`${FM_BASE}/digital-twin/simulate/`, payload, authHeaders());
  return res.data;
};

/**
 * Get current status of digital twin
 * @param {string} twinId - Digital twin identifier
 * @returns {Promise} Current twin state and health status
 */
export const getDigitalTwinStatus = async (twinId) => {
  const res = await axios.get(`${FM_BASE}/digital-twin/status/${twinId}/`, authHeaders());
  return res.data;
};

/**
 * Compare multiple FM scenarios on same digital twin
 * @param {object} payload - { twin_id, scenarios }
 * @returns {Promise} Comparative analysis of scenarios
 */
export const compareDigitalTwinScenarios = async (payload) => {
  const res = await axios.post(`${FM_BASE}/digital-twin/compare-scenarios/`, payload, authHeaders());
  return res.data;
};

// ═══ ENHANCED COUNTERFACTUAL (DO-CALCULUS) ═══

/**
 * Perform do-operator intervention analysis (causal inference)
 * @param {object} payload - { intervention, target_outcomes, background_evidence }
 * @returns {Promise} Causal effects of intervention
 */
export const performDoIntervention = async (payload) => {
  const res = await axios.post(`${FM_BASE}/do-intervention/`, payload, authHeaders());
  return res.data;
};

/**
 * Perform counterfactual reasoning: "What if X had been different?"
 * @param {object} payload - { factual_world, counterfactual_intervention, target_outcome }
 * @returns {Promise} Counterfactual analysis with interpretation
 */
export const counterfactualQuery = async (payload) => {
  const res = await axios.post(`${FM_BASE}/counterfactual-query/`, payload, authHeaders());
  return res.data;
};

/**
 * Estimate average causal effect of treatment on outcome
 * @param {object} payload - { treatment, outcome, adjustment_set }
 * @returns {Promise} Average Treatment Effect (ATE)
 */
export const estimateCausalEffect = async (payload) => {
  const res = await axios.post(`${FM_BASE}/causal-effect/`, payload, authHeaders());
  return res.data;
};

/**
 * Perform sensitivity analysis to unmeasured confounding
 * @param {object} payload - { intervention, target_outcome, unmeasured_confounder_strength }
 * @returns {Promise} Sensitivity analysis results
 */
export const performSensitivityAnalysis = async (payload) => {
  const res = await axios.post(`${FM_BASE}/sensitivity-analysis/`, payload, authHeaders());
  return res.data;
};

// ═══ CLAUSE OPTIMIZATION ═══

/**
 * Multi-objective optimization for FM clause improvement
 * @param {object} payload - { current_clause, optimization_objectives, constraints, party_preferences }
 * @returns {Promise} Optimized clause with improvement metrics
 */
export const optimizeFMClause = async (payload) => {
  const res = await axios.post(`${FM_BASE}/clause-optimize/`, payload, authHeaders());
  return res.data;
};

/**
 * Optimize clause balancing multiple party interests
 * @param {object} payload - { current_clause, buyer_preferences, seller_preferences, neutral_arbitrator }
 * @returns {Promise} Balanced optimized clause with fairness analysis
 */
export const multiPartyOptimize = async (payload) => {
  const res = await axios.post(`${FM_BASE}/multi-party-optimize/`, payload, authHeaders());
  return res.data;
};

// ═══════════════════════════════════════════════════════════════════════════════
// APPROVAL WORKFLOWS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Create approval request for clause change
 * @param {object} payload - { contract_id, contract_name, change_type, original_clause, proposed_clause, change_justification, risk_reduction, improvement_score }
 * @returns {Promise} Created approval request with request_id
 */
export const createApprovalRequest = async (payload) => {
  const res = await axios.post(`${FM_BASE}/approval/create/`, payload, authHeaders());
  return res.data;
};

/**
 * Approve an approval step
 * @param {object} payload - { request_id, comments }
 * @returns {Promise} Approval result with next approver info
 */
export const approveApprovalRequest = async (payload) => {
  const res = await axios.post(`${FM_BASE}/approval/approve/`, payload, authHeaders());
  return res.data;
};

/**
 * Reject an approval request
 * @param {object} payload - { request_id, reason }
 * @returns {Promise} Rejection confirmation
 */
export const rejectApprovalRequest = async (payload) => {
  const res = await axios.post(`${FM_BASE}/approval/reject/`, payload, authHeaders());
  return res.data;
};

/**
 * Get approval request status
 * @param {string} requestId - Approval request ID
 * @returns {Promise} Complete approval request status with chain and audit trail
 */
export const getApprovalStatus = async (requestId) => {
  const res = await axios.get(`${FM_BASE}/approval/status/${requestId}/`, authHeaders());
  return res.data;
};

/**
 * Get pending approvals for current user
 * @returns {Promise} List of pending approval requests
 */
export const getPendingApprovals = async () => {
  const res = await axios.get(`${FM_BASE}/approval/pending/`, authHeaders());
  return res.data;
};
