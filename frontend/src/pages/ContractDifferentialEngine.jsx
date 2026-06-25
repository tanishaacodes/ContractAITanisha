/**
 * Contract Differential Intelligence Engine (CDIE)
 * ==================================================
 * Enterprise-grade graph-based contract comparison dashboard.
 *
 * 4 Tabs:
 *   1. Graph Diff      — Compare two contracts, see color-coded diff graph
 *   2. GDS Analytics   — PageRank clause influence + structural similarity
 *   3. GNN Scoring     — Graph Neural Network risk & stability scores
 *   4. How It Works    — Architecture explainer
 */

import { useState, useEffect, useCallback } from 'react';
import {
  GitCompare, Network, Brain, BookOpen, Sparkles, ArrowLeft,
  AlertCircle, CheckCircle, Zap, TrendingUp, Activity, RefreshCw,
  Download, Info, Shield, BarChart2, Database, Cpu, Link,
  FileJson, Clock, MessageSquare, Target, PlayCircle
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  RadialBarChart, RadialBar, Legend, Cell, LineChart, Line
} from 'recharts';

import api from '../utils/api';
import ContractNetworkGraph from '../components/graph/ContractNetworkGraph';
import ContractGraph3D from '../components/graph/ContractGraph3D';
import {
  ingestContractGraph,
  compareContractGraph,
  compareMultiContractGraph,
  getPageRank,
  getContractSimilarity,
  getGNNScore,
} from '../services/cuadGraphService';

// ─── Tab definitions ───────────────────────────────────────────────────────
const TABS = [
  { id: 'diff',      label: 'Graph Diff',        icon: GitCompare,  color: 'from-purple-500 to-blue-500'  },
  { id: 'gds',       label: 'GDS Analytics',     icon: BarChart2,   color: 'from-cyan-500 to-teal-500'    },
  { id: 'gnn',       label: 'GNN Scoring',       icon: Brain,       color: 'from-pink-500 to-rose-500'    },
  { id: 'rag',       label: 'AI GraphRAG',       icon: MessageSquare, color: 'from-violet-500 to-purple-500' },
  { id: 'train',     label: 'GNN Training',      icon: Cpu,         color: 'from-orange-500 to-red-500'   },
  { id: 'graph3d',   label: '3D Graph',          icon: Network,     color: 'from-teal-500 to-green-500'   },
  { id: 'temporal',  label: 'Amendment History', icon: Clock,       color: 'from-blue-500 to-indigo-500'  },
  { id: 'cuadjson',  label: 'CUAD JSON Ingest',  icon: FileJson,    color: 'from-emerald-500 to-teal-500' },
  { id: 'similar',   label: 'Build SIMILAR',     icon: Link,        color: 'from-yellow-500 to-amber-500' },
  { id: 'howto',     label: 'How It Works',      icon: BookOpen,    color: 'from-amber-500 to-orange-500' },
];

// ─── Node diff legend ───────────────────────────────────────────────────────
const DIFF_LEGEND = [
  { status: 'same',     color: '#68BC00', label: 'Same (identical risk)' },
  { status: 'modified', color: '#FFD86E', label: 'Modified (risk differs)' },
  { status: 'missing',  color: '#F16667', label: 'Missing from Contract B' },
  { status: 'new',      color: '#4C8EDA', label: 'New in Contract B' },
];

// ─── Helpers ────────────────────────────────────────────────────────────────
const getRiskColor = (score) => {
  if (score >= 70) return 'text-red-400';
  if (score >= 40) return 'text-yellow-400';
  return 'text-green-400';
};

const getRiskBg = (score) => {
  if (score >= 70) return 'bg-red-900/20 border-red-700';
  if (score >= 40) return 'bg-yellow-900/20 border-yellow-700';
  return 'bg-green-900/20 border-green-700';
};

const ScoreGauge = ({ value, label, color }) => (
  <div className="flex flex-col items-center gap-2">
    <div className={`relative w-28 h-28 rounded-full flex items-center justify-center border-4 ${color} bg-slate-900`}
         style={{ boxShadow: `0 0 24px ${color.includes('red') ? '#ef444488' : color.includes('yellow') ? '#f59e0b88' : '#10b98188'}` }}>
      <span className="text-2xl font-bold text-white">{value}</span>
    </div>
    <span className="text-xs text-slate-400 font-medium">{label}</span>
  </div>
);

