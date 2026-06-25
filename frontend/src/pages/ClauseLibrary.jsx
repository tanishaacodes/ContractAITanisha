import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft, Loader, AlertTriangle, CheckCircle, Sparkles, FileText,
  Database, Search, Brain, Zap, GitCompare, DollarSign, TrendingUp,
  FileEdit, Activity, BarChart2, Calendar, Layers, ChevronDown,
  ChevronUp, Info, Download, Minus
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid, Legend, ReferenceLine,
  AreaChart, Area, Cell
} from 'recharts';
import api from '../utils/api';
import ClauseLibraryTree from '../components/ClauseLibraryTree';

// ─── helpers ────────────────────────────────────────────────────────────────
const fmt = (v) =>
  v >= 1e6 ? `$${(v / 1e6).toFixed(1)}M` :
  v >= 1e3 ? `$${(v / 1e3).toFixed(0)}K` : `$${Number(v || 0).toFixed(0)}`;

const BAR_COLORS = ['#a855f7','#6366f1','#3b82f6','#06b6d4','#10b981','#f59e0b','#f97316','#ef4444'];
const OUTLOOK_BG = { HIGH:'bg-red-900/20 border-red-700', MEDIUM:'bg-yellow-900/20 border-yellow-700', LOW:'bg-green-900/20 border-green-700' };
const OUTLOOK_COLOR = { HIGH:'text-red-400', MEDIUM:'text-yellow-400', LOW:'text-green-400' };
const METHOD_BADGE = { xgboost:'bg-blue-900/40 text-blue-300', linear:'bg-purple-900/40 text-purple-300', exp_smoothing:'bg-slate-700 text-slate-300', constant:'bg-slate-700 text-slate-400' };

// ─── Diff viewer for redline ─────────────────────────────────────────────────
function DiffViewer({ diff }) {
  if (!diff?.length) return <p className="text-slate-500 text-xs">No diff available</p>;
  return (
    <p className="text-xs leading-relaxed font-mono whitespace-pre-wrap">
      {diff.map((t, i) =>
        t.type === 'delete' ? <span key={i} className="bg-red-900/50 text-red-300 line-through px-0.5">{t.text} </span> :
        t.type === 'insert' ? <span key={i} className="bg-green-900/50 text-green-300 px-0.5">{t.text} </span> :
        <span key={i} className="text-slate-400">{t.text} </span>
      )}
    </p>
  );
}

