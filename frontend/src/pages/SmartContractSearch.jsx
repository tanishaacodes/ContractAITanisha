import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search, Zap, BarChart3, Users, DollarSign, Shield,
  AlertTriangle, Clock, FileText, Cloud, CreditCard,
  Flame, FileQuestion, CheckCircle, RefreshCw, Brain,
  MessageSquare, TrendingUp, Target, Network, Filter,
  GitCompare, Eye, Database, Sparkles, BookOpen, Trash2,
  Plus, ChevronDown, ChevronUp, Scale, Activity, Maximize,
  Minimize, Maximize2,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, RadarChart, Radar, PolarGrid, PolarAngleAxis,
  LineChart, Line, CartesianGrid, Legend, RadialBarChart, RadialBar,
  AreaChart, Area,
} from 'recharts';
import {
  getPrebuiltSearches, runPrebuiltSearch, semanticSearch,
  aiAgentSearch, getSearchAnalytics, runNegotiationAgents,
  getContractStats, buildContractGraph, buildAllGraphs,
  scoreForceMajeure, getNegotiationMemory, clearNegotiationMemory,
  graphMultiHop, benchmarkClause, langchainAgentSearch,
  classifyClauseWithLegalBERT, getNode2VecRecommendations,
  syncGraphRealtime, bulkReclassify,
} from '../services/searchIntelligence';
import axios from 'axios';
import ReactFlow, { Background, Controls, MiniMap, ReactFlowProvider, MarkerType, useReactFlow } from 'reactflow';
import 'reactflow/dist/style.css';
import TemporalAnalysisPanel from '../components/TemporalAnalysisPanel';
import AnomalyDetectionPanel from '../components/AnomalyDetectionPanel';
import Neo4jGraphViz from '../components/Neo4jGraphViz';
import CFOFinancialMetricsPanel from '../components/CFOFinancialMetricsPanel';

const API_BASE = (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));
const authHeader = () => ({ Authorization: `Bearer ${localStorage.getItem('token')}` });

// Fetch user's contracts for dropdown selectors
async function fetchUserContracts() {
  const res = await axios.get(`${API_BASE}/api/contracts/list`, { headers: authHeader() });
  return (res.data.contracts || res.data || []).map(c => ({ id: c.id, title: c.originalFilename || c.original_filename || c.title || c.id }));
}

function useContracts() {
  const [contracts, setContracts] = useState([]);
  useEffect(() => {
    fetchUserContracts().then(setContracts).catch(() => {});
  }, []);
  return contracts;
}

function ContractSelect({ value, onChange, placeholder = 'Select a contract...' }) {
  const contracts = useContracts();
  return (
    <select
      value={value}
      onChange={e => onChange(e.target.value)}
      className="w-full px-3 py-2.5 bg-slate-900/60 border border-slate-600 text-white rounded-lg text-sm focus:outline-none focus:border-cyan-500"
    >
      <option value="">{placeholder}</option>
      {contracts.map(c => (
        <option key={c.id} value={c.id}>{c.title}</option>
      ))}
    </select>
  );
}

// ─── Constants ────────────────────────────────────────────────
const TABS = [
  { id: 'prebuilt',   label: 'Pre-built Searches', icon: Zap },
  { id: 'semantic',   label: 'Smart Search',        icon: Search },
  { id: 'agent',      label: 'AI Agent',            icon: Brain },
  { id: 'analytics',  label: 'Analytics',           icon: BarChart3 },
  { id: 'negotiate',  label: 'Negotiation AI',       icon: Users },
  { id: 'graph',      label: 'Graph Builder',        icon: Network },
  { id: 'fmscorer',  label: 'FM Risk Scorer',       icon: Cloud },
  { id: 'benchmark',  label: 'Clause Benchmark',     icon: Scale },
];

const RISK_COLORS = { HIGH: '#F16667', CRITICAL: '#ef4444', MEDIUM: '#FFD86E', LOW: '#68BC00', NOT_ANALYZED: '#6b7280' };
const PIE_COLORS  = ['#F16667','#FFD86E','#68BC00','#4C8EDA','#9063CD','#6b7280'];

const ICON_MAP = { DollarSign, Shield, AlertTriangle, Cloud, Clock, FileQuestion, Flame, CreditCard, Search };

const COLOR_CLASS = {
  emerald: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400 hover:border-emerald-400/70 hover:bg-emerald-500/20',
  red:     'border-red-500/40 bg-red-500/10 text-red-400 hover:border-red-400/70 hover:bg-red-500/20',
  orange:  'border-orange-500/40 bg-orange-500/10 text-orange-400 hover:border-orange-400/70 hover:bg-orange-500/20',
  yellow:  'border-yellow-500/40 bg-yellow-500/10 text-yellow-400 hover:border-yellow-400/70 hover:bg-yellow-500/20',
  slate:   'border-slate-500/40 bg-slate-500/10 text-slate-400 hover:border-slate-400/70 hover:bg-slate-500/20',
  blue:    'border-blue-500/40 bg-blue-500/10 text-blue-400 hover:border-blue-400/70 hover:bg-blue-500/20',
};

// ─── Shared Components ────────────────────────────────────────
function StatCard({ label, value, sub, color = 'cyan' }) {
  const map = {
    cyan:    'text-cyan-400 border-cyan-500/30 bg-cyan-500/5',
    red:     'text-red-400 border-red-500/30 bg-red-500/5',
    yellow:  'text-yellow-400 border-yellow-500/30 bg-yellow-500/5',
    emerald: 'text-emerald-400 border-emerald-500/30 bg-emerald-500/5',
    orange:  'text-orange-400 border-orange-500/30 bg-orange-500/5',
    slate:   'text-slate-400 border-slate-500/30 bg-slate-500/5',
  };
  const cls = map[color] || map.cyan;
  return (
    <div className={`rounded-xl border p-4 ${cls}`}>
      <div className="text-xs text-slate-400 mb-1">{label}</div>
      <div className={`text-2xl font-bold ${cls.split(' ')[0]}`}>{value}</div>
      {sub && <div className="text-xs text-slate-500 mt-1">{sub}</div>}
    </div>
  );
}

function RiskBadge({ level }) {
  const map = {
    HIGH:     'bg-red-500/20 text-red-400 border-red-500/40',
    CRITICAL: 'bg-red-700/30 text-red-300 border-red-600/50',
    MEDIUM:   'bg-yellow-500/20 text-yellow-400 border-yellow-500/40',
    LOW:      'bg-emerald-500/20 text-emerald-400 border-emerald-500/40',
  };
  if (!level) return null;
  return <span className={`px-2 py-0.5 text-xs rounded-full border ${map[level] || 'bg-slate-500/20 text-slate-400 border-slate-500/40'}`}>{level}</span>;
}

function FMBar({ score }) {
  if (!score && score !== 0) return null;
  const pct = Math.round(score * 100);
  const color = pct >= 60 ? '#F16667' : pct >= 30 ? '#FFD86E' : '#68BC00';
  return (
    <div className="flex items-center gap-2 mt-1">
      <Cloud size={11} className="text-orange-400 shrink-0" />
      <div className="flex-1 bg-slate-700 rounded-full h-1.5">
        <div className="h-1.5 rounded-full transition-all" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="text-xs shrink-0" style={{ color }}>{pct}%</span>
    </div>
  );
}

// #5 PENDING: Action buttons on result cards (View Graph, Redline, Negotiate)
function ContractCard({ contract, onClick, onViewGraph, onRedline, onNegotiate, onBuildGraph }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-800/50 hover:border-cyan-500/30 transition-all duration-200">
      <div
        className="p-4 cursor-pointer"
        onClick={() => onClick && onClick(contract.id)}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <FileText size={14} className="text-cyan-400 shrink-0" />
              <span className="text-white text-sm font-medium truncate">{contract.title}</span>
            </div>
            <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-slate-400">
              {contract.contractType && <span>{contract.contractType}</span>}
              {contract.jurisdiction && <span>· {contract.jurisdiction}</span>}
              {contract.clauseCount !== undefined && <span>· {contract.clauseCount} clauses</span>}
              {contract.uploadedAt && <span>· {new Date(contract.uploadedAt).toLocaleDateString()}</span>}
            </div>
            {/* #3 PENDING: FM Risk bar */}
            {contract.forceMajeureScore > 0 && <FMBar score={contract.forceMajeureScore} />}
            {contract.matchingClauses?.length > 0 && (
              <div className="mt-2 space-y-1">
                {contract.matchingClauses.map((cl, i) => (
                  <div key={i} className="text-xs text-slate-500 bg-slate-900/50 rounded p-1.5 border border-slate-700/30">
                    <span className="text-cyan-500">{cl.type}:</span> {cl.snippet}
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="flex flex-col gap-1 items-end shrink-0">
            <RiskBadge level={contract.riskLevel} />
            {contract.liabilityLevel && <span className="text-xs text-slate-500">{contract.liabilityLevel} liability</span>}
            {contract.contractValue && <span className="text-xs text-emerald-400">{String(contract.contractValue).replace(/^\$+/, '$')}</span>}
            {contract.hasAnalysis && <span className="text-xs text-blue-400 flex items-center gap-1"><CheckCircle size={10} /> Analyzed</span>}
          </div>
        </div>
      </div>

      {/* #5 PENDING: Action buttons */}
      <div className="border-t border-slate-700/40 px-4 py-2 flex gap-2 flex-wrap">
        <button
          onClick={e => { e.stopPropagation(); onViewGraph && onViewGraph(contract.id); }}
          className="flex items-center gap-1 px-2 py-1 text-xs bg-violet-500/10 text-violet-400 border border-violet-500/30 rounded-lg hover:bg-violet-500/20 transition"
        >
          <Network size={11} /> Graph
        </button>
        <button
          onClick={e => { e.stopPropagation(); onRedline && onRedline(contract); }}
          className="flex items-center gap-1 px-2 py-1 text-xs bg-blue-500/10 text-blue-400 border border-blue-500/30 rounded-lg hover:bg-blue-500/20 transition"
        >
          <GitCompare size={11} /> Redline
        </button>
        <button
          onClick={e => { e.stopPropagation(); onNegotiate && onNegotiate(contract); }}
          className="flex items-center gap-1 px-2 py-1 text-xs bg-orange-500/10 text-orange-400 border border-orange-500/30 rounded-lg hover:bg-orange-500/20 transition"
        >
          <Users size={11} /> Negotiate
        </button>
        <button
          onClick={e => { e.stopPropagation(); onBuildGraph && onBuildGraph(contract.id); }}
          className="flex items-center gap-1 px-2 py-1 text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded-lg hover:bg-emerald-500/20 transition"
        >
          <Database size={11} /> Build Graph
        </button>
      </div>
    </div>
  );
}

// #6 PENDING: Word-style redline diff viewer
function RedlineDiffViewer({ original, redlined, onClose }) {
  if (!original || !redlined) return null;

  // Simple word-level diff
  const diffWords = (orig, redr) => {
    const origWords = orig.split(/(\s+)/);
    const redrWords = redr.split(/(\s+)/);
    const result = [];
    const maxLen = Math.max(origWords.length, redrWords.length);
    for (let i = 0; i < maxLen; i++) {
      const o = origWords[i];
      const r = redrWords[i];
      if (o === r) {
        result.push({ type: 'same', value: o || r });
      } else if (!o) {
        result.push({ type: 'added', value: r });
      } else if (!r) {
        result.push({ type: 'removed', value: o });
      } else {
        result.push({ type: 'removed', value: o });
        result.push({ type: 'added', value: r });
      }
    }
    return result;
  };

  const diff = diffWords(original, redlined);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <h3 className="text-white font-semibold flex items-center gap-2">
            <GitCompare size={18} className="text-blue-400" /> Word-style Redline Diff
          </h3>
          <div className="flex gap-4 text-xs mr-4">
            <span className="text-red-400 line-through">Removed</span>
            <span className="text-emerald-400 underline">Added</span>
            <span className="text-slate-300">Unchanged</span>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-xl leading-none">&times;</button>
        </div>
        <div className="overflow-auto p-5 leading-relaxed text-sm flex-1">
          {diff.map((part, i) => {
            if (part.type === 'added') return (
              <span key={i} className="text-emerald-400 underline bg-emerald-500/10 px-0.5 rounded">{part.value}</span>
            );
            if (part.type === 'removed') return (
              <span key={i} className="text-red-400 line-through bg-red-500/10 px-0.5 rounded">{part.value}</span>
            );
            return <span key={i} className="text-slate-300">{part.value}</span>;
          })}
        </div>
      </div>
    </div>
  );
}

function LoadingSpinner({ text = 'Loading...' }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3">
      <div className="w-10 h-10 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
      <span className="text-slate-400 text-sm">{text}</span>
    </div>
  );
}

// ─── Tab 1: Pre-built Searches ────────────────────────────────
function PrebuiltTab({ navigate, onRedline, onNegotiate, onBuildGraph }) {
  const [searches, setSearches] = useState([]);
  const [active, setActive] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingSearches, setLoadingSearches] = useState(true);

  useEffect(() => {
    getPrebuiltSearches().then(d => setSearches(d.searches || [])).catch(() => {}).finally(() => setLoadingSearches(false));
  }, []);

  const run = async (s) => {
    setActive(s.id); setLoading(true); setResults(null);
    try { setResults(await runPrebuiltSearch(s.id, 20)); }
    catch (e) { setResults({ error: e.response?.data?.error || 'Search failed' }); }
    finally { setLoading(false); }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-white mb-1">Pre-built Search Templates</h2>
        <p className="text-slate-400 text-sm">Click any template to instantly find matching contracts</p>
      </div>
      {loadingSearches ? <LoadingSpinner text="Loading templates..." /> : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {searches.map(s => {
            const Icon = ICON_MAP[s.icon] || Search;
            return (
              <button key={s.id} onClick={() => run(s)}
                className={`rounded-xl border p-4 text-left transition-all duration-200 ${COLOR_CLASS[s.color] || COLOR_CLASS.slate} ${active === s.id ? 'ring-2 ring-cyan-500/50' : ''}`}>
                <div className="flex items-center gap-2 mb-2"><Icon size={18} /><span className="font-semibold text-sm">{s.label}</span></div>
                <p className="text-xs opacity-70">{s.description}</p>
              </button>
            );
          })}
        </div>
      )}
      {loading && <LoadingSpinner text="Running search..." />}
      {results && !loading && (
        results.error
          ? <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl p-4">{results.error}</div>
          : <>
            <div className="flex items-center gap-2 mb-3">
              <Sparkles size={16} className="text-cyan-400" />
              <span className="text-white font-semibold">{results.label}</span>
              <span className="text-slate-400 text-sm">({results.count})</span>
            </div>
            {results.contracts?.length === 0
              ? <div className="text-center py-10 text-slate-400">No contracts match this criteria</div>
              : <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                  {results.contracts.map(c => (
                    <ContractCard key={c.id} contract={c}
                      onClick={id => navigate(`/contract/${id}/clauses`)}
                      onViewGraph={id => navigate(`/contract-graph?contract=${id}`)}
                      onRedline={onRedline}
                      onNegotiate={onNegotiate}
                      onBuildGraph={onBuildGraph}
                    />
                  ))}
                </div>
            }
          </>
      )}
    </div>
  );
}

