import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Zap, Brain, Lightbulb, AlertCircle, TrendingDown,
  Loader, Shield, CheckCircle, XCircle, FileText, Info, Search,
  Table, Target, Flame, Activity, BarChart2, DollarSign, Eye,
  ChevronUp, ChevronDown, GitBranch, TrendingUp, AlertTriangle,
  Award, Users, Lock, Cpu, Star, ArrowRight, RefreshCw, Filter,
  Network, Bot, Play, ChevronRight, Maximize2, ThumbsUp, ThumbsDown,
  Swords, Handshake, Ban, Edit3, PlusCircle, MinusCircle
} from 'lucide-react';
import ReactFlow, {
  Background, Controls, MiniMap, Handle, Position, useNodesState, useEdgesState, MarkerType
} from 'reactflow';
import 'reactflow/dist/style.css';
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Legend, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, AreaChart, Area, CartesianGrid
} from 'recharts';
import api from '../utils/api';

const COLORS = {
  HIGH: '#ef4444', MEDIUM: '#f59e0b', LOW: '#10b981',
  HEADING: '#8b5cf6', DEFINITION: '#06b6d4', OBLIGATION: '#f59e0b',
  RISK: '#ef4444', RIGHT: '#10b981',
  CONTRACTOR: '#3b82f6', EMPLOYER: '#8b5cf6', SHARED: '#06b6d4',
};

const riskBg = (level) => {
  if (level === 'HIGH') return 'bg-red-900/30 text-red-400 border-red-800';
  if (level === 'MEDIUM') return 'bg-yellow-900/30 text-yellow-400 border-yellow-800';
  return 'bg-green-900/30 text-green-400 border-green-800';
};

const heatColor = (score) => {
  if (score >= 0.7) return '#ef4444';
  if (score >= 0.5) return '#f97316';
  if (score >= 0.3) return '#f59e0b';
  if (score > 0) return '#22c55e';
  return '#1e293b';
};

const TABS = [
  { id: 'process', label: 'Process', icon: Zap },
  { id: 'analysis', label: 'Analysis', icon: Brain },
  { id: 'clauses', label: 'Clause Table', icon: Table },
  { id: 'heatmap', label: 'Risk Heatmap', icon: Flame },
  { id: 'insights', label: 'AI Insights', icon: Eye },
  { id: 'deal', label: 'Deal Score', icon: Target },
  { id: 'graph', label: 'Graph View', icon: Network },
  { id: 'rl', label: 'RL Negotiation', icon: Bot },
  { id: 'explain', label: 'Explain', icon: Lightbulb },
  { id: 'breakdown', label: 'Risk Breakdown', icon: AlertCircle },
];

// ── React Flow custom nodes ──────────────────────────────────────────────────
const ContractNodeRF = ({ data }) => (
  <div style={{
    background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
    border: '2px solid rgba(234,179,8,0.7)',
    borderRadius: 16,
    padding: '14px 20px',
    minWidth: 200,
    textAlign: 'center',
    boxShadow: '0 0 30px rgba(234,179,8,0.25), 0 0 60px rgba(234,179,8,0.1)',
  }}>
    <Handle type="source" position={Position.Bottom} style={{ background: '#eab308', width: 10, height: 10, border: '2px solid #fff' }} />
    <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 8 }}>
      <div style={{ background: 'rgba(234,179,8,0.15)', border: '1px solid rgba(234,179,8,0.4)', borderRadius: 10, padding: 8 }}>
        <Zap style={{ width: 20, height: 20, color: '#eab308' }} />
      </div>
    </div>
    <p style={{ color: '#fff', fontSize: 12, fontWeight: 800, marginBottom: 4 }}>{data.label}</p>
    <div style={{ background: 'rgba(234,179,8,0.1)', border: '1px solid rgba(234,179,8,0.2)', borderRadius: 6, padding: '2px 8px', display: 'inline-block' }}>
      <span style={{ color: '#eab308', fontSize: 11, fontWeight: 700 }}>{data.clause_count} clauses</span>
    </div>
    <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: 9, marginTop: 4, letterSpacing: '0.1em' }}>CONTRACT NODE</p>
  </div>
);

const PartyNodeRF = ({ data }) => {
  const color = data.label === 'CONTRACTOR' ? '#3b82f6' : data.label === 'EMPLOYER' ? '#8b5cf6' : '#06b6d4';
  const icon = data.label === 'CONTRACTOR' ? '🏗️' : data.label === 'EMPLOYER' ? '🏢' : '🤝';
  return (
    <div style={{
      background: `linear-gradient(135deg, rgba(10,10,30,0.95), rgba(20,20,50,0.95))`,
      border: `2px solid ${color}88`,
      borderRadius: 14,
      padding: '12px 18px',
      minWidth: 150,
      textAlign: 'center',
      boxShadow: `0 0 20px ${color}33, 0 0 40px ${color}11`,
    }}>
      <Handle type="target" position={Position.Top} style={{ background: color, width: 8, height: 8, border: '2px solid #fff' }} />
      <Handle type="source" position={Position.Bottom} style={{ background: color, width: 8, height: 8, border: '2px solid #fff' }} />
      <div style={{ fontSize: 22, marginBottom: 6 }}>{icon}</div>
      <p style={{ color: '#fff', fontSize: 11, fontWeight: 800, letterSpacing: '0.05em' }}>{data.label}</p>
      <div style={{ marginTop: 6, display: 'flex', justifyContent: 'center', gap: 4 }}>
        <div style={{ background: `${color}22`, border: `1px solid ${color}44`, borderRadius: 5, padding: '2px 8px' }}>
          <span style={{ color, fontSize: 10, fontWeight: 700 }}>{data.count} clauses</span>
        </div>
      </div>
      <p style={{ color: 'rgba(255,255,255,0.3)', fontSize: 8, marginTop: 4, letterSpacing: '0.1em' }}>PARTY NODE</p>
    </div>
  );
};

const RiskNodeRF = ({ data }) => {
  const glyph = data.label === 'HIGH RISK' ? '🔴' : data.label === 'MEDIUM RISK' ? '🟡' : '🟢';
  return (
    <div style={{
      background: `linear-gradient(135deg, rgba(10,10,30,0.97), rgba(25,10,10,0.97))`,
      border: `2px solid ${data.color}88`,
      borderRadius: 14,
      padding: '12px 18px',
      minWidth: 140,
      textAlign: 'center',
      boxShadow: `0 0 25px ${data.color}44, 0 0 50px ${data.color}11`,
    }}>
      <Handle type="target" position={Position.Top} style={{ background: data.color, width: 8, height: 8, border: '2px solid #fff' }} />
      <div style={{ fontSize: 24, marginBottom: 6 }}>{glyph}</div>
      <p style={{ color: '#fff', fontSize: 11, fontWeight: 800 }}>{data.label}</p>
      <div style={{ marginTop: 6 }}>
        <div style={{ background: `${data.color}22`, border: `1px solid ${data.color}44`, borderRadius: 5, padding: '2px 8px', display: 'inline-block' }}>
          <span style={{ color: data.color, fontSize: 10, fontWeight: 700 }}>{data.count} clauses</span>
        </div>
      </div>
      <p style={{ color: 'rgba(255,255,255,0.3)', fontSize: 8, marginTop: 4, letterSpacing: '0.1em' }}>RISK NODE</p>
    </div>
  );
};

const ClauseNodeRF = ({ data, selected }) => {
  const riskColor = data.risk_level === 'HIGH' ? '#ef4444' : data.risk_level === 'MEDIUM' ? '#f59e0b' : '#10b981';
  const stColor = data.sentence_type === 'RISK' ? '#ef4444' : data.sentence_type === 'OBLIGATION' ? '#f59e0b' :
    data.sentence_type === 'RIGHT' ? '#10b981' : data.sentence_type === 'DEFINITION' ? '#06b6d4' : '#8b5cf6';
  const riskPct = data.risk_score || 0;
  return (
    <div style={{
      background: selected
        ? `linear-gradient(135deg, rgba(30,30,60,0.98), rgba(40,20,60,0.98))`
        : `linear-gradient(135deg, rgba(15,20,35,0.97), rgba(20,25,45,0.97))`,
      border: `1.5px solid ${selected ? riskColor : riskColor + '55'}`,
      borderRadius: 12,
      padding: '10px 14px',
      minWidth: 170,
      maxWidth: 200,
      boxShadow: selected ? `0 0 20px ${riskColor}55` : `0 0 8px ${riskColor}22`,
      transition: 'all 0.2s',
    }}>
      <Handle type="target" position={Position.Top} style={{ background: riskColor, width: 7, height: 7, border: '1.5px solid #fff' }} />
      <Handle type="source" position={Position.Bottom} style={{ background: '#475569', width: 6, height: 6 }} />
      <p style={{ color: '#fff', fontSize: 11, fontWeight: 700, marginBottom: 6, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{data.label}</p>
      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 6 }}>
        <span style={{ background: `${stColor}20`, border: `1px solid ${stColor}50`, color: stColor, fontSize: 9, fontWeight: 700, padding: '2px 6px', borderRadius: 4 }}>{data.sentence_type}</span>
        <span style={{ background: `${riskColor}20`, border: `1px solid ${riskColor}50`, color: riskColor, fontSize: 9, fontWeight: 700, padding: '2px 6px', borderRadius: 4 }}>{riskPct}%</span>
      </div>
      {/* Risk bar */}
      <div style={{ background: 'rgba(255,255,255,0.08)', borderRadius: 99, height: 3, overflow: 'hidden' }}>
        <div style={{ width: `${riskPct}%`, height: '100%', background: `linear-gradient(90deg, ${riskColor}88, ${riskColor})`, borderRadius: 99, transition: 'width 0.3s' }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 5 }}>
        <span style={{ color: 'rgba(255,255,255,0.35)', fontSize: 8 }}>{data.clause_type || 'Clause'}</span>
        <span style={{ color: 'rgba(255,165,0,0.7)', fontSize: 8 }}>₹{((data.financial_impact || 0) / 1000).toFixed(0)}K</span>
      </div>
    </div>
  );
};

const rfNodeTypes = {
  contractNode: ContractNodeRF,
  partyNode: PartyNodeRF,
  riskNode: RiskNodeRF,
  clauseNode: ClauseNodeRF,
};

// ── RL Action config ─────────────────────────────────────────────────────────
const ACTION_CONFIG = {
  accept:                  { icon: ThumbsUp,     color: '#10b981', bg: 'bg-green-900/20',  border: 'border-green-800/40' },
  reject:                  { icon: Ban,           color: '#ef4444', bg: 'bg-red-900/20',    border: 'border-red-800/40' },
  modify_clause:           { icon: Edit3,         color: '#3b82f6', bg: 'bg-blue-900/20',   border: 'border-blue-800/40' },
  add_cap:                 { icon: Shield,        color: '#8b5cf6', bg: 'bg-purple-900/20', border: 'border-purple-800/40' },
  share_risk:              { icon: Handshake,     color: '#06b6d4', bg: 'bg-cyan-900/20',   border: 'border-cyan-800/40' },
  delay_penalty_reduction: { icon: MinusCircle,   color: '#f59e0b', bg: 'bg-yellow-900/20', border: 'border-yellow-800/40' },
};

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-slate-800 border border-slate-600 rounded-lg p-3 shadow-xl">
      <p className="text-slate-300 text-xs mb-1">{label}</p>
      {payload.map((p, i) => (
        <p key={i} className="text-sm font-bold" style={{ color: p.color || p.fill }}>{p.name}: {p.value}</p>
      ))}
    </div>
  );
};