// ─── Redline clause card ─────────────────────────────────────────────────────
function RedlineCard({ r, index }) {
  const [expanded, setExpanded] = useState(false);
  const RISK_COLOR = { HIGH:'text-red-400', MEDIUM:'text-yellow-400', LOW:'text-green-400', UNKNOWN:'text-slate-400' };
  return (
    <div className={`border rounded-xl transition ${r.needs_redline ? 'border-red-800 bg-red-900/10' : 'border-slate-700 bg-slate-900'}`}>
      <button className="w-full flex items-center justify-between p-4 text-left" onClick={() => setExpanded(e => !e)}>
        <div className="flex items-center gap-3 min-w-0">
          <span className="text-slate-500 text-sm w-6 flex-shrink-0">#{index + 1}</span>
          <div className="min-w-0">
            <p className="text-white font-semibold text-sm truncate">{r.clause_name || r.clause_type}</p>
            <p className="text-xs text-slate-400">{r.clause_type} · Similarity: {(r.similarity * 100).toFixed(1)}%</p>
          </div>
        </div>
        <div className="flex items-center gap-3 flex-shrink-0 ml-3">
          <span className={`text-xs font-semibold ${RISK_COLOR[r.risk_level] || 'text-slate-400'}`}>{r.risk_level}</span>
          {r.needs_redline
            ? <span className="flex items-center gap-1 text-xs text-red-400 bg-red-900/30 px-2 py-0.5 rounded-full border border-red-800"><AlertTriangle className="w-3 h-3" />REDLINE</span>
            : <span className="flex items-center gap-1 text-xs text-green-400 bg-green-900/30 px-2 py-0.5 rounded-full border border-green-800"><CheckCircle className="w-3 h-3" />OK</span>
          }
          {expanded ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
        </div>
      </button>
      {expanded && (
        <div className="px-4 pb-4 space-y-4 border-t border-slate-800 pt-4">
          <div>
            <div className="flex justify-between text-xs text-slate-400 mb-1">
              <span>Similarity to Standard</span>
              <span className={r.similarity < 0.75 ? 'text-red-400' : 'text-green-400'}>{(r.similarity * 100).toFixed(1)}%</span>
            </div>
            <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
              <div className={`h-full rounded-full ${r.similarity > 0.75 ? 'bg-green-500' : r.similarity > 0.5 ? 'bg-yellow-500' : 'bg-red-500'}`} style={{ width: `${r.similarity * 100}%` }} />
            </div>
          </div>
          {r.needs_redline && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs font-semibold text-red-400 mb-2">Original</p>
                  <div className="bg-slate-800/60 rounded-lg p-3 text-xs text-slate-300 max-h-32 overflow-y-auto">{r.original_text || 'N/A'}</div>
                </div>
                <div>
                  <p className="text-xs font-semibold text-green-400 mb-2">Suggested Redline</p>
                  <div className="bg-slate-800/60 rounded-lg p-3 text-xs text-slate-300 max-h-32 overflow-y-auto">{r.suggested_text || 'N/A'}</div>
                </div>
              </div>
              {r.diff?.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-purple-400 mb-2">Inline Diff</p>
                  <div className="bg-slate-800/60 rounded-lg p-3 max-h-28 overflow-y-auto"><DiffViewer diff={r.diff} /></div>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
export default function ClauseLibrary() {
  const navigate = useNavigate();
  const { contractId } = useParams();

  // ── clause library state ──
  const [contract, setContract] = useState(null);
  const [library, setLibrary] = useState(null);
  const [selectedClause, setSelectedClause] = useState(null);
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [processingStats, setProcessingStats] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [searchMode, setSearchMode] = useState('hybrid');
  const [clusterMethod, setClusterMethod] = useState('kmeans');

  // ── tab ──
  const [activeTab, setActiveTab] = useState('clauses');

  // ── drift state ──
  const [driftSummary, setDriftSummary] = useState([]);
  const [driftLoading, setDriftLoading] = useState(false);
  const [driftSelected, setDriftSelected] = useState(null);
  const [driftDetail, setDriftDetail] = useState(null);
  const [driftTimeline, setDriftTimeline] = useState([]);
  const [driftSubTab, setDriftSubTab] = useState('overview');

  // ── CFO state ──
  const [cfoKpis, setCfoKpis] = useState(null);
  const [lossByType, setLossByType] = useState([]);
  const [lossByContract, setLossByContract] = useState([]);
  const [cashFlow, setCashFlow] = useState([]);
  const [heatmap, setHeatmap] = useState(null);
  const [cfoLoading, setCfoLoading] = useState(false);
  const [cfoSubTab, setCfoSubTab] = useState('summary');
  const [cfoScope, setCfoScope] = useState('this'); // Always show 'this' contract only

  // ── predictive risk state ──
  const [forecasts, setForecasts] = useState([]);
  const [predSelected, setPredSelected] = useState(null);
  const [predDetail, setPredDetail] = useState(null);
  const [predLoading, setPredLoading] = useState(false);
  const [predDetailLoading, setPredDetailLoading] = useState(false);
  const [horizon, setHorizon] = useState(6);

  // ── redline state ──
  const [redlines, setRedlines] = useState(null);
  const [redlineLoading, setRedlineLoading] = useState(false);
  const [redlineError, setRedlineError] = useState('');
  const [redlineThreshold, setRedlineThreshold] = useState(0.75);
  const [genSuggestions, setGenSuggestions] = useState(true);
  const [redlineFilter, setRedlineFilter] = useState('all');
  const [exporting, setExporting] = useState(false);

  // ─────────────────────────────────────────────────────────────────────────
  useEffect(() => { if (contractId) loadClauseLibrary(); }, [contractId]);

  // Lazy-load tab data when switching
  useEffect(() => {
    if (activeTab === 'drift' && !driftSummary.length && !driftLoading) loadDrift();
    if (activeTab === 'cfo' && !cfoKpis && !cfoLoading) loadCFO();
    if (activeTab === 'predictive' && !forecasts.length && !predLoading) loadForecasts();
  }, [activeTab]);

  // ── loaders ──────────────────────────────────────────────────────────────
  const loadClauseLibrary = async () => {
    try {
      setLoading(true); setError('');
      const r = await api.get(`/contracts/${contractId}/clause-library`);
      setContract({ id: r.data.contract_id, name: r.data.contract_name });
      setLibrary(r.data.library);
    } catch (err) {
      setError(err.response?.status === 404
        ? 'Clause library not found. Click "Process Contract" to generate it.'
        : err.response?.data?.error || 'Failed to load clause library');
    } finally { setLoading(false); }
  };

  const processClauseLibrary = async () => {
    try {
      setProcessing(true); setError(''); setSuccess('');
      const r = await api.post(`/contracts/${contractId}/clause-library/process`, { cluster_method: clusterMethod });
      setSuccess('Clause library processed successfully!');
      setProcessingStats(r.data.data);
      setTimeout(loadClauseLibrary, 1000);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to process clause library');
    } finally { setProcessing(false); }
  };

  const handleSemanticSearch = async () => {
    if (!searchQuery.trim()) return;
    try {
      setSearching(true); setError('');
      const r = await api.post('/clause-library/hybrid-search', { query: searchQuery, contract_id: contractId, limit: 10, mode: searchMode });
      if (r.data.error) { setError(r.data.error); setSearchResults([]); }
      else setSearchResults(r.data.results);
    } catch (err) {
      setError(err.response?.data?.error || 'Search failed');
    } finally { setSearching(false); }
  };

  const loadDrift = async () => {
    setDriftLoading(true);
    try {
      const r = await api.get('/clause-library/drift/summary/');
      setDriftSummary(r.data.summary || []);
    } catch (e) { console.error(e); }
    finally { setDriftLoading(false); }
  };

  const loadDriftDetail = async (item) => {
    const displayName = item?.clause_type || item;
    const rawType = item?.raw_clause_type || item;
    setDriftSelected(displayName);
    setDriftDetail(null); // show loading state
    try {
      const [det, tl] = await Promise.all([
        api.get('/clause-library/drift/type/', { params: { clause_type: rawType } }),
        api.get('/clause-library/drift/timeline/', { params: { clause_type: rawType } }),
      ]);
      setDriftDetail({ ...det.data, clause_type: displayName });
      setDriftTimeline(tl.data.timeline || []);
    } catch (e) { console.error('Drift detail error:', e); }
  };

  const loadCFO = async (scope = cfoScope) => {
    setCfoLoading(true);
    const params = scope === 'this' && contractId ? { contract_id: contractId } : {};
    try {
      const [sumR, typeR, contR, cfR, hmR] = await Promise.all([
        api.get('/analytics/cfo/summary/', { params }),
        api.get('/analytics/cfo/loss-by-type/', { params }),
        api.get('/analytics/cfo/loss-by-contract/', { params }),
        api.get('/analytics/cfo/cash-flow/', { params }),
        api.get('/analytics/cfo/risk-heatmap/', { params }),
      ]);
      setCfoKpis({ ...sumR.data.kpis, top_exposure_clauses: sumR.data.top_exposure_clauses || [] });
      setLossByType(typeR.data.data || []);
      setLossByContract(contR.data.data || []);
      setCashFlow(cfR.data.projection || []);
      setHeatmap(hmR.data);
    } catch (e) { console.error(e); }
    finally { setCfoLoading(false); }
  };

  const switchCfoScope = (s) => {
    setCfoScope(s);
    setCfoKpis(null); // reset so it reloads
    loadCFO(s);
  };

  const loadForecasts = async () => {
    setPredLoading(true);
    try {
      const r = await api.get(`/analytics/predictive-risk/?horizon=${horizon}`);
      setForecasts(r.data.forecasts || []);
    } catch (e) { console.error(e); }
    finally { setPredLoading(false); }
  };

  const loadPredDetail = async (clauseType) => {
    setPredDetailLoading(true); setPredSelected(clauseType);
    try {
      const r = await api.get(`/analytics/predictive-risk/${encodeURIComponent(clauseType)}/?horizon=${horizon}`);
      setPredDetail(r.data);
    } catch (e) { console.error(e); }
    finally { setPredDetailLoading(false); }
  };

  const runRedline = async () => {
    if (!contractId) return;
    try {
      setRedlineLoading(true); setRedlineError('');
      const r = await api.post(`/contracts/${contractId}/redline/`, { threshold: redlineThreshold, generate_suggestions: genSuggestions });
      setRedlines(r.data);
    } catch (e) {
      setRedlineError(e.response?.data?.error || 'Redline analysis failed');
    } finally { setRedlineLoading(false); }
  };

  const exportRedline = async () => {
    if (!redlines) return;
    try {
      setExporting(true);
      const r = await api.post(`/contracts/${contractId}/redline/export/`, { redlines: redlines.redlines }, { responseType: 'blob' });
      const url = URL.createObjectURL(r.data);
      const a = document.createElement('a'); a.href = url; a.download = `redline_${contractId}.txt`; a.click();
    } catch (e) { console.error(e); }
    finally { setExporting(false); }
  };

  // ── helpers ───────────────────────────────────────────────────────────────
  const buildPredChart = (f) => {
    if (!f) return [];
    return [
      ...(f.history || []).map(h => ({ month: h.month, actual: h.avg_risk, predicted: null, lower: null, upper: null })),
      ...(f.forecast || []).map(p => ({ month: p.month, actual: null, predicted: p.predicted_risk, lower: p.lower, upper: p.upper })),
    ];
  };

  const filteredRedlines = redlines?.redlines?.filter(r =>
    redlineFilter === 'drifted' ? r.needs_redline :
    redlineFilter === 'ok' ? !r.needs_redline : true
  ) || [];

  // ─────────────────────────────────────────────────────────────────────────
  if (loading) return (
    <div className="flex items-center justify-center min-h-screen">
      <Loader className="w-12 h-12 text-purple-400 animate-spin" />
    </div>
  );

  const TABS = [
    { id: 'clauses',    label: 'Clauses',          icon: FileText  },
    { id: 'drift',      label: 'Drift Detection',   icon: GitCompare },
    { id: 'redline',    label: 'Auto Redline',       icon: FileEdit  },
  ];

  return (
    <div className="space-y-5 pb-12">

      {/* ── Header ── */}
      <div className="flex items-center gap-4">
        <button onClick={() => navigate('/dashboard')} className="p-2 hover:bg-slate-800 rounded-lg">
          <ArrowLeft className="w-6 h-6 text-blue-400" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-1">
            <Brain className="w-8 h-8 text-purple-400" />
            <h1 className="text-3xl font-bold text-white">AI Clause Library</h1>
          </div>
          {contract && <p className="text-slate-400 text-sm">{contract.name}</p>}
        </div>
      </div>

      {/* ── Tabs ── */}
      <div className="flex gap-1 bg-slate-900 border border-slate-800 rounded-xl p-1 overflow-x-auto">
        {TABS.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold whitespace-nowrap transition flex-1 justify-center ${
              activeTab === t.id
                ? 'bg-purple-600 text-white shadow'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}>
            <t.icon className="w-4 h-4" />
            {t.label}
          </button>
        ))}
      </div>

      {/* ── Alerts ── */}
      {error && (
        <div className="bg-red-900/20 border border-red-800 rounded-xl p-4 flex gap-3">
          <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
          <p className="text-red-200 text-sm">{error}</p>
        </div>
      )}
      {success && (
        <div className="bg-green-900/20 border border-green-800 rounded-xl p-4 flex gap-3">
          <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
          <p className="text-green-200 text-sm">{success}</p>
        </div>
      )}

      {/* ════════════════════════════════════════════════════════════════════
          TAB 1 — CLAUSES
      ════════════════════════════════════════════════════════════════════ */}
      {activeTab === 'clauses' && (
        <div className="space-y-5">
          {/* processing stats */}
          {processingStats && (
            <div className="bg-gradient-to-br from-purple-900/20 to-blue-900/20 border border-purple-800 rounded-xl p-5">
              <div className="flex items-center gap-2 mb-3">
                <Zap className="w-5 h-5 text-yellow-400" />
                <h2 className="text-lg font-bold text-white">Processing Results</h2>
              </div>
              <div className="grid grid-cols-4 gap-3">
                {[
                  { label: 'Total Clauses', value: processingStats.total_clauses, color: 'text-white' },
                  { label: 'AI Categories', value: processingStats.clusters, color: 'text-purple-400' },
                  { label: 'Time', value: `${processingStats.processing_time?.toFixed(2)}s`, color: 'text-blue-400' },
                  { label: 'Vector DB', value: processingStats.qdrant_storage ? 'Stored' : 'Skipped', color: processingStats.qdrant_storage ? 'text-green-400' : 'text-slate-500' },
                ].map(k => (
                  <div key={k.label} className="bg-slate-800/50 rounded-lg p-3 text-center">
                    <p className={`text-xl font-bold ${k.color}`}>{k.value}</p>
                    <p className="text-xs text-slate-400 mt-0.5">{k.label}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {!library ? (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center">
              <FileText className="w-16 h-16 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400 text-lg mb-2">No clause library generated yet</p>
              <p className="text-slate-500 text-sm mb-6">Process this contract to extract, cluster and name all clauses using AI</p>
              {/* cluster method */}
              <div className="flex justify-center gap-2 mb-3">
                {['kmeans', 'lda'].map(m => (
                  <button key={m} onClick={() => setClusterMethod(m)}
                    className={`px-4 py-1.5 rounded-lg text-sm font-semibold border transition ${
                      clusterMethod === m ? 'bg-purple-600 border-purple-500 text-white' : 'border-slate-700 text-slate-400 hover:border-slate-500'
                    }`}>
                    {m === 'kmeans' ? 'KMeans (BERT)' : 'LDA (Topic Modeling)'}
                  </button>
                ))}
              </div>
              <div className="max-w-md mx-auto mb-5 text-left bg-slate-800/60 border border-slate-700 rounded-xl p-4 text-xs text-slate-300 space-y-2">
                {clusterMethod === 'kmeans' ? (
                  <>
                    <p className="font-semibold text-purple-300">KMeans (BERT Semantic)</p>
                    <p>Groups clauses by <span className="text-white font-medium">semantic meaning</span> using BERT embeddings. Two clauses about "payment liability" and "financial obligation" will cluster together even if they use different words.</p>
                    <p className="text-slate-400">Cluster names: generated by AI — human-readable labels like <span className="text-white">"Payment Terms"</span></p>
                  </>
                ) : (
                  <>
                    <p className="font-semibold text-blue-300">LDA (Topic Modeling)</p>
                    <p>Groups clauses by <span className="text-white font-medium">shared keywords</span> using Latent Dirichlet Allocation. Each cluster = a statistical topic of co-occurring legal terms.</p>
                    <p className="text-slate-400">Cluster names: top 3 topic words e.g. <span className="text-white">"Payment / Shall / Party"</span> — different groupings than KMeans</p>
                  </>
                )}
              </div>
              <button onClick={processClauseLibrary} disabled={processing}
                className={`px-6 py-3 rounded-lg font-semibold transition ${processing ? 'bg-slate-700 text-slate-500 cursor-not-allowed' : 'bg-purple-600 hover:bg-purple-700 text-white'}`}>
                {processing
                  ? <span className="flex items-center gap-2"><Loader className="w-5 h-5 animate-spin" />Processing...</span>
                  : <span className="flex items-center gap-2"><Brain className="w-5 h-5" />Process Contract & Build Library</span>
                }
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
              {/* Tree */}
              <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5">
                <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                  <h2 className="text-lg font-bold text-white">Organized Clause Tree</h2>
                  <div className="flex items-center gap-2">
                    <div className="flex flex-col gap-1">
                      <div className="flex items-center gap-1 bg-slate-800 rounded-lg p-1">
                        {['kmeans', 'lda'].map(m => (
                          <button key={m} onClick={() => setClusterMethod(m)}
                            className={`px-3 py-1 rounded text-xs font-semibold transition ${clusterMethod === m ? 'bg-purple-600 text-white' : 'text-slate-400 hover:text-white'}`}>
                            {m === 'kmeans' ? 'KMeans' : 'LDA'}
                          </button>
                        ))}
                      </div>
                      <p className="text-slate-500 text-xs text-center">
                        {clusterMethod === 'kmeans' ? 'BERT semantic grouping' : 'Keyword topic grouping'}
                      </p>
                    </div>
                    <button onClick={processClauseLibrary} disabled={processing}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${processing ? 'bg-slate-700 text-slate-500 cursor-not-allowed' : 'bg-purple-600 hover:bg-purple-700 text-white'}`}>
                      {processing ? <span className="flex items-center gap-1"><Loader className="w-3 h-3 animate-spin" />Processing...</span> : 'Reprocess'}
                    </button>
                  </div>
                </div>
                <ClauseLibraryTree library={library} onClauseSelect={setSelectedClause} selectedClauseId={selectedClause?.id} />
              </div>

              {/* Search + Details */}
              <div className="space-y-5">
                {/* Search */}
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Search className="w-4 h-4 text-blue-400" />
                    <h3 className="font-bold text-white text-sm">Hybrid Search</h3>
                  </div>
                  <div className="flex gap-1 bg-slate-800 rounded-lg p-1 mb-3">
                    {['bm25','bert','hybrid'].map(m => (
                      <button key={m} onClick={() => setSearchMode(m)}
                        className={`flex-1 py-1 rounded text-xs font-semibold transition ${searchMode === m ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}>
                        {m.toUpperCase()}
                      </button>
                    ))}
                  </div>
                  <input type="text" value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                    onKeyPress={e => e.key === 'Enter' && handleSemanticSearch()}
                    placeholder="Search similar clauses..."
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-300 placeholder-slate-500 text-sm focus:outline-none focus:border-blue-500 mb-2" />
                  <button onClick={handleSemanticSearch} disabled={searching || !searchQuery.trim()}
                    className={`w-full py-2 rounded-lg text-sm font-semibold transition ${searching || !searchQuery.trim() ? 'bg-slate-700 text-slate-500 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 text-white'}`}>
                    {searching ? <span className="flex items-center justify-center gap-2"><Loader className="w-4 h-4 animate-spin" />Searching...</span> : `Search (${searchMode.toUpperCase()})`}
                  </button>
                  {searchResults.length > 0 && (
                    <div className="mt-3 space-y-2 max-h-72 overflow-y-auto">
                      {searchResults.map((r, i) => (
                        <div key={r.clause_id || i} className="bg-slate-800/50 rounded-lg p-3 border border-slate-700 hover:border-blue-500 transition cursor-pointer">
                          <div className="flex items-center justify-between gap-2 mb-1">
                            <div className="flex items-center gap-1.5 min-w-0">
                              {r.llm_rank && <span className="text-xs text-purple-400 font-bold flex-shrink-0">#{r.llm_rank}</span>}
                              <span className="text-xs font-semibold text-white truncate">{r.clause_name || r.clause_type || 'Clause'}</span>
                            </div>
                            <div className="flex items-center gap-1 flex-shrink-0">
                              {r.risk_level && (
                                <span className={`text-xs px-1.5 py-0.5 rounded font-bold ${r.risk_level === 'HIGH' ? 'bg-red-900/60 text-red-300' : r.risk_level === 'MEDIUM' ? 'bg-yellow-900/60 text-yellow-300' : 'bg-green-900/60 text-green-300'}`}>{r.risk_level}</span>
                              )}
                              <span className={`text-xs px-1.5 py-0.5 rounded font-bold ${r.source === 'GraphRAG' ? 'bg-purple-900/60 text-purple-300' : r.source === 'BERT' ? 'bg-blue-900/60 text-blue-300' : 'bg-slate-700 text-slate-300'}`}>{r.source || searchMode.toUpperCase()}</span>
                            </div>
                          </div>
                          <p className="text-xs text-slate-400 line-clamp-2">{r.clause_text || r.text || ''}</p>
                          <div className="flex items-center justify-between mt-1.5">
                            {r.contract_name && <p className="text-xs text-slate-600 truncate">📄 {r.contract_name}</p>}
                            {r.llm_score > 0 && (
                              <span className="text-xs text-green-400 flex-shrink-0 ml-auto">🤖 {(r.final_score * 100).toFixed(0)}%</span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Selected clause */}
                {selectedClause && (
                  <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <FileText className="w-4 h-4 text-green-400" />
                      <h3 className="font-bold text-white text-sm">Clause Details</h3>
                    </div>
                    <div className="space-y-2 text-sm">
                      <p className="text-slate-400 text-xs">Name</p>
                      <p className="font-semibold text-white">{selectedClause.clause_name}</p>
                      <p className="text-slate-400 text-xs mt-2">Category</p>
                      <p className="font-semibold text-purple-400">{selectedClause.clause_type}</p>
                      {selectedClause.confidence != null && (
                        <>
                          <p className="text-slate-400 text-xs mt-2">Confidence</p>
                          <div className="flex items-center gap-2">
                            <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                              <div className="h-full bg-gradient-to-r from-blue-500 to-purple-500" style={{ width: `${selectedClause.confidence * 100}%` }} />
                            </div>
                            <span className="text-xs text-white">{(selectedClause.confidence * 100).toFixed(0)}%</span>
                          </div>
                        </>
                      )}
                      {selectedClause.extracted_text && (
                        <>
                          <p className="text-slate-400 text-xs mt-2">Extracted Text</p>
                          <div className="bg-slate-800 rounded p-2 max-h-40 overflow-y-auto">
                            <p className="text-xs text-slate-300">{selectedClause.extracted_text}</p>
                          </div>
                        </>
                      )}
                      <div className="flex gap-2 pt-2">
                        {selectedClause.found && <span className="px-2 py-0.5 bg-green-900/50 text-green-300 rounded text-xs border border-green-800">Found</span>}
                        {selectedClause.has_embedding && <span className="px-2 py-0.5 bg-purple-900/50 text-purple-300 rounded text-xs border border-purple-800"><Database className="w-3 h-3 inline mr-1" />Vector</span>}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ════════════════════════════════════════════════════════════════════
          TAB 2 — DRIFT DETECTION
      ════════════════════════════════════════════════════════════════════ */}
      {activeTab === 'drift' && (
        <div className="space-y-4">
          {/* scope banner */}
          <div className="flex items-center gap-3 bg-blue-950/40 border border-blue-800/50 rounded-xl px-4 py-3">
            <GitCompare className="w-4 h-4 text-blue-400 flex-shrink-0" />
            <div className="flex-1 text-sm">
              <span className="text-blue-300 font-semibold">Cross-Contract Analysis</span>
              <span className="text-slate-400"> — comparing clause language across </span>
              <span className="text-white font-semibold">all your contracts</span>
              <span className="text-slate-400">, not just this one. Drift = how far a clause has deviated from your standard template (highest-confidence version).</span>
            </div>
          </div>

          {driftLoading ? (
            <div className="flex flex-col items-center justify-center py-20 gap-3">
              <Loader className="w-10 h-10 text-purple-400 animate-spin" />
              <p className="text-slate-400 text-sm">Running BERT cosine similarity across all contracts...</p>
            </div>
          ) : (
            <>
              {/* ── KPI banner ── */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                {[
                  { label: 'Critical Drift', value: driftSummary.filter(s=>s.status==='critical').length, color:'text-red-400', bar:'bg-red-500', bg:'from-red-900/30 to-red-900/10 border-red-800' },
                  { label: 'Warning',         value: driftSummary.filter(s=>s.status==='warning').length,  color:'text-yellow-400', bar:'bg-yellow-500', bg:'from-yellow-900/30 to-yellow-900/10 border-yellow-800' },
                  { label: 'Healthy',         value: driftSummary.filter(s=>s.status==='healthy').length,  color:'text-green-400', bar:'bg-green-500', bg:'from-green-900/30 to-green-900/10 border-green-800' },
                  { label: 'Total Types',     value: driftSummary.length, color:'text-blue-400', bar:'bg-blue-500', bg:'from-blue-900/30 to-blue-900/10 border-blue-800' },
                  { label: 'Avg Drift Rate',  value: driftSummary.length ? `${(driftSummary.reduce((a,s)=>a+s.drift_rate,0)/driftSummary.length*100).toFixed(0)}%` : '—', color:'text-purple-400', bar:'bg-purple-500', bg:'from-purple-900/30 to-purple-900/10 border-purple-800' },
                ].map(k => (
                  <div key={k.label} className={`bg-gradient-to-br ${k.bg} border rounded-xl p-4`}>
                    <p className={`text-2xl font-bold ${k.color}`}>{k.value}</p>
                    <p className="text-slate-400 text-xs mt-0.5">{k.label}</p>
                  </div>
                ))}
              </div>

              {/* ── Main 2-col layout: list + detail ── */}
              <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">

                {/* LEFT — clause type list + bar chart */}
                <div className="lg:col-span-2 space-y-3">
                  {/* mini bar chart */}
                  {driftSummary.length > 0 && (
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                      <p className="text-xs font-bold text-slate-400 uppercase tracking-wide mb-3 flex items-center gap-2">
                        <BarChart2 className="w-3.5 h-3.5 text-purple-400" />Drift Rate by Clause Type
                      </p>
                      <ResponsiveContainer width="100%" height={160}>
                        <BarChart data={driftSummary} barSize={14} margin={{left:-10}}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                          <XAxis dataKey="clause_type" tick={false} />
                          <YAxis tick={{ fill: '#64748b', fontSize: 9 }} tickFormatter={v=>`${(v*100).toFixed(0)}%`} />
                          <Tooltip
                            contentStyle={{ background:'#0f172a', border:'1px solid #334155', borderRadius:8, fontSize:11 }}
                            formatter={v=>[`${(v*100).toFixed(1)}%`,'Drift']}
                            labelFormatter={l=>l}
                          />
                          <ReferenceLine y={0.5} stroke="#ef4444" strokeDasharray="3 3" strokeWidth={1} />
                          <Bar dataKey="drift_rate" radius={[3,3,0,0]}>
                            {driftSummary.map((s,i) => (
                              <Cell key={i} fill={s.status==='critical'?'#ef4444':s.status==='warning'?'#f59e0b':'#10b981'} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                      {/* legend */}
                      <div className="flex items-center gap-4 mt-2 text-xs text-slate-400">
                        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-red-500 inline-block" />Critical (&gt;50%)</span>
                        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-yellow-500 inline-block" />Warning (20-50%)</span>
                        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-green-500 inline-block" />Healthy (&lt;20%)</span>
                      </div>
                    </div>
                  )}

                  {/* clause type cards list */}
                  <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                    <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
                      <p className="text-xs font-bold text-slate-400 uppercase tracking-wide">Clause Types ({driftSummary.length})</p>
                      <p className="text-xs text-slate-500">Click to inspect</p>
                    </div>
                    <div className="max-h-[420px] overflow-y-auto divide-y divide-slate-800/60">
                      {driftSummary.map(s => {
                        const isSelected = driftSelected === s.clause_type;
                        return (
                          <button key={s.clause_type} onClick={() => loadDriftDetail(s)}
                            className={`w-full px-4 py-3 text-left transition hover:bg-slate-800/60 ${isSelected ? 'bg-slate-800 border-l-2 border-l-purple-500' : ''}`}>
                            <div className="flex items-center justify-between mb-1.5">
                              <span className={`text-sm font-semibold truncate pr-2 ${isSelected ? 'text-purple-300' : 'text-white'}`}>{s.clause_type}</span>
                              <span className={`text-xs font-bold px-2 py-0.5 rounded-full flex-shrink-0 ${
                                s.status==='critical' ? 'bg-red-900/50 text-red-400 border border-red-700' :
                                s.status==='warning'  ? 'bg-yellow-900/50 text-yellow-400 border border-yellow-700' :
                                'bg-green-900/50 text-green-400 border border-green-700'
                              }`}>{s.status.toUpperCase()}</span>
                            </div>
                            {/* drift bar */}
                            <div className="flex items-center gap-2">
                              <div className="flex-1 h-1 bg-slate-700 rounded-full overflow-hidden">
                                <div className={`h-full rounded-full transition-all ${
                                  s.status==='critical'?'bg-red-500':s.status==='warning'?'bg-yellow-500':'bg-green-500'
                                }`} style={{width:`${s.drift_rate*100}%`}} />
                              </div>
                              <span className={`text-xs font-bold w-9 text-right flex-shrink-0 ${
                                s.status==='critical'?'text-red-400':s.status==='warning'?'text-yellow-400':'text-green-400'
                              }`}>{(s.drift_rate*100).toFixed(0)}%</span>
                            </div>
                            <div className="flex items-center gap-4 mt-1.5 text-xs text-slate-500">
                              <span>{s.drifted_count}/{s.total_count} drifted</span>
                              <span>Sim: {s.avg_similarity ? `${(s.avg_similarity*100).toFixed(0)}%` : '—'}</span>
                            </div>
                          </button>
                        );
                      })}
                      {!driftSummary.length && (
                        <div className="px-4 py-10 text-center text-slate-500 text-sm">
                          No drift data.<br />Process a contract first.
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* RIGHT — detail panel */}
                <div className="lg:col-span-3 space-y-3">
                  {!driftDetail && !driftSelected ? (
                    <div className="bg-slate-900 border border-slate-800 rounded-xl flex flex-col items-center justify-center py-20 gap-3">
                      <GitCompare className="w-12 h-12 text-slate-700" />
                      <p className="text-slate-400 font-medium">Select a clause type to inspect drift</p>
                      <p className="text-slate-500 text-sm">BERT cosine similarity vs standard template</p>
                    </div>
                  ) : !driftDetail && driftSelected ? (
                    <div className="bg-slate-900 border border-slate-800 rounded-xl flex flex-col items-center justify-center py-20 gap-3">
                      <Loader className="w-8 h-8 text-purple-400 animate-spin" />
                      <p className="text-slate-400 text-sm">Loading drift analysis for <span className="text-purple-300 font-semibold">{driftSelected}</span>...</p>
                    </div>
                  ) : (
                    <>
                      {/* header */}
                      <div className="bg-gradient-to-r from-slate-900 to-slate-800/50 border border-slate-700 rounded-xl p-5">
                        <div className="flex items-start justify-between gap-3 mb-4">
                          <div>
                            <h3 className="text-lg font-bold text-white">{driftDetail.clause_type}</h3>
                            <p className="text-slate-400 text-sm mt-0.5">
                              {driftDetail.drifted_count} drifted · {driftDetail.total_count} total ·
                              Avg similarity <span className={`font-bold ${driftDetail.avg_similarity > 0.75 ? 'text-green-400' : driftDetail.avg_similarity > 0.5 ? 'text-yellow-400' : 'text-red-400'}`}>
                                {driftDetail.avg_similarity ? `${(driftDetail.avg_similarity*100).toFixed(1)}%` : 'N/A'}
                              </span>
                            </p>
                          </div>
                          <div className="text-right flex-shrink-0">
                            <p className="text-xs text-slate-500 mb-1">Drift Rate</p>
                            <p className={`text-3xl font-bold ${driftDetail.drift_rate > 0.5 ? 'text-red-400' : driftDetail.drift_rate > 0.2 ? 'text-yellow-400' : 'text-green-400'}`}>
                              {driftDetail.drift_rate ? `${(driftDetail.drift_rate*100).toFixed(0)}%` : '0%'}
                            </p>
                          </div>
                        </div>
                        {/* gauge row */}
                        <div>
                          <div className="flex justify-between text-xs text-slate-500 mb-1">
                            <span>Avg similarity to standard template</span>
                            <span>Threshold 75%</span>
                          </div>
                          <div className="relative h-3 bg-slate-700 rounded-full overflow-hidden">
                            <div className="h-full rounded-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500"
                              style={{width:`${(driftDetail.avg_similarity||0)*100}%`}} />
                            {/* threshold marker */}
                            <div className="absolute top-0 h-full w-0.5 bg-white/60" style={{left:'75%'}} />
                          </div>
                          <div className="flex justify-between text-xs mt-1">
                            <span className="text-red-400">0% — Drifted</span>
                            <span className="text-green-400">100% — Identical</span>
                          </div>
                        </div>
                      </div>

                      {/* standard template */}
                      {driftDetail.standard && (
                        <div className="bg-blue-950/40 border border-blue-800/60 rounded-xl p-4">
                          <div className="flex items-center gap-2 mb-2">
                            <CheckCircle className="w-4 h-4 text-blue-400" />
                            <p className="text-xs font-bold text-blue-300 uppercase tracking-wide">Standard Template</p>
                            <span className="text-xs text-slate-500 ml-auto">{driftDetail.standard.contract_name}</span>
                          </div>
                          <p className="text-slate-300 text-xs leading-relaxed line-clamp-4">{driftDetail.standard.text || 'No text available'}</p>
                        </div>
                      )}

                      {/* timeline chart (if data available) */}
                      {driftTimeline.length > 0 && (
                        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                          <p className="text-xs font-bold text-slate-400 uppercase tracking-wide mb-3 flex items-center gap-2">
                            <Activity className="w-3.5 h-3.5 text-purple-400" />Drift Over Time
                          </p>
                          <ResponsiveContainer width="100%" height={130}>
                            <AreaChart data={driftTimeline} margin={{left:-15, right:5}}>
                              <defs>
                                <linearGradient id="simGrad" x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%" stopColor="#a855f7" stopOpacity={0.3}/>
                                  <stop offset="95%" stopColor="#a855f7" stopOpacity={0}/>
                                </linearGradient>
                              </defs>
                              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                              <XAxis dataKey="date" tick={{ fill:'#475569', fontSize:9 }} tickFormatter={v=>v?.slice(0,7)} />
                              <YAxis domain={[0,1]} tick={{ fill:'#475569', fontSize:9 }} tickFormatter={v=>`${(v*100).toFixed(0)}%`} />
                              <Tooltip contentStyle={{ background:'#0f172a', border:'1px solid #334155', borderRadius:6, fontSize:10 }} formatter={v=>[`${(v*100).toFixed(1)}%`]} />
                              <ReferenceLine y={0.75} stroke="#10b981" strokeDasharray="4 4" strokeWidth={1} />
                              <Area type="monotone" dataKey="similarity" stroke="#a855f7" fill="url(#simGrad)" strokeWidth={2} dot={{ fill:'#a855f7', r:3 }} name="Similarity" />
                            </AreaChart>
                          </ResponsiveContainer>
                        </div>
                      )}

                      {/* per-clause breakdown */}
                      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                        <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
                          <p className="text-xs font-bold text-slate-400 uppercase tracking-wide">Clause Comparison ({(driftDetail.clauses||[]).length})</p>
                          <div className="flex items-center gap-2 text-xs text-slate-500">
                            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500" />Drifted</span>
                            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500" />OK</span>
                          </div>
                        </div>
                        <div className="divide-y divide-slate-800/60 max-h-72 overflow-y-auto">
                          {(driftDetail.clauses || []).map((c, i) => (
                            <div key={c.id} className={`px-4 py-3 ${c.is_drifted ? 'bg-red-900/10' : ''}`}>
                              <div className="flex items-center gap-3">
                                <span className="text-slate-600 text-xs font-mono w-5 flex-shrink-0">{i+1}</span>
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2 mb-1">
                                    <span className="text-sm font-semibold text-white truncate">{c.clause_name || `Clause ${i+1}`}</span>
                                    {c.is_drifted
                                      ? <span className="flex items-center gap-1 text-xs text-red-400 bg-red-900/30 px-1.5 py-0.5 rounded border border-red-800 flex-shrink-0"><AlertTriangle className="w-3 h-3" />DRIFTED</span>
                                      : <span className="flex items-center gap-1 text-xs text-green-400 bg-green-900/30 px-1.5 py-0.5 rounded border border-green-800 flex-shrink-0"><CheckCircle className="w-3 h-3" />MATCH</span>
                                    }
                                  </div>
                                  <p className="text-xs text-slate-500 mb-2">{c.contract_name}</p>
                                  <div className="flex items-center gap-2">
                                    <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                                      <div className={`h-full rounded-full ${c.similarity>0.75?'bg-green-500':c.similarity>0.5?'bg-yellow-500':'bg-red-500'}`}
                                        style={{width:`${c.similarity*100}%`}} />
                                    </div>
                                    <span className={`text-xs font-bold w-10 text-right flex-shrink-0 ${c.similarity>0.75?'text-green-400':c.similarity>0.5?'text-yellow-400':'text-red-400'}`}>
                                      {(c.similarity*100).toFixed(1)}%
                                    </span>
                                  </div>
                                  {c.text_preview && (
                                    <p className="text-xs text-slate-500 mt-1.5 line-clamp-2">{c.text_preview}</p>
                                  )}
                                </div>
                                <div className="text-right flex-shrink-0">
                                  <p className="text-xs text-slate-500">Risk</p>
                                  <span className={`text-xs font-bold ${c.risk_level==='HIGH'?'text-red-400':c.risk_level==='MEDIUM'?'text-yellow-400':'text-green-400'}`}>{c.risk_level||'—'}</span>
                                </div>
                              </div>
                            </div>
                          ))}
                          {!(driftDetail.clauses||[]).length && (
                            <p className="text-center py-6 text-slate-500 text-sm">No clause data available.</p>
                          )}
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* ════════════════════════════════════════════════════════════════════
          TAB 3 — CFO ANALYTICS
      ════════════════════════════════════════════════════════════════════ */}
      {activeTab === 'cfo' && (
        <div className="space-y-4">
          {/* scope toggle */}
          <div className="flex items-center justify-between bg-slate-900 border border-slate-800 rounded-xl px-4 py-3">
            <div className="flex items-center gap-2 text-sm">
              <DollarSign className="w-4 h-4 text-green-400" />
              <span className="text-slate-400">Showing data for:</span>
              <span className="text-white font-semibold">This contract only ({contract?.originalFilename || contractId})</span>
            </div>
          </div>

          {cfoLoading ? (
            <div className="flex flex-col items-center justify-center py-20 gap-3">
              <Loader className="w-10 h-10 text-green-400 animate-spin" />
              <p className="text-slate-400 text-sm">Aggregating financial exposure — {cfoScope === 'all' ? 'all contracts' : 'this contract'}...</p>
            </div>
          ) : (
            <>
              {/* ── KPI banner ── */}
              {cfoKpis && (
                <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
                  {[
                    { label: 'Total Exposure', value: fmt(cfoKpis.total_exposure), color: 'text-red-400', bg: 'from-red-900/30 to-red-900/10 border-red-800', sub: cfoScope === 'this' ? 'this contract only' : 'across all contracts' },
                    { label: 'Avg Risk Score', value: `${(cfoKpis.avg_risk_score * 100).toFixed(1)}%`, color: 'text-orange-400', bg: 'from-orange-900/30 to-orange-900/10 border-orange-800', sub: cfoScope === 'this' ? 'this contract' : 'portfolio avg' },
                    { label: 'High Risk Clauses', value: cfoKpis.high_risk_clauses, color: 'text-red-400', bg: 'from-red-900/20 to-transparent border-red-900', sub: 'need attention' },
                    { label: 'Total Clauses', value: cfoKpis.total_clauses, color: 'text-blue-400', bg: 'from-blue-900/20 to-transparent border-blue-900', sub: 'analyzed' },
                    { label: 'Contracts', value: cfoKpis.total_contracts, color: 'text-purple-400', bg: 'from-purple-900/20 to-transparent border-purple-900', sub: cfoScope === 'this' ? 'selected' : 'in portfolio' },
                    { label: 'Per Contract', value: fmt(cfoKpis.exposure_per_contract), color: 'text-yellow-400', bg: 'from-yellow-900/20 to-transparent border-yellow-900', sub: 'avg exposure' },
                  ].map(k => (
                    <div key={k.label} className={`bg-gradient-to-br ${k.bg} border rounded-xl p-4`}>
                      <p className={`text-2xl font-bold ${k.color}`}>{k.value}</p>
                      <p className="text-white text-xs font-medium mt-0.5">{k.label}</p>
                      <p className="text-slate-500 text-xs">{k.sub}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* ── Sub-tab nav ── */}
              <div className="flex gap-1 bg-slate-900 border border-slate-800 rounded-xl p-1">
                {[
                  {id:'summary', label:'Top Exposure', icon: DollarSign},
                  {id:'bytype',  label:'By Clause Type', icon: Layers},
                  {id:'bycontract', label:'By Contract', icon: FileText},
                  {id:'cashflow', label:'Cash Flow', icon: Calendar},
                  {id:'heatmap', label:'Risk Heatmap', icon: BarChart2},
                ].map(t => (
                  <button key={t.id} onClick={() => setCfoSubTab(t.id)}
                    className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold flex-1 justify-center transition ${
                      cfoSubTab === t.id ? 'bg-green-600 text-white shadow' : 'text-slate-400 hover:text-white hover:bg-slate-800'
                    }`}>
                    <t.icon className="w-3.5 h-3.5" />{t.label}
                  </button>
                ))}
              </div>

              {/* ── Top Exposure ── */}
              {cfoSubTab === 'summary' && cfoKpis && (
                <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
                  {/* clause list */}
                  <div className="lg:col-span-3 bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                    <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between">
                      <h3 className="font-bold text-white text-sm flex items-center gap-2"><DollarSign className="w-4 h-4 text-red-400" />Top 5 Highest Exposure Clauses</h3>
                      <span className="text-xs text-slate-500">All contracts</span>
                    </div>
                    <div className="divide-y divide-slate-800/60">
                      {(cfoKpis.top_exposure_clauses || []).length === 0 && (
                        <p className="text-slate-400 text-sm text-center py-8">No exposure data yet. Process contracts first.</p>
                      )}
                      {(cfoKpis.top_exposure_clauses || []).map((c, i) => (
                        <div key={c.id} className="flex items-center gap-4 px-5 py-4 hover:bg-slate-800/30 transition">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0 ${
                            i === 0 ? 'bg-red-900/50 text-red-400' : i === 1 ? 'bg-orange-900/50 text-orange-400' : 'bg-slate-800 text-slate-400'
                          }`}>{i+1}</div>
                          <div className="flex-1 min-w-0">
                            <p className="text-white font-semibold text-sm truncate">{c.clause_name}</p>
                            <div className="flex items-center gap-2 mt-0.5">
                              <span className="text-xs text-purple-400">{c.clause_type}</span>
                              <span className="text-slate-600">·</span>
                              <span className="text-xs text-slate-400">{c.contract_name}</span>
                            </div>
                            {/* risk bar */}
                            <div className="flex items-center gap-2 mt-1.5">
                              <div className="flex-1 h-1 bg-slate-700 rounded-full overflow-hidden">
                                <div className={`h-full rounded-full ${c.risk_level==='HIGH'?'bg-red-500':c.risk_level==='MEDIUM'?'bg-yellow-500':'bg-green-500'}`}
                                  style={{width:`${(c.risk_score||0)*100}%`}} />
                              </div>
                              <span className="text-xs text-slate-500">{((c.risk_score||0)*100).toFixed(0)}% risk</span>
                            </div>
                          </div>
                          <div className="text-right flex-shrink-0">
                            <p className="text-red-400 font-bold text-lg">{fmt(c.financial_impact)}</p>
                            <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                              c.risk_level==='HIGH' ? 'bg-red-900/40 text-red-400' :
                              c.risk_level==='MEDIUM' ? 'bg-yellow-900/40 text-yellow-400' : 'bg-green-900/40 text-green-400'
                            }`}>{c.risk_level}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  {/* donut-style breakdown */}
                  <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5">
                    <h3 className="font-bold text-white text-sm mb-4 flex items-center gap-2"><BarChart2 className="w-4 h-4 text-green-400" />Exposure Breakdown</h3>
                    <ResponsiveContainer width="100%" height={200}>
                      <BarChart data={lossByType.slice(0, 6)} layout="vertical" margin={{left: 0, right: 10}}>
                        <XAxis type="number" tick={{ fill:'#475569', fontSize:9 }} tickFormatter={fmt} />
                        <YAxis type="category" dataKey="clause_type" tick={{ fill:'#94a3b8', fontSize:9 }} width={100} />
                        <Tooltip contentStyle={{ background:'#0f172a', border:'1px solid #334155', borderRadius:8, fontSize:11 }} formatter={v=>[fmt(v),'Exposure']} />
                        <Bar dataKey="total_loss" radius={[0,3,3,0]}>
                          {lossByType.slice(0,6).map((_,i)=><Cell key={i} fill={BAR_COLORS[i%BAR_COLORS.length]} />)}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                    <div className="mt-4 space-y-1.5">
                      {lossByType.slice(0,4).map((t,i)=>(
                        <div key={t.clause_type} className="flex items-center gap-2 text-xs">
                          <span className="w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{background:BAR_COLORS[i%BAR_COLORS.length]}} />
                          <span className="text-slate-300 truncate flex-1">{t.clause_type}</span>
                          <span className="text-slate-400 flex-shrink-0">{fmt(t.total_loss)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* ── By Type ── */}
              {cfoSubTab === 'bytype' && (
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-bold text-white text-sm flex items-center gap-2"><Layers className="w-4 h-4 text-purple-400" />Financial Exposure by Clause Type</h3>
                    <span className="text-xs text-slate-500">{lossByType.length} clause types</span>
                  </div>
                  <ResponsiveContainer width="100%" height={Math.max(260, lossByType.length * 36)}>
                    <BarChart data={lossByType} layout="vertical" margin={{left:0, right:40}}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                      <XAxis type="number" tick={{ fill:'#475569', fontSize:10 }} tickFormatter={fmt} />
                      <YAxis type="category" dataKey="clause_type" tick={{ fill:'#94a3b8', fontSize:10 }} width={140} />
                      <Tooltip contentStyle={{ background:'#0f172a', border:'1px solid #334155', borderRadius:8 }}
                        formatter={(v, name) => name === 'total_loss' ? [fmt(v), 'Total Exposure'] : [`${(v*100).toFixed(1)}%`, 'Avg Risk']} />
                      <Bar dataKey="total_loss" radius={[0,4,4,0]} label={{ position:'right', formatter: fmt, fill:'#64748b', fontSize:10 }}>
                        {lossByType.map((_,i)=><Cell key={i} fill={BAR_COLORS[i%BAR_COLORS.length]} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                  {/* table below chart */}
                  <div className="mt-4 overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead><tr className="border-b border-slate-800">
                        {['Clause Type','Total Exposure','Avg/Clause','Max','Clauses','Avg Risk'].map(h=>(
                          <th key={h} className="text-left py-2 px-3 text-slate-400 font-medium">{h}</th>
                        ))}
                      </tr></thead>
                      <tbody className="divide-y divide-slate-800/40">
                        {lossByType.map((t,i)=>(
                          <tr key={t.clause_type} className="hover:bg-slate-800/30">
                            <td className="py-2 px-3 text-white font-medium flex items-center gap-2">
                              <span className="w-2 h-2 rounded-full flex-shrink-0" style={{background:BAR_COLORS[i%BAR_COLORS.length]}} />
                              {t.clause_type}
                            </td>
                            <td className="py-2 px-3 text-red-400 font-bold">{fmt(t.total_loss)}</td>
                            <td className="py-2 px-3 text-slate-300">{fmt(t.avg_loss)}</td>
                            <td className="py-2 px-3 text-orange-400">{fmt(t.max_loss)}</td>
                            <td className="py-2 px-3 text-blue-400">{t.clause_count}</td>
                            <td className="py-2 px-3">
                              <div className="flex items-center gap-2">
                                <div className="w-12 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                                  <div className={`h-full rounded-full ${t.avg_risk_score>0.7?'bg-red-500':t.avg_risk_score>0.4?'bg-yellow-500':'bg-green-500'}`}
                                    style={{width:`${t.avg_risk_score*100}%`}} />
                                </div>
                                <span className="text-slate-300">{(t.avg_risk_score*100).toFixed(0)}%</span>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* ── By Contract ── */}
              {cfoSubTab === 'bycontract' && (
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-bold text-white text-sm flex items-center gap-2"><FileText className="w-4 h-4 text-blue-400" />Financial Exposure by Contract</h3>
                    <span className="text-xs text-slate-500">{lossByContract.length} contracts</span>
                  </div>
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart data={lossByContract}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                      <XAxis dataKey="contract_name" tick={{ fill:'#94a3b8', fontSize:10 }} angle={-15} textAnchor="end" height={50} />
                      <YAxis tick={{ fill:'#94a3b8', fontSize:10 }} tickFormatter={fmt} />
                      <Tooltip contentStyle={{ background:'#0f172a', border:'1px solid #334155', borderRadius:8 }}
                        formatter={(v, n) => n==='total_loss'?[fmt(v),'Exposure']:[`${(v*100).toFixed(1)}%`,'Avg Risk']} />
                      <Bar dataKey="total_loss" name="total_loss" radius={[4,4,0,0]}>
                        {lossByContract.map((_,i)=><Cell key={i} fill={BAR_COLORS[i%BAR_COLORS.length]} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                  <div className="mt-4 space-y-2">
                    {lossByContract.map((c,i)=>(
                      <div key={c.contract_id} className="flex items-center gap-3 bg-slate-800/30 rounded-lg px-4 py-2.5">
                        <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{background:BAR_COLORS[i%BAR_COLORS.length]}} />
                        <div className="flex-1 min-w-0">
                          <p className="text-white text-xs font-medium truncate">{c.contract_name}</p>
                          <p className="text-slate-500 text-xs">{c.clause_count} clauses · {c.high_risk_count||0} high risk</p>
                        </div>
                        <div className="text-right flex-shrink-0">
                          <p className="text-red-400 font-bold text-sm">{fmt(c.total_loss)}</p>
                          <p className="text-slate-500 text-xs">{((c.avg_risk_score||0)*100).toFixed(0)}% risk</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* ── Cash Flow ── */}
              {cfoSubTab === 'cashflow' && (
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="font-bold text-white text-sm flex items-center gap-2"><Calendar className="w-4 h-4 text-blue-400" />Risk Exposure Cash Flow Projection</h3>
                      <p className="text-slate-400 text-xs mt-0.5">When financial risk from each clause type is expected to materialize over 24 months</p>
                    </div>
                    {cashFlow.length > 0 && (
                      <div className="text-right">
                        <p className="text-xs text-slate-500">Total Projected</p>
                        <p className="text-red-400 font-bold text-lg">{fmt(cashFlow[cashFlow.length-1]?.cumulative||0)}</p>
                      </div>
                    )}
                  </div>
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={cashFlow}>
                      <defs>
                        <linearGradient id="expG2" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#ef4444" stopOpacity={0.4}/><stop offset="95%" stopColor="#ef4444" stopOpacity={0}/></linearGradient>
                        <linearGradient id="cumG2" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#a855f7" stopOpacity={0.3}/><stop offset="95%" stopColor="#a855f7" stopOpacity={0}/></linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="month" tick={{ fill:'#475569', fontSize:10 }} />
                      <YAxis tick={{ fill:'#475569', fontSize:10 }} tickFormatter={fmt} />
                      <Tooltip contentStyle={{ background:'#0f172a', border:'1px solid #334155', borderRadius:8 }}
                        formatter={(v,n) => [fmt(v), n==='exposure'?'Monthly Exposure':'Cumulative']} />
                      <Legend formatter={v => v==='exposure'?'Monthly Exposure':'Cumulative Exposure'} />
                      <Area type="monotone" dataKey="cumulative" stroke="#a855f7" fill="url(#cumG2)" strokeWidth={2} name="cumulative" />
                      <Area type="monotone" dataKey="exposure" stroke="#ef4444" fill="url(#expG2)" strokeWidth={2} name="exposure" />
                    </AreaChart>
                  </ResponsiveContainer>
                  <div className="mt-4 grid grid-cols-3 gap-3 text-xs">
                    {[
                      { label: 'Peak Month', value: cashFlow.reduce((a,b)=>b.exposure>a.exposure?b:a, {exposure:0, month:'—'})?.month, color:'text-red-400' },
                      { label: 'Peak Exposure', value: fmt(Math.max(...cashFlow.map(c=>c.exposure||0))), color:'text-orange-400' },
                      { label: '12-mo Cumulative', value: fmt(cashFlow[11]?.cumulative||0), color:'text-purple-400' },
                    ].map(k => (
                      <div key={k.label} className="bg-slate-800/50 rounded-lg p-3 text-center">
                        <p className={`text-base font-bold ${k.color}`}>{k.value}</p>
                        <p className="text-slate-500 mt-0.5">{k.label}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* ── Heatmap ── */}
              {cfoSubTab === 'heatmap' && (
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 overflow-x-auto">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-bold text-white text-sm flex items-center gap-2"><BarChart2 className="w-4 h-4 text-yellow-400" />Risk Heatmap: Clause Type × Contract</h3>
                    <div className="flex items-center gap-3 text-xs text-slate-400">
                      <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-green-600 inline-block" />Low</span>
                      <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-yellow-500 inline-block" />Med</span>
                      <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-red-500 inline-block" />High</span>
                    </div>
                  </div>
                  {heatmap?.rows?.length ? (
                    <table className="text-xs border-collapse w-full">
                      <thead>
                        <tr className="border-b border-slate-700">
                          <th className="text-left py-2 px-3 text-slate-400 font-medium min-w-[150px]">Clause Type</th>
                          {heatmap.contracts?.map(c => (
                            <th key={c} className="py-2 px-3 text-center text-slate-400 font-medium min-w-[110px] max-w-[140px]">
                              <span className="truncate block" title={c}>{c.length > 14 ? c.slice(0, 14) + '…' : c}</span>
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/30">
                        {heatmap.rows.map(row => (
                          <tr key={row.clause_type} className="hover:bg-slate-800/20">
                            <td className="py-2.5 px-3 text-slate-200 font-medium">{row.clause_type}</td>
                            {row.values?.map((v, i) => {
                              const r = v.risk || 0;
                              const bg = r > 0.7 ? `rgba(239,68,68,${0.3 + r*0.6})` :
                                         r > 0.4 ? `rgba(245,158,11,${0.3 + r*0.5})` :
                                         r > 0   ? `rgba(16,185,129,${0.2 + r*0.4})` : '';
                              return (
                                <td key={i} className="py-2.5 px-3 text-center rounded" style={{ background: bg }}>
                                  {r > 0 ? (
                                    <div>
                                      <p className="font-bold text-white">{(r*100).toFixed(0)}%</p>
                                      {v.financial > 0 && <p className="text-slate-300 text-xs">{fmt(v.financial)}</p>}
                                    </div>
                                  ) : <span className="text-slate-700">—</span>}
                                </td>
                              );
                            })}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : <p className="text-slate-400 text-center py-8">No heatmap data. Process contracts to generate risk scores first.</p>}
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* ════════════════════════════════════════════════════════════════════
          TAB 4 — PREDICTIVE RISK
      ════════════════════════════════════════════════════════════════════ */}
      {activeTab === 'predictive' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-slate-400 text-sm">XGBoost + Linear regression forecasting of clause risk trajectories</p>
            <div className="flex items-center gap-2">
              <span className="text-slate-400 text-xs">Horizon:</span>
              {[3, 6, 12].map(h => (
                <button key={h} onClick={() => { setHorizon(h); setForecasts([]); setPredDetail(null); }}
                  className={`px-3 py-1 rounded text-xs font-semibold transition ${horizon === h ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-300'}`}>
                  {h}mo
                </button>
              ))}
            </div>
          </div>

          {predLoading ? (
            <div className="flex justify-center py-16"><Loader className="w-8 h-8 text-blue-400 animate-spin" /></div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
              {/* List */}
              <div className="lg:col-span-1 bg-slate-900 border border-slate-800 rounded-xl p-4">
                <p className="text-xs font-bold text-slate-400 uppercase tracking-wide mb-3">All Clause Types</p>
                <div className="space-y-2 max-h-[560px] overflow-y-auto pr-1">
                  {forecasts.length === 0 && <p className="text-slate-400 text-sm text-center py-6">No risk history found.<br />Process contracts first.</p>}
                  {forecasts.map(f => (
                    <button key={f.clause_type} onClick={() => loadPredDetail(f.clause_type)}
                      className={`w-full text-left p-3 rounded-lg border transition ${predSelected === f.clause_type ? 'border-blue-600 bg-blue-900/20' : 'border-slate-700 bg-slate-800/30 hover:border-slate-600'}`}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-semibold text-white truncate pr-2">{f.clause_type}</span>
                        <span className={`text-xs font-bold ${OUTLOOK_COLOR[f.risk_outlook] || 'text-slate-400'}`}>{f.risk_outlook}</span>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-slate-400">
                        <span>{f.trend === 'increasing' ? '↑' : f.trend === 'decreasing' ? '↓' : '—'} {f.trend}</span>
                        <span className={`px-1.5 py-0.5 rounded ${METHOD_BADGE[f.method] || 'bg-slate-700 text-slate-400'}`}>{f.method}</span>
                      </div>
                      <div className="mt-2 h-1 bg-slate-700 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-500 rounded-full" style={{ width: `${Math.min((f.forecast_avg_risk || 0) * 100, 100)}%` }} />
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Detail */}
              <div className="lg:col-span-2">
                {!predDetail && !predDetailLoading && (
                  <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center">
                    <Activity className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                    <p className="text-slate-400">Select a clause type to see its forecast</p>
                  </div>
                )}
                {predDetailLoading && <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 flex justify-center"><Loader className="w-8 h-8 text-blue-400 animate-spin" /></div>}
                {predDetail && !predDetailLoading && (
                  <div className="space-y-4">
                    <div className={`${OUTLOOK_BG[predDetail.risk_outlook] || 'bg-slate-900 border-slate-700'} border rounded-xl p-5`}>
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="text-lg font-bold text-white">{predDetail.clause_type}</h3>
                        <span className={`font-bold ${OUTLOOK_COLOR[predDetail.risk_outlook]}`}>{predDetail.risk_outlook} RISK</span>
                      </div>
                      <div className="grid grid-cols-4 gap-3 text-sm">
                        {[
                          { label: 'Current Risk', value: `${(predDetail.current_avg_risk * 100).toFixed(1)}%` },
                          { label: 'Forecast Avg', value: `${(predDetail.forecast_avg_risk * 100).toFixed(1)}%` },
                          { label: 'Trend', value: predDetail.trend },
                          { label: 'Method', value: predDetail.method },
                        ].map(k => (
                          <div key={k.label}>
                            <p className="text-slate-400 text-xs">{k.label}</p>
                            <p className="text-white font-bold text-sm mt-0.5">{k.value}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                      <ResponsiveContainer width="100%" height={260}>
                        <AreaChart data={buildPredChart(predDetail)}>
                          <defs>
                            <linearGradient id="actG2" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} /><stop offset="95%" stopColor="#3b82f6" stopOpacity={0} /></linearGradient>
                            <linearGradient id="predG2" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#a855f7" stopOpacity={0.3} /><stop offset="95%" stopColor="#a855f7" stopOpacity={0} /></linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                          <XAxis dataKey="month" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                          <YAxis domain={[0, 1]} tick={{ fill: '#94a3b8', fontSize: 10 }} tickFormatter={v => `${(v * 100).toFixed(0)}%`} />
                          <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #475569', borderRadius: 8 }} formatter={v => v != null ? [`${(v * 100).toFixed(1)}%`] : ['N/A']} />
                          <Legend />
                          <ReferenceLine y={0.7} stroke="#ef4444" strokeDasharray="4 4" />
                          <Area type="monotone" dataKey="actual" stroke="#3b82f6" fill="url(#actG2)" strokeWidth={2} name="Historical" connectNulls={false} />
                          <Area type="monotone" dataKey="predicted" stroke="#a855f7" fill="url(#predG2)" strokeWidth={2} strokeDasharray="5 5" name="Forecast" connectNulls={false} />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ════════════════════════════════════════════════════════════════════
          TAB 5 — AUTO REDLINE
      ════════════════════════════════════════════════════════════════════ */}
      {activeTab === 'redline' && (
        <div className="space-y-4">
          {/* Config */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <div className="flex flex-wrap items-center gap-6">
              <div>
                <label className="text-slate-400 text-xs block mb-1">Similarity Threshold</label>
                <div className="flex items-center gap-3">
                  <input type="range" min="0.5" max="0.95" step="0.05" value={redlineThreshold} onChange={e => setRedlineThreshold(parseFloat(e.target.value))} className="accent-orange-500 w-32" />
                  <span className="text-white font-bold text-sm">{(redlineThreshold * 100).toFixed(0)}%</span>
                </div>
                <p className="text-slate-500 text-xs mt-0.5">Clauses below this similarity will be flagged</p>
              </div>
              <div className="flex items-center gap-2">
                <input type="checkbox" id="genS" checked={genSuggestions} onChange={e => setGenSuggestions(e.target.checked)} className="accent-orange-500 w-4 h-4" />
                <label htmlFor="genS" className="text-slate-300 text-sm">Generate AI suggestions</label>
              </div>
              <button onClick={runRedline} disabled={redlineLoading}
                className={`flex items-center gap-2 px-5 py-2 rounded-lg font-semibold text-sm transition ${redlineLoading ? 'bg-slate-700 text-slate-500 cursor-not-allowed' : 'bg-orange-600 hover:bg-orange-700 text-white'}`}>
                {redlineLoading ? <><Loader className="w-4 h-4 animate-spin" />Analyzing...</> : <><Zap className="w-4 h-4" />Run Redline Analysis</>}
              </button>
              {redlines && (
                <button onClick={exportRedline} disabled={exporting}
                  className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-semibold">
                  {exporting ? <Loader className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}Export
                </button>
              )}
            </div>
          </div>

          {redlineError && (
            <div className="bg-red-900/20 border border-red-800 rounded-xl p-4 flex gap-3">
              <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
              <p className="text-red-300 text-sm">{redlineError}</p>
            </div>
          )}

          {redlines && (
            <div className="space-y-4">
              {/* Summary */}
              <div className="grid grid-cols-4 gap-3">
                {[
                  { label: 'Total Clauses', value: redlines.total_clauses, color: 'text-blue-400' },
                  { label: 'Needs Redline', value: redlines.drifted_clauses, color: 'text-red-400' },
                  { label: 'Compliant', value: redlines.total_clauses - redlines.drifted_clauses, color: 'text-green-400' },
                  { label: 'Threshold', value: `${(redlines.threshold * 100).toFixed(0)}%`, color: 'text-orange-400' },
                ].map(k => (
                  <div key={k.label} className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center">
                    <p className={`text-2xl font-bold ${k.color}`}>{k.value}</p>
                    <p className="text-slate-400 text-xs mt-1">{k.label}</p>
                  </div>
                ))}
              </div>

              {/* Filter */}
              <div className="flex gap-2">
                {[{id:'all',label:`All (${redlines.total_clauses})`},{id:'drifted',label:`Redline (${redlines.drifted_clauses})`},{id:'ok',label:`OK (${redlines.total_clauses - redlines.drifted_clauses})`}].map(f => (
                  <button key={f.id} onClick={() => setRedlineFilter(f.id)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-semibold transition ${redlineFilter === f.id ? 'bg-orange-600 text-white' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}>
                    {f.label}
                  </button>
                ))}
              </div>

              {/* Diff legend */}
              <div className="flex items-center gap-4 text-xs text-slate-400 bg-slate-900 border border-slate-800 rounded-lg px-4 py-2">
                <Info className="w-3.5 h-3.5" />
                <span className="bg-red-900/50 text-red-300 px-1 rounded">deleted</span>
                <span className="bg-green-900/50 text-green-300 px-1 rounded">inserted</span>
                <span>unchanged</span>
              </div>

              {/* Cards */}
              <div className="space-y-3">
                {filteredRedlines.map((r, i) => <RedlineCard key={r.clause_id} r={r} index={i} />)}
                {!filteredRedlines.length && <p className="text-center py-6 text-slate-400">No clauses match this filter.</p>}
              </div>
            </div>
          )}

          {!redlines && !redlineLoading && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center">
              <FileEdit className="w-16 h-16 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400 text-lg mb-2">Ready to analyze</p>
              <p className="text-slate-500 text-sm">Configure options above and click "Run Redline Analysis" to compare your contract clauses against standard templates.</p>
            </div>
          )}
        </div>
      )}

    </div>
  );
}