// ─── Tab 2: Semantic Search ───────────────────────────────────
function SemanticTab({ navigate, onRedline, onNegotiate, onBuildGraph }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({ contractType: '', jurisdiction: '', riskLevel: '', liabilityLevel: '' });

  const search = async () => {
    if (!query.trim()) return;
    setLoading(true); setResults(null);
    try { setResults(await semanticSearch(query, filters, 20)); }
    catch (e) { setResults({ error: e.response?.data?.error || 'Search failed' }); }
    finally { setLoading(false); }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-white mb-1">Smart Semantic Search</h2>
        <p className="text-slate-400 text-sm">AI-powered semantic search — finds contracts by meaning, not just keywords</p>
      </div>
      <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4 space-y-3">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && search()}
              placeholder="e.g. force majeure, unlimited liability, payment default..."
              className="w-full pl-10 pr-4 py-3 bg-slate-900/60 border border-slate-600 text-white placeholder-slate-500 rounded-lg focus:outline-none focus:border-cyan-500 text-sm" />
          </div>
          <button onClick={() => setShowFilters(v => !v)} className="px-4 py-3 bg-slate-700 text-slate-300 rounded-lg hover:bg-slate-600 transition flex items-center gap-2 text-sm">
            <Filter size={16} /> Filters
          </button>
          <button onClick={search} disabled={loading || !query.trim()}
            className="px-6 py-3 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 disabled:bg-slate-600 disabled:cursor-not-allowed transition text-sm font-medium">
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
        {showFilters && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 pt-3 border-t border-slate-700/50">
            {[{ label: 'Contract Type', key: 'contractType', placeholder: 'e.g. NDA, MSA' },
              { label: 'Jurisdiction',  key: 'jurisdiction',  placeholder: 'e.g. Dubai, USA' }].map(f => (
              <div key={f.key}>
                <label className="text-xs text-slate-400 mb-1 block">{f.label}</label>
                <input value={filters[f.key]} onChange={e => setFilters(p => ({ ...p, [f.key]: e.target.value }))}
                  placeholder={f.placeholder}
                  className="w-full px-3 py-2 bg-slate-900/60 border border-slate-600 text-white placeholder-slate-500 rounded-lg text-sm focus:outline-none focus:border-cyan-500" />
              </div>
            ))}
            {[{ label: 'Risk Level', key: 'riskLevel', opts: ['', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'] },
              { label: 'Liability',  key: 'liabilityLevel', opts: ['', 'LOW', 'MEDIUM', 'HIGH'] }].map(f => (
              <div key={f.key}>
                <label className="text-xs text-slate-400 mb-1 block">{f.label}</label>
                <select value={filters[f.key]} onChange={e => setFilters(p => ({ ...p, [f.key]: e.target.value }))}
                  className="w-full px-3 py-2 bg-slate-900/60 border border-slate-600 text-white rounded-lg text-sm focus:outline-none focus:border-cyan-500">
                  {f.opts.map(o => <option key={o} value={o}>{o || 'All'}</option>)}
                </select>
              </div>
            ))}
          </div>
        )}
      </div>
      {loading && <LoadingSpinner text="Searching..." />}
      {results && !loading && (
        results.error
          ? <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl p-4">{results.error}</div>
          : <>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-white font-semibold">{results.count} results</span>
              <span className="text-slate-500 text-sm">for "{results.query}"</span>
              <span className="ml-auto text-xs text-slate-500 bg-slate-800 border border-slate-700 px-2 py-0.5 rounded-full">{results.method}</span>
            </div>
            {results.contracts?.length === 0
              ? <div className="text-center py-10 text-slate-400">No contracts found</div>
              : <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                  {results.contracts.map(c => (
                    <ContractCard key={c.id} contract={c}
                      onClick={id => navigate(`/contract/${id}/clauses`)}
                      onViewGraph={id => navigate(`/contract-graph?contract=${id}`)}
                      onRedline={onRedline} onNegotiate={onNegotiate} onBuildGraph={onBuildGraph}
                    />
                  ))}
                </div>
            }
          </>
      )}
    </div>
  );
}

// ─── Tab 3: AI Agent ──────────────────────────────────────────
const MULTIHOP_TYPES = [
  { id: 'high_risk', label: 'High Risk Contracts', desc: 'Shows ALL high-risk contracts (not just one)' },
  { id: 'cascading_fm', label: 'Cascading FM Risk', desc: 'Shows how Force Majeure connects ACROSS multiple contracts' },
  { id: 'connected_risks', label: 'Connected Risks', desc: 'Shows risk connections between DIFFERENT contracts' },
  { id: 'obligations', label: 'Obligation Network', desc: 'Shows obligations across ALL contracts' },
  { id: 'all_nodes', label: 'All Graph Nodes', desc: 'Shows EVERY contract in the system' },
];

function AgentTab({ navigate, onRedline, onNegotiate, onBuildGraph }) {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [multiHopResult, setMultiHopResult] = useState(null);
  const [multiHopLoading, setMultiHopLoading] = useState(null);
  const [useLangChain, setUseLangChain] = useState(false);

  const EXAMPLES = [
    'Which contracts have cascading force majeure risk?',
    'Show me all high liability contracts in Dubai',
    'Find contracts with payment default clauses',
    'Which contracts have unlimited liability exposure?',
    "Show contracts that haven't been analyzed yet",
  ];

  const runMultiHop = async (queryType) => {
    setMultiHopLoading(queryType); setMultiHopResult(null);
    try { setMultiHopResult(await graphMultiHop(queryType, null)); }
    catch (e) { setMultiHopResult({ error: e.response?.data?.error || 'Multi-hop query failed' }); }
    finally { setMultiHopLoading(null); }
  };

  const ask = async (q) => {
    const text = q || query;
    if (!text.trim()) return;
    if (q) setQuery(q);
    setLoading(true); setResult(null);
    try {
      if (useLangChain) {
        setResult(await langchainAgentSearch(text));
      } else {
        setResult(await aiAgentSearch(text));
      }
    }
    catch (e) { setResult({ error: e.response?.data?.error || 'Agent failed' }); }
    finally { setLoading(false); }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white mb-1">AI Agent Search</h2>
          <p className="text-slate-400 text-sm">Ask anything — agent analyzes your contracts to provide intelligent answers</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Standard</span>
          <button
            onClick={() => setUseLangChain(!useLangChain)}
            className={`relative w-11 h-6 rounded-full transition-colors ${useLangChain ? 'bg-violet-600' : 'bg-slate-600'}`}
          >
            <div className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform ${useLangChain ? 'translate-x-5' : 'translate-x-0'}`} />
          </button>
          <span className="text-xs text-violet-400">Advanced AI</span>
        </div>
      </div>
      <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4 space-y-3">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Brain size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-violet-400" />
            <input value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && ask()}
              placeholder="Ask anything about your contracts..."
              className="w-full pl-10 pr-4 py-3 bg-slate-900/60 border border-slate-600 text-white placeholder-slate-500 rounded-lg focus:outline-none focus:border-violet-500 text-sm" />
          </div>
          <button onClick={() => ask()} disabled={loading || !query.trim()}
            className="px-6 py-3 bg-violet-600 text-white rounded-lg hover:bg-violet-700 disabled:bg-slate-600 disabled:cursor-not-allowed transition text-sm font-medium flex items-center gap-2">
            {loading ? <RefreshCw size={16} className="animate-spin" /> : <Zap size={16} />}
            {loading ? 'Thinking...' : 'Ask AI'}
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {EXAMPLES.map((q, i) => (
            <button key={i} onClick={() => ask(q)}
              className="text-xs px-3 py-1.5 bg-slate-700/50 text-slate-400 border border-slate-600/50 rounded-full hover:border-violet-500/50 hover:text-violet-400 transition">
              {q}
            </button>
          ))}
        </div>
      </div>
      {loading && <LoadingSpinner text="AI Agent is thinking..." />}
      {result && !loading && (
        result.error
          ? <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl p-4">{result.error}</div>
          : <>
            <div className="bg-violet-500/10 border border-violet-500/30 rounded-xl p-5">
              <div className="flex items-center gap-2 mb-3">
                <Brain size={18} className="text-violet-400" />
                <span className="text-violet-300 font-semibold">AI Agent Answer</span>
                <div className="ml-auto flex gap-1 flex-wrap">
                  {result.tools_used?.map(t => (
                    <span key={t} className="text-xs bg-violet-900/40 text-violet-400 border border-violet-500/30 px-2 py-0.5 rounded-full">{t}</span>
                  ))}
                </div>
              </div>
              <p className="text-white text-sm leading-relaxed">{result.answer}</p>
            </div>
            {result.portfolio_stats && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <StatCard label="Total Contracts" value={result.portfolio_stats.total} color="cyan" />
                <StatCard label="High Risk" value={result.portfolio_stats.high_risk} color="red" />
                <StatCard label="Force Majeure" value={result.portfolio_stats.force_majeure} color="orange" />
                <StatCard label="High Liability" value={result.portfolio_stats.high_liability} color="yellow" />
              </div>
            )}
            {result.contracts?.length > 0 && (
              <>
                <h3 className="text-white font-semibold flex items-center gap-2"><Target size={16} className="text-cyan-400" /> Relevant Contracts</h3>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                  {result.contracts.map(c => (
                    <ContractCard key={c.id} contract={c}
                      onClick={id => navigate(`/contract/${id}/clauses`)}
                      onViewGraph={id => navigate(`/contract-graph?contract=${id}`)}
                      onRedline={onRedline} onNegotiate={onNegotiate} onBuildGraph={onBuildGraph}
                    />
                  ))}
                </div>
              </>
            )}
          </>
      )}

      {/* Multi-hop Neo4j Graph Queries */}
      <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5 space-y-4">
        <div className="flex items-center gap-2 mb-1">
          <Network size={16} className="text-cyan-400" />
          <h3 className="text-white font-semibold text-sm">Multi-hop Neo4j Graph Queries</h3>
        </div>

        {/* Explanation Banner */}
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3">
          <div className="flex items-start gap-2">
            <div className="text-blue-400 text-lg">ℹ️</div>
            <div className="text-xs text-blue-200 leading-relaxed">
              <strong className="text-blue-300">What are Multi-hop Queries?</strong>
              <div className="mt-1 text-blue-100/80">
                These queries <strong>traverse across MULTIPLE contracts</strong> in the knowledge graph to find related clauses, risks, and obligations.
                If you select a contract, it will show how that contract connects to OTHER contracts through shared risks or obligations.
              </div>
              <div className="mt-2 flex gap-3 text-[10px]">
                <span>• <strong>Without contract:</strong> Shows ALL relationships</span>
                <span>• <strong>With contract:</strong> Shows connections FROM that contract</span>
              </div>
            </div>
          </div>
        </div>

        <p className="text-slate-500 text-xs">Execute deep graph traversal queries across all your contracts in the knowledge graph</p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
          {MULTIHOP_TYPES.map(t => (
            <button key={t.id} onClick={() => runMultiHop(t.id)} disabled={!!multiHopLoading}
              className="p-3 text-left bg-slate-900/50 border border-slate-700/50 rounded-lg hover:border-cyan-500/40 hover:bg-slate-900/80 transition disabled:opacity-50">
              <div className="flex items-center gap-2 mb-1">
                {multiHopLoading === t.id
                  ? <RefreshCw size={13} className="animate-spin text-cyan-400" />
                  : <Activity size={13} className="text-cyan-400" />
                }
                <span className="text-white text-xs font-medium">{t.label}</span>
              </div>
              <p className="text-slate-500 text-xs">{t.desc}</p>
            </button>
          ))}
        </div>
        {multiHopResult && (
          multiHopResult.error
            ? <div className="text-red-400 text-xs p-3 bg-red-500/10 border border-red-500/20 rounded-lg">{multiHopResult.error}</div>
            : <div className="bg-slate-900/50 border border-slate-700/30 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-cyan-400 text-sm font-semibold capitalize">{(multiHopResult.query_type || '').replace(/_/g,' ')}</span>
                  {multiHopResult.nodes?.length > 0 && <span className="text-slate-500 text-xs">{multiHopResult.nodes.length} nodes · {multiHopResult.links?.length || 0} edges</span>}
                </div>

                {/* Query Result Explanation */}
                <div className="mb-3 p-2.5 bg-cyan-500/5 border border-cyan-500/20 rounded-lg">
                  <div className="text-[11px] text-cyan-200">
                    {multiHopResult.query_type === 'cascading_fm' && (
                      <>
                        <strong>📊 What you're seeing:</strong> Force Majeure clauses that cascade across contracts through shared obligations or jurisdiction risks.
                      </>
                    )}
                    {multiHopResult.query_type === 'high_risk' && (
                      <>
                        <strong>📊 What you're seeing:</strong> All your contracts rated HIGH or CRITICAL risk ({multiHopResult.nodes?.filter(n => n.type === 'Contract').length || 0} contracts) and their associated risk clauses.
                      </>
                    )}
                    {multiHopResult.query_type === 'obligation_network' && (
                      <>
                        <strong>📊 What you're seeing:</strong> All obligation relationships across contracts showing how legal duties connect.
                        {multiHopResult.nodes?.length > 20 && (
                          <div className="mt-2 p-2 bg-yellow-500/10 border border-yellow-500/30 rounded text-yellow-200">
                            ⚠️ <strong>Too many nodes ({multiHopResult.nodes.length})!</strong> Select a specific contract above to see a simpler view.
                          </div>
                        )}
                      </>
                    )}
                    {multiHopResult.query_type === 'connected_risks' && (
                      <>
                        <strong>📊 What you're seeing:</strong> Risk nodes that are connected across multiple contracts through shared clause patterns.
                      </>
                    )}
                    {multiHopResult.query_type === 'all_nodes' && (
                      <>
                        <strong>📊 What you're seeing:</strong> Complete graph topology showing ALL contracts, clauses, risks, and obligations.
                        <div className="mt-2 p-2 bg-yellow-500/10 border border-yellow-500/30 rounded text-yellow-200">
                          ⚠️ <strong>This shows EVERYTHING ({multiHopResult.nodes.length} nodes)!</strong> Very complex. Consider using filtered queries instead.
                        </div>
                      </>
                    )}
                  </div>
                </div>
                {/* Simple Summary */}
                {multiHopResult.nodes?.length > 0 && (
                  <div className="mb-3 p-3 bg-slate-800/60 rounded-lg border border-slate-600/30">
                    <div className="text-xs font-semibold text-white mb-2">📋 Simple Summary:</div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="p-2 bg-blue-500/10 rounded border border-blue-500/20">
                        <div className="text-blue-400 font-semibold">{multiHopResult.nodes?.filter(n => n.type === 'Contract').length || 0}</div>
                        <div className="text-slate-400">Contracts</div>
                      </div>
                      <div className="p-2 bg-purple-500/10 rounded border border-purple-500/20">
                        <div className="text-purple-400 font-semibold">{multiHopResult.nodes?.filter(n => n.type === 'Clause').length || 0}</div>
                        <div className="text-slate-400">Clauses</div>
                      </div>
                      <div className="p-2 bg-orange-500/10 rounded border border-orange-500/20">
                        <div className="text-orange-400 font-semibold">{multiHopResult.nodes?.filter(n => n.type === 'Obligation').length || 0}</div>
                        <div className="text-slate-400">Obligations</div>
                      </div>
                      <div className="p-2 bg-red-500/10 rounded border border-red-500/20">
                        <div className="text-red-400 font-semibold">{multiHopResult.nodes?.filter(n => n.type === 'Risk').length || 0}</div>
                        <div className="text-slate-400">Risks</div>
                      </div>
                    </div>
                    <div className="mt-2 text-[10px] text-slate-500 italic">
                      💡 Tip: The graph below shows how these connect. Orange hexagons = Obligations, Purple circles = Clauses
                    </div>
                  </div>
                )}

                {/* Graph Visualization */}
                {multiHopResult.nodes?.length > 0 && multiHopResult.links ? (
                  <div className="mb-3">
                    <Neo4jGraphViz
                      graphData={{ nodes: multiHopResult.nodes, links: multiHopResult.links }}
                      height={multiHopResult.nodes.length > 20 ? "600px" : "400px"}
                      onNodeClick={(node) => console.log('Clicked node:', node)}
                    />
                  </div>
                ) : (
                  <div className="text-slate-500 text-sm text-center py-8">No graph data available</div>
                )}
                {/* Cypher Query */}
                {multiHopResult.cypher_used && (
                  <div className="mt-3 p-2 bg-slate-800/60 rounded text-xs text-slate-500 font-mono break-all">
                    <span className="text-slate-400">Cypher:</span> {multiHopResult.cypher_used}
                  </div>
                )}
              </div>
        )}
      </div>
    </div>
  );
}

// ─── Tab 4: Analytics ─────────────────────────────────────────
// ─── Analytics helpers ─────────────────────────────────────────
const CHART_TOOLTIP = { contentStyle: { background: '#0f172a', border: '1px solid #334155', borderRadius: 10, fontSize: 12 }, cursor: { fill: '#ffffff08' } };
const GRID_STYLE   = { stroke: '#1e293b', strokeDasharray: '3 3' };
const TICK_STYLE   = { fill: '#64748b', fontSize: 11 };

const RISK_GRADIENT = { HIGH: '#ef4444', CRITICAL: '#dc2626', MEDIUM: '#f59e0b', LOW: '#22c55e', NOT_ANALYZED: '#475569' };
const TYPE_COLORS = ['#06b6d4','#8b5cf6','#f97316','#22c55e','#f43f5e','#eab308','#3b82f6','#a855f7','#10b981','#fb923c'];

function AnalyticsKPI({ label, value, sub, color, icon: Icon, trend }) {
  const colorMap = {
    cyan: 'from-cyan-500/20 to-cyan-600/5 border-cyan-500/30 text-cyan-400',
    emerald: 'from-emerald-500/20 to-emerald-600/5 border-emerald-500/30 text-emerald-400',
    red: 'from-red-500/20 to-red-600/5 border-red-500/30 text-red-400',
    orange: 'from-orange-500/20 to-orange-600/5 border-orange-500/30 text-orange-400',
    violet: 'from-violet-500/20 to-violet-600/5 border-violet-500/30 text-violet-400',
    blue: 'from-blue-500/20 to-blue-600/5 border-blue-500/30 text-blue-400',
  };
  const cls = colorMap[color] || colorMap.cyan;
  return (
    <div className={`relative overflow-hidden bg-gradient-to-br ${cls} border rounded-xl p-4`}>
      <div className="flex items-start justify-between">
        <div>
          <div className="text-slate-400 text-xs font-medium uppercase tracking-wider mb-1">{label}</div>
          <div className={`text-3xl font-black ${cls.split(' ').find(c => c.startsWith('text-'))}`}>{value}</div>
          {sub && <div className="text-slate-500 text-xs mt-1">{sub}</div>}
        </div>
        {Icon && <div className={`p-2 rounded-lg bg-black/20`}><Icon size={20} className={cls.split(' ').find(c => c.startsWith('text-'))} /></div>}
      </div>
      {trend !== undefined && (
        <div className={`flex items-center gap-1 mt-2 text-xs font-medium ${trend >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
          <TrendingUp size={11} className={trend < 0 ? 'rotate-180' : ''} />
          {Math.abs(trend)}% vs last month
        </div>
      )}
    </div>
  );
}

function ChartCard({ title, icon: Icon, iconColor = 'text-cyan-400', children, className = '' }) {
  return (
    <div className={`bg-slate-900/80 border border-slate-700/50 rounded-2xl p-5 ${className}`} style={{ backdropFilter: 'blur(12px)' }}>
      <div className="flex items-center gap-2 mb-4">
        {Icon && <div className="p-1.5 rounded-lg bg-slate-800/80"><Icon size={15} className={iconColor} /></div>}
        <h3 className="text-white font-semibold text-sm">{title}</h3>
      </div>
      {children}
    </div>
  );
}