// ─── Main Component ─────────────────────────────────────────────────────────
export default function ContractDifferentialEngine() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('diff');
  const [isVisible, setIsVisible] = useState(false);

  // contracts list for dropdowns
  const [contracts, setContracts] = useState([]);
  const [contractsLoading, setContractsLoading] = useState(false);

  // Tab 1 — Graph Diff state
  const [c1Id, setC1Id] = useState('');
  const [c2Id, setC2Id] = useState('');
  const [riskWeight, setRiskWeight] = useState(1.0);
  const [obligationWeight, setObligationWeight] = useState(1.0);
  const [diffLoading, setDiffLoading] = useState(false);
  const [diffResult, setDiffResult] = useState(null);
  const [ingestStatus, setIngestStatus] = useState({ c1: null, c2: null });

  // Tab 1 — Multi-contract mode
  const [multiMode, setMultiMode] = useState(false);
  const [c3Id, setC3Id] = useState('');
  const [c4Id, setC4Id] = useState('');
  const [c5Id, setC5Id] = useState('');
  const [multiResult, setMultiResult] = useState(null);
  const [multiLoading, setMultiLoading] = useState(false);

  // Tab 2 — GDS state
  const [gdsContractId, setGdsContractId] = useState('');
  const [gdsCustomId, setGdsCustomId] = useState('');
  const [gdsUseCustom, setGdsUseCustom] = useState(false);
  const [prLoading, setPrLoading] = useState(false);
  const [prResult, setPrResult] = useState(null);
  const [simC1, setSimC1] = useState('');
  const [simC2, setSimC2] = useState('');
  const [simLoading, setSimLoading] = useState(false);
  const [simResult, setSimResult] = useState(null);

  // Tab 3 — GNN state
  const [gnnContractId, setGnnContractId] = useState('');
  const [gnnCustomId, setGnnCustomId] = useState('');
  const [gnnUseCustom, setGnnUseCustom] = useState(false);
  const [gnnLoading, setGnnLoading] = useState(false);
  const [gnnResult, setGnnResult] = useState(null);

  // Tab 4 — GraphRAG state
  const [ragContractId, setRagContractId] = useState('');
  const [ragLoading, setRagLoading] = useState(false);
  const [ragResult, setRagResult] = useState(null);
  const [ragCompC1, setRagCompC1] = useState('');
  const [ragCompC2, setRagCompC2] = useState('');
  const [ragCompLoading, setRagCompLoading] = useState(false);
  const [ragCompResult, setRagCompResult] = useState(null);
  const [ragNegGoals, setRagNegGoals] = useState('');
  const [ragNegLoading, setRagNegLoading] = useState(false);
  const [ragNegResult, setRagNegResult] = useState(null);

  // Tab 5 — GNN Training state
  const [trainContractId, setTrainContractId] = useState('');
  const [trainEpochs, setTrainEpochs] = useState(200);
  const [trainLoading, setTrainLoading] = useState(false);
  const [trainResult, setTrainResult] = useState(null);

  // Tab 7 — Temporal/Amendment state
  const [amendContractId, setAmendContractId] = useState('');
  const [amendDesc, setAmendDesc] = useState('');
  const [amendDate, setAmendDate] = useState('');
  const [amendLoading, setAmendLoading] = useState(false);
  const [amendResult, setAmendResult] = useState(null);
  const [historyContractId, setHistoryContractId] = useState('');
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyResult, setHistoryResult] = useState(null);

  // Tab 8 — CUAD JSON Ingest state
  const [cuadJsonText, setCuadJsonText] = useState('');
  const [cuadJsonLoading, setCuadJsonLoading] = useState(false);
  const [cuadJsonResult, setCuadJsonResult] = useState(null);

  // Tab 9 — Build SIMILAR edges state
  const [similarThreshold, setSimilarThreshold] = useState(0.70);
  const [similarLoading, setSimilarLoading] = useState(false);
  const [similarResult, setSimilarResult] = useState(null);

  useEffect(() => {
    setIsVisible(true);
    loadContracts();
  }, []);

  const loadContracts = async () => {
    setContractsLoading(true);
    try {
      const res = await api.get('/contracts/list');
      setContracts(res.data?.contracts || res.data || []);
    } catch (e) {
      console.error('Failed to load contracts', e);
    } finally {
      setContractsLoading(false);
    }
  };

  // ── Tab 1 actions ────────────────────────────────────────────────────────

  const handleIngest = async (contractId, key) => {
    setIngestStatus(prev => ({ ...prev, [key]: 'loading' }));
    try {
      const res = await ingestContractGraph(contractId);
      setIngestStatus(prev => ({ ...prev, [key]: res.success ? 'done' : 'error' }));
    } catch {
      setIngestStatus(prev => ({ ...prev, [key]: 'error' }));
    }
  };

  const handleCompare = async () => {
    if (!c1Id || !c2Id) return;
    setDiffLoading(true);
    setDiffResult(null);
    try {
      const res = await compareContractGraph(c1Id, c2Id, riskWeight, obligationWeight);
      setDiffResult(res);
    } catch (e) {
      alert('Comparison failed: ' + (e.response?.data?.error || e.message));
    } finally {
      setDiffLoading(false);
    }
  };

  const handleMultiCompare = async () => {
    const ids = [c1Id, c2Id, c3Id, c4Id, c5Id].filter(Boolean);
    if (ids.length < 2) return;
    setMultiLoading(true);
    setMultiResult(null);
    try {
      const res = await compareMultiContractGraph(ids, riskWeight, obligationWeight);
      setMultiResult(res);
    } catch (e) {
      alert('Multi-contract comparison failed: ' + (e.response?.data?.error || e.message));
    } finally {
      setMultiLoading(false);
    }
  };

  // ── Tab 2 actions ────────────────────────────────────────────────────────

  const handlePageRank = async () => {
    const effectiveId = gdsUseCustom ? gdsCustomId.trim() : gdsContractId;
    if (!effectiveId) return;
    setPrLoading(true);
    setPrResult(null);
    try {
      const res = await getPageRank(effectiveId);
      setPrResult(res);
    } catch (e) {
      alert('PageRank failed: ' + (e.response?.data?.error || e.message));
    } finally {
      setPrLoading(false);
    }
  };

  const handleSimilarity = async () => {
    if (!simC1 || !simC2) return;
    setSimLoading(true);
    setSimResult(null);
    try {
      const res = await getContractSimilarity(simC1, simC2);
      setSimResult(res);
    } catch (e) {
      alert('Similarity failed: ' + (e.response?.data?.error || e.message));
    } finally {
      setSimLoading(false);
    }
  };

  // ── Tab 3 actions ────────────────────────────────────────────────────────

  const handleGNN = async () => {
    const effectiveId = gnnUseCustom ? gnnCustomId.trim() : gnnContractId;
    if (!effectiveId) return;
    setGnnLoading(true);
    setGnnResult(null);
    try {
      const res = await getGNNScore(effectiveId);
      setGnnResult(res);
    } catch (e) {
      alert('GNN scoring failed: ' + (e.response?.data?.error || e.message));
    } finally {
      setGnnLoading(false);
    }
  };

  // ── Tab 4: GraphRAG handlers ──────────────────────────────────────────────

  const handleRagAnalyze = async () => {
    if (!ragContractId) return;
    setRagLoading(true); setRagResult(null);
    try {
      const res = await api.post('/cuad-graph/rag-analyze/', { contract_id: ragContractId });
      setRagResult(res.data);
    } catch (e) { alert('RAG analysis failed: ' + (e.response?.data?.error || e.message)); }
    finally { setRagLoading(false); }
  };

  const handleRagCompare = async () => {
    if (!ragCompC1 || !ragCompC2) return;
    setRagCompLoading(true); setRagCompResult(null);
    try {
      const res = await api.post('/cuad-graph/rag-compare/', { contract1_id: ragCompC1, contract2_id: ragCompC2 });
      setRagCompResult(res.data);
    } catch (e) { alert('RAG compare failed: ' + (e.response?.data?.error || e.message)); }
    finally { setRagCompLoading(false); }
  };

  const handleRagNegotiate = async () => {
    if (!ragContractId) return;
    setRagNegLoading(true); setRagNegResult(null);
    try {
      const res = await api.post('/cuad-graph/rag-negotiate/', { contract_id: ragContractId, negotiation_goals: ragNegGoals });
      setRagNegResult(res.data);
    } catch (e) { alert('Negotiation RAG failed: ' + (e.response?.data?.error || e.message)); }
    finally { setRagNegLoading(false); }
  };

  // ── Tab 5: GNN Training handlers ──────────────────────────────────────────

  const handleGNNTrain = async () => {
    if (!trainContractId) return;
    setTrainLoading(true); setTrainResult(null);
    try {
      const res = await api.post('/cuad-graph/gnn-train/', { contract_id: trainContractId, epochs: trainEpochs });
      setTrainResult(res.data);
    } catch (e) { alert('GNN training failed: ' + (e.response?.data?.error || e.message)); }
    finally { setTrainLoading(false); }
  };

  // ── Tab 7: Temporal/Amendment handlers ───────────────────────────────────

  const handleTrackAmendment = async () => {
    if (!amendContractId || !amendDesc) return;
    setAmendLoading(true); setAmendResult(null);
    try {
      const res = await api.post('/cuad-graph/amendment/', {
        contract_id: amendContractId, description: amendDesc, date: amendDate
      });
      setAmendResult(res.data);
    } catch (e) { alert('Amendment tracking failed: ' + (e.response?.data?.error || e.message)); }
    finally { setAmendLoading(false); }
  };

  const handleGetHistory = async () => {
    if (!historyContractId) return;
    setHistoryLoading(true); setHistoryResult(null);
    try {
      const res = await api.get(`/cuad-graph/amendments/${historyContractId}/`);
      setHistoryResult(res.data);
    } catch (e) { alert('History fetch failed: ' + (e.response?.data?.error || e.message)); }
    finally { setHistoryLoading(false); }
  };

  // ── Tab 8: CUAD JSON Ingest handlers ─────────────────────────────────────

  const handleCuadJsonIngest = async () => {
    if (!cuadJsonText.trim()) return;
    setCuadJsonLoading(true); setCuadJsonResult(null);
    try {
      const parsed = JSON.parse(cuadJsonText);
      const contracts = Array.isArray(parsed) ? parsed : [parsed];
      const res = await api.post('/cuad-graph/ingest-cuad-json/', { contracts });
      setCuadJsonResult(res.data);
    } catch (e) {
      if (e instanceof SyntaxError) alert('Invalid JSON: ' + e.message);
      else alert('Ingest failed: ' + (e.response?.data?.error || e.message));
    }
    finally { setCuadJsonLoading(false); }
  };

  // ── Tab 9: Build SIMILAR edges handler ───────────────────────────────────

  const handleBuildSimilar = async () => {
    setSimilarLoading(true); setSimilarResult(null);
    try {
      const res = await api.post('/cuad-graph/build-similar/', { threshold: similarThreshold });
      setSimilarResult(res.data);
    } catch (e) { alert('Build similar failed: ' + (e.response?.data?.error || e.message)); }
    finally { setSimilarLoading(false); }
  };

  // ── Contract selector component ──────────────────────────────────────────
  const ContractSelect = ({ value, onChange, label, placeholder }) => (
    <div className="flex flex-col gap-1">
      <label className="text-xs text-slate-400 font-medium">{label}</label>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="bg-slate-800 border border-slate-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500/30 transition-all"
      >
        <option value="">{contractsLoading ? 'Loading…' : placeholder || '— Select contract —'}</option>
        {contracts.map(c => (
          <option key={c.id} value={c.id}>
            {c.filename || c.originalFilename || c.id}
          </option>
        ))}
      </select>
    </div>
  );

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-6 min-h-screen">
      {/* Animated background */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-purple-600 rounded-full mix-blend-multiply filter blur-3xl opacity-8"></div>
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-blue-600 rounded-full mix-blend-multiply filter blur-3xl opacity-8"></div>
        <div className="absolute top-1/2 left-1/2 w-64 h-64 bg-cyan-600 rounded-full mix-blend-multiply filter blur-3xl opacity-5 -translate-x-1/2 -translate-y-1/2"></div>
      </div>

      {/* Header */}
      <div className={`transition-all duration-700 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-4'}`}>
        <button
          onClick={() => navigate(-1)}
          className="group flex items-center gap-2 text-slate-400 hover:text-white transition-all mb-4"
        >
          <ArrowLeft size={18} className="transition-transform group-hover:-translate-x-1" />
          Back
        </button>

        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-4xl font-bold bg-gradient-to-r from-white via-purple-200 to-blue-200 bg-clip-text text-transparent">
                Contract Differential Engine
              </h1>
              <Sparkles className="w-6 h-6 text-purple-400 animate-pulse" />
            </div>
            <p className="text-slate-400 text-sm">
              CUAD Graph Intelligence — compare, analyze, and score contracts via Neo4j knowledge graph
            </p>
          </div>
          <div className="relative group hidden lg:flex">
            <div className="absolute inset-0 bg-gradient-to-br from-purple-600 to-blue-600 rounded-2xl blur-xl opacity-50 group-hover:opacity-75 transition-opacity"></div>
            <div className="relative flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-600 to-blue-600 shadow-lg shadow-purple-500/40 group-hover:scale-110 transition-transform">
              <GitCompare className="w-8 h-8 text-white" />
            </div>
          </div>
        </div>
      </div>

      {/* Tab Bar */}
      <div className={`flex flex-wrap gap-2 transition-all duration-700 delay-100 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-sm transition-all duration-300 ${
              activeTab === tab.id
                ? `bg-gradient-to-r ${tab.color} text-white shadow-lg scale-105`
                : 'bg-slate-800/80 text-slate-400 hover:text-white hover:bg-slate-700/80 border border-slate-700'
            }`}
          >
            <tab.icon size={15} />
            {tab.label}
          </button>
        ))}
      </div>

      {/* ═══════════════════════════════════════════════════════════
          TAB 1 — GRAPH DIFF
      ═══════════════════════════════════════════════════════════ */}
      {activeTab === 'diff' && (
        <div className="space-y-5 animate-fadeIn">
          {/* Controls */}
          <div className="bg-slate-900 rounded-2xl border border-slate-700 p-6 hover:border-purple-700/50 transition-all">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <GitCompare className="w-5 h-5 text-purple-400" />
                Select Contracts to Compare
              </h2>
              <button
                onClick={() => { setMultiMode(m => !m); setMultiResult(null); }}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                  multiMode
                    ? 'bg-purple-600 border-purple-500 text-white'
                    : 'bg-slate-800 border-slate-600 text-slate-400 hover:text-white hover:border-slate-500'
                }`}
              >
                <Network size={13} />
                {multiMode ? 'Portfolio Mode (3–5)' : 'Standard Mode (2)'}
              </button>
            </div>

            <div className={`grid gap-6 mb-6 ${multiMode ? 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3' : 'grid-cols-1 md:grid-cols-2'}`}>
              {/* Contract A */}
              <div className="space-y-3">
                <ContractSelect
                  value={c1Id}
                  onChange={setC1Id}
                  label="Contract A (Reference)"
                  placeholder="— Select Contract A —"
                />
                {c1Id && (
                  <button
                    onClick={() => handleIngest(c1Id, 'c1')}
                    disabled={ingestStatus.c1 === 'loading'}
                    className="flex items-center gap-2 text-xs px-3 py-1.5 bg-purple-900/30 border border-purple-700 rounded-lg text-purple-300 hover:bg-purple-900/50 transition-all"
                  >
                    <Database size={12} />
                    {ingestStatus.c1 === 'loading' ? 'Ingesting…' :
                     ingestStatus.c1 === 'done' ? '✓ Ingested to Neo4j' :
                     ingestStatus.c1 === 'error' ? '✗ Ingest failed' :
                     'Ingest to Neo4j Graph'}
                  </button>
                )}
              </div>

              {/* Contract B */}
              <div className="space-y-3">
                <ContractSelect
                  value={c2Id}
                  onChange={setC2Id}
                  label="Contract B (Compare)"
                  placeholder="— Select Contract B —"
                />
                {c2Id && (
                  <button
                    onClick={() => handleIngest(c2Id, 'c2')}
                    disabled={ingestStatus.c2 === 'loading'}
                    className="flex items-center gap-2 text-xs px-3 py-1.5 bg-blue-900/30 border border-blue-700 rounded-lg text-blue-300 hover:bg-blue-900/50 transition-all"
                  >
                    <Database size={12} />
                    {ingestStatus.c2 === 'loading' ? 'Ingesting…' :
                     ingestStatus.c2 === 'done' ? '✓ Ingested to Neo4j' :
                     ingestStatus.c2 === 'error' ? '✗ Ingest failed' :
                     'Ingest to Neo4j Graph'}
                  </button>
                )}
              </div>

              {/* Contracts C, D, E — portfolio mode only */}
              {multiMode && (
                <>
                  <div className="space-y-3">
                    <ContractSelect value={c3Id} onChange={setC3Id} label="Contract C (Optional)" placeholder="— Select Contract C —" />
                  </div>
                  <div className="space-y-3">
                    <ContractSelect value={c4Id} onChange={setC4Id} label="Contract D (Optional)" placeholder="— Select Contract D —" />
                  </div>
                  <div className="space-y-3">
                    <ContractSelect value={c5Id} onChange={setC5Id} label="Contract E (Optional)" placeholder="— Select Contract E —" />
                  </div>
                </>
              )}
            </div>

            {/* Weight Sliders */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs text-slate-400 font-medium flex items-center gap-1">
                    <Shield size={11} /> Risk Weight
                  </label>
                  <span className="text-sm font-bold text-purple-400">{riskWeight.toFixed(1)}</span>
                </div>
                <input
                  type="range" min={0} max={5} step={0.5}
                  value={riskWeight}
                  onChange={e => setRiskWeight(parseFloat(e.target.value))}
                  className="w-full accent-purple-500"
                />
                <div className="flex justify-between text-xs text-slate-600 mt-1">
                  <span>0 (ignore)</span><span>5 (max)</span>
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs text-slate-400 font-medium flex items-center gap-1">
                    <Activity size={11} /> Obligation Weight
                  </label>
                  <span className="text-sm font-bold text-cyan-400">{obligationWeight.toFixed(1)}</span>
                </div>
                <input
                  type="range" min={0} max={5} step={0.5}
                  value={obligationWeight}
                  onChange={e => setObligationWeight(parseFloat(e.target.value))}
                  className="w-full accent-cyan-500"
                />
                <div className="flex justify-between text-xs text-slate-600 mt-1">
                  <span>0 (ignore)</span><span>5 (max)</span>
                </div>
              </div>
            </div>

            {multiMode ? (
              <button
                onClick={handleMultiCompare}
                disabled={!c1Id || !c2Id || multiLoading}
                className="w-full flex items-center justify-center gap-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-bold py-3.5 rounded-xl transition-all duration-300 disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-purple-500/20 hover:scale-[1.01]"
              >
                {multiLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                    Building Portfolio Graph…
                  </>
                ) : (
                  <>
                    <Network size={18} />
                    Run Portfolio Graph Analysis ({[c1Id, c2Id, c3Id, c4Id, c5Id].filter(Boolean).length} contracts)
                    <Sparkles size={14} className="opacity-70" />
                  </>
                )}
              </button>
            ) : (
              <button
                onClick={handleCompare}
                disabled={!c1Id || !c2Id || c1Id === c2Id || diffLoading}
                className="w-full flex items-center justify-center gap-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold py-3.5 rounded-xl transition-all duration-300 disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-purple-500/20 hover:shadow-purple-500/40 hover:scale-[1.01]"
              >
                {diffLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                    Analyzing Contracts…
                  </>
                ) : (
                  <>
                    <GitCompare size={18} />
                    Run Graph Differential Analysis
                    <Sparkles size={14} className="opacity-70" />
                  </>
                )}
              </button>
            )}
          </div>

          {/* ── Portfolio Multi-Contract Results ─────────────────────── */}
          {multiResult && multiMode && (
            <div className="space-y-5 animate-fadeIn">
              {/* Coverage legend */}
              <div className="bg-slate-900 rounded-2xl border border-purple-700/30 p-5">
                <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
                  <Network size={15} className="text-purple-400" />
                  Portfolio Graph — {multiResult.contract_count} Contracts · {multiResult.total_clause_types} Clause Types
                </h3>
                <div className="flex flex-wrap gap-3 mb-4">
                  {[
                    { label: 'Universal', color: '#68BC00', count: multiResult.coverage_summary?.universal, desc: 'All contracts' },
                    { label: 'Common',    color: '#FFD86E', count: multiResult.coverage_summary?.common,    desc: 'Majority' },
                    { label: 'Partial',   color: '#F97316', count: multiResult.coverage_summary?.partial,   desc: 'Minority' },
                    { label: 'Unique',    color: '#4C8EDA', count: multiResult.coverage_summary?.unique,    desc: '1 contract only' },
                  ].map(item => (
                    <div key={item.label} className="flex items-center gap-2 bg-slate-800 rounded-lg px-3 py-2 border border-slate-700">
                      <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: item.color, boxShadow: `0 0 6px ${item.color}88` }}></div>
                      <span className="text-white text-xs font-semibold">{item.label}</span>
                      <span className="text-slate-400 text-xs">({item.count})</span>
                      <span className="text-slate-500 text-xs hidden sm:inline">— {item.desc}</span>
                    </div>
                  ))}
                </div>

                {/* Contract ranking table */}
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-700">
                        <th className="text-left text-xs text-slate-400 font-medium py-2 pr-4">Rank</th>
                        <th className="text-left text-xs text-slate-400 font-medium py-2 pr-4">Contract</th>
                        <th className="text-right text-xs text-slate-400 font-medium py-2 pr-4">Risk Score</th>
                        <th className="text-right text-xs text-slate-400 font-medium py-2 pr-4">Clauses</th>
                        <th className="text-right text-xs text-slate-400 font-medium py-2">Obligations</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[...multiResult.contracts]
                        .sort((a, b) => b.weighted_score - a.weighted_score)
                        .map((c, i) => (
                          <tr key={c.id} className="border-b border-slate-800 hover:bg-slate-800/40 transition-colors">
                            <td className="py-2.5 pr-4">
                              <span className={`text-xs font-bold px-2 py-0.5 rounded ${i === 0 ? 'bg-red-900/40 text-red-300' : i === 1 ? 'bg-yellow-900/40 text-yellow-300' : 'bg-slate-700 text-slate-300'}`}>
                                #{i + 1}
                              </span>
                            </td>
                            <td className="py-2.5 pr-4 text-white font-medium">{c.name}</td>
                            <td className={`py-2.5 pr-4 text-right font-bold ${c.weighted_score > 50 ? 'text-red-400' : c.weighted_score > 25 ? 'text-yellow-400' : 'text-green-400'}`}>
                              {c.weighted_score}
                            </td>
                            <td className="py-2.5 pr-4 text-right text-slate-400">{c.clause_count}</td>
                            <td className="py-2.5 text-right text-slate-400">{c.obligation_count}</td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* 3D visualization of portfolio graph */}
              <ContractGraph3D
                nodes={multiResult.nodes.map(n => ({
                  id: n.id,
                  label: n.data?.label || n.id,
                  type: n.data?.type || 'ClauseType',
                  risk_score: n.data?.avg_risk || n.data?.score || 0,
                  size: n.data?.size || 40,
                  diff_status: n.data?.coverage,
                }))}
                edges={multiResult.edges.map(e => ({ id: e.id, source: e.source, target: e.target, label: e.label }))}
                height="600px"
              />
            </div>
          )}

          {/* Diff Results */}
          {!multiMode && diffResult && (
            <div className="space-y-5">
              {/* Score Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Contract A score */}
                <div className="bg-slate-900 rounded-xl border border-purple-800/60 p-5 hover:border-purple-600 transition-all">
                  <div className="text-xs text-slate-400 mb-1 font-medium">Contract A</div>
                  <div className="text-lg font-bold text-white truncate">{diffResult.contract1?.name}</div>
                  <div className="mt-3 flex items-end gap-2">
                    <span className={`text-3xl font-black ${diffResult.contract1?.weighted_score > diffResult.contract2?.weighted_score ? 'text-red-400' : 'text-green-400'}`}>
                      {diffResult.contract1?.weighted_score}
                    </span>
                    <span className="text-slate-500 text-sm mb-1">weighted score</span>
                  </div>
                  <div className="mt-2 text-xs text-slate-500">
                    {diffResult.contract1?.clause_count} clauses · {diffResult.contract1?.obligation_count} obligations
                  </div>
                </div>

                {/* Diff Score */}
                <div className="bg-slate-900 rounded-xl border border-slate-600 p-5 flex flex-col items-center justify-center hover:border-blue-600 transition-all">
                  <div className="text-xs text-slate-400 mb-2 font-medium">Differential Score</div>
                  <div className="text-5xl font-black text-white">{diffResult.diff_score}</div>
                  <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                    {DIFF_LEGEND.map(l => (
                      <div key={l.status} className="flex items-center gap-1.5">
                        <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: l.color }}></div>
                        <span className="text-slate-400">{diffResult.diff_summary?.[l.status] ?? 0} {l.status}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Contract B score */}
                <div className="bg-slate-900 rounded-xl border border-blue-800/60 p-5 hover:border-blue-600 transition-all">
                  <div className="text-xs text-slate-400 mb-1 font-medium">Contract B</div>
                  <div className="text-lg font-bold text-white truncate">{diffResult.contract2?.name}</div>
                  <div className="mt-3 flex items-end gap-2">
                    <span className={`text-3xl font-black ${diffResult.contract2?.weighted_score > diffResult.contract1?.weighted_score ? 'text-red-400' : 'text-green-400'}`}>
                      {diffResult.contract2?.weighted_score}
                    </span>
                    <span className="text-slate-500 text-sm mb-1">weighted score</span>
                  </div>
                  <div className="mt-2 text-xs text-slate-500">
                    {diffResult.contract2?.clause_count} clauses · {diffResult.contract2?.obligation_count} obligations
                  </div>
                </div>
              </div>

              {/* Legend */}
              <div className="flex flex-wrap gap-4 px-1">
                {DIFF_LEGEND.map(l => (
                  <div key={l.status} className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full shadow-lg" style={{ backgroundColor: l.color, boxShadow: `0 0 8px ${l.color}88` }}></div>
                    <span className="text-xs text-slate-300">{l.label}</span>
                  </div>
                ))}
              </div>

              {/* Diff Graph */}
              <div className="bg-slate-900 rounded-2xl border border-slate-700 p-1">
                <ContractNetworkGraph
                  key={`diff-${c1Id}-${c2Id}-${riskWeight}-${obligationWeight}-${diffResult.nodes?.length}`}
                  initialData={{ nodes: diffResult.nodes, edges: diffResult.edges }}
                  height={520}
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════
          TAB 2 — GDS ANALYTICS
      ═══════════════════════════════════════════════════════════ */}
      {activeTab === 'gds' && (
        <div className="space-y-6 animate-fadeIn">
          {/* PageRank Section */}
          <div className="bg-slate-900 rounded-2xl border border-slate-700 p-6 hover:border-cyan-700/50 transition-all">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-cyan-400" />
              PageRank — Clause Influence Scores
            </h2>
            <p className="text-slate-400 text-sm mb-5">
              Identifies the most central and influential clauses in the contract risk network using PageRank.
              Higher score = clause has greater impact on overall contract risk.
            </p>

            {/* Source toggle */}
            <div className="flex items-center gap-2 mb-3">
              <button
                onClick={() => { setGdsUseCustom(false); setPrResult(null); }}
                className={`px-3 py-1 rounded-lg text-xs font-semibold border transition-all ${!gdsUseCustom ? 'bg-cyan-600 border-cyan-500 text-white' : 'bg-slate-800 border-slate-600 text-slate-400 hover:text-white'}`}
              >MySQL Contract</button>
              <button
                onClick={() => { setGdsUseCustom(true); setPrResult(null); }}
                className={`px-3 py-1 rounded-lg text-xs font-semibold border transition-all ${gdsUseCustom ? 'bg-emerald-600 border-emerald-500 text-white' : 'bg-slate-800 border-slate-600 text-slate-400 hover:text-white'}`}
              >Neo4j / CUAD ID</button>
              {gdsUseCustom && <span className="text-xs text-emerald-400">← paste your CUAD JSON contract ID here</span>}
            </div>

            <div className="flex flex-col md:flex-row gap-4 items-end mb-5">
              <div className="flex-1">
                {gdsUseCustom ? (
                  <div className="flex flex-col gap-1">
                    <label className="text-xs text-slate-400 font-medium">Neo4j Contract ID</label>
                    <input
                      type="text"
                      value={gdsCustomId}
                      onChange={e => setGdsCustomId(e.target.value)}
                      placeholder="e.g. C-1001"
                      className="bg-slate-800 border border-emerald-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-emerald-400 focus:ring-1 focus:ring-emerald-400/30 transition-all"
                    />
                  </div>
                ) : (
                  <ContractSelect
                    value={gdsContractId}
                    onChange={setGdsContractId}
                    label="Select Contract"
                  />
                )}
              </div>
              <button
                onClick={handlePageRank}
                disabled={(gdsUseCustom ? !gdsCustomId.trim() : !gdsContractId) || prLoading}
                className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-cyan-600 to-teal-600 hover:from-cyan-700 hover:to-teal-700 text-white font-semibold rounded-xl transition-all disabled:opacity-40 disabled:cursor-not-allowed whitespace-nowrap"
              >
                {prLoading ? <><div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>Running…</> : <><TrendingUp size={15} /> Run PageRank</>}
              </button>
            </div>

            {prResult && (
              <div className="space-y-4">
                <div className="flex gap-4 text-xs text-slate-400">
                  <span>Nodes: <span className="text-white font-semibold">{prResult.node_count}</span></span>
                  <span>Edges: <span className="text-white font-semibold">{prResult.edge_count}</span></span>
                  <span>Method: <span className="text-cyan-400 font-semibold">{prResult.method}</span></span>
                </div>
                {prResult.pagerank && prResult.pagerank.length > 0 && (
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart data={prResult.pagerank.slice(0, 12)} margin={{ top: 5, right: 20, left: 0, bottom: 60 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="clause_name" tick={{ fill: '#94a3b8', fontSize: 10 }} angle={-40} textAnchor="end" interval={0} />
                      <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '8px' }}
                        labelStyle={{ color: '#e2e8f0' }}
                        formatter={(val) => [`${val.toFixed(1)}`, 'Influence Score']}
                      />
                      <Bar dataKey="pagerank_score" radius={[4, 4, 0, 0]}>
                        {prResult.pagerank.slice(0, 12).map((entry, idx) => (
                          <Cell key={idx} fill={entry.risk_score >= 0.7 ? '#F16667' : entry.risk_score >= 0.4 ? '#FFD86E' : '#68BC00'} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                )}
                {/* Top influencers list */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-2">
                  {prResult.pagerank.slice(0, 6).map((item, idx) => (
                    <div key={idx} className="flex items-center gap-3 bg-slate-800/60 rounded-lg p-3 border border-slate-700 hover:border-cyan-700/50 transition-all">
                      <span className="text-lg font-black text-slate-500">#{idx + 1}</span>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm text-white font-medium truncate">{item.clause_name}</div>
                        <div className="text-xs text-slate-400">{item.clause_type}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-bold text-cyan-400">{item.pagerank_score.toFixed(1)}</div>
                        <div className={`text-xs ${item.risk_level === 'HIGH' ? 'text-red-400' : item.risk_level === 'MEDIUM' ? 'text-yellow-400' : 'text-green-400'}`}>
                          {item.risk_level}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Similarity Section */}
          <div className="bg-slate-900 rounded-2xl border border-slate-700 p-6 hover:border-teal-700/50 transition-all">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Network className="w-5 h-5 text-teal-400" />
              Structural Similarity — Cross-Contract Analysis
            </h2>
            <p className="text-slate-400 text-sm mb-5">
              Measures structural similarity between two contracts using Jaccard (clause type overlap) +
              cosine (risk vector) hybrid scoring.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
              <ContractSelect value={simC1} onChange={setSimC1} label="Contract A" />
              <ContractSelect value={simC2} onChange={setSimC2} label="Contract B" />
            </div>

            <button
              onClick={handleSimilarity}
              disabled={!simC1 || !simC2 || simC1 === simC2 || simLoading}
              className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-teal-600 to-cyan-600 hover:from-teal-700 hover:to-cyan-700 text-white font-semibold rounded-xl transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {simLoading ? <><div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>Computing…</> : <><Network size={15} /> Compute Similarity</>}
            </button>

            {simResult && (
              <div className="mt-5 space-y-4">
                {/* Main score */}
                <div className="flex items-center gap-6 flex-wrap">
                  <div className="bg-slate-800 rounded-xl p-4 border border-teal-700/40">
                    <div className="text-xs text-slate-400 mb-1">Combined Similarity</div>
                    <div className="text-4xl font-black text-teal-400">{(simResult.similarity_score * 100).toFixed(0)}%</div>
                  </div>
                  <div className="bg-slate-800 rounded-xl p-4 border border-slate-600">
                    <div className="text-xs text-slate-400 mb-1">Jaccard (types)</div>
                    <div className="text-2xl font-bold text-white">{(simResult.jaccard_similarity * 100).toFixed(0)}%</div>
                  </div>
                  <div className="bg-slate-800 rounded-xl p-4 border border-slate-600">
                    <div className="text-xs text-slate-400 mb-1">Cosine (risk)</div>
                    <div className="text-2xl font-bold text-white">{(simResult.cosine_similarity * 100).toFixed(0)}%</div>
                  </div>
                  <div className="bg-slate-800 rounded-xl p-4 border border-slate-600">
                    <div className="text-xs text-slate-400 mb-1">Common Clause Types</div>
                    <div className="text-2xl font-bold text-green-400">{simResult.clause_overlap?.common_count}</div>
                  </div>
                </div>

                {/* Progress bar */}
                <div>
                  <div className="flex justify-between text-xs text-slate-400 mb-1">
                    <span>Similarity Index</span>
                    <span>{(simResult.similarity_score * 100).toFixed(1)}%</span>
                  </div>
                  <div className="w-full h-3 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-teal-500 to-cyan-500 transition-all duration-1000"
                      style={{ width: `${simResult.similarity_score * 100}%` }}
                    ></div>
                  </div>
                </div>

                {/* Clause overlap details */}
                {simResult.clause_overlap && (
                  <div className="space-y-3">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      <div className="bg-green-900/20 border border-green-700/40 rounded-lg p-3">
                        <div className="text-xs text-green-400 font-medium mb-2">Common ({simResult.clause_overlap.common?.length})</div>
                        <div className="space-y-1">
                          {(simResult.clause_overlap.common || []).map(t => (
                            <div key={t} className="text-xs text-slate-300 flex items-center gap-1">
                              <CheckCircle size={10} className="text-green-400" /> {t}
                            </div>
                          ))}
                        </div>
                      </div>
                      <div className="bg-red-900/20 border border-red-700/40 rounded-lg p-3">
                        <div className="text-xs text-red-400 font-medium mb-2">Only in A ({simResult.clause_overlap.only_in_contract1?.length})</div>
                        <div className="space-y-1">
                          {(simResult.clause_overlap.only_in_contract1 || []).length === 0
                            ? <div className="text-xs text-slate-500 italic">None — all clauses shared</div>
                            : (simResult.clause_overlap.only_in_contract1 || []).map(t => (
                                <div key={t} className="text-xs text-slate-300 flex items-center gap-1">
                                  <AlertCircle size={10} className="text-red-400" /> {t}
                                </div>
                              ))
                          }
                        </div>
                      </div>
                      <div className="bg-blue-900/20 border border-blue-700/40 rounded-lg p-3">
                        <div className="text-xs text-blue-400 font-medium mb-2">Only in B ({simResult.clause_overlap.only_in_contract2?.length})</div>
                        <div className="space-y-1">
                          {(simResult.clause_overlap.only_in_contract2 || []).length === 0
                            ? <div className="text-xs text-slate-500 italic">None — all clauses shared</div>
                            : (simResult.clause_overlap.only_in_contract2 || []).map(t => (
                                <div key={t} className="text-xs text-slate-300 flex items-center gap-1">
                                  <Info size={10} className="text-blue-400" /> {t}
                                </div>
                              ))
                          }
                        </div>
                      </div>
                    </div>

                    {/* Risk comparison table for shared clauses */}
                    {simResult.clause_risk_comparison && Object.keys(simResult.clause_risk_comparison).length > 0 && (
                      <div className="bg-slate-800/60 border border-slate-700 rounded-lg p-3">
                        <div className="text-xs text-slate-400 font-semibold mb-2 flex items-center gap-1">
                          <Activity size={11} /> Risk Score Comparison (shared clauses)
                        </div>
                        <div className="space-y-1.5 max-h-48 overflow-y-auto">
                          {Object.entries(simResult.clause_risk_comparison).map(([name, data]) => (
                            <div key={name} className="grid grid-cols-[1fr_auto_auto_auto] gap-2 items-center text-xs">
                              <span className="text-slate-300 truncate">{name}</span>
                              <span className="text-purple-300 font-mono">{(data.contract1_risk * 100).toFixed(0)}%</span>
                              <span className="text-slate-500">↔</span>
                              <span className="text-blue-300 font-mono">{(data.contract2_risk * 100).toFixed(0)}%
                                <span className={`ml-1 ${data.diff > 0.1 ? 'text-red-400' : data.diff > 0.05 ? 'text-yellow-400' : 'text-green-400'}`}>
                                  ({data.diff > 0 ? '+' : ''}{(data.diff * 100).toFixed(0)}%)
                                </span>
                              </span>
                            </div>
                          ))}
                        </div>
                        <div className="text-xs text-slate-600 mt-2">A (purple) vs B (blue) — diff highlights where contracts differ in risk</div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════
          TAB 3 — GNN SCORING
      ═══════════════════════════════════════════════════════════ */}
      {activeTab === 'gnn' && (
        <div className="space-y-5 animate-fadeIn">
          <div className="bg-slate-900 rounded-2xl border border-slate-700 p-6 hover:border-pink-700/50 transition-all">
            <h2 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
              <Brain className="w-5 h-5 text-pink-400" />
              Graph Neural Network Contract Scoring
            </h2>
            <p className="text-slate-400 text-sm mb-5">
              A GCN (Graph Convolutional Network) trained on the contract risk graph predicts overall
              contract risk and stability. Falls back to PageRank-weighted rule-based scoring when
              PyTorch Geometric is unavailable.
            </p>

            {/* Source toggle */}
            <div className="flex items-center gap-2 mb-3">
              <button
                onClick={() => { setGnnUseCustom(false); setGnnResult(null); }}
                className={`px-3 py-1 rounded-lg text-xs font-semibold border transition-all ${!gnnUseCustom ? 'bg-pink-600 border-pink-500 text-white' : 'bg-slate-800 border-slate-600 text-slate-400 hover:text-white'}`}
              >MySQL Contract</button>
              <button
                onClick={() => { setGnnUseCustom(true); setGnnResult(null); }}
                className={`px-3 py-1 rounded-lg text-xs font-semibold border transition-all ${gnnUseCustom ? 'bg-emerald-600 border-emerald-500 text-white' : 'bg-slate-800 border-slate-600 text-slate-400 hover:text-white'}`}
              >Neo4j / CUAD ID</button>
              {gnnUseCustom && <span className="text-xs text-emerald-400">← paste your CUAD JSON contract ID here</span>}
            </div>

            <div className="flex flex-col md:flex-row gap-4 items-end mb-5">
              <div className="flex-1">
                {gnnUseCustom ? (
                  <div className="flex flex-col gap-1">
                    <label className="text-xs text-slate-400 font-medium">Neo4j Contract ID</label>
                    <input
                      type="text"
                      value={gnnCustomId}
                      onChange={e => setGnnCustomId(e.target.value)}
                      placeholder="e.g. C-1001"
                      className="bg-slate-800 border border-emerald-600 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-emerald-400 focus:ring-1 focus:ring-emerald-400/30 transition-all"
                    />
                  </div>
                ) : (
                  <ContractSelect value={gnnContractId} onChange={setGnnContractId} label="Select Contract to Score" />
                )}
              </div>
              <button
                onClick={handleGNN}
                disabled={(gnnUseCustom ? !gnnCustomId.trim() : !gnnContractId) || gnnLoading}
                className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-pink-600 to-rose-600 hover:from-pink-700 hover:to-rose-700 text-white font-semibold rounded-xl transition-all disabled:opacity-40 disabled:cursor-not-allowed whitespace-nowrap"
              >
                {gnnLoading ? <><div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>Scoring…</> : <><Brain size={15} /> Score with GNN</>}
              </button>
            </div>

            {gnnResult && (
              <div className="space-y-6">
                {/* Method badge */}
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                    gnnResult.method === 'pytorch_geometric_gcn'
                      ? 'bg-pink-900/40 text-pink-300 border border-pink-700'
                      : 'bg-slate-700 text-slate-300 border border-slate-600'
                  }`}>
                    {gnnResult.method === 'pytorch_geometric_gcn' ? '🧠 PyTorch GCN' : '📊 Rule-based Fallback'}
                  </span>
                  <span className="text-xs text-slate-500">{gnnResult.node_count} nodes · {gnnResult.edge_count} edges in graph</span>
                </div>

                {/* Score gauges */}
                <div className="flex flex-wrap gap-8 justify-center py-4">
                  <div className="text-center">
                    <div
                      className={`w-36 h-36 rounded-full flex flex-col items-center justify-center border-4 ${gnnResult.risk_score >= 70 ? 'border-red-500' : gnnResult.risk_score >= 40 ? 'border-yellow-500' : 'border-green-500'} bg-slate-800`}
                      style={{ boxShadow: gnnResult.risk_score >= 70 ? '0 0 30px #ef444466' : gnnResult.risk_score >= 40 ? '0 0 30px #f59e0b66' : '0 0 30px #10b98166' }}
                    >
                      <span className={`text-4xl font-black ${getRiskColor(gnnResult.risk_score)}`}>{gnnResult.risk_score}</span>
                      <span className="text-xs text-slate-400 mt-1">/ 100</span>
                    </div>
                    <div className="mt-3 text-sm font-semibold text-slate-300">Risk Score</div>
                    <div className={`text-xs mt-1 ${gnnResult.risk_score >= 70 ? 'text-red-400' : gnnResult.risk_score >= 40 ? 'text-yellow-400' : 'text-green-400'}`}>
                      {gnnResult.risk_score >= 70 ? 'HIGH RISK' : gnnResult.risk_score >= 40 ? 'MEDIUM RISK' : 'LOW RISK'}
                    </div>
                  </div>

                  <div className="text-center">
                    <div
                      className={`w-36 h-36 rounded-full flex flex-col items-center justify-center border-4 ${gnnResult.stability_score >= 70 ? 'border-green-500' : gnnResult.stability_score >= 40 ? 'border-yellow-500' : 'border-red-500'} bg-slate-800`}
                      style={{ boxShadow: gnnResult.stability_score >= 70 ? '0 0 30px #10b98166' : gnnResult.stability_score >= 40 ? '0 0 30px #f59e0b66' : '0 0 30px #ef444466' }}
                    >
                      <span className={`text-4xl font-black ${gnnResult.stability_score >= 70 ? 'text-green-400' : gnnResult.stability_score >= 40 ? 'text-yellow-400' : 'text-red-400'}`}>
                        {gnnResult.stability_score}
                      </span>
                      <span className="text-xs text-slate-400 mt-1">/ 100</span>
                    </div>
                    <div className="mt-3 text-sm font-semibold text-slate-300">Stability Score</div>
                    <div className={`text-xs mt-1 ${gnnResult.stability_score >= 70 ? 'text-green-400' : gnnResult.stability_score >= 40 ? 'text-yellow-400' : 'text-red-400'}`}>
                      {gnnResult.stability_score >= 70 ? 'STABLE' : gnnResult.stability_score >= 40 ? 'MODERATE' : 'UNSTABLE'}
                    </div>
                  </div>
                </div>

                {/* Top risky clauses */}
                {gnnResult.top_risky_clauses && gnnResult.top_risky_clauses.length > 0 && (
                  <div>
                    <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                      <AlertCircle size={14} className="text-red-400" />
                      Top Risk Clauses (GNN)
                    </h3>
                    <div className="space-y-2">
                      {gnnResult.top_risky_clauses.map((c, idx) => (
                        <div key={idx} className="flex items-center gap-3 bg-slate-800/60 rounded-lg px-4 py-3 border border-slate-700 hover:border-red-700/50 transition-all">
                          <span className="text-xs font-black text-slate-500 w-5">#{idx + 1}</span>
                          <div className="flex-1 min-w-0">
                            <div className="text-sm text-white font-medium truncate">{c.clause_name}</div>
                            <div className={`text-xs mt-0.5 ${c.risk_level === 'HIGH' ? 'text-red-400' : c.risk_level === 'MEDIUM' ? 'text-yellow-400' : 'text-green-400'}`}>
                              {c.risk_level}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className={`text-base font-bold ${getRiskColor(c.gnn_risk)}`}>{c.gnn_risk}</div>
                            <div className="text-xs text-slate-500">GNN risk</div>
                          </div>
                          <div className="w-20 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${c.gnn_risk >= 70 ? 'bg-red-500' : c.gnn_risk >= 40 ? 'bg-yellow-500' : 'bg-green-500'}`}
                              style={{ width: `${c.gnn_risk}%` }}
                            ></div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════
          TAB 4 — HOW IT WORKS
      ═══════════════════════════════════════════════════════════ */}
      {activeTab === 'howto' && (
        <div className="space-y-5 animate-fadeIn">
          {/* Architecture overview */}
          <div className="bg-slate-900 rounded-2xl border border-amber-700/40 p-6">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-amber-400" />
              CUAD Graph Architecture
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              {[
                { layer: 'Frontend', tech: 'React + React Flow', desc: 'Interactive Neo4j-style graph visualization with real-time parameter updates' },
                { layer: 'Backend', tech: 'Django + NetworkX', desc: 'CUAD graph service with PageRank, cosine similarity, and GNN scoring' },
                { layer: 'Graph DB', tech: 'Neo4j (optional)', desc: 'Persistent contract knowledge graph; falls back to in-memory NetworkX' },
              ].map(item => (
                <div key={item.layer} className="bg-slate-800 rounded-xl p-4 border border-slate-700">
                  <div className="text-amber-400 text-xs font-bold uppercase tracking-wider mb-1">{item.layer}</div>
                  <div className="text-white font-semibold mb-2">{item.tech}</div>
                  <div className="text-slate-400 text-xs leading-relaxed">{item.desc}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Node types */}
          <div className="bg-slate-900 rounded-2xl border border-slate-700 p-6">
            <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
              <Database size={16} className="text-cyan-400" />
              CUAD Graph Node Types (13)
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
              {[
                { type: 'Contract', color: '#68BC00', desc: 'Top-level contract entity' },
                { type: 'Clause', color: '#4C8EDA', desc: 'Individual clause text + risk score' },
                { type: 'ClauseType', color: '#9063CD', desc: '14 CUAD canonical clause categories' },
                { type: 'Party', color: '#FFD86E', desc: 'Named parties (partyA, partyB)' },
                { type: 'Jurisdiction', color: '#9063CD', desc: 'Governing law jurisdiction' },
                { type: 'Obligation', color: '#F79767', desc: 'Extracted contractual obligations' },
                { type: 'Risk', color: '#F16667', desc: 'Risk nodes (score ≥ 0.5)' },
                { type: 'Industry', color: '#06B6D4', desc: 'Contract type / industry sector' },
              ].map(n => (
                <div key={n.type} className="flex items-start gap-2 bg-slate-800/60 rounded-lg p-3 border border-slate-700">
                  <div className="w-3 h-3 rounded-full mt-0.5 flex-shrink-0" style={{ backgroundColor: n.color, boxShadow: `0 0 6px ${n.color}88` }}></div>
                  <div>
                    <div className="text-xs font-bold text-white">{n.type}</div>
                    <div className="text-xs text-slate-400 mt-0.5 leading-relaxed">{n.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Relationships */}
          <div className="bg-slate-900 rounded-2xl border border-slate-700 p-6">
            <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
              <Network size={16} className="text-purple-400" />
              Relationship Types (11)
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
              {[
                ['HAS_CLAUSE', 'Contract → Clause'],
                ['IS_TYPE', 'Clause → ClauseType'],
                ['HAS_PARTY', 'Contract → Party'],
                ['GOVERNED_BY', 'Contract → Jurisdiction'],
                ['CREATES_OBLIGATION', 'Clause → Obligation'],
                ['CREATES_RISK', 'Clause → Risk'],
                ['REFERS_TO', 'Clause → Clause'],
                ['DEFINES', 'Clause → Definition'],
                ['AMENDED_BY', 'Contract → Amendment'],
                ['BELONGS_TO', 'Contract → Industry'],
                ['HAS_VECTOR', 'Contract → ContractEmbedding'],
              ].map(([rel, desc]) => (
                <div key={rel} className="flex items-center gap-2 py-1.5 px-3 bg-slate-800/40 rounded-lg border border-slate-700/50">
                  <code className="text-purple-300 font-mono">{rel}</code>
                  <span className="text-slate-400">{desc}</span>
                </div>
              ))}
            </div>
          </div>

          {/* GNN Architecture */}
          <div className="bg-slate-900 rounded-2xl border border-pink-700/30 p-6">
            <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
              <Brain size={16} className="text-pink-400" />
              Graph Neural Network Architecture
            </h3>
            <div className="space-y-3 text-sm">
              <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 font-mono text-xs text-slate-300 leading-relaxed">
                <div className="text-pink-400 mb-2"># SimpleGCN (PyTorch Geometric)</div>
                <div>Input features: [risk_score, type_multiplier, type_idx]  # 3-dim</div>
                <div>conv1 = GCNConv(3 → 16)  # Message passing layer 1</div>
                <div>relu activation</div>
                <div>conv2 = GCNConv(16 → 1)  # Output layer</div>
                <div>sigmoid → risk probability per node</div>
                <div className="text-slate-500 mt-2"># Contract score = mean(sigmoid outputs) × 100</div>
                <div className="text-slate-500"># Stability = 100 − risk_score</div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                <div className="bg-slate-800 rounded-lg p-3 border border-slate-700">
                  <div className="text-pink-300 font-semibold mb-1">Edge Construction</div>
                  <div className="text-slate-400">Clauses of the same canonical CUAD type are connected bidirectionally, weighted by average risk score.</div>
                </div>
                <div className="bg-slate-800 rounded-lg p-3 border border-slate-700">
                  <div className="text-amber-300 font-semibold mb-1">Fallback</div>
                  <div className="text-slate-400">When PyTorch unavailable: PageRank centrality × risk_score × clause_type_multiplier (weighted average).</div>
                </div>
              </div>
            </div>
          </div>

          {/* Diff scoring */}
          <div className="bg-slate-900 rounded-2xl border border-slate-700 p-6">
            <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
              <GitCompare size={16} className="text-blue-400" />
              Differential Scoring Formula
            </h3>
            <div className="bg-slate-800 rounded-lg p-4 font-mono text-xs text-slate-300 border border-slate-700">
              <div className="text-blue-300 mb-2"># Weighted contract score</div>
              <div>risk_total = Σ (clause.risk_score × clause_type_multiplier)</div>
              <div>obligation_count = count(clauses where risk_score ≥ 0.4)</div>
              <div className="mt-1">score = risk_total × risk_weight × 10 + obligation_count × obligation_weight × 2</div>
              <div className="mt-2 text-slate-500"># Differential score</div>
              <div>diff_score = |score_A - score_B|</div>
              <div className="mt-2 text-slate-500"># Node diff classification</div>
              <div>same     ← both contracts, |risk_A - risk_B| &lt; 0.15</div>
              <div>modified ← both contracts, |risk_A - risk_B| ≥ 0.15</div>
              <div>missing  ← only in Contract A</div>
              <div>new      ← only in Contract B</div>
            </div>
          </div>
        </div>
      )}

      {/* ════════════════════════════════════════════════════════════════════
          Tab 4 — AI GraphRAG (Neo4j knowledge graph)
      ════════════════════════════════════════════════════════════════════ */}
      {activeTab === 'rag' && (
        <div className="space-y-6">
          {/* Section A: Single Contract Analysis */}
          <div className="bg-slate-900 rounded-2xl border border-violet-700/30 p-6">
            <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
              <MessageSquare size={16} className="text-violet-400" />
              AI Contract Risk Analysis (GraphRAG)
            </h3>
            <div className="flex flex-wrap gap-4 mb-4">
              <div className="flex-1 min-w-[220px]">
                <ContractSelect value={ragContractId} onChange={setRagContractId} label="Contract to Analyze" placeholder="Select contract" />
              </div>
              <div className="flex items-end">
                <button
                  onClick={handleRagAnalyze}
                  disabled={ragLoading || !ragContractId}
                  className="px-5 py-2 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 rounded-lg text-white font-medium flex items-center gap-2 transition-colors"
                >
                  {ragLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                  {ragLoading ? 'Analyzing...' : 'Analyze with AI'}
                </button>
              </div>
            </div>
            {ragResult && (
              <div className="space-y-4">
                <div className="flex items-center gap-3 flex-wrap">
                  <span className="px-2 py-1 bg-violet-900/40 border border-violet-700 text-violet-300 text-xs rounded">
                    {ragResult.source}
                  </span>
                  <span className="text-slate-400 text-sm">{ragResult.contract_name}</span>
                  <span className="text-red-400 text-sm font-semibold">
                    {ragResult.graph_context?.high_risk_count} HIGH risk clauses
                  </span>
                </div>
                <div className="bg-slate-800 rounded-xl border border-violet-700/20 p-5">
                  <pre className="text-slate-200 text-sm whitespace-pre-wrap font-sans leading-relaxed">
                    {ragResult.ai_analysis}
                  </pre>
                </div>
                {/* Top clauses */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {(ragResult.graph_context?.top_clauses || []).slice(0, 4).map((c, i) => (
                    <div key={i} className={`p-3 rounded-lg border text-xs ${c.risk_level === 'HIGH' ? 'bg-red-900/20 border-red-700/40' : c.risk_level === 'MEDIUM' ? 'bg-yellow-900/20 border-yellow-700/40' : 'bg-green-900/20 border-green-700/40'}`}>
                      <div className="font-semibold text-white">{c.name}</div>
                      <div className="text-slate-400">{c.type} · Risk: {(c.risk_score * 100).toFixed(0)}%</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Section B: AI Comparison of Two Contracts */}
          <div className="bg-slate-900 rounded-2xl border border-violet-700/30 p-6">
            <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
              <GitCompare size={16} className="text-violet-400" />
              AI Contract Comparison (GraphRAG)
            </h3>
            <div className="flex flex-wrap gap-4 mb-4">
              <div className="flex-1 min-w-[200px]">
                <ContractSelect value={ragCompC1} onChange={setRagCompC1} label="Contract A" placeholder="Select contract A" />
              </div>
              <div className="flex-1 min-w-[200px]">
                <ContractSelect value={ragCompC2} onChange={setRagCompC2} label="Contract B" placeholder="Select contract B" />
              </div>
              <div className="flex items-end">
                <button
                  onClick={handleRagCompare}
                  disabled={ragCompLoading || !ragCompC1 || !ragCompC2}
                  className="px-5 py-2 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 rounded-lg text-white font-medium flex items-center gap-2 transition-colors"
                >
                  {ragCompLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <GitCompare className="w-4 h-4" />}
                  {ragCompLoading ? 'Comparing...' : 'Compare with AI'}
                </button>
              </div>
            </div>
            {ragCompResult && (
              <div className="bg-slate-800 rounded-xl border border-violet-700/20 p-5">
                <pre className="text-slate-200 text-sm whitespace-pre-wrap font-sans leading-relaxed">
                  {ragCompResult.ai_comparison}
                </pre>
              </div>
            )}
          </div>

          {/* Section C: Negotiation Recommendations */}
          <div className="bg-slate-900 rounded-2xl border border-violet-700/30 p-6">
            <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
              <Target size={16} className="text-violet-400" />
              AI Negotiation Recommendations
            </h3>
            <div className="flex flex-wrap gap-4 mb-4">
              <div className="flex-1 min-w-[200px]">
                <ContractSelect value={ragContractId} onChange={setRagContractId} label="Contract" placeholder="Select contract" />
              </div>
              <div className="flex-1 min-w-[260px]">
                <label className="text-xs text-slate-400 mb-1 block">Negotiation Goals (optional)</label>
                <input
                  type="text"
                  value={ragNegGoals}
                  onChange={e => setRagNegGoals(e.target.value)}
                  placeholder="e.g. reduce liability exposure, shorten notice period"
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-100 text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
              </div>
              <div className="flex items-end">
                <button
                  onClick={handleRagNegotiate}
                  disabled={ragNegLoading || !ragContractId}
                  className="px-5 py-2 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 rounded-lg text-white font-medium flex items-center gap-2 transition-colors"
                >
                  {ragNegLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Target className="w-4 h-4" />}
                  {ragNegLoading ? 'Generating...' : 'Get Strategy'}
                </button>
              </div>
            </div>
            {ragNegResult && (
              <div className="space-y-4">
                <div className="bg-slate-800 rounded-xl border border-violet-700/20 p-5">
                  <pre className="text-slate-200 text-sm whitespace-pre-wrap font-sans leading-relaxed">
                    {ragNegResult.ai_recommendations}
                  </pre>
                </div>
                {ragNegResult.quick_tips?.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-white mb-3">Quick Action Tips</h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {ragNegResult.quick_tips.map((tip, i) => (
                        <div key={i} className={`p-3 rounded-lg border text-xs ${tip.urgency === 'HIGH' ? 'border-red-700/40 bg-red-900/20' : tip.urgency === 'MEDIUM' ? 'border-yellow-700/40 bg-yellow-900/20' : 'border-blue-700/40 bg-blue-900/20'}`}>
                          <div className="font-semibold text-white mb-1">{tip.action} — {tip.clause}</div>
                          <div className="text-slate-300">{tip.tip}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ════════════════════════════════════════════════════════════════════
          Tab 5 — GNN Training (200-epoch loop)
      ════════════════════════════════════════════════════════════════════ */}
      {activeTab === 'train' && (
        <div className="space-y-6">
          <div className="bg-slate-900 rounded-2xl border border-orange-700/30 p-6">
            <h3 className="text-base font-bold text-white mb-2 flex items-center gap-2">
              <Cpu size={16} className="text-orange-400" />
              GNN Training — PyTorch Geometric GCN
            </h3>
            <p className="text-slate-400 text-sm mb-5">
              Train a Graph Convolutional Network on the contract graph. Runs <code className="text-orange-300">N</code> epochs
              with Adam optimizer, MSE loss on text-based risk scores. Saves checkpoint to <code className="text-orange-300">/tmp/</code>.
            </p>
            <div className="flex flex-wrap gap-4 mb-5">
              <div className="flex-1 min-w-[220px]">
                <ContractSelect value={trainContractId} onChange={setTrainContractId} label="Contract to Train On" placeholder="Select contract" />
              </div>
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Epochs: {trainEpochs}</label>
                <input
                  type="range" min={10} max={500} step={10}
                  value={trainEpochs}
                  onChange={e => setTrainEpochs(parseInt(e.target.value))}
                  className="w-40 accent-orange-500"
                />
              </div>
              <div className="flex items-end">
                <button
                  onClick={handleGNNTrain}
                  disabled={trainLoading || !trainContractId}
                  className="px-5 py-2 bg-orange-600 hover:bg-orange-500 disabled:opacity-50 rounded-lg text-white font-medium flex items-center gap-2 transition-colors"
                >
                  {trainLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <PlayCircle className="w-4 h-4" />}
                  {trainLoading ? `Training (${trainEpochs} epochs)...` : 'Train GNN'}
                </button>
              </div>
            </div>
            {trainResult && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {[
                    { label: 'Trained', value: trainResult.trained ? '✓ Yes' : '✗ Fallback', color: trainResult.trained ? 'text-green-400' : 'text-yellow-400' },
                    { label: 'Epochs', value: trainResult.epochs || '-', color: 'text-orange-400' },
                    { label: 'Final Loss', value: trainResult.final_loss?.toFixed(6) || '-', color: 'text-blue-400' },
                    { label: 'Method', value: trainResult.method, color: 'text-slate-300' },
                  ].map((s, i) => (
                    <div key={i} className="bg-slate-800 rounded-lg p-3 border border-slate-700 text-center">
                      <div className={`text-lg font-bold ${s.color}`}>{s.value}</div>
                      <div className="text-xs text-slate-400">{s.label}</div>
                    </div>
                  ))}
                </div>
                {/* Loss curve */}
                {trainResult.loss_history?.length > 1 && (
                  <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
                    <h4 className="text-sm font-semibold text-white mb-3">Training Loss Curve</h4>
                    <ResponsiveContainer width="100%" height={180}>
                      <LineChart data={trainResult.loss_history}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis dataKey="epoch" stroke="#64748b" tick={{ fontSize: 10 }} />
                        <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
                        <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }} />
                        <Line type="monotone" dataKey="loss" stroke="#f97316" strokeWidth={2} dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}
                {/* Final risk/stability */}
                <div className="flex flex-wrap gap-4 justify-center pt-2">
                  <ScoreGauge value={trainResult.risk_score} label="Risk Score" color={trainResult.risk_score >= 70 ? 'border-red-500' : trainResult.risk_score >= 40 ? 'border-yellow-500' : 'border-green-500'} />
                  <ScoreGauge value={trainResult.stability_score} label="Stability Score" color={trainResult.stability_score >= 70 ? 'border-green-500' : trainResult.stability_score >= 40 ? 'border-yellow-500' : 'border-red-500'} />
                </div>
                {trainResult.checkpoint_path && (
                  <div className="text-xs text-slate-500 text-center">Checkpoint saved: <code className="text-orange-300">{trainResult.checkpoint_path}</code></div>
                )}
                {trainResult.note && (
                  <div className="text-xs text-yellow-400 bg-yellow-900/20 border border-yellow-700/30 rounded p-3">{trainResult.note}</div>
                )}
                {trainResult.fallback_reason && (
                  <div className="text-xs text-orange-300 bg-orange-900/20 border border-orange-700/30 rounded p-3">
                    <span className="font-semibold">PyTorch fallback reason: </span>{trainResult.fallback_reason}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ════════════════════════════════════════════════════════════════════
          Tab 6 — 3D Graph Visualization
      ════════════════════════════════════════════════════════════════════ */}
      {activeTab === 'graph3d' && (
        <div className="space-y-4">
          <div className="bg-slate-900 rounded-2xl border border-teal-700/30 p-4">
            <h3 className="text-base font-bold text-white mb-2 flex items-center gap-2">
              <Network size={16} className="text-teal-400" />
              3D Contract Knowledge Graph
            </h3>
            <p className="text-slate-400 text-xs mb-3">
              Interactive 3D WebGL visualization. Drag to rotate · Scroll to zoom · Click node for details.
              Showing {diffResult?.nodes?.length || 0} nodes from the last comparison.
            </p>
          </div>
          {(diffResult?.nodes?.length > 0 || multiResult?.nodes?.length > 0) ? (() => {
            const activeNodes = multiResult?.nodes?.length > 0 ? multiResult.nodes : diffResult.nodes;
            const activeEdges = multiResult?.nodes?.length > 0 ? multiResult.edges : diffResult.edges;
            const isPortfolio = multiResult?.nodes?.length > 0;
            return (
              <ContractGraph3D
                nodes={activeNodes.map(n => ({
                  id: n.id,
                  label: n.data?.label || n.id,
                  type: n.data?.type || 'Clause',
                  risk_score: n.data?.risk_c1 || n.data?.avg_risk || 0,
                  size: n.data?.size || 40,
                  diff_status: n.data?.diff_status || n.data?.coverage,
                }))}
                edges={activeEdges.map(e => ({ id: e.id, source: e.source, target: e.target, label: e.label }))}
                height="650px"
              />
            );
          })() : (
            <div className="flex flex-col items-center justify-center h-64 bg-slate-900 rounded-2xl border border-slate-700">
              <Network className="w-12 h-12 text-slate-600 mb-3" />
              <p className="text-slate-400 text-sm">Run a Graph Diff or Portfolio comparison first to see the 3D visualization</p>
              <button
                onClick={() => setActiveTab('diff')}
                className="mt-3 px-4 py-2 bg-teal-700 hover:bg-teal-600 rounded-lg text-white text-sm transition-colors"
              >
                Go to Graph Diff
              </button>
            </div>
          )}
        </div>
      )}

      {/* ════════════════════════════════════════════════════════════════════
          Tab 7 — Amendment History (Temporal Graph)
      ════════════════════════════════════════════════════════════════════ */}
      {activeTab === 'temporal' && (
        <div className="space-y-6">
          {/* Track new amendment */}
          <div className="bg-slate-900 rounded-2xl border border-blue-700/30 p-6">
            <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
              <Clock size={16} className="text-blue-400" />
              Track Contract Amendment
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
              <ContractSelect value={amendContractId} onChange={setAmendContractId} label="Contract" placeholder="Select contract" />
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Amendment Date (optional)</label>
                <input type="date" value={amendDate} onChange={e => setAmendDate(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div className="sm:col-span-2">
                <label className="text-xs text-slate-400 mb-1 block">Amendment Description</label>
                <input type="text" value={amendDesc} onChange={e => setAmendDesc(e.target.value)}
                  placeholder="e.g. Rate increase + liability cap added"
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-100 text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
            </div>
            <button onClick={handleTrackAmendment} disabled={amendLoading || !amendContractId || !amendDesc}
              className="px-5 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg text-white font-medium flex items-center gap-2 transition-colors">
              {amendLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Clock className="w-4 h-4" />}
              {amendLoading ? 'Tracking...' : 'Record Amendment'}
            </button>
            {amendResult && (
              <div className="mt-4 p-4 bg-blue-900/20 border border-blue-700/30 rounded-xl">
                <div className="text-green-400 font-semibold mb-2">✓ Amendment recorded</div>
                <div className="text-xs text-slate-300 space-y-1">
                  <div>ID: <code className="text-blue-300">{amendResult.amendment_id}</code></div>
                  <div>Date: {amendResult.date}</div>
                  <div>Affected clauses: {amendResult.total_affected} ({amendResult.risk_increased} with increased risk)</div>
                </div>
                {amendResult.affected_clauses?.length > 0 && (
                  <div className="mt-3 space-y-2">
                    {amendResult.affected_clauses.map((c, i) => (
                      <div key={i} className="flex items-center justify-between text-xs bg-slate-800 rounded p-2">
                        <span className="text-slate-300">{c.clause_name}</span>
                        <span className="text-slate-400">{c.old_risk?.toFixed(3)} → <span className="text-red-400 font-semibold">{c.new_risk?.toFixed(3)}</span> (+{c.delta?.toFixed(3)})</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Get amendment history */}
          <div className="bg-slate-900 rounded-2xl border border-blue-700/30 p-6">
            <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
              <TrendingUp size={16} className="text-blue-400" />
              Amendment Timeline
            </h3>
            <div className="flex flex-wrap gap-4 mb-4">
              <div className="flex-1 min-w-[220px]">
                <ContractSelect value={historyContractId} onChange={setHistoryContractId} label="Contract" placeholder="Select contract" />
              </div>
              <div className="flex items-end">
                <button onClick={handleGetHistory} disabled={historyLoading || !historyContractId}
                  className="px-5 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg text-white font-medium flex items-center gap-2 transition-colors">
                  {historyLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <TrendingUp className="w-4 h-4" />}
                  {historyLoading ? 'Loading...' : 'Get History'}
                </button>
              </div>
            </div>
            {historyResult && (
              <div className="space-y-3">
                <div className="flex items-center gap-4 text-sm">
                  <span className="text-slate-400">{historyResult.contract_name}</span>
                  <span className="text-blue-400 font-semibold">{historyResult.total_amendments} amendments</span>
                  <span className={`font-semibold ${historyResult.current_risk_level === 'HIGH' ? 'text-red-400' : historyResult.current_risk_level === 'MEDIUM' ? 'text-yellow-400' : 'text-green-400'}`}>
                    Current risk: {historyResult.current_risk_level} ({(historyResult.current_avg_risk * 100).toFixed(0)}%)
                  </span>
                </div>
                {historyResult.amendments?.length > 0 ? (
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {historyResult.amendments.map((a, i) => (
                      <div key={i} className="bg-slate-800 rounded-lg p-3 border border-slate-700 text-xs">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-blue-300 font-mono">{a.id}</span>
                          <span className="text-slate-400">{a.date}</span>
                        </div>
                        <div className="text-slate-200">{a.description}</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-slate-500 text-sm">No amendments recorded yet.</div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ════════════════════════════════════════════════════════════════════
          Tab 8 — CUAD JSON Bulk Ingestion
      ════════════════════════════════════════════════════════════════════ */}
      {activeTab === 'cuadjson' && (
        <div className="space-y-6">
          <div className="bg-slate-900 rounded-2xl border border-emerald-700/30 p-6">
            <h3 className="text-base font-bold text-white mb-2 flex items-center gap-2">
              <FileJson size={16} className="text-emerald-400" />
              CUAD Dataset JSON Bulk Ingestion
            </h3>
            <p className="text-slate-400 text-sm mb-4">
              Paste CUAD-format JSON (array or single object) to ingest into Neo4j with all 13 node types.
              Max 100 contracts per batch.
            </p>
            <div className="bg-slate-800 rounded-lg p-3 border border-slate-700 text-xs font-mono text-slate-400 mb-4">
              {`[{\n  "contract_id": "C-1001",\n  "name": "Enterprise SaaS Agreement",\n  "party_a": "VendorCorp",\n  "party_b": "ClientCorp",\n  "jurisdiction": "Delaware",\n  "industry": "Technology",\n  "clauses": [{\n    "clause_id": "CL-1",\n    "clause_type": "Termination",\n    "clause_name": "Termination for Convenience",\n    "text": "...",\n    "risk_score": 0.7,\n    "confidence": 85.0\n  }],\n  "amendments": [],\n  "definitions": []\n}]`}
            </div>
            <textarea
              value={cuadJsonText}
              onChange={e => setCuadJsonText(e.target.value)}
              rows={8}
              placeholder="Paste CUAD JSON here..."
              className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-100 text-xs font-mono placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 mb-4 resize-y"
            />
            <button onClick={handleCuadJsonIngest} disabled={cuadJsonLoading || !cuadJsonText.trim()}
              className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 rounded-lg text-white font-medium flex items-center gap-2 transition-colors">
              {cuadJsonLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Database className="w-4 h-4" />}
              {cuadJsonLoading ? 'Ingesting...' : 'Ingest to Neo4j'}
            </button>
            {cuadJsonResult && (
              <div className="mt-4 p-4 bg-emerald-900/20 border border-emerald-700/30 rounded-xl">
                <div className="text-green-400 font-semibold mb-3">✓ Ingestion complete</div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {[
                    { label: 'Contracts', value: cuadJsonResult.contracts_ingested },
                    { label: 'Nodes Created', value: cuadJsonResult.total_nodes_created },
                    { label: 'Relationships', value: cuadJsonResult.total_relationships_created },
                    { label: 'Errors', value: cuadJsonResult.errors?.length || 0 },
                  ].map((s, i) => (
                    <div key={i} className="bg-slate-800 rounded-lg p-3 border border-slate-700 text-center">
                      <div className="text-xl font-bold text-emerald-400">{s.value}</div>
                      <div className="text-xs text-slate-400">{s.label}</div>
                    </div>
                  ))}
                </div>
                {cuadJsonResult.errors?.length > 0 && (
                  <div className="mt-3 text-xs text-red-400 space-y-1">
                    {cuadJsonResult.errors.map((e, i) => <div key={i}>{e.contract_id}: {e.error}</div>)}
                  </div>
                )}
                <div className="mt-2 text-xs text-slate-500">Mode: {cuadJsonResult.mode}</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ════════════════════════════════════════════════════════════════════
          Tab 9 — Build SIMILAR Edges
      ════════════════════════════════════════════════════════════════════ */}
      {activeTab === 'similar' && (
        <div className="space-y-6">
          <div className="bg-slate-900 rounded-2xl border border-yellow-700/30 p-6">
            <h3 className="text-base font-bold text-white mb-2 flex items-center gap-2">
              <Link size={16} className="text-yellow-400" />
              Auto-Build SIMILAR Edges in Neo4j
            </h3>
            <p className="text-slate-400 text-sm mb-5">
              Computes cosine similarity between all clause embeddings (AI or risk-vector fallback)
              and persists <code className="text-yellow-300">(:Clause)-[:SIMILAR]→(:Clause)</code> edges in Neo4j
              for clauses above the threshold.
            </p>
            <div className="flex flex-wrap gap-6 items-end mb-5">
              <div>
                <label className="text-xs text-slate-400 mb-1 block">Similarity Threshold: {similarThreshold.toFixed(2)}</label>
                <input type="range" min={0.3} max={0.99} step={0.05} value={similarThreshold}
                  onChange={e => setSimilarThreshold(parseFloat(e.target.value))}
                  className="w-48 accent-yellow-500" />
                <div className="text-xs text-slate-500 mt-1">
                  {similarThreshold >= 0.85 ? 'Very high — only near-identical clauses' :
                   similarThreshold >= 0.70 ? 'High — strong semantic match' :
                   similarThreshold >= 0.55 ? 'Medium — related clauses' :
                   'Low — broad similarity network'}
                </div>
              </div>
              <button onClick={handleBuildSimilar} disabled={similarLoading}
                className="px-5 py-2 bg-yellow-600 hover:bg-yellow-500 disabled:opacity-50 rounded-lg text-white font-medium flex items-center gap-2 transition-colors">
                {similarLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Link className="w-4 h-4" />}
                {similarLoading ? 'Building network...' : 'Build SIMILAR Graph'}
              </button>
            </div>
            {similarResult && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {[
                    { label: 'Clauses Compared', value: similarResult.clauses_compared, color: 'text-yellow-400' },
                    { label: 'Pairs Found', value: similarResult.pairs_found, color: 'text-green-400' },
                    { label: 'Edges Created', value: similarResult.edges_created, color: 'text-blue-400' },
                    { label: 'Threshold', value: similarResult.threshold?.toFixed(2), color: 'text-slate-300' },
                  ].map((s, i) => (
                    <div key={i} className="bg-slate-800 rounded-lg p-3 border border-slate-700 text-center">
                      <div className={`text-xl font-bold ${s.color}`}>{s.value}</div>
                      <div className="text-xs text-slate-400">{s.label}</div>
                    </div>
                  ))}
                </div>
                <div className="text-xs text-slate-500">Method: {similarResult.method}</div>
                {similarResult.note && <div className="text-xs text-yellow-400 bg-yellow-900/20 border border-yellow-700/30 rounded p-3">{similarResult.note}</div>}
                {similarResult.duplicates_skipped > 0 && (
                  <div className="text-xs text-orange-400 bg-orange-900/20 border border-orange-700/30 rounded p-3">
                    ⚠ {similarResult.duplicates_skipped} near-duplicate pairs (≥98% similarity) were skipped to show meaningful variations
                  </div>
                )}
                {similarResult.top_pairs?.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-white mb-2">Top Similar Clause Pairs</h4>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {similarResult.top_pairs.map((p, i) => (
                        <div key={i} className="flex items-center justify-between gap-3 text-xs bg-slate-800 rounded p-3 border border-slate-700 hover:border-yellow-600/50 transition-all">
                          <span className="text-slate-300 truncate flex-1" title={p.clause1_name || p.clause1_id}>
                            {p.clause1_name || p.clause1?.slice(0, 20) || 'Clause 1'}
                          </span>
                          <span className="text-yellow-400 font-bold whitespace-nowrap">↔ {(p.score * 100).toFixed(1)}%</span>
                          <span className="text-slate-300 truncate flex-1" title={p.clause2_name || p.clause2_id}>
                            {p.clause2_name || p.clause2?.slice(0, 20) || 'Clause 2'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
