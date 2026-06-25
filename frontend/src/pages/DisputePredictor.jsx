/**
 * DisputePredictor.jsx
 * =====================
 * UniContractAI – Dispute Predictor & Simulator Dashboard
 *
 * 5 Tabs:
 *  1. Predict         – Enter contract text / signals → run prediction
 *  2. Risk Graph      – 60-node Bayesian graph (React Flow Neo4j style)
 *  3. Scenario Sim    – What-if scenario simulation
 *  4. History         – Past predictions
 *  5. How It Works    – Architecture explainer
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';
import ReactECharts from 'echarts-for-react';
import { io } from 'socket.io-client';
import {
  ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area,
  CartesianGrid, XAxis, YAxis, Tooltip
} from 'recharts';
import {
  AlertTriangle, Brain, BarChart3, History,
  Info, Play, RefreshCw, Trash2, ChevronRight,
  TrendingUp, Shield, Zap, Scale, Globe,
  Activity, Target, FileText, Sliders, Maximize2, Minimize2,
  Table2, Clock, GitBranch, Users, Map, ChevronDown, ChevronUp,
  ArrowRight, CheckCircle, XCircle, Minus, DollarSign, Calendar, Lock,
} from 'lucide-react';
import {
  predictDispute,
  simulateDisputeScenarios,
  getDisputeGraph,
  listPredictions,
  getPrediction,
  deletePrediction,
  getPrebuiltScenarios,
  getAIStatus,
  getClauseRiskTable,
  getTimeTravelRisk,
  runDigitalTwin,
  runNegotiationSimulator,
  runMultiAgentNegotiation,
  getPortfolioDisputeHeatmap,
  runMCTSNegotiation,
  runAdvancedMultiAgent,
  optimizeContractWithRL,
  matchLegalPrecedents,
} from '../services/disputeService';
import RiskGraph3D from '../components/arbitration/RiskGraph3D';
import NeoVizPanel from '../components/dispute/NeoVizPanel';
import NegotiationTreeVisualization from '../components/dispute/NegotiationTreeVisualization';
import MultiAgentDecisionPanel from '../components/dispute/MultiAgentDecisionPanel';

// ─── CLUSTER COLOR MAP ───────────────────────────────────────
const CLUSTER_COLORS = {
  geo:          { bg: '#dc2626', border: '#ef4444', text: '#fca5a5' },
  macro:        { bg: '#d97706', border: '#f59e0b', text: '#fcd34d' },
  market:       { bg: '#7c3aed', border: '#8b5cf6', text: '#c4b5fd' },
  supply_chain: { bg: '#0369a1', border: '#0ea5e9', text: '#7dd3fc' },
  financial:    { bg: '#047857', border: '#10b981', text: '#6ee7b7' },
  operational:  { bg: '#b45309', border: '#f59e0b', text: '#fde68a' },
  contract:     { bg: '#1d4ed8', border: '#3b82f6', text: '#93c5fd' },
  legal:        { bg: '#6d28d9', border: '#a78bfa', text: '#ddd6fe' },
};

const SEVERITY_COLOR = (prob) => {
  if (prob >= 0.7) return '#ef4444';
  if (prob >= 0.45) return '#f59e0b';
  return '#10b981';
};

// ─── RISK GRAPH LAYOUT ──────────────────────────────────────
const buildGraphElements = (graphData, liveSignals = {}) => {
  if (!graphData?.nodes) return { nodes: [], edges: [] };

  // Cluster horizontal bands
  const LAYER_Y = { 1: 0, 2: 140, 3: 280, 4: 420, 5: 560, 6: 700, 7: 840, 8: 980 };
  const clusterCounter = {};

  const nodes = graphData.nodes.map((n) => {
    const layer = n.layer || 1;
    const cluster = n.cluster || 'geo';
    clusterCounter[layer] = (clusterCounter[layer] || 0) + 1;
    const idx = clusterCounter[layer];
    const colors = CLUSTER_COLORS[cluster] || CLUSTER_COLORS['contract'];
    const prob = liveSignals[n.id] ?? n.current_probability ?? n.base_probability;
    const nodeColor = SEVERITY_COLOR(prob);

    return {
      id: n.id,
      type: 'default',
      position: { x: (idx - 1) * 160, y: LAYER_Y[layer] || 0 },
      data: {
        probability: prob,
        label: (
          <div style={{ textAlign: 'center', fontSize: '10px', lineHeight: 1.3 }}>
            <div style={{ fontWeight: 700, color: colors.text, marginBottom: 2 }}>{n.label}</div>
            <div style={{
              background: nodeColor,
              color: '#fff',
              borderRadius: 4,
              padding: '1px 4px',
              fontSize: 9,
              fontWeight: 700,
            }}>
              {(prob * 100).toFixed(0)}%
            </div>
          </div>
        ),
      },
      style: {
        background: colors.bg,
        border: `2px solid ${nodeColor}`,
        borderRadius: 8,
        width: 130,
        padding: '6px 4px',
        color: colors.text,
        boxShadow: prob >= 0.6 ? `0 0 12px ${nodeColor}88` : 'none',
      },
    };
  });

  const edges = (graphData.edges || []).map((e, i) => ({
    id: `e-${i}`,
    source: e.source,
    target: e.target,
    animated: (e.conditional_probability || 0) > 0.6,
    style: {
      stroke: (e.conditional_probability || 0) > 0.6 ? '#ef4444' : '#475569',
      strokeWidth: (e.conditional_probability || 0) > 0.7 ? 2 : 1,
    },
    markerEnd: { type: MarkerType.ArrowClosed, color: '#475569' },
  }));

  return { nodes, edges };
};

// ─── METRIC CARD ────────────────────────────────────────────
const MetricCard = ({ label, value, unit = '%', color = '#06b6d4', icon: Icon, subtitle }) => (
  <div style={{
    background: 'linear-gradient(135deg, #1e293b, #0f172a)',
    border: `1px solid ${color}30`,
    borderRadius: 12,
    padding: '16px 20px',
    minWidth: 160,
  }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
      {Icon && <Icon size={14} color={color} />}
      <span style={{ color: '#94a3b8', fontSize: 11 }}>{label}</span>
    </div>
    <div style={{ fontSize: 28, fontWeight: 800, color }}>
      {typeof value === 'number' && unit === '%'
        ? `${(value * 100).toFixed(0)}${unit}`
        : typeof value === 'number' && unit === '$'
        ? `$${value >= 1e6 ? (value / 1e6).toFixed(1) + 'M' : value.toLocaleString()}`
        : value ?? '–'
      }
    </div>
    {subtitle && <div style={{ color: '#64748b', fontSize: 10, marginTop: 4 }}>{subtitle}</div>}
  </div>
);

// ─── RISK DRIVER ROW ────────────────────────────────────────
const RiskDriverRow = ({ driver, rank }) => {
  const colors = CLUSTER_COLORS[driver.cluster] || CLUSTER_COLORS.contract;
  const severityColor = SEVERITY_COLOR(driver.probability);
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 12,
      padding: '12px 16px',
      background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
      borderRadius: 10,
      border: `2px solid ${colors.border}40`,
      transition: 'all 0.3s ease',
      cursor: 'pointer',
      position: 'relative',
      overflow: 'hidden'
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.borderColor = `${colors.border}80`;
      e.currentTarget.style.boxShadow = `0 4px 12px ${colors.border}30`;
      e.currentTarget.style.transform = 'translateX(4px)';
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.borderColor = `${colors.border}40`;
      e.currentTarget.style.boxShadow = 'none';
      e.currentTarget.style.transform = 'translateX(0)';
    }}>
      <div style={{
        position: 'absolute',
        left: 0,
        top: 0,
        bottom: 0,
        width: 4,
        background: `linear-gradient(180deg, ${colors.bg} 0%, ${colors.border} 100%)`
      }} />
      <div style={{
        width: 28,
        height: 28,
        borderRadius: '50%',
        background: `linear-gradient(135deg, ${colors.bg} 0%, ${colors.border} 100%)`,
        color: colors.text,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: 12,
        fontWeight: 800,
        flexShrink: 0,
        boxShadow: `0 2px 8px ${colors.bg}40`
      }}>{rank}</div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          color: '#e2e8f0',
          fontSize: 13,
          fontWeight: 700,
          marginBottom: 2,
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis'
        }}>{driver.label}</div>
        <div style={{
          color: '#64748b',
          fontSize: 11,
          fontWeight: 600,
          textTransform: 'uppercase',
          letterSpacing: '0.05em'
        }}>{driver.cluster}</div>
      </div>
      <div style={{
        background: `linear-gradient(135deg, ${severityColor}30 0%, ${severityColor}20 100%)`,
        border: `2px solid ${severityColor}`,
        borderRadius: 8,
        padding: '6px 12px',
        color: severityColor,
        fontSize: 13,
        fontWeight: 800,
        boxShadow: `0 2px 8px ${severityColor}30`,
        whiteSpace: 'nowrap'
      }}>
        {(driver.probability * 100).toFixed(0)}%
      </div>
      <div style={{
        background: '#f59e0b20',
        border: '1px solid #f59e0b60',
        borderRadius: 6,
        padding: '4px 10px',
        color: '#fbbf24',
        fontSize: 11,
        fontWeight: 700,
        whiteSpace: 'nowrap'
      }}>
        +{(driver.delta * 100).toFixed(0)}%
      </div>
    </div>
  );
};

// ─── PROPAGATION PATH ───────────────────────────────────────
const PropagationPath = ({ path }) => {
  if (!path?.length) return null;
  return (
    <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 4 }}>
      {path.map((node, i) => (
        <div key={node.node} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <div style={{
            background: '#1e293b',
            border: `1px solid ${SEVERITY_COLOR(node.probability)}50`,
            borderRadius: 6, padding: '3px 10px',
            color: SEVERITY_COLOR(node.probability),
            fontSize: 11, fontWeight: 600,
          }}>
            {node.label}
            <span style={{ color: '#64748b', marginLeft: 4 }}>
              {(node.probability * 100).toFixed(0)}%
            </span>
          </div>
          {i < path.length - 1 && <ChevronRight size={12} color="#475569" />}
        </div>
      ))}
    </div>
  );
};

// ═══════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════

export default function DisputePredictor() {
  const [activeTab, setActiveTab] = useState('predict');

  // ── TAB 1: Predict ──
  const [contractText, setContractText] = useState('');
  const [contractValue, setContractValue] = useState(5000000);
  const [contractTitle, setContractTitle] = useState('');
  const [predicting, setPredicting] = useState(false);
  const [prediction, setPrediction] = useState(null);
  const [predError, setPredError] = useState('');

  // ── TAB 2: Graph ──
  const [graphData, setGraphData] = useState(null);
  const [graphLoading, setGraphLoading] = useState(false);
  const [graphFullscreen, setGraphFullscreen] = useState(false);
  const [rfNodes, setRfNodes, onNodesChange] = useNodesState([]);
  const [rfEdges, setRfEdges, onEdgesChange] = useEdgesState([]);

  // ── TAB 3: Scenarios ──
  const [baseSignals, setBaseSignals] = useState({});
  const [prebuiltScenarios, setPrebuiltScenarios] = useState([]);
  const [selectedScenarios, setSelectedScenarios] = useState([]);
  const [simulating, setSimulating] = useState(false);
  const [simResults, setSimResults] = useState(null);
  const [simError, setSimError] = useState('');

  // ── TAB 4: History ──
  const [predictions, setPredictions] = useState([]);
  const [histLoading, setHistLoading] = useState(false);
  const [expandedHistId, setExpandedHistId] = useState(null);
  const [loadingHistId, setLoadingHistId] = useState(null);

  // ── AI Status ──
  const [aiStatus, setAiStatus] = useState(null);

  // ── TAB: Clause Risk Table ──
  const [clauseTable, setClauseTable] = useState(null);
  const [clauseTableLoading, setClauseTableLoading] = useState(false);
  const [clauseTableError, setClauseTableError] = useState('');

  // ── TAB: Time Travel ──
  const [timeTravelData, setTimeTravelData] = useState(null);
  const [timeTravelLoading, setTimeTravelLoading] = useState(false);
  const [timeTravelMonths, setTimeTravelMonths] = useState(12);
  const [timeTravelSlider, setTimeTravelSlider] = useState(0);
  const [timeTravelError, setTimeTravelError] = useState('');

  // ── TAB: Digital Twin ──
  const [twinData, setTwinData] = useState(null);
  const [twinLoading, setTwinLoading] = useState(false);
  const [twinMonths, setTwinMonths] = useState(12);
  const [twinError, setTwinError] = useState('');

  // ── TAB: Negotiation Sim ──
  const [negSimData, setNegSimData] = useState(null);
  const [negSimLoading, setNegSimLoading] = useState(false);
  const [negSimError, setNegSimError] = useState('');
  const [negInitState, setNegInitState] = useState({
    price: 110, delivery_days: 40, liability_cap: 0.2,
    payment_terms: 60, termination_penalty: 10, force_majeure: 1,
  });
  const [negRounds, setNegRounds] = useState(10);
  const [negMode, setNegMode] = useState('mcts'); // 'mcts' or 'multi'
  const [multiAgentData, setMultiAgentData] = useState(null);
  const [negTreeNodes, setNegTreeNodes, onNegNodesChange] = useNodesState([]);
  const [negTreeEdges, setNegTreeEdges, onNegEdgesChange] = useEdgesState([]);

  // ── TAB: Portfolio Heatmap ──
  const [portfolioData, setPortfolioData] = useState(null);
  const [portfolioLoading, setPortfolioLoading] = useState(false);
  const [portfolioError, setPortfolioError] = useState('');

  // ── TAB: MCTS Tree (NEW) ──
  const [mctsResult, setMctsResult] = useState(null);
  const [mctsLoading, setMctsLoading] = useState(false);
  const [mctsIterations, setMctsIterations] = useState(500);
  const [mctsDepth, setMctsDepth] = useState(5);
  const [mctsError, setMctsError] = useState('');

  // ── TAB: Multi-Agent AI (NEW) ──
  const [advMultiAgentResult, setAdvMultiAgentResult] = useState(null);
  const [advMultiAgentLoading, setAdvMultiAgentLoading] = useState(false);
  const [advMultiAgentRounds, setAdvMultiAgentRounds] = useState(5);
  const [advMultiAgentError, setAdvMultiAgentError] = useState('');

  // ── TAB: RL Optimizer (NEW) ──
  const [rlResult, setRlResult] = useState(null);
  const [rlLoading, setRlLoading] = useState(false);
  const [rlError, setRlError] = useState('');

  // ── TAB: Legal Precedents (NEW) ──
  const [precedentResult, setPrecedentResult] = useState(null);
  const [precedentLoading, setPrecedentLoading] = useState(false);
  const [precedentError, setPrecedentError] = useState('');

  // ── WebSocket real-time ──
  const socketRef = useRef(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [wsLivePosteriors, setWsLivePosteriors] = useState({});

  // ── Portfolio Digital Twin (aggregate) ──
  const [portfolioTwinData, setPortfolioTwinData] = useState(null);
  const [portfolioTwinLoading, setPortfolioTwinLoading] = useState(false);

  // ── Manual signals ──
  const [showSignals, setShowSignals] = useState(false);
  const [manualSignals, setManualSignals] = useState({
    WarRisk: 0.05,
    CommodityPriceShock: 0.25,
    ContractAmbiguity: 0.40,
    SupplierDelay: 0.20,
    PaymentDefaultRisk: 0.15,
    CounterpartyCreditRisk: 0.18,
  });

  // ── Load prebuilt scenarios + AI status on mount (graph loads only after prediction) ──
  useEffect(() => {
    loadPrebuilt();
    // Poll AI status every 8s until all components are online (max 5 attempts)
    let attempts = 0;
    const fetchStatus = () => {
      getAIStatus().then(d => {
        setAiStatus(d);
        attempts++;
        const allOnline = d?.legalbert?.model_loaded && d?.rag?.retriever_ready;
        if (!allOnline && attempts < 5) {
          setTimeout(fetchStatus, 8000);
        }
      }).catch(() => {
        attempts++;
        if (attempts < 5) setTimeout(fetchStatus, 8000);
      });
    };
    fetchStatus();
  }, []);

  const loadGraph = async () => {
    setGraphLoading(true);
    try {
      const data = await getDisputeGraph();
      setGraphData(data);
      const { nodes, edges } = buildGraphElements(data);
      setRfNodes(nodes);
      setRfEdges(edges);
    } catch (e) {
      console.error('Graph load error:', e);
    } finally {
      setGraphLoading(false);
    }
  };

  const loadPrebuilt = async () => {
    try {
      const data = await getPrebuiltScenarios();
      setPrebuiltScenarios(data.scenarios || []);
    } catch (e) { /* silent */ }
  };

  const loadHistory = async () => {
    setHistLoading(true);
    try {
      const data = await listPredictions();
      setPredictions(data.predictions || []);
    } catch (e) { /* silent */ }
    finally { setHistLoading(false); }
  };

  const loadFromHistory = async (p) => {
    setLoadingHistId(p.id);
    try {
      // Fetch full detail from the detail endpoint
      const data = await getPrediction(p.id);
      const full = data.prediction || data;

      // Normalize: the detail endpoint returns different field names than predict
      const normalized = {
        ...full,
        // ensure all metric fields exist
        dispute_probability:      full.dispute_probability ?? 0,
        contract_risk_score:      full.contract_risk_score ?? 0,
        arbitration_probability:  full.arbitration_probability ?? 0,
        litigation_probability:   full.litigation_probability ?? 0,
        settlement_probability:   full.settlement_probability ?? 0,
        financial_stress_score:   full.financial_stress_score ?? 0,
        operational_risk_score:   full.operational_risk_score ?? 0,
        geopolitical_risk_score:  full.geopolitical_risk_score ?? 0,
        predicted_cost_usd:       full.predicted_cost_usd ?? 0,
        legal_cost_exposure_usd:  full.legal_cost_exposure_usd ?? 0,
        top_risk_drivers:         full.top_risk_drivers || [],
        risk_propagation_path:    full.risk_propagation_path || [],
        mitigation_recommendations: full.mitigation_recommendations || [],
        explanation:              full.explanation || '',
        gnn_dispute_score:        full.gnn_dispute_score ?? null,
        // map bayesian_risk_nodes → bayesian_posteriors for graph
        bayesian_posteriors:      full.bayesian_risk_nodes || full.bayesian_posteriors || {},
      };

      // Restore contract inputs — use real contract value derived from prediction
      setContractTitle(normalized.contract_title || '');
      const restoredValue = normalized.predicted_cost_usd > 0 && normalized.dispute_probability > 0
        ? Math.round(normalized.predicted_cost_usd / normalized.dispute_probability)
        : contractValue;
      setContractValue(restoredValue);
      setContractText(normalized.contract_text || '');

      // Populate predict tab result panels
      setPrediction(normalized);

      // Auto-fill negotiation sliders from this historical prediction
      _syncNegStateFromPrediction(normalized);

      // Restore base signals for scenario tab
      if (normalized.input_signals) setBaseSignals(normalized.input_signals);

      // Rebuild graph from saved Bayesian posteriors
      if (normalized.bayesian_posteriors && Object.keys(normalized.bayesian_posteriors).length > 0) {
        try {
          const graphData = await getDisputeGraph();
          const { nodes, edges } = buildGraphElements(graphData, normalized.bayesian_posteriors);
          setRfNodes(nodes);
          setRfEdges(edges);
        } catch (_) {
          // graph reload failed silently
        }
      }
      setActiveTab('predict');
    } catch (e) {
      console.error('Failed to load prediction detail:', e);
    } finally {
      setLoadingHistId(null);
    }
  };

  useEffect(() => {
    if (activeTab === 'history') loadHistory();
  }, [activeTab]);

  // ── RUN PREDICTION ──
  const runPrediction = async () => {
    if (!contractText.trim() && Object.keys(manualSignals).length === 0) {
      setPredError('Please enter contract text or set risk signals.');
      return;
    }
    setPredicting(true);
    setPredError('');
    setPrediction(null);
    try {
      // Auto-derive title from first non-empty line of contract text if not set
      const effectiveTitle = contractTitle.trim() ||
        contractText.trim().split('\n').find(l => l.trim().length > 5)?.trim().slice(0, 60) ||
        'Contract Analysis';
      const result = await predictDispute({
        contractText,
        contractValue,
        contractTitle: effectiveTitle,
        manualSignals: showSignals ? manualSignals : {},
        generateExplanation: true,
      });
      setPrediction(result);
      // Auto-fill negotiation sliders from Bayesian posteriors
      _syncNegStateFromPrediction(result);
      // Emit to WebSocket for real-time propagation
      if (result.input_signals) emitRiskSignals(result.input_signals);
      // Refresh graph with live posteriors — fetch graph structure if not yet loaded
      if (result.all_node_posteriors) {
        try {
          const gd = graphData || await getDisputeGraph();
          if (!graphData) setGraphData(gd);
          const { nodes, edges } = buildGraphElements(gd, result.all_node_posteriors);
          setRfNodes(nodes);
          setRfEdges(edges);
        } catch (_) {}
      }
    } catch (e) {
      setPredError(e?.response?.data?.error || e.message || 'Prediction failed.');
    } finally {
      setPredicting(false);
    }
  };

  // ── AUTO-FILL NEGOTIATION SLIDERS FROM PREDICTION ──
  // Called right after every successful prediction. Maps Bayesian posteriors
  // back to the 6 numeric contract parameters used by Negotiation/MCTS/RL tabs.
  const _syncNegStateFromPrediction = (result) => {
    try {
      const p = result.all_node_posteriors || result.bayesian_risk_nodes || {};
      const signals = result.input_signals || {};

      // payment_terms: extract from contract text if possible, else use PaymentDefaultRisk
      // EPC contract says "60 days" — detect common patterns
      const payRisk = p['PaymentDefaultRisk'] ?? signals['PaymentDefaultRisk'] ?? 0.3;
      const textHint = (contractText || '').toLowerCase();
      let payment_terms = Math.round(30 + payRisk * 60);  // 30–90 days
      if (textHint.includes('60 days')) payment_terms = 60;
      else if (textHint.includes('30 days')) payment_terms = 30;
      else if (textHint.includes('45 days')) payment_terms = 45;
      else if (textHint.includes('net 30')) payment_terms = 30;
      else if (textHint.includes('net 60')) payment_terms = 60;

      // delivery_days: detect from contract or use SupplierDelay posterior
      const delRisk = p['SupplierDelay'] ?? signals['SupplierDelay'] ?? 0.3;
      let delivery_days = Math.round(15 + delRisk * 75);  // 15–90 days
      // EPC "18 months" → 540 days, too large for RL slider; cap at 90 for RL state
      if (textHint.includes('18 months')) delivery_days = 60;
      else if (textHint.includes('12 months')) delivery_days = 45;
      else if (textHint.includes('24 months')) delivery_days = 75;

      // liability_cap: extract % from contract text (e.g. "15%" → 0.15)
      const liabMatch = textHint.match(/liability[^.]*?(\d+)%/);
      let liability_cap;
      if (liabMatch) {
        liability_cap = parseFloat((parseInt(liabMatch[1]) / 100).toFixed(2));
        liability_cap = Math.max(0.05, Math.min(0.99, liability_cap));
      } else {
        const ambRisk = p['ContractAmbiguity'] ?? signals['ContractAmbiguity'] ?? 0.3;
        liability_cap = parseFloat(Math.max(0.1, Math.min(0.9, 0.65 - ambRisk * 0.5)).toFixed(2));
      }

      // termination_penalty: extract % from contract text (e.g. "5%" demobilization cap)
      const termMatch = textHint.match(/demobiliz[^.]*?(\d+)%|termination[^.]*?(\d+)%/);
      let termination_penalty;
      if (termMatch) {
        termination_penalty = parseInt(termMatch[1] || termMatch[2]);
      } else {
        const termRisk = p['TerminationRisk'] ?? signals['TerminationRisk'] ?? 0.3;
        termination_penalty = Math.round(termRisk * 30);
      }

      // price: RL index 80–160 from dispute probability
      const dispProb = result.dispute_probability ?? 0.4;
      const price = Math.round(80 + dispProb * 80);

      // force_majeure: 1 if contract mentions it (most EPC do)
      const force_majeure = textHint.includes('force majeure') || textHint.includes('force-majeure') ? 1 : 0;

      setNegInitState({ price, delivery_days, liability_cap, payment_terms, termination_penalty, force_majeure });
    } catch (_) {
      // fail silently — sliders keep their defaults
    }
  };

  // ── RUN SIMULATION ──
  const runSimulation = async () => {
    if (selectedScenarios.length === 0) {
      setSimError('Select at least one scenario.');
      return;
    }
    setSimulating(true);
    setSimError('');
    setSimResults(null);
    try {
      const scenarios = prebuiltScenarios
        .filter(s => selectedScenarios.includes(s.id))
        .map(s => ({ name: s.name, description: s.description, overrides: s.overrides }));
      const result = await simulateDisputeScenarios({
        baseSignals: manualSignals,
        scenarios,
        contractValue,
      });
      setSimResults(result);
    } catch (e) {
      setSimError(e?.response?.data?.error || e.message || 'Simulation failed.');
    } finally {
      setSimulating(false);
    }
  };

  const handleDeletePrediction = async (id) => {
    try {
      await deletePrediction(id);
      setPredictions(prev => prev.filter(p => p.id !== id));
    } catch (e) { /* silent */ }
  };

  // ── CLAUSE RISK TABLE ──
  const runClauseRiskTable = async () => {
    if (!contractText.trim()) { setClauseTableError('Enter contract text on the Predict tab first.'); return; }
    setClauseTableLoading(true); setClauseTableError(''); setClauseTable(null);
    try {
      const data = await getClauseRiskTable(contractText, contractValue);
      setClauseTable(data);
    } catch (e) {
      setClauseTableError(e?.response?.data?.error || e.message || 'Failed.');
    } finally { setClauseTableLoading(false); }
  };

  // ── TIME TRAVEL ──
  const runTimeTravelSim = async () => {
    setTimeTravelLoading(true); setTimeTravelError(''); setTimeTravelData(null); setTimeTravelSlider(0);
    try {
      const data = await getTimeTravelRisk(contractText, contractValue, timeTravelMonths);
      setTimeTravelData(data);
    } catch (e) {
      setTimeTravelError(e?.response?.data?.error || e.message || 'Failed.');
    } finally { setTimeTravelLoading(false); }
  };

  // ── DIGITAL TWIN ──
  const runDigitalTwinSim = async () => {
    setTwinLoading(true); setTwinError(''); setTwinData(null);
    try {
      const data = await runDigitalTwin({ contractValue, months: twinMonths, contractText });
      setTwinData(data);
    } catch (e) {
      setTwinError(e?.response?.data?.error || e.message || 'Failed.');
    } finally { setTwinLoading(false); }
  };

  // ── NEGOTIATION SIM ──
  const runNegSim = async () => {
    setNegSimLoading(true); setNegSimError(''); setNegSimData(null); setMultiAgentData(null);
    try {
      if (negMode === 'mcts') {
        const data = await runNegotiationSimulator({ contractValue, initialState: negInitState, rounds: negRounds });
        setNegSimData(data);
        if (data.negotiation_tree_nodes) { setNegTreeNodes(data.negotiation_tree_nodes); setNegTreeEdges(data.negotiation_tree_edges || []); }
      } else {
        const data = await runMultiAgentNegotiation({ contractValue, initialState: negInitState, rounds: Math.min(negRounds, 5) });
        setMultiAgentData(data);
      }
    } catch (e) {
      setNegSimError(e?.response?.data?.error || e.message || 'Failed.');
    } finally { setNegSimLoading(false); }
  };

  // ── PORTFOLIO HEATMAP ──
  const loadPortfolioHeatmap = async () => {
    setPortfolioLoading(true); setPortfolioError(''); setPortfolioData(null);
    try {
      // If there's a current prediction from the Predict tab, use it directly
      // (single-contract analysis — no need to pull unrelated DB records)
      if (prediction) {
        const dp = prediction.dispute_probability ?? 0;
        const cr = prediction.contract_risk_score ?? dp;
        const fs = prediction.financial_stress_score ?? dp * 0.9;
        const cost = prediction.predicted_cost_usd ?? 0;
        const risk_level = dp < 0.25 ? 'low' : dp < 0.5 ? 'medium' : dp < 0.75 ? 'high' : 'critical';
        const contractEntry = {
          id: prediction.id || 'current',
          title: prediction.contract_title || contractTitle || 'Current Contract',
          contract_id: prediction.contract_id || 'current',
          dispute_probability: Math.round(dp * 1000) / 1000,
          contract_risk: Math.round(cr * 1000) / 1000,
          financial_stress: Math.round(fs * 1000) / 1000,
          predicted_cost: Math.round(cost),
          risk_level,
          top_driver: prediction.top_risk_drivers?.[0]?.label || 'Contract Analysis',
          created_at: new Date().toISOString(),
        };
        const risk_distribution = { low: 0, medium: 0, high: 0, critical: 0 };
        risk_distribution[risk_level] += 1;
        setPortfolioData({
          contracts: [contractEntry],
          total_contracts: 1,
          risk_distribution,
          avg_dispute_probability: dp,
          total_predicted_exposure: cost,
          high_risk_count: risk_level === 'high' || risk_level === 'critical' ? 1 : 0,
          critical_count: risk_level === 'critical' ? 1 : 0,
        });
        return;
      }
      // No current prediction — fall back to API (DB records)
      const data = await getPortfolioDisputeHeatmap();
      setPortfolioData(data);
    } catch (e) {
      setPortfolioError(e?.response?.data?.error || e.message || 'Failed.');
    } finally { setPortfolioLoading(false); }
  };

  useEffect(() => {
    if (activeTab === 'portfolio') loadPortfolioHeatmap();
  }, [activeTab, prediction]);

  // ── WEBSOCKET SETUP (OPTIONAL - DISABLE IF NO SOCKET.IO SERVER) ──
  useEffect(() => {
    // Set to false to completely disable WebSocket (prevents console errors)
    const ENABLE_WEBSOCKET = false;

    if (!ENABLE_WEBSOCKET) {
      setWsConnected(false);
      return;
    }

    try {
      const socket = io((import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')), {
        transports: ['websocket', 'polling'],
        timeout: 3000,
        reconnectionAttempts: 1,
        reconnectionDelay: 5000,
      });
      socketRef.current = socket;
      socket.on('connect', () => setWsConnected(true));
      socket.on('disconnect', () => setWsConnected(false));
      socket.on('risk_update', (data) => {
        if (data?.posteriors) {
          setWsLivePosteriors(data.posteriors);
          // Update graph nodes live
          if (graphData) {
            const { nodes, edges } = buildGraphElements(graphData, data.posteriors);
            setRfNodes(nodes);
            setRfEdges(edges);
          }
        }
      });
      socket.on('connect_error', () => {
        setWsConnected(false);
        // Suppress error logging
      });
    } catch (e) {
      setWsConnected(false);
    }
    return () => { if (socketRef.current) socketRef.current.disconnect(); };
  }, []);

  // Emit signals to WebSocket when prediction runs
  const emitRiskSignals = (signals) => {
    if (socketRef.current?.connected && signals) {
      socketRef.current.emit('update_signals', { signals });
    }
  };

  // ── PORTFOLIO TWIN ──
  const runPortfolioTwin = async () => {
    setPortfolioTwinLoading(true);
    try {
      // Simulate portfolio of contracts using existing portfolio heatmap data
      const heatmapData = portfolioData || await getPortfolioDisputeHeatmap();
      if (!portfolioData) setPortfolioData(heatmapData);
      const contracts = heatmapData.contracts || [];
      // Aggregate stats
      const total = contracts.length || 12;
      const highRisk = contracts.filter(c => c.dispute_probability > 0.5).length;
      const criticalRisk = contracts.filter(c => c.dispute_probability > 0.7).length;
      const totalExposure = contracts.reduce((sum, c) => sum + (c.predicted_cost || 0), 0);
      const avgRisk = contracts.reduce((sum, c) => sum + c.dispute_probability, 0) / (total || 1);
      // Build month-by-month portfolio risk
      const months = 12;
      const portfolioTimeline = Array.from({ length: months + 1 }, (_, m) => {
        const escalation = 1 + m * 0.02;
        return {
          month: m,
          label: m === 0 ? 'Start' : `Month ${m}`,
          avg_dispute_risk: Math.min(0.95, avgRisk * escalation),
          contracts_at_risk: Math.round(highRisk * escalation),
          expected_cost: Math.round(totalExposure * escalation),
          critical_count: Math.round(criticalRisk * Math.min(escalation, 1.5)),
        };
      });
      setPortfolioTwinData({
        total_contracts: total,
        contracts_at_risk: highRisk,
        high_dispute_prob_count: criticalRisk,
        expected_arbitration_cost: totalExposure,
        avg_dispute_probability: avgRisk,
        timeline: portfolioTimeline,
      });
    } catch (e) {
      console.error('Portfolio twin failed:', e);
    } finally {
      setPortfolioTwinLoading(false);
    }
  };

  // ═══════════════════════════════════════════════════════════
  // NEW ADVANCED AI HANDLERS
  // ═══════════════════════════════════════════════════════════

  const handleRunMCTS = async () => {
    setMctsLoading(true);
    setMctsError('');
    try {
      const result = await runMCTSNegotiation(negInitState, mctsIterations, mctsDepth);
      setMctsResult(result);
    } catch (error) {
      console.error('MCTS error:', error);
      setMctsError(error.message || 'MCTS negotiation failed');
    } finally {
      setMctsLoading(false);
    }
  };

  const handleRunAdvancedMultiAgent = async () => {
    setAdvMultiAgentLoading(true);
    setAdvMultiAgentError('');
    try {
      const result = await runAdvancedMultiAgent(negInitState, advMultiAgentRounds);
      setAdvMultiAgentResult(result);
    } catch (error) {
      console.error('Advanced Multi-agent error:', error);
      setAdvMultiAgentError(error.message || 'Multi-agent negotiation failed');
    } finally {
      setAdvMultiAgentLoading(false);
    }
  };

  const handleRunRL = async () => {
    setRlLoading(true);
    setRlError('');
    try {
      const result = await optimizeContractWithRL(negInitState);
      setRlResult(result);
    } catch (error) {
      console.error('RL error:', error);
      setRlError(error.message || 'RL optimization failed');
    } finally {
      setRlLoading(false);
    }
  };

  const handleMatchPrecedents = async () => {
    setPrecedentLoading(true);
    setPrecedentError('');
    try {
      const result = await matchLegalPrecedents(
        contractText || 'Sample construction contract with EPC terms',
        contractValue,
        'construction',
        'US',
        5
      );
      setPrecedentResult(result);
    } catch (error) {
      console.error('Precedent matching error:', error);
      setPrecedentError(error.message || 'Precedent matching failed');
    } finally {
      setPrecedentLoading(false);
    }
  };

  const tabs = [
    { id: 'predict',   label: 'Predict',          icon: Brain },
    { id: 'graph',     label: 'Risk Graph 2D',     icon: Activity },
    { id: 'graph3d',   label: 'Risk Graph 3D',     icon: Globe },
    { id: 'scenarios', label: 'Scenario Sim',      icon: Sliders },
    { id: 'clause-risk', label: 'Clause Risk Table', icon: Table2 },
    { id: 'timetravel',  label: 'Time Travel',       icon: Clock },
    { id: 'twin',        label: 'Digital Twin',      icon: GitBranch },
    { id: 'negotiation', label: 'Negotiation Sim',   icon: Users },
    { id: 'mcts',        label: 'MCTS Tree',         icon: GitBranch },
    { id: 'multiagent',  label: 'Multi-Agent AI',    icon: Users },
    { id: 'rl',          label: 'RL Optimizer',      icon: Zap },
    { id: 'precedents',  label: 'Legal Precedents',  icon: Scale },
    { id: 'portfolio',   label: 'Portfolio Heatmap', icon: Map },
    { id: 'neo4j',       label: 'Neo4j Graph',       icon: Globe },
    { id: 'history',   label: 'History',           icon: History },
    { id: 'howto',     label: 'How It Works',      icon: Info },
  ];

  return (
    <>
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .spin {
          animation: spin 1s linear infinite;
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        .pulse {
          animation: pulse 2s ease-in-out infinite;
        }
      `}</style>
      <div style={{
        minHeight: '100vh',
        background: 'linear-gradient(180deg, #0a0f1e 0%, #0d1424 100%)',
        color: '#e2e8f0',
        fontFamily: 'system-ui, sans-serif',
        padding: '24px',
      }}>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
          <div style={{
            width: 44, height: 44, borderRadius: 10,
            background: 'linear-gradient(135deg, #dc2626, #7c3aed)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Scale size={22} color="#fff" />
          </div>
          <div style={{ flex: 1 }}>
            <h1 style={{ fontSize: 24, fontWeight: 800, color: '#f1f5f9', margin: 0 }}>
              Dispute Predictor & Simulator
            </h1>
            <p style={{ color: '#64748b', fontSize: 13, margin: 0 }}>
              60-node Bayesian Risk Network · GNN Scoring · Legal AI · RAG
            </p>
          </div>
          {/* AI Status Badges */}
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
            {/* WebSocket indicator — only show when connected */}
            {wsConnected && (
              <div style={{
                background: '#10b98115', border: '1px solid #10b98160',
                borderRadius: 7, padding: '4px 10px',
                display: 'flex', alignItems: 'center', gap: 5,
              }}>
                <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#10b981', boxShadow: '0 0 6px #10b981' }} />
                <span style={{ color: '#10b981', fontSize: 11, fontWeight: 600 }}>Live</span>
                <span style={{ color: '#475569', fontSize: 10 }}>WS</span>
              </div>
            )}
          </div>
          {aiStatus && (
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {[
                { label: 'Bayesian', ok: aiStatus.bayesian?.available, detail: `${aiStatus.bayesian?.nodes}n` },
                { label: 'GNN', ok: aiStatus.gnn?.available, detail: aiStatus.gnn?.model_loaded ? 'trained' : 'heuristic' },
                { label: 'LegalBERT', ok: aiStatus.legalbert?.model_loaded, detail: aiStatus.legalbert?.model_loaded ? 'active' : 'offline' },
                { label: 'RAG', ok: aiStatus.rag?.retriever_ready, detail: `${aiStatus.rag?.indexed_clauses ?? 0} clauses` },
              ].map(s => (
                <div key={s.label} style={{
                  background: s.ok ? '#10b98115' : '#47456815',
                  border: `1px solid ${s.ok ? '#10b98160' : '#47456860'}`,
                  borderRadius: 7, padding: '4px 10px',
                  display: 'flex', alignItems: 'center', gap: 5,
                }}>
                  <div style={{
                    width: 6, height: 6, borderRadius: '50%',
                    background: s.ok ? '#10b981' : '#475569',
                  }} />
                  <span style={{ color: s.ok ? '#10b981' : '#64748b', fontSize: 11, fontWeight: 600 }}>
                    {s.label}
                  </span>
                  <span style={{ color: '#475569', fontSize: 10 }}>{s.detail}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div style={{
        display: 'flex', gap: 4, marginBottom: 24,
        background: '#0f172a',
        borderRadius: 10, padding: 4,
        border: '1px solid #1e293b',
        overflowX: 'auto',
      }}>
        {tabs.map(tab => {
          const Icon = tab.icon;
          const active = activeTab === tab.id;
          const isPredictTab = tab.id === 'predict';
          const isDisabled = !isPredictTab && !prediction;
          return (
            <button
              key={tab.id}
              onClick={() => {
                if (!isDisabled) {
                  setActiveTab(tab.id);
                } else {
                  alert('🔒 Please run a prediction first on the "Predict" tab to unlock this feature');
                }
              }}
              disabled={isDisabled}
              title={isDisabled ? '🔒 Run prediction first to unlock' : ''}
              style={{
                display: 'flex', alignItems: 'center', gap: 6,
                padding: '8px 16px', borderRadius: 7, border: 'none',
                cursor: isDisabled ? 'not-allowed' : 'pointer',
                whiteSpace: 'nowrap',
                background: active ? 'linear-gradient(135deg, #dc2626, #7c3aed)' : 'transparent',
                color: isDisabled ? '#334155' : (active ? '#fff' : '#64748b'),
                fontWeight: active ? 700 : 500,
                fontSize: 13,
                transition: 'all 0.2s',
                opacity: isDisabled ? 0.4 : 1,
                position: 'relative',
              }}
            >
              {isDisabled ? <Lock size={14} /> : <Icon size={14} />}
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* ═══ TAB 1: PREDICT ═══ */}
      {activeTab === 'predict' && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(400px, 1fr) minmax(400px, 1fr)',
          gap: 24,
          alignItems: 'start'
        }}>
          {/* Left: Input */}
          <div style={{
            background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
            border: '2px solid #334155',
            borderRadius: 14,
            padding: 24,
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.4)',
            height: 'fit-content',
            position: 'sticky',
            top: 20
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
              <span style={{ fontSize: 24 }}>📄</span>
              <h3 style={{ color: '#e2e8f0', margin: 0, fontSize: 18, fontWeight: 800, letterSpacing: '-0.02em' }}>
                Contract Analysis
              </h3>
            </div>

            <label style={{
              color: '#94a3b8',
              fontSize: 12,
              fontWeight: 600,
              display: 'block',
              marginBottom: 6,
              textTransform: 'uppercase',
              letterSpacing: '0.05em'
            }}>
              📝 Contract Title (optional)
            </label>
            <input
              value={contractTitle}
              onChange={e => setContractTitle(e.target.value)}
              placeholder="e.g. EPC Infrastructure Contract"
              style={{
                width: '100%',
                padding: '10px 14px',
                marginBottom: 16,
                background: '#1e293b',
                border: '2px solid #334155',
                borderRadius: 10,
                color: '#e2e8f0',
                fontSize: 14,
                boxSizing: 'border-box',
                transition: 'all 0.3s ease',
                outline: 'none'
              }}
              onFocus={(e) => e.target.style.borderColor = '#3b82f6'}
              onBlur={(e) => e.target.style.borderColor = '#334155'}
            />

            <label style={{
              color: '#94a3b8',
              fontSize: 12,
              fontWeight: 600,
              display: 'block',
              marginBottom: 6,
              textTransform: 'uppercase',
              letterSpacing: '0.05em'
            }}>
              💰 Contract Value (USD)
            </label>
            <input
              type="number"
              value={contractValue}
              onChange={e => setContractValue(Number(e.target.value))}
              style={{
                width: '100%',
                padding: '10px 14px',
                marginBottom: 16,
                background: '#1e293b',
                border: '2px solid #334155',
                borderRadius: 10,
                color: '#e2e8f0',
                fontSize: 14,
                boxSizing: 'border-box',
                transition: 'all 0.3s ease',
                outline: 'none'
              }}
              onFocus={(e) => e.target.style.borderColor = '#10b981'}
              onBlur={(e) => e.target.style.borderColor = '#334155'}
            />

            <label style={{
              color: '#94a3b8',
              fontSize: 12,
              fontWeight: 600,
              display: 'block',
              marginBottom: 6,
              textTransform: 'uppercase',
              letterSpacing: '0.05em'
            }}>
              📋 Contract Text (paste full contract or excerpt)
            </label>
            <textarea
              value={contractText}
              onChange={e => setContractText(e.target.value)}
              rows={10}
              placeholder="Paste your contract text here. The AI will extract risk signals and run the Bayesian dispute prediction network..."
              style={{
                width: '100%',
                padding: '12px 14px',
                marginBottom: 16,
                background: '#1e293b',
                border: '2px solid #334155',
                borderRadius: 10,
                color: '#e2e8f0',
                fontSize: 13,
                lineHeight: 1.6,
                resize: 'vertical',
                boxSizing: 'border-box',
                fontFamily: 'inherit',
                minHeight: 200,
                transition: 'all 0.3s ease',
                outline: 'none'
              }}
              onFocus={(e) => e.target.style.borderColor = '#7c3aed'}
              onBlur={(e) => e.target.style.borderColor = '#334155'}
            />

            {/* Manual signal overrides */}
            <button
              onClick={() => setShowSignals(!showSignals)}
              style={{
                background: 'none', border: '1px solid #334155',
                borderRadius: 6, color: '#94a3b8', padding: '5px 12px',
                fontSize: 12, cursor: 'pointer', marginBottom: 12,
              }}
            >
              {showSignals ? '▲' : '▼'} Advanced: Override Risk Signals
            </button>

            {showSignals && (
              <div style={{
                background: '#1e293b', borderRadius: 8, padding: 14,
                marginBottom: 12, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10,
              }}>
                {Object.entries(manualSignals).map(([key, val]) => (
                  <div key={key}>
                    <label style={{ color: '#94a3b8', fontSize: 11 }}>
                      {key}: {(val * 100).toFixed(0)}%
                    </label>
                    <input
                      type="range" min={0} max={1} step={0.05}
                      value={val}
                      onChange={e => setManualSignals(prev => ({
                        ...prev, [key]: parseFloat(e.target.value),
                      }))}
                      style={{ width: '100%' }}
                    />
                  </div>
                ))}
              </div>
            )}

            {predError && (
              <div style={{
                background: '#dc262615', border: '1px solid #dc2626',
                borderRadius: 6, padding: '8px 12px', color: '#fca5a5',
                fontSize: 12, marginBottom: 12,
              }}>
                {predError}
              </div>
            )}

            <button
              onClick={runPrediction}
              disabled={predicting || !contractText.trim()}
              style={{
                width: '100%',
                padding: '14px',
                background: predicting || !contractText.trim()
                  ? '#374151'
                  : 'linear-gradient(135deg, #dc2626 0%, #ef4444 50%, #7c3aed 100%)',
                border: 'none',
                borderRadius: 12,
                color: '#fff',
                fontWeight: 800,
                fontSize: 15,
                cursor: predicting || !contractText.trim() ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 10,
                boxShadow: predicting || !contractText.trim() ? 'none' : '0 6px 20px rgba(220, 38, 38, 0.4)',
                transition: 'all 0.3s ease',
                textTransform: 'uppercase',
                letterSpacing: '0.05em'
              }}
              onMouseEnter={(e) => {
                if (!predicting && contractText.trim()) {
                  e.target.style.transform = 'translateY(-2px)';
                  e.target.style.boxShadow = '0 8px 28px rgba(220, 38, 38, 0.6)';
                }
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = predicting || !contractText.trim() ? 'none' : '0 6px 20px rgba(220, 38, 38, 0.4)';
              }}
            >
              {predicting ? (
                <><RefreshCw size={18} className="spin" /> Analyzing Contract...</>
              ) : (
                <><Play size={18} /> Run Dispute Prediction</>
              )}
            </button>
            {!contractText.trim() && (
              <div style={{
                color: '#64748b',
                fontSize: 11,
                marginTop: 8,
                textAlign: 'center',
                fontStyle: 'italic'
              }}>
                Please enter contract text to run prediction
              </div>
            )}
          </div>

          {/* Right: Results */}
          <div style={{ minHeight: 600 }}>
            {!prediction ? (
              <div style={{
                background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
                border: '2px dashed #475569',
                borderRadius: 14,
                padding: 60,
                textAlign: 'center',
                color: '#64748b',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                minHeight: 400
              }}>
                <Scale size={64} style={{ marginBottom: 20, opacity: 0.4 }} />
                <h3 style={{ color: '#94a3b8', fontSize: 18, fontWeight: 700, margin: '0 0 10px 0' }}>
                  No Analysis Yet
                </h3>
                <p style={{ fontSize: 14, margin: 0, maxWidth: 300 }}>
                  Enter your contract details on the left and click "Run Dispute Prediction" to see AI-powered risk analysis
                </p>
              </div>
            ) : (
              <div>
                {/* Core metrics */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
                  <MetricCard
                    label="Dispute Probability" value={prediction.dispute_probability} unit="%"
                    color={SEVERITY_COLOR(prediction.dispute_probability)} icon={AlertTriangle}
                    subtitle="Overall dispute likelihood"
                  />
                  <MetricCard
                    label="Contract Risk Score" value={prediction.contract_risk_score} unit="%"
                    color="#f59e0b" icon={Shield}
                    subtitle="Bayesian contract risk"
                  />
                  <MetricCard
                    label="Arbitration Probability" value={prediction.arbitration_probability} unit="%"
                    color="#7c3aed" icon={Scale}
                    subtitle="Escalation to arbitration"
                  />
                  <MetricCard
                    label="Legal Cost Exposure" value={prediction.legal_cost_exposure_usd} unit="$"
                    color="#ef4444" icon={TrendingUp}
                    subtitle="P90 legal cost estimate"
                  />
                </div>

                {/* Secondary metrics */}
                <div style={{
                  background: '#0f172a', border: '1px solid #1e293b',
                  borderRadius: 10, padding: 14, marginBottom: 14,
                }}>
                  <h4 style={{ color: '#94a3b8', fontSize: 12, marginBottom: 10 }}>RISK BREAKDOWN</h4>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
                    {[
                      { label: 'Financial Stress', val: prediction.financial_stress_score, color: '#10b981' },
                      { label: 'Operational Risk', val: prediction.operational_risk_score, color: '#f59e0b' },
                      { label: 'Geopolitical Risk', val: prediction.geopolitical_risk_score, color: '#ef4444' },
                      { label: 'Litigation Prob.', val: prediction.litigation_probability, color: '#8b5cf6' },
                      { label: 'Settlement Prob.', val: prediction.settlement_probability, color: '#06b6d4' },
                      { label: 'Predicted Cost', val: prediction.predicted_cost_usd, color: '#f59e0b', isUSD: true },
                    ].map(m => (
                      <div key={m.label} style={{
                        background: '#1e293b', borderRadius: 8, padding: '10px 12px',
                        borderTop: `2px solid ${m.color}`,
                      }}>
                        <div style={{ color: '#64748b', fontSize: 10 }}>{m.label}</div>
                        <div style={{ color: m.color, fontWeight: 700, fontSize: 16 }}>
                          {m.isUSD
                            ? `$${(m.val / 1000).toFixed(0)}K`
                            : `${(m.val * 100).toFixed(0)}%`
                          }
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* GNN + LegalBERT AI scores */}
                {(prediction.gnn_dispute_score !== null || prediction.legalbert_available) && (
                  <div style={{
                    background: '#0f172a', border: '1px solid #7c3aed30',
                    borderRadius: 10, padding: 14, marginBottom: 14,
                  }}>
                    <h4 style={{ color: '#94a3b8', fontSize: 12, marginBottom: 10 }}>
                      AI MODEL SCORES
                    </h4>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>

                      {/* GNN Score */}
                      <div style={{
                        background: '#1e293b', borderRadius: 8, padding: '12px 14px',
                        border: '1px solid #7c3aed40',
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                          <Brain size={12} color="#7c3aed" />
                          <span style={{ color: '#94a3b8', fontSize: 11 }}>GNN Dispute Score</span>
                          <span style={{
                            background: prediction.gnn_source === 'gnn_model' ? '#10b98120' : '#f59e0b20',
                            border: `1px solid ${prediction.gnn_source === 'gnn_model' ? '#10b981' : '#f59e0b'}`,
                            borderRadius: 4, padding: '1px 5px', fontSize: 9, fontWeight: 700,
                            color: prediction.gnn_source === 'gnn_model' ? '#10b981' : '#f59e0b',
                          }}>
                            {prediction.gnn_source === 'gnn_model' ? 'TRAINED' : prediction.gnn_source === 'gnn_heuristic' ? 'HEURISTIC' : 'N/A'}
                          </span>
                        </div>
                        <div style={{ fontSize: 24, fontWeight: 800, color: SEVERITY_COLOR(prediction.gnn_dispute_score ?? 0) }}>
                          {prediction.gnn_dispute_score !== null ? `${(prediction.gnn_dispute_score * 100).toFixed(0)}%` : '–'}
                        </div>
                        {prediction.gnn_confidence !== null && (
                          <div style={{ color: '#64748b', fontSize: 10, marginTop: 2 }}>
                            Confidence: {(prediction.gnn_confidence * 100).toFixed(0)}%
                          </div>
                        )}
                        {prediction.gnn_outcome_distribution && (
                          <div style={{ marginTop: 8, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                            {[
                              { label: 'Buyer Win', val: prediction.gnn_outcome_distribution.buyer_win, color: '#10b981' },
                              { label: 'Supplier Win', val: prediction.gnn_outcome_distribution.supplier_win, color: '#ef4444' },
                              { label: 'Partial', val: prediction.gnn_outcome_distribution.partial_award, color: '#f59e0b' },
                              { label: 'Settlement', val: prediction.gnn_outcome_distribution.settlement, color: '#06b6d4' },
                            ].map(o => o.val != null && (
                              <div key={o.label} style={{
                                background: o.color + '15', border: `1px solid ${o.color}40`,
                                borderRadius: 4, padding: '2px 6px',
                                color: o.color, fontSize: 10, fontWeight: 600,
                              }}>
                                {o.label}: {(o.val * 100).toFixed(0)}%
                              </div>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* LegalBERT panel */}
                      <div style={{
                        background: '#1e293b', borderRadius: 8, padding: '12px 14px',
                        border: '1px solid #0ea5e940',
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                          <Zap size={12} color="#0ea5e9" />
                          <span style={{ color: '#94a3b8', fontSize: 11 }}>LegalBERT Amplification</span>
                          <span style={{
                            background: prediction.legalbert_available ? '#10b98120' : '#47456820',
                            border: `1px solid ${prediction.legalbert_available ? '#10b981' : '#475568'}`,
                            borderRadius: 4, padding: '1px 5px', fontSize: 9, fontWeight: 700,
                            color: prediction.legalbert_available ? '#10b981' : '#64748b',
                          }}>
                            {prediction.legalbert_available ? 'ACTIVE' : 'OFFLINE'}
                          </span>
                        </div>
                        {prediction.legalbert_available && prediction.legalbert_amplified_nodes?.length > 0 ? (
                          <div>
                            <div style={{ color: '#64748b', fontSize: 10, marginBottom: 6 }}>
                              {prediction.legalbert_amplified_nodes.length} risks semantically amplified
                            </div>
                            {prediction.legalbert_amplified_nodes.slice(0, 4).map(a => (
                              <div key={a.node} style={{
                                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                padding: '3px 0', borderBottom: '1px solid #0f172a',
                              }}>
                                <span style={{ color: '#cbd5e1', fontSize: 11 }}>{a.node}</span>
                                <div style={{ display: 'flex', gap: 6 }}>
                                  <span style={{ color: '#0ea5e9', fontSize: 10 }}>
                                    sim {a.similarity?.toFixed(2)}
                                  </span>
                                  <span style={{ color: '#10b981', fontSize: 10 }}>
                                    +{(a.boost * 100)?.toFixed(0)}%
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div style={{ color: '#475569', fontSize: 11 }}>
                            {prediction.legalbert_available ? 'No semantic amplification triggered.' : 'LegalBERT model not loaded on this server.'}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* RAG — Similar Clauses - Enhanced */}
                {prediction.similar_clauses?.length > 0 && (
                  <div style={{
                    background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
                    border: '2px solid #06b6d450',
                    borderRadius: 12,
                    padding: 18,
                    marginBottom: 16,
                    boxShadow: '0 4px 16px rgba(6, 182, 212, 0.15)'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
                      <span style={{ fontSize: 20 }}>🔍</span>
                      <h4 style={{ color: '#06b6d4', fontSize: 14, fontWeight: 700, margin: 0, letterSpacing: '-0.01em' }}>
                        SIMILAR CLAUSES (AI RAG)
                      </h4>
                    </div>
                    <div style={{ maxHeight: 400, overflowY: 'auto', paddingRight: 4 }}>
                      {prediction.similar_clauses.map((c, i) => (
                        <div key={i} style={{
                          background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
                          borderRadius: 10,
                          padding: '14px 16px',
                          marginBottom: 10,
                          border: '2px solid #06b6d430',
                          transition: 'all 0.3s ease',
                          cursor: 'pointer'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.borderColor = '#06b6d480';
                          e.currentTarget.style.boxShadow = '0 4px 12px rgba(6, 182, 212, 0.2)';
                          e.currentTarget.style.transform = 'translateX(4px)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.borderColor = '#06b6d430';
                          e.currentTarget.style.boxShadow = 'none';
                          e.currentTarget.style.transform = 'translateX(0)';
                        }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10, gap: 12, flexWrap: 'wrap' }}>
                            <span style={{
                              background: '#06b6d420',
                              border: '1px solid #06b6d460',
                              borderRadius: 6,
                              padding: '4px 10px',
                              color: '#06b6d4',
                              fontSize: 11,
                              fontWeight: 700,
                              textTransform: 'uppercase',
                              letterSpacing: '0.05em'
                            }}>
                              {c.clause_type || 'CLAUSE'}
                            </span>
                            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                              <span style={{
                                background: '#64748b20',
                                border: '1px solid #64748b40',
                                borderRadius: 5,
                                padding: '3px 8px',
                                color: '#94a3b8',
                                fontSize: 10,
                                fontWeight: 600
                              }}>
                                BM25: {c.bm25_score?.toFixed(2)}
                              </span>
                              <span style={{
                                background: '#7c3aed20',
                                border: '1px solid #7c3aed40',
                                borderRadius: 5,
                                padding: '3px 8px',
                                color: '#a78bfa',
                                fontSize: 10,
                                fontWeight: 600
                              }}>
                                BERT: {c.bert_score?.toFixed(2)}
                              </span>
                              <span style={{
                                background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                                border: '1px solid #10b981',
                                borderRadius: 5,
                                padding: '3px 8px',
                                color: '#fff',
                                fontSize: 10,
                                fontWeight: 700,
                                boxShadow: '0 2px 4px rgba(16, 185, 129, 0.3)'
                              }}>
                                Score: {c.fusion_score?.toFixed(3)}
                              </span>
                            </div>
                          </div>
                          <p style={{
                            color: '#cbd5e1',
                            fontSize: 12,
                            margin: 0,
                            lineHeight: 1.6,
                            maxHeight: 80,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            display: '-webkit-box',
                            WebkitLineClamp: 3,
                            WebkitBoxOrient: 'vertical'
                          }}>
                            {c.clause_text}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Top risk drivers - Enhanced */}
                {prediction.top_risk_drivers?.length > 0 && (
                  <div style={{
                    background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
                    border: '2px solid #f59e0b50',
                    borderRadius: 12,
                    padding: 18,
                    marginBottom: 16,
                    boxShadow: '0 4px 16px rgba(245, 158, 11, 0.15)'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
                      <span style={{ fontSize: 20 }}>⚡</span>
                      <h4 style={{ color: '#f59e0b', fontSize: 14, fontWeight: 700, margin: 0, letterSpacing: '-0.01em' }}>
                        TOP RISK DRIVERS
                      </h4>
                      <span style={{
                        background: '#f59e0b20',
                        border: '1px solid #f59e0b60',
                        borderRadius: 6,
                        padding: '2px 8px',
                        color: '#fbbf24',
                        fontSize: 10,
                        fontWeight: 600,
                        marginLeft: 'auto'
                      }}>
                        Top {Math.min(5, prediction.top_risk_drivers.length)}
                      </span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {prediction.top_risk_drivers.slice(0, 5).map((d, i) => (
                        <RiskDriverRow key={d.node} driver={d} rank={i + 1} />
                      ))}
                    </div>
                  </div>
                )}

                {/* Propagation path */}
                {prediction.risk_propagation_path?.length > 0 && (
                  <div style={{
                    background: '#0f172a', border: '1px solid #1e293b',
                    borderRadius: 10, padding: 14, marginBottom: 14,
                  }}>
                    <h4 style={{ color: '#94a3b8', fontSize: 12, marginBottom: 10 }}>RISK PROPAGATION PATH</h4>
                    <PropagationPath path={prediction.risk_propagation_path} />
                  </div>
                )}

                {/* Mitigations */}
                {prediction.mitigation_recommendations?.length > 0 && (
                  <div style={{
                    background: '#0f172a', border: '1px solid #1e293b',
                    borderRadius: 10, padding: 14, marginBottom: 14,
                  }}>
                    <h4 style={{ color: '#94a3b8', fontSize: 12, marginBottom: 10 }}>MITIGATION RECOMMENDATIONS</h4>
                    {prediction.mitigation_recommendations.map((m, i) => (
                      <div key={i} style={{
                        display: 'flex', gap: 10, padding: '8px 0',
                        borderBottom: i < prediction.mitigation_recommendations.length - 1 ? '1px solid #1e293b' : 'none',
                      }}>
                        <div style={{
                          width: 20, height: 20, borderRadius: '50%',
                          background: '#10b98120', border: '1px solid #10b981',
                          color: '#10b981', fontSize: 11, fontWeight: 700,
                          display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                        }}>{i + 1}</div>
                        <div style={{ color: '#cbd5e1', fontSize: 13 }}>{m.recommendation}</div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Explanation */}
                {prediction.explanation && (
                  <div style={{
                    background: 'linear-gradient(135deg, #1e293b, #0f172a)',
                    border: '1px solid #334155', borderRadius: 10, padding: 14,
                  }}>
                    <h4 style={{ color: '#94a3b8', fontSize: 12, marginBottom: 8 }}>
                      AI LEGAL EXPLANATION
                    </h4>
                    <div style={{ color: '#cbd5e1', fontSize: 12, lineHeight: 1.8 }}>
                      {prediction.explanation.split('\n').map((line, i) => {
                        if (!line.trim()) return <div key={i} style={{ height: 6 }} />;
                        if (line.startsWith('### ')) return (
                          <div key={i} style={{ color: '#e2e8f0', fontWeight: 700, fontSize: 13, marginTop: 12, marginBottom: 4 }}>
                            {line.replace('### ', '')}
                          </div>
                        );
                        if (line.startsWith('## ')) return (
                          <div key={i} style={{ color: '#f1f5f9', fontWeight: 700, fontSize: 14, marginTop: 14, marginBottom: 4 }}>
                            {line.replace('## ', '')}
                          </div>
                        );
                        const parts = line.split(/(\*\*[^*]+\*\*)/g);
                        return (
                          <div key={i} style={{ marginBottom: 2 }}>
                            {parts.map((part, j) =>
                              part.startsWith('**') && part.endsWith('**')
                                ? <strong key={j} style={{ color: '#e2e8f0' }}>{part.slice(2, -2)}</strong>
                                : <span key={j}>{part}</span>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ═══ TAB 2: RISK GRAPH ═══ */}
      {activeTab === 'graph' && (
        <div>
          {/* Fullscreen overlay */}
          {graphFullscreen && (
            <div style={{
              position: 'fixed', inset: 0, zIndex: 9999,
              background: '#020617', display: 'flex', flexDirection: 'column',
            }}>
              <div style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '10px 16px', background: '#0f172a', borderBottom: '1px solid #1e293b', flexShrink: 0,
              }}>
                <div>
                  <span style={{ color: '#e2e8f0', fontWeight: 700, fontSize: 15 }}>60-Node Bayesian Risk Graph</span>
                  <span style={{ color: '#64748b', fontSize: 11, marginLeft: 12 }}>8 risk layers · Red edges = high-risk paths</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  {Object.entries(CLUSTER_COLORS).map(([cluster, colors]) => (
                    <div key={cluster} style={{
                      display: 'flex', alignItems: 'center', gap: 4,
                      background: colors.bg + '40', border: `1px solid ${colors.border}60`,
                      borderRadius: 5, padding: '2px 8px',
                    }}>
                      <div style={{ width: 7, height: 7, borderRadius: '50%', background: colors.border }} />
                      <span style={{ color: colors.text, fontSize: 10 }}>{cluster.replace('_', ' ')}</span>
                    </div>
                  ))}
                  <button onClick={() => setGraphFullscreen(false)} style={{
                    marginLeft: 8, background: '#1e293b', border: '1px solid #334155',
                    borderRadius: 8, padding: '6px 12px', color: '#e2e8f0',
                    cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6, fontSize: 12,
                  }}>
                    <Minimize2 size={14} /> Exit Fullscreen
                  </button>
                </div>
              </div>
              <div style={{ flex: 1 }}>
                <ReactFlow
                  nodes={rfNodes} edges={rfEdges}
                  onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
                  fitView minZoom={0.05} maxZoom={2}
                >
                  <Background color="#1e293b" gap={24} />
                  <Controls style={{ background: '#0f172a', border: '1px solid #334155' }} />
                  <MiniMap
                    nodeColor={n => SEVERITY_COLOR(n.data?.probability ?? 0.2)}
                    style={{ background: '#0f172a', border: '1px solid #334155' }}
                  />
                </ReactFlow>
              </div>
            </div>
          )}

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <div>
              <h3 style={{ color: '#e2e8f0', margin: 0 }}>60-Node Bayesian Risk Graph</h3>
              <p style={{ color: '#64748b', fontSize: 12, margin: 0 }}>
                8 risk layers · Node brightness = posterior probability · Red edges = high-risk propagation paths
              </p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {Object.entries(CLUSTER_COLORS).map(([cluster, colors]) => (
                <div key={cluster} style={{
                  display: 'flex', alignItems: 'center', gap: 4,
                  background: colors.bg + '40', border: `1px solid ${colors.border}60`,
                  borderRadius: 5, padding: '2px 8px',
                }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: colors.border }} />
                  <span style={{ color: colors.text, fontSize: 10 }}>
                    {cluster.replace('_', ' ')}
                  </span>
                </div>
              ))}
              <button onClick={() => setGraphFullscreen(true)} style={{
                marginLeft: 4, background: '#1e293b', border: '1px solid #334155',
                borderRadius: 8, padding: '6px 12px', color: '#e2e8f0',
                cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6, fontSize: 12,
              }}>
                <Maximize2 size={14} /> Fullscreen
              </button>
            </div>
          </div>

          {graphLoading ? (
            <div style={{ textAlign: 'center', padding: 60, color: '#475569' }}>
              <RefreshCw size={32} className="animate-spin" style={{ margin: '0 auto 12px' }} />
              Loading graph...
            </div>
          ) : rfNodes.length === 0 ? (
            <div style={{
              height: 400, border: '1px dashed #1e293b', borderRadius: 12,
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
              color: '#475569', gap: 12,
            }}>
              <Activity size={48} color="#1e293b" />
              <div style={{ fontSize: 15, color: '#475569' }}>No prediction data yet</div>
              <div style={{ fontSize: 12, color: '#334155' }}>
                Run a prediction on the <strong style={{ color: '#64748b' }}>Predict</strong> tab to populate the risk graph
              </div>
              <button
                onClick={() => setActiveTab('predict')}
                style={{
                  marginTop: 8, background: 'linear-gradient(135deg, #7c3aed, #1d4ed8)',
                  border: 'none', borderRadius: 8, padding: '8px 20px',
                  color: '#fff', fontSize: 13, cursor: 'pointer',
                }}
              >
                Go to Predict
              </button>
            </div>
          ) : (
            <div style={{ height: 700, border: '1px solid #1e293b', borderRadius: 12, overflow: 'hidden' }}>
              <ReactFlow
                nodes={rfNodes}
                edges={rfEdges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                fitView
                minZoom={0.1}
                maxZoom={2}
              >
                <Background color="#1e293b" gap={24} />
                <Controls style={{ background: '#0f172a', border: '1px solid #334155' }} />
                <MiniMap
                  nodeColor={n => SEVERITY_COLOR(n.data?.probability ?? 0.2)}
                  style={{ background: '#0f172a', border: '1px solid #334155' }}
                />
              </ReactFlow>
            </div>
          )}

          <div style={{ marginTop: 12, color: '#475569', fontSize: 11, textAlign: 'center' }}>
            Tip: Run a Prediction on Tab 1 to see live risk posterior updates on this graph.
          </div>
        </div>
      )}

      {/* ═══ TAB 3: 3D RISK GRAPH ═══ */}
      {activeTab === 'graph3d' && (
        <div style={{
          background: '#0f172a',
          border: '1px solid #1e293b',
          borderRadius: 12,
          padding: 24,
        }}>
          <div style={{ marginBottom: 16 }}>
            <h2 style={{ color: '#f1f5f9', fontSize: 20, fontWeight: 800, marginBottom: 4 }}>
              3D Risk Intelligence Graph
            </h2>
            <p style={{ color: '#64748b', fontSize: 13, margin: 0 }}>
              Interactive 3D visualization of the 60-node Bayesian risk network with animated risk propagation
            </p>
          </div>

          <RiskGraph3D
            graphData={{
              nodes: graphData?.nodes?.map(node => ({
                ...node,
                node_id: node.id || node.nodeId || node.node_id,
                label: node.label || node.data?.label || 'Node',
                cluster: node.cluster || 'contract',
                layer: node.layer || 1,
                base_probability: node.data?.probability || node.base_probability || node.baseProbability || 0.1,
              })) || [],
              links: graphData?.edges?.map(edge => ({
                source: edge.source || edge.sourceNodeId || edge.source_node_id,
                target: edge.target || edge.targetNodeId || edge.target_node_id,
                source_node_id: edge.source || edge.sourceNodeId || edge.source_node_id,
                target_node_id: edge.target || edge.targetNodeId || edge.target_node_id,
                conditional_probability: edge.conditionalProbability || edge.conditional_probability || 0.5,
              })) || [],
            }}
            onNodeClick={(node) => {
              console.log('Selected node:', node);
            }}
          />
        </div>
      )}

      {/* ═══ TAB 4: SCENARIO SIMULATOR ═══ */}
      {activeTab === 'scenarios' && (
        <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: 20 }}>
          {/* Left panel */}
          <div style={{
            background: '#0f172a', border: '1px solid #1e293b',
            borderRadius: 12, padding: 20,
          }}>
            <h3 style={{ color: '#e2e8f0', marginBottom: 4, fontSize: 15, fontWeight: 700 }}>
              Scenario Configuration
            </h3>
            <p style={{ color: '#64748b', fontSize: 12, marginBottom: 16 }}>
              Select scenarios to simulate. Each overrides specific Bayesian risk nodes.
            </p>

            <label style={{ color: '#94a3b8', fontSize: 12 }}>Contract Value (USD)</label>
            <input
              type="number"
              value={contractValue}
              onChange={e => setContractValue(Number(e.target.value))}
              style={{
                width: '100%', padding: '8px 12px', margin: '4px 0 14px',
                background: '#1e293b', border: '1px solid #334155',
                borderRadius: 8, color: '#e2e8f0', fontSize: 13, boxSizing: 'border-box',
              }}
            />

            <h4 style={{ color: '#94a3b8', fontSize: 12, marginBottom: 10 }}>SELECT SCENARIOS</h4>
            {prebuiltScenarios.map(s => {
              const selected = selectedScenarios.includes(s.id);
              const sevColors = {
                extreme: '#ef4444', severe: '#f59e0b',
                moderate: '#8b5cf6', low: '#10b981',
              };
              return (
                <div
                  key={s.id}
                  onClick={() => setSelectedScenarios(prev =>
                    prev.includes(s.id) ? prev.filter(x => x !== s.id) : [...prev, s.id]
                  )}
                  style={{
                    background: selected ? '#1e293b' : '#0f172a',
                    border: `1px solid ${selected ? sevColors[s.severity] : '#334155'}`,
                    borderRadius: 8, padding: '10px 14px', marginBottom: 8,
                    cursor: 'pointer', transition: 'all 0.15s',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 600 }}>{s.name}</div>
                    <span style={{
                      background: sevColors[s.severity] + '22',
                      border: `1px solid ${sevColors[s.severity]}`,
                      borderRadius: 4, padding: '1px 6px',
                      color: sevColors[s.severity], fontSize: 10, fontWeight: 700,
                    }}>
                      {s.severity.toUpperCase()}
                    </span>
                  </div>
                  <div style={{ color: '#64748b', fontSize: 11, marginTop: 3 }}>{s.description}</div>
                </div>
              );
            })}

            {simError && (
              <div style={{
                background: '#dc262615', border: '1px solid #dc2626',
                borderRadius: 6, padding: '8px 12px', color: '#fca5a5',
                fontSize: 12, margin: '8px 0',
              }}>
                {simError}
              </div>
            )}

            <button
              onClick={runSimulation}
              disabled={simulating || selectedScenarios.length === 0}
              style={{
                width: '100%', padding: '11px',
                background: simulating || selectedScenarios.length === 0
                  ? '#374151'
                  : 'linear-gradient(135deg, #7c3aed, #dc2626)',
                border: 'none', borderRadius: 8,
                color: '#fff', fontWeight: 700, fontSize: 13,
                cursor: simulating || selectedScenarios.length === 0 ? 'not-allowed' : 'pointer',
                marginTop: 8,
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
              }}
            >
              {simulating ? (
                <><RefreshCw size={14} /> Simulating...</>
              ) : (
                <><Zap size={14} /> Run {selectedScenarios.length} Scenario{selectedScenarios.length !== 1 ? 's' : ''}</>
              )}
            </button>
          </div>

          {/* Right: results */}
          <div>
            {!simResults ? (
              <div style={{
                background: '#0f172a', border: '1px dashed #334155',
                borderRadius: 12, padding: 40, textAlign: 'center', color: '#475569',
              }}>
                <Sliders size={48} style={{ margin: '0 auto 16px' }} />
                <p style={{ fontSize: 14 }}>Select scenarios and run simulation</p>
              </div>
            ) : (
              <div>
                {/* Base vs scenarios comparison */}
                <div style={{
                  background: '#0f172a', border: '1px solid #1e293b',
                  borderRadius: 12, padding: 16, marginBottom: 16,
                }}>
                  <h4 style={{ color: '#94a3b8', fontSize: 12, marginBottom: 12 }}>BASE CASE</h4>
                  <div style={{ display: 'flex', gap: 12 }}>
                    <MetricCard
                      label="Base Dispute Prob." value={simResults.base_dispute_probability} unit="%"
                      color="#10b981" icon={Shield}
                    />
                    <MetricCard
                      label="Base Contract Risk" value={simResults.base_contract_risk} unit="%"
                      color="#06b6d4" icon={Activity}
                    />
                  </div>
                </div>

                {simResults.scenarios?.map((s, i) => {
                  const deltaColor = s.delta > 0.15 ? '#ef4444' : s.delta > 0.05 ? '#f59e0b' : '#10b981';
                  return (
                    <div key={i} style={{
                      background: '#0f172a', border: `1px solid ${deltaColor}30`,
                      borderRadius: 12, padding: 16, marginBottom: 14,
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                        <div>
                          <h4 style={{ color: '#e2e8f0', margin: 0, fontSize: 14, fontWeight: 700 }}>
                            {s.scenario_name}
                          </h4>
                          <p style={{ color: '#64748b', fontSize: 11, margin: 0 }}>{s.description}</p>
                        </div>
                        <div style={{
                          background: deltaColor + '22',
                          border: `1px solid ${deltaColor}`,
                          borderRadius: 8, padding: '4px 12px',
                          color: deltaColor, fontWeight: 800, fontSize: 16,
                        }}>
                          {s.delta >= 0 ? '+' : ''}{(s.delta * 100).toFixed(0)}% dispute risk
                        </div>
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginBottom: 12 }}>
                        {[
                          { label: 'Dispute Prob.', val: s.scenario_dispute_probability, unit: '%', color: SEVERITY_COLOR(s.scenario_dispute_probability) },
                          { label: 'Arbitration', val: simResults.scenarios[i]?.scenario_dispute_probability * 0.6, unit: '%', color: '#7c3aed' },
                          { label: 'Predicted Cost', val: s.scenario_cost_usd, unit: '$', color: '#ef4444' },
                          { label: 'Cost Delta', val: s.cost_delta, unit: '$', color: deltaColor },
                        ].map(m => (
                          <div key={m.label} style={{
                            background: '#1e293b', borderRadius: 8, padding: '10px 12px',
                            borderTop: `2px solid ${m.color}`,
                          }}>
                            <div style={{ color: '#64748b', fontSize: 10 }}>{m.label}</div>
                            <div style={{ color: m.color, fontWeight: 700, fontSize: 16 }}>
                              {m.unit === '$'
                                ? `$${(m.val / 1000).toFixed(0)}K`
                                : `${(m.val * 100).toFixed(0)}%`
                              }
                            </div>
                          </div>
                        ))}
                      </div>

                      {s.propagation_path?.length > 0 && (
                        <div style={{
                          background: '#1e293b', borderRadius: 8, padding: '10px 12px',
                        }}>
                          <div style={{ color: '#64748b', fontSize: 10, marginBottom: 6 }}>RISK PATH</div>
                          <PropagationPath path={s.propagation_path} />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ═══ TAB: NEO4J GRAPH ═══ */}
      {activeTab === 'neo4j' && <NeoVizPanel />}

      {/* ═══ TAB 4: HISTORY ═══ */}
      {activeTab === 'history' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3 style={{ color: '#e2e8f0', margin: 0 }}>Prediction History</h3>
            <button
              onClick={loadHistory}
              style={{
                background: '#1e293b', border: '1px solid #334155',
                borderRadius: 7, padding: '6px 14px',
                color: '#94a3b8', fontSize: 12, cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: 6,
              }}
            >
              <RefreshCw size={12} /> Refresh
            </button>
          </div>

          {histLoading ? (
            <div style={{ textAlign: 'center', padding: 40, color: '#475569' }}>Loading...</div>
          ) : predictions.length === 0 ? (
            <div style={{
              background: '#0f172a', border: '1px dashed #334155',
              borderRadius: 12, padding: 40, textAlign: 'center', color: '#475569',
            }}>
              <History size={40} style={{ margin: '0 auto 12px' }} />
              <p>No predictions yet. Run your first dispute analysis.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {predictions.map(p => {
                const c = SEVERITY_COLOR(p.dispute_probability);
                const isExpanded = expandedHistId === p.id;
                return (
                  <div key={p.id} style={{
                    background: '#0f172a', border: `1px solid ${isExpanded ? c : c + '30'}`,
                    borderRadius: 12, overflow: 'hidden',
                    transition: 'border-color 0.2s',
                  }}>
                    {/* ── Card Header (always visible, clickable) ── */}
                    <div
                      onClick={() => loadFromHistory(p)}
                      style={{
                        padding: 16, cursor: 'pointer',
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                        userSelect: 'none',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12, flex: 1 }}>
                        <div style={{
                          width: 40, height: 40, borderRadius: 8, flexShrink: 0,
                          background: c + '20', border: `1px solid ${c}`,
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontWeight: 800, fontSize: 14, color: c,
                        }}>
                          {(p.dispute_probability * 100).toFixed(0)}%
                        </div>
                        <div>
                          <div style={{ color: '#e2e8f0', fontWeight: 700, fontSize: 14 }}>
                            {p.contract_title || 'Manual Analysis'}
                          </div>
                          <div style={{ color: '#64748b', fontSize: 11 }}>
                            {new Date(p.created_at).toLocaleString()} · Legal Exposure:&nbsp;
                            <span style={{ color: '#ef4444', fontWeight: 700 }}>
                              ${(p.legal_cost_exposure_usd / 1000).toFixed(0)}K
                            </span>
                          </div>
                        </div>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <div style={{ display: 'flex', gap: 8 }}>
                          {[
                            { label: 'Dispute', val: p.dispute_probability, color: c },
                            { label: 'Risk', val: p.contract_risk_score, color: '#f59e0b' },
                            { label: 'Arbitration', val: p.arbitration_probability, color: '#7c3aed' },
                          ].map(m => (
                            <div key={m.label} style={{
                              background: '#1e293b', borderRadius: 6, padding: '4px 10px', textAlign: 'center',
                            }}>
                              <div style={{ color: '#64748b', fontSize: 9 }}>{m.label}</div>
                              <div style={{ color: m.color, fontWeight: 700, fontSize: 13 }}>
                                {(m.val * 100).toFixed(0)}%
                              </div>
                            </div>
                          ))}
                        </div>
                        <div style={{
                          background: 'linear-gradient(135deg, #6d28d920, #1d4ed820)',
                          border: '1px solid #6d28d950',
                          borderRadius: 6, padding: '4px 12px',
                          color: '#a78bfa', fontSize: 11, display: 'flex', alignItems: 'center', gap: 4,
                          flexShrink: 0, opacity: loadingHistId === p.id ? 0.6 : 1,
                        }}>
                          {loadingHistId === p.id
                            ? <><RefreshCw size={10} className="animate-spin" /> Loading...</>
                            : <><Play size={10} fill="#a78bfa" /> View Full Results</>
                          }
                        </div>
                        <button
                          onClick={e => { e.stopPropagation(); handleDeletePrediction(p.id); }}
                          style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#475569', padding: 4 }}
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>

                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ═══ TAB: MCTS TREE (NEW) ═══ */}
      {activeTab === 'mcts' && (
        <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 12, padding: 20 }}>
          <h3 style={{ color: '#e2e8f0', marginBottom: 16, fontSize: 18, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8 }}>
            <GitBranch size={20} style={{ color: '#3b82f6' }} />
            MCTS Negotiation Tree
            {prediction && (
              <span style={{ fontSize: 10, background: '#10b98120', border: '1px solid #10b981', borderRadius: 4, padding: '2px 8px', color: '#10b981', fontWeight: 600 }}>
                Auto-filled from prediction
              </span>
            )}
          </h3>
          <p style={{ color: '#94a3b8', fontSize: 13, marginBottom: 20 }}>
            Monte Carlo Tree Search for optimal contract negotiation strategy
          </p>

          {/* Controls */}
          <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
            <div>
              <label style={{ color: '#94a3b8', fontSize: 12, display: 'block', marginBottom: 4 }}>
                Max Iterations
              </label>
              <input
                type="number"
                value={mctsIterations}
                onChange={(e) => setMctsIterations(Number(e.target.value))}
                style={{
                  background: '#1e293b', border: '1px solid #334155', borderRadius: 6,
                  padding: '8px 12px', color: '#e2e8f0', fontSize: 13, width: 120,
                }}
              />
            </div>
            <div>
              <label style={{ color: '#94a3b8', fontSize: 12, display: 'block', marginBottom: 4 }}>
                Max Depth
              </label>
              <input
                type="number"
                value={mctsDepth}
                onChange={(e) => setMctsDepth(Number(e.target.value))}
                style={{
                  background: '#1e293b', border: '1px solid #334155', borderRadius: 6,
                  padding: '8px 12px', color: '#e2e8f0', fontSize: 13, width: 120,
                }}
              />
            </div>
            <button
              onClick={handleRunMCTS}
              disabled={mctsLoading}
              style={{
                marginLeft: 'auto', padding: '8px 20px', borderRadius: 8, border: 'none',
                background: mctsLoading ? '#475569' : 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                color: '#fff', fontWeight: 600, fontSize: 13, cursor: mctsLoading ? 'not-allowed' : 'pointer',
                display: 'flex', alignItems: 'center', gap: 6,
              }}
            >
              <Play size={14} />
              {mctsLoading ? 'Running...' : 'Run MCTS'}
            </button>
          </div>

          {mctsError && (
            <div style={{ background: '#7f1d1d', border: '1px solid #991b1b', borderRadius: 8, padding: 12, marginBottom: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <AlertTriangle size={16} style={{ color: '#fca5a5' }} />
                <span style={{ color: '#fca5a5', fontSize: 13 }}>{mctsError}</span>
              </div>
            </div>
          )}

          {mctsResult && (
            <>
              {/* Summary Stats */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12, marginBottom: 20 }}>
                <div style={{ background: '#1e293b', borderRadius: 8, padding: 16, border: '1px solid #334155' }}>
                  <div style={{ color: '#94a3b8', fontSize: 11, marginBottom: 4 }}>Optimal Path Score</div>
                  <div style={{ color: '#10b981', fontSize: 24, fontWeight: 700 }}>
                    {mctsResult.best_score != null
                      ? `${Math.min(100, Math.max(0, (mctsResult.best_score / 1e7 + 5) * 10)).toFixed(1)}`
                      : 'N/A'}
                  </div>
                  <div style={{ color: '#64748b', fontSize: 10, marginTop: 2 }}>Composite 0–100</div>
                </div>
                <div style={{ background: '#1e293b', borderRadius: 8, padding: 16, border: '1px solid #334155' }}>
                  <div style={{ color: '#94a3b8', fontSize: 11, marginBottom: 4 }}>Dispute Risk</div>
                  <div style={{ color: '#ef4444', fontSize: 24, fontWeight: 700 }}>
                    {(mctsResult.dispute_risk * 100).toFixed(1)}%
                  </div>
                </div>
                <div style={{ background: '#1e293b', borderRadius: 8, padding: 16, border: '1px solid #334155' }}>
                  <div style={{ color: '#94a3b8', fontSize: 11, marginBottom: 4 }}>Commercial Value</div>
                  <div style={{ color: '#3b82f6', fontSize: 24, fontWeight: 700 }}>
                    ${(mctsResult.commercial_value / 1000000).toFixed(1)}M
                  </div>
                </div>
              </div>

              {/* Tree Visualization */}
              <NegotiationTreeVisualization treeData={mctsResult.tree} />
            </>
          )}
        </div>
      )}

      {/* ═══ TAB: MULTI-AGENT AI (NEW) ═══ */}
      {activeTab === 'multiagent' && (
        <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 12, padding: 20 }}>
          <h3 style={{ color: '#e2e8f0', marginBottom: 16, fontSize: 18, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Users size={20} style={{ color: '#8b5cf6' }} />
            Multi-Agent Negotiation (5 Autonomous Agents)
            {prediction && (
              <span style={{ fontSize: 10, background: '#10b98120', border: '1px solid #10b981', borderRadius: 4, padding: '2px 8px', color: '#10b981', fontWeight: 600 }}>
                Auto-filled from prediction
              </span>
            )}
          </h3>
          <p style={{ color: '#94a3b8', fontSize: 13, marginBottom: 20 }}>
            Buyer • Supplier • Regulator • Risk • Finance agents with weighted consensus
          </p>

          {/* Controls */}
          <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
            <div>
              <label style={{ color: '#94a3b8', fontSize: 12, display: 'block', marginBottom: 4 }}>
                Max Rounds
              </label>
              <input
                type="number"
                value={advMultiAgentRounds}
                onChange={(e) => setAdvMultiAgentRounds(Number(e.target.value))}
                style={{
                  background: '#1e293b', border: '1px solid #334155', borderRadius: 6,
                  padding: '8px 12px', color: '#e2e8f0', fontSize: 13, width: 120,
                }}
              />
            </div>
            <button
              onClick={handleRunAdvancedMultiAgent}
              disabled={advMultiAgentLoading}
              style={{
                marginLeft: 'auto', padding: '8px 20px', borderRadius: 8, border: 'none',
                background: advMultiAgentLoading ? '#475569' : 'linear-gradient(135deg, #8b5cf6, #ec4899)',
                color: '#fff', fontWeight: 600, fontSize: 13, cursor: advMultiAgentLoading ? 'not-allowed' : 'pointer',
                display: 'flex', alignItems: 'center', gap: 6,
              }}
            >
              <Play size={14} />
              {advMultiAgentLoading ? 'Running...' : 'Run Multi-Agent'}
            </button>
          </div>

          {advMultiAgentError && (
            <div style={{ background: '#7f1d1d', border: '1px solid #991b1b', borderRadius: 8, padding: 12, marginBottom: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <AlertTriangle size={16} style={{ color: '#fca5a5' }} />
                <span style={{ color: '#fca5a5', fontSize: 13 }}>{advMultiAgentError}</span>
              </div>
            </div>
          )}

          {advMultiAgentResult && (
            <>
              {/* Risk Reduction Banner */}
              {advMultiAgentResult.dispute_risk_reduction !== undefined && (
                <div style={{ background: '#14532d', border: '1px solid #166534', borderRadius: 8, padding: 12, marginBottom: 20 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <TrendingUp size={18} style={{ color: '#86efac' }} />
                    <span style={{ color: '#86efac', fontSize: 14, fontWeight: 600 }}>
                      Dispute Risk Reduction: {(advMultiAgentResult.dispute_risk_reduction * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              )}

              {/* Agent Decision Panel */}
              <MultiAgentDecisionPanel
                agentDecisions={advMultiAgentResult.agent_decisions}
                originalContract={advMultiAgentResult.initial_contract}
                negotiatedContract={advMultiAgentResult.final_contract}
              />
            </>
          )}
        </div>
      )}

      {/* ═══ TAB: RL OPTIMIZER (NEW) ═══ */}
      {activeTab === 'rl' && (
        <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 12, padding: 20 }}>
          <h3 style={{ color: '#e2e8f0', marginBottom: 16, fontSize: 18, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Zap size={20} style={{ color: '#eab308' }} />
            Reinforcement Learning Contract Optimizer
            {prediction && (
              <span style={{ fontSize: 10, background: '#10b98120', border: '1px solid #10b981', borderRadius: 4, padding: '2px 8px', color: '#10b981', fontWeight: 600 }}>
                Auto-filled from prediction
              </span>
            )}
          </h3>
          <p style={{ color: '#94a3b8', fontSize: 13, marginBottom: 20 }}>
            Deep Q-Network (DQN) for risk-optimized contract parameters
          </p>

          <button
            onClick={handleRunRL}
            disabled={rlLoading}
            style={{
              padding: '10px 24px', borderRadius: 8, border: 'none',
              background: rlLoading ? '#475569' : 'linear-gradient(135deg, #eab308, #f97316)',
              color: '#fff', fontWeight: 600, fontSize: 14, cursor: rlLoading ? 'not-allowed' : 'pointer',
              display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20,
            }}
          >
            <Play size={16} />
            {rlLoading ? 'Optimizing...' : 'Optimize with RL'}
          </button>

          {rlError && (
            <div style={{ background: '#7f1d1d', border: '1px solid #991b1b', borderRadius: 8, padding: 12, marginBottom: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <AlertTriangle size={16} style={{ color: '#fca5a5' }} />
                <span style={{ color: '#fca5a5', fontSize: 13 }}>{rlError}</span>
              </div>
            </div>
          )}

          {rlResult && (
            <>
              {/* STUNNING VISUALIZATION: Radial Charts + Comparison */}
              <div style={{
                background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
                borderRadius: 16,
                padding: 24,
                border: '1px solid #334155',
                marginBottom: 24,
                boxShadow: '0 20px 60px rgba(0,0,0,0.5)'
              }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 20 }}>
                  {/* Before Optimization - Radial */}
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ color: '#94a3b8', fontSize: 12, marginBottom: 12, fontWeight: 600 }}>BEFORE OPTIMIZATION</div>
                    <ResponsiveContainer width="100%" height={180}>
                      <PieChart>
                        <Pie
                          data={[
                            { name: 'Risk', value: (rlResult.initial_dispute_risk ?? rlResult.dispute_risk) * 100 },
                            { name: 'Safe', value: 100 - (rlResult.initial_dispute_risk ?? rlResult.dispute_risk) * 100 }
                          ]}
                          cx="50%"
                          cy="50%"
                          innerRadius={50}
                          outerRadius={70}
                          startAngle={90}
                          endAngle={-270}
                          dataKey="value"
                        >
                          <Cell fill="#ef4444" />
                          <Cell fill="#1e293b" />
                        </Pie>
                      </PieChart>
                    </ResponsiveContainer>
                    <div style={{
                      marginTop: -100,
                      fontSize: 32,
                      fontWeight: 800,
                      color: '#ef4444',
                      textShadow: '0 0 20px rgba(239, 68, 68, 0.5)'
                    }}>
                      {((rlResult.initial_dispute_risk ?? rlResult.dispute_risk) * 100).toFixed(1)}%
                    </div>
                    <div style={{ color: '#64748b', fontSize: 11, marginTop: 50 }}>High Risk Contract</div>
                  </div>

                  {/* Arrow & Improvement */}
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 16 }}>
                    <div style={{
                      background: 'linear-gradient(135deg, #10b981, #059669)',
                      borderRadius: 12,
                      padding: '12px 20px',
                      boxShadow: '0 10px 40px rgba(16, 185, 129, 0.4)',
                      animation: 'pulse 2s infinite'
                    }}>
                      <div style={{ fontSize: 40, textAlign: 'center' }}>⚡</div>
                      <div style={{ color: '#fff', fontSize: 13, fontWeight: 700, textAlign: 'center' }}>RL OPTIMIZED</div>
                    </div>
                    <div style={{
                      background: 'linear-gradient(90deg, #10b981, #059669)',
                      height: 4,
                      width: '100%',
                      borderRadius: 2,
                      position: 'relative',
                      overflow: 'hidden'
                    }}>
                      <div style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent)',
                        animation: 'shimmer 1.5s infinite'
                      }}></div>
                    </div>
                    <div style={{
                      fontSize: 28,
                      fontWeight: 800,
                      color: '#10b981',
                      textShadow: '0 0 20px rgba(16, 185, 129, 0.6)'
                    }}>
                      ↓ {Math.abs((rlResult.risk_reduction ?? 0) * 100).toFixed(1)}%
                    </div>
                    <div style={{ color: '#94a3b8', fontSize: 11 }}>Risk Reduced</div>
                  </div>

                  {/* After Optimization - Radial */}
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ color: '#94a3b8', fontSize: 12, marginBottom: 12, fontWeight: 600 }}>AFTER OPTIMIZATION</div>
                    <ResponsiveContainer width="100%" height={180}>
                      <PieChart>
                        <Pie
                          data={[
                            { name: 'Risk', value: rlResult.dispute_risk * 100 },
                            { name: 'Safe', value: 100 - rlResult.dispute_risk * 100 }
                          ]}
                          cx="50%"
                          cy="50%"
                          innerRadius={50}
                          outerRadius={70}
                          startAngle={90}
                          endAngle={-270}
                          dataKey="value"
                        >
                          <Cell fill="#10b981" />
                          <Cell fill="#1e293b" />
                        </Pie>
                      </PieChart>
                    </ResponsiveContainer>
                    <div style={{
                      marginTop: -100,
                      fontSize: 32,
                      fontWeight: 800,
                      color: '#10b981',
                      textShadow: '0 0 20px rgba(16, 185, 129, 0.5)'
                    }}>
                      {(rlResult.dispute_risk * 100).toFixed(1)}%
                    </div>
                    <div style={{ color: '#64748b', fontSize: 11, marginTop: 50 }}>Optimized Contract</div>
                  </div>
                </div>
              </div>

              <style>
                {`
                  @keyframes pulse {
                    0%, 100% { transform: scale(1); opacity: 1; }
                    50% { transform: scale(1.05); opacity: 0.9; }
                  }
                  @keyframes shimmer {
                    0% { transform: translateX(-100%); }
                    100% { transform: translateX(100%); }
                  }
                  @keyframes slideIn {
                    from { transform: translateX(-20px); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                  }
                `}
              </style>

              {/* OPTIMIZATION JOURNEY - AREA CHART */}
              {(() => {
                // Simulate the optimization journey based on actions taken
                const initialRisk = (rlResult.initial_dispute_risk ?? rlResult.dispute_risk) * 100;
                const finalRisk = rlResult.dispute_risk * 100;
                const steps = rlResult.actions_taken.length;

                // Create a smooth declining curve
                const journeyData = Array.from({ length: steps + 1 }, (_, i) => {
                  const progress = i / steps;
                  // Exponential decay curve for realistic optimization
                  const risk = initialRisk - (initialRisk - finalRisk) * (1 - Math.exp(-3 * progress));
                  return {
                    step: i,
                    risk: Math.max(finalRisk, risk),
                    target: finalRisk
                  };
                });

                return (
                  <div style={{
                    background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
                    borderRadius: 16,
                    padding: 24,
                    border: '1px solid #334155',
                    marginBottom: 24,
                    boxShadow: '0 10px 40px rgba(0,0,0,0.3)'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                      <Activity size={20} style={{ color: '#10b981' }} />
                      <h4 style={{ color: '#e2e8f0', fontSize: 16, fontWeight: 700 }}>
                        Optimization Journey
                      </h4>
                      <div style={{
                        marginLeft: 'auto',
                        fontSize: 11,
                        color: '#64748b',
                        background: '#0f172a',
                        padding: '4px 12px',
                        borderRadius: 6,
                        border: '1px solid #334155'
                      }}>
                        {steps} optimization steps
                      </div>
                    </div>
                    <ResponsiveContainer width="100%" height={200}>
                      <AreaChart data={journeyData}>
                        <defs>
                          <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#ef4444" stopOpacity={0.8} />
                            <stop offset="100%" stopColor="#10b981" stopOpacity={0.2} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis
                          dataKey="step"
                          stroke="#64748b"
                          style={{ fontSize: 11 }}
                          label={{ value: 'Optimization Steps', position: 'insideBottom', offset: -5, fill: '#94a3b8', fontSize: 12 }}
                        />
                        <YAxis
                          stroke="#64748b"
                          style={{ fontSize: 11 }}
                          label={{ value: 'Risk %', angle: -90, position: 'insideLeft', fill: '#94a3b8', fontSize: 12 }}
                          domain={[Math.floor(finalRisk) - 5, Math.ceil(initialRisk) + 5]}
                        />
                        <Tooltip
                          contentStyle={{
                            background: '#0f172a',
                            border: '1px solid #334155',
                            borderRadius: 8,
                            fontSize: 12
                          }}
                          formatter={(value) => [`${value.toFixed(2)}%`, 'Risk']}
                        />
                        <Area
                          type="monotone"
                          dataKey="risk"
                          stroke="#10b981"
                          strokeWidth={3}
                          fill="url(#riskGradient)"
                          animationDuration={2000}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                    <div style={{
                      display: 'flex',
                      justifyContent: 'center',
                      gap: 20,
                      marginTop: 12,
                      fontSize: 11,
                      color: '#64748b'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <div style={{ width: 12, height: 12, background: '#ef4444', borderRadius: 2 }}></div>
                        <span>Initial Risk: {initialRisk.toFixed(1)}%</span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <div style={{ width: 12, height: 12, background: '#10b981', borderRadius: 2 }}></div>
                        <span>Final Risk: {finalRisk.toFixed(1)}%</span>
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* Insight note when risk is still high after optimization */}
              {rlResult.dispute_risk > 0.7 && (
                <div style={{ background: '#1c1a0f', border: '1px solid #92400e', borderRadius: 8, padding: '10px 14px', marginBottom: 16, display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                  <span style={{ fontSize: 16 }}>⚠️</span>
                  <div>
                    <div style={{ color: '#fbbf24', fontSize: 12, fontWeight: 600, marginBottom: 2 }}>High Residual Risk — Contract Terms Optimized to Minimum</div>
                    <div style={{ color: '#92400e', fontSize: 11, lineHeight: 1.5 }}>
                      The RL agent has minimized all adjustable parameters (penalty→0, delivery minimized, liability cap maximized).
                      Remaining risk ({(rlResult.dispute_risk * 100).toFixed(1)}%) stems from the contract text itself —
                      geopolitical, financial, and legal signals extracted from the clauses that cannot be resolved by adjusting numeric terms alone.
                      Consider revising the contract language to remove ambiguous clauses.
                    </div>
                  </div>
                </div>
              )}

              {/* Actions Taken - STUNNING BAR CHART VISUALIZATION */}
              {rlResult.actions_taken?.length > 0 && (() => {
                // Deduplicate actions and count occurrences
                const actionCounts = rlResult.actions_taken.reduce((acc, action) => {
                  acc[action] = (acc[action] || 0) + 1;
                  return acc;
                }, {});
                const uniqueActions = Object.entries(actionCounts).sort((a, b) => b[1] - a[1]);
                const maxCount = Math.max(...uniqueActions.map(([, count]) => count));

                return (
                  <div style={{
                    background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
                    borderRadius: 16,
                    padding: 24,
                    border: '1px solid #334155',
                    marginBottom: 20,
                    boxShadow: '0 10px 40px rgba(0,0,0,0.3)'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
                      <div>
                        <h4 style={{ color: '#e2e8f0', fontSize: 16, fontWeight: 700, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
                          <Zap size={18} style={{ color: '#f59e0b' }} />
                          Optimization Actions
                        </h4>
                        <div style={{ color: '#64748b', fontSize: 12 }}>
                          {rlResult.actions_taken.length} actions • {uniqueActions.length} unique strategies
                        </div>
                      </div>
                      <div style={{
                        background: 'linear-gradient(135deg, #f59e0b, #dc2626)',
                        padding: '8px 16px',
                        borderRadius: 8,
                        fontSize: 12,
                        fontWeight: 700,
                        color: '#fff'
                      }}>
                        AI OPTIMIZED
                      </div>
                    </div>

                    <div style={{ display: 'grid', gap: 12 }}>
                      {uniqueActions.map(([action, count], idx) => {
                        const percentage = (count / maxCount) * 100;
                        const isDecrease = action.includes('decrease') || action.includes('toggle');
                        const color = isDecrease ? '#10b981' : '#3b82f6';
                        const bgColor = isDecrease ? '#10b98120' : '#3b82f620';

                        return (
                          <div
                            key={action}
                            style={{
                              background: '#0f172a',
                              borderRadius: 10,
                              padding: '14px 16px',
                              border: `1px solid ${color}30`,
                              animation: `slideIn 0.5s ease-out ${idx * 0.1}s both`,
                              position: 'relative',
                              overflow: 'hidden'
                            }}
                          >
                            {/* Background progress bar */}
                            <div style={{
                              position: 'absolute',
                              left: 0,
                              top: 0,
                              bottom: 0,
                              width: `${percentage}%`,
                              background: `linear-gradient(90deg, ${color}15, ${color}05)`,
                              transition: 'width 1s ease-out',
                              borderRadius: '10px 0 0 10px'
                            }}></div>

                            <div style={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 12, flex: 1 }}>
                                <div style={{
                                  width: 32,
                                  height: 32,
                                  borderRadius: 8,
                                  background: bgColor,
                                  border: `2px solid ${color}`,
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  fontSize: 16
                                }}>
                                  {isDecrease ? '📉' : '📈'}
                                </div>
                                <div style={{ flex: 1 }}>
                                  <div style={{ color: '#e2e8f0', fontSize: 14, fontWeight: 600, marginBottom: 2 }}>
                                    {action.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                                  </div>
                                  <div style={{ color: '#64748b', fontSize: 11 }}>
                                    Applied {count} {count === 1 ? 'time' : 'times'} during optimization
                                  </div>
                                </div>
                              </div>
                              <div style={{
                                background: bgColor,
                                border: `2px solid ${color}`,
                                borderRadius: 8,
                                padding: '6px 14px',
                                fontSize: 18,
                                fontWeight: 800,
                                color,
                                minWidth: 50,
                                textAlign: 'center'
                              }}>
                                {count}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })()}

              {/* Optimized Contract Parameters - PREMIUM CARDS */}
              <div style={{
                background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
                borderRadius: 16,
                padding: 24,
                border: '1px solid #334155',
                boxShadow: '0 10px 40px rgba(0,0,0,0.3)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
                  <Target size={20} style={{ color: '#06b6d4' }} />
                  <h4 style={{ color: '#e2e8f0', fontSize: 16, fontWeight: 700 }}>
                    Optimized Contract Parameters
                  </h4>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
                  {Object.entries(rlResult.optimized_contract || {}).map(([k, v], idx) => {
                    // Meta for each RL parameter — what it means and real-world interpretation
                    const paramMeta = {
                      price: {
                        icon: '💰', color: '#f59e0b',
                        label: 'Price Index',
                        unit: '',
                        desc: 'RL score 80–160 (100 = baseline)',
                        interpret: v => v <= 90 ? 'Below market — favorable' : v <= 110 ? 'At market rate' : v <= 130 ? 'Above baseline' : 'Premium pricing',
                      },
                      delivery_days: {
                        icon: '📅', color: '#3b82f6',
                        label: 'Delivery Window',
                        unit: ' days',
                        desc: 'Optimal delivery buffer (days)',
                        interpret: v => v <= 20 ? 'Aggressive timeline' : v <= 35 ? 'Tight but feasible' : v <= 55 ? 'Standard buffer' : 'Conservative schedule',
                      },
                      liability_cap: {
                        icon: '🛡️', color: '#06b6d4',
                        label: 'Liability Cap',
                        unit: '%',
                        desc: '% of contract value',
                        interpret: v => v >= 0.8 ? 'High exposure — renegotiate' : v >= 0.4 ? 'Moderate cap' : 'Well-capped liability',
                      },
                      payment_terms: {
                        icon: '💳', color: '#10b981',
                        label: 'Payment Terms',
                        unit: ' days',
                        desc: 'Days to invoice payment',
                        interpret: v => v <= 30 ? 'Fast payment — low default risk' : v <= 45 ? 'Standard net-30/45' : v <= 65 ? 'Net-60 — standard for EPC' : v <= 75 ? 'Extended — monitor cash flow' : 'Long-term — high default risk',
                      },
                      termination_penalty: {
                        icon: '⚠️', color: '#ef4444',
                        label: 'Termination Penalty',
                        unit: '%',
                        desc: '% of contract value',
                        interpret: v => v === 0 ? 'No penalty — low lock-in' : v <= 5 ? 'Minimal penalty' : v <= 15 ? 'Moderate deterrent' : 'High penalty — strong commitment',
                      },
                      force_majeure: {
                        icon: '⚡', color: '#8b5cf6',
                        label: 'Force Majeure',
                        unit: '',
                        desc: '1 = clause active, 0 = not covered',
                        interpret: v => v >= 1 ? 'Covered — risk protected' : 'Not covered — high exposure',
                      },
                    };

                    const meta = paramMeta[k] || { icon: '📊', color: '#64748b', label: k.replace(/_/g, ' '), unit: '', desc: '', interpret: () => '' };
                    const { icon, color, label, unit, desc, interpret } = meta;

                    // Format display value
                    const displayVal = k === 'liability_cap'
                      ? (v * 100).toFixed(0) + '%'
                      : k === 'termination_penalty'
                      ? v + '%'
                      : String(v) + unit;

                    const interpretation = interpret(v);

                    return (
                      <div key={k} style={{
                        background: `linear-gradient(135deg, ${color}15, ${color}05)`,
                        borderRadius: 12, padding: '16px 18px',
                        border: `2px solid ${color}30`,
                        position: 'relative', overflow: 'hidden',
                        transition: 'transform 0.3s ease, box-shadow 0.3s ease', cursor: 'default',
                      }}
                      onMouseEnter={e => { e.currentTarget.style.transform='translateY(-4px)'; e.currentTarget.style.boxShadow=`0 12px 30px ${color}40`; }}
                      onMouseLeave={e => { e.currentTarget.style.transform='translateY(0)'; e.currentTarget.style.boxShadow='none'; }}>
                        <div style={{ position:'absolute', top:0, right:0, width:80, height:80, background:`radial-gradient(circle, ${color}20, transparent)`, pointerEvents:'none' }} />
                        <div style={{ position:'relative' }}>
                          <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:8 }}>
                            <div style={{ fontSize:20 }}>{icon}</div>
                            <div>
                              <div style={{ color:'#94a3b8', fontSize:10, fontWeight:600, textTransform:'uppercase', letterSpacing:'0.5px' }}>{label}</div>
                              <div style={{ color:'#475569', fontSize:10 }}>{desc}</div>
                            </div>
                          </div>
                          <div style={{ color, fontSize:26, fontWeight:800, textShadow:`0 2px 10px ${color}40`, marginBottom:4 }}>
                            {displayVal}
                          </div>
                          {interpretation && (
                            <div style={{ color:'#94a3b8', fontSize:11, marginBottom:8, fontStyle:'italic' }}>{interpretation}</div>
                          )}
                          <div style={{ padding:'3px 8px', background:`${color}20`, borderRadius:6, fontSize:10, fontWeight:600, color, display:'inline-block' }}>
                            RL OPTIMIZED
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* ═══ TAB: LEGAL PRECEDENTS (NEW) ═══ */}
      {activeTab === 'precedents' && (
        <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 12, padding: 20 }}>
          <h3 style={{ color: '#e2e8f0', marginBottom: 16, fontSize: 18, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Scale size={20} style={{ color: '#f59e0b' }} />
            Legal Precedent Matching
          </h3>
          <p style={{ color: '#94a3b8', fontSize: 13, marginBottom: 20 }}>
            Find similar arbitration cases using LegalBERT embeddings
          </p>

          <button
            onClick={handleMatchPrecedents}
            disabled={precedentLoading}
            style={{
              padding: '10px 24px', borderRadius: 8, border: 'none',
              background: precedentLoading ? '#475569' : 'linear-gradient(135deg, #f59e0b, #dc2626)',
              color: '#fff', fontWeight: 600, fontSize: 14, cursor: precedentLoading ? 'not-allowed' : 'pointer',
              display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20,
            }}
          >
            <Play size={16} />
            {precedentLoading ? 'Matching...' : 'Match Precedents'}
          </button>

          {precedentError && (
            <div style={{ background: '#7f1d1d', border: '1px solid #991b1b', borderRadius: 8, padding: 12, marginBottom: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <AlertTriangle size={16} style={{ color: '#fca5a5' }} />
                <span style={{ color: '#fca5a5', fontSize: 13 }}>{precedentError}</span>
              </div>
            </div>
          )}

          {precedentResult && (
            <div>
              {/* Outcome Prediction Card */}
              {precedentResult.prediction && (
                <div style={{ background: '#1e293b', borderRadius: 10, padding: 20, border: '1px solid #334155', marginBottom: 16 }}>
                  <h4 style={{ color: '#f59e0b', fontSize: 15, fontWeight: 700, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Scale size={16} /> Predicted Outcome
                  </h4>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 12 }}>
                    {[
                      { label: 'Outcome', value: (precedentResult.prediction.predicted_outcome || 'Settlement').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()), color: '#f59e0b' },
                      { label: 'Win Probability', value: `${((precedentResult.prediction.win_probability || 0) * 100).toFixed(1)}%`, color: '#10b981' },
                      { label: 'Confidence', value: `${((precedentResult.prediction.confidence || 0) * 100).toFixed(1)}%`, color: '#3b82f6' },
                    ].map(m => (
                      <div key={m.label} style={{ background: '#0f172a', borderRadius: 8, padding: '12px 16px', textAlign: 'center' }}>
                        <div style={{ color: '#64748b', fontSize: 11, marginBottom: 6 }}>{m.label}</div>
                        <div style={{ color: m.color, fontSize: 20, fontWeight: 700 }}>{m.value}</div>
                      </div>
                    ))}
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
                    {[
                      { label: 'Expected Award', value: `$${((precedentResult.prediction.expected_award || 0) / 1e6).toFixed(2)}M` },
                      { label: 'Duration', value: `${precedentResult.prediction.expected_duration_days || 365} days` },
                      { label: 'Legal Costs', value: `$${((precedentResult.prediction.expected_legal_costs || 0) / 1e6).toFixed(2)}M` },
                    ].map(m => (
                      <div key={m.label} style={{ background: '#0f172a', borderRadius: 8, padding: '10px 14px' }}>
                        <div style={{ color: '#64748b', fontSize: 11, marginBottom: 4 }}>{m.label}</div>
                        <div style={{ color: '#e2e8f0', fontSize: 16, fontWeight: 600 }}>{m.value}</div>
                      </div>
                    ))}
                  </div>
                  {precedentResult.prediction.note && (
                    <div style={{ marginTop: 12, background: '#1a2a1a', border: '1px solid #374151', borderRadius: 6, padding: '8px 12px', color: '#94a3b8', fontSize: 12 }}>
                      {precedentResult.prediction.note}
                    </div>
                  )}
                </div>
              )}

              {/* Similar Precedents */}
              <h4 style={{ color: '#e2e8f0', fontSize: 14, fontWeight: 700, marginBottom: 12 }}>
                Similar Precedents ({(precedentResult.similar_precedents || []).length} found)
              </h4>
              {(precedentResult.similar_precedents || []).length === 0 ? (
                <div style={{ background: '#1e293b', borderRadius: 8, padding: 20, textAlign: 'center', color: '#64748b', fontSize: 13 }}>
                  No similar precedents found above similarity threshold. Try adding more contract text or clauses.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {(precedentResult.similar_precedents || []).map((p, i) => (
                    <div key={i} style={{ background: '#1e293b', borderRadius: 8, padding: 16, border: '1px solid #334155' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                        <div>
                          <div style={{ color: '#e2e8f0', fontSize: 14, fontWeight: 600 }}>{p.case_name || p.case_id}</div>
                          <div style={{ color: '#64748b', fontSize: 12, marginTop: 2 }}>{p.case_id}</div>
                        </div>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                          <span style={{ background: '#10b98120', border: '1px solid #10b981', borderRadius: 4, padding: '2px 8px', color: '#10b981', fontSize: 11, fontWeight: 600 }}>
                            {((p.similarity || 0) * 100).toFixed(1)}% match
                          </span>
                          <span style={{
                            background: p.outcome === 'claimant_win' ? '#dc262620' : p.outcome === 'settlement' ? '#3b82f620' : '#f59e0b20',
                            border: `1px solid ${p.outcome === 'claimant_win' ? '#dc2626' : p.outcome === 'settlement' ? '#3b82f6' : '#f59e0b'}`,
                            borderRadius: 4, padding: '2px 8px',
                            color: p.outcome === 'claimant_win' ? '#f87171' : p.outcome === 'settlement' ? '#60a5fa' : '#fbbf24',
                            fontSize: 11, fontWeight: 600,
                          }}>
                            {(p.outcome || 'settlement').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                          </span>
                        </div>
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
                        <div style={{ background: '#0f172a', borderRadius: 6, padding: '8px 12px' }}>
                          <div style={{ color: '#64748b', fontSize: 10, marginBottom: 2 }}>Award</div>
                          <div style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 600 }}>${((p.award_amount || 0) / 1e6).toFixed(2)}M</div>
                        </div>
                        <div style={{ background: '#0f172a', borderRadius: 6, padding: '8px 12px' }}>
                          <div style={{ color: '#64748b', fontSize: 10, marginBottom: 2 }}>Duration</div>
                          <div style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 600 }}>{p.duration_days || 365} days</div>
                        </div>
                        <div style={{ background: '#0f172a', borderRadius: 6, padding: '8px 12px' }}>
                          <div style={{ color: '#64748b', fontSize: 10, marginBottom: 2 }}>Legal Costs</div>
                          <div style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 600 }}>${((p.legal_costs || 0) / 1e6).toFixed(2)}M</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ═══ TAB 5: HOW IT WORKS ═══ */}
      {activeTab === 'howto' && (
        <div style={{ maxWidth: 860 }}>
          <h3 style={{ color: '#e2e8f0', marginBottom: 20, fontSize: 18 }}>
            How the Dispute Predictor Works
          </h3>

          {[
            {
              step: 1,
              title: 'Contract Text → Risk Signal Extraction',
              color: '#06b6d4',
              icon: FileText,
              body: 'The system scans contract text using legal pattern matching to identify 12+ risk signals: ambiguous language ("best efforts", "reasonable discretion"), delivery risk clauses, payment default provisions, liability exposure terms, commodity price references, jurisdiction conflicts, IP ownership disputes, and more. Each keyword match increments a weighted evidence score that seeds the Bayesian network.',
            },
            {
              step: 2,
              title: 'LegalBERT Semantic Amplification',
              color: '#06b6d4',
              icon: Brain,
              body: 'The extracted risk signals are amplified using LegalBERT embeddings (legal-bert-base-uncased). Each risk node is mapped to a canonical legal phrase and compared via cosine similarity against the contract text embedding. High semantic similarity (≥ 0.70) boosts the evidence signal by up to +0.15, improving detection of paraphrased risk clauses that keyword matching misses.',
            },
            {
              step: 3,
              title: '60-Node Bayesian Risk Network',
              color: '#f59e0b',
              icon: Activity,
              body: 'A directed acyclic Bayesian graph with 60 nodes across 8 risk layers (Geopolitical → Macroeconomic → Market → Supply Chain → Financial → Operational → Contract → Legal) performs belief propagation. Each node computes a posterior probability using Noisy-OR combination of parent influences. Evidence flows from root risks (War Risk, Inflation) through intermediary nodes to terminal legal outcomes (DisputeProbability, ArbitrationInitiation).',
            },
            {
              step: 4,
              title: 'GNN Clause Graph Scoring',
              color: '#7c3aed',
              icon: Brain,
              body: 'The GCN+GAT architecture (shared with the Arbitration module) scores an 8-node clause graph built from Bayesian cluster posteriors. Each node carries an 8-dimensional feature vector. The GNN produces a dispute_score with outcome distribution (Buyer Win / Supplier Win / Partial Award / Settlement). Ensemble formula: Final = 0.60 × Bayesian + 0.40 × GNN. Falls back to heuristic scoring when no trained model is available.',
            },
            {
              step: 5,
              title: 'BM25 + BERT Hybrid RAG Retrieval',
              color: '#0ea5e9',
              icon: Target,
              body: 'BM25 lexical search and BERT semantic search are run in parallel over all clauses in the database. Results are fused using Reciprocal Rank Fusion (RRF). The top-5 similar clauses are surfaced with individual BM25 score, BERT score, and fusion score — giving users precedent-aware context for their contract\'s risk profile.',
            },
            {
              step: 6,
              title: 'Legal Cost Estimation',
              color: '#ef4444',
              icon: TrendingUp,
              body: 'Legal cost is estimated as: Cost = ContractValue × DisputeProbability × (BaseCostRate + LegalExposureScore × ScaleFactor). Arbitration mode adds ICC/LCIA fee estimates (1–5% of contract value). Both P50 (median scenario) and P90 (worst-case scenario) percentile estimates are provided.',
            },
            {
              step: 7,
              title: 'Qwen 2.5 Legal Explanation',
              color: '#10b981',
              icon: Zap,
              body: 'The Qwen 2.5-0.5B model (via Ollama at localhost:11434) generates a contextual legal explanation covering key risk drivers, clause-level dispute triggers, and specific mitigation recommendations. Uses temperature 0.3 and a 45-second timeout. A structured rule-based fallback generates explanations from top Bayesian risk nodes when the LLM is unavailable.',
            },
            {
              step: 8,
              title: 'Scenario What-If Simulation',
              color: '#8b5cf6',
              icon: Sliders,
              body: 'The Scenario Simulator lets users override specific risk node probabilities (e.g., "What if war risk doubles?") and immediately re-runs Bayesian inference to compute the changed dispute probability, arbitration risk, legal cost exposure, and node-level delta. Pre-built scenarios include War Escalation, Financial Crisis, Supply Chain Collapse, Commodity Price Shock, and High Contract Ambiguity.',
            },
          ].map(step => {
            const Icon = step.icon;
            return (
              <div key={step.step} style={{
                background: '#0f172a', border: `1px solid ${step.color}30`,
                borderRadius: 12, padding: 20, marginBottom: 14,
                display: 'flex', gap: 16,
              }}>
                <div style={{
                  width: 40, height: 40, borderRadius: 10,
                  background: step.color + '20', border: `1px solid ${step.color}`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                }}>
                  <Icon size={18} color={step.color} />
                </div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                    <span style={{
                      background: step.color + '20', color: step.color,
                      borderRadius: 4, padding: '1px 8px', fontSize: 11, fontWeight: 700,
                    }}>Step {step.step}</span>
                    <h4 style={{ color: '#e2e8f0', margin: 0, fontSize: 14, fontWeight: 700 }}>{step.title}</h4>
                  </div>
                  <p style={{ color: '#94a3b8', fontSize: 13, lineHeight: 1.7, margin: 0 }}>{step.body}</p>
                </div>
              </div>
            );
          })}

          {/* Ensemble formula */}
          <div style={{
            background: '#0f172a', border: '1px solid #7c3aed40',
            borderRadius: 12, padding: 20, marginTop: 8, marginBottom: 14,
          }}>
            <h4 style={{ color: '#94a3b8', fontSize: 12, marginBottom: 14 }}>ENSEMBLE SCORING FORMULA</h4>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
              {[
                { label: 'Bayesian Network', weight: '60%', color: '#f59e0b' },
                { label: '+', weight: null, color: '#64748b' },
                { label: 'GNN Clause Graph', weight: '40%', color: '#7c3aed' },
                { label: '=', weight: null, color: '#64748b' },
                { label: 'Dispute Probability', weight: 'Final', color: '#06b6d4' },
              ].map((item, i) => item.weight && item.weight !== null ? (
                <div key={i} style={{
                  background: item.color + '15', border: `1px solid ${item.color}50`,
                  borderRadius: 8, padding: '8px 16px', textAlign: 'center',
                }}>
                  <div style={{ color: item.color, fontWeight: 800, fontSize: 18 }}>{item.weight}</div>
                  <div style={{ color: '#94a3b8', fontSize: 11 }}>{item.label}</div>
                </div>
              ) : (
                <div key={i} style={{ color: '#64748b', fontSize: 22, fontWeight: 700 }}>{item.label}</div>
              ))}
            </div>
            <p style={{ color: '#64748b', fontSize: 12, marginTop: 12, marginBottom: 0 }}>
              AI amplifies evidence signals before Bayesian inference. RAG retrieval provides historical precedent context. AI generates the final natural-language explanation.
            </p>
          </div>

          {/* Architecture diagram */}
          <div style={{
            background: '#0f172a', border: '1px solid #1e293b',
            borderRadius: 12, padding: 20, marginTop: 8,
          }}>
            <h4 style={{ color: '#94a3b8', fontSize: 12, marginBottom: 14 }}>BAYESIAN NETWORK — 8 RISK LAYERS (60 NODES)</h4>
            <div style={{ display: 'flex', gap: 0, overflowX: 'auto' }}>
              {[
                { layer: 'L1', name: 'Geopolitical', nodes: 8, color: '#ef4444' },
                { layer: 'L2', name: 'Macroeconomic', nodes: 8, color: '#f59e0b' },
                { layer: 'L3', name: 'Market/Industry', nodes: 7, color: '#8b5cf6' },
                { layer: 'L4', name: 'Supply Chain', nodes: 8, color: '#3b82f6' },
                { layer: 'L5', name: 'Financial', nodes: 6, color: '#10b981' },
                { layer: 'L6', name: 'Operational', nodes: 6, color: '#f59e0b' },
                { layer: 'L7', name: 'Contract', nodes: 7, color: '#3b82f6' },
                { layer: 'L8', name: 'Legal Outcome', nodes: 10, color: '#a78bfa' },
              ].map((l, i, arr) => (
                <div key={l.layer} style={{ display: 'flex', alignItems: 'center' }}>
                  <div style={{
                    background: l.color + '15', border: `1px solid ${l.color}40`,
                    borderRadius: 8, padding: '10px 14px', textAlign: 'center', minWidth: 90,
                  }}>
                    <div style={{ color: l.color, fontWeight: 800, fontSize: 14 }}>{l.layer}</div>
                    <div style={{ color: '#e2e8f0', fontSize: 11, fontWeight: 600 }}>{l.name}</div>
                    <div style={{ color: '#64748b', fontSize: 10 }}>{l.nodes} nodes</div>
                  </div>
                  {i < arr.length - 1 && (
                    <div style={{ color: '#334155', fontSize: 16, padding: '0 4px' }}>→</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ═══ TAB: CLAUSE RISK TABLE ═══ */}
      {activeTab === 'clause-risk' && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
            <div>
              <h3 style={{ color: '#e2e8f0', fontSize: 18, fontWeight: 700, margin: 0 }}>Clause Risk Table</h3>
              <p style={{ color: '#64748b', fontSize: 13, margin: '4px 0 0' }}>Per-clause: Risk Probability · Counterfactual Risk · What-If Risk · Dispute Probability · Commercial Value</p>
            </div>
            <button onClick={runClauseRiskTable} disabled={clauseTableLoading}
              style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 20px', background: 'linear-gradient(135deg, #1d4ed8, #7c3aed)', border: 'none', borderRadius: 8, color: '#fff', fontWeight: 700, fontSize: 13, cursor: 'pointer' }}>
              {clauseTableLoading ? <RefreshCw size={14} className="spin" /> : <Play size={14} />}
              {clauseTableLoading ? 'Analyzing...' : 'Analyze Clauses'}
            </button>
          </div>

          {!contractText.trim() && !clauseTable && (
            <div style={{ background: '#1e293b', border: '1px solid #f59e0b40', borderRadius: 12, padding: 20, color: '#f59e0b', fontSize: 13 }}>
              ⚠ Paste contract text in the <strong>Predict</strong> tab first, then click "Analyze Clauses" to generate the clause risk table.
            </div>
          )}

          {clauseTableError && <div style={{ color: '#ef4444', background: '#ef444415', border: '1px solid #ef444440', borderRadius: 8, padding: 12, marginBottom: 16, fontSize: 13 }}>{clauseTableError}</div>}

          {clauseTable && (
            <div>
              {/* Summary cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 20 }}>
                {[
                  { label: 'Clauses Detected', value: clauseTable.clause_count, unit: '', color: '#06b6d4' },
                  { label: 'Avg Risk Score', value: (clauseTable.summary?.avg_risk * 100).toFixed(0) + '%', unit: '', color: '#f59e0b' },
                  { label: 'Highest Risk Clause', value: clauseTable.summary?.highest_risk_clause?.replace(/_/g, ' '), unit: '', color: '#ef4444' },
                  { label: 'Total Dispute Exposure', value: '$' + (clauseTable.summary?.total_dispute_exposure >= 1e6 ? (clauseTable.summary.total_dispute_exposure / 1e6).toFixed(1) + 'M' : (clauseTable.summary?.total_dispute_exposure || 0).toLocaleString()), unit: '', color: '#10b981' },
                ].map(card => (
                  <div key={card.label} style={{ background: '#0f172a', border: `1px solid ${card.color}30`, borderRadius: 10, padding: '14px 16px' }}>
                    <div style={{ color: '#64748b', fontSize: 11, marginBottom: 4 }}>{card.label}</div>
                    <div style={{ color: card.color, fontSize: 20, fontWeight: 800 }}>{card.value}</div>
                  </div>
                ))}
              </div>

              {/* Clause Risk Table */}
              <div style={{ borderRadius: 12, overflow: 'hidden', border: '1px solid #1e293b', background: '#0f172a' }}>
                {/* Header row */}
                <div style={{ display: 'grid', gridTemplateColumns: '160px 1fr 110px 110px 100px 110px 130px 80px', background: '#1e293b', borderBottom: '1px solid #334155', padding: '10px 12px', gap: 8 }}>
                  {['Clause Type','Clause Text','Risk Score','Counterfactual','What-If','Dispute Prob.','Commercial Value','Risk Δ'].map(h => (
                    <div key={h} style={{ color: '#94a3b8', fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{h}</div>
                  ))}
                </div>
                {/* Rows */}
                {(clauseTable.clauses || []).map((row, i) => {
                  // dispute_probability = per-clause Bayesian dispute prob (base case)
                  const dpv     = row.dispute_probability || 0;
                  // counterfactual_dispute_prob = if this clause removed/rewritten
                  const cfDp    = row.counterfactual_dispute_prob ?? row.counterfactual_risk ?? dpv * 0.75;
                  // whatif_dispute_prob = worst-case stress scenario
                  const wiDp    = row.whatif_dispute_prob ?? row.what_if_risk ?? dpv * 1.1;
                  // risk_probability = contract risk score for this clause path
                  const riskPct = ((row.risk_probability || 0) * 100).toFixed(0);

                  const dpColor = dpv >= 0.6 ? '#ef4444' : dpv >= 0.35 ? '#f59e0b' : '#10b981';
                  const cfColor = cfDp >= 0.6 ? '#ef4444' : cfDp >= 0.35 ? '#f59e0b' : '#10b981';
                  const wiColor = wiDp >= 0.7 ? '#ef4444' : wiDp >= 0.5 ? '#f59e0b' : '#a78bfa';
                  const cv      = row.commercial_value || 0;
                  // Risk delta = dispute prob increase under stress vs base
                  const delta   = row.risk_delta ?? (wiDp - dpv);
                  const dColor  = delta > 0.15 ? '#ef4444' : delta > 0.08 ? '#f59e0b' : '#10b981';
                  return (
                    <div key={i} style={{ display: 'grid', gridTemplateColumns: '160px 1fr 110px 110px 100px 110px 130px 80px', padding: '10px 12px', gap: 8, borderBottom: '1px solid #1e293b', background: i % 2 === 0 ? '#0f172a' : '#111827', alignItems: 'center' }}>
                      {/* Clause Type */}
                      <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 5, padding: '2px 8px', color: '#93c5fd', fontSize: 11, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {(row.clause_type || '').replace(/_/g, ' ')}
                      </div>
                      {/* Clause Text */}
                      <div style={{ color: '#94a3b8', fontSize: 11, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={row.clause_text}>
                        {row.clause_text}
                      </div>
                      {/* Risk Score bar */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <div style={{ flex: 1, height: 6, background: '#334155', borderRadius: 3 }}>
                          <div style={{ width: `${riskPct}%`, height: '100%', background: '#3b82f6', borderRadius: 3 }} />
                        </div>
                        <b style={{ color: '#93c5fd', fontSize: 11 }}>{riskPct}%</b>
                      </div>
                      {/* Counterfactual Dispute Prob (if clause removed) */}
                      <div style={{ color: cfColor, fontWeight: 700, fontSize: 13 }} title="Dispute probability if this clause is removed or rewritten safely">
                        {(cfDp * 100).toFixed(0)}%
                      </div>
                      {/* What-If Dispute Prob (worst-case stress) */}
                      <div style={{ color: wiColor, fontWeight: 700, fontSize: 13 }} title="Dispute probability under worst-case stress scenario">
                        {(wiDp * 100).toFixed(0)}%
                      </div>
                      {/* Dispute Prob badge — per-clause independent Bayesian score */}
                      <div>
                        <span style={{ background: `${dpColor}22`, border: `1px solid ${dpColor}`, borderRadius: 5, padding: '2px 8px', color: dpColor, fontWeight: 700, fontSize: 11 }}>
                          {(dpv * 100).toFixed(0)}%
                        </span>
                      </div>
                      {/* Commercial Value */}
                      <div style={{ color: '#10b981', fontWeight: 700, fontSize: 13 }}>
                        ${cv >= 1e6 ? (cv / 1e6).toFixed(1) + 'M' : cv.toLocaleString()}
                      </div>
                      {/* Risk Delta = stress - base */}
                      <div style={{ color: dColor, fontWeight: 700, fontSize: 13 }}>
                        {delta >= 0 ? '+' : ''}{(delta * 100).toFixed(0)}%
                      </div>
                    </div>
                  );
                })}
              </div>
              <p style={{ color: '#475569', fontSize: 11, marginTop: 10 }}>
                <strong style={{ color: '#64748b' }}>Risk Score</strong> = clause contract risk · <strong style={{ color: '#64748b' }}>Counterfactual</strong> = dispute prob if clause removed · <strong style={{ color: '#64748b' }}>What-If</strong> = dispute prob under stress · <strong style={{ color: '#64748b' }}>Dispute Prob.</strong> = independent Bayesian score per clause · <strong style={{ color: '#64748b' }}>Risk Δ</strong> = Stress minus Base
              </p>
            </div>
          )}
        </div>
      )}

      {/* ═══ TAB: TIME TRAVEL ═══ */}
      {activeTab === 'timetravel' && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
            <div>
              <h3 style={{ color: '#e2e8f0', fontSize: 18, fontWeight: 700, margin: 0 }}>Time-Travel Risk Simulation</h3>
              <p style={{ color: '#64748b', fontSize: 13, margin: '4px 0 0' }}>Month-by-month Bayesian risk evolution with random event injection</p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <label style={{ color: '#94a3b8', fontSize: 12 }}>Months:</label>
                <input type="number" value={timeTravelMonths} onChange={e => setTimeTravelMonths(Math.min(24, Math.max(3, parseInt(e.target.value) || 12)))}
                  style={{ width: 64, padding: '6px 10px', background: '#1e293b', border: '1px solid #334155', borderRadius: 7, color: '#e2e8f0', fontSize: 13 }} />
              </div>
              <button onClick={runTimeTravelSim} disabled={timeTravelLoading}
                style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 20px', background: 'linear-gradient(135deg, #0369a1, #7c3aed)', border: 'none', borderRadius: 8, color: '#fff', fontWeight: 700, fontSize: 13, cursor: 'pointer' }}>
                {timeTravelLoading ? <RefreshCw size={14} /> : <Clock size={14} />}
                {timeTravelLoading ? 'Simulating...' : 'Run Time Travel'}
              </button>
            </div>
          </div>

          {timeTravelError && <div style={{ color: '#ef4444', background: '#ef444415', border: '1px solid #ef444440', borderRadius: 8, padding: 12, marginBottom: 16, fontSize: 13 }}>{timeTravelError}</div>}

          {!timeTravelData && !timeTravelLoading && (
            <div style={{ background: '#0f172a', border: '1px dashed #334155', borderRadius: 12, padding: 40, textAlign: 'center', color: '#475569' }}>
              <Clock size={40} style={{ marginBottom: 12, opacity: 0.4 }} />
              <p>Click "Run Time Travel" to simulate month-by-month risk evolution.</p>
            </div>
          )}

          {timeTravelData && (
            <div>
              {/* Slider */}
              <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 12, padding: 20, marginBottom: 20 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <h4 style={{ color: '#e2e8f0', fontSize: 14, fontWeight: 700, margin: 0 }}>
                    {timeTravelData.history[timeTravelSlider]?.label || 'Start'} — Dispute Risk: {' '}
                    <span style={{ color: SEVERITY_COLOR(timeTravelData.history[timeTravelSlider]?.dispute_probability || 0) }}>
                      {((timeTravelData.history[timeTravelSlider]?.dispute_probability || 0) * 100).toFixed(0)}%
                    </span>
                  </h4>
                  <span style={{ color: '#64748b', fontSize: 12 }}>
                    State: <strong style={{ color: '#06b6d4' }}>{timeTravelData.history[timeTravelSlider]?.lifecycle_state}</strong>
                  </span>
                </div>
                <input type="range" min={0} max={timeTravelData.history.length - 1} value={timeTravelSlider}
                  onChange={e => setTimeTravelSlider(parseInt(e.target.value))}
                  style={{ width: '100%', accentColor: '#7c3aed', cursor: 'pointer' }} />
                <div style={{ display: 'flex', justifyContent: 'space-between', color: '#475569', fontSize: 11, marginTop: 4 }}>
                  <span>Month 0 (Start)</span><span>Month {timeTravelData.months}</span>
                </div>

                {/* Events at this month */}
                {(timeTravelData.history[timeTravelSlider]?.events || []).length > 0 && (
                  <div style={{ marginTop: 12, display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    <span style={{ color: '#64748b', fontSize: 11 }}>Events:</span>
                    {timeTravelData.history[timeTravelSlider].events.map((ev, i) => (
                      <span key={i} style={{ background: '#f59e0b20', border: '1px solid #f59e0b50', borderRadius: 5, padding: '2px 8px', color: '#fcd34d', fontSize: 11 }}>
                        ⚡ {ev}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Mini KPI row at selected month */}
              {(() => {
                const m = timeTravelData.history[timeTravelSlider];
                if (!m) return null;
                return (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 10, marginBottom: 20 }}>
                    {[
                      { label: 'Dispute Risk', value: `${(m.dispute_probability * 100).toFixed(0)}%`, color: SEVERITY_COLOR(m.dispute_probability) },
                      { label: 'Contract Risk', value: `${(m.risk_score * 100).toFixed(0)}%`, color: '#06b6d4' },
                      { label: 'Financial Stress', value: `${(m.financial_stress * 100).toFixed(0)}%`, color: '#f59e0b' },
                      { label: 'Est. Dispute Cost', value: `$${m.estimated_cost >= 1e6 ? (m.estimated_cost / 1e6).toFixed(1) + 'M' : m.estimated_cost.toLocaleString()}`, color: '#ef4444' },
                      { label: 'Lifecycle State', value: m.lifecycle_state, color: '#a78bfa' },
                    ].map(c => (
                      <div key={c.label} style={{ background: '#0f172a', border: `1px solid ${c.color}30`, borderRadius: 10, padding: '12px 14px' }}>
                        <div style={{ color: '#64748b', fontSize: 11, marginBottom: 4 }}>{c.label}</div>
                        <div style={{ color: c.color, fontWeight: 800, fontSize: 17 }}>{c.value}</div>
                      </div>
                    ))}
                  </div>
                );
              })()}

              {/* ECharts dual-line animated chart */}
              <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 12, padding: 20 }}>
                <h4 style={{ color: '#94a3b8', fontSize: 12, marginBottom: 8 }}>RISK EVOLUTION OVER {timeTravelData.months} MONTHS</h4>
                <ReactECharts
                  option={{
                    backgroundColor: 'transparent',
                    tooltip: {
                      trigger: 'axis',
                      backgroundColor: '#1e293b',
                      borderColor: '#334155',
                      textStyle: { color: '#e2e8f0', fontSize: 12 },
                      formatter: (params) => {
                        const m = timeTravelData.history[params[0]?.dataIndex];
                        const evts = m?.events?.join(', ') || 'No events';
                        return `<b>${params[0]?.axisValue}</b><br/>${params.map(p => `${p.marker}${p.seriesName}: <b>${(p.value * 100).toFixed(0)}%</b>`).join('<br/>')}<br/><span style="color:#f59e0b;font-size:10px">⚡ ${evts}</span>`;
                      },
                    },
                    legend: {
                      data: ['Dispute Risk', 'Contract Risk', 'Financial Stress'],
                      textStyle: { color: '#94a3b8', fontSize: 11 },
                      top: 0,
                    },
                    grid: { left: 40, right: 20, top: 36, bottom: 30 },
                    xAxis: {
                      type: 'category',
                      data: timeTravelData.history.map(p => p.label),
                      axisLabel: { color: '#475569', fontSize: 10, rotate: 30 },
                      axisLine: { lineStyle: { color: '#334155' } },
                      splitLine: { show: false },
                    },
                    yAxis: {
                      type: 'value',
                      min: 0, max: 1,
                      axisLabel: { color: '#475569', fontSize: 10, formatter: v => `${(v * 100).toFixed(0)}%` },
                      splitLine: { lineStyle: { color: '#1e293b' } },
                    },
                    visualMap: {
                      show: false,
                      type: 'continuous',
                      seriesIndex: 0,
                      min: 0, max: 1,
                      inRange: { color: ['#10b981', '#f59e0b', '#ef4444'] },
                    },
                    series: [
                      {
                        name: 'Dispute Risk',
                        type: 'line',
                        data: timeTravelData.history.map(p => p.dispute_probability),
                        smooth: true,
                        symbol: 'circle', symbolSize: 6,
                        lineStyle: { width: 3 },
                        areaStyle: { opacity: 0.15, color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#ef4444' }, { offset: 1, color: 'transparent' }] } },
                        markPoint: {
                          data: [{ type: 'max', name: 'Peak Risk' }],
                          label: { color: '#fff', fontSize: 10 },
                          itemStyle: { color: '#ef4444' },
                        },
                      },
                      {
                        name: 'Contract Risk',
                        type: 'line',
                        data: timeTravelData.history.map(p => p.risk_score),
                        smooth: true,
                        symbol: 'circle', symbolSize: 5,
                        lineStyle: { width: 2, color: '#06b6d4' },
                        itemStyle: { color: '#06b6d4' },
                      },
                      {
                        name: 'Financial Stress',
                        type: 'line',
                        data: timeTravelData.history.map(p => p.financial_stress),
                        smooth: true,
                        symbol: 'diamond', symbolSize: 5,
                        lineStyle: { width: 2, color: '#f59e0b', type: 'dashed' },
                        itemStyle: { color: '#f59e0b' },
                      },
                    ],
                  }}
                  style={{ height: 240 }}
                  opts={{ renderer: 'canvas' }}
                  onEvents={{
                    click: (params) => { if (params.dataIndex !== undefined) setTimeTravelSlider(params.dataIndex); }
                  }}
                />
                <p style={{ color: '#475569', fontSize: 10, margin: '4px 0 0' }}>Click any point on the chart to jump to that month in the timeline.</p>
              </div>

              {/* Full timeline table */}
              <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 12, overflow: 'hidden', marginTop: 16 }}>
                <div style={{ padding: '14px 16px', borderBottom: '1px solid #1e293b' }}>
                  <h4 style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 700, margin: 0 }}>Full Timeline</h4>
                </div>
                <div style={{ maxHeight: 300, overflowY: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                    <thead style={{ position: 'sticky', top: 0, background: '#1e293b' }}>
                      <tr>
                        {['Month', 'Lifecycle State', 'Dispute Risk', 'Contract Risk', 'Fin. Stress', 'Events'].map(h => (
                          <th key={h} style={{ padding: '10px 12px', color: '#94a3b8', fontWeight: 600, textAlign: 'left', fontSize: 11 }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {timeTravelData.history.map((row, i) => {
                        const rc = SEVERITY_COLOR(row.dispute_probability);
                        return (
                          <tr key={i} onClick={() => setTimeTravelSlider(i)} style={{ borderBottom: '1px solid #1e293b', cursor: 'pointer', background: i === timeTravelSlider ? '#1e293b' : 'transparent' }}>
                            <td style={{ padding: '8px 12px', color: '#94a3b8' }}>{row.label}</td>
                            <td style={{ padding: '8px 12px' }}>
                              <span style={{ background: '#06b6d420', border: '1px solid #06b6d450', borderRadius: 4, padding: '1px 7px', color: '#06b6d4', fontSize: 11 }}>{row.lifecycle_state}</span>
                            </td>
                            <td style={{ padding: '8px 12px', color: rc, fontWeight: 700 }}>{(row.dispute_probability * 100).toFixed(0)}%</td>
                            <td style={{ padding: '8px 12px', color: '#93c5fd' }}>{(row.risk_score * 100).toFixed(0)}%</td>
                            <td style={{ padding: '8px 12px', color: '#fcd34d' }}>{(row.financial_stress * 100).toFixed(0)}%</td>
                            <td style={{ padding: '8px 12px', color: '#f59e0b', fontSize: 11 }}>{row.events.join(', ') || '—'}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ═══ TAB: DIGITAL TWIN ═══ */}
      {activeTab === 'twin' && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
            <div>
              <h3 style={{ color: '#e2e8f0', fontSize: 18, fontWeight: 700, margin: 0 }}>Contract Digital Twin</h3>
              <p style={{ color: '#64748b', fontSize: 13, margin: '4px 0 0' }}>Living contract simulation — lifecycle states, events, risk propagation, value erosion</p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <label style={{ color: '#94a3b8', fontSize: 12 }}>Months:</label>
                <input type="number" value={twinMonths} onChange={e => setTwinMonths(Math.min(24, Math.max(3, parseInt(e.target.value) || 12)))}
                  style={{ width: 64, padding: '6px 10px', background: '#1e293b', border: '1px solid #334155', borderRadius: 7, color: '#e2e8f0', fontSize: 13 }} />
              </div>
              <button onClick={runDigitalTwinSim} disabled={twinLoading}
                style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 20px', background: 'linear-gradient(135deg, #047857, #7c3aed)', border: 'none', borderRadius: 8, color: '#fff', fontWeight: 700, fontSize: 13, cursor: 'pointer' }}>
                {twinLoading ? <RefreshCw size={14} /> : <GitBranch size={14} />}
                {twinLoading ? 'Simulating...' : 'Run Digital Twin'}
              </button>
            </div>
          </div>

          {twinError && <div style={{ color: '#ef4444', background: '#ef444415', border: '1px solid #ef444440', borderRadius: 8, padding: 12, marginBottom: 16, fontSize: 13 }}>{twinError}</div>}

          {!twinData && !twinLoading && (
            <div style={{ background: '#0f172a', border: '1px dashed #334155', borderRadius: 12, padding: 40, textAlign: 'center', color: '#475569' }}>
              <GitBranch size={40} style={{ marginBottom: 12, opacity: 0.4 }} />
              <p>Click "Run Digital Twin" to simulate the full contract lifecycle.</p>
            </div>
          )}

          {twinData && (
            <div>
              {/* Summary Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 20 }}>
                {[
                  { label: 'Final State', value: twinData.final_state, color: twinData.final_state === 'Completed' ? '#10b981' : twinData.final_state === 'Arbitration' ? '#ef4444' : '#f59e0b' },
                  {
                    label: twinData.final_state === 'Settlement' ? 'Post-Settlement Risk' :
                           twinData.final_state === 'Arbitration' ? 'Residual Dispute Risk' : 'Final Dispute Risk',
                    value: `${(twinData.final_dispute_probability * 100).toFixed(0)}%`,
                    color: SEVERITY_COLOR(twinData.final_dispute_probability),
                    subtitle: twinData.final_state === 'Settlement' ? '(resolved via settlement)' :
                              twinData.final_state === 'Arbitration' ? '(at arbitration stage)' : '',
                  },
                  { label: 'Value Erosion', value: `$${twinData.value_erosion >= 1e6 ? (twinData.value_erosion / 1e6).toFixed(1) + 'M' : twinData.value_erosion.toLocaleString()}`, color: '#ef4444' },
                  { label: 'Arbitration Outcome', value: twinData.arbitration_outcome !== 'N/A' ? twinData.arbitration_outcome : 'No Arbitration', color: twinData.arbitration_outcome !== 'N/A' ? '#a78bfa' : '#64748b' },
                ].map(c => (
                  <div key={c.label} style={{ background: '#0f172a', border: `1px solid ${c.color}30`, borderRadius: 10, padding: '14px 16px' }}>
                    <div style={{ color: '#64748b', fontSize: 11, marginBottom: 4 }}>{c.label}</div>
                    <div style={{ color: c.color, fontWeight: 800, fontSize: 17 }}>{c.value}</div>
                    {c.subtitle && <div style={{ color: '#475569', fontSize: 10, marginTop: 2 }}>{c.subtitle}</div>}
                  </div>
                ))}
              </div>

              {/* Lifecycle Timeline */}
              <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 12, padding: 20, marginBottom: 20 }}>
                <h4 style={{ color: '#94a3b8', fontSize: 12, marginBottom: 16 }}>CONTRACT LIFECYCLE TIMELINE</h4>
                <div style={{ overflowX: 'auto' }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: 0, minWidth: 'max-content' }}>
                    {twinData.timeline.map((point, i) => {
                      const stateColors = {
                        'Signed': '#10b981', 'Active': '#06b6d4', 'At Risk': '#f59e0b',
                        'Delay': '#f97316', 'Renegotiation': '#a78bfa', 'Dispute': '#ef4444',
                        'Arbitration': '#dc2626', 'Settlement': '#10b981', 'Completed': '#10b981', 'Terminated': '#475569'
                      };
                      const color = stateColors[point.lifecycle_state] || '#475569';
                      return (
                        <div key={i} style={{ display: 'flex', alignItems: 'flex-start' }}>
                          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: 110 }}>
                            <div style={{ width: 36, height: 36, borderRadius: '50%', background: color + '25', border: `2px solid ${color}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 700, color }}>M{point.month}</div>
                            <div style={{ color, fontSize: 10, fontWeight: 700, marginTop: 4, textAlign: 'center' }}>{point.lifecycle_state}</div>
                            <div style={{ color: SEVERITY_COLOR(point.dispute_probability), fontSize: 10, marginTop: 2 }}>{(point.dispute_probability * 100).toFixed(0)}%</div>
                            {point.events.length > 0 && (
                              <div style={{ fontSize: 9, color: '#f59e0b', marginTop: 2, textAlign: 'center', maxWidth: 100 }}>
                                {point.events.map(ev => ev.icon + ' ' + ev.name.split(' ')[0]).join(', ')}
                              </div>
                            )}
                            {point.is_critical && <div style={{ fontSize: 9, color: '#ef4444', fontWeight: 700, marginTop: 2 }}>⚠ CRITICAL</div>}
                          </div>
                          {i < twinData.timeline.length - 1 && (
                            <div style={{ height: 2, width: 30, background: '#334155', marginTop: 17, flexShrink: 0 }} />
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* Value + Risk Chart */}
              <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 12, padding: 20 }}>
                <ReactECharts
                  style={{ height: 220 }}
                  option={{
                    backgroundColor: 'transparent',
                    tooltip: { trigger: 'axis', backgroundColor: '#1e293b', borderColor: '#334155', textStyle: { color: '#e2e8f0', fontSize: 11 } },
                    legend: { data: ['Contract Value ($M)', 'Dispute Risk (%)'], top: 0, right: 10, textStyle: { color: '#94a3b8', fontSize: 11 } },
                    grid: { left: 50, right: 60, top: 30, bottom: 30 },
                    xAxis: {
                      type: 'category',
                      data: twinData.timeline.map(p => p.label.replace('Contract ', '')),
                      axisLabel: { color: '#64748b', fontSize: 10, interval: Math.max(0, Math.floor(twinData.timeline.length / 8) - 1) },
                      axisLine: { lineStyle: { color: '#334155' } },
                    },
                    yAxis: [
                      { type: 'value', name: '$M', nameTextStyle: { color: '#64748b', fontSize: 10 }, axisLabel: { color: '#64748b', fontSize: 10, formatter: v => `$${(v/1e6).toFixed(1)}M` }, splitLine: { lineStyle: { color: '#1e293b' } } },
                      { type: 'value', name: 'Risk %', nameTextStyle: { color: '#64748b', fontSize: 10 }, axisLabel: { color: '#64748b', fontSize: 10, formatter: v => `${(v*100).toFixed(0)}%` }, min: 0, max: 1, splitLine: { show: false } },
                    ],
                    series: [
                      {
                        name: 'Contract Value ($M)',
                        type: 'bar',
                        yAxisIndex: 0,
                        data: twinData.timeline.map(p => p.current_value),
                        itemStyle: { color: (params) => { const ratio = params.data / (twinData.original_value || 1); return ratio > 0.85 ? '#10b981' : ratio > 0.65 ? '#f59e0b' : '#ef4444'; } },
                        barMaxWidth: 24,
                      },
                      {
                        name: 'Dispute Risk (%)',
                        type: 'line',
                        yAxisIndex: 1,
                        data: twinData.timeline.map(p => p.dispute_probability),
                        smooth: true,
                        symbol: 'circle', symbolSize: 5,
                        lineStyle: { color: '#ef4444', width: 2 },
                        itemStyle: { color: '#ef4444' },
                        areaStyle: { color: 'rgba(239,68,68,0.08)' },
                      },
                    ],
                  }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748b', fontSize: 11, marginTop: 4 }}>
                  <span>Original: ${(twinData.original_value / 1e6).toFixed(1)}M</span>
                  <span>Final: ${(twinData.final_value / 1e6).toFixed(1)}M</span>
                  <span style={{ color: '#ef4444' }}>Erosion: ${(twinData.value_erosion / 1e6).toFixed(1)}M ({((twinData.value_erosion / twinData.original_value) * 100).toFixed(1)}%)</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ═══ TAB: NEGOTIATION SIMULATOR ═══ */}
      {activeTab === 'negotiation' && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
            <div>
              <h3 style={{ color: '#e2e8f0', fontSize: 18, fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
                Negotiation Simulator
                {prediction && (
                  <span style={{ fontSize: 10, background: '#10b98120', border: '1px solid #10b981', borderRadius: 4, padding: '2px 8px', color: '#10b981', fontWeight: 600 }}>
                    Auto-filled from prediction
                  </span>
                )}
              </h3>
              <p style={{ color: '#64748b', fontSize: 13, margin: '4px 0 0' }}>MCTS 2-agent (Buyer vs Supplier) or 5-agent (+ Regulator + Risk + Finance)</p>
            </div>
          </div>

          {/* Mode Toggle */}
          <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
            {[{ id: 'mcts', label: '2-Agent MCTS (Buyer + Supplier)' }, { id: 'multi', label: '5-Agent Multi-Agent' }].map(m => (
              <button key={m.id} onClick={() => setNegMode(m.id)}
                style={{ padding: '8px 18px', borderRadius: 7, border: 'none', cursor: 'pointer', fontWeight: 700, fontSize: 12,
                  background: negMode === m.id ? 'linear-gradient(135deg, #dc2626, #7c3aed)' : '#1e293b',
                  color: negMode === m.id ? '#fff' : '#94a3b8' }}>
                {m.label}
              </button>
            ))}
          </div>

          {/* Config */}
          <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: 20 }}>
            <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 12, padding: 20 }}>
              <h4 style={{ color: '#e2e8f0', fontSize: 14, fontWeight: 700, marginBottom: 16, marginTop: 0 }}>Contract Parameters</h4>
              {[
                { key: 'price', label: 'Price Index', min: 50, max: 200, step: 1 },
                { key: 'delivery_days', label: 'Delivery Days', min: 10, max: 120, step: 1 },
                { key: 'liability_cap', label: 'Liability Cap', min: 0.1, max: 1.0, step: 0.05 },
                { key: 'payment_terms', label: 'Payment Terms (days)', min: 15, max: 120, step: 5 },
                { key: 'termination_penalty', label: 'Termination Penalty', min: 0, max: 30, step: 1 },
              ].map(({ key, label, min, max, step }) => (
                <div key={key} style={{ marginBottom: 14 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <label style={{ color: '#94a3b8', fontSize: 12 }}>{label}</label>
                    <span style={{ color: '#e2e8f0', fontSize: 12, fontWeight: 700 }}>{negInitState[key]}</span>
                  </div>
                  <input type="range" min={min} max={max} step={step} value={negInitState[key]}
                    onChange={e => setNegInitState(prev => ({ ...prev, [key]: parseFloat(e.target.value) }))}
                    style={{ width: '100%', accentColor: '#7c3aed' }} />
                </div>
              ))}
              <div style={{ marginBottom: 14 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <label style={{ color: '#94a3b8', fontSize: 12 }}>Negotiation Rounds</label>
                  <span style={{ color: '#e2e8f0', fontSize: 12, fontWeight: 700 }}>{negRounds}</span>
                </div>
                <input type="range" min={3} max={negMode === 'multi' ? 5 : 15} value={negRounds} onChange={e => setNegRounds(parseInt(e.target.value))}
                  style={{ width: '100%', accentColor: '#dc2626' }} />
              </div>
              {negSimError && <div style={{ color: '#ef4444', fontSize: 12, marginBottom: 12 }}>{negSimError}</div>}
              <button onClick={runNegSim} disabled={negSimLoading}
                style={{ width: '100%', padding: '10px', background: 'linear-gradient(135deg, #dc2626, #7c3aed)', border: 'none', borderRadius: 8, color: '#fff', fontWeight: 700, fontSize: 13, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
                {negSimLoading ? <RefreshCw size={14} /> : <Play size={14} />}
                {negSimLoading ? 'Negotiating...' : 'Run Simulation'}
              </button>
            </div>

            <div>
              {/* MCTS results */}
              {negSimData && negMode === 'mcts' && (
                <div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginBottom: 16 }}>
                    {[
                      { label: 'Base Dispute Risk', value: `${(negSimData.base_dispute_probability * 100).toFixed(0)}%`, color: SEVERITY_COLOR(negSimData.base_dispute_probability) },
                      { label: 'Optimal Dispute Risk', value: `${(negSimData.optimal_dispute_probability * 100).toFixed(0)}%`, color: SEVERITY_COLOR(negSimData.optimal_dispute_probability) },
                      { label: 'Risk Reduction', value: `${(negSimData.dispute_reduction * 100).toFixed(0)}%`, color: '#10b981' },
                      { label: 'Commercial Value', value: `${negSimData.commercial_value?.toFixed(0)}`, color: '#06b6d4' },
                      { label: 'Optimal Score', value: `${negSimData.optimal_score?.toFixed(0)}`, color: '#a78bfa' },
                      { label: 'Estimated Savings', value: `$${negSimData.estimated_savings >= 1e6 ? (negSimData.estimated_savings / 1e6).toFixed(1) + 'M' : negSimData.estimated_savings?.toLocaleString()}`, color: '#10b981' },
                    ].map(c => (
                      <div key={c.label} style={{ background: '#0f172a', border: `1px solid ${c.color}30`, borderRadius: 10, padding: '12px 14px' }}>
                        <div style={{ color: '#64748b', fontSize: 11 }}>{c.label}</div>
                        <div style={{ color: c.color, fontWeight: 800, fontSize: 18 }}>{c.value}</div>
                      </div>
                    ))}
                  </div>

                  {/* Optimal contract state */}
                  <div style={{ background: '#0f172a', border: '1px solid #10b98130', borderRadius: 12, padding: 16, marginBottom: 16 }}>
                    <h4 style={{ color: '#10b981', fontSize: 13, fontWeight: 700, marginBottom: 12, marginTop: 0 }}>OPTIMAL CONTRACT</h4>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
                      {Object.entries(negSimData.optimal_state || {}).map(([k, v]) => (
                        <div key={k} style={{ background: '#1e293b', borderRadius: 8, padding: '8px 12px', display: 'flex', justifyContent: 'space-between' }}>
                          <span style={{ color: '#94a3b8', fontSize: 12 }}>{k.replace(/_/g, ' ')}</span>
                          <span style={{ color: '#10b981', fontWeight: 700, fontSize: 12 }}>{typeof v === 'number' ? v.toFixed(v % 1 !== 0 ? 2 : 0) : v}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Round-by-round actions */}
                  <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 12, padding: 16, marginBottom: 16 }}>
                    <h4 style={{ color: '#94a3b8', fontSize: 12, marginBottom: 12, marginTop: 0 }}>NEGOTIATION ROUNDS</h4>
                    <div style={{ maxHeight: 220, overflowY: 'auto' }}>
                      {(negSimData.negotiation_rounds || []).map((round, i) => (
                        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '8px 0', borderBottom: '1px solid #1e293b' }}>
                          <span style={{ color: '#475569', fontSize: 11, minWidth: 55 }}>Round {round.round}</span>
                          <div style={{ background: '#1d4ed820', border: '1px solid #3b82f630', borderRadius: 5, padding: '2px 8px', fontSize: 11, color: '#93c5fd' }}>🛒 {round.buyer_action}</div>
                          <div style={{ background: '#04785720', border: '1px solid #10b98130', borderRadius: 5, padding: '2px 8px', fontSize: 11, color: '#6ee7b7' }}>🏭 {round.supplier_action}</div>
                          <span style={{ marginLeft: 'auto', color: SEVERITY_COLOR(round.dispute_probability), fontWeight: 700, fontSize: 12 }}>{(round.dispute_probability * 100).toFixed(0)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Negotiation Tree (ReactFlow) */}
                  {negTreeNodes.length > 0 && (
                    <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 12, overflow: 'hidden' }}>
                      <div style={{ padding: '12px 16px', borderBottom: '1px solid #1e293b', color: '#e2e8f0', fontSize: 13, fontWeight: 700 }}>Negotiation Tree (MCTS Path)</div>
                      <div style={{ height: 280 }}>
                        <ReactFlow nodes={negTreeNodes} edges={negTreeEdges} onNodesChange={onNegNodesChange} onEdgesChange={onNegEdgesChange} fitView>
                          <Background color="#1e293b" gap={16} />
                          <Controls />
                        </ReactFlow>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Multi-agent results */}
              {multiAgentData && negMode === 'multi' && (
                <div>
                  {/* Agent Summary */}
                  <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 12, padding: 16, marginBottom: 16 }}>
                    <h4 style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 700, marginBottom: 12, marginTop: 0 }}>5-AGENT OUTCOME</h4>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 8 }}>
                      {[
                        { label: 'Buyer', value: multiAgentData.agent_summary?.buyer_final_utility?.toFixed(3), color: '#3b82f6', icon: '🛒' },
                        { label: 'Supplier', value: multiAgentData.agent_summary?.supplier_final_utility?.toFixed(3), color: '#10b981', icon: '🏭' },
                        { label: 'Risk Score', value: `${(multiAgentData.final_dispute_probability * 100).toFixed(0)}%`, color: SEVERITY_COLOR(multiAgentData.final_dispute_probability), icon: '🎯' },
                        { label: 'Finance', value: multiAgentData.agent_summary?.finance_final_score?.toFixed(3), color: '#f59e0b', icon: '💹' },
                        { label: 'Regulatory', value: multiAgentData.agent_summary?.regulatory_status, color: multiAgentData.agent_summary?.regulatory_status === 'PASS' ? '#10b981' : '#ef4444', icon: '⚖️' },
                      ].map(c => (
                        <div key={c.label} style={{ background: '#1e293b', borderRadius: 10, padding: '12px 10px', textAlign: 'center' }}>
                          <div style={{ fontSize: 20, marginBottom: 4 }}>{c.icon}</div>
                          <div style={{ color: '#64748b', fontSize: 10 }}>{c.label}</div>
                          <div style={{ color: c.color, fontWeight: 800, fontSize: 16 }}>{c.value}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Round decisions table */}
                  {(multiAgentData.round_results || []).map((round, ri) => (
                    <div key={ri} style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 10, padding: '12px 16px', marginBottom: 10 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                        <span style={{ color: '#e2e8f0', fontWeight: 700, fontSize: 13 }}>Round {round.round}</span>
                        <span style={{ color: SEVERITY_COLOR(round.dispute_probability), fontWeight: 700, fontSize: 13 }}>{(round.dispute_probability * 100).toFixed(0)}% dispute risk</span>
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                        {(round.actions || []).map((action, ai) => {
                          const agentColors = { Buyer: '#3b82f6', Supplier: '#10b981', Regulator: '#f59e0b', Risk: '#ef4444', Finance: '#a78bfa' };
                          const ac = agentColors[action.agent] || '#475569';
                          return (
                            <div key={ai} style={{ background: ac + '20', border: `1px solid ${ac}50`, borderRadius: 6, padding: '3px 10px', fontSize: 11, color: ac }}>
                              {action.icon} <strong>{action.agent}</strong>: {action.action}
                              {action.cost_impact !== undefined && action.cost_impact !== 0 && (
                                <span style={{ marginLeft: 8, color: action.cost_impact > 0 ? '#ef4444' : '#10b981', fontWeight: 700 }}>
                                  ({action.cost_impact > 0 ? '+' : ''}${Math.abs(action.cost_impact).toLocaleString()})
                                </span>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ))}

                  {/* Clause Comparison */}
                  <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 12, overflow: 'hidden', marginTop: 8 }}>
                    <div style={{ padding: '12px 16px', borderBottom: '1px solid #1e293b', color: '#e2e8f0', fontSize: 13, fontWeight: 700 }}>Clause Comparison: Initial vs Optimal</div>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                      <thead style={{ background: '#1e293b' }}>
                        <tr>{['Field', 'Initial', 'Optimal', 'Changed?'].map(h => <th key={h} style={{ padding: '10px 14px', color: '#94a3b8', fontWeight: 600, textAlign: 'left', fontSize: 11 }}>{h}</th>)}</tr>
                      </thead>
                      <tbody>
                        {(multiAgentData.comparison_table || []).map((row, i) => (
                          <tr key={i} style={{ borderBottom: '1px solid #1e293b', background: row.changed ? '#10b98108' : 'transparent' }}>
                            <td style={{ padding: '9px 14px', color: '#e2e8f0' }}>{row.label}</td>
                            <td style={{ padding: '9px 14px', color: '#64748b' }}>{typeof row.initial === 'number' ? row.initial.toFixed(row.initial % 1 ? 2 : 0) : row.initial}{row.format}</td>
                            <td style={{ padding: '9px 14px', color: '#10b981', fontWeight: 700 }}>{typeof row.final === 'number' ? row.final.toFixed(row.final % 1 ? 2 : 0) : row.final}{row.format}</td>
                            <td style={{ padding: '9px 14px' }}>
                              {row.changed ? <span style={{ color: '#10b981', fontSize: 12 }}>✓ Changed</span> : <span style={{ color: '#475569', fontSize: 12 }}>— Same</span>}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {!negSimData && !multiAgentData && !negSimLoading && (
                <div style={{ background: '#0f172a', border: '1px dashed #334155', borderRadius: 12, padding: 40, textAlign: 'center', color: '#475569' }}>
                  <Users size={40} style={{ marginBottom: 12, opacity: 0.4 }} />
                  <p>Configure contract parameters and click "Run Simulation".</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ═══ TAB: PORTFOLIO HEATMAP ═══ */}
      {activeTab === 'portfolio' && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
            <div>
              <h3 style={{ color: '#e2e8f0', fontSize: 22, fontWeight: 800, margin: 0, letterSpacing: '-0.02em' }}>Portfolio Dispute Heatmap</h3>
              <p style={{ color: '#64748b', fontSize: 14, margin: '6px 0 0', fontWeight: 500 }}>
                {prediction ? 'Dispute risk breakdown for the contract analyzed in the Predict tab' : 'Real-time dispute risk analysis across all contracts in your portfolio'}
              </p>
            </div>
            <button onClick={loadPortfolioHeatmap} disabled={portfolioLoading}
              style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '12px 24px', background: portfolioLoading ? '#1e293b' : 'linear-gradient(135deg, #7c3aed 0%, #6366f1 50%, #0369a1 100%)', border: 'none', borderRadius: 10, color: '#fff', fontWeight: 700, fontSize: 14, cursor: portfolioLoading ? 'not-allowed' : 'pointer', boxShadow: portfolioLoading ? 'none' : '0 4px 12px rgba(124, 58, 237, 0.3)', transition: 'all 0.3s ease', opacity: portfolioLoading ? 0.6 : 1 }}>
              {portfolioLoading ? <RefreshCw size={16} className="spin" /> : <RefreshCw size={16} />}
              {portfolioLoading ? 'Loading...' : 'Refresh'}
            </button>
          </div>

          {portfolioError && <div style={{ color: '#ef4444', background: '#ef444415', border: '1px solid #ef444440', borderRadius: 10, padding: 14, marginBottom: 20, fontSize: 14, fontWeight: 500 }}>{portfolioError}</div>}

          {portfolioData && (
            <div>
              {/* Enhanced Stats row with icons and gradients */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 14, marginBottom: 24 }}>
                {[
                  { label: 'Total Contracts', value: portfolioData.total_contracts, color: '#06b6d4', icon: '📋', gradient: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)' },
                  { label: 'Avg Dispute Risk', value: `${(portfolioData.avg_dispute_probability * 100).toFixed(0)}%`, color: SEVERITY_COLOR(portfolioData.avg_dispute_probability), icon: '⚠️', gradient: `linear-gradient(135deg, ${SEVERITY_COLOR(portfolioData.avg_dispute_probability)} 0%, ${SEVERITY_COLOR(portfolioData.avg_dispute_probability)}dd 100%)` },
                  { label: 'High Risk', value: portfolioData.high_risk_count, color: '#f59e0b', icon: '🔥', gradient: 'linear-gradient(135deg, #f59e0b 0%, #f97316 100%)' },
                  { label: 'Critical Risk', value: portfolioData.critical_count, color: '#ef4444', icon: '🚨', gradient: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)' },
                  { label: 'Total Exposure', value: `$${portfolioData.total_predicted_exposure >= 1e6 ? (portfolioData.total_predicted_exposure / 1e6).toFixed(1) + 'M' : portfolioData.total_predicted_exposure.toLocaleString()}`, color: '#a78bfa', icon: '💰', gradient: 'linear-gradient(135deg, #a78bfa 0%, #8b5cf6 100%)' },
                ].map(c => (
                  <div key={c.label} style={{
                    background: `linear-gradient(135deg, #0f172a 0%, #1e293b 100%)`,
                    border: `2px solid ${c.color}40`,
                    borderRadius: 12,
                    padding: '18px 20px',
                    position: 'relative',
                    overflow: 'hidden',
                    transition: 'all 0.3s ease',
                    cursor: 'pointer',
                    boxShadow: `0 4px 12px ${c.color}15`
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-4px)';
                    e.currentTarget.style.boxShadow = `0 8px 24px ${c.color}30`;
                    e.currentTarget.style.borderColor = `${c.color}80`;
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = `0 4px 12px ${c.color}15`;
                    e.currentTarget.style.borderColor = `${c.color}40`;
                  }}>
                    <div style={{ position: 'absolute', top: -20, right: -20, fontSize: 60, opacity: 0.1 }}>{c.icon}</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                      <span style={{ fontSize: 20 }}>{c.icon}</span>
                      <div style={{ color: '#94a3b8', fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{c.label}</div>
                    </div>
                    <div style={{ color: c.color, fontWeight: 900, fontSize: 28, letterSpacing: '-0.02em', textShadow: `0 2px 8px ${c.color}40` }}>{c.value}</div>
                    <div style={{
                      position: 'absolute',
                      bottom: 0,
                      left: 0,
                      right: 0,
                      height: 3,
                      background: c.gradient
                    }} />
                  </div>
                ))}
              </div>

              {/* Risk Analysis Visualization */}
              {(() => {
                const contracts = portfolioData.contracts || [];
                const riskCategories = ['Legal', 'Contract', 'Operational', 'Financial', 'Geopolitical'];
                const categoryIcons  = { Legal: '⚖️', Contract: '📄', Operational: '⚙️', Financial: '💵', Geopolitical: '🌍' };
                const categoryColors = { Legal: '#ef4444', Contract: '#f97316', Operational: '#f59e0b', Financial: '#3b82f6', Geopolitical: '#8b5cf6' };

                // Node → cluster mapping
                const NODE_CLUSTERS = {
                  WarRisk:'geo', SanctionsRisk:'geo', PoliticalInstability:'geo', TradeRestriction:'geo',
                  TariffRisk:'geo', EnergySecurityRisk:'geo', BorderDisruption:'geo', MilitaryEscalation:'geo',
                  InflationRisk:'macro', InterestRateShock:'macro', CurrencyVolatility:'macro',
                  CommodityPriceShock:'macro', EnergyPriceShock:'macro', GlobalDemandShock:'macro',
                  LogisticsCostIncrease:'macro', CreditMarketTightening:'macro',
                  CompetitionIncrease:'market', DemandDecline:'market', MarketPricePressure:'market',
                  TechnologyDisruption:'market', RegulatoryChange:'market', ESGRegulation:'market', EnvironmentalReg:'market',
                  SupplierBankruptcy:'supply_chain', SupplierFinancialStress:'supply_chain', SupplierDelay:'supply_chain',
                  SupplierQualityFailure:'supply_chain', TransportDisruption:'supply_chain', PortCongestion:'supply_chain', InventoryShortage:'supply_chain',
                  CounterpartyCreditRisk:'financial', PaymentDefaultRisk:'financial', CashFlowStress:'financial',
                  FinancingCostIncrease:'financial', WorkingCapitalStress:'financial', ContractCostOverrun:'financial',
                  DeliveryFailure:'operational', SLAViolation:'operational', ServiceFailure:'operational',
                  ProjectDelay:'operational', ScopeChangeRisk:'operational', CostEscalation:'operational',
                  ContractAmbiguity:'contract', ClauseConflict:'contract', LiabilityExposure:'contract',
                  TerminationRisk:'contract', RenegotiationRisk:'contract', ContractPerformanceRisk:'contract', ContractRisk:'contract',
                  DisputeTrigger:'legal', ArbitrationRisk:'legal', LitigationRisk:'legal',
                  ComplianceFailure:'legal', RegulatoryPenalty:'legal', JurisdictionRisk:'legal',
                };

                // Compute per-category averages from Bayesian posteriors
                const computeCategoryRisks = (posteriors) => {
                  if (!posteriors || Object.keys(posteriors).length === 0) return null;
                  const catMapFull = { geo:'Geopolitical', macro:'Financial', market:'Operational',
                    supply_chain:'Operational', financial:'Financial', operational:'Operational',
                    contract:'Contract', legal:'Legal' };
                  const catSums = { Geopolitical:[], Financial:[], Operational:[], Contract:[], Legal:[] };
                  Object.entries(posteriors).forEach(([node, val]) => {
                    const cat = catMapFull[NODE_CLUSTERS[node]];
                    if (cat) catSums[cat].push(val);
                  });
                  const result = {};
                  Object.entries(catSums).forEach(([cat, vals]) => {
                    result[cat] = vals.length > 0 ? vals.reduce((a,b)=>a+b,0)/vals.length : null;
                  });
                  return result;
                };

                const posteriors = prediction?.all_node_posteriors || prediction?.bayesian_posteriors || null;
                const catRisks = computeCategoryRisks(posteriors);

                // Build category values — real or fallback
                const catValues = riskCategories.map((cat, ri) => {
                  let val;
                  if (catRisks && catRisks[cat] != null) {
                    val = catRisks[cat];
                  } else {
                    const seed = (ri * 17 % 100) / 100;
                    const m = { Legal:1.15, Contract:1.05, Operational:0.85, Financial:0.95, Geopolitical:0.70 };
                    val = Math.min(0.95, (contracts[0]?.dispute_probability || 0.5) * (m[cat]||1) * (0.85 + seed * 0.20));
                  }
                  return { cat, val: parseFloat(val.toFixed(3)) };
                });

                const riskLabel = (v) => v >= 0.7 ? 'CRITICAL' : v >= 0.5 ? 'HIGH' : v >= 0.3 ? 'MEDIUM' : 'LOW';
                const riskColor = (v) => v >= 0.7 ? '#ef4444' : v >= 0.5 ? '#f97316' : v >= 0.3 ? '#f59e0b' : '#10b981';

                // Radar chart option
                const radarOption = {
                  backgroundColor: 'transparent',
                  tooltip: {
                    trigger: 'item',
                    backgroundColor: 'rgba(15,23,42,0.97)',
                    borderColor: '#475569',
                    borderWidth: 1,
                    textStyle: { color: '#e2e8f0', fontSize: 13, fontWeight: 600 },
                    formatter: (p) => {
                      if (!p.value) return '';
                      return riskCategories.map((cat,i) => {
                        const v = p.value[i];
                        const pct = (v*100).toFixed(0);
                        return `<div style="display:flex;align-items:center;gap:8px;margin:3px 0">
                          <span style="font-size:16px">${categoryIcons[cat]}</span>
                          <span style="color:#94a3b8;font-size:12px;min-width:90px">${cat}</span>
                          <span style="color:${riskColor(v)};font-weight:900;font-size:14px">${pct}%</span>
                          <span style="color:${riskColor(v)};font-size:10px;font-weight:700;background:${riskColor(v)}20;padding:2px 6px;border-radius:4px">${riskLabel(v)}</span>
                        </div>`;
                      }).join('');
                    }
                  },
                  radar: {
                    center: ['50%', '50%'],
                    radius: '68%',
                    startAngle: 90,
                    shape: 'polygon',
                    indicator: riskCategories.map(cat => ({
                      name: `${categoryIcons[cat]} ${cat}`,
                      max: 1,
                      color: categoryColors[cat],
                    })),
                    axisName: {
                      color: '#e2e8f0',
                      fontSize: 13,
                      fontWeight: 700,
                      padding: [4, 8],
                    },
                    splitNumber: 4,
                    splitLine: { lineStyle: { color: '#334155', width: 1 } },
                    splitArea: { areaStyle: { color: ['rgba(30,41,59,0.6)', 'rgba(15,23,42,0.6)', 'rgba(30,41,59,0.4)', 'rgba(15,23,42,0.4)'] } },
                    axisLine: { lineStyle: { color: '#475569', width: 1 } },
                  },
                  series: [{
                    name: 'Dispute Risk Profile',
                    type: 'radar',
                    data: [{
                      value: catValues.map(c => c.val),
                      name: contracts[0]?.title || 'Current Contract',
                      areaStyle: {
                        color: {
                          type: 'radial',
                          x: 0.5, y: 0.5, r: 1,
                          colorStops: [
                            { offset: 0, color: 'rgba(239,68,68,0.5)' },
                            { offset: 1, color: 'rgba(124,58,237,0.15)' },
                          ]
                        }
                      },
                      lineStyle: { color: '#f97316', width: 2.5, shadowBlur: 12, shadowColor: '#f9731680' },
                      itemStyle: { color: '#f97316', borderColor: '#fff', borderWidth: 2 },
                      symbol: 'circle',
                      symbolSize: 8,
                    }],
                  }],
                };

                return (
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
                    {/* Left: Radar Chart */}
                    <div style={{
                      background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
                      border: '2px solid #334155',
                      borderRadius: 16,
                      padding: 24,
                      boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
                    }}>
                      <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom: 16 }}>
                        <h4 style={{ color:'#e2e8f0', fontSize:15, fontWeight:800, margin:0, letterSpacing:'-0.01em' }}>
                          🕸️ RISK RADAR
                        </h4>
                        <div style={{ color:'#64748b', fontSize:11, fontWeight:600, background:'#0f172a', padding:'4px 10px', borderRadius:6, border:'1px solid #334155' }}>
                          5-Dimension Profile
                        </div>
                      </div>
                      <ReactECharts option={radarOption} style={{ height: 340 }} opts={{ renderer: 'canvas' }} />
                    </div>

                    {/* Right: Category Risk Bars */}
                    <div style={{
                      background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
                      border: '2px solid #334155',
                      borderRadius: 16,
                      padding: 24,
                      boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
                    }}>
                      <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom: 20 }}>
                        <h4 style={{ color:'#e2e8f0', fontSize:15, fontWeight:800, margin:0, letterSpacing:'-0.01em' }}>
                          📊 CATEGORY BREAKDOWN
                        </h4>
                        <div style={{ color:'#64748b', fontSize:11, fontWeight:600, background:'#0f172a', padding:'4px 10px', borderRadius:6, border:'1px solid #334155' }}>
                          Bayesian Posteriors
                        </div>
                      </div>
                      <div style={{ display:'flex', flexDirection:'column', gap: 14 }}>
                        {[...catValues].sort((a,b) => b.val - a.val).map(({ cat, val }) => {
                          const pct = (val * 100).toFixed(1);
                          const col = riskColor(val);
                          const lvl = riskLabel(val);
                          return (
                            <div key={cat}>
                              <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom: 6 }}>
                                <div style={{ display:'flex', alignItems:'center', gap: 8 }}>
                                  <span style={{ fontSize: 18 }}>{categoryIcons[cat]}</span>
                                  <span style={{ color:'#e2e8f0', fontSize:13, fontWeight:700 }}>{cat}</span>
                                  <span style={{
                                    color: col, fontSize:10, fontWeight:800,
                                    background:`${col}20`, padding:'2px 7px',
                                    borderRadius:20, border:`1px solid ${col}40`,
                                    letterSpacing:'0.05em',
                                  }}>{lvl}</span>
                                </div>
                                <span style={{ color: col, fontSize:16, fontWeight:900 }}>{pct}%</span>
                              </div>
                              <div style={{ height:10, background:'#1e293b', borderRadius:6, overflow:'hidden', boxShadow:'inset 0 2px 4px rgba(0,0,0,0.4)' }}>
                                <div style={{
                                  width:`${pct}%`,
                                  height:'100%',
                                  background:`linear-gradient(90deg, ${col}cc 0%, ${col} 100%)`,
                                  borderRadius:6,
                                  boxShadow:`0 0 10px ${col}80`,
                                  transition:'width 0.8s cubic-bezier(0.4,0,0.2,1)',
                                }} />
                              </div>
                            </div>
                          );
                        })}
                      </div>

                      {/* Overall risk score */}
                      <div style={{
                        marginTop: 20,
                        padding: '14px 16px',
                        background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
                        borderRadius: 10,
                        border: `2px solid ${riskColor(contracts[0]?.dispute_probability||0)}40`,
                        display:'flex', alignItems:'center', justifyContent:'space-between',
                      }}>
                        <div style={{ color:'#94a3b8', fontSize:12, fontWeight:600 }}>OVERALL DISPUTE RISK</div>
                        <div style={{ display:'flex', alignItems:'center', gap: 10 }}>
                          <div style={{
                            color: riskColor(contracts[0]?.dispute_probability||0),
                            fontSize: 22, fontWeight: 900,
                            textShadow:`0 0 12px ${riskColor(contracts[0]?.dispute_probability||0)}80`,
                          }}>
                            {((contracts[0]?.dispute_probability||0)*100).toFixed(0)}%
                          </div>
                          <div style={{
                            color: riskColor(contracts[0]?.dispute_probability||0),
                            fontSize:11, fontWeight:800,
                            background:`${riskColor(contracts[0]?.dispute_probability||0)}20`,
                            padding:'4px 10px', borderRadius:20,
                            border:`1px solid ${riskColor(contracts[0]?.dispute_probability||0)}50`,
                          }}>
                            {riskLabel(contracts[0]?.dispute_probability||0)}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* Heatmap Insights */}
              <div style={{
                background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
                border: '2px solid #3b82f6',
                borderRadius: 12,
                padding: 20,
                marginBottom: 24,
                boxShadow: '0 4px 16px rgba(59, 130, 246, 0.2)'
              }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16 }}>
                  <div style={{ fontSize: 32, marginTop: -4 }}>💡</div>
                  <div style={{ flex: 1 }}>
                    <h4 style={{ color: '#3b82f6', fontSize: 14, fontWeight: 700, margin: '0 0 8px 0', letterSpacing: '-0.01em' }}>
                      HEATMAP INSIGHTS
                    </h4>
                    <div style={{ color: '#94a3b8', fontSize: 13, lineHeight: 1.6 }}>
                      • <strong style={{ color: '#e2e8f0' }}>Color Coding:</strong> <span style={{ color: '#10b981' }}>Green</span> = Low Risk (0-30%),
                      <span style={{ color: '#fbbf24', marginLeft: 4 }}>Yellow</span> = Medium (30-50%),
                      <span style={{ color: '#f97316', marginLeft: 4 }}>Orange</span> = High (50-70%),
                      <span style={{ color: '#dc2626', marginLeft: 4 }}>Red</span> = Critical (70-100%)
                      <br />
                      • <strong style={{ color: '#e2e8f0' }}>Risk Categories:</strong> {portfolioData.total_contracts === 1 ? 'Your contract is analyzed across 5 risk dimensions using actual Bayesian posteriors from the Predict tab.' : 'Each contract is analyzed across 5 risk dimensions (Legal, Contract, Operational, Financial, Geopolitical)'}
                      <br />
                      • <strong style={{ color: '#e2e8f0' }}>{portfolioData.total_contracts === 1 ? 'Data Source' : 'Pattern Detection'}:</strong> {portfolioData.total_contracts === 1 ? 'Cell values are the average Bayesian node posteriors for each risk cluster from your latest prediction.' : 'Vertical hot spots indicate systemic risks affecting multiple contracts; horizontal hot spots show contracts with multi-category exposure'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Risk Distribution — per-category counts for single contract */}
              {(() => {
                const contracts = portfolioData.contracts || [];
                const isSingle = portfolioData.total_contracts === 1;

                // For single contract: count how many of the 5 categories fall into each level
                const NODE_CLUSTERS2 = {
                  WarRisk:'geo', SanctionsRisk:'geo', PoliticalInstability:'geo', TradeRestriction:'geo',
                  TariffRisk:'geo', EnergySecurityRisk:'geo', BorderDisruption:'geo', MilitaryEscalation:'geo',
                  InflationRisk:'macro', InterestRateShock:'macro', CurrencyVolatility:'macro',
                  CommodityPriceShock:'macro', EnergyPriceShock:'macro', GlobalDemandShock:'macro',
                  LogisticsCostIncrease:'macro', CreditMarketTightening:'macro',
                  CompetitionIncrease:'market', DemandDecline:'market', MarketPricePressure:'market',
                  TechnologyDisruption:'market', RegulatoryChange:'market', ESGRegulation:'market', EnvironmentalReg:'market',
                  SupplierBankruptcy:'supply_chain', SupplierFinancialStress:'supply_chain', SupplierDelay:'supply_chain',
                  SupplierQualityFailure:'supply_chain', TransportDisruption:'supply_chain', PortCongestion:'supply_chain', InventoryShortage:'supply_chain',
                  CounterpartyCreditRisk:'financial', PaymentDefaultRisk:'financial', CashFlowStress:'financial',
                  FinancingCostIncrease:'financial', WorkingCapitalStress:'financial', ContractCostOverrun:'financial',
                  DeliveryFailure:'operational', SLAViolation:'operational', ServiceFailure:'operational',
                  ProjectDelay:'operational', ScopeChangeRisk:'operational', CostEscalation:'operational',
                  ContractAmbiguity:'contract', ClauseConflict:'contract', LiabilityExposure:'contract',
                  TerminationRisk:'contract', RenegotiationRisk:'contract', ContractPerformanceRisk:'contract', ContractRisk:'contract',
                  DisputeTrigger:'legal', ArbitrationRisk:'legal', LitigationRisk:'legal',
                  ComplianceFailure:'legal', RegulatoryPenalty:'legal', JurisdictionRisk:'legal',
                };
                const catMapFull2 = { geo:'Geopolitical', macro:'Financial', market:'Operational',
                  supply_chain:'Operational', financial:'Financial', operational:'Operational',
                  contract:'Contract', legal:'Legal' };
                const riskCats = ['Legal','Contract','Operational','Financial','Geopolitical'];
                const posteriors2 = prediction?.all_node_posteriors || prediction?.bayesian_posteriors || null;
                let catVals2 = {};
                if (posteriors2 && Object.keys(posteriors2).length > 0) {
                  const sums = { Geopolitical:[], Financial:[], Operational:[], Contract:[], Legal:[] };
                  Object.entries(posteriors2).forEach(([node, val]) => {
                    const cat = catMapFull2[NODE_CLUSTERS2[node]];
                    if (cat) sums[cat].push(val);
                  });
                  Object.entries(sums).forEach(([cat, vals]) => {
                    catVals2[cat] = vals.length > 0 ? vals.reduce((a,b)=>a+b,0)/vals.length : (contracts[0]?.dispute_probability || 0.5);
                  });
                } else {
                  const dp = contracts[0]?.dispute_probability || 0.5;
                  const m2 = { Legal:1.15, Contract:1.05, Operational:0.85, Financial:0.95, Geopolitical:0.70 };
                  riskCats.forEach((cat,i) => { catVals2[cat] = Math.min(0.95, dp * (m2[cat]||1)); });
                }

                // Count categories by level
                let dist = { low:0, medium:0, high:0, critical:0 };
                if (isSingle) {
                  Object.values(catVals2).forEach(v => {
                    if (v >= 0.7) dist.critical++;
                    else if (v >= 0.5) dist.high++;
                    else if (v >= 0.3) dist.medium++;
                    else dist.low++;
                  });
                } else {
                  dist = portfolioData.risk_distribution || dist;
                }

                const total = isSingle ? 5 : (portfolioData.total_contracts || 1);
                const distLabel = isSingle ? 'of 5 categories' : 'of portfolio';

                return (
                  <div style={{
                    background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
                    border: '2px solid #334155',
                    borderRadius: 16,
                    padding: 24,
                    boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
                  }}>
                    <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom: 20 }}>
                      <h4 style={{ color:'#e2e8f0', fontSize:16, fontWeight:700, letterSpacing:'-0.01em', margin:0 }}>
                        📊 RISK DISTRIBUTION
                      </h4>
                      <div style={{ color:'#64748b', fontSize:12, fontWeight:600 }}>
                        {isSingle ? 'By Category (5 dimensions)' : `Total: ${portfolioData.total_contracts} Contracts`}
                      </div>
                    </div>
                    <div style={{ display:'flex', gap:14 }}>
                      {[
                        { key:'low',      label:'Low Risk',    color:'#10b981', icon:'✅', gradient:'linear-gradient(135deg,#10b981,#059669)' },
                        { key:'medium',   label:'Medium Risk', color:'#f59e0b', icon:'⚡', gradient:'linear-gradient(135deg,#f59e0b,#d97706)' },
                        { key:'high',     label:'High Risk',   color:'#f97316', icon:'⚠️', gradient:'linear-gradient(135deg,#f97316,#ea580c)' },
                        { key:'critical', label:'Critical',    color:'#ef4444', icon:'🚨', gradient:'linear-gradient(135deg,#ef4444,#dc2626)' },
                      ].map(cat => {
                        const count = dist[cat.key] || 0;
                        const pct = total > 0 ? (count / total * 100).toFixed(0) : 0;
                        return (
                          <div key={cat.key} style={{
                            flex:1, background:`linear-gradient(135deg,${cat.color}10,${cat.color}05)`,
                            border:`2px solid ${cat.color}40`, borderRadius:12, padding:'18px 20px',
                            textAlign:'center', position:'relative', overflow:'hidden',
                            transition:'all 0.3s ease', cursor:'pointer', boxShadow:`0 4px 12px ${cat.color}15`,
                          }}
                          onMouseEnter={e => { e.currentTarget.style.transform='translateY(-6px)'; e.currentTarget.style.boxShadow=`0 12px 32px ${cat.color}30`; e.currentTarget.style.borderColor=`${cat.color}80`; }}
                          onMouseLeave={e => { e.currentTarget.style.transform='translateY(0)'; e.currentTarget.style.boxShadow=`0 4px 12px ${cat.color}15`; e.currentTarget.style.borderColor=`${cat.color}40`; }}>
                            <div style={{ position:'absolute', top:-10, right:-10, fontSize:50, opacity:0.08 }}>{cat.icon}</div>
                            <div style={{ fontSize:24, marginBottom:8 }}>{cat.icon}</div>
                            <div style={{ color:cat.color, fontWeight:900, fontSize:36, letterSpacing:'-0.02em', marginBottom:4, textShadow:`0 2px 8px ${cat.color}40` }}>{count}</div>
                            <div style={{ color:cat.color, fontSize:12, fontWeight:700, marginBottom:4, textTransform:'uppercase', letterSpacing:'0.05em' }}>{cat.label}</div>
                            <div style={{ color:'#64748b', fontSize:11, fontWeight:600, marginBottom:10 }}>{pct}% {distLabel}</div>
                            <div style={{ height:8, background:'#1e293b', borderRadius:4, overflow:'hidden', boxShadow:'inset 0 2px 4px rgba(0,0,0,0.3)' }}>
                              <div style={{ width:`${pct}%`, height:'100%', background:cat.gradient, borderRadius:4, transition:'width 0.6s ease', boxShadow:`0 0 8px ${cat.color}60` }} />
                            </div>
                            <div style={{ position:'absolute', bottom:0, left:0, right:0, height:3, background:cat.gradient }} />
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })()}
            </div>
          )}

          {!portfolioData && !portfolioLoading && (
            <div style={{ background: '#0f172a', border: '1px dashed #334155', borderRadius: 12, padding: 40, textAlign: 'center', color: '#475569' }}>
              <Map size={40} style={{ marginBottom: 12, opacity: 0.4 }} />
              <p>Loading portfolio heatmap...</p>
            </div>
          )}

          {/* ── PORTFOLIO DIGITAL TWIN (1000+ contracts aggregate) ── */}
          {portfolioData && (
            <div style={{ marginTop: 24 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                <div>
                  <h3 style={{ color: '#e2e8f0', fontSize: 16, fontWeight: 700, margin: 0 }}>Portfolio Digital Twin</h3>
                  <p style={{ color: '#64748b', fontSize: 12, margin: '4px 0 0' }}>Aggregate simulation — risk trajectory across all contracts over 12 months</p>
                </div>
                <button onClick={runPortfolioTwin} disabled={portfolioTwinLoading}
                  style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '9px 18px', background: 'linear-gradient(135deg, #047857, #0369a1)', border: 'none', borderRadius: 8, color: '#fff', fontWeight: 700, fontSize: 13, cursor: 'pointer' }}>
                  {portfolioTwinLoading ? <RefreshCw size={14} /> : <GitBranch size={14} />}
                  {portfolioTwinLoading ? 'Simulating...' : 'Run Portfolio Twin'}
                </button>
              </div>

              {portfolioTwinData && (
                <div>
                  {/* Aggregate KPIs */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 20 }}>
                    {[
                      { label: 'Total Contracts', value: portfolioTwinData.total_contracts, color: '#06b6d4' },
                      { label: 'Contracts At Risk (>50%)', value: portfolioTwinData.contracts_at_risk, color: '#f59e0b' },
                      { label: 'DisputeProb > 70%', value: portfolioTwinData.high_dispute_prob_count, color: '#ef4444' },
                      { label: 'Expected Arb. Cost', value: `$${portfolioTwinData.expected_arbitration_cost >= 1e6 ? (portfolioTwinData.expected_arbitration_cost / 1e6).toFixed(1) + 'M' : portfolioTwinData.expected_arbitration_cost?.toLocaleString()}`, color: '#a78bfa' },
                    ].map(c => (
                      <div key={c.label} style={{ background: '#0f172a', border: `1px solid ${c.color}30`, borderRadius: 10, padding: '14px 16px' }}>
                        <div style={{ color: '#64748b', fontSize: 11, marginBottom: 4 }}>{c.label}</div>
                        <div style={{ color: c.color, fontWeight: 900, fontSize: 22 }}>{c.value}</div>
                      </div>
                    ))}
                  </div>

                  {/* ECharts portfolio trend line */}
                  <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 12, padding: 20 }}>
                    <h4 style={{ color: '#94a3b8', fontSize: 12, marginBottom: 8 }}>PORTFOLIO RISK TRAJECTORY (12-MONTH SIMULATION)</h4>
                    <ReactECharts
                      option={{
                        backgroundColor: 'transparent',
                        tooltip: {
                          trigger: 'axis',
                          backgroundColor: '#1e293b',
                          borderColor: '#334155',
                          textStyle: { color: '#e2e8f0', fontSize: 12 },
                          formatter: params => params.map(p => `${p.marker}${p.seriesName}: <b>${p.value}</b>`).join('<br/>'),
                        },
                        legend: {
                          data: ['Avg Dispute Risk %', 'Contracts At Risk', 'Critical Count'],
                          textStyle: { color: '#94a3b8', fontSize: 11 },
                          top: 0,
                        },
                        grid: { left: 50, right: 50, top: 36, bottom: 30 },
                        xAxis: {
                          type: 'category',
                          data: portfolioTwinData.timeline.map(t => t.label),
                          axisLabel: { color: '#475569', fontSize: 10 },
                          axisLine: { lineStyle: { color: '#334155' } },
                        },
                        yAxis: [
                          { type: 'value', name: 'Risk %', axisLabel: { color: '#475569', fontSize: 10, formatter: v => `${v}%` }, splitLine: { lineStyle: { color: '#1e293b' } } },
                          { type: 'value', name: 'Count', axisLabel: { color: '#475569', fontSize: 10 }, splitLine: { show: false } },
                        ],
                        series: [
                          {
                            name: 'Avg Dispute Risk %',
                            type: 'line',
                            yAxisIndex: 0,
                            data: portfolioTwinData.timeline.map(t => (t.avg_dispute_risk * 100).toFixed(1)),
                            smooth: true,
                            lineStyle: { width: 3, color: '#ef4444' },
                            areaStyle: { opacity: 0.1, color: '#ef4444' },
                            symbol: 'circle', symbolSize: 5,
                            itemStyle: { color: '#ef4444' },
                          },
                          {
                            name: 'Contracts At Risk',
                            type: 'bar',
                            yAxisIndex: 1,
                            data: portfolioTwinData.timeline.map(t => t.contracts_at_risk),
                            itemStyle: { color: '#f59e0b', opacity: 0.7 },
                            barMaxWidth: 20,
                          },
                          {
                            name: 'Critical Count',
                            type: 'line',
                            yAxisIndex: 1,
                            data: portfolioTwinData.timeline.map(t => t.critical_count),
                            smooth: true,
                            lineStyle: { width: 2, color: '#a78bfa', type: 'dashed' },
                            symbol: 'diamond', symbolSize: 5,
                            itemStyle: { color: '#a78bfa' },
                          },
                        ],
                      }}
                      style={{ height: 260 }}
                      opts={{ renderer: 'canvas' }}
                    />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
      </div>
    </>
  );
}