function AnalyticsTab({ navigate }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeSection, setActiveSection] = useState('overview');

  useEffect(() => {
    getSearchAnalytics().then(setData).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner text="Loading analytics..." />;
  if (!data) return <div className="text-slate-400 text-center py-10">Failed to load analytics</div>;

  const s = data.summary || {};
  const riskPie = Object.entries(data.risk_breakdown || {}).filter(([, v]) => v > 0).map(([k, v]) => ({ name: k, value: v, fill: RISK_GRADIENT[k] || '#475569' }));
  const liabilityPie = (data.liability_distribution || []).filter(d => d.value > 0);
  const typeDist = data.type_distribution || [];
  const clauseTypes = data.clause_type_breakdown || [];
  const confData = data.confidence_per_contract || [];
  const riskTrend = data.risk_trend || [];
  const clausePerContract = data.clause_per_contract || [];
  const fmContracts = data.force_majeure_contracts || [];
  const highValue = data.high_value_contracts || [];

  const sections = [
    { id: 'overview', label: 'Overview' },
    { id: 'risk',     label: 'Risk Intelligence' },
    { id: 'clauses',  label: 'Clause Analytics' },
    { id: 'financial',label: 'Financial' },
    { id: 'advanced', label: 'Advanced' },
  ];

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-xl font-bold text-white">Portfolio Analytics</h2>
          <p className="text-slate-400 text-sm mt-0.5">Live intelligence across {s.total_contracts || 0} contracts · {s.total_clauses || 0} clauses</p>
        </div>
        <div className="flex gap-1 bg-slate-800/60 border border-slate-700/40 rounded-xl p-1">
          {sections.map(sec => (
            <button key={sec.id} onClick={() => setActiveSection(sec.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${activeSection === sec.id ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' : 'text-slate-400 hover:text-white'}`}>
              {sec.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── OVERVIEW ── */}
      {activeSection === 'overview' && (
        <div className="space-y-5">
          {/* KPI Row */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <AnalyticsKPI label="Contracts" value={s.total_contracts || 0} color="cyan" icon={FileText} sub="in portfolio" />
            <AnalyticsKPI label="Analyzed" value={s.analyzed_contracts || 0} color="emerald" icon={CheckCircle} sub={`${s.total_contracts ? Math.round((s.analyzed_contracts/s.total_contracts)*100) : 0}% coverage`} />
            <AnalyticsKPI label="High Risk" value={s.high_risk_contracts || 0} color="red" icon={AlertTriangle} sub="need attention" />
            <AnalyticsKPI label="Total Clauses" value={s.total_clauses || 0} color="blue" icon={FileText} sub={`~${s.avg_clauses_per_contract || 0}/contract`} />
            <AnalyticsKPI label="High Liability" value={s.high_liability_count || 0} color="orange" icon={Shield} sub="exposure risk" />
            <AnalyticsKPI label="FM Contracts" value={s.fm_contracts || 0} color="violet" icon={Cloud} sub="force majeure" />
          </div>

          {/* Risk + Type row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
            {/* Risk donut */}
            <ChartCard title="Risk Distribution" icon={Shield} iconColor="text-red-400">
              {riskPie.length > 0 ? (
                <div className="flex items-center gap-3">
                  <ResponsiveContainer width={140} height={140}>
                    <PieChart>
                      <Pie data={riskPie} dataKey="value" cx="50%" cy="50%" innerRadius={38} outerRadius={62} paddingAngle={3}>
                        {riskPie.map((e, i) => <Cell key={i} fill={e.fill} />)}
                      </Pie>
                      <Tooltip {...CHART_TOOLTIP} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="space-y-1.5 flex-1">
                    {riskPie.map((e, i) => (
                      <div key={i} className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-1.5">
                          <div className="w-2.5 h-2.5 rounded-full" style={{ background: e.fill }} />
                          <span className="text-slate-400">{e.name}</span>
                        </div>
                        <span className="font-bold text-white">{e.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : <div className="text-slate-500 text-xs text-center py-10">No risk data</div>}
            </ChartCard>

            {/* Contract type donut */}
            <ChartCard title="Contract Types" icon={FileText} iconColor="text-cyan-400">
              {typeDist.length > 0 ? (
                <div className="flex items-center gap-3">
                  <ResponsiveContainer width={140} height={140}>
                    <PieChart>
                      <Pie data={typeDist.map((d,i) => ({...d, name: d.type, value: d.count, fill: TYPE_COLORS[i % TYPE_COLORS.length]}))} dataKey="value" cx="50%" cy="50%" innerRadius={38} outerRadius={62} paddingAngle={3}>
                        {typeDist.map((_, i) => <Cell key={i} fill={TYPE_COLORS[i % TYPE_COLORS.length]} />)}
                      </Pie>
                      <Tooltip {...CHART_TOOLTIP} formatter={(v, n) => [v, n]} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="space-y-1.5 flex-1 overflow-hidden">
                    {typeDist.slice(0, 5).map((d, i) => (
                      <div key={i} className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-1.5 min-w-0">
                          <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: TYPE_COLORS[i % TYPE_COLORS.length] }} />
                          <span className="text-slate-400 truncate">{d.type}</span>
                        </div>
                        <span className="font-bold text-white shrink-0 ml-1">{d.count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : <div className="text-slate-500 text-xs text-center py-10">No type data</div>}
            </ChartCard>

            {/* Liability pie */}
            <ChartCard title="Liability Exposure" icon={AlertTriangle} iconColor="text-orange-400">
              {liabilityPie.length > 0 ? (
                <div className="flex flex-col items-center">
                  <ResponsiveContainer width="100%" height={120}>
                    <PieChart>
                      <Pie data={liabilityPie} dataKey="value" cx="50%" cy="50%" outerRadius={52} paddingAngle={3}
                        label={({ name, value }) => `${name}:${value}`} labelLine={false}>
                        {liabilityPie.map((_, i) => <Cell key={i} fill={['#ef4444','#f59e0b','#22c55e','#64748b'][i % 4]} />)}
                      </Pie>
                      <Tooltip {...CHART_TOOLTIP} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="flex flex-wrap gap-2 justify-center mt-2">
                    {liabilityPie.map((d, i) => (
                      <div key={i} className="flex items-center gap-1 text-xs">
                        <div className="w-2 h-2 rounded-full" style={{ background: ['#ef4444','#f59e0b','#22c55e','#64748b'][i % 4] }} />
                        <span className="text-slate-400">{d.name} <span className="text-white font-bold">{d.value}</span></span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : <div className="text-slate-500 text-xs text-center py-10">No liability data</div>}
            </ChartCard>
          </div>

          {/* Contract-level table */}
          <ChartCard title="Contract Portfolio Overview" icon={Database} iconColor="text-blue-400">
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-slate-700/50">
                    {['Contract', 'Type', 'Clauses', 'Risk Level', 'Risk Score', 'FM Score'].map(h => (
                      <th key={h} className="text-left text-slate-400 font-semibold py-2 pr-4">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {clausePerContract.map((c, i) => {
                    const fm = fmContracts.find(f => f.title?.startsWith(c.title?.slice(0, 15)));
                    return (
                      <tr key={i} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition">
                        <td className="py-2.5 pr-4 text-white font-medium max-w-[180px] truncate">{c.title}</td>
                        <td className="py-2.5 pr-4 text-slate-400 text-xs max-w-[120px] truncate">{c.contractType || '—'}</td>
                        <td className="py-2.5 pr-4">
                          <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded-full border border-blue-500/30 font-bold">{c.clauses}</span>
                        </td>
                        <td className="py-2.5 pr-4"><RiskBadge level={c.riskLevel} /></td>
                        <td className="py-2.5 pr-4">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 bg-slate-700/50 rounded-full h-1.5 w-16">
                              <div className="h-1.5 rounded-full" style={{ width: `${Math.min(c.riskScore, 100).toFixed(0)}%`, background: RISK_GRADIENT[c.riskLevel] || '#64748b' }} />
                            </div>
                            <span className="text-slate-300">{Math.round(c.riskScore)}%</span>
                          </div>
                        </td>
                        <td className="py-2.5 text-orange-400 font-medium">{fm ? `${Math.round(fm.riskScore * 100)}%` : '—'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </ChartCard>
        </div>
      )}

      {/* ── RISK INTELLIGENCE ── */}
      {activeSection === 'risk' && (
        <div className="space-y-5">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {/* Risk score trend */}
            <ChartCard title="Risk Score Trend (by Upload Order)" icon={TrendingUp} iconColor="text-red-400">
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={riskTrend}>
                  <defs>
                    <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid {...GRID_STYLE} />
                  <XAxis dataKey="title" tick={TICK_STYLE} tickFormatter={v => v.slice(0,10)} />
                  <YAxis tick={TICK_STYLE} domain={[0, 100]} tickFormatter={v => `${v}%`} />
                  <Tooltip {...CHART_TOOLTIP} formatter={v => [`${v}%`, 'Risk Score']} />
                  <Area type="monotone" dataKey="riskScore" stroke="#ef4444" strokeWidth={2} fill="url(#riskGrad)" dot={{ fill: '#ef4444', r: 4 }} />
                </AreaChart>
              </ResponsiveContainer>
            </ChartCard>

            {/* High liability bar */}
            <ChartCard title="High Liability Contracts — Risk Scores" icon={Shield} iconColor="text-red-400">
              {data.high_liability_contracts?.length > 0 ? (
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={data.high_liability_contracts} layout="vertical">
                    <CartesianGrid {...GRID_STYLE} horizontal={false} />
                    <XAxis type="number" tick={TICK_STYLE} domain={[0, 100]} tickFormatter={v => `${v}%`} />
                    <YAxis type="category" dataKey="title" tick={TICK_STYLE} width={90} tickFormatter={v => v.slice(0,12)} />
                    <Tooltip {...CHART_TOOLTIP} formatter={v => [`${Math.round(v)}%`, 'Risk Score']} />
                    <Bar dataKey="riskScore" radius={[0,4,4,0]}>
                      {data.high_liability_contracts.map((d, i) => (
                        <Cell key={i} fill={d.riskScore >= 70 ? '#ef4444' : d.riskScore >= 40 ? '#f59e0b' : '#22c55e'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : <div className="text-slate-500 text-xs text-center py-10">No high liability contracts</div>}
            </ChartCard>
          </div>

          {/* Force Majeure scored list */}
          <ChartCard title="Force Majeure Risk Scoring — All Contracts" icon={Cloud} iconColor="text-orange-400">
            {fmContracts.length > 0 ? (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                {fmContracts.map((c, i) => {
                  const pct = Math.round((c.riskScore || 0) * 100);
                  const color = pct >= 70 ? '#ef4444' : pct >= 40 ? '#f59e0b' : '#22c55e';
                  return (
                    <div key={i} onClick={() => navigate(`/contracts/${c.id}/clauses`)}
                      className="p-3 rounded-xl bg-slate-800/50 border border-slate-700/40 hover:border-orange-500/40 cursor-pointer transition group">
                      <div className="flex items-start justify-between mb-2">
                        <span className="text-white text-xs font-semibold group-hover:text-orange-300 transition truncate max-w-[65%]">{c.title}</span>
                        <span className="text-xs font-black shrink-0 ml-2" style={{ color }}>{pct}%</span>
                      </div>
                      <div className="w-full bg-slate-700/50 rounded-full h-2 mb-2">
                        <div className="h-2 rounded-full transition-all" style={{ width: `${pct}%`, background: color, boxShadow: `0 0 8px ${color}66` }} />
                      </div>
                      {c.clauseSnippet && <p className="text-slate-500 text-xs truncate">{c.clauseSnippet}</p>}
                    </div>
                  );
                })}
              </div>
            ) : <div className="text-slate-500 text-xs text-center py-8">No force majeure clauses found</div>}
          </ChartCard>
        </div>
      )}

      {/* ── CLAUSE ANALYTICS ── */}
      {activeSection === 'clauses' && (
        <div className="space-y-5">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {/* Clause count per contract */}
            <ChartCard title="Clauses Extracted per Contract" icon={FileText} iconColor="text-cyan-400">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={clausePerContract}>
                  <CartesianGrid {...GRID_STYLE} />
                  <XAxis dataKey="title" tick={TICK_STYLE} tickFormatter={v => v.slice(0,10)} />
                  <YAxis tick={TICK_STYLE} allowDecimals={false} />
                  <Tooltip {...CHART_TOOLTIP} formatter={v => [v, 'Clauses']} />
                  <Bar dataKey="clauses" radius={[4,4,0,0]}>
                    {clausePerContract.map((d, i) => (
                      <Cell key={i} fill={RISK_GRADIENT[d.riskLevel] || '#06b6d4'} fillOpacity={0.85} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <div className="flex gap-3 mt-2 text-xs text-slate-500 flex-wrap">
                {Object.entries(RISK_GRADIENT).map(([k, v]) => (
                  <div key={k} className="flex items-center gap-1"><div className="w-2 h-2 rounded-full" style={{ background: v }} />{k}</div>
                ))}
              </div>
            </ChartCard>

            {/* Clause types breakdown */}
            <ChartCard title="Clause Type Breakdown" icon={Scale} iconColor="text-violet-400">
              {clauseTypes.length > 0 ? (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={clauseTypes} layout="vertical">
                    <CartesianGrid {...GRID_STYLE} horizontal={false} />
                    <XAxis type="number" tick={TICK_STYLE} allowDecimals={false} />
                    <YAxis type="category" dataKey="name" tick={TICK_STYLE} width={110} tickFormatter={v => v.slice(0,15)} />
                    <Tooltip {...CHART_TOOLTIP} formatter={v => [v, 'Count']} />
                    <Bar dataKey="value" radius={[0,4,4,0]}>
                      {clauseTypes.map((_, i) => <Cell key={i} fill={TYPE_COLORS[i % TYPE_COLORS.length]} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : <div className="text-slate-500 text-xs text-center py-10">No clause type data</div>}
            </ChartCard>
          </div>

          {/* AI Confidence per contract */}
          <ChartCard title="AI Extraction Confidence per Contract" icon={Brain} iconColor="text-emerald-400">
            {confData.length > 0 ? (
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={confData}>
                  <CartesianGrid {...GRID_STYLE} />
                  <XAxis dataKey="title" tick={TICK_STYLE} tickFormatter={v => v.slice(0,12)} />
                  <YAxis tick={TICK_STYLE} domain={[0, 100]} tickFormatter={v => `${v}%`} />
                  <Tooltip {...CHART_TOOLTIP} formatter={v => [`${v}%`, 'Confidence']} />
                  <Bar dataKey="confidence" radius={[4,4,0,0]}>
                    {confData.map((d, i) => (
                      <Cell key={i} fill={d.confidence >= 80 ? '#22c55e' : d.confidence >= 60 ? '#f59e0b' : '#ef4444'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : <div className="text-slate-500 text-xs text-center py-8">No confidence data</div>}
          </ChartCard>
        </div>
      )}

      {/* ── FINANCIAL ── */}
      {activeSection === 'financial' && (
        <div className="space-y-5">
          <ChartCard title="Top High Value Contracts" icon={DollarSign} iconColor="text-emerald-400">
            {highValue.length > 0 ? (
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={highValue}>
                  <defs>
                    <linearGradient id="valGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#22c55e" stopOpacity={0.9} />
                      <stop offset="95%" stopColor="#16a34a" stopOpacity={0.7} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid {...GRID_STYLE} />
                  <XAxis dataKey="title" tick={TICK_STYLE} tickFormatter={v => v.slice(0,12)} />
                  <YAxis tick={TICK_STYLE} tickFormatter={v => {
                    const n = typeof v === 'string' ? parseFloat(v.replace(/[^0-9.]/g, '')) : v;
                    return isNaN(n) ? v : n >= 1000000 ? `$${(n/1000000).toFixed(1)}M` : n >= 1000 ? `$${(n/1000).toFixed(0)}k` : `$${n}`;
                  }} />
                  <Tooltip {...CHART_TOOLTIP} formatter={(v) => {
                    const n = typeof v === 'string' ? v : `$${Number(v).toLocaleString()}`;
                    return [n, 'Contract Value'];
                  }} />
                  <Bar dataKey="value" fill="url(#valGrad)" radius={[6,6,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : <div className="text-slate-500 text-xs text-center py-10">No contract value data available</div>}
          </ChartCard>

          {/* Financial table */}
          <ChartCard title="Contract Financial Summary" icon={Activity} iconColor="text-cyan-400">
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-slate-700/50">
                    {['Contract', 'Value', 'Liability Level', 'Jurisdiction', 'Risk Level'].map(h => (
                      <th key={h} className="text-left text-slate-400 font-semibold py-2 pr-4">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {highValue.map((c, i) => (
                    <tr key={i} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition">
                      <td className="py-2.5 pr-4 text-white font-medium max-w-[200px] truncate">{c.title}</td>
                      <td className="py-2.5 pr-4 text-emerald-400 font-bold">{c.valueLabel || (c.value ? `$${Number(c.value).toLocaleString()}` : '—')}</td>
                      <td className="py-2.5 pr-4"><RiskBadge level={c.liabilityLevel} /></td>
                      <td className="py-2.5 pr-4 text-slate-400">{c.jurisdiction || '—'}</td>
                      <td className="py-2.5"><RiskBadge level={clausePerContract.find(cc => cc.title?.startsWith(c.title?.slice(0,15)))?.riskLevel || 'NOT_ANALYZED'} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </ChartCard>
        </div>
      )}

      {/* ── ADVANCED ── */}
      {activeSection === 'advanced' && (
        <div className="space-y-5">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {/* Jurisdictions */}
            {data.top_jurisdictions?.length > 0 && (
              <ChartCard title="Top Jurisdictions" icon={Network} iconColor="text-blue-400">
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={data.top_jurisdictions}>
                    <CartesianGrid {...GRID_STYLE} />
                    <XAxis dataKey="jurisdiction" tick={TICK_STYLE} tickFormatter={v => v?.slice(0,10) || 'N/A'} />
                    <YAxis tick={TICK_STYLE} allowDecimals={false} />
                    <Tooltip {...CHART_TOOLTIP} formatter={v => [v, 'Contracts']} />
                    <Bar dataKey="count" fill="#3b82f6" radius={[4,4,0,0]} fillOpacity={0.85} />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>
            )}

            {/* Contract age */}
            {data.contract_age?.length > 0 && (
              <ChartCard title="Contract Age (Days in Portfolio)" icon={Clock} iconColor="text-yellow-400">
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={data.contract_age}>
                    <CartesianGrid {...GRID_STYLE} />
                    <XAxis dataKey="title" tick={TICK_STYLE} tickFormatter={v => v.slice(0,10)} />
                    <YAxis tick={TICK_STYLE} tickFormatter={v => `${v}d`} />
                    <Tooltip {...CHART_TOOLTIP} formatter={v => [`${v} days`, 'Age']} />
                    <Bar dataKey="days" radius={[4,4,0,0]}>
                      {data.contract_age.map((d, i) => (
                        <Cell key={i} fill={d.days > 30 ? '#f59e0b' : '#22c55e'} fillOpacity={0.85} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>
            )}
          </div>

          {/* Temporal & Anomaly */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <TemporalAnalysisPanel contractId={null} />
            <AnomalyDetectionPanel onContractClick={(id) => navigate(`/contracts/${id}/clauses`)} />
          </div>

          {/* CFO Metrics */}
          <CFOFinancialMetricsPanel />
        </div>
      )}
    </div>
  );
}

// ─── Tab 5: Negotiation AI (#7 #8 #9) ────────────────────────
const PERSONALITY_MODES = ['aggressive', 'balanced', 'conservative'];
const PERSONALITY_COLORS = { aggressive: 'red', balanced: 'blue', conservative: 'emerald' };
const PERSONALITY_DESC = {
  aggressive: 'Push hard for maximum protection, reject unfavorable terms',
  balanced: 'Firm but fair, seek mutual benefit',
  conservative: 'Reasonable and flexible, avoid conflict',
};

function NegotiateTab({ initialContract = null }) {
  const [clauseText, setClauseText]     = useState(initialContract ? '' : '');
  const [clauseType, setClauseType]     = useState('General');
  const [rounds, setRounds]             = useState(3);
  const [contractId, setContractId]     = useState(initialContract?.id || '');
  const [result, setResult]             = useState(null);
  const [loading, setLoading]           = useState(false);
  const [activeRound, setActiveRound]   = useState(0);
  // #9 multi-clause
  const [multiMode, setMultiMode]       = useState(false);
  const [extraClauses, setExtraClauses] = useState([]);
  // #8 memory
  const [memory, setMemory]             = useState(null);
  const [showMemory, setShowMemory]     = useState(false);
  // Personality modes
  const [buyerMode, setBuyerMode]       = useState('balanced');
  const [supplierMode, setSupplierMode] = useState('balanced');

  const TYPES = ['General','Liability','Force Majeure','Payment','Termination','Confidentiality','Indemnity','Dispute Resolution'];
  const EXAMPLE = `The Supplier shall not be liable for any delays resulting from acts beyond their reasonable control. In the event of force majeure, the Supplier shall notify the Buyer within 30 days. The Buyer shall have no right to terminate the contract during a force majeure period of up to 12 months.`;

  const loadMemory = async () => {
    try { setMemory(await getNegotiationMemory()); } catch { }
  };

  const run = async () => {
    setLoading(true); setResult(null); setActiveRound(0);
    try {
      let clauses = null;
      if (multiMode && extraClauses.length > 0) {
        clauses = [{ type: clauseType, text: clauseText }, ...extraClauses];
      }
      const data = await runNegotiationAgents(clauseText, clauseType, rounds, contractId || null, clauses, buyerMode, supplierMode);
      setResult(data);
      loadMemory();
    } catch (e) { setResult({ error: e.response?.data?.error || 'Negotiation failed' }); }
    finally { setLoading(false); }
  };

  const scoreColor = s => s >= 70 ? 'text-emerald-400' : s >= 50 ? 'text-yellow-400' : 'text-red-400';

  const addClause = () => setExtraClauses(p => [...p, { type: 'General', text: '' }]);
  const removeClause = i => setExtraClauses(p => p.filter((_, idx) => idx !== i));

  // Render multi-clause results
  const renderMulti = () => {
    if (!result?.multi_clause) return null;
    return (
      <div className="space-y-4">
        <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4">
          <h3 className="text-white font-semibold mb-3">Multi-Clause Results ({result.total_clauses} clauses)</h3>
          <div className="text-sm text-slate-400 mb-4">Overall improvement: <span className={result.overall_improvement >= 0 ? 'text-emerald-400' : 'text-red-400'}>{result.overall_improvement > 0 ? '+' : ''}{result.overall_improvement} pts</span></div>
          {result.results?.map((r, i) => (
            <div key={i} className="mb-4 p-4 bg-slate-900/50 border border-slate-700/30 rounded-xl">
              <div className="flex items-center justify-between mb-2">
                <span className="text-cyan-400 font-medium text-sm">{r.clause_type}</span>
                <span className={`text-sm font-bold ${scoreColor(r.final_analysis?.improvement || 0)}`}>
                  {r.final_analysis?.improvement >= 0 ? '+' : ''}{r.final_analysis?.improvement} pts
                </span>
              </div>
              <p className="text-slate-300 text-xs leading-relaxed bg-slate-900/50 rounded p-2 border border-slate-700/30">{r.final_clause}</p>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white mb-1">Buyer vs Supplier AI Negotiation</h2>
          <p className="text-slate-400 text-sm">AI agents debate clauses through rounds using Neo4j graph context + strategy memory</p>
        </div>
        <button onClick={() => { setShowMemory(v => !v); if (!memory) loadMemory(); }}
          className="flex items-center gap-2 px-3 py-2 bg-slate-700 text-slate-300 rounded-lg hover:bg-slate-600 transition text-sm">
          <BookOpen size={14} /> Memory {memory && `(${Object.keys(memory.stats || {}).length} types)`}
        </button>
      </div>

      {/* #8 Memory panel */}
      {showMemory && memory && (
        <div className="bg-slate-800/60 border border-emerald-500/30 rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-emerald-400 font-semibold text-sm flex items-center gap-2"><BookOpen size={14} /> Strategy Memory</h3>
            <button onClick={() => clearNegotiationMemory().then(loadMemory)} className="text-xs text-red-400 hover:text-red-300 flex items-center gap-1"><Trash2 size={12} /> Clear All</button>
          </div>
          {memory.available_types?.length === 0
            ? <p className="text-slate-500 text-sm">No memories yet. Run negotiations to build memory.</p>
            : <div className="flex flex-wrap gap-2">
                {memory.available_types?.map(t => (
                  <span key={t} className="px-2 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded-full text-xs">
                    {t} ({memory.stats?.[t] || 0})
                  </span>
                ))}
              </div>
          }
        </div>
      )}

      <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5 space-y-4">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Clause Type</label>
            <select value={clauseType} onChange={e => setClauseType(e.target.value)}
              className="w-full px-3 py-2 bg-slate-900/60 border border-slate-600 text-white rounded-lg text-sm focus:outline-none focus:border-cyan-500">
              {TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Rounds: {rounds}</label>
            <input type="range" min={1} max={5} value={rounds} onChange={e => setRounds(Number(e.target.value))} className="w-full mt-2" />
          </div>
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Contract (optional — for graph context)</label>
            <ContractSelect value={contractId} onChange={setContractId} placeholder="Select contract (optional)..." />
          </div>
          {/* #9 Multi-clause toggle */}
          <div className="flex items-end">
            <button onClick={() => setMultiMode(v => !v)}
              className={`w-full py-2 rounded-lg text-sm transition flex items-center justify-center gap-2 ${multiMode ? 'bg-violet-600 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'}`}>
              <Plus size={14} /> {multiMode ? 'Multi-clause ON' : 'Multi-clause'}
            </button>
          </div>
        </div>

        {/* Personality mode selectors */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 pt-3 border-t border-slate-700/40">
          {[
            { label: 'Buyer Personality', mode: buyerMode, setMode: setBuyerMode, side: 'Buyer' },
            { label: 'Supplier Personality', mode: supplierMode, setMode: setSupplierMode, side: 'Supplier' },
          ].map(({ label, mode, setMode, side }) => (
            <div key={side}>
              <label className="text-xs text-slate-400 mb-2 block">{label}</label>
              <div className="flex gap-1">
                {PERSONALITY_MODES.map(m => {
                  const active = mode === m;
                  const activeClass = m === 'aggressive' ? 'bg-red-600 text-white' : m === 'conservative' ? 'bg-emerald-600 text-white' : 'bg-blue-600 text-white';
                  return (
                    <button key={m} onClick={() => setMode(m)} title={PERSONALITY_DESC[m]}
                      className={`flex-1 py-1.5 rounded-lg text-xs font-medium capitalize transition ${
                        active ? activeClass : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
                      }`}>
                      {m}
                    </button>
                  );
                })}
              </div>
              {mode && <p className="text-xs text-slate-500 mt-1">{PERSONALITY_DESC[mode]}</p>}
            </div>
          ))}
        </div>

        {/* Strategy memory suggested clauses */}
        {memory?.available_types?.includes(clauseType) && memory?.suggestions?.[clauseType]?.length > 0 && (
          <div className="p-3 bg-violet-900/20 border border-violet-500/30 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <BookOpen size={13} className="text-violet-400" />
              <span className="text-violet-400 text-xs font-semibold">Memory Suggests ({clauseType})</span>
            </div>
            <div className="space-y-1">
              {memory.suggestions[clauseType].slice(0, 2).map((s, i) => (
                <div key={i} className="flex items-start gap-2 text-xs">
                  <button onClick={() => setClauseText(s.text || s)}
                    className="shrink-0 px-2 py-0.5 bg-violet-500/20 text-violet-400 border border-violet-500/30 rounded hover:bg-violet-500/30 transition">
                    Use
                  </button>
                  <span className="text-slate-400 leading-relaxed">{(s.text || s).slice(0, 120)}...</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="text-xs text-slate-400">Primary Clause</label>
            <button onClick={() => setClauseText(EXAMPLE)} className="text-xs text-cyan-400 hover:text-cyan-300">Use example</button>
          </div>
          <textarea value={clauseText} onChange={e => setClauseText(e.target.value)}
            placeholder="Paste the clause you want to negotiate..." rows={4}
            className="w-full px-3 py-2 bg-slate-900/60 border border-slate-600 text-white placeholder-slate-500 rounded-lg text-sm focus:outline-none focus:border-cyan-500 resize-none" />
        </div>

        {/* #9 Extra clauses for multi-clause mode */}
        {multiMode && (
          <div className="space-y-3">
            {extraClauses.map((cl, i) => (
              <div key={i} className="bg-slate-900/40 border border-slate-700/50 rounded-xl p-3 space-y-2">
                <div className="flex items-center gap-2">
                  <select value={cl.type} onChange={e => setExtraClauses(p => p.map((c, idx) => idx === i ? { ...c, type: e.target.value } : c))}
                    className="px-2 py-1 bg-slate-800 border border-slate-600 text-white rounded text-xs focus:outline-none">
                    {TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                  <button onClick={() => removeClause(i)} className="ml-auto text-red-400 hover:text-red-300"><Trash2 size={14} /></button>
                </div>
                <textarea value={cl.text} onChange={e => setExtraClauses(p => p.map((c, idx) => idx === i ? { ...c, text: e.target.value } : c))}
                  placeholder={`Clause ${i + 2} text...`} rows={3}
                  className="w-full px-3 py-2 bg-slate-900/60 border border-slate-600 text-white placeholder-slate-500 rounded-lg text-xs focus:outline-none resize-none" />
              </div>
            ))}
            <button onClick={addClause} className="flex items-center gap-2 text-sm text-cyan-400 hover:text-cyan-300">
              <Plus size={14} /> Add another clause
            </button>
          </div>
        )}

        <button onClick={run} disabled={loading || !clauseText.trim()}
          className="w-full py-3 bg-gradient-to-r from-blue-600 to-violet-600 text-white rounded-lg hover:from-blue-700 hover:to-violet-700 disabled:from-slate-600 disabled:to-slate-600 disabled:cursor-not-allowed transition font-medium flex items-center justify-center gap-2">
          {loading ? <RefreshCw size={16} className="animate-spin" /> : <Users size={16} />}
          {loading ? 'Agents Negotiating...' : `Start AI Negotiation${multiMode && extraClauses.length > 0 ? ` (${extraClauses.length + 1} clauses)` : ''}`}
        </button>
      </div>

      {loading && <LoadingSpinner text="AI agents are negotiating..." />}

      {result && !loading && (
        result.error
          ? <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl p-4">{result.error}</div>
          : result.multi_clause
            ? renderMulti()
            : <>
                {result.final_analysis && (
                  <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5">
                    <h3 className="text-white font-semibold mb-4 flex items-center gap-2"><TrendingUp size={16} className="text-emerald-400" />Negotiation Result</h3>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
                      {[
                        { label: 'Original Score', val: result.final_analysis.original_risk_score },
                        { label: 'Final Score', val: result.final_analysis.final_risk_score },
                        { label: 'Improvement', val: `${result.final_analysis.improvement > 0 ? '+' : ''}${result.final_analysis.improvement}` },
                        { label: 'Rounds', val: result.rounds_completed },
                      ].map(({ label, val }) => (
                        <div key={label} className="text-center p-3 bg-slate-900/50 rounded-lg">
                          <div className="text-xs text-slate-400 mb-1">{label}</div>
                          <div className={`text-xl font-bold ${scoreColor(typeof val === 'number' ? val : 60)}`}>{val}</div>
                        </div>
                      ))}
                    </div>
                    {/* Risk score delta bar */}
                    {result.final_analysis.original_risk_score !== undefined && result.final_analysis.final_risk_score !== undefined && (
                      <div className="mb-4 p-3 bg-slate-900/50 rounded-lg border border-slate-700/50">
                        <div className="flex items-center justify-between mb-2 text-xs text-slate-400">
                          <span>Risk Score Change</span>
                          <span className={result.final_analysis.improvement > 0 ? 'text-emerald-400' : 'text-red-400'}>
                            {result.final_analysis.original_risk_score} → {result.final_analysis.final_risk_score}
                            {' '}({result.final_analysis.improvement > 0 ? '+' : ''}{result.final_analysis.improvement} pts)
                          </span>
                        </div>
                        <div className="relative h-3 bg-slate-700 rounded-full overflow-hidden">
                          <div className="absolute h-3 rounded-full bg-red-500/40 transition-all" style={{ width: `${result.final_analysis.original_risk_score}%` }} />
                          <div className="absolute h-3 rounded-full bg-emerald-500 transition-all" style={{ width: `${result.final_analysis.final_risk_score}%` }} />
                        </div>
                        <div className="flex justify-between mt-1 text-xs text-slate-500">
                          <span className="text-red-400">Before: {result.final_analysis.original_risk_score}</span>
                          <span className="text-emerald-400">After: {result.final_analysis.final_risk_score}</span>
                        </div>
                      </div>
                    )}
                    {/* Financial impact */}
                    {result.financial_impact && (
                      <div className="mb-4 p-3 bg-emerald-900/20 rounded-lg border border-emerald-500/30">
                        <div className="flex items-center gap-2 mb-1">
                          <DollarSign size={14} className="text-emerald-400" />
                          <span className="text-emerald-400 text-sm font-semibold">Financial Impact</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-slate-300 text-sm">{result.financial_impact.interpretation}</span>
                          <span className={`text-lg font-bold ${result.financial_impact.estimated_risk_reduction_usd >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                            {result.financial_impact.estimated_risk_reduction_usd >= 0 ? '+' : ''}${Math.abs(result.financial_impact.estimated_risk_reduction_usd).toLocaleString()}
                          </span>
                        </div>
                      </div>
                    )}
                    <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-3 mb-3">
                      <p className="text-emerald-300 text-sm">{result.final_analysis.verdict}</p>
                    </div>
                    <div className="flex gap-3 text-sm">
                      <span className="text-blue-400 capitalize">{result.buyer_mode || 'balanced'} Buyer: {result.final_analysis.buyer_rounds_won} round(s)</span>
                      <span className="text-slate-500">·</span>
                      <span className="text-orange-400 capitalize">{result.supplier_mode || 'balanced'} Supplier: {result.final_analysis.supplier_rounds_won} round(s)</span>
                    </div>
                  </div>
                )}
                <div className="bg-slate-800/60 border border-emerald-500/30 rounded-xl p-5">
                  <h3 className="text-white font-semibold mb-3 flex items-center gap-2"><CheckCircle size={16} className="text-emerald-400" />Final Negotiated Clause</h3>
                  <p className="text-slate-300 text-sm leading-relaxed bg-slate-900/50 rounded-lg p-4 border border-slate-700/50">{result.final_clause}</p>
                </div>
                <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5">
                  <h3 className="text-white font-semibold mb-4 flex items-center gap-2"><MessageSquare size={16} className="text-cyan-400" />Negotiation History</h3>
                  <div className="flex gap-2 mb-4 flex-wrap">
                    {result.negotiation_history?.map((h, i) => (
                      <button key={i} onClick={() => setActiveRound(i)}
                        className={`px-3 py-1.5 rounded-lg text-sm transition ${activeRound === i ? 'bg-cyan-600 text-white' : 'bg-slate-700 text-slate-400 hover:bg-slate-600'}`}>
                        Round {h.round} ({h.round_winner === 'buyer' ? 'B' : 'S'})
                      </button>
                    ))}
                  </div>
                  {result.negotiation_history?.[activeRound] && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                      {[
                        { label: 'Buyer Agent', color: 'blue', text: result.negotiation_history[activeRound].buyer_proposal, score: result.negotiation_history[activeRound].buyer_score },
                        { label: 'Supplier Agent', color: 'orange', text: result.negotiation_history[activeRound].supplier_counter, score: result.negotiation_history[activeRound].supplier_score },
                      ].map(({ label, color, text, score }) => (
                        <div key={label} className={`bg-${color}-500/10 border border-${color}-500/30 rounded-xl p-4`}>
                          <div className="flex items-center justify-between mb-2">
                            <span className={`text-${color}-400 font-semibold text-sm`}>{label}</span>
                            <span className={`text-sm font-bold ${scoreColor(score)}`}>Score: {score}</span>
                          </div>
                          <p className="text-slate-300 text-xs leading-relaxed">{text}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </>
      )}
    </div>
  );
}

// ─── Advanced Clause Knowledge Graph ──────────────────────────
const CLAUSE_TYPE_COLORS = {
  'Force Majeure':       { bg: '#1c1917', border: '#f97316', glow: '#f9731688', text: '#fed7aa', icon: '🌪' },
  'Liability':           { bg: '#1c0a0a', border: '#ef4444', glow: '#ef444488', text: '#fca5a5', icon: '⚖' },
  'Indemnity':           { bg: '#2d1b00', border: '#f59e0b', glow: '#f59e0b88', text: '#fde68a', icon: '🛡' },
  'Payment':             { bg: '#052e16', border: '#22c55e', glow: '#22c55e88', text: '#86efac', icon: '💰' },
  'Termination':         { bg: '#1e1b4b', border: '#8b5cf6', glow: '#8b5cf688', text: '#ddd6fe', icon: '🔚' },
  'Confidentiality':     { bg: '#0c1a2e', border: '#06b6d4', glow: '#06b6d488', text: '#a5f3fc', icon: '🔒' },
  'Dispute Resolution':  { bg: '#1a0a2e', border: '#a855f7', glow: '#a855f788', text: '#e9d5ff', icon: '⚡' },
  'Governing Law':       { bg: '#0a1628', border: '#3b82f6', glow: '#3b82f688', text: '#93c5fd', icon: '📜' },
  'IP Rights':           { bg: '#0f2a1a', border: '#10b981', glow: '#10b98188', text: '#6ee7b7', icon: '💡' },
  'Warranty':            { bg: '#1a1200', border: '#eab308', glow: '#eab30888', text: '#fef08a', icon: '✅' },
  'default':             { bg: '#1e293b', border: '#64748b', glow: '#64748b88', text: '#cbd5e1', icon: '📋' },
};

const RISK_THRESHOLDS = { HIGH: 0.6, MEDIUM: 0.3 };
const riskColor  = s => s >= RISK_THRESHOLDS.HIGH ? '#ef4444' : s >= RISK_THRESHOLDS.MEDIUM ? '#f59e0b' : '#22c55e';
const riskLabel  = s => s >= RISK_THRESHOLDS.HIGH ? 'HIGH' : s >= RISK_THRESHOLDS.MEDIUM ? 'MED' : 'LOW';
const edgeWeight = s => s >= RISK_THRESHOLDS.HIGH ? 3.5 : s >= RISK_THRESHOLDS.MEDIUM ? 2.2 : 1.4;

// Rich custom node label rendered as HTML inside ReactFlow foreignObject via data.html approach
// We use plain style nodes with rich inline HTML label via the `label` prop (supports JSX)
function makeContractNode(title, clauseCount) {
  return {
    id: 'contract',
    type: 'default',
    data: {
      label: (
        <div style={{ textAlign: 'center', padding: '4px 2px' }}>
          <div style={{ fontSize: 18, marginBottom: 2 }}>📄</div>
          <div style={{ fontSize: 12, fontWeight: 800, color: '#86efac', letterSpacing: 0.5 }}>{title?.slice(0, 28)}{title?.length > 28 ? '…' : ''}</div>
          <div style={{ fontSize: 9, color: '#4ade80', marginTop: 3, opacity: 0.8 }}>CONTRACT · {clauseCount} clauses</div>
        </div>
      ),
    },
    position: { x: 0, y: 0 },
    style: {
      background: 'radial-gradient(circle at 30% 30%, #166534 0%, #052e16 100%)',
      border: '2.5px solid #22c55e',
      borderRadius: 16,
      padding: '10px 16px',
      minWidth: 200,
      boxShadow: '0 0 28px #22c55e66, 0 0 8px #22c55e33, inset 0 1px 0 #4ade8022',
    },
  };
}

function makeClauseNode(cl, i, x, y) {
  const score = cl.risk_score || 0;
  const theme = CLAUSE_TYPE_COLORS[cl.type] || CLAUSE_TYPE_COLORS.default;
  const rc    = riskColor(score);
  return {
    id: `clause-${i}`,
    type: 'default',
    data: {
      label: (
        <div style={{ textAlign: 'center', padding: '2px' }}>
          <div style={{ fontSize: 14, marginBottom: 2 }}>{theme.icon}</div>
          <div style={{ fontSize: 11, fontWeight: 700, color: theme.text }}>{cl.type}</div>
          <div style={{ display: 'flex', gap: 4, justifyContent: 'center', marginTop: 4, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 8, padding: '1px 5px', borderRadius: 6, background: rc + '22', border: `1px solid ${rc}`, color: rc, fontWeight: 700 }}>
              {riskLabel(score)} {(score * 100).toFixed(0)}%
            </span>
            {cl.obligations?.length > 0 && (
              <span style={{ fontSize: 8, padding: '1px 5px', borderRadius: 6, background: '#f9731622', border: '1px solid #f97316', color: '#fdba74', fontWeight: 700 }}>
                {cl.obligations.length} OBL
              </span>
            )}
          </div>
        </div>
      ),
    },
    position: { x, y },
    style: {
      background: `radial-gradient(circle at 30% 30%, ${theme.bg} 0%, #0f172a 100%)`,
      border: `2px solid ${theme.border}`,
      borderRadius: 12,
      padding: '8px 14px',
      minWidth: 120,
      boxShadow: `0 0 18px ${theme.glow}, inset 0 1px 0 ${theme.border}22`,
    },
  };
}

function makeObligationNode(text, id, x, y) {
  const short = String(text).slice(0, 45);
  return {
    id,
    type: 'default',
    data: {
      label: (
        <div style={{ textAlign: 'center', padding: '1px' }}>
          <div style={{ fontSize: 9, color: '#fdba74', fontWeight: 600, lineHeight: 1.4 }}>
            {short}{text.length > 45 ? '…' : ''}
          </div>
        </div>
      ),
    },
    position: { x, y },
    style: {
      background: 'radial-gradient(circle, #431407 0%, #0f172a 100%)',
      border: '1.5px solid #f97316',
      borderRadius: 8,
      padding: '5px 8px',
      maxWidth: 140,
      boxShadow: '0 0 10px #f9731633',
      fontSize: 9,
    },
  };
}

function makeRiskNode(score, id, x, y, clauseType) {
  const rc = riskColor(score);
  const rl = riskLabel(score);
  return {
    id,
    type: 'default',
    data: {
      label: (
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 10, fontWeight: 800, color: rc }}>{rl} RISK</div>
          <div style={{ fontSize: 16, fontWeight: 900, color: rc }}>{(score * 100).toFixed(0)}%</div>
          <div style={{ fontSize: 8, color: '#94a3b8', marginTop: 2 }}>FM Score</div>
        </div>
      ),
    },
    position: { x, y },
    style: {
      background: `radial-gradient(circle, ${rc}15 0%, #0f172a 100%)`,
      border: `2px solid ${rc}`,
      borderRadius: '50%',
      padding: '8px',
      width: 80,
      height: 80,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      boxShadow: `0 0 20px ${rc}55, 0 0 6px ${rc}33`,
    },
  };
}

function buildGraphFromResult(result) {
  const nodes = [];
  const edges = [];
  const clauses = result.clauses || [];

  // ── Contract hub (center top) ──
  nodes.push(makeContractNode(result.contract_title, clauses.length));

  // ── Radial layout for clauses ──
  const total = clauses.length;
  const radiusX = Math.max(320, total * 55);
  const radiusY = 260;
  const centerX = 0;
  const centerY = 320;

  clauses.forEach((cl, i) => {
    const angle = (Math.PI / (total + 1)) * (i + 1); // spread across bottom half
    const cx = centerX + Math.cos(Math.PI - angle) * radiusX;
    const cy = centerY + Math.sin(angle) * radiusY * 0.6;
    const clauseId = `clause-${i}`;
    const score    = cl.risk_score || 0;

    nodes.push(makeClauseNode(cl, i, cx, cy));

    // Edge: Contract → Clause (weight = risk score)
    const ew = edgeWeight(score);
    const ec = riskColor(score);
    edges.push({
      id: `e-c-${clauseId}`,
      source: 'contract',
      target: clauseId,
      type: 'default',
      animated: score >= RISK_THRESHOLDS.HIGH,
      label: `w:${(score * 100).toFixed(0)}`,
      labelStyle: { fill: ec, fontSize: 8, fontWeight: 700 },
      labelBgStyle: { fill: '#0f172a', fillOpacity: 0.8 },
      style: { stroke: ec, strokeWidth: ew, opacity: 0.75 },
      markerEnd: { type: MarkerType.ArrowClosed, color: ec, width: 14, height: 14 },
    });

    // ── Risk node (circular, off to the right of each clause) ──
    if (score > 0) {
      const riskId = `risk-${i}`;
      nodes.push(makeRiskNode(score, riskId, cx + 140, cy - 30));
      edges.push({
        id: `e-${clauseId}-${riskId}`,
        source: clauseId,
        target: riskId,
        type: 'default',
        animated: score >= RISK_THRESHOLDS.HIGH,
        label: 'EXPOSES',
        labelStyle: { fill: riskColor(score), fontSize: 7, fontWeight: 700 },
        labelBgStyle: { fill: '#0f172a', fillOpacity: 0.8 },
        style: { stroke: riskColor(score), strokeWidth: 1.5, strokeDasharray: score < RISK_THRESHOLDS.MEDIUM ? '4 3' : undefined },
        markerEnd: { type: MarkerType.ArrowClosed, color: riskColor(score), width: 10, height: 10 },
      });
    }

    // ── Obligation nodes (below each clause) ──
    (cl.obligations || []).slice(0, 3).forEach((ob, j) => {
      const obId  = `ob-${i}-${j}`;
      const spread = (j - 1) * 130;
      nodes.push(makeObligationNode(ob, obId, cx + spread, cy + 150));
      edges.push({
        id: `e-${clauseId}-${obId}`,
        source: clauseId,
        target: obId,
        type: 'default',
        animated: false,
        label: 'OBLIGES',
        labelStyle: { fill: '#f97316', fontSize: 7, fontWeight: 600 },
        labelBgStyle: { fill: '#0f172a', fillOpacity: 0.7 },
        style: { stroke: '#f97316', strokeWidth: 1.2, strokeDasharray: '5 3', opacity: 0.7 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#f97316', width: 8, height: 8 },
      });
    });

    // ── Cross-edges: connect high-risk clauses to each other ──
    if (score >= RISK_THRESHOLDS.HIGH && i > 0) {
      const prevHighIdx = clauses.slice(0, i).reduceRight((found, c, idx) => found === -1 && c.risk_score >= RISK_THRESHOLDS.HIGH ? idx : found, -1);
      if (prevHighIdx !== -1) {
        edges.push({
          id: `e-cross-${prevHighIdx}-${i}`,
          source: `clause-${prevHighIdx}`,
          target: clauseId,
          type: 'default',
          animated: true,
          label: 'AMPLIFIES',
          labelStyle: { fill: '#ef4444', fontSize: 7, fontWeight: 700 },
          labelBgStyle: { fill: '#0f172a', fillOpacity: 0.8 },
          style: { stroke: '#ef444466', strokeWidth: 1.5, strokeDasharray: '6 3' },
          markerEnd: { type: MarkerType.ArrowClosed, color: '#ef4444', width: 8, height: 8 },
        });
      }
    }
  });

  return { nodes, edges };
}

// ─── Tab 6: Graph Builder (#4) ────────────────────────────────
function GraphBuilderTab() {
  const [contractId, setContractId] = useState('');
  const [useLlm, setUseLlm] = useState(true);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [batchResult, setBatchResult] = useState(null);
  const [batchLoading, setBatchLoading] = useState(false);
  const [showGraph, setShowGraph] = useState(true);
  const [selectedNode, setSelectedNode] = useState(null);
  const [syncLoading, setSyncLoading] = useState(false);
  const [node2vecRecs, setNode2vecRecs] = useState(null);
  const [recsLoading, setRecsLoading] = useState(false);
  const [expandedSections, setExpandedSections] = useState({ text: false, obligations: false, properties: false });
  const [isFullscreen, setIsFullscreen] = useState(false);

  const build = async () => {
    if (!contractId) return;
    setLoading(true); setResult(null);
    try { setResult(await buildContractGraph(contractId, useLlm)); }
    catch (e) { setResult({ error: e.response?.data?.error || 'Graph build failed' }); }
    finally { setLoading(false); }
  };

  const buildAll = async () => {
    setBatchLoading(true); setBatchResult(null);
    try { setBatchResult(await buildAllGraphs()); }
    catch (e) { setBatchResult({ error: e.response?.data?.error || 'Batch build failed' }); }
    finally { setBatchLoading(false); }
  };

  const syncRealtime = async () => {
    if (!contractId) return;
    setSyncLoading(true);
    try {
      await syncGraphRealtime(contractId);
      // Rebuild to see updated graph
      await build();
    } catch (e) {
      console.error('Real-time sync failed:', e);
    } finally {
      setSyncLoading(false);
    }
  };

  const loadNode2VecRecs = async (nodeId) => {
    if (!nodeId) return;
    setRecsLoading(true);
    setNode2vecRecs(null);
    try {
      const data = await getNode2VecRecommendations(nodeId, 5);
      console.log('Node2Vec response:', data);
      setNode2vecRecs(data);
    } catch (e) {
      console.error('Node2Vec recommendations failed:', e);
      console.error('Error details:', e.response?.data || e.message);
      setNode2vecRecs({
        error: e.response?.data?.error || e.message || 'Failed to load recommendations'
      });
    } finally {
      setRecsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-white mb-1">Auto Clause Extraction → Neo4j Graph Builder</h2>
        <p className="text-slate-400 text-sm">Extracts clauses using AI or rule-based patterns, then pushes Contract→Clause→Risk→Obligation nodes into Neo4j</p>
      </div>
      <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5 space-y-4">
        <div className="space-y-3">
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Select Contract</label>
            <ContractSelect value={contractId} onChange={setContractId} placeholder="Choose a contract to build graph for..." />
          </div>
          <div className="flex gap-3">
            <button onClick={() => setUseLlm(v => !v)}
              className={`px-4 py-2.5 rounded-lg text-sm transition ${useLlm ? 'bg-violet-600 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'}`}>
              {useLlm ? 'LLM Extraction' : 'Rule-based'}
            </button>
            <button onClick={build} disabled={loading || !contractId}
              className="flex-1 py-2.5 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:bg-slate-600 disabled:cursor-not-allowed transition text-sm font-medium flex items-center justify-center gap-2">
              {loading ? <RefreshCw size={14} className="animate-spin" /> : <Database size={14} />}
              {loading ? 'Building...' : 'Build Graph'}
            </button>
            <button onClick={syncRealtime} disabled={syncLoading || !contractId}
              className="px-4 py-2.5 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 disabled:bg-slate-600 disabled:cursor-not-allowed transition text-sm font-medium flex items-center gap-2"
              title="Real-time sync: Rebuild graph and refresh index">
              {syncLoading ? <RefreshCw size={14} className="animate-spin" /> : <Sparkles size={14} />}
              Sync
            </button>
          </div>
        </div>
        <div className="flex items-center justify-between pt-2 border-t border-slate-700/40">
          <span className="text-xs text-slate-500">Or build graphs for all contracts at once</span>
          <button onClick={buildAll} disabled={batchLoading}
            className="px-4 py-2 bg-slate-700 text-slate-300 rounded-lg hover:bg-slate-600 disabled:opacity-50 transition text-sm flex items-center gap-2">
            {batchLoading ? <RefreshCw size={14} className="animate-spin" /> : <Network size={14} />}
            {batchLoading ? 'Building all...' : 'Batch Build All'}
          </button>
        </div>
      </div>

      {loading && <LoadingSpinner text="Extracting clauses and building graph..." />}

      {result && !loading && (
        result.error
          ? <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl p-4">{result.error}</div>
          : <div className="space-y-4">
              {/* Header row */}
              <div className="flex items-center gap-3 px-1">
                <CheckCircle size={18} className="text-emerald-400" />
                <span className="text-white font-semibold">{result.contract_title}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full border ${result.pushed_to_neo4j ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-slate-500/20 text-slate-400 border-slate-500/30'}`}>
                  {result.pushed_to_neo4j ? 'Pushed to Neo4j' : 'Extracted only'}
                </span>
                <span className="text-xs text-slate-500">{result.extraction_method}</span>
                <div className="ml-auto flex gap-2">
                  <button onClick={() => setShowGraph(v => !v)}
                    className={`px-3 py-1 text-xs rounded-lg border transition ${showGraph ? 'bg-cyan-600 text-white border-cyan-500' : 'bg-slate-700 text-slate-300 border-slate-600 hover:bg-slate-600'}`}>
                    {showGraph ? 'Hide Graph' : 'Show Graph'}
                  </button>
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-4 gap-3">
                <StatCard label="Clauses Extracted" value={result.clauses_extracted} color="emerald" />
                <StatCard label="High Risk" value={(result.clauses || []).filter(c => (c.risk_score||0) >= 0.6).length} color="red" sub="FM ≥ 60%" />
                <StatCard label="Obligations" value={(result.clauses || []).reduce((s, c) => s + (c.obligations?.length || 0), 0)} color="orange" />
                <StatCard label="Neo4j Pushed" value={result.pushed_to_neo4j ? 'Yes' : 'No'} color={result.pushed_to_neo4j ? 'emerald' : 'slate'} sub={result.extraction_method} />
              </div>

              {/* Graph */}
              {showGraph && (() => {
                const { nodes, edges } = buildGraphFromResult(result);
                const clauses = result.clauses || [];
                const highRisk = clauses.filter(c => (c.risk_score || 0) >= RISK_THRESHOLDS.HIGH).length;
                const totalObl = clauses.reduce((s, c) => s + (c.obligations?.length || 0), 0);

                // Highlight edges connected to selected node
                const enhancedEdges = edges.map(edge => {
                  if (selectedNode && (edge.source === selectedNode.id || edge.target === selectedNode.id)) {
                    return {
                      ...edge,
                      style: {
                        ...edge.style,
                        strokeWidth: (edge.style?.strokeWidth || 1) * 2,
                        opacity: 1,
                      },
                      animated: true,
                    };
                  }
                  return edge;
                });

                // Highlight nodes connected to selected node
                const connectedNodeIds = selectedNode
                  ? new Set([
                      ...edges.filter(e => e.source === selectedNode.id).map(e => e.target),
                      ...edges.filter(e => e.target === selectedNode.id).map(e => e.source),
                    ])
                  : new Set();

                const enhancedNodes = nodes.map(node => {
                  if (selectedNode && selectedNode.id === node.id) {
                    return {
                      ...node,
                      style: {
                        ...node.style,
                        boxShadow: '0 0 20px 5px rgba(59, 130, 246, 0.6)',
                      },
                    };
                  }
                  if (selectedNode && connectedNodeIds.has(node.id)) {
                    return {
                      ...node,
                      style: {
                        ...node.style,
                        opacity: 1,
                        boxShadow: '0 0 10px 2px rgba(34, 197, 94, 0.4)',
                      },
                    };
                  }
                  if (selectedNode) {
                    return {
                      ...node,
                      style: {
                        ...node.style,
                        opacity: 0.3,
                      },
                    };
                  }
                  return node;
                });

                return (
                  <div className="space-y-3">
                    {/* Graph metrics bar */}
                    <div className="flex flex-wrap gap-3 text-xs">
                      {[
                        { label: 'Nodes', val: nodes.length, color: 'text-cyan-400' },
                        { label: 'Edges', val: edges.length, color: 'text-blue-400' },
                        { label: 'High-Risk Clauses', val: highRisk, color: 'text-red-400' },
                        { label: 'Obligations', val: totalObl, color: 'text-orange-400' },
                        { label: 'Animated Edges', val: edges.filter(e => e.animated).length, color: 'text-violet-400' },
                        { label: 'Cross-links', val: edges.filter(e => e.id.startsWith('e-cross')).length, color: 'text-yellow-400' },
                      ].map(m => (
                        <div key={m.label} className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800/60 border border-slate-700/40 rounded-lg">
                          <span className={`font-bold text-sm ${m.color}`}>{m.val}</span>
                          <span className="text-slate-400">{m.label}</span>
                        </div>
                      ))}
                    </div>

                    {/* Interactive Tips */}
                    <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg px-4 py-2 flex items-center gap-3">
                      <Eye size={16} className="text-blue-400 shrink-0" />
                      <div className="text-xs text-blue-300">
                        <span className="font-semibold">Interactive Graph:</span> Drag nodes to reposition • Click nodes for full details • Scroll to zoom • Use controls (bottom-left) to navigate
                      </div>
                    </div>

                    {/* Legend */}
                    <div className="flex flex-wrap gap-4 text-xs px-1">
                      <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-full bg-emerald-500" /><span className="text-slate-400">Contract hub</span></div>
                      {Object.entries(CLAUSE_TYPE_COLORS).slice(0, 6).map(([t, c]) => (
                        <div key={t} className="flex items-center gap-1.5">
                          <div className="w-3 h-3 rounded-full" style={{ background: c.border }} />
                          <span className="text-slate-400">{t}</span>
                        </div>
                      ))}
                      <div className="flex items-center gap-1.5"><div className="w-8 border-t-2 border-red-400 border-dashed" /><span className="text-slate-400">AMPLIFIES (cross-risk)</span></div>
                      <div className="flex items-center gap-1.5"><div className="w-8 border-t-2 border-orange-400 border-dashed" /><span className="text-slate-400">OBLIGES</span></div>
                    </div>

                    <div className={`${isFullscreen ? 'fixed inset-0 z-50 bg-slate-900' : ''}`}>
                      {isFullscreen && (
                        <div className="absolute top-4 right-4 z-10 flex gap-2">
                          <button
                            onClick={() => setIsFullscreen(false)}
                            className="px-3 py-2 bg-slate-800 text-white rounded-lg hover:bg-slate-700 transition flex items-center gap-2 border border-slate-600"
                          >
                            <Minimize size={16} />
                            <span className="text-sm">Exit Fullscreen</span>
                          </button>
                        </div>
                      )}

                      <div className={`flex gap-3 ${isFullscreen ? 'h-screen p-4' : ''}`}>
                        {/* Main graph canvas */}
                        <div className={`flex-1 rounded-xl overflow-hidden border border-slate-700/50 ${isFullscreen ? 'h-full' : ''}`} style={{ height: isFullscreen ? '100%' : 620, background: 'radial-gradient(ellipse at center, #0f172a 0%, #020617 100%)' }}>
                          {/* Fullscreen button overlay */}
                          {!isFullscreen && (
                            <button
                              onClick={() => setIsFullscreen(true)}
                              className="absolute top-2 right-2 z-10 p-2 bg-slate-800/80 hover:bg-slate-700 text-white rounded-lg transition border border-slate-600/50"
                              title="Fullscreen"
                            >
                              <Maximize2 size={16} />
                            </button>
                          )}

                          <ReactFlowProvider>
                            <ReactFlow
                              nodes={enhancedNodes}
                              edges={enhancedEdges}
                              fitView
                              fitViewOptions={{ padding: 0.25 }}
                              nodesDraggable={true}
                              nodesConnectable={false}
                              elementsSelectable={true}
                              panOnScroll={true}
                              zoomOnScroll={true}
                              zoomOnDoubleClick={true}
                              selectNodesOnDrag={false}
                            onNodeClick={(_, node) => {
                              setSelectedNode(node);
                              setExpandedSections({ text: true, obligations: false, properties: false });
                            }}
                            onPaneClick={() => {
                              setSelectedNode(null);
                              setExpandedSections({ text: false, obligations: false, properties: false });
                            }}
                            defaultEdgeOptions={{
                              type: 'default',
                              labelStyle: { fontSize: 10, fontWeight: 600 },
                              labelBgPadding: [8, 4],
                              labelBgBorderRadius: 4,
                            }}
                          >
                            <Background variant="dots" color="#1e293b" gap={24} size={1.2} />
                            <Controls style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
                            <MiniMap
                              style={{ background: '#020617', border: '1px solid #334155', borderRadius: 8 }}
                              nodeColor={n => {
                                if (n.id === 'contract') return '#22c55e';
                                if (n.id.startsWith('risk')) return riskColor(result.clauses?.[parseInt(n.id.split('-')[1])]?.risk_score || 0);
                                if (n.id.startsWith('ob')) return '#f97316';
                                const idx = parseInt(n.id.split('-')[1]);
                                const cl = result.clauses?.[idx];
                                return cl ? (CLAUSE_TYPE_COLORS[cl.type] || CLAUSE_TYPE_COLORS.default).border : '#64748b';
                              }}
                              maskColor="#02061788"
                            />
                          </ReactFlow>
                        </ReactFlowProvider>
                      </div>

                      {/* Node info panel (right side) */}
                      <div className={`w-80 shrink-0 space-y-2 ${isFullscreen ? 'h-full' : ''}`}>
                        <div className="flex items-center gap-2 px-1 mb-2">
                          <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Node Inspector</div>
                          {selectedNode && (
                            <div className="text-xs px-2 py-0.5 bg-blue-500/20 text-blue-400 border border-blue-500/30 rounded-full">
                              Active
                            </div>
                          )}
                        </div>
                        {selectedNode ? (
                          <div className={`bg-slate-800/80 border border-slate-600/50 rounded-xl p-4 space-y-3 overflow-y-auto ${isFullscreen ? 'h-[calc(100vh-100px)]' : 'max-h-[600px]'}`}>
                            <div className="flex items-center justify-between">
                              <div className="text-xs text-slate-500">ID: {selectedNode.id}</div>
                              <button
                                onClick={() => {
                                  setSelectedNode(null);
                                  setExpandedSections({ text: false, obligations: false, properties: false });
                                }}
                                className="text-xs text-slate-500 hover:text-slate-300 transition"
                                title="Close inspector"
                              >
                                ✕
                              </button>
                            </div>
                            {selectedNode.id === 'contract' && (
                              <>
                                <div className="text-emerald-400 font-bold text-sm">📄 CONTRACT HUB</div>
                                <div className="text-slate-300 text-xs">{result.contract_title}</div>
                                <div className="text-slate-400 text-xs">{clauses.length} clauses extracted</div>
                                <div className="text-slate-400 text-xs">{totalObl} total obligations</div>
                              </>
                            )}
                            {selectedNode.id.startsWith('clause-') && (() => {
                              const idx = parseInt(selectedNode.id.split('-')[1]);
                              const cl = clauses[idx];
                              if (!cl) return null;
                              const theme = CLAUSE_TYPE_COLORS[cl.type] || CLAUSE_TYPE_COLORS.default;
                              const rc = riskColor(cl.risk_score || 0);
                              return (
                                <>
                                  <div className="font-bold text-sm" style={{ color: theme.text }}>{theme.icon} {cl.type}</div>
                                  <div className="flex items-center gap-2">
                                    <span className="text-xs px-2 py-0.5 rounded-full font-bold" style={{ background: rc + '22', border: `1px solid ${rc}`, color: rc }}>{riskLabel(cl.risk_score || 0)} RISK</span>
                                    <span className="text-xs text-slate-400">{((cl.risk_score || 0) * 100).toFixed(0)}%</span>
                                  </div>

                                  {/* Full Clause Text - Expandable */}
                                  <div className="border-t border-slate-700/30 pt-2">
                                    <button
                                      onClick={() => setExpandedSections(prev => ({ ...prev, text: !prev.text }))}
                                      className="flex items-center justify-between w-full text-xs text-slate-300 font-semibold hover:text-white transition"
                                    >
                                      <span>📝 Full Clause Text</span>
                                      <ChevronDown size={14} className={`transform transition ${expandedSections.text ? 'rotate-180' : ''}`} />
                                    </button>
                                    {expandedSections.text ? (
                                      <div className="mt-2 text-xs text-slate-300 leading-relaxed bg-slate-900/50 border border-slate-700/30 rounded-lg p-3 max-h-60 overflow-y-auto">
                                        {cl.text || 'No text available'}
                                      </div>
                                    ) : (
                                      <div className="mt-2 text-xs text-slate-400 leading-relaxed">
                                        {(cl.text || '').slice(0, 120)}…
                                      </div>
                                    )}
                                  </div>

                                  {/* Properties */}
                                  <div className="border-t border-slate-700/30 pt-2">
                                    <button
                                      onClick={() => setExpandedSections(prev => ({ ...prev, properties: !prev.properties }))}
                                      className="flex items-center justify-between w-full text-xs text-slate-300 font-semibold hover:text-white transition"
                                    >
                                      <span>🔍 Properties</span>
                                      <ChevronDown size={14} className={`transform transition ${expandedSections.properties ? 'rotate-180' : ''}`} />
                                    </button>
                                    {expandedSections.properties && (
                                      <div className="mt-2 space-y-1">
                                        <div className="text-xs"><span className="text-slate-500">Type:</span> <span className="text-slate-300">{cl.type}</span></div>
                                        <div className="text-xs"><span className="text-slate-500">Risk Score:</span> <span className="text-slate-300">{((cl.risk_score || 0) * 100).toFixed(1)}%</span></div>
                                        <div className="text-xs"><span className="text-slate-500">Obligations:</span> <span className="text-slate-300">{cl.obligations?.length || 0}</span></div>
                                        {cl.sentiment && <div className="text-xs"><span className="text-slate-500">Sentiment:</span> <span className="text-slate-300">{cl.sentiment}</span></div>}
                                        {cl.confidence !== undefined && <div className="text-xs"><span className="text-slate-500">Confidence:</span> <span className="text-slate-300">{(cl.confidence * 100).toFixed(1)}%</span></div>}
                                      </div>
                                    )}
                                  </div>

                                  {/* Obligations - Expandable */}
                                  {cl.obligations?.length > 0 && (
                                    <div className="border-t border-slate-700/30 pt-2">
                                      <button
                                        onClick={() => setExpandedSections(prev => ({ ...prev, obligations: !prev.obligations }))}
                                        className="flex items-center justify-between w-full text-xs text-orange-400 font-semibold hover:text-orange-300 transition"
                                      >
                                        <span>📋 Obligations ({cl.obligations.length})</span>
                                        <ChevronDown size={14} className={`transform transition ${expandedSections.obligations ? 'rotate-180' : ''}`} />
                                      </button>
                                      {expandedSections.obligations ? (
                                        <div className="mt-2 space-y-2">
                                          {cl.obligations.map((o, j) => (
                                            <div key={j} className="text-xs text-slate-300 bg-orange-500/5 border border-orange-500/20 rounded-lg p-2 leading-relaxed">
                                              <span className="text-orange-400 font-bold">#{j + 1}:</span> {String(o)}
                                            </div>
                                          ))}
                                        </div>
                                      ) : (
                                        <div className="mt-2 space-y-1">
                                          {cl.obligations.slice(0, 2).map((o, j) => (
                                            <div key={j} className="text-xs text-slate-500 border-l-2 border-orange-500/40 pl-2">{String(o).slice(0, 60)}…</div>
                                          ))}
                                        </div>
                                      )}
                                    </div>
                                  )}
                                </>
                              );
                            })()}
                            {selectedNode.id.startsWith('risk-') && (() => {
                              const idx = parseInt(selectedNode.id.split('-')[1]);
                              const cl = clauses[idx];
                              if (!cl) return null;
                              const rc = riskColor(cl.risk_score || 0);
                              return (
                                <>
                                  <div className="font-bold text-sm" style={{ color: rc }}>⚠ RISK NODE</div>
                                  <div className="text-xs text-slate-400">For: {cl.type}</div>
                                  <div className="text-4xl font-black text-center py-4" style={{ color: rc }}>{((cl.risk_score || 0) * 100).toFixed(0)}%</div>
                                  <div className="text-xs text-slate-500 text-center mb-2">FM Exposure Score</div>
                                  <div className="border-t border-slate-700/30 pt-2">
                                    <div className="text-xs text-slate-400 mb-1 font-semibold">Associated Clause:</div>
                                    <div className="text-xs text-slate-300 bg-slate-900/50 border border-slate-700/30 rounded-lg p-2 leading-relaxed">
                                      {(cl.text || '').slice(0, 200)}…
                                    </div>
                                  </div>
                                </>
                              );
                            })()}
                            {selectedNode.id.startsWith('ob-') && (() => {
                              const parts = selectedNode.id.split('-');
                              const clauseIdx = parseInt(parts[1]);
                              const obIdx = parseInt(parts[2]);
                              const cl = clauses[clauseIdx];
                              const obligation = cl?.obligations?.[obIdx];
                              return (
                                <>
                                  <div className="text-orange-400 font-bold text-sm">📋 OBLIGATION</div>
                                  <div className="text-xs text-slate-500 mb-2">From: {cl?.type || 'Unknown clause'}</div>
                                  <div className="text-xs text-slate-300 bg-slate-900/50 border border-slate-700/30 rounded-lg p-3 leading-relaxed">
                                    {String(obligation || selectedNode.data?.label?.props?.children?.props?.children || 'Obligation node')}
                                  </div>
                                  {cl && (
                                    <div className="border-t border-slate-700/30 pt-2 mt-2">
                                      <div className="text-xs text-slate-400 mb-1 font-semibold">Parent Clause:</div>
                                      <div className="text-xs text-slate-500">
                                        {(cl.text || '').slice(0, 100)}…
                                      </div>
                                    </div>
                                  )}
                                </>
                              );
                            })()}

                            {/* Node2Vec Recommendations */}
                            <div className="pt-3 border-t border-slate-700/30">
                              <button
                                onClick={() => loadNode2VecRecs(selectedNode.id)}
                                disabled={recsLoading}
                                className="w-full px-3 py-1.5 bg-violet-600/20 text-violet-400 border border-violet-500/30 rounded-lg hover:bg-violet-600/30 disabled:opacity-50 transition text-xs font-medium flex items-center justify-center gap-2"
                              >
                                {recsLoading ? <RefreshCw size={12} className="animate-spin" /> : <Network size={12} />}
                                {recsLoading ? 'Loading...' : 'Similar Nodes'}
                              </button>
                              {node2vecRecs && !node2vecRecs.error && node2vecRecs.recommendations?.length > 0 && (
                                <div className="mt-2 space-y-2">
                                  <div className="text-xs text-violet-400 font-semibold">✨ Similar Clauses (Graph-based):</div>
                                  {node2vecRecs.recommendations.map((rec, i) => (
                                    <div key={i} className="text-xs p-2.5 bg-violet-500/10 border border-violet-500/20 rounded-lg hover:bg-violet-500/15 transition">
                                      <div className="flex items-center justify-between mb-1.5">
                                        <span className="text-violet-300 font-semibold text-[11px]">Similar Clause #{i + 1}</span>
                                        <span className="text-violet-400 font-bold">{(rec.similarity_score * 100).toFixed(0)}% match</span>
                                      </div>
                                      {rec.clause_text && (
                                        <div className="text-slate-300 text-[11px] leading-relaxed mb-1.5 bg-slate-900/50 p-2 rounded border border-slate-700/30">
                                          {rec.clause_text.slice(0, 150)}...
                                        </div>
                                      )}
                                      <div className="flex items-center gap-1.5 text-[10px]">
                                        <span className="text-slate-500">Neo4j ID:</span>
                                        <span className="text-slate-400">{rec.clause_id}</span>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              )}
                              {node2vecRecs && !node2vecRecs.error && node2vecRecs.recommendations?.length === 0 && node2vecRecs.message && (
                                <div className="mt-2 text-xs text-yellow-400 p-2 bg-yellow-500/10 border border-yellow-500/20 rounded leading-relaxed">
                                  ℹ️ {node2vecRecs.message}
                                </div>
                              )}
                              {node2vecRecs?.error && (
                                <div className="mt-2 text-xs text-red-400 p-2 bg-red-500/10 border border-red-500/20 rounded">
                                  {node2vecRecs.error}
                                </div>
                              )}
                            </div>
                          </div>
                        ) : (
                          <div className="bg-slate-800/40 border border-slate-700/30 rounded-xl p-5 text-center space-y-3">
                            <div className="text-slate-600 text-3xl">🔍</div>
                            <div className="text-slate-400 text-sm font-medium">No node selected</div>
                            <div className="text-slate-500 text-xs leading-relaxed">
                              Click any node in the graph to view:
                              <div className="mt-2 space-y-1">
                                <div>• Full clause text</div>
                                <div>• Risk analysis</div>
                                <div>• Obligations</div>
                                <div>• Node properties</div>
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Edge type legend */}
                        <div className="bg-slate-800/40 border border-slate-700/30 rounded-xl p-3 space-y-2 mt-3">
                          <div className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Edge Types</div>
                          {[
                            { color: '#ef4444', label: 'EXPOSES (high risk)', dash: false, animated: true },
                            { color: '#f59e0b', label: 'EXPOSES (med risk)', dash: true, animated: false },
                            { color: '#f97316', label: 'OBLIGES', dash: true, animated: false },
                            { color: '#ef4444', label: 'AMPLIFIES', dash: true, animated: true },
                          ].map(e => (
                            <div key={e.label} className="flex items-center gap-2">
                              <div className="w-8 border-t" style={{ borderColor: e.color, borderStyle: e.dash ? 'dashed' : 'solid', borderWidth: 1.5 }} />
                              <span className="text-xs text-slate-500">{e.label}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                    </div> {/* Close fullscreen container */}
                  </div>
                );
              })()}

              {/* Clause list below graph */}
              <div className="space-y-2">
                {result.clauses?.map((cl, i) => (
                  <div key={i} className="p-3 bg-slate-900/50 border border-slate-700/30 rounded-lg">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-cyan-400 text-sm font-medium">{cl.type}</span>
                      <span className="text-xs text-orange-400">FM Risk: {((cl.risk_score || 0) * 100).toFixed(0)}%</span>
                    </div>
                    <p className="text-slate-400 text-xs leading-relaxed">{(cl.text || '').slice(0, 200)}{cl.text?.length > 200 ? '...' : ''}</p>
                    {cl.obligations?.length > 0 && (
                      <div className="mt-1 flex flex-wrap gap-1">
                        {cl.obligations.slice(0, 3).map((o, j) => (
                          <span key={j} className="text-xs bg-blue-500/10 text-blue-400 border border-blue-500/20 px-1.5 py-0.5 rounded">{String(o).slice(0, 60)}</span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
      )}

      {batchResult && !batchLoading && (
        batchResult.error
          ? <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl p-4">{batchResult.error}</div>
          : <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5">
              <h3 className="text-white font-semibold mb-3">Batch Build Complete — {batchResult.processed} contracts processed</h3>
              <div className="space-y-1 max-h-60 overflow-y-auto">
                {batchResult.results?.map((r, i) => (
                  <div key={i} className="flex items-center gap-3 text-xs p-2 bg-slate-900/40 rounded">
                    <span className={r.pushed ? 'text-emerald-400' : 'text-slate-500'}>{r.pushed ? '✓' : '○'}</span>
                    <span className="text-slate-300 truncate flex-1">{r.title || r.contract_id}</span>
                    <span className="text-slate-500 shrink-0">{r.clauses_extracted} clauses</span>
                  </div>
                ))}
              </div>
            </div>
      )}
    </div>
  );
}

// ─── Tab 7: FM Risk Scorer (#3) ───────────────────────────────
function FMScorerTab() {
  const [text, setText] = useState('');
  const [contractId, setContractId] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expandedClauses, setExpandedClauses] = useState(new Set());

  const toggleClause = (index) => {
    const newExpanded = new Set(expandedClauses);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedClauses(newExpanded);
  };

  const EXAMPLE_CLAUSE = `In the event of force majeure including acts of God, pandemic, war, earthquake, flood, or any government action, the Supplier shall have no obligation to perform. The Buyer shall have no right to terminate for up to 12 months. Unlimited force majeure extensions may be granted at Supplier's sole discretion.`;

  const score = async () => {
    setLoading(true); setResult(null);
    try { setResult(await scoreForceMajeure(contractId ? null : text, contractId || null)); }
    catch (e) { setResult({ error: e.response?.data?.error || 'Scoring failed' }); }
    finally { setLoading(false); }
  };

  const riskColor = level => ({ HIGH: 'text-red-400 border-red-500/30 bg-red-500/10', MEDIUM: 'text-yellow-400 border-yellow-500/30 bg-yellow-500/10', LOW: 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10' }[level] || '');

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-white mb-1">Force Majeure Risk Scorer</h2>
        <p className="text-slate-400 text-sm">Scores clause text 0–1 using 20+ weighted FM signals. Identifies risky provisions vs protective ones.</p>
      </div>
      <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5 space-y-4">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-end">
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Score a Contract</label>
            <ContractSelect value={contractId} onChange={v => { setContractId(v); if (v) setText(''); }} placeholder="Select contract to score all FM clauses..." />
          </div>
          <div className="flex items-center justify-center text-slate-500 text-sm pb-1">— or paste text below —</div>
        </div>
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="text-xs text-slate-400">Score Arbitrary Text</label>
            <button onClick={() => setText(EXAMPLE_CLAUSE)} className="text-xs text-cyan-400 hover:text-cyan-300">Use high-risk example</button>
          </div>
          <textarea value={text} onChange={e => { setText(e.target.value); if (e.target.value) setContractId(''); }} rows={5}
            placeholder="Paste a force majeure clause to score..."
            className="w-full px-3 py-2 bg-slate-900/60 border border-slate-600 text-white placeholder-slate-500 rounded-lg text-sm focus:outline-none focus:border-orange-500 resize-none" />
        </div>
        <button onClick={score} disabled={loading || (!text.trim() && !contractId.trim())}
          className="w-full py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:bg-slate-600 disabled:cursor-not-allowed transition font-medium flex items-center justify-center gap-2">
          {loading ? <RefreshCw size={16} className="animate-spin" /> : <Cloud size={16} />}
          {loading ? 'Scoring...' : 'Score Force Majeure Risk'}
        </button>
      </div>

      {loading && <LoadingSpinner text="Scoring FM risk..." />}

      {result && !loading && (
        result.error
          ? <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl p-4">{result.error}</div>
          : <div className="space-y-4">
              {/* Single text score */}
              {result.score !== undefined && (
                <div className={`rounded-xl border p-5 ${riskColor(result.risk_level)}`}>
                  <div className="flex items-center justify-between mb-3">
                    <span className="font-semibold text-lg">FM Risk: {result.risk_level}</span>
                    <span className="text-3xl font-bold">{(result.score * 100).toFixed(0)}%</span>
                  </div>
                  <div className="w-full bg-slate-700 rounded-full h-3 mb-4">
                    <div className="h-3 rounded-full transition-all" style={{ width: `${result.score * 100}%`, background: result.risk_level === 'HIGH' ? '#F16667' : result.risk_level === 'MEDIUM' ? '#FFD86E' : '#68BC00' }} />
                  </div>
                  {result.signals?.length > 0 && (
                    <div className="space-y-1">
                      <div className="text-xs font-semibold mb-2 opacity-70">Detected Signals:</div>
                      {result.signals.map((s, i) => (
                        <div key={i} className="flex items-center justify-between text-xs">
                          <span className={s.impact === 'risk' ? 'text-red-400' : 'text-emerald-400'}>
                            {s.impact === 'risk' ? '⚠' : '✓'} {s.signal}
                          </span>
                          <span className={s.weight > 0 ? 'text-red-400' : 'text-emerald-400'}>
                            {s.weight > 0 ? '+' : ''}{(s.weight * 100).toFixed(0)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Contract-level FM scoring */}
              {result.fm_clauses !== undefined && (
                <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6 shadow-xl">
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h3 className="text-white font-bold text-lg flex items-center gap-2">
                        <Shield size={20} className="text-orange-400" />
                        Contract FM Clauses
                      </h3>
                      <p className="text-slate-400 text-xs mt-1">Click any clause to view detailed risk analysis</p>
                    </div>
                    <div className={`px-4 py-2 rounded-xl border-2 backdrop-blur-sm ${riskColor(result.risk_level)} shadow-lg`}>
                      <div className="text-2xl font-bold">{(result.overall_fm_risk_score * 100).toFixed(0)}%</div>
                      <div className="text-xs font-semibold opacity-90">{result.risk_level}</div>
                    </div>
                  </div>
                  {result.fm_clauses.length === 0
                    ? <div className="text-center py-8">
                        <Cloud size={48} className="mx-auto text-slate-600 mb-3" />
                        <p className="text-slate-500 text-sm">No force majeure clauses found in this contract.</p>
                      </div>
                    : <div className="space-y-4">
                        {result.fm_clauses.map((cl, i) => {
                          const isExpanded = expandedClauses.has(i);
                          const riskLevel = cl.score >= 0.7 ? 'HIGH' : cl.score >= 0.4 ? 'MEDIUM' : 'LOW';
                          const riskColorClass = cl.score >= 0.7 ? 'from-red-500/20 to-red-600/20 border-red-500/40' : cl.score >= 0.4 ? 'from-yellow-500/20 to-orange-500/20 border-yellow-500/40' : 'from-emerald-500/20 to-green-500/20 border-emerald-500/40';
                          const textColorClass = cl.score >= 0.7 ? 'text-red-400' : cl.score >= 0.4 ? 'text-yellow-400' : 'text-emerald-400';

                          return (
                            <div key={i} className={`group bg-gradient-to-br ${riskColorClass} border backdrop-blur-sm rounded-xl overflow-hidden hover:shadow-lg hover:scale-[1.01] transition-all duration-300 cursor-pointer ${isExpanded ? 'shadow-xl' : ''}`}>
                              <div className="p-4 bg-slate-900/40 backdrop-blur-sm" onClick={() => toggleClause(i)}>
                                <div className="flex items-center justify-between mb-3">
                                  <div className="flex items-center gap-3">
                                    <div className={`p-2 rounded-lg ${cl.score >= 0.7 ? 'bg-red-500/20' : cl.score >= 0.4 ? 'bg-yellow-500/20' : 'bg-emerald-500/20'}`}>
                                      {cl.score >= 0.7 ? <AlertTriangle size={18} className="text-red-400" /> :
                                       cl.score >= 0.4 ? <Activity size={18} className="text-yellow-400" /> :
                                       <CheckCircle size={18} className="text-emerald-400" />}
                                    </div>
                                    <div>
                                      <span className={`${textColorClass} text-base font-bold`}>{cl.type}</span>
                                      <div className="flex items-center gap-2 mt-0.5">
                                        <span className="text-slate-500 text-xs">Click to {isExpanded ? 'collapse' : 'expand'}</span>
                                        {isExpanded ? <ChevronUp size={14} className="text-slate-400" /> : <ChevronDown size={14} className="text-slate-400" />}
                                      </div>
                                    </div>
                                  </div>
                                  <div className="text-right">
                                    <div className={`text-3xl font-bold ${textColorClass}`}>{(cl.score * 100).toFixed(0)}%</div>
                                    <div className={`text-xs font-semibold ${textColorClass} opacity-80`}>{riskLevel}</div>
                                  </div>
                                </div>

                                <div className="relative">
                                  <div className="h-2 bg-slate-800/50 rounded-full overflow-hidden mb-3">
                                    <div
                                      className={`h-full transition-all duration-500 ${cl.score >= 0.7 ? 'bg-gradient-to-r from-red-500 to-red-600' : cl.score >= 0.4 ? 'bg-gradient-to-r from-yellow-500 to-orange-500' : 'bg-gradient-to-r from-emerald-500 to-green-500'}`}
                                      style={{ width: `${cl.score * 100}%` }}
                                    />
                                  </div>
                                </div>

                                <p className="text-slate-300 text-sm leading-relaxed mb-3 line-clamp-2">{cl.snippet}</p>

                                {!isExpanded && cl.signals?.length > 0 && (
                                  <div className="flex flex-wrap gap-2">
                                    {cl.signals.slice(0, 4).map((s, j) => (
                                      <span key={j} className={`text-xs px-2.5 py-1 rounded-lg font-medium transition-all ${s.impact === 'risk' ? 'bg-red-500/20 text-red-300 border border-red-500/30 hover:bg-red-500/30' : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/30'}`}>
                                        {s.signal}
                                      </span>
                                    ))}
                                    {cl.signals.length > 4 && (
                                      <span className="text-xs px-2.5 py-1 rounded-lg bg-slate-700/40 text-slate-400 border border-slate-600/40 font-medium">
                                        +{cl.signals.length - 4} more signals
                                      </span>
                                    )}
                                  </div>
                                )}
                              </div>

                              {/* Expanded Details */}
                              {isExpanded && (
                                <div className="border-t border-slate-700/50 bg-gradient-to-br from-slate-900/95 to-slate-950/95 backdrop-blur-sm animate-in slide-in-from-top duration-300">
                                  {/* Full Clause Text */}
                                  <div className="p-5 border-b border-slate-700/30">
                                    <h4 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                                      <div className="p-1.5 bg-cyan-500/20 rounded-lg">
                                        <FileText size={16} className="text-cyan-400" />
                                      </div>
                                      Full Clause Text
                                    </h4>
                                    <div className="bg-slate-950/60 border border-slate-700/40 rounded-xl p-4 shadow-inner">
                                      <p className="text-slate-300 text-sm leading-relaxed">
                                        {cl.text || cl.snippet}
                                      </p>
                                    </div>
                                  </div>

                                  {/* Risk Signals Breakdown */}
                                  {cl.signals?.length > 0 && (
                                    <div className="p-5 border-b border-slate-700/30">
                                      <div className="flex items-center justify-between mb-4">
                                        <h4 className="text-sm font-bold text-white flex items-center gap-2">
                                          <div className="p-1.5 bg-purple-500/20 rounded-lg">
                                            <Activity size={16} className="text-purple-400" />
                                          </div>
                                          Risk Signals Analysis
                                        </h4>
                                        <span className="text-xs px-3 py-1 bg-slate-800/60 border border-slate-700/40 rounded-full text-slate-400 font-semibold">
                                          {cl.signals.length} signals detected
                                        </span>
                                      </div>
                                      <div className="grid gap-2">
                                        {cl.signals.map((s, j) => {
                                          const isRisk = s.impact === 'risk';
                                          return (
                                            <div key={j} className={`group relative overflow-hidden rounded-lg border transition-all hover:scale-[1.02] ${isRisk ? 'bg-red-500/5 border-red-500/30 hover:bg-red-500/10' : 'bg-emerald-500/5 border-emerald-500/30 hover:bg-emerald-500/10'}`}>
                                              <div className="flex items-center justify-between p-3">
                                                <div className="flex items-center gap-3 flex-1">
                                                  <div className={`p-1.5 rounded-lg ${isRisk ? 'bg-red-500/20' : 'bg-emerald-500/20'}`}>
                                                    {isRisk ? <AlertTriangle size={14} className="text-red-400" /> : <CheckCircle size={14} className="text-emerald-400" />}
                                                  </div>
                                                  <span className={`text-sm font-medium ${isRisk ? 'text-red-300' : 'text-emerald-300'}`}>
                                                    {s.signal}
                                                  </span>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                  <div className={`px-3 py-1 rounded-lg font-bold text-sm ${isRisk ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
                                                    {s.weight > 0 ? '+' : ''}{(s.weight * 100).toFixed(0)}%
                                                  </div>
                                                </div>
                                              </div>
                                              <div className={`absolute bottom-0 left-0 h-0.5 transition-all ${isRisk ? 'bg-red-500/50' : 'bg-emerald-500/50'}`} style={{ width: `${Math.abs(s.weight) * 100}%` }} />
                                            </div>
                                          );
                                        })}
                                      </div>
                                    </div>
                                  )}

                                  {/* Risk Summary Stats */}
                                  <div className="p-5">
                                    <h4 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                                      <div className="p-1.5 bg-orange-500/20 rounded-lg">
                                        <Target size={16} className="text-orange-400" />
                                      </div>
                                      Risk Assessment Summary
                                    </h4>
                                    <div className="grid grid-cols-3 gap-3">
                                      <div className={`relative overflow-hidden rounded-xl p-4 border-2 ${cl.score >= 0.7 ? 'bg-red-500/10 border-red-500/40' : cl.score >= 0.4 ? 'bg-yellow-500/10 border-yellow-500/40' : 'bg-emerald-500/10 border-emerald-500/40'}`}>
                                        <div className="text-slate-400 text-xs font-semibold mb-2">Risk Score</div>
                                        <div className={`text-3xl font-bold ${textColorClass}`}>
                                          {(cl.score * 100).toFixed(0)}%
                                        </div>
                                        <div className={`absolute top-2 right-2 opacity-10 ${textColorClass}`}>
                                          <TrendingUp size={32} />
                                        </div>
                                      </div>
                                      <div className={`relative overflow-hidden rounded-xl p-4 border-2 ${cl.score >= 0.7 ? 'bg-red-500/10 border-red-500/40' : cl.score >= 0.4 ? 'bg-yellow-500/10 border-yellow-500/40' : 'bg-emerald-500/10 border-emerald-500/40'}`}>
                                        <div className="text-slate-400 text-xs font-semibold mb-2">Risk Level</div>
                                        <div className={`text-2xl font-bold ${textColorClass}`}>
                                          {riskLevel}
                                        </div>
                                        <div className={`absolute top-2 right-2 opacity-10 ${textColorClass}`}>
                                          <Shield size={32} />
                                        </div>
                                      </div>
                                      <div className={`relative overflow-hidden rounded-xl p-4 border-2 ${cl.score >= 0.7 ? 'bg-red-500/10 border-red-500/40' : cl.score >= 0.4 ? 'bg-yellow-500/10 border-yellow-500/40' : 'bg-emerald-500/10 border-emerald-500/40'}`}>
                                        <div className="text-slate-400 text-xs font-semibold mb-2">Signals</div>
                                        <div className={`text-3xl font-bold ${textColorClass}`}>
                                          {cl.signals?.length || 0}
                                        </div>
                                        <div className={`absolute top-2 right-2 opacity-10 ${textColorClass}`}>
                                          <Activity size={32} />
                                        </div>
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                  }
                </div>
              )}
            </div>
      )}
    </div>
  );
}

// ─── Tab 8: Clause Benchmark ──────────────────────────────────
const BENCHMARK_TYPES = ['force_majeure', 'liability', 'payment', 'termination', 'indemnity', 'confidentiality'];
const BENCHMARK_COLORS = { force_majeure: 'orange', liability: 'red', payment: 'emerald', termination: 'blue', indemnity: 'yellow', confidentiality: 'violet' };

function ClauseBenchmarkTab() {
  const [clauseText, setClauseText] = useState('');
  const [clauseType, setClauseType] = useState('force_majeure');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [warning, setWarning] = useState(null);

  // Auto-detect clause type from text using keywords
  const detectClauseType = (text) => {
    const lowerText = text.toLowerCase();

    const keywords = {
      force_majeure: ['force majeure', 'acts of god', 'war', 'terrorism', 'pandemic', 'earthquake', 'flood', 'civil unrest', 'government action', 'natural disaster', 'beyond reasonable control'],
      liability: ['liability', 'aggregate liability', 'total liability', 'liable for', 'damages', 'consequential damages', 'indirect damages', 'punitive damages', 'liability cap', 'fee cap', 'maximum liability'],
      payment: ['payment', 'invoice', 'fees', 'compensation', 'pay', 'paid', 'late payment', 'interest', 'non-refundable', 'payment terms', 'due date'],
      termination: ['termination', 'terminate', 'cancel', 'cancellation', 'notice period', 'written notice', 'material breach', 'end this agreement', 'terminate immediately'],
      indemnity: ['indemnify', 'indemnification', 'hold harmless', 'defend', 'third-party claims', 'arising from', 'negligence', 'willful misconduct'],
      confidentiality: ['confidential', 'confidentiality', 'proprietary information', 'non-disclosure', 'trade secrets', 'confidential information', 'disclose', 'disclosure']
    };

    const scores = {};
    for (const [type, keywordList] of Object.entries(keywords)) {
      scores[type] = keywordList.filter(keyword => lowerText.includes(keyword)).length;
    }

    // Return the type with highest keyword matches, or null if no matches
    const maxScore = Math.max(...Object.values(scores));
    if (maxScore === 0) return null;

    return Object.entries(scores).find(([_, score]) => score === maxScore)?.[0];
  };

  const EXAMPLES = {
    force_majeure: 'The Supplier shall not be liable for delays caused by acts of God, war, pandemic or government action. Notice shall be given within 30 days. The Buyer may terminate after 6 months.',
    liability: 'The total aggregate liability of either party shall not exceed the total fees paid in the preceding 12 months. Neither party shall be liable for indirect or consequential damages.',
    payment: 'Payment shall be made within 30 days of invoice. Late payments shall bear interest at 2% per month. All payments are non-refundable.',
    termination: 'Either party may terminate this agreement with 30 days written notice. The Company may terminate immediately for material breach.',
    indemnity: 'Each party shall indemnify the other against third-party claims arising from their own negligence or willful misconduct.',
    confidentiality: 'Each party agrees to keep confidential all proprietary information for a period of 5 years following disclosure.',
  };

  const run = async () => {
    if (!clauseText.trim()) return;

    // Detect actual clause type and warn if mismatch
    const detectedType = detectClauseType(clauseText);
    if (detectedType && detectedType !== clauseType) {
      setWarning({
        detected: detectedType,
        selected: clauseType
      });
      return; // Don't proceed with benchmark
    }

    setWarning(null);
    setLoading(true); setResult(null);
    try { setResult(await benchmarkClause(clauseText, clauseType)); }
    catch (e) { setResult({ error: e.response?.data?.error || 'Benchmark failed' }); }
    finally { setLoading(false); }
  };

  const proceedAnyway = async () => {
    setWarning(null);
    setLoading(true); setResult(null);
    try { setResult(await benchmarkClause(clauseText, clauseType)); }
    catch (e) { setResult({ error: e.response?.data?.error || 'Benchmark failed' }); }
    finally { setLoading(false); }
  };

  const switchToDetectedTab = () => {
    if (warning) {
      setClauseType(warning.detected);
      setWarning(null);
      setResult(null);
    }
  };

  const color = BENCHMARK_COLORS[clauseType] || 'cyan';

  const getScoreColor = (s) => s >= 70 ? 'text-emerald-400' : s >= 50 ? 'text-yellow-400' : 'text-red-400';
  const getRatingColor = (r) => ({
    GOOD: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40',
    NEEDS_IMPROVEMENT: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40',
    POOR: 'bg-red-500/20 text-red-400 border-red-500/40',
  }[r] || 'bg-slate-500/20 text-slate-400 border-slate-500/40');

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-white mb-1">Clause Benchmarking</h2>
        <p className="text-slate-400 text-sm">Compare your clause against industry-standard templates — see how it scores vs best practices</p>
      </div>

      <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5 space-y-4">
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
          {BENCHMARK_TYPES.map(t => (
            <button key={t} onClick={() => { setClauseType(t); setResult(null); setWarning(null); }}
              className={`p-3 rounded-xl border text-left transition capitalize text-sm ${clauseType === t
                ? 'border-cyan-500/60 bg-cyan-500/10 text-cyan-300'
                : 'border-slate-700/50 bg-slate-900/30 text-slate-400 hover:border-slate-600'
              }`}>
              {t.replace(/_/g, ' ')}
            </button>
          ))}
        </div>

        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="text-xs text-slate-400">Your Clause ({clauseType.replace(/_/g,' ')})</label>
            <button onClick={() => setClauseText(EXAMPLES[clauseType] || '')} className="text-xs text-cyan-400 hover:text-cyan-300">Use example</button>
          </div>
          <textarea value={clauseText} onChange={e => { setClauseText(e.target.value); setWarning(null); }}
            placeholder={`Paste your ${clauseType.replace(/_/g,' ')} clause here...`} rows={5}
            className="w-full px-3 py-2 bg-slate-900/60 border border-slate-600 text-white placeholder-slate-500 rounded-lg text-sm focus:outline-none focus:border-cyan-500 resize-none" />
        </div>

        <button onClick={run} disabled={loading || !clauseText.trim()}
          className="w-full py-3 bg-gradient-to-r from-cyan-600 to-blue-600 text-white rounded-lg hover:from-cyan-700 hover:to-blue-700 disabled:from-slate-600 disabled:to-slate-600 disabled:cursor-not-allowed transition font-medium flex items-center justify-center gap-2">
          {loading ? <RefreshCw size={16} className="animate-spin" /> : <Scale size={16} />}
          {loading ? 'Benchmarking...' : 'Benchmark Clause'}
        </button>
      </div>

      {/* Warning: Clause type mismatch */}
      {warning && (
        <div className="bg-orange-500/10 border-2 border-orange-500/40 rounded-xl p-5 space-y-4">
          <div className="flex items-start gap-3">
            <AlertTriangle size={24} className="text-orange-400 flex-shrink-0 mt-1" />
            <div className="flex-1">
              <h3 className="text-orange-400 font-semibold mb-2 flex items-center gap-2">
                Clause Type Mismatch Detected
              </h3>
              <p className="text-slate-300 text-sm mb-3">
                The text you pasted appears to be a <span className="font-semibold text-orange-300 capitalize">{warning.detected.replace(/_/g, ' ')}</span> clause,
                but you're on the <span className="font-semibold text-cyan-300 capitalize">{warning.selected.replace(/_/g, ' ')}</span> tab.
              </p>
              <p className="text-slate-400 text-xs mb-4">
                Benchmarking this clause against the wrong template will give incorrect results.
                The missing/present protections will be for {warning.selected.replace(/_/g, ' ')} clauses, not {warning.detected.replace(/_/g, ' ')} clauses.
              </p>
              <div className="flex flex-wrap gap-3">
                <button onClick={switchToDetectedTab}
                  className="px-4 py-2 bg-gradient-to-r from-orange-600 to-red-600 text-white rounded-lg hover:from-orange-700 hover:to-red-700 transition font-medium flex items-center gap-2 text-sm">
                  <CheckCircle size={16} />
                  Switch to {warning.detected.replace(/_/g, ' ')} tab
                </button>
                <button onClick={proceedAnyway}
                  className="px-4 py-2 bg-slate-700 text-slate-300 rounded-lg hover:bg-slate-600 transition font-medium text-sm">
                  Proceed anyway (not recommended)
                </button>
                <button onClick={() => setWarning(null)}
                  className="px-4 py-2 border border-slate-600 text-slate-400 rounded-lg hover:border-slate-500 hover:text-slate-300 transition font-medium text-sm">
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {loading && <LoadingSpinner text="Comparing against industry templates..." />}

      {result && !loading && (
        result.error
          ? <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl p-4">{result.error}</div>
          : <div className="space-y-4">
              {/* Score summary */}
              <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-white font-semibold">Benchmark Result</h3>
                    <p className="text-slate-400 text-xs mt-0.5 capitalize">{result.clause_type?.replace(/_/g,' ')} · compared against industry template</p>
                  </div>
                  <div className="text-right">
                    <div className={`text-4xl font-bold ${getScoreColor(result.clause_score)}`}>{result.clause_score?.toFixed(0)}</div>
                    <span className={`text-xs px-2 py-0.5 rounded-full border mt-1 inline-block ${getRatingColor(result.rating)}`}>{result.rating?.replace(/_/g,' ')}</span>
                  </div>
                </div>

                {/* Score bar: your score vs benchmark */}
                <div className="mb-4">
                  <div className="flex justify-between text-xs text-slate-400 mb-1">
                    <span>Your score</span>
                    <span>Industry benchmark: {result.benchmark_score?.toFixed(0)}</span>
                  </div>
                  <div className="relative h-3 bg-slate-700 rounded-full overflow-hidden">
                    <div className="absolute h-3 rounded-full bg-slate-500/50 transition-all" style={{ width: `${result.benchmark_score || 0}%` }} />
                    <div className={`absolute h-3 rounded-full transition-all ${(result.clause_score || 0) >= (result.benchmark_score || 0) ? 'bg-emerald-500' : 'bg-orange-500'}`} style={{ width: `${result.clause_score || 0}%` }} />
                  </div>
                  <div className="flex justify-between mt-1 text-xs">
                    <span className={getScoreColor(result.clause_score || 0)}>Your: {result.clause_score?.toFixed(0)}</span>
                    <span className="text-slate-500">Gap: {result.score_gap > 0 ? '+' : ''}{result.score_gap?.toFixed(1)} pts</span>
                    <span className="text-slate-500">Benchmark: {result.benchmark_score?.toFixed(0)}</span>
                  </div>
                </div>

                {result.recommendation && <p className="text-slate-300 text-sm">{result.recommendation}</p>}
                {result.llm_analysis && <p className="text-slate-400 text-xs mt-2 italic">{result.llm_analysis}</p>}
              </div>

              {/* Missing vs present key protections */}
              {(result.key_protections_missing?.length > 0 || result.key_protections_present?.length > 0) && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {result.key_protections_present?.length > 0 && (
                    <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-xl p-4">
                      <h4 className="text-emerald-400 font-semibold text-sm mb-3 flex items-center gap-2"><CheckCircle size={14} /> Present Protections</h4>
                      <ul className="space-y-1">
                        {result.key_protections_present.map((e, i) => (
                          <li key={i} className="text-slate-300 text-xs flex items-center gap-2"><span className="text-emerald-500">✓</span>{e}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {result.key_protections_missing?.length > 0 && (
                    <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-4">
                      <h4 className="text-red-400 font-semibold text-sm mb-3 flex items-center gap-2"><AlertTriangle size={14} /> Missing Protections</h4>
                      <ul className="space-y-1">
                        {result.key_protections_missing.map((e, i) => (
                          <li key={i} className="text-slate-300 text-xs flex items-center gap-2"><span className="text-red-500">✗</span>{e}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Industry standard template */}
              {result.benchmark_template && (
                <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4">
                  <h4 className="text-slate-300 font-semibold text-sm mb-3 flex items-center gap-2"><BookOpen size={14} className="text-slate-400" /> Industry Standard Template</h4>
                  <p className="text-slate-400 text-xs leading-relaxed">{result.benchmark_template}</p>
                </div>
              )}
            </div>
      )}
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────
export default function SmartContractSearch() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('prebuilt');
  const [stats, setStats] = useState(null);
  const [reclassifying, setReclassifying] = useState(false);
  const [reclassifyResult, setReclassifyResult] = useState(null);

  // #6 Redline diff state
  const [redlineData, setRedlineData]     = useState(null);
  // Navigate to negotiate tab with prefilled contract
  const [negotiateContract, setNegotiateContract] = useState(null);
  // Graph build toast
  const [graphToast, setGraphToast] = useState(null);

  useEffect(() => {
    getContractStats().then(setStats).catch(() => {});
  }, []);

  const handleRedline = (contract) => {
    // Show diff between first two clauses, or mock diff for demo
    const clauses = [];  // we'd fetch them; for now open the redline page
    navigate(`/contracts/${contract.id}/redline`);
  };

  const handleNegotiate = (contract) => {
    setNegotiateContract(contract);
    setActiveTab('negotiate');
  };

  const handleBuildGraph = async (contractId) => {
    setGraphToast({ status: 'loading', msg: 'Building graph...' });
    try {
      const res = await buildContractGraph(contractId, false);
      setGraphToast({ status: 'success', msg: `Graph built: ${res.clauses_extracted} clauses extracted` });
    } catch {
      setGraphToast({ status: 'error', msg: 'Graph build failed' });
    }
    setTimeout(() => setGraphToast(null), 4000);
  };

  const cardActions = { onRedline: handleRedline, onNegotiate: handleNegotiate, onBuildGraph: handleBuildGraph };

  const handleReclassify = async () => {
    setReclassifying(true);
    setReclassifyResult(null);
    try {
      const res = await bulkReclassify();
      setReclassifyResult(res);
      // Refresh stats after reclassify
      getContractStats().then(setStats).catch(() => {});
    } catch {
      setReclassifyResult({ error: 'Reclassification failed' });
    } finally {
      setReclassifying(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 p-6">
      <div className="max-w-7xl mx-auto space-y-6">

        {/* Toast notification */}
        {graphToast && (
          <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-xl border text-sm flex items-center gap-2 shadow-lg ${
            graphToast.status === 'success' ? 'bg-emerald-900/80 border-emerald-500/50 text-emerald-300' :
            graphToast.status === 'error'   ? 'bg-red-900/80 border-red-500/50 text-red-300' :
            'bg-slate-800 border-slate-600 text-slate-300'
          }`}>
            {graphToast.status === 'loading' && <RefreshCw size={14} className="animate-spin" />}
            {graphToast.status === 'success' && <CheckCircle size={14} />}
            {graphToast.status === 'error'   && <AlertTriangle size={14} />}
            {graphToast.msg}
          </div>
        )}

        {/* #6 Redline diff modal */}
        {redlineData && (
          <RedlineDiffViewer original={redlineData.original} redlined={redlineData.redlined} onClose={() => setRedlineData(null)} />
        )}

        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
                <Search size={16} className="text-white" />
              </div>
              <h1 className="text-2xl font-bold text-white">Smart Contract Search</h1>
              <span className="px-2 py-0.5 text-xs bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 rounded-full">NEW</span>
            </div>
            <p className="text-slate-400 text-sm ml-11">Pre-built Searches · AI Agent · Analytics · Negotiation AI · Graph Builder · Risk Scorer · Clause Benchmark</p>
          </div>
          <div className="flex items-center gap-6">
            {stats && (
              <div className="hidden lg:flex gap-5 text-sm">
                {[
                  { val: stats.total_contracts,         label: 'Contracts',  color: 'text-white' },
                  { val: stats.high_risk_contracts,     label: 'High Risk',  color: 'text-red-400' },
                  { val: stats.force_majeure_contracts, label: 'FM Clauses', color: 'text-orange-400' },
                  { val: `${stats.analysis_coverage}%`, label: 'Analyzed',  color: 'text-cyan-400' },
                ].map(({ val, label, color }) => (
                  <div key={label} className="text-center">
                    <div className={`text-xl font-bold ${color}`}>{val}</div>
                    <div className="text-slate-500 text-xs">{label}</div>
                  </div>
                ))}
              </div>
            )}
            <div className="flex flex-col items-end gap-1">
              <button
                onClick={handleReclassify}
                disabled={reclassifying}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-slate-700/60 hover:bg-slate-600/60 border border-slate-600/50 text-slate-300 rounded-lg transition disabled:opacity-50"
                title="Re-run contract type classification with improved AI classifier"
              >
                <RefreshCw size={12} className={reclassifying ? 'animate-spin' : ''} />
                {reclassifying ? 'Reclassifying...' : 'Fix Contract Types'}
              </button>
              {reclassifyResult && !reclassifyResult.error && (
                <span className="text-xs text-emerald-400">{reclassifyResult.updated} contracts updated</span>
              )}
              {reclassifyResult?.error && (
                <span className="text-xs text-red-400">{reclassifyResult.error}</span>
              )}
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-slate-800/60 border border-slate-700/50 rounded-xl p-1 overflow-x-auto">
          {TABS.map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium whitespace-nowrap transition-all duration-200 ${
                  isActive ? 'bg-cyan-600 text-white shadow-lg shadow-cyan-500/20' : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
                }`}>
                <Icon size={15} />{tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab content */}
        <div className="min-h-96">
          {activeTab === 'prebuilt'   && <PrebuiltTab  navigate={navigate} {...cardActions} />}
          {activeTab === 'semantic'   && <SemanticTab  navigate={navigate} {...cardActions} />}
          {activeTab === 'agent'      && <AgentTab     navigate={navigate} {...cardActions} />}
          {activeTab === 'analytics'  && <AnalyticsTab navigate={navigate} />}
          {activeTab === 'negotiate'  && <NegotiateTab initialContract={negotiateContract} />}
          {activeTab === 'graph'      && <GraphBuilderTab />}
          {activeTab === 'fmscorer'   && <FMScorerTab />}
          {activeTab === 'benchmark'  && <ClauseBenchmarkTab />}
        </div>
      </div>
    </div>
  );
}