export default function RRIE() {
  const navigate = useNavigate();
  const [contracts, setContracts] = useState([]);
  const [selectedContractId, setSelectedContractId] = useState('');
  const [processing, setProcessing] = useState(false);
  const [processResult, setProcessResult] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [clauseTable, setClauseTable] = useState([]);
  const [loadingClauses, setLoadingClauses] = useState(false);
  const [clauseSort, setClauseSort] = useState({ col: 'risk_score', dir: 'desc' });
  const [clauseFilter, setClauseFilter] = useState('');
  const [heatmap, setHeatmap] = useState(null);
  const [loadingHeatmap, setLoadingHeatmap] = useState(false);
  const [insights, setInsights] = useState(null);
  const [loadingInsights, setLoadingInsights] = useState(false);
  const [dealScore, setDealScore] = useState(null);
  const [loadingDeal, setLoadingDeal] = useState(false);
  const [allClauses, setAllClauses] = useState([]);
  const [selectedClause, setSelectedClause] = useState(null);
  const [selectedClauseData, setSelectedClauseData] = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [loadingExplanation, setLoadingExplanation] = useState(false);
  const [riskBreakdown, setRiskBreakdown] = useState(null);
  const [loadingBreakdown, setLoadingBreakdown] = useState(false);
  const [graphData, setGraphData] = useState(null);
  const [loadingGraph, setLoadingGraph] = useState(false);
  const [rfNodes, setRfNodes, onNodesChange] = useNodesState([]);
  const [rfEdges, setRfEdges, onEdgesChange] = useEdgesState([]);
  const [rlData, setRlData] = useState(null);
  const [loadingRL, setLoadingRL] = useState(false);
  const [rlSimCount, setRlSimCount] = useState(500);
  const [rlFilter, setRlFilter] = useState('');
  const [rlSelectedClause, setRlSelectedClause] = useState(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [selectedNode, setSelectedNode] = useState(null);
  const [graphFilter, setGraphFilter] = useState('all');
  const [tab, setTab] = useState('process');

  const onNodeClick = useCallback((_, node) => setSelectedNode(node), []);
  const onPaneClick = useCallback(() => setSelectedNode(null), []);

  useEffect(() => {
    api.get('/contracts/list')
      .then(r => setContracts(r.data?.contracts || r.data || []))
      .catch(e => console.error('Failed to load contracts:', e));
  }, []);

  // Load clauses for explain/breakdown whenever contract changes
  useEffect(() => {
    if (!selectedContractId) return;
    api.get(`/rrie/contracts/${selectedContractId}/clauses`)
      .then(r => setAllClauses(r.data?.clauses || []))
      .catch(() => {});
  }, [selectedContractId]);

  useEffect(() => {
    if (!selectedContractId) return;
    if (tab === 'analysis' && !analysis) loadAnalysis();
    if (tab === 'clauses' && clauseTable.length === 0) loadClauseTable();
    if (tab === 'heatmap' && !heatmap) loadHeatmap();
    if (tab === 'insights' && !insights) loadInsights();
    if (tab === 'deal' && !dealScore) loadDealScore();
    if (tab === 'graph' && !graphData) loadGraph();
    if (tab === 'rl' && !rlData) loadRL();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, selectedContractId]);

  const handleContractChange = (id) => {
    setSelectedContractId(id);
    setAnalysis(null); setClauseTable([]); setHeatmap(null);
    setInsights(null); setDealScore(null); setAllClauses([]);
    setExplanation(null); setRiskBreakdown(null);
    setSelectedClause(null); setSelectedClauseData(null);
    setProcessResult(null); setGraphData(null);
    setRfNodes([]); setRfEdges([]); setRlData(null);
  };

  const handleProcessRRIE = async () => {
    if (!selectedContractId) return;
    setProcessing(true); setProcessResult(null);
    try {
      const res = await api.post(`/rrie/contracts/${selectedContractId}/process`);
      if (res.data.success) {
        setProcessResult(res.data);
        setAnalysis(null); setClauseTable([]); setHeatmap(null);
        setInsights(null); setDealScore(null);
        // reload clauses
        api.get(`/rrie/contracts/${selectedContractId}/clauses`)
          .then(r => setAllClauses(r.data?.clauses || []));
      }
    } catch (e) {
      console.error('RRIE processing failed:', e);
    } finally {
      setProcessing(false);
    }
  };

  const loadAnalysis = async () => {
    if (!selectedContractId) return;
    setLoadingAnalysis(true);
    try {
      const res = await api.get(`/rrie/contracts/${selectedContractId}/analysis`);
      setAnalysis(res.data);
    } catch (e) { console.error(e); } finally { setLoadingAnalysis(false); }
  };

  const loadClauseTable = async () => {
    if (!selectedContractId) return;
    setLoadingClauses(true);
    try {
      const res = await api.get(`/rrie/contracts/${selectedContractId}/clauses`);
      const clauses = res.data?.clauses || [];
      setClauseTable(clauses);
      setAllClauses(clauses);
    } catch (e) { console.error(e); } finally { setLoadingClauses(false); }
  };

  const loadHeatmap = async () => {
    if (!selectedContractId) return;
    setLoadingHeatmap(true);
    try {
      const res = await api.get(`/rrie/contracts/${selectedContractId}/heatmap`);
      setHeatmap(res.data);
    } catch (e) { console.error(e); } finally { setLoadingHeatmap(false); }
  };

  const loadInsights = async () => {
    if (!selectedContractId) return;
    setLoadingInsights(true);
    try {
      const res = await api.get(`/rrie/contracts/${selectedContractId}/insights`);
      setInsights(res.data);
    } catch (e) { console.error(e); } finally { setLoadingInsights(false); }
  };

  const loadDealScore = async () => {
    if (!selectedContractId) return;
    setLoadingDeal(true);
    try {
      const res = await api.get(`/rrie/contracts/${selectedContractId}/deal-score`);
      setDealScore(res.data);
    } catch (e) { console.error(e); } finally { setLoadingDeal(false); }
  };

  const loadGraph = async () => {
    if (!selectedContractId) return;
    setLoadingGraph(true);
    try {
      const res = await api.get(`/rrie/contracts/${selectedContractId}/graph`);
      setGraphData(res.data);
      setRfNodes(res.data.nodes || []);
      setRfEdges(res.data.edges || []);
    } catch (e) { console.error(e); } finally { setLoadingGraph(false); }
  };

  const loadRL = async (sims) => {
    if (!selectedContractId) return;
    setLoadingRL(true);
    try {
      const simCount = sims || rlSimCount;
      const res = await api.get(`/rrie/contracts/${selectedContractId}/rl-negotiation?simulations=${simCount}`);
      setRlData(res.data);
    } catch (e) { console.error(e); } finally { setLoadingRL(false); }
  };

  const handleExplainClause = async (clauseId) => {
    if (!clauseId) return;
    const clauseData = allClauses.find(c => c.id === clauseId);
    setSelectedClause(clauseId);
    setSelectedClauseData(clauseData);
    setLoadingExplanation(true);
    setExplanation(null);
    try {
      const res = await api.post('/rrie/explain', { clause_id: clauseId });
      setExplanation(res.data.success ? res.data : { error: res.data.error || 'Explanation failed' });
    } catch (e) {
      setExplanation({ error: 'AI service unavailable. Try again shortly.' });
    } finally { setLoadingExplanation(false); }
  };

  const handleRiskBreakdown = async (clauseId) => {
    if (!clauseId) return;
    const clauseData = allClauses.find(c => c.id === clauseId);
    setSelectedClause(clauseId);
    setSelectedClauseData(clauseData);
    setLoadingBreakdown(true);
    setRiskBreakdown(null);
    try {
      const res = await api.get(`/rrie/clauses/${clauseId}/risk-breakdown`);
      setRiskBreakdown(res.data.success ? res.data : { error: 'Failed to load' });
    } catch (e) {
      setRiskBreakdown({ error: 'Failed to load risk breakdown' });
    } finally { setLoadingBreakdown(false); }
  };

  const handleExplainFromTable = (clauseId) => {
    setTab('explain');
    handleExplainClause(clauseId);
  };

  const handleBreakdownFromTable = (clauseId) => {
    setTab('breakdown');
    handleRiskBreakdown(clauseId);
  };

  const sortedClauses = [...clauseTable]
    .filter(c => !clauseFilter ||
      c.clause_name?.toLowerCase().includes(clauseFilter.toLowerCase()) ||
      c.clause_type?.toLowerCase().includes(clauseFilter.toLowerCase()) ||
      c.sentence_type?.toLowerCase().includes(clauseFilter.toLowerCase()))
    .sort((a, b) => {
      const va = a[clauseSort.col] ?? 0;
      const vb = b[clauseSort.col] ?? 0;
      if (typeof va === 'string') return clauseSort.dir === 'asc' ? va.localeCompare(vb) : vb.localeCompare(va);
      return clauseSort.dir === 'asc' ? va - vb : vb - va;
    });

  const toggleSort = (col) => setClauseSort(prev => ({ col, dir: prev.col === col && prev.dir === 'desc' ? 'asc' : 'desc' }));

  const SortIcon = ({ col }) => clauseSort.col !== col ? null :
    clauseSort.dir === 'asc' ? <ChevronUp className="w-3 h-3 inline ml-1 text-purple-400" /> : <ChevronDown className="w-3 h-3 inline ml-1 text-purple-400" />;

  const getSentenceTypeData = () => Object.entries(analysis?.sentence_types || {}).map(([k, v]) => ({ name: k, value: v, color: COLORS[k] || '#64748b' }));
  const getPartyData = () => Object.entries(analysis?.parties || {}).map(([k, v]) => ({ name: k, value: v, color: COLORS[k] || '#64748b' }));
  const getRiskLevelData = () => Object.entries(analysis?.risk_levels || {}).map(([k, v]) => ({ name: k, value: v, fill: COLORS[k] || '#64748b' }));

  // Graph computed values (moved out of JSX to avoid hook-in-conditional issue)
  const graphFilteredNodes = rfNodes.filter(n => {
    if (graphFilter === 'all') return true;
    if (graphFilter === 'high') return (n.type === 'clauseNode' && n.data?.risk_level === 'HIGH') || n.type !== 'clauseNode';
    if (graphFilter === 'risk') return n.data?.sentence_type === 'RISK' || n.type !== 'clauseNode';
    if (graphFilter === 'obligation') return n.data?.sentence_type === 'OBLIGATION' || n.type !== 'clauseNode';
    return true;
  });
  const graphFilteredNodeIds = new Set(graphFilteredNodes.map(n => n.id));
  const graphFilteredEdges = rfEdges.filter(e => graphFilteredNodeIds.has(e.source) && graphFilteredNodeIds.has(e.target));
  const graphHeight = isFullscreen ? '100vh' : '680px';

  const NoData = ({ icon: Icon, message, action, actionLabel }) => (
    <div className="flex flex-col items-center justify-center py-20 gap-4">
      <div className="w-20 h-20 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center">
        <Icon className="w-9 h-9 text-slate-500" />
      </div>
      <p className="text-slate-400 text-base">{message}</p>
      {action && (
        <button onClick={action} className="mt-2 px-5 py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium flex items-center gap-2 transition-colors">
          <ArrowRight className="w-4 h-4" /> {actionLabel}
        </button>
      )}
    </div>
  );

  const LoadingSpinner = ({ color = 'purple' }) => (
    <div className="flex flex-col items-center justify-center py-20 gap-3">
      <Loader className={`w-10 h-10 text-${color}-400 animate-spin`} />
      <p className="text-slate-400 text-sm">Analyzing contract data...</p>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#080d1a] pb-16">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-[#080d1a]/95 backdrop-blur border-b border-slate-800 px-6 py-4">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate(-1)} className="p-2 hover:bg-slate-800 rounded-lg transition-colors">
            <ArrowLeft className="w-5 h-5 text-blue-400" />
          </button>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-yellow-500/10 border border-yellow-500/30 flex items-center justify-center">
              <Zap className="w-6 h-6 text-yellow-400" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white leading-tight">RRIE</h1>
              <p className="text-slate-500 text-xs">Risk &amp; Responsibility Intelligence Engine</p>
            </div>
          </div>
          <div className="ml-auto">
            <select
              value={selectedContractId}
              onChange={(e) => handleContractChange(e.target.value)}
              className="bg-slate-800/80 border border-slate-700 rounded-lg px-4 py-2 text-white text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent min-w-[280px]"
            >
              <option value="">— Select a contract —</option>
              {contracts.map(c => (
                <option key={c.id} value={c.id}>{c.original_filename || c.contract_name || `Contract ${c.id}`}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-0.5 mt-3 overflow-x-auto">
          {TABS.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-1.5 px-4 py-2 text-xs font-medium rounded-lg whitespace-nowrap transition-all ${
                tab === t.id
                  ? 'bg-purple-600/20 text-purple-300 border border-purple-600/40'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              <t.icon className="w-3.5 h-3.5" />
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <div className="px-6 pt-6 space-y-6">

        {/* ══════════════════ PROCESS TAB ══════════════════ */}
        {tab === 'process' && (
          <div className="space-y-6">
            {/* Hero */}
            <div className="relative overflow-hidden rounded-2xl border border-purple-800/40 bg-gradient-to-br from-purple-950/40 via-slate-900 to-slate-900 p-8">
              <div className="absolute top-0 right-0 w-64 h-64 bg-purple-600/5 rounded-full blur-3xl" />
              <div className="relative">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 rounded-xl bg-yellow-500/10 border border-yellow-500/20 flex items-center justify-center">
                    <Zap className="w-7 h-7 text-yellow-400" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-white">RRIE Pipeline</h2>
                    <p className="text-slate-400 text-sm">4-stage AI analysis engine</p>
                  </div>
                </div>
                <p className="text-slate-300 text-sm leading-relaxed mb-6 max-w-2xl">
                  The Risk &amp; Responsibility Intelligence Engine applies multi-layer NLP to classify, attribute and score every clause in the contract — building a full risk intelligence profile.
                </p>

                <div className="grid grid-cols-4 gap-4 mb-8">
                  {[
                    { step: '01', label: 'Sentence Classification', desc: 'Heading · Definition · Obligation · Risk · Right', icon: FileText, color: 'blue' },
                    { step: '02', label: 'Party Attribution', desc: 'Contractor · Employer · Shared', icon: Users, color: 'purple' },
                    { step: '03', label: 'Risk Scoring', desc: 'Keyword detection + weighted scoring', icon: AlertTriangle, color: 'orange' },
                    { step: '04', label: 'Financial Impact', desc: 'Clause-level exposure estimation', icon: DollarSign, color: 'green' },
                  ].map(({ step, label, desc, icon: Icon, color }) => (
                    <div key={step} className={`bg-${color}-900/10 border border-${color}-800/30 rounded-xl p-4`}>
                      <span className={`text-xs font-bold text-${color}-500 font-mono`}>STEP {step}</span>
                      <div className="flex items-center gap-2 mt-2 mb-1">
                        <Icon className={`w-4 h-4 text-${color}-400`} />
                        <p className="text-white text-sm font-semibold">{label}</p>
                      </div>
                      <p className="text-slate-400 text-xs">{desc}</p>
                    </div>
                  ))}
                </div>

                <button
                  onClick={handleProcessRRIE}
                  disabled={processing || !selectedContractId}
                  className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-500 hover:to-purple-600 disabled:from-slate-700 disabled:to-slate-700 disabled:text-slate-500 text-white px-8 py-3.5 rounded-xl font-semibold flex items-center gap-3 transition-all shadow-lg shadow-purple-900/30"
                >
                  {processing ? <><Loader className="w-5 h-5 animate-spin" /> Processing RRIE Pipeline...</> : <><Zap className="w-5 h-5" /> Run RRIE Analysis</>}
                </button>
              </div>
            </div>

            {/* Process Result */}
            {processResult && (
              <div className="bg-green-900/10 border border-green-700/40 rounded-2xl p-6">
                <div className="flex items-center gap-3 mb-5">
                  <CheckCircle className="w-6 h-6 text-green-400" />
                  <h3 className="text-lg font-bold text-white">Processing Complete</h3>
                  <span className="ml-auto text-green-400 font-mono text-sm">{processResult.clauses_processed} clauses analyzed</span>
                </div>
                <div className="grid grid-cols-5 gap-3">
                  {processResult.summary && Object.entries({
                    ...processResult.summary.sentence_types,
                    ...Object.fromEntries(Object.entries(processResult.summary.risk_levels).map(([k, v]) => [`${k} Risk`, v]))
                  }).map(([k, v]) => (
                    <div key={k} className="bg-slate-800/60 rounded-xl p-3 text-center">
                      <p className="text-2xl font-bold text-white">{v}</p>
                      <p className="text-xs text-slate-400 mt-0.5">{k}</p>
                    </div>
                  ))}
                </div>
                <div className="mt-4 flex gap-3">
                  <button onClick={() => setTab('analysis')} className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium flex items-center gap-2">
                    <Brain className="w-4 h-4" /> View Analysis
                  </button>
                  <button onClick={() => { setTab('clauses'); loadClauseTable(); }} className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium flex items-center gap-2">
                    <Table className="w-4 h-4" /> Clause Table
                  </button>
                  <button onClick={() => { setTab('deal'); loadDealScore(); }} className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium flex items-center gap-2">
                    <Target className="w-4 h-4" /> Deal Score
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ══════════════════ ANALYSIS TAB ══════════════════ */}
        {tab === 'analysis' && (
          <div className="space-y-5">
            {loadingAnalysis ? <LoadingSpinner /> : analysis ? (
              <>
                {/* What is Analysis? - Explanation Panel */}
                <div className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 border border-purple-700/40 rounded-2xl p-6 backdrop-blur-xl">
                  <div className="flex items-start gap-4">
                    <div className="p-3 bg-gradient-to-br from-purple-600/30 to-blue-600/30 rounded-xl border border-purple-700/50">
                      <Brain className="w-6 h-6 text-purple-300" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-bold text-white mb-2 bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
                        📊 What is Contract Analysis?
                      </h3>
                      <p className="text-sm text-slate-300 leading-relaxed mb-4">
                        AI-powered deep analysis revealing the <strong className="text-white">composition, balance, and risk distribution</strong> of your contract. Understand who bears what risk, which clause types dominate, and where the critical issues lie.
                      </p>

                      {/* 3 Key Metrics Explained */}
                      <div className="grid grid-cols-3 gap-3">
                        <div className="bg-orange-900/20 border border-orange-700/40 rounded-xl p-3">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xl">📝</span>
                            <p className="text-xs font-bold text-orange-300">Sentence Types</p>
                          </div>
                          <p className="text-xs text-slate-400 leading-relaxed">
                            Shows clause composition: <strong className="text-orange-400">RISK</strong> (dangerous), <strong className="text-yellow-400">OBLIGATION</strong> (duties), <strong className="text-green-400">RIGHT</strong> (protections)
                          </p>
                        </div>

                        <div className="bg-blue-900/20 border border-blue-700/40 rounded-xl p-3">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xl">⚖️</span>
                            <p className="text-xs font-bold text-blue-300">Party Balance</p>
                          </div>
                          <p className="text-xs text-slate-400 leading-relaxed">
                            Who bears risk: <strong className="text-blue-400">CONTRACTOR</strong> (YOU), <strong className="text-purple-400">EMPLOYER</strong> (THEM), <strong className="text-cyan-400">SHARED</strong> (BOTH)
                          </p>
                        </div>

                        <div className="bg-red-900/20 border border-red-700/40 rounded-xl p-3">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xl">🎯</span>
                            <p className="text-xs font-bold text-red-300">Risk Severity</p>
                          </div>
                          <p className="text-xs text-slate-400 leading-relaxed">
                            Danger levels: <strong className="text-red-400">HIGH</strong> (urgent), <strong className="text-yellow-400">MEDIUM</strong> (watch), <strong className="text-green-400">LOW</strong> (safe)
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* KPI row */}
                <div className="grid grid-cols-4 gap-4">
                  {[
                    { label: 'Total Clauses', value: analysis.total_clauses || 0, icon: FileText, color: 'blue', sub: 'analyzed' },
                    { label: 'High Risk', value: analysis.risk_levels?.HIGH || 0, icon: AlertTriangle, color: 'red', sub: 'clauses' },
                    { label: 'Medium Risk', value: analysis.risk_levels?.MEDIUM || 0, icon: AlertCircle, color: 'yellow', sub: 'clauses' },
                    { label: 'Low Risk', value: analysis.risk_levels?.LOW || 0, icon: Shield, color: 'green', sub: 'clauses' },
                  ].map(({ label, value, icon: Icon, color, sub }) => (
                    <div key={label} className="bg-slate-900 border border-slate-800 rounded-2xl p-5 relative overflow-hidden">
                      <div className={`absolute top-0 right-0 w-24 h-24 bg-${color}-600/5 rounded-full blur-xl`} />
                      <div className={`w-9 h-9 rounded-lg bg-${color}-900/40 border border-${color}-800/50 flex items-center justify-center mb-3`}>
                        <Icon className={`w-5 h-5 text-${color}-400`} />
                      </div>
                      <p className="text-3xl font-black text-white">{value}</p>
                      <p className={`text-xs text-${color}-400 font-medium mt-0.5`}>{sub}</p>
                      <p className="text-xs text-slate-500 mt-0.5">{label}</p>
                    </div>
                  ))}
                </div>

                {/* Enhanced Charts Row with Intelligence Panels */}
                <div className="grid grid-cols-3 gap-5">
                  {/* Sentence Types */}
                  <div className="bg-gradient-to-br from-slate-900/90 to-slate-800/90 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-5 relative overflow-hidden">
                    {/* Floating blob */}
                    <div className="absolute -top-10 -right-10 w-32 h-32 bg-gradient-to-br from-orange-600/10 to-red-600/10 rounded-full blur-3xl"></div>

                    <div className="relative z-10">
                      <div className="flex items-center gap-2 mb-1">
                        <div className="p-1.5 bg-gradient-to-br from-orange-600/20 to-red-600/20 rounded-lg border border-orange-700/40">
                          <FileText className="w-4 h-4 text-orange-400" />
                        </div>
                        <h3 className="text-sm font-bold bg-gradient-to-r from-orange-400 to-red-400 bg-clip-text text-transparent">
                          Sentence Type Distribution
                        </h3>
                      </div>
                      <p className="text-xs text-slate-400 mb-4">NLP classification of all clauses</p>
                    <ResponsiveContainer width="100%" height={200}>
                      <PieChart>
                        <Pie data={getSentenceTypeData()} cx="50%" cy="50%" innerRadius={45} outerRadius={75} paddingAngle={3} dataKey="value">
                          {getSentenceTypeData().map((e, i) => <Cell key={i} fill={e.color} />)}
                        </Pie>
                        <Tooltip content={<CustomTooltip />} />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {getSentenceTypeData().map(e => (
                        <div key={e.name} className="flex items-center gap-1.5">
                          <div className="w-2 h-2 rounded-full" style={{ background: e.color }} />
                          <span className="text-xs text-slate-400">{e.name} <span className="text-slate-300 font-medium">{e.value}</span></span>
                        </div>
                      ))}
                    </div>
                    </div>
                  </div>

                  {/* Party Attribution */}
                  <div className="bg-gradient-to-br from-slate-900/90 to-slate-800/90 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-5 relative overflow-hidden">
                    {/* Floating blob */}
                    <div className="absolute -top-10 -right-10 w-32 h-32 bg-gradient-to-br from-cyan-600/10 to-blue-600/10 rounded-full blur-3xl"></div>

                    <div className="relative z-10">
                      <div className="flex items-center gap-2 mb-1">
                        <div className="p-1.5 bg-gradient-to-br from-cyan-600/20 to-blue-600/20 rounded-lg border border-cyan-700/40">
                          <Users className="w-4 h-4 text-cyan-400" />
                        </div>
                        <h3 className="text-sm font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
                          Party Attribution
                        </h3>
                      </div>
                      <p className="text-xs text-slate-400 mb-4">Risk ownership by contracting party</p>
                    <ResponsiveContainer width="100%" height={200}>
                      <PieChart>
                        <Pie data={getPartyData()} cx="50%" cy="50%" innerRadius={45} outerRadius={75} paddingAngle={3} dataKey="value">
                          {getPartyData().map((e, i) => <Cell key={i} fill={e.color} />)}
                        </Pie>
                        <Tooltip content={<CustomTooltip />} />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {getPartyData().map(e => (
                        <div key={e.name} className="flex items-center gap-1.5">
                          <div className="w-2 h-2 rounded-full" style={{ background: e.color }} />
                          <span className="text-xs text-slate-400">{e.name} <span className="text-slate-300 font-medium">{e.value}</span></span>
                        </div>
                      ))}
                    </div>
                    </div>
                  </div>

                  {/* Risk Levels */}
                  <div className="bg-gradient-to-br from-slate-900/90 to-slate-800/90 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-5 relative overflow-hidden">
                    {/* Floating blob */}
                    <div className="absolute -top-10 -right-10 w-32 h-32 bg-gradient-to-br from-red-600/10 to-orange-600/10 rounded-full blur-3xl"></div>

                    <div className="relative z-10">
                      <div className="flex items-center gap-2 mb-1">
                        <div className="p-1.5 bg-gradient-to-br from-red-600/20 to-orange-600/20 rounded-lg border border-red-700/40">
                          <AlertTriangle className="w-4 h-4 text-red-400" />
                        </div>
                        <h3 className="text-sm font-bold bg-gradient-to-r from-red-400 to-orange-400 bg-clip-text text-transparent">
                          Risk Level Breakdown
                        </h3>
                      </div>
                      <p className="text-xs text-slate-400 mb-4">Clause risk severity distribution</p>
                    <ResponsiveContainer width="100%" height={200}>
                      <BarChart data={getRiskLevelData()} barSize={36}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                        <XAxis dataKey="name" stroke="#475569" tick={{ fontSize: 11, fill: '#94a3b8' }} />
                        <YAxis stroke="#475569" tick={{ fontSize: 11, fill: '#94a3b8' }} />
                        <Tooltip content={<CustomTooltip />} />
                        <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                          {getRiskLevelData().map((e, i) => <Cell key={i} fill={e.fill} />)}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                    </div>
                  </div>
                </div>

                {/* Intelligence Panels - Detailed Explanations */}
                <div className="grid grid-cols-2 gap-5">
                  {/* Sentence Type Intelligence */}
                  <div className="bg-gradient-to-br from-slate-900/80 to-slate-800/80 backdrop-blur-xl border border-orange-700/30 rounded-2xl p-5 relative overflow-hidden">
                    <div className="absolute -bottom-10 -left-10 w-32 h-32 bg-gradient-to-br from-orange-600/10 to-red-600/10 rounded-full blur-3xl"></div>

                    <div className="relative z-10">
                      <h4 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                        <span className="text-orange-400">📝</span> Sentence Type Intelligence
                      </h4>

                      <div className="space-y-3 text-xs">
                        {/* RISK Analysis */}
                        {analysis.sentence_types?.RISK > 0 && (
                          <div className="bg-red-900/20 border border-red-800/40 rounded-lg p-3">
                            <p className="text-red-300 font-bold mb-1">🔴 RISK ({analysis.sentence_types.RISK} clauses)</p>
                            <p className="text-slate-300 leading-relaxed">
                              Clauses that create <strong className="text-red-400">liability, penalties, or obligations</strong> that could hurt you if triggered. Higher RISK count = more dangerous contract.
                            </p>
                          </div>
                        )}

                        {/* OBLIGATION Analysis */}
                        {analysis.sentence_types?.OBLIGATION > 0 && (
                          <div className="bg-yellow-900/20 border border-yellow-800/40 rounded-lg p-3">
                            <p className="text-yellow-300 font-bold mb-1">🟡 OBLIGATION ({analysis.sentence_types.OBLIGATION} clauses)</p>
                            <p className="text-slate-300 leading-relaxed">
                              Duties you <strong className="text-yellow-400">must perform</strong>. Not inherently risky, but creates work requirements. Monitor compliance carefully.
                            </p>
                          </div>
                        )}

                        {/* RIGHT Analysis */}
                        {analysis.sentence_types?.RIGHT > 0 && (
                          <div className="bg-green-900/20 border border-green-800/40 rounded-lg p-3">
                            <p className="text-green-300 font-bold mb-1">🟢 RIGHT ({analysis.sentence_types.RIGHT} clauses)</p>
                            <p className="text-slate-300 leading-relaxed">
                              Clauses that <strong className="text-green-400">protect YOU</strong> — grants permissions, termination rights, IP ownership. The more, the better!
                            </p>
                          </div>
                        )}

                        {/* DEFINITION Analysis */}
                        {analysis.sentence_types?.DEFINITION > 0 && (
                          <div className="bg-cyan-900/20 border border-cyan-800/40 rounded-lg p-3">
                            <p className="text-cyan-300 font-bold mb-1">🔵 DEFINITION ({analysis.sentence_types.DEFINITION} clauses)</p>
                            <p className="text-slate-300 leading-relaxed">
                              Definitions and interpretations. Usually <strong className="text-cyan-400">low risk</strong>, but read carefully — some definitions hide obligations.
                            </p>
                          </div>
                        )}

                        {/* Key Insight */}
                        <div className="mt-4 p-3 bg-blue-900/20 border border-blue-800/30 rounded-lg">
                          <p className="text-blue-300 text-xs leading-relaxed">
                            <strong className="text-blue-200">💡 Ideal Balance:</strong> RISK clauses should be ≤30% of total. RIGHT clauses should be ≥20%. Your contract: {analysis.sentence_types?.RISK && analysis.total_clauses ? `${Math.round((analysis.sentence_types.RISK / analysis.total_clauses) * 100)}% RISK` : 'Calculate ratio'}.
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Party Attribution Intelligence */}
                  <div className="bg-gradient-to-br from-slate-900/80 to-slate-800/80 backdrop-blur-xl border border-cyan-700/30 rounded-2xl p-5 relative overflow-hidden">
                    <div className="absolute -bottom-10 -right-10 w-32 h-32 bg-gradient-to-br from-cyan-600/10 to-blue-600/10 rounded-full blur-3xl"></div>

                    <div className="relative z-10">
                      <h4 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                        <span className="text-cyan-400">⚖️</span> Party Balance Intelligence
                      </h4>

                      <div className="space-y-3 text-xs">
                        {/* CONTRACTOR Analysis */}
                        <div className={`border rounded-lg p-3 ${
                          (analysis.parties?.CONTRACTOR || 0) / analysis.total_clauses > 0.4
                            ? 'bg-red-900/20 border-red-800/40'
                            : 'bg-blue-900/20 border-blue-800/40'
                        }`}>
                          <p className="text-blue-300 font-bold mb-1">
                            🏗️ CONTRACTOR - YOU ({analysis.parties?.CONTRACTOR || 0} clauses = {analysis.total_clauses ? Math.round((analysis.parties?.CONTRACTOR || 0) / analysis.total_clauses * 100) : 0}%)
                          </p>
                          <p className="text-slate-300 leading-relaxed">
                            <strong className="text-blue-400">YOUR obligations and liabilities.</strong> If this is {'>'}40%, you're taking most of the risk = unfair contract!
                          </p>
                          <p className={`mt-2 font-bold ${
                            (analysis.parties?.CONTRACTOR || 0) / analysis.total_clauses > 0.4
                              ? 'text-red-400'
                              : 'text-green-400'
                          }`}>
                            {(analysis.parties?.CONTRACTOR || 0) / analysis.total_clauses > 0.4
                              ? '⚠️ TOO HIGH! Negotiate to reduce your burden.'
                              : '✅ OK - Reasonable contractor obligations.'}
                          </p>
                        </div>

                        {/* EMPLOYER Analysis */}
                        <div className={`border rounded-lg p-3 ${
                          (analysis.parties?.EMPLOYER || 0) / analysis.total_clauses < 0.15
                            ? 'bg-red-900/20 border-red-800/40'
                            : 'bg-purple-900/20 border-purple-800/40'
                        }`}>
                          <p className="text-purple-300 font-bold mb-1">
                            🏢 EMPLOYER - THEM ({analysis.parties?.EMPLOYER || 0} clauses = {analysis.total_clauses ? Math.round((analysis.parties?.EMPLOYER || 0) / analysis.total_clauses * 100) : 0}%)
                          </p>
                          <p className="text-slate-300 leading-relaxed">
                            <strong className="text-purple-400">THEIR obligations and liabilities.</strong> The more, the better for YOU. They should have responsibilities too!
                          </p>
                          <p className={`mt-2 font-bold ${
                            (analysis.parties?.EMPLOYER || 0) / analysis.total_clauses < 0.15
                              ? 'text-red-400'
                              : 'text-green-400'
                          }`}>
                            {(analysis.parties?.EMPLOYER || 0) / analysis.total_clauses < 0.15
                              ? '⚠️ TOO LOW! They have almost no obligations. Add more!'
                              : '✅ GOOD - They share the burden.'}
                          </p>
                        </div>

                        {/* SHARED Analysis */}
                        <div className="bg-cyan-900/20 border border-cyan-800/40 rounded-lg p-3">
                          <p className="text-cyan-300 font-bold mb-1">
                            🤝 SHARED - BOTH ({analysis.parties?.SHARED || 0} clauses = {analysis.total_clauses ? Math.round((analysis.parties?.SHARED || 0) / analysis.total_clauses * 100) : 0}%)
                          </p>
                          <p className="text-slate-300 leading-relaxed">
                            <strong className="text-cyan-400">Mutual obligations</strong> affecting both parties equally. Ideal: {'>'}50% should be SHARED for fairness.
                          </p>
                          <p className={`mt-2 font-bold ${
                            (analysis.parties?.SHARED || 0) / analysis.total_clauses > 0.5
                              ? 'text-green-400'
                              : 'text-yellow-400'
                          }`}>
                            {(analysis.parties?.SHARED || 0) / analysis.total_clauses > 0.5
                              ? '✅ WELL-BALANCED! Contract is fair.'
                              : '⚡ Could be more balanced. Add mutual clauses.'}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* High risk clause cards */}
                {analysis.high_risk_clauses?.length > 0 && (
                  <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                    <div className="flex items-center justify-between mb-5">
                      <div>
                        <h3 className="text-base font-bold text-white flex items-center gap-2">
                          <AlertTriangle className="w-5 h-5 text-red-400" /> Critical Risk Clauses
                        </h3>
                        <p className="text-xs text-slate-500 mt-0.5">Clauses requiring immediate attention</p>
                      </div>
                      <span className="text-xs text-red-400 font-medium bg-red-900/20 border border-red-900/40 px-3 py-1 rounded-full">
                        {analysis.high_risk_clauses.length} clauses flagged
                      </span>
                    </div>
                    <div className="space-y-3">
                      {analysis.high_risk_clauses.map((c, i) => (
                        <div key={i} className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4 flex items-start gap-4 hover:border-red-800/40 transition-colors">
                          <div className="w-8 h-8 rounded-lg bg-red-900/30 border border-red-800/40 flex items-center justify-center shrink-0 mt-0.5">
                            <span className="text-red-400 font-bold text-xs">{i + 1}</span>
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="font-semibold text-white">{c.clause_name}</p>
                            <div className="flex flex-wrap gap-2 mt-1.5">
                              <span className={`px-2 py-0.5 rounded text-xs font-medium border ${
                                c.sentence_type === 'RISK' ? 'bg-red-900/30 text-red-400 border-red-800' :
                                c.sentence_type === 'OBLIGATION' ? 'bg-yellow-900/30 text-yellow-400 border-yellow-800' :
                                'bg-slate-700 text-slate-300 border-slate-600'
                              }`}>{c.sentence_type}</span>
                              <span className={`px-2 py-0.5 rounded text-xs font-medium border ${
                                c.party === 'CONTRACTOR' ? 'bg-blue-900/30 text-blue-400 border-blue-800' :
                                c.party === 'EMPLOYER' ? 'bg-purple-900/30 text-purple-400 border-purple-800' :
                                'bg-cyan-900/30 text-cyan-400 border-cyan-800'
                              }`}>{c.party}</span>
                            </div>
                          </div>
                          <div className="text-right shrink-0">
                            <div className="text-2xl font-black text-red-400">{((c.risk_score || 0) * 100).toFixed(0)}%</div>
                            <div className="text-xs text-slate-500">₹{(c.financial_impact || 0).toLocaleString()}</div>
                            <div className="flex gap-1 mt-2">
                              <button onClick={() => handleExplainFromTable(c.id)} className="px-2 py-1 bg-purple-600/80 hover:bg-purple-600 rounded text-xs text-white transition-colors">Explain</button>
                              <button onClick={() => handleBreakdownFromTable(c.id)} className="px-2 py-1 bg-orange-600/80 hover:bg-orange-600 rounded text-xs text-white transition-colors">Why</button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <NoData icon={Brain} message="No analysis available. Process the contract first." action={() => setTab('process')} actionLabel="Go to Process" />
            )}
          </div>
        )}

        {/* ══════════════════ CLAUSE TABLE TAB ══════════════════ */}
        {tab === 'clauses' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <Table className="w-5 h-5 text-blue-400" /> Clause Intelligence Table
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  {sortedClauses.length} of {clauseTable.length} clauses · sorted by {clauseSort.col.replace('_', ' ')} {clauseSort.dir}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    placeholder="Filter by name, type, party..."
                    value={clauseFilter}
                    onChange={e => setClauseFilter(e.target.value)}
                    className="pl-8 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:ring-2 focus:ring-purple-500 focus:border-transparent w-56"
                  />
                </div>
                <button onClick={loadClauseTable} disabled={!selectedContractId} className="px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 disabled:opacity-50 text-slate-300 rounded-lg text-xs flex items-center gap-1.5 transition-colors">
                  <RefreshCw className="w-3.5 h-3.5" /> Refresh
                </button>
              </div>
            </div>

            {loadingClauses ? <LoadingSpinner color="blue" /> : sortedClauses.length > 0 ? (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-slate-800/80 border-b border-slate-700">
                        {[
                          { col: 'clause_name', label: 'Clause Name' },
                          { col: 'clause_type', label: 'Type' },
                          { col: 'sentence_type', label: 'Sentence' },
                          { col: 'party', label: 'Party' },
                          { col: 'risk_score', label: 'Risk Score' },
                          { col: 'risk_level', label: 'Level' },
                          { col: 'financial_impact', label: 'Fin. Impact' },
                        ].map(({ col, label }) => (
                          <th key={col} onClick={() => toggleSort(col)}
                            className="px-4 py-3.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider cursor-pointer hover:text-slate-200 select-none whitespace-nowrap">
                            {label}<SortIcon col={col} />
                          </th>
                        ))}
                        <th className="px-4 py-3.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sortedClauses.map((c, i) => (
                        <tr key={c.id} className={`border-b border-slate-800/60 hover:bg-slate-800/40 transition-colors ${i % 2 === 1 ? 'bg-slate-900/40' : ''}`}>
                          <td className="px-4 py-3.5">
                            <p className="text-white font-semibold text-sm max-w-[200px] truncate" title={c.clause_name}>{c.clause_name || '—'}</p>
                            <p className="text-xs text-slate-500 mt-0.5 max-w-[200px] truncate">{c.text_preview}</p>
                          </td>
                          <td className="px-4 py-3.5">
                            <span className="text-slate-400 text-xs">{c.clause_type || '—'}</span>
                          </td>
                          <td className="px-4 py-3.5">
                            <span className={`px-2.5 py-1 rounded-md text-xs font-semibold border ${
                              c.sentence_type === 'RISK' ? 'bg-red-900/30 text-red-400 border-red-800/60' :
                              c.sentence_type === 'OBLIGATION' ? 'bg-yellow-900/30 text-yellow-400 border-yellow-800/60' :
                              c.sentence_type === 'RIGHT' ? 'bg-green-900/30 text-green-400 border-green-800/60' :
                              c.sentence_type === 'DEFINITION' ? 'bg-cyan-900/30 text-cyan-400 border-cyan-800/60' :
                              'bg-purple-900/30 text-purple-400 border-purple-800/60'
                            }`}>{c.sentence_type}</span>
                          </td>
                          <td className="px-4 py-3.5">
                            <span className={`px-2.5 py-1 rounded-md text-xs font-semibold border ${
                              c.party === 'CONTRACTOR' ? 'bg-blue-900/30 text-blue-400 border-blue-800/60' :
                              c.party === 'EMPLOYER' ? 'bg-purple-900/30 text-purple-400 border-purple-800/60' :
                              'bg-cyan-900/30 text-cyan-400 border-cyan-800/60'
                            }`}>{c.party}</span>
                          </td>
                          <td className="px-4 py-3.5">
                            <div className="flex items-center gap-2.5">
                              <div className="w-20 bg-slate-700 rounded-full h-1.5 overflow-hidden">
                                <div className="h-1.5 rounded-full transition-all" style={{ width: `${Math.round(c.risk_score * 100)}%`, background: heatColor(c.risk_score) }} />
                              </div>
                              <span className="text-xs font-mono font-bold" style={{ color: heatColor(c.risk_score) }}>{(c.risk_score * 100).toFixed(0)}%</span>
                            </div>
                          </td>
                          <td className="px-4 py-3.5">
                            <span className={`px-2.5 py-1 rounded-md text-xs font-semibold border ${riskBg(c.risk_level)}`}>{c.risk_level}</span>
                          </td>
                          <td className="px-4 py-3.5">
                            <span className="text-slate-200 text-xs font-mono">₹{(c.financial_impact || 0).toLocaleString()}</span>
                          </td>
                          <td className="px-4 py-3.5">
                            <div className="flex gap-1">
                              <button onClick={() => handleExplainFromTable(c.id)} className="px-2.5 py-1 bg-purple-600/80 hover:bg-purple-600 border border-purple-700 rounded-md text-xs text-white font-medium transition-colors">Explain</button>
                              <button onClick={() => handleBreakdownFromTable(c.id)} className="px-2.5 py-1 bg-orange-600/80 hover:bg-orange-600 border border-orange-700 rounded-md text-xs text-white font-medium transition-colors">Why</button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <NoData icon={Table} message="No clause data. Process the contract with RRIE first." action={() => setTab('process')} actionLabel="Go to Process" />
            )}
          </div>
        )}

        {/* ══════════════════ HEATMAP TAB ══════════════════ */}
        {tab === 'heatmap' && (
          <div className="space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <Flame className="w-5 h-5 text-orange-400" /> Risk Heatmap
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">Average risk intensity: Sentence Type × Party matrix</p>
              </div>
              <button onClick={loadHeatmap} disabled={!selectedContractId} className="px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 rounded-lg text-xs flex items-center gap-1.5 transition-colors">
                <RefreshCw className="w-3.5 h-3.5" /> Refresh
              </button>
            </div>

            {loadingHeatmap ? <LoadingSpinner color="orange" /> : heatmap?.rows?.length > 0 ? (
              <>
                {/* Legend */}
                <div className="flex items-center gap-4 bg-slate-900 border border-slate-800 rounded-xl px-5 py-3">
                  <span className="text-slate-400 text-xs font-medium">Risk Scale:</span>
                  <div className="flex items-center gap-1 flex-1">
                    {['#1e293b', '#22c55e', '#84cc16', '#f59e0b', '#f97316', '#ef4444'].map((c, i) => (
                      <div key={i} className="h-3 flex-1 first:rounded-l-full last:rounded-r-full" style={{ background: c }} />
                    ))}
                  </div>
                  <div className="flex gap-4 text-xs text-slate-400">
                    <span>0% None</span><span className="text-green-400">Low</span><span className="text-yellow-400">Medium</span><span className="text-red-400">Critical</span>
                  </div>
                </div>

                {/* Matrix */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr>
                        <th className="text-left text-xs font-semibold text-slate-400 uppercase pb-4 pr-8 w-36">Type \ Party</th>
                        {heatmap.parties.map(p => (
                          <th key={p} className="text-center text-xs font-semibold text-slate-300 pb-4 px-4 uppercase tracking-wide">{p}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {heatmap.rows.map(row => (
                        <tr key={row.sentence_type} className="group">
                          <td className="py-2.5 pr-8">
                            <span className={`px-2.5 py-1 rounded-md text-xs font-semibold border ${
                              row.sentence_type === 'RISK' ? 'bg-red-900/30 text-red-400 border-red-800/60' :
                              row.sentence_type === 'OBLIGATION' ? 'bg-yellow-900/30 text-yellow-400 border-yellow-800/60' :
                              row.sentence_type === 'RIGHT' ? 'bg-green-900/30 text-green-400 border-green-800/60' :
                              row.sentence_type === 'DEFINITION' ? 'bg-cyan-900/30 text-cyan-400 border-cyan-800/60' :
                              'bg-purple-900/30 text-purple-400 border-purple-800/60'
                            }`}>{row.sentence_type}</span>
                          </td>
                          {row.values.map(cell => (
                            <td key={cell.party} className="py-2.5 px-4 text-center">
                              <div
                                className="mx-auto w-24 h-16 rounded-xl flex flex-col items-center justify-center cursor-default transition-all hover:scale-110 hover:shadow-lg"
                                style={{
                                  background: `${heatColor(cell.avg_risk)}22`,
                                  borderWidth: 1,
                                  borderColor: `${heatColor(cell.avg_risk)}55`,
                                  opacity: cell.count === 0 ? 0.25 : 1,
                                  boxShadow: cell.avg_risk >= 0.5 ? `0 0 12px ${heatColor(cell.avg_risk)}33` : 'none'
                                }}
                                title={`${row.sentence_type} × ${cell.party}: ${(cell.avg_risk * 100).toFixed(0)}% avg (${cell.count} clauses)`}
                              >
                                <span className="font-black text-base" style={{ color: heatColor(cell.avg_risk) }}>{(cell.avg_risk * 100).toFixed(0)}%</span>
                                <span className="text-xs" style={{ color: `${heatColor(cell.avg_risk)}99` }}>{cell.count} cls</span>
                              </div>
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Per-party summary */}
                <div className="grid grid-cols-3 gap-4">
                  {heatmap.parties.map(p => {
                    const allVals = heatmap.rows.flatMap(r => r.values.filter(v => v.party === p && v.count > 0).map(v => v.avg_risk));
                    const avg = allVals.length ? allVals.reduce((a, b) => a + b, 0) / allVals.length : 0;
                    const max = allVals.length ? Math.max(...allVals) : 0;
                    return (
                      <div key={p} className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
                        <div className="flex items-center justify-between mb-3">
                          <span className={`px-2.5 py-1 rounded-md text-xs font-semibold border ${
                            p === 'CONTRACTOR' ? 'bg-blue-900/30 text-blue-400 border-blue-800/60' :
                            p === 'EMPLOYER' ? 'bg-purple-900/30 text-purple-400 border-purple-800/60' :
                            'bg-cyan-900/30 text-cyan-400 border-cyan-800/60'
                          }`}>{p}</span>
                          <span className="text-xs text-slate-500">avg risk</span>
                        </div>
                        <p className="text-3xl font-black" style={{ color: heatColor(avg) }}>{(avg * 100).toFixed(0)}%</p>
                        <div className="mt-2 space-y-1">
                          <div className="flex justify-between text-xs text-slate-500">
                            <span>Average</span><span style={{ color: heatColor(avg) }}>{(avg * 100).toFixed(0)}%</span>
                          </div>
                          <div className="flex justify-between text-xs text-slate-500">
                            <span>Peak</span><span style={{ color: heatColor(max) }}>{(max * 100).toFixed(0)}%</span>
                          </div>
                        </div>
                        <div className="w-full bg-slate-700 rounded-full h-2 mt-3">
                          <div className="h-2 rounded-full transition-all" style={{ width: `${avg * 100}%`, background: heatColor(avg) }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </>
            ) : (
              <NoData icon={Flame} message="No heatmap data. Process the contract with RRIE first." action={() => setTab('process')} actionLabel="Go to Process" />
            )}
          </div>
        )}

        {/* ══════════════════ AI INSIGHTS TAB ══════════════════ */}
        {tab === 'insights' && (
          <div className="space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <Eye className="w-5 h-5 text-cyan-400" /> AI Insights
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">Deep risk intelligence, liability analysis &amp; GraphRAG queries</p>
              </div>
              <button onClick={loadInsights} disabled={!selectedContractId} className="px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 rounded-lg text-xs flex items-center gap-1.5">
                <RefreshCw className="w-3.5 h-3.5" /> Refresh
              </button>
            </div>

            {loadingInsights ? <LoadingSpinner color="cyan" /> : insights ? (
              <>
                {/* What is AI Insights? - Info Panel */}
                <div className="bg-gradient-to-r from-cyan-900/20 to-blue-900/20 border border-cyan-700/40 rounded-2xl p-6">
                  <div className="flex items-start gap-4">
                    <div className="p-3 bg-cyan-900/40 rounded-xl border border-cyan-700/50">
                      <Brain className="w-6 h-6 text-cyan-300" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-bold text-white mb-2">What is AI Insights?</h3>
                      <p className="text-sm text-slate-300 leading-relaxed mb-3">
                        AI-powered deep analysis revealing hidden patterns, liability distribution, and risk relationships in your contract using advanced NLP and GraphRAG technology.
                      </p>
                      <div className="grid grid-cols-3 gap-3">
                        <div className="bg-slate-900/60 border border-slate-700/50 rounded-lg p-3">
                          <div className="text-xs font-bold text-blue-400 mb-1">⚖️ Liability Balance</div>
                          <div className="text-xs text-slate-400">Shows WHO bears the risk - you, them, or both</div>
                        </div>
                        <div className="bg-slate-900/60 border border-slate-700/50 rounded-lg p-3">
                          <div className="text-xs font-bold text-red-400 mb-1">🎯 Top Risk Clauses</div>
                          <div className="text-xs text-slate-400">Most dangerous clauses ranked by severity</div>
                        </div>
                        <div className="bg-slate-900/60 border border-slate-700/50 rounded-lg p-3">
                          <div className="text-xs font-bold text-yellow-400 mb-1">🔍 Hidden Risks</div>
                          <div className="text-xs text-slate-400">Dangerous clauses disguised as definitions</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Liability Balance */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                  <div className="flex items-center justify-between mb-5">
                    <div>
                      <h3 className="text-base font-bold text-white flex items-center gap-2">
                        <BarChart2 className="w-5 h-5 text-blue-400" /> Liability Balance Analysis
                      </h3>
                      <p className="text-xs text-slate-500 mt-0.5">Risk ownership distribution across contracting parties</p>
                    </div>
                    <span className={`text-xs px-3 py-1.5 rounded-full font-semibold border ${
                      insights.liability_balance?.verdict === 'BALANCED' ? 'bg-green-900/30 text-green-400 border-green-800' :
                      insights.liability_balance?.verdict === 'MODERATELY UNBALANCED' ? 'bg-yellow-900/30 text-yellow-400 border-yellow-800' :
                      'bg-red-900/30 text-red-400 border-red-800'
                    }`}>{insights.liability_balance?.verdict}</span>
                  </div>

                  <div className="bg-blue-900/10 border border-blue-700/30 rounded-xl p-3 mb-4">
                    <div className="text-xs text-slate-300 space-y-1">
                      <p><span className="font-bold text-blue-400">Contractor</span> = Risks YOU bear (your responsibility)</p>
                      <p><span className="font-bold text-purple-400">Employer</span> = Risks THEY bear (their responsibility)</p>
                      <p><span className="font-bold text-cyan-400">Shared</span> = Risks BOTH share (mutual responsibility)</p>
                      <p className="mt-2 pt-2 border-t border-blue-700/30 text-yellow-300">
                        <strong>⚠️ Warning:</strong> If Contractor &gt; 60%, you're taking most risk = unfair deal!
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-4 mb-4">
                    {[
                      { label: 'Contractor', pct: insights.liability_balance?.contractor_pct || 0, color: '#3b82f6', bg: 'bg-blue-900/20', border: 'border-blue-800/40' },
                      { label: 'Employer', pct: insights.liability_balance?.employer_pct || 0, color: '#8b5cf6', bg: 'bg-purple-900/20', border: 'border-purple-800/40' },
                      { label: 'Shared', pct: insights.liability_balance?.shared_pct || 0, color: '#06b6d4', bg: 'bg-cyan-900/20', border: 'border-cyan-800/40' },
                    ].map(({ label, pct, color, bg, border }) => (
                      <div key={label} className={`${bg} border ${border} rounded-xl p-4`}>
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm font-semibold text-slate-300">{label}</span>
                          <span className="text-xl font-black" style={{ color }}>{pct}%</span>
                        </div>
                        <div className="bg-slate-700 rounded-full h-2">
                          <div className="h-2 rounded-full transition-all" style={{ width: `${pct}%`, background: color }} />
                        </div>
                      </div>
                    ))}
                  </div>
                  {insights.liability_balance?.unbalanced_clauses?.length > 0 && (
                    <div className="border-t border-slate-800 pt-4">
                      <p className="text-xs font-semibold text-slate-400 mb-2">High-risk contractor clauses:</p>
                      <div className="flex flex-wrap gap-2">
                        {insights.liability_balance.unbalanced_clauses.map((c, i) => (
                          <span key={i} className="px-2.5 py-1 bg-blue-900/20 border border-blue-800/40 rounded-lg text-xs text-blue-300">
                            {c.clause_name} — <span className="text-blue-400 font-bold">{(c.risk_score * 100).toFixed(0)}%</span>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Top 10 Risks */}
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                  <h3 className="text-base font-bold text-white mb-1 flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-red-400" /> Top Risk Clauses
                  </h3>
                  <p className="text-xs text-slate-500 mb-3">Ranked by normalized risk score — highest exposure first</p>

                  <div className="bg-red-900/10 border border-red-700/30 rounded-xl p-3 mb-4">
                    <div className="text-xs text-slate-300">
                      <p className="font-bold text-red-400 mb-2">Why These Are Dangerous:</p>
                      <ul className="list-disc list-inside space-y-1 text-slate-400">
                        <li>Can trigger <span className="text-white font-semibold">lawsuits and penalties</span></li>
                        <li>May cause <span className="text-white font-semibold">unlimited financial liability</span></li>
                        <li>Keywords shown = words that triggered the risk alert</li>
                        <li>Top 3 (red badges) = <span className="text-red-300 font-semibold">MUST negotiate these!</span></li>
                      </ul>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {(insights.top_risks || []).map((c, i) => (
                      <div key={c.id} className="flex items-center gap-3 bg-slate-800/50 border border-slate-700/60 rounded-xl p-3.5 hover:border-red-900/40 transition-colors">
                        <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 text-xs font-black ${
                          i < 3 ? 'bg-red-900/40 text-red-400 border border-red-800/50' : 'bg-slate-700 text-slate-400'
                        }`}>{i + 1}</div>
                        <div className="flex-1 min-w-0">
                          <p className="text-white text-sm font-semibold truncate">{c.clause_name}</p>
                          <div className="flex items-center gap-2 mt-0.5">
                            {c.sentence_type && <span className="text-xs text-slate-400">{c.sentence_type}</span>}
                            {c.party && <span className="text-xs text-slate-500">· {c.party}</span>}
                          </div>
                          {c.keywords?.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-1.5">
                              {c.keywords.slice(0, 4).map(kw => (
                                <span key={kw} className="px-1.5 py-0.5 bg-red-900/20 border border-red-900/30 rounded text-xs text-red-400">{kw}</span>
                              ))}
                            </div>
                          )}
                        </div>
                        <div className="text-right shrink-0 min-w-[80px]">
                          <div className="text-lg font-black" style={{ color: heatColor(c.risk_score) }}>{(c.risk_score * 100).toFixed(0)}%</div>
                          <div className="text-xs text-slate-500">₹{(c.financial_impact || 0).toLocaleString()}</div>
                        </div>
                        <div className="flex flex-col gap-1 shrink-0">
                          <button onClick={() => handleExplainFromTable(c.id)} className="px-2.5 py-1 bg-purple-600/80 hover:bg-purple-600 border border-purple-700/60 rounded-md text-xs text-white transition-colors">Explain</button>
                          <button onClick={() => handleBreakdownFromTable(c.id)} className="px-2.5 py-1 bg-orange-600/80 hover:bg-orange-600 border border-orange-700/60 rounded-md text-xs text-white transition-colors">Why</button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* GraphRAG Info Panel */}
                <div className="bg-gradient-to-r from-purple-900/20 to-cyan-900/20 border border-purple-700/40 rounded-2xl p-5">
                  <div className="flex items-center gap-3 mb-3">
                    <GitBranch className="w-5 h-5 text-purple-400" />
                    <h3 className="text-sm font-bold text-white">Advanced Graph Analysis (GraphRAG)</h3>
                  </div>
                  <p className="text-xs text-slate-300 mb-3">
                    Uses AI + Graph Database to find HIDDEN CONNECTIONS between clauses and answer complex questions like "Which clauses make YOU responsible?" or "Which risks trigger OTHER risks?"
                  </p>
                  <div className="grid grid-cols-3 gap-2">
                    <div className="bg-slate-900/60 border border-blue-700/30 rounded p-2">
                      <div className="text-xs font-bold text-blue-400">Contractor Risks</div>
                      <div className="text-xs text-slate-500">Clauses where YOU bear risk</div>
                    </div>
                    <div className="bg-slate-900/60 border border-cyan-700/30 rounded p-2">
                      <div className="text-xs font-bold text-cyan-400">Shared Liabilities</div>
                      <div className="text-xs text-slate-500">Affects BOTH parties equally</div>
                    </div>
                    <div className="bg-slate-900/60 border border-orange-700/30 rounded p-2">
                      <div className="text-xs font-bold text-orange-400">Cascading</div>
                      <div className="text-xs text-slate-500">One clause triggers others</div>
                    </div>
                  </div>
                </div>

                {/* Hidden + GraphRAG grid */}
                <div className="grid grid-cols-2 gap-5">
                  {/* Hidden Risk Clauses */}
                  {insights.hidden_risk_clauses?.length > 0 && (
                    <div className="bg-slate-900 border border-yellow-800/30 rounded-2xl p-6">
                      <h3 className="text-base font-bold text-white mb-1 flex items-center gap-2">
                        <Lock className="w-5 h-5 text-yellow-400" /> Hidden Risk Clauses
                      </h3>
                      <p className="text-xs text-yellow-600/80 mb-2">High-risk content disguised as Definitions or Headings</p>
                      <div className="bg-yellow-900/10 border border-yellow-700/30 rounded p-2 mb-3">
                        <p className="text-xs text-slate-300">⚠️ These look innocent but are LEGAL TRAPS! Read carefully.</p>
                      </div>
                      <div className="space-y-3">
                        {insights.hidden_risk_clauses.map((c, i) => (
                          <div key={i} className="bg-yellow-900/10 border border-yellow-900/30 rounded-xl p-3">
                            <div className="flex items-start justify-between gap-2">
                              <div>
                                <p className="text-white text-sm font-semibold">{c.clause_name}</p>
                                <p className="text-xs text-yellow-500/70 mt-0.5">{c.sentence_type} · {(c.risk_score * 100).toFixed(0)}% risk</p>
                                <p className="text-xs text-slate-500 mt-1 italic line-clamp-2">{c.text_preview}</p>
                              </div>
                              <button onClick={() => handleExplainFromTable(c.id)} className="px-2 py-1 bg-yellow-700/80 hover:bg-yellow-600 rounded-md text-xs text-white shrink-0 transition-colors">Explain</button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* GraphRAG Queries */}
                  <div className="space-y-4">
                    {[
                      { key: 'contractor_risks', label: 'Contractor High Risks', borderColor: 'border-blue-800/30', labelColor: 'text-blue-400', icon: Shield, bg: 'bg-blue-900/10' },
                      { key: 'shared_liabilities', label: 'Shared Liabilities', borderColor: 'border-cyan-800/30', labelColor: 'text-cyan-400', icon: GitBranch, bg: 'bg-cyan-900/10' },
                      { key: 'cascading_obligations', label: 'Cascading Obligations', borderColor: 'border-orange-800/30', labelColor: 'text-orange-400', icon: Activity, bg: 'bg-orange-900/10' },
                    ].map(({ key, label, borderColor, labelColor, icon: Icon, bg }) => (
                      <div key={key} className={`bg-slate-900 border ${borderColor} rounded-xl p-4`}>
                        <h4 className={`text-xs font-bold ${labelColor} flex items-center gap-1.5 mb-3`}>
                          <Icon className="w-3.5 h-3.5" /> {label}
                          <span className="ml-auto text-slate-500 font-normal">{(insights.graph_queries?.[key] || []).length} found</span>
                        </h4>
                        <div className="space-y-1.5">
                          {(insights.graph_queries?.[key] || []).length === 0
                            ? <p className="text-slate-500 text-xs italic">None identified</p>
                            : (insights.graph_queries[key]).map((c, i) => (
                              <div key={i} className={`${bg} border ${borderColor} rounded-lg p-2.5`}>
                                <p className="text-white text-xs font-medium">{c.clause_name}</p>
                                <p className={`text-xs ${labelColor} opacity-70 mt-0.5`}>{((c.risk_score || 0) * 100).toFixed(0)}% · {c.sentence_type || c.clause_type || ''}</p>
                              </div>
                            ))
                          }
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <NoData icon={Eye} message="No insights available. Process the contract with RRIE first." action={() => setTab('process')} actionLabel="Go to Process" />
            )}
          </div>
        )}

        {/* ══════════════════ DEAL SCORE TAB ══════════════════ */}
        {tab === 'deal' && (
          <div className="space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <Target className="w-5 h-5 text-green-400" /> Deal Scoring Engine
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">AI-powered go/no-go decision with quantitative risk scoring</p>
              </div>
              <button onClick={loadDealScore} disabled={!selectedContractId} className="px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 rounded-lg text-xs flex items-center gap-1.5">
                <RefreshCw className="w-3.5 h-3.5" /> Refresh
              </button>
            </div>

            {loadingDeal ? <LoadingSpinner color="green" /> : dealScore ? (
              <>
                {/* Decision hero */}
                <div className={`relative overflow-hidden rounded-2xl border-2 p-8 ${
                  dealScore.decision === 'GO' ? 'bg-green-950/40 border-green-600/60' :
                  dealScore.decision === 'NEGOTIATE' ? 'bg-yellow-950/40 border-yellow-600/60' :
                  'bg-red-950/40 border-red-600/60'
                }`}>
                  <div className={`absolute top-0 right-0 w-80 h-80 rounded-full blur-3xl opacity-10 ${
                    dealScore.decision === 'GO' ? 'bg-green-400' : dealScore.decision === 'NEGOTIATE' ? 'bg-yellow-400' : 'bg-red-400'
                  }`} />
                  <div className="relative flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-3 mb-3">
                        <Award className={`w-8 h-8 ${dealScore.decision === 'GO' ? 'text-green-400' : dealScore.decision === 'NEGOTIATE' ? 'text-yellow-400' : 'text-red-400'}`} />
                        <span className="text-slate-400 text-sm font-medium">RRIE Deal Decision</span>
                      </div>
                      <p className={`text-6xl font-black tracking-widest mb-3 ${
                        dealScore.decision === 'GO' ? 'text-green-400' : dealScore.decision === 'NEGOTIATE' ? 'text-yellow-400' : 'text-red-400'
                      }`}>{dealScore.decision}</p>
                      <p className="text-slate-300 text-base max-w-lg">{dealScore.summary}</p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="text-slate-400 text-xs mb-1 uppercase tracking-wider">Deal Score</p>
                      <p className={`text-7xl font-black leading-none ${
                        dealScore.deal_score > 70 ? 'text-green-400' : dealScore.deal_score > 40 ? 'text-yellow-400' : 'text-red-400'
                      }`}>{dealScore.deal_score}</p>
                      <p className="text-slate-500 text-sm mt-0.5">/ 100</p>
                      <div className="w-48 bg-slate-700/60 rounded-full h-3 mt-3 overflow-hidden">
                        <div className="h-3 rounded-full transition-all" style={{
                          width: `${dealScore.deal_score}%`,
                          background: dealScore.decision === 'GO' ? 'linear-gradient(90deg,#16a34a,#22c55e)' : dealScore.decision === 'NEGOTIATE' ? 'linear-gradient(90deg,#ca8a04,#eab308)' : 'linear-gradient(90deg,#dc2626,#ef4444)'
                        }} />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Metrics */}
                <div className="grid grid-cols-4 gap-4">
                  {[
                    { label: 'Total Clauses', value: dealScore.metrics?.total_clauses, unit: '', icon: FileText, color: 'blue' },
                    { label: 'Avg Risk', value: dealScore.metrics?.avg_risk_pct, unit: '%', icon: Activity, color: 'orange' },
                    { label: 'High Risk', value: `${dealScore.metrics?.high_risk_count} (${dealScore.metrics?.high_risk_pct}%)`, unit: '', icon: AlertTriangle, color: 'red' },
                    { label: 'Rights Ratio', value: dealScore.metrics?.rights_ratio?.toFixed(2), unit: 'x', icon: Star, color: 'green' },
                  ].map(({ label, value, unit, icon: Icon, color }) => (
                    <div key={label} className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-start gap-3">
                      <div className={`w-9 h-9 rounded-lg bg-${color}-900/30 border border-${color}-800/40 flex items-center justify-center shrink-0`}>
                        <Icon className={`w-5 h-5 text-${color}-400`} />
                      </div>
                      <div>
                        <p className="text-xl font-black text-white">{value}{unit}</p>
                        <p className="text-xs text-slate-500 mt-0.5">{label}</p>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="grid grid-cols-2 gap-5">
                  {/* Reasons */}
                  <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                    <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                      <Info className="w-5 h-5 text-blue-400" /> Key Decision Factors
                    </h3>
                    <div className="space-y-3">
                      {(dealScore.reasons || []).map((reason, i) => (
                        <div key={i} className="flex items-start gap-3 p-3 bg-slate-800/50 rounded-xl">
                          <div className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${
                            dealScore.decision === 'GO' ? 'bg-green-900/50 border border-green-700' :
                            dealScore.decision === 'NEGOTIATE' ? 'bg-yellow-900/50 border border-yellow-700' : 'bg-red-900/50 border border-red-700'
                          }`}>
                            <div className={`w-1.5 h-1.5 rounded-full ${
                              dealScore.decision === 'GO' ? 'bg-green-400' : dealScore.decision === 'NEGOTIATE' ? 'bg-yellow-400' : 'bg-red-400'
                            }`} />
                          </div>
                          <p className="text-slate-300 text-sm leading-relaxed">{reason}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Party Risk Balance */}
                  <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                    <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                      <BarChart2 className="w-5 h-5 text-cyan-400" /> Party Risk Balance
                    </h3>
                    <div className="space-y-4">
                      {[
                        { label: 'Contractor', val: dealScore.metrics?.contractor_risk || 0, color: '#3b82f6', bg: 'bg-blue-900/20' },
                        { label: 'Employer', val: dealScore.metrics?.employer_risk || 0, color: '#8b5cf6', bg: 'bg-purple-900/20' },
                      ].map(({ label, val, color, bg }) => {
                        const total = (dealScore.metrics?.contractor_risk || 0) + (dealScore.metrics?.employer_risk || 0) || 1;
                        const pct = Math.round(val / total * 100);
                        return (
                          <div key={label}>
                            <div className="flex justify-between text-sm mb-1.5">
                              <span style={{ color }} className="font-semibold">{label}</span>
                              <span className="text-slate-300 font-mono">{val.toFixed(3)} <span className="text-slate-500">({pct}%)</span></span>
                            </div>
                            <div className="bg-slate-700 rounded-full h-2.5 overflow-hidden">
                              <div className="h-2.5 rounded-full transition-all" style={{ width: `${pct}%`, background: color }} />
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* Score formula */}
                    <div className="mt-5 p-3 bg-slate-800/60 border border-slate-700/60 rounded-xl">
                      <p className="text-xs text-slate-400 font-mono leading-relaxed">
                        Score = 100 − (avg_risk×100) + (balance×5) + (rights_ratio×10) − (high_risk_pct×0.5)
                      </p>
                    </div>
                  </div>
                </div>

                {/* LLM Reasoning */}
                {dealScore.llm_reasoning && (
                  <div className="bg-slate-900 border border-purple-800/30 rounded-2xl p-6">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-9 h-9 rounded-xl bg-purple-900/30 border border-purple-800/40 flex items-center justify-center">
                        <Brain className="w-5 h-5 text-purple-400" />
                      </div>
                      <div>
                        <h3 className="text-base font-bold text-white">AI Business Recommendation</h3>
                        <p className="text-xs text-slate-500">Generated by AI</p>
                      </div>
                    </div>
                    <p className="text-slate-200 leading-relaxed text-sm border-l-2 border-purple-600/40 pl-4">{dealScore.llm_reasoning}</p>
                  </div>
                )}
              </>
            ) : (
              <NoData icon={Target} message="No deal score available. Process the contract with RRIE first." action={() => setTab('process')} actionLabel="Go to Process" />
            )}
          </div>
        )}

        {/* ══════════════════ EXPLAIN TAB ══════════════════ */}
        {tab === 'explain' && (
          <div className="space-y-5">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Lightbulb className="w-5 h-5 text-yellow-400" /> Clause Explainer
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">AI-powered clause meaning, risk explanation &amp; mitigation strategies</p>
            </div>

            {/* Clause selector */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Select Clause</label>
              {allClauses.length === 0 ? (
                <div className="flex items-center gap-3 p-3 bg-yellow-900/10 border border-yellow-800/30 rounded-xl">
                  <AlertCircle className="w-4 h-4 text-yellow-400 shrink-0" />
                  <p className="text-yellow-300 text-sm">No clauses loaded. Process the contract first or switch to Clause Table tab.</p>
                </div>
              ) : (
                <select
                  value={selectedClause || ''}
                  onChange={(e) => { if (e.target.value) handleExplainClause(e.target.value); }}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value="">— Select a clause to explain —</option>
                  {allClauses.map(c => (
                    <option key={c.id} value={c.id}>
                      {c.clause_name} · {c.sentence_type || '?'} · {c.party || '?'} · {((c.risk_score || 0) * 100).toFixed(0)}% risk
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Selected clause preview */}
            {selectedClauseData && (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
                <div className="flex items-start gap-4">
                  <div className="flex-1">
                    <p className="text-white font-bold text-base">{selectedClauseData.clause_name}</p>
                    <div className="flex flex-wrap gap-2 mt-2">
                      <span className={`px-2.5 py-1 rounded-md text-xs font-semibold border ${
                        selectedClauseData.sentence_type === 'RISK' ? 'bg-red-900/30 text-red-400 border-red-800/60' :
                        selectedClauseData.sentence_type === 'OBLIGATION' ? 'bg-yellow-900/30 text-yellow-400 border-yellow-800/60' :
                        'bg-slate-700 text-slate-300 border-slate-600'
                      }`}>{selectedClauseData.sentence_type}</span>
                      <span className={`px-2.5 py-1 rounded-md text-xs font-semibold border ${
                        selectedClauseData.party === 'CONTRACTOR' ? 'bg-blue-900/30 text-blue-400 border-blue-800/60' :
                        'bg-purple-900/30 text-purple-400 border-purple-800/60'
                      }`}>{selectedClauseData.party}</span>
                      <span className={`px-2.5 py-1 rounded-md text-xs font-semibold border ${riskBg(selectedClauseData.risk_level)}`}>{selectedClauseData.risk_level} RISK</span>
                    </div>
                    {selectedClauseData.text_preview && (
                      <p className="text-slate-400 text-xs mt-2 italic leading-relaxed">{selectedClauseData.text_preview}</p>
                    )}
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-3xl font-black" style={{ color: heatColor(selectedClauseData.risk_score) }}>{((selectedClauseData.risk_score || 0) * 100).toFixed(0)}%</p>
                    <p className="text-xs text-slate-500 mt-0.5">risk score</p>
                    <p className="text-sm font-mono text-slate-300 mt-1">₹{(selectedClauseData.financial_impact || 0).toLocaleString()}</p>
                  </div>
                </div>
              </div>
            )}

            {loadingExplanation ? (
              <div className="flex flex-col items-center justify-center py-16 gap-3">
                <Loader className="w-10 h-10 text-purple-400 animate-spin" />
                <p className="text-slate-400 text-sm">AI is analyzing this clause...</p>
              </div>
            ) : explanation?.error ? (
              <div className="bg-red-900/10 border border-red-800/40 rounded-2xl p-6 flex items-start gap-3">
                <XCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                <div>
                  <p className="text-red-400 font-semibold">Explanation Failed</p>
                  <p className="text-red-300/70 text-sm mt-1">{explanation.error}</p>
                </div>
              </div>
            ) : explanation ? (
              <div className="grid grid-cols-2 gap-4">
                {[
                  { key: 'meaning', label: 'Plain Language Meaning', color: 'purple', icon: FileText },
                  { key: 'risk_explanation', label: 'Risk Explanation', color: 'red', icon: AlertTriangle },
                  { key: 'impact', label: 'Business Impact', color: 'blue', icon: TrendingDown },
                  { key: 'mitigation', label: 'Mitigation Strategies', color: 'green', icon: Shield },
                ].filter(({ key }) => explanation[key]).map(({ key, label, color, icon: Icon }) => (
                  <div key={key} className={`bg-${color}-900/10 border border-${color}-800/30 rounded-2xl p-5`}>
                    <div className="flex items-center gap-2 mb-3">
                      <Icon className={`w-4 h-4 text-${color}-400`} />
                      <h3 className={`text-sm font-bold text-${color}-400`}>{label}</h3>
                    </div>
                    <p className="text-slate-200 text-sm leading-relaxed">{explanation[key]}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-16 gap-3">
                <Lightbulb className="w-12 h-12 text-slate-600" />
                <p className="text-slate-400">Select a clause above to generate an AI explanation</p>
              </div>
            )}
          </div>
        )}

        {/* ══════════════════ RISK BREAKDOWN TAB ══════════════════ */}
        {tab === 'breakdown' && (
          <div className="space-y-5">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-orange-400" /> Risk Breakdown
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">Keyword-level risk decomposition — see exactly what drives each clause's risk score</p>
            </div>

            {/* Clause selector */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Select Clause</label>
              {allClauses.length === 0 ? (
                <div className="flex items-center gap-3 p-3 bg-yellow-900/10 border border-yellow-800/30 rounded-xl">
                  <AlertCircle className="w-4 h-4 text-yellow-400 shrink-0" />
                  <p className="text-yellow-300 text-sm">No clauses loaded. Process the contract first or switch to Clause Table tab.</p>
                </div>
              ) : (
                <select
                  value={selectedClause || ''}
                  onChange={(e) => { if (e.target.value) handleRiskBreakdown(e.target.value); }}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white text-sm focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                >
                  <option value="">— Select a clause for risk breakdown —</option>
                  {allClauses.map(c => (
                    <option key={c.id} value={c.id}>
                      {c.clause_name} · {c.risk_level || 'N/A'} · {((c.risk_score || 0) * 100).toFixed(0)}% risk
                    </option>
                  ))}
                </select>
              )}
            </div>

            {loadingBreakdown ? (
              <div className="flex flex-col items-center justify-center py-16 gap-3">
                <Loader className="w-10 h-10 text-orange-400 animate-spin" />
                <p className="text-slate-400 text-sm">Computing risk decomposition...</p>
              </div>
            ) : riskBreakdown?.error ? (
              <div className="bg-red-900/10 border border-red-800/40 rounded-2xl p-6 flex items-start gap-3">
                <XCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                <p className="text-red-300">{riskBreakdown.error}</p>
              </div>
            ) : riskBreakdown ? (
              <>
                {/* Enhanced Score Cards with Glassmorphism */}
                <div className="grid grid-cols-4 gap-4">
                  {[
                    { label: 'Total Raw Score', value: riskBreakdown.total_score, unit: '', color: '#94a3b8', gradient: 'from-slate-600/20 to-slate-700/20', icon: '📊' },
                    { label: 'Normalized Risk', value: `${((riskBreakdown.normalized_score || 0) * 100).toFixed(0)}%`, unit: '', color: heatColor(riskBreakdown.normalized_score), gradient: riskBreakdown.normalized_score >= 0.6 ? 'from-red-600/20 to-orange-600/20' : riskBreakdown.normalized_score >= 0.3 ? 'from-yellow-600/20 to-orange-600/20' : 'from-green-600/20 to-emerald-600/20', icon: '📈' },
                    { label: 'Risk Level', value: riskBreakdown.risk_level, unit: '', color: COLORS[riskBreakdown.risk_level] || '#94a3b8', gradient: riskBreakdown.risk_level === 'HIGH' ? 'from-red-600/20 to-pink-600/20' : riskBreakdown.risk_level === 'MEDIUM' ? 'from-yellow-600/20 to-orange-600/20' : 'from-green-600/20 to-cyan-600/20', icon: riskBreakdown.risk_level === 'HIGH' ? '🔴' : riskBreakdown.risk_level === 'MEDIUM' ? '🟡' : '🟢' },
                    { label: 'Financial Exposure', value: riskBreakdown.financial_impact?.formatted || '₹0', unit: '', color: '#f97316', gradient: 'from-orange-600/20 to-red-600/20', icon: '💰' },
                  ].map(({ label, value, color, gradient, icon }) => (
                    <div key={label} className={`relative bg-gradient-to-br ${gradient} backdrop-blur-xl border border-slate-700/50 rounded-2xl p-5 overflow-hidden group hover:scale-105 transition-all duration-300 hover:shadow-xl`}
                      style={{ boxShadow: `0 10px 40px ${color}15` }}>
                      {/* Animated gradient blob */}
                      <div className="absolute -top-10 -right-10 w-32 h-32 bg-gradient-to-br opacity-20 rounded-full blur-2xl group-hover:opacity-30 transition-opacity"
                        style={{ background: `radial-gradient(circle, ${color}40 0%, transparent 70%)` }}></div>

                      {/* Icon */}
                      <div className="text-3xl mb-2 relative z-10">{icon}</div>

                      {/* Label */}
                      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 relative z-10">{label}</p>

                      {/* Value with text shadow */}
                      <p className="text-3xl font-black relative z-10 transition-all group-hover:scale-110"
                        style={{
                          color,
                          textShadow: `0 2px 20px ${color}60, 0 0 40px ${color}40`
                        }}>
                        {value}
                      </p>
                    </div>
                  ))}
                </div>

                {/* Enhanced Keyword Breakdown with Glassmorphism */}
                <div className="relative bg-gradient-to-br from-slate-900/90 via-slate-900/50 to-slate-800/90 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-6 overflow-hidden">
                  {/* Floating gradient blob */}
                  <div className="absolute -top-20 -right-20 w-60 h-60 bg-gradient-to-br from-orange-600/10 to-red-600/10 rounded-full blur-3xl"></div>

                  <h3 className="text-base font-bold text-white mb-1 flex items-center gap-2 relative z-10">
                    <div className="p-2 bg-gradient-to-br from-orange-600/20 to-red-600/20 rounded-lg border border-orange-700/40">
                      <Cpu className="w-5 h-5 text-orange-400" />
                    </div>
                    <span className="bg-gradient-to-r from-orange-400 via-red-400 to-orange-400 bg-clip-text text-transparent">
                      Keyword Risk Contributions
                    </span>
                  </h3>
                  <p className="text-xs text-slate-400 mb-6 relative z-10">Each detected risk keyword and its percentage contribution to the total risk score</p>

                  {riskBreakdown.keyword_contributions?.length > 0 ? (
                    <div className="space-y-3 relative z-10">
                      {riskBreakdown.keyword_contributions.map((kw, i) => {
                        const barColor = kw.contribution_pct >= 10 ? ['#ef4444', '#dc2626'] : kw.contribution_pct >= 7 ? ['#f97316', '#ea580c'] : ['#fb923c', '#f97316'];
                        return (
                          <div key={i}
                            className="relative bg-gradient-to-r from-slate-800/80 via-slate-800/40 to-slate-800/80 backdrop-blur-sm border border-slate-700/50 rounded-xl p-4 overflow-hidden group hover:scale-[1.02] hover:border-orange-700/60 transition-all duration-300"
                            style={{
                              animationDelay: `${i * 50}ms`,
                              animation: 'fadeIn 0.5s ease-out forwards'
                            }}>
                            {/* Shimmer effect on hover */}
                            <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                              style={{
                                background: 'linear-gradient(90deg, transparent, rgba(249, 115, 22, 0.1), transparent)',
                                animation: 'shimmer 2s infinite'
                              }}></div>

                            <div className="flex items-center justify-between mb-3 relative z-10">
                              <div className="flex items-center gap-3">
                                <span className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold border shadow-lg transition-all group-hover:scale-110`}
                                  style={{
                                    background: `linear-gradient(135deg, ${barColor[0]}30, ${barColor[1]}30)`,
                                    borderColor: `${barColor[0]}60`,
                                    color: barColor[0],
                                    boxShadow: `0 4px 12px ${barColor[0]}30`
                                  }}>
                                  {i + 1}
                                </span>
                                <span className="font-bold text-white capitalize text-sm">{kw.keyword}</span>
                              </div>
                              <div className="flex items-center gap-4">
                                <span className="text-xs text-slate-400">
                                  Weight: <span className="text-slate-200 font-mono font-semibold">{kw.weight}</span>
                                </span>
                                <span className="text-lg font-black px-3 py-1 rounded-lg"
                                  style={{
                                    color: barColor[0],
                                    background: `${barColor[0]}20`,
                                    textShadow: `0 2px 10px ${barColor[0]}50`
                                  }}>
                                  {kw.contribution_pct}%
                                </span>
                              </div>
                            </div>

                            {/* Enhanced progress bar with gradient and glow */}
                            <div className="relative w-full bg-slate-700/50 rounded-full h-3 overflow-hidden border border-slate-600/50">
                              <div
                                className="h-3 rounded-full relative transition-all duration-1000 ease-out"
                                style={{
                                  width: `${kw.contribution_pct}%`,
                                  background: `linear-gradient(90deg, ${barColor[0]}, ${barColor[1]})`,
                                  boxShadow: `0 0 20px ${barColor[0]}60, inset 0 1px 0 rgba(255,255,255,0.3)`
                                }}>
                                {/* Animated shimmer overlay */}
                                <div className="absolute inset-0 opacity-50"
                                  style={{
                                    background: 'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.3) 50%, transparent 100%)',
                                    animation: 'shimmer 2s infinite'
                                  }}></div>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="text-slate-500 text-center py-8 italic">No risk keywords detected in this clause</p>
                  )}

                  {riskBreakdown.explanation && (
                    <div className="mt-5 p-4 bg-blue-900/10 border border-blue-800/30 rounded-xl flex items-start gap-3">
                      <Info className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
                      <p className="text-blue-200 text-sm leading-relaxed">{riskBreakdown.explanation}</p>
                    </div>
                  )}
                </div>

                {/* Enhanced Visual Chart with Glassmorphism */}
                {riskBreakdown.keyword_contributions?.length > 0 && (
                  <div className="relative bg-gradient-to-br from-slate-900/90 via-slate-900/50 to-slate-800/90 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-6 overflow-hidden">
                    {/* Floating gradient blobs */}
                    <div className="absolute -bottom-20 -left-20 w-60 h-60 bg-gradient-to-br from-orange-600/10 to-red-600/10 rounded-full blur-3xl"></div>
                    <div className="absolute -top-20 -right-20 w-40 h-40 bg-gradient-to-br from-red-600/10 to-pink-600/10 rounded-full blur-3xl"></div>

                    <div className="relative z-10">
                      <div className="flex items-center gap-3 mb-6">
                        <div className="p-2 bg-gradient-to-br from-orange-600/20 to-red-600/20 rounded-lg border border-orange-700/40">
                          <TrendingDown className="w-5 h-5 text-orange-400" />
                        </div>
                        <div>
                          <h3 className="text-base font-bold bg-gradient-to-r from-orange-400 via-red-400 to-orange-400 bg-clip-text text-transparent">
                            Visual Contribution Chart
                          </h3>
                          <p className="text-xs text-slate-400">Top contributors ranked by impact</p>
                        </div>
                      </div>

                      <div className="bg-slate-900/40 backdrop-blur-sm border border-slate-700/30 rounded-xl p-4">
                        <ResponsiveContainer width="100%" height={300}>
                          <BarChart
                            data={riskBreakdown.keyword_contributions.slice(0, 10)}
                            layout="vertical"
                            barSize={20}
                            margin={{ top: 5, right: 30, left: 10, bottom: 5 }}>
                            <defs>
                              {/* Gradient definitions for bars */}
                              <linearGradient id="barGradient" x1="0" y1="0" x2="1" y2="0">
                                <stop offset="0%" stopColor="#f97316" stopOpacity={0.8} />
                                <stop offset="50%" stopColor="#ef4444" stopOpacity={0.9} />
                                <stop offset="100%" stopColor="#dc2626" stopOpacity={1} />
                              </linearGradient>
                              <filter id="glow">
                                <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
                                <feMerge>
                                  <feMergeNode in="coloredBlur"/>
                                  <feMergeNode in="SourceGraphic"/>
                                </feMerge>
                              </filter>
                            </defs>
                            <CartesianGrid
                              strokeDasharray="3 3"
                              stroke="#334155"
                              horizontal={true}
                              vertical={false}
                              opacity={0.3} />
                            <XAxis
                              type="number"
                              domain={[0, 'dataMax']}
                              stroke="#64748b"
                              tick={{ fontSize: 11, fill: '#94a3b8', fontWeight: 600 }}
                              tickLine={{ stroke: '#475569' }}
                              axisLine={{ stroke: '#475569' }}
                              unit="%"
                              label={{ value: 'Contribution (%)', position: 'insideBottom', offset: -5, style: { fill: '#94a3b8', fontSize: 11, fontWeight: 600 } }} />
                            <YAxis
                              type="category"
                              dataKey="keyword"
                              stroke="#64748b"
                              tick={{ fontSize: 11, fill: '#cbd5e1', fontWeight: 600 }}
                              tickLine={false}
                              axisLine={{ stroke: '#475569' }}
                              width={120}
                              tickFormatter={(value) => value.charAt(0).toUpperCase() + value.slice(1)} />
                            <Tooltip
                              content={<CustomTooltip />}
                              cursor={{ fill: 'rgba(249, 115, 22, 0.1)' }}
                              contentStyle={{
                                background: 'rgba(15, 23, 42, 0.95)',
                                backdropFilter: 'blur(12px)',
                                border: '1px solid rgba(100, 116, 139, 0.3)',
                                borderRadius: '12px',
                                padding: '12px',
                                boxShadow: '0 10px 40px rgba(0, 0, 0, 0.5)'
                              }}
                              labelStyle={{ color: '#f1f5f9', fontWeight: 600, marginBottom: '4px' }}
                              itemStyle={{ color: '#f97316', fontWeight: 600 }}
                              formatter={(v) => [`${v}%`, 'Contribution']} />
                            <Bar
                              dataKey="contribution_pct"
                              fill="url(#barGradient)"
                              radius={[0, 8, 8, 0]}
                              filter="url(#glow)"
                              animationDuration={1000}
                              animationBegin={200} />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>

                      {/* Summary info */}
                      <div className="mt-4 p-3 bg-gradient-to-r from-blue-900/20 to-cyan-900/20 border border-blue-700/30 rounded-xl">
                        <p className="text-xs text-blue-300 leading-relaxed flex items-start gap-2">
                          <Info className="w-4 h-4 shrink-0 mt-0.5" />
                          <span>
                            Risk driven by <strong className="text-blue-200">{riskBreakdown.keyword_contributions.slice(0, 3).map(k => k.keyword).join(', ')}</strong> ({riskBreakdown.keyword_contributions.slice(0, 3).reduce((sum, k) => sum + k.contribution_pct, 0).toFixed(1)}% of total risk). Focus negotiation efforts on mitigating these keywords.
                          </span>
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="flex flex-col items-center justify-center py-16 gap-3">
                <AlertCircle className="w-12 h-12 text-slate-600" />
                <p className="text-slate-400">Select a clause above to view keyword risk breakdown</p>
              </div>
            )}
          </div>
        )}

        {/* ══════════════════ GRAPH VIEW TAB ══════════════════ */}
        {tab === 'graph' && (
            <div className="space-y-4">
              {/* Header */}
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-white flex items-center gap-2">
                    <Network className="w-5 h-5 text-cyan-400" /> Contract Risk Intelligence Graph
                  </h2>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Neo4j-style knowledge graph · {graphData?.stats?.total_nodes || 0} nodes · {graphData?.stats?.total_edges || 0} edges · real contract data
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {/* Filter */}
                  <div className="flex bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
                    {[
                      { id: 'all', label: 'All' },
                      { id: 'high', label: 'High Risk' },
                      { id: 'risk', label: 'Risk Type' },
                      { id: 'obligation', label: 'Obligations' },
                    ].map(f => (
                      <button key={f.id} onClick={() => setGraphFilter(f.id)}
                        className={`px-3 py-1.5 text-xs font-medium transition-colors ${graphFilter === f.id ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'}`}>
                        {f.label}
                      </button>
                    ))}
                  </div>
                  <button onClick={loadGraph} disabled={!selectedContractId} className="p-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 rounded-lg transition-colors" title="Refresh">
                    <RefreshCw className="w-4 h-4" />
                  </button>
                  <button onClick={() => setIsFullscreen(f => !f)} className="p-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 rounded-lg transition-colors" title="Fullscreen">
                    <Maximize2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Legend bar */}
              <div className="flex flex-wrap items-center gap-4 bg-slate-900/80 border border-slate-800 rounded-xl px-5 py-3 backdrop-blur">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Node Types:</span>
                {[
                  { label: 'Contract', color: '#eab308', Icon: Zap },
                  { label: 'Party', color: '#06b6d4', Icon: Users },
                  { label: 'High Risk', color: '#ef4444', Icon: AlertTriangle },
                  { label: 'Medium Risk', color: '#f59e0b', Icon: AlertTriangle },
                  { label: 'Low Risk', color: '#10b981', Icon: Shield },
                  { label: 'Clause', color: '#94a3b8', Icon: FileText },
                ].map(({ label, color, Icon }) => (
                  <div key={label} className="flex items-center gap-1.5">
                    <div className="w-6 h-6 rounded-lg border flex items-center justify-center" style={{ borderColor: `${color}55`, background: `${color}18` }}>
                      <Icon style={{ width: 12, height: 12, color }} />
                    </div>
                    <span className="text-xs text-slate-400">{label}</span>
                  </div>
                ))}
                <div className="ml-auto flex gap-5 text-xs text-slate-500">
                  <span className="flex items-center gap-1.5"><span className="inline-block w-7 h-0 border-t border-dashed border-slate-500"></span>belongs_to</span>
                  <span className="flex items-center gap-1.5"><span className="inline-block w-7 h-0 border-t-2 border-blue-500"></span>affects</span>
                  <span className="flex items-center gap-1.5"><span className="inline-block w-7 h-0 border-t-2 border-red-500"></span>has_risk</span>
                </div>
              </div>

              {loadingGraph ? (
                <LoadingSpinner color="cyan" />
              ) : rfNodes.length > 0 ? (
                <>
                  {/* Fullscreen overlay — covers entire viewport including sidebar/header */}
                  {isFullscreen && (
                    <div style={{ position: 'fixed', inset: 0, zIndex: 9999, background: '#050a14' }}>
                      <ReactFlow
                        nodes={graphFilteredNodes}
                        edges={graphFilteredEdges}
                        onNodesChange={onNodesChange}
                        onEdgesChange={onEdgesChange}
                        onNodeClick={onNodeClick}
                        onPaneClick={onPaneClick}
                        nodeTypes={rfNodeTypes}
                        fitView
                        fitViewOptions={{ padding: 0.12 }}
                        minZoom={0.05}
                        maxZoom={3}
                        style={{ width: '100vw', height: '100vh' }}
                      >
                        <Background color="#0f172a" gap={28} size={1} />
                        <Controls style={{ background: 'rgba(15,20,35,0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10 }} />
                        <MiniMap
                          nodeColor={(n) => {
                            if (n.type === 'contractNode') return '#eab308';
                            if (n.type === 'partyNode') return n.data?.label === 'CONTRACTOR' ? '#3b82f6' : n.data?.label === 'EMPLOYER' ? '#8b5cf6' : '#06b6d4';
                            if (n.type === 'riskNode') return n.data?.color || '#ef4444';
                            return n.data?.risk_level === 'HIGH' ? '#ef4444' : n.data?.risk_level === 'MEDIUM' ? '#f59e0b' : '#10b981';
                          }}
                          style={{ background: 'rgba(8,13,26,0.95)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10 }}
                          maskColor="rgba(0,0,0,0.6)"
                        />
                        {/* Exit button */}
                        <div style={{ position: 'absolute', top: 20, right: 20, zIndex: 10 }}>
                          <button onClick={() => setIsFullscreen(false)}
                            style={{ background: 'rgba(15,20,35,0.95)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', padding: '10px 20px', borderRadius: 12, fontSize: 13, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', backdropFilter: 'blur(10px)', boxShadow: '0 4px 24px rgba(0,0,0,0.5)' }}>
                            <Maximize2 style={{ width: 16, height: 16 }} /> Exit Fullscreen
                          </button>
                        </div>
                        {/* Title */}
                        <div style={{ position: 'absolute', top: 20, left: 20, zIndex: 5, pointerEvents: 'none' }}>
                          <div style={{ background: 'rgba(8,13,26,0.9)', border: '1px solid rgba(6,182,212,0.3)', borderRadius: 12, padding: '10px 16px', backdropFilter: 'blur(10px)' }}>
                            <p style={{ color: '#06b6d4', fontSize: 12, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 6 }}>
                              <Network style={{ width: 13, height: 13 }} /> RRIE Knowledge Graph — FULLSCREEN
                            </p>
                            <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: 11, marginTop: 2 }}>{graphData?.contract_name}</p>
                          </div>
                        </div>
                        {/* Node detail in fullscreen */}
                        {selectedNode && (
                          <div style={{ position: 'absolute', top: 80, right: 20, width: 260, background: 'rgba(8,13,26,0.95)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 16, padding: 18, backdropFilter: 'blur(10px)', zIndex: 10 }}>
                            <p style={{ color: '#fff', fontSize: 13, fontWeight: 700, marginBottom: 10 }}>{selectedNode.data?.label}</p>
                            {selectedNode.type === 'clauseNode' && (
                              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                                {[['Sentence', selectedNode.data?.sentence_type], ['Party', selectedNode.data?.party], ['Risk', `${selectedNode.data?.risk_score}%`], ['Level', selectedNode.data?.risk_level], ['Impact', `₹${(selectedNode.data?.financial_impact||0).toLocaleString()}`]].map(([k, v]) => (
                                  <div key={k} style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span style={{ color: 'rgba(255,255,255,0.4)', fontSize: 11 }}>{k}</span>
                                    <span style={{ color: '#fff', fontSize: 11, fontWeight: 700 }}>{v}</span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                      </ReactFlow>
                    </div>
                  )}

                  {/* Normal (non-fullscreen) graph */}
                  <div className="relative">
                    <div
                      className="border border-slate-700/60 rounded-2xl overflow-hidden"
                      style={{
                        height: '680px',
                        background: 'radial-gradient(ellipse at 20% 20%, rgba(6,182,212,0.04) 0%, transparent 60%), radial-gradient(ellipse at 80% 80%, rgba(139,92,246,0.04) 0%, transparent 60%), linear-gradient(135deg, #050a14 0%, #080d1a 50%, #05080f 100%)',
                      }}
                    >
                      <ReactFlow
                        nodes={graphFilteredNodes}
                        edges={graphFilteredEdges}
                        onNodesChange={onNodesChange}
                        onEdgesChange={onEdgesChange}
                        onNodeClick={onNodeClick}
                        onPaneClick={onPaneClick}
                        nodeTypes={rfNodeTypes}
                        fitView
                        fitViewOptions={{ padding: 0.15 }}
                        minZoom={0.05}
                        maxZoom={3}
                        attributionPosition="bottom-left"
                      >
                        <Background color="#0f172a" gap={28} size={1} />
                        <Controls style={{ background: 'rgba(15,20,35,0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10 }} />
                        <MiniMap
                          nodeColor={(n) => {
                            if (n.type === 'contractNode') return '#eab308';
                            if (n.type === 'partyNode') return n.data?.label === 'CONTRACTOR' ? '#3b82f6' : n.data?.label === 'EMPLOYER' ? '#8b5cf6' : '#06b6d4';
                            if (n.type === 'riskNode') return n.data?.color || '#ef4444';
                            return n.data?.risk_level === 'HIGH' ? '#ef4444' : n.data?.risk_level === 'MEDIUM' ? '#f59e0b' : '#10b981';
                          }}
                          style={{ background: 'rgba(8,13,26,0.95)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10 }}
                          maskColor="rgba(0,0,0,0.6)"
                        />
                        {/* Graph title overlay */}
                        <div style={{ position: 'absolute', top: 14, left: 14, zIndex: 5, pointerEvents: 'none' }}>
                          <div className="bg-slate-900/80 border border-slate-700/60 rounded-xl px-4 py-2.5 backdrop-blur">
                            <p className="text-xs font-bold text-cyan-400 flex items-center gap-1.5">
                              <Network style={{ width: 12, height: 12 }} /> RRIE Knowledge Graph
                            </p>
                            <p className="text-xs text-slate-500 mt-0.5">{graphData?.contract_name}</p>
                          </div>
                        </div>
                      </ReactFlow>
                    </div>

                    {/* Node detail panel */}
                    {selectedNode && (
                      <div className="absolute top-4 right-4 w-72 bg-slate-900/95 border border-slate-700 rounded-2xl p-5 backdrop-blur shadow-2xl z-10">
                      <div className="flex items-center justify-between mb-4">
                        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Node Detail</span>
                        <button onClick={() => setSelectedNode(null)} className="text-slate-500 hover:text-white text-lg leading-none">×</button>
                      </div>
                      <p className="text-white font-bold text-sm mb-3">{selectedNode.data?.label}</p>
                      <div className="space-y-2">
                        {selectedNode.type === 'clauseNode' && <>
                          {[
                            { k: 'Type', v: selectedNode.data?.clause_type || 'N/A' },
                            { k: 'Sentence', v: selectedNode.data?.sentence_type },
                            { k: 'Party', v: selectedNode.data?.party },
                            { k: 'Risk Score', v: `${selectedNode.data?.risk_score}%` },
                            { k: 'Risk Level', v: selectedNode.data?.risk_level },
                            { k: 'Fin. Impact', v: `₹${(selectedNode.data?.financial_impact || 0).toLocaleString()}` },
                          ].map(({ k, v }) => (
                            <div key={k} className="flex justify-between items-center">
                              <span className="text-xs text-slate-500">{k}</span>
                              <span className={`text-xs font-bold ${
                                v === 'HIGH' ? 'text-red-400' : v === 'MEDIUM' ? 'text-yellow-400' :
                                v === 'CONTRACTOR' ? 'text-blue-400' : v === 'EMPLOYER' ? 'text-purple-400' :
                                v === 'SHARED' ? 'text-cyan-400' : 'text-slate-200'
                              }`}>{v}</span>
                            </div>
                          ))}
                          <div className="mt-2 pt-2 border-t border-slate-800">
                            <div className="flex justify-between text-xs mb-1">
                              <span className="text-slate-500">Risk</span>
                              <span style={{ color: selectedNode.data?.risk_level === 'HIGH' ? '#ef4444' : selectedNode.data?.risk_level === 'MEDIUM' ? '#f59e0b' : '#10b981' }}>{selectedNode.data?.risk_score}%</span>
                            </div>
                            <div className="bg-slate-700 rounded-full h-2">
                              <div className="h-2 rounded-full" style={{
                                width: `${selectedNode.data?.risk_score}%`,
                                background: selectedNode.data?.risk_level === 'HIGH' ? 'linear-gradient(90deg,#dc2626,#ef4444)' : selectedNode.data?.risk_level === 'MEDIUM' ? 'linear-gradient(90deg,#ca8a04,#f59e0b)' : 'linear-gradient(90deg,#16a34a,#10b981)'
                              }} />
                            </div>
                          </div>
                        </>}
                        {selectedNode.type === 'partyNode' && (
                          <div className="p-3 bg-slate-800/60 rounded-xl">
                            <p className="text-slate-400 text-xs">Clauses attributed to this party</p>
                            <p className="text-white text-2xl font-black mt-1">{selectedNode.data?.count}</p>
                          </div>
                        )}
                        {selectedNode.type === 'riskNode' && (
                          <div className="p-3 bg-slate-800/60 rounded-xl">
                            <p className="text-slate-400 text-xs">Clauses at this risk level</p>
                            <p className="text-2xl font-black mt-1" style={{ color: selectedNode.data?.color }}>{selectedNode.data?.count}</p>
                          </div>
                        )}
                        {selectedNode.type === 'contractNode' && (
                          <div className="p-3 bg-slate-800/60 rounded-xl">
                            <p className="text-slate-400 text-xs">Total clauses in contract</p>
                            <p className="text-yellow-400 text-2xl font-black mt-1">{selectedNode.data?.clause_count}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
                </>
              ) : (
                <NoData icon={Network} message="No graph data. Process the contract with RRIE first." action={() => setTab('process')} actionLabel="Go to Process" />
              )}

              {/* Stats row */}
              {graphData && (
                <div className="grid grid-cols-6 gap-3">
                  {[
                    { label: 'Total Nodes', value: graphData.stats?.total_nodes, color: '#06b6d4' },
                    { label: 'Total Edges', value: graphData.stats?.total_edges, color: '#3b82f6' },
                    { label: 'Clauses', value: graphData.stats?.total_clauses, color: '#8b5cf6' },
                    { label: 'Party Nodes', value: 3, color: '#06b6d4' },
                    { label: 'Risk Nodes', value: 3, color: '#ef4444' },
                    { label: 'Contract Hub', value: 1, color: '#eab308' },
                  ].map(({ label, value, color }) => (
                    <div key={label} className="bg-slate-900 border border-slate-800 rounded-xl p-3 text-center">
                      <p className="text-xl font-black" style={{ color }}>{value}</p>
                      <p className="text-xs text-slate-500 mt-0.5">{label}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
        )}

        {/* ══════════════════ RL NEGOTIATION TAB ══════════════════ */}
        {tab === 'rl' && (
          <div className="space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <Bot className="w-5 h-5 text-purple-400" /> RL Negotiation Engine
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">Q-Learning AI recommends optimal negotiation action per clause</p>
              </div>
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-2 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2">
                  <Play className="w-3.5 h-3.5 text-purple-400" />
                  <span className="text-xs text-slate-400">Simulations:</span>
                  <select
                    value={rlSimCount}
                    onChange={e => setRlSimCount(Number(e.target.value))}
                    className="bg-slate-900 text-white text-sm font-medium border border-slate-700 rounded px-2 py-1 focus:outline-none focus:border-purple-500 cursor-pointer hover:bg-slate-800 transition-colors"
                    style={{
                      backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e")`,
                      backgroundPosition: 'right 0.25rem center',
                      backgroundRepeat: 'no-repeat',
                      backgroundSize: '1.25em 1.25em',
                      paddingRight: '2rem',
                      appearance: 'none'
                    }}
                  >
                    {[100, 250, 500, 1000, 2000].map(n => <option key={n} value={n} className="bg-slate-900 text-white">{n}</option>)}
                  </select>
                </div>
                <button
                  onClick={() => { setRlData(null); loadRL(rlSimCount); }}
                  disabled={!selectedContractId || loadingRL}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white rounded-lg text-xs flex items-center gap-1.5 font-medium transition-colors"
                >
                  {loadingRL ? <Loader className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                  Run Simulation
                </button>
              </div>
            </div>

            {loadingRL ? (
              <div className="flex flex-col items-center justify-center py-16 gap-3">
                <Bot className="w-10 h-10 text-purple-400 animate-pulse" />
                <p className="text-slate-300 text-sm font-medium">Running {rlSimCount} Q-Learning simulations...</p>
                <p className="text-slate-500 text-xs">Agent is learning optimal negotiation strategies</p>
              </div>
            ) : rlData ? (
              <>
                {/* Portfolio verdict */}
                <div className="bg-slate-900 border border-purple-800/40 rounded-2xl p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-xl bg-purple-900/30 border border-purple-800/40 flex items-center justify-center">
                        <Bot className="w-7 h-7 text-purple-400" />
                      </div>
                      <div>
                        <p className="text-xs text-purple-400 font-medium uppercase tracking-wider">Portfolio Strategy</p>
                        <p className="text-xl font-bold text-white mt-0.5">{rlData.portfolio_verdict}</p>
                        <p className="text-xs text-slate-400 mt-0.5">{rlData.simulations_run} simulations · {rlData.total_clauses} clauses analyzed</p>
                      </div>
                    </div>
                    <div className="flex gap-4">
                      {[
                        { label: 'Accept', pct: rlData.accept_pct, color: '#10b981' },
                        { label: 'Negotiate', pct: rlData.negotiate_pct, color: '#3b82f6' },
                        { label: 'Reject', pct: rlData.reject_pct, color: '#ef4444' },
                      ].map(({ label, pct, color }) => (
                        <div key={label} className="text-center">
                          <p className="text-2xl font-black" style={{ color }}>{pct}%</p>
                          <p className="text-xs text-slate-500">{label}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Action distribution bar */}
                  <div className="mt-5">
                    <p className="text-xs text-slate-500 mb-2">Action Distribution</p>
                    <div className="flex rounded-full overflow-hidden h-3">
                      {Object.entries(rlData.action_summary || {}).map(([action, count]) => {
                        const pct = Math.round(count / rlData.total_clauses * 100);
                        const cfg = ACTION_CONFIG[action];
                        return pct > 0 ? (
                          <div key={action} title={`${action}: ${count} clauses (${pct}%)`}
                            style={{ width: `${pct}%`, background: cfg?.color || '#64748b' }} />
                        ) : null;
                      })}
                    </div>
                    <div className="flex flex-wrap gap-3 mt-2">
                      {Object.entries(rlData.action_summary || {}).map(([action, count]) => {
                        const cfg = ACTION_CONFIG[action];
                        const Icon = cfg?.icon || Shield;
                        return (
                          <div key={action} className="flex items-center gap-1.5">
                            <Icon className="w-3 h-3" style={{ color: cfg?.color }} />
                            <span className="text-xs text-slate-400 capitalize">{action.replace(/_/g, ' ')}</span>
                            <span className="text-xs font-bold text-slate-300">{count}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>

                {/* Clause list + detail panel */}
                <div className="grid grid-cols-5 gap-5">
                  {/* Clause list */}
                  <div className="col-span-3 space-y-3">
                    <div className="flex items-center gap-2">
                      <div className="relative flex-1">
                        <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                        <input
                          type="text"
                          placeholder="Filter clauses..."
                          value={rlFilter}
                          onChange={e => setRlFilter(e.target.value)}
                          className="w-full pl-8 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        />
                      </div>
                    </div>

                    <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
                      {(rlData.clauses || [])
                        .filter(c => !rlFilter || c.clause_name.toLowerCase().includes(rlFilter.toLowerCase()))
                        .map(c => {
                          const cfg = ACTION_CONFIG[c.best_action] || {};
                          const Icon = cfg.icon || Shield;
                          const isSelected = rlSelectedClause?.id === c.id;
                          return (
                            <div
                              key={c.id}
                              onClick={() => setRlSelectedClause(c)}
                              className={`bg-slate-900 border rounded-xl p-4 cursor-pointer transition-all hover:border-purple-700/50 ${isSelected ? 'border-purple-600/60 bg-purple-900/10' : 'border-slate-800'}`}
                            >
                              <div className="flex items-start gap-3">
                                <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 border ${cfg.bg} ${cfg.border}`}>
                                  <Icon className="w-5 h-5" style={{ color: cfg.color }} />
                                </div>
                                <div className="flex-1 min-w-0">
                                  <p className="text-white text-sm font-semibold truncate">{c.clause_name}</p>
                                  <div className="flex flex-wrap gap-1.5 mt-1">
                                    <span className="text-xs font-bold px-2 py-0.5 rounded border" style={{ color: cfg.color, background: `${cfg.color}15`, borderColor: `${cfg.color}40` }}>
                                      {c.best_label}
                                    </span>
                                    <span className={`text-xs px-2 py-0.5 rounded border ${
                                      c.risk_level === 'HIGH' ? 'bg-red-900/30 text-red-400 border-red-800/60' :
                                      c.risk_level === 'MEDIUM' ? 'bg-yellow-900/30 text-yellow-400 border-yellow-800/60' :
                                      'bg-green-900/30 text-green-400 border-green-800/60'
                                    }`}>{c.risk_level}</span>
                                  </div>
                                </div>
                                <div className="text-right shrink-0">
                                  <p className="text-sm font-black" style={{ color: cfg.color }}>{c.confidence}%</p>
                                  <p className="text-xs text-slate-500">confidence</p>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                    </div>
                  </div>

                  {/* Detail panel */}
                  <div className="col-span-2">
                    {rlSelectedClause ? (
                      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 sticky top-4 space-y-5">
                        <div>
                          <p className="text-white font-bold text-base">{rlSelectedClause.clause_name}</p>
                          <div className="flex flex-wrap gap-2 mt-2">
                            {[
                              { label: rlSelectedClause.sentence_type, color: '#8b5cf6' },
                              { label: rlSelectedClause.party, color: '#06b6d4' },
                              { label: `${rlSelectedClause.risk_score}% risk`, color: rlSelectedClause.risk_level === 'HIGH' ? '#ef4444' : rlSelectedClause.risk_level === 'MEDIUM' ? '#f59e0b' : '#10b981' },
                            ].map(({ label, color }) => (
                              <span key={label} className="px-2 py-0.5 rounded text-xs font-semibold border"
                                style={{ color, background: `${color}15`, borderColor: `${color}40` }}>{label}</span>
                            ))}
                          </div>
                        </div>

                        {/* Best action highlight */}
                        {(() => {
                          const cfg = ACTION_CONFIG[rlSelectedClause.best_action] || {};
                          const Icon = cfg.icon || Shield;
                          return (
                            <div className={`${cfg.bg} border ${cfg.border} rounded-xl p-4`}>
                              <p className="text-xs text-slate-400 uppercase tracking-wider mb-2">Recommended Action</p>
                              <div className="flex items-center gap-3">
                                <Icon className="w-6 h-6" style={{ color: cfg.color }} />
                                <div>
                                  <p className="text-white font-bold">{rlSelectedClause.best_label}</p>
                                  <p className="text-xs text-slate-400 mt-0.5">{rlSelectedClause.best_description}</p>
                                </div>
                              </div>
                              <div className="mt-3">
                                <div className="flex justify-between text-xs mb-1">
                                  <span className="text-slate-400">Confidence</span>
                                  <span className="font-bold" style={{ color: cfg.color }}>{rlSelectedClause.confidence}%</span>
                                </div>
                                <div className="bg-slate-700 rounded-full h-2 overflow-hidden">
                                  <div className="h-2 rounded-full" style={{ width: `${rlSelectedClause.confidence}%`, background: cfg.color }} />
                                </div>
                              </div>
                            </div>
                          );
                        })()}

                        {/* All actions ranked */}
                        <div>
                          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">All Actions Ranked</p>
                          <div className="space-y-2">
                            {(rlSelectedClause.all_actions || []).map((a, i) => {
                              const cfg = ACTION_CONFIG[a.action] || {};
                              const Icon = cfg.icon || Shield;
                              return (
                                <div key={a.action} className={`flex items-center gap-2.5 p-2.5 rounded-lg border ${i === 0 ? `${cfg.bg} ${cfg.border}` : 'bg-slate-800/40 border-slate-700/60'}`}>
                                  <span className="text-xs text-slate-500 w-4 font-mono">{i + 1}</span>
                                  <Icon className="w-4 h-4 shrink-0" style={{ color: cfg.color }} />
                                  <span className="text-xs text-slate-300 flex-1">{a.label}</span>
                                  <div className="text-right">
                                    <span className="text-xs font-bold" style={{ color: cfg.color }}>{a.confidence}%</span>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>

                        {/* Financial */}
                        <div className="p-3 bg-slate-800/60 border border-slate-700/60 rounded-xl">
                          <div className="flex justify-between text-sm">
                            <span className="text-slate-400">Financial Exposure</span>
                            <span className="text-orange-400 font-mono font-bold">₹{(rlSelectedClause.financial_impact || 0).toLocaleString()}</span>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 flex flex-col items-center justify-center gap-3 h-64">
                        <Bot className="w-12 h-12 text-slate-600" />
                        <p className="text-slate-400 text-sm text-center">Select a clause from the list to see detailed RL recommendations</p>
                      </div>
                    )}
                  </div>
                </div>
              </>
            ) : (
              <div className="flex flex-col items-center justify-center py-20 gap-4">
                <div className="w-20 h-20 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center">
                  <Bot className="w-10 h-10 text-slate-500" />
                </div>
                <p className="text-slate-300 font-medium">Q-Learning Negotiation Agent</p>
                <p className="text-slate-500 text-sm text-center max-w-md">
                  The RL engine simulates thousands of negotiation episodes per clause and learns the optimal strategy using Q-values.
                  Select simulation count and click Run.
                </p>
                {!selectedContractId ? (
                  <p className="text-yellow-400 text-sm">Select a contract first</p>
                ) : (
                  <button
                    onClick={() => loadRL(rlSimCount)}
                    className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-xl font-semibold flex items-center gap-2 transition-colors shadow-lg shadow-purple-900/30"
                  >
                    <Play className="w-5 h-5" /> Run {rlSimCount} Simulations
                  </button>
                )}
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}
