import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  BookOpen, CheckCircle, AlertTriangle, ShieldAlert,
  TrendingDown, BarChart2, RefreshCw, ChevronDown, ChevronUp,
  ArrowLeft, Plus, Loader2, Network
} from 'lucide-react';
import useThemeStore from '../store/themeStore';
import PlaybookKnowledgeGraph from '../components/graph/PlaybookKnowledgeGraph';

const API_BASE = (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));
const headers = () => ({ Authorization: `Bearer ${localStorage.getItem('token')}` });

// ---------------------------------------------------------------------------
// Colour helpers
// ---------------------------------------------------------------------------
const statusBg = (isStandard) =>
  isStandard ? 'bg-green-900 bg-opacity-20 border-green-500' : 'bg-red-900 bg-opacity-20 border-red-500';

const statusText = (isStandard) =>
  isStandard ? 'text-green-400' : 'text-red-400';

const driftColor = (similarity, drift) => {
  if (similarity < 0.7 && drift > 0.5) return { bg: 'bg-red-800', label: 'Broken', text: 'text-white' };
  if (similarity < 0.8)               return { bg: 'bg-orange-600', label: 'Degrading', text: 'text-white' };
  if (drift > 0.3)                    return { bg: 'bg-yellow-500', label: 'Drifting', text: 'text-gray-900' };
  return                               { bg: 'bg-green-600', label: 'Healthy', text: 'text-white' };
};

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** Summary metric card (reuses the card pattern seen across the app) */
function MetricCard({ icon: Icon, label, value, color = 'text-blue-400' }) {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 flex items-center gap-3">
      <div className={`${color}`}><Icon className="w-6 h-6" /></div>
      <div>
        <p className="text-gray-400 text-xs uppercase tracking-wide">{label}</p>
        <p className={`text-xl font-bold ${color}`}>{value}</p>
      </div>
    </div>
  );
}

/** Single clause result card with expandable fallback suggestion */
function ClauseCard({ result, onAccept }) {
  const [expanded, setExpanded] = useState(!result.is_standard);

  return (
    <div className={`border rounded-lg overflow-hidden ${statusBg(result.is_standard)}`}>
      {/* header row */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-3 text-left"
      >
        <div className="flex items-center gap-3">
          {result.is_standard
            ? <CheckCircle className="w-5 h-5 text-green-400" />
            : <AlertTriangle className="w-5 h-5 text-red-400" />}
          <div>
            <span className={`font-semibold ${statusText(result.is_standard)}`}>
              {result.clause_name}
            </span>
            <span className="text-gray-500 text-xs ml-2">
              [{result.clause_type} · {result.jurisdiction}]
            </span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-gray-400 text-sm">
            {(result.similarity_score * 100).toFixed(1)}% match
          </span>
          {result.mandatory && !result.is_standard && (
            <span className="bg-red-700 text-white text-xs px-2 py-0.5 rounded-full">
              Negotiation Triggered
            </span>
          )}
          {expanded ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
        </div>
      </button>

      {/* expandable body */}
      {expanded && !result.is_standard && (
        <div className="px-4 pb-4 border-t border-gray-700 pt-3">
          <p className="text-gray-400 text-xs uppercase tracking-wide mb-1">Suggested Fallback</p>
          <p className="text-gray-200 text-sm bg-gray-900 rounded p-3 whitespace-pre-wrap">
            {result.suggested_text}
          </p>
          {!result.fallback_accepted ? (
            <button
              onClick={() => onAccept(result.id)}
              className="mt-3 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium px-4 py-1.5 rounded transition"
            >
              Accept Fallback
            </button>
          ) : (
            <span className="mt-3 inline-block text-green-400 text-sm">Fallback Accepted</span>
          )}
        </div>
      )}
    </div>
  );
}

/** Drift trend line (simple bar-based visual — no external chart lib dependency) */
function DriftTrendPanel({ driftData }) {
  if (!driftData || driftData.length === 0) {
    return <p className="text-gray-500 text-sm">No drift data available yet. Run a playbook check first.</p>;
  }

  // Group by clause_type
  const grouped = {};
  driftData.forEach((d) => {
    if (!grouped[d.clause_type]) grouped[d.clause_type] = [];
    grouped[d.clause_type].push(d);
  });

  return (
    <div className="space-y-4">
      {Object.entries(grouped).map(([type, rows]) => {
        const latest = rows[rows.length - 1];
        return (
          <div key={type} className="bg-gray-800 border border-gray-700 rounded-lg p-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-gray-200 font-medium">{type}</span>
              <span className="text-gray-500 text-xs">{latest.snapshot_date}</span>
            </div>
            {/* similarity bar */}
            <div className="flex items-center gap-2 mb-1">
              <span className="text-gray-500 text-xs w-28">Avg Similarity</span>
              <div className="flex-1 bg-gray-700 rounded-full h-2.5">
                <div
                  className="h-2.5 rounded-full bg-blue-500"
                  style={{ width: `${latest.avg_similarity * 100}%` }}
                />
              </div>
              <span className="text-gray-400 text-xs w-12 text-right">
                {(latest.avg_similarity * 100).toFixed(0)}%
              </span>
            </div>
            {/* non-standard rate bar */}
            <div className="flex items-center gap-2">
              <span className="text-gray-500 text-xs w-28">Non-Std Rate</span>
              <div className="flex-1 bg-gray-700 rounded-full h-2.5">
                <div
                  className="h-2.5 rounded-full bg-red-500"
                  style={{ width: `${latest.non_standard_rate * 100}%` }}
                />
              </div>
              <span className="text-gray-400 text-xs w-12 text-right">
                {(latest.non_standard_rate * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

/** Heatmap grid */
function HeatmapPanel({ heatmapData }) {
  if (!heatmapData || heatmapData.length === 0) {
    return <p className="text-gray-500 text-sm">No heatmap data yet.</p>;
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
      {heatmapData.map((item, i) => {
        const { bg, label, text } = driftColor(item.avg_similarity, item.avg_non_standard);
        return (
          <div key={i} className={`${bg} ${text} rounded-lg p-4`}>
            <p className="font-bold text-sm">{item.clause_type}</p>
            <p className="text-xs opacity-80 mt-1">Similarity: {(item.avg_similarity * 100).toFixed(1)}%</p>
            <p className="text-xs opacity-80">Drift: {(item.avg_non_standard * 100).toFixed(1)}%</p>
            <span className="inline-block mt-2 bg-black bg-opacity-25 rounded px-2 py-0.5 text-xs">
              {label}
            </span>
          </div>
        );
      })}
    </div>
  );
}

/** Update suggestions review panel */
function UpdateSuggestionsPanel({ suggestions, onApprove, onReject }) {
  if (!suggestions || suggestions.length === 0) {
    return <p className="text-gray-500 text-sm">No pending update suggestions.</p>;
  }

  return (
    <div className="space-y-3">
      {suggestions.map((s) => (
        <div key={s.id} className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="flex justify-between items-start">
            <div>
              <span className="text-gray-200 font-semibold">{s.clause_type}</span>
              <span className="text-gray-500 text-xs ml-2">({s.jurisdiction})</span>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => onApprove(s.id)}
                className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium px-3 py-1 rounded transition"
              >Approve</button>
              <button
                onClick={() => onReject(s.id)}
                className="bg-red-700 hover:bg-red-600 text-white text-xs font-medium px-3 py-1 rounded transition"
              >Reject</button>
            </div>
          </div>
          <div className="mt-2 flex gap-4 text-xs text-gray-400">
            <span>Avg Similarity: {(s.avg_similarity * 100).toFixed(1)}%</span>
            <span>Non-Std Rate: {(s.non_standard_rate * 100).toFixed(1)}%</span>
          </div>
          <p className="text-gray-500 text-xs mt-1 italic">{s.reason}</p>
          <div className="mt-2">
            <p className="text-gray-400 text-xs uppercase tracking-wide">Suggested New Standard</p>
            <p className="text-gray-200 text-sm bg-gray-900 rounded p-2 mt-1 whitespace-pre-wrap">
              {s.suggested_standard}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------
const TAB_CONTRACT = 'contract';
const TAB_DRIFT    = 'drift';
const TAB_COVERAGE = 'coverage';
const TAB_HEATMAP  = 'heatmap';
const TAB_UPDATES  = 'updates';
const TAB_GRAPH    = 'graph'; // EdgeQuake-style knowledge graph

export default function PlaybookAutomation() {
  const { contractId } = useParams();
  const navigate        = useNavigate();
  const { theme }       = useThemeStore();

  // ---- state
  const [tab, setTab]                       = useState(contractId ? TAB_CONTRACT : TAB_COVERAGE);
  const [loading, setLoading]               = useState(false);
  const [error, setError]                   = useState(null);

  // per-tab data
  const [results, setResults]               = useState(null);   // contract results
  const [driftData, setDriftData]           = useState(null);
  const [coverage, setCoverage]             = useState(null);
  const [heatmapData, setHeatmapData]       = useState(null);
  const [suggestions, setSuggestions]       = useState(null);
  const [playbooks, setPlaybooks]           = useState(null); // For knowledge graph

  // ---- fetchers
  const fetchResults = useCallback(async () => {
    if (!contractId) return;
    setLoading(true); setError(null);
    try {
      const res = await axios.get(`${API_BASE}/api/playbook/contracts/${contractId}/results`, { headers: headers() });
      setResults(res.data);
    } catch (e) {
      setError(e.response?.data?.error || 'Failed to load results');
    } finally { setLoading(false); }
  }, [contractId]);

  const runCheck = async () => {
    if (!contractId) return;
    setLoading(true); setError(null);
    try {
      const res = await axios.post(`${API_BASE}/api/playbook/contracts/${contractId}/run`, {}, { headers: headers() });
      setResults(res.data);
    } catch (e) {
      setError(e.response?.data?.error || 'Playbook check failed');
    } finally { setLoading(false); }
  };

  const fetchDrift = async () => {
    setLoading(true); setError(null);
    try {
      const res = await axios.get(`${API_BASE}/api/playbook/drift`, { headers: headers() });
      setDriftData(res.data);
    } catch (e) { setError(e.response?.data?.error || 'Failed'); }
    finally { setLoading(false); }
  };

  const fetchCoverage = async () => {
    setLoading(true); setError(null);
    try {
      const res = await axios.get(`${API_BASE}/api/playbook/coverage`, { headers: headers() });
      setCoverage(res.data);
    } catch (e) { setError(e.response?.data?.error || 'Failed'); }
    finally { setLoading(false); }
  };

  const fetchHeatmap = async () => {
    setLoading(true); setError(null);
    try {
      const res = await axios.get(`${API_BASE}/api/playbook/heatmap`, { headers: headers() });
      setHeatmapData(res.data);
    } catch (e) { setError(e.response?.data?.error || 'Failed'); }
    finally { setLoading(false); }
  };

  const fetchSuggestions = async () => {
    setLoading(true); setError(null);
    try {
      const res = await axios.get(`${API_BASE}/api/playbook/update-suggestions`, { headers: headers() });
      setSuggestions(res.data);
    } catch (e) { setError(e.response?.data?.error || 'Failed'); }
    finally { setLoading(false); }
  };

  const fetchPlaybooks = async () => {
    setLoading(true); setError(null);
    try {
      const res = await axios.get(`${API_BASE}/api/playbook/admin/playbooks`, { headers: headers() });
      // Transform response to include name and clause_count for graph
      const transformed = res.data.map(pb => ({
        ...pb,
        name: `${pb.clause_type} - ${pb.jurisdiction}`,
        clause_count: 5, // Default count, can be computed later
      }));
      setPlaybooks(transformed);
    } catch (e) { setError(e.response?.data?.error || 'Failed to load playbooks'); }
    finally { setLoading(false); }
  };

  const captureDrift = async () => {
    setLoading(true);
    try {
      await axios.post(`${API_BASE}/api/playbook/drift/capture`, {}, { headers: headers() });
      await fetchDrift();
      await fetchSuggestions();
    } catch (e) { setError(e.response?.data?.error || 'Failed'); }
    finally { setLoading(false); }
  };

  const acceptFallback = async (resultId) => {
    try {
      await axios.post(`${API_BASE}/api/playbook/results/${resultId}/accept`, {}, { headers: headers() });
      // optimistic update
      setResults(prev => prev && {
        ...prev,
        results: prev.results.map(r => r.id === resultId ? { ...r, fallback_accepted: true } : r)
      });
    } catch (e) { setError(e.response?.data?.error || 'Failed'); }
  };

  const approveSuggestion = async (id) => {
    try {
      await axios.post(`${API_BASE}/api/playbook/update-suggestions/${id}/approve`, {}, { headers: headers() });
      setSuggestions(prev => prev?.filter(s => s.id !== id));
    } catch (e) { setError(e.response?.data?.error || 'Failed'); }
  };

  const rejectSuggestion = async (id) => {
    try {
      await axios.post(`${API_BASE}/api/playbook/update-suggestions/${id}/reject`, {}, { headers: headers() });
      setSuggestions(prev => prev?.filter(s => s.id !== id));
    } catch (e) { setError(e.response?.data?.error || 'Failed'); }
  };

  // ---- load on tab switch
  useEffect(() => {
    if (tab === TAB_CONTRACT)  fetchResults();
    if (tab === TAB_DRIFT)     fetchDrift();
    if (tab === TAB_COVERAGE)  fetchCoverage();
    if (tab === TAB_HEATMAP)   fetchHeatmap();
    if (tab === TAB_UPDATES)   fetchSuggestions();
    if (tab === TAB_GRAPH)     { fetchPlaybooks(); fetchDrift(); } // Graph needs both
  }, [tab]);

  // ---- tab definitions
  const tabs = [
    ...(contractId ? [{ id: TAB_CONTRACT, label: 'Playbook Review', icon: BookOpen }] : []),
    { id: TAB_DRIFT,    label: 'Drift Analytics', icon: TrendingDown },
    { id: TAB_COVERAGE, label: 'Coverage',        icon: BarChart2 },
    { id: TAB_HEATMAP,  label: 'Heatmap',         icon: ShieldAlert },
    { id: TAB_UPDATES,  label: 'Update Suggestions', icon: RefreshCw },
    { id: TAB_GRAPH,    label: 'Knowledge Graph', icon: Network }, // NEW: EdgeQuake-style
  ];

  // ---- render
  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-6">
      {/* page header */}
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center gap-3 mb-1">
          {contractId && (
            <button onClick={() => navigate(`/contracts/${contractId}`)} className="text-gray-500 hover:text-gray-300 transition">
              <ArrowLeft className="w-5 h-5" />
            </button>
          )}
          <BookOpen className="w-7 h-7 text-emerald-400" />
          <h1 className="text-2xl font-bold text-gray-100">Playbook Automation</h1>
        </div>
        <p className="text-gray-500 text-sm ml-10">
          AI-powered comparison of incoming contracts against your legal playbook.
          Non-standard terms are flagged and approved fallback language is suggested automatically.
        </p>
      </div>

      {/* tab bar */}
      <div className="max-w-6xl mx-auto mt-5 flex gap-1 border-b border-gray-700 overflow-x-auto">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium rounded-t-lg transition whitespace-nowrap
              ${tab === id
                ? 'bg-gray-800 text-emerald-400 border border-gray-700 border-b-gray-900'
                : 'text-gray-500 hover:text-gray-300'}`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* error banner */}
      {error && (
        <div className="max-w-6xl mx-auto mt-4 bg-red-900 bg-opacity-30 border border-red-600 rounded-lg p-3">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {/* loading spinner */}
      {loading && (
        <div className="max-w-6xl mx-auto mt-12 flex justify-center">
          <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
        </div>
      )}

      {/* ============================================================== */}
      {/* TAB: CONTRACT – playbook review for a single contract            */}
      {/* ============================================================== */}
      {!loading && tab === TAB_CONTRACT && (
        <div className="max-w-6xl mx-auto mt-6 space-y-5">
          {/* action + summary cards */}
          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={runCheck}
              className="bg-emerald-600 hover:bg-emerald-500 text-white font-medium px-5 py-2 rounded-lg transition flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" /> Run Playbook Check
            </button>
          </div>

          {results && (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <MetricCard icon={BookOpen}      label="Total Evaluated"     value={results.total_evaluated}     color="text-blue-400" />
                <MetricCard icon={CheckCircle}   label="Standard"           value={results.standard_count}      color="text-green-400" />
                <MetricCard icon={AlertTriangle} label="Non-Standard"       value={results.non_standard_count}  color="text-red-400" />
                <MetricCard icon={ShieldAlert}   label="Mandatory Violations" value={results.mandatory_violations} color="text-orange-400" />
              </div>

              {/* clause cards */}
              <div className="space-y-3">
                {results.results.length === 0 && (
                  <p className="text-gray-500 text-sm">
                    No clauses matched any playbook entries. Ensure clauses have been extracted and
                    clause_type is enriched, or add playbook entries via the admin API.
                  </p>
                )}
                {results.results.map((r) => (
                  <ClauseCard key={r.id} result={r} onAccept={acceptFallback} />
                ))}
              </div>
            </>
          )}

          {!results && !loading && (
            <p className="text-gray-500 text-sm">Press "Run Playbook Check" to evaluate this contract.</p>
          )}
        </div>
      )}

      {/* ============================================================== */}
      {/* TAB: DRIFT                                                       */}
      {/* ============================================================== */}
      {!loading && tab === TAB_DRIFT && (
        <div className="max-w-6xl mx-auto mt-6 space-y-5">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-200">Playbook Drift Over Time</h2>
            <button
              onClick={captureDrift}
              className="bg-gray-700 hover:bg-gray-600 text-gray-200 text-sm font-medium px-4 py-1.5 rounded transition flex items-center gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Capture Now
            </button>
          </div>
          <p className="text-gray-500 text-sm">
            Tracks how frequently incoming clauses deviate from your approved standards over time.
            "Capture Now" snapshots current data (normally runs daily via cron).
          </p>
          <DriftTrendPanel driftData={driftData} />
        </div>
      )}

      {/* ============================================================== */}
      {/* TAB: COVERAGE                                                    */}
      {/* ============================================================== */}
      {!loading && tab === TAB_COVERAGE && (
        <div className="max-w-6xl mx-auto mt-6 space-y-5">
          <h2 className="text-lg font-semibold text-gray-200">Playbook Coverage Dashboard</h2>
          <p className="text-gray-500 text-sm">
            Shows how much of your contract risk surface is governed by playbook rules.
          </p>
          {coverage ? (
            <>
              <div className="grid grid-cols-3 gap-3">
                <MetricCard icon={BarChart2}    label="Total Clauses"     value={coverage.total_clauses}     color="text-blue-400" />
                <MetricCard icon={CheckCircle}  label="Governed"          value={coverage.governed_clauses}  color="text-green-400" />
                <MetricCard icon={BookOpen}     label="Coverage %"        value={`${coverage.coverage_pct}%`} color="text-emerald-400" />
              </div>

              {/* coverage bar */}
              <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
                <div className="flex justify-between text-xs text-gray-400 mb-1">
                  <span>Governed</span>
                  <span>{coverage.coverage_pct}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-3">
                  <div className="h-3 rounded-full bg-emerald-500" style={{ width: `${coverage.coverage_pct}%` }} />
                </div>
              </div>

              {/* ungoverned types */}
              {coverage.ungoverned && coverage.ungoverned.length > 0 && (
                <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
                  <h3 className="text-gray-200 font-medium mb-2 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-orange-400" /> Ungoverned Clause Types
                  </h3>
                  <div className="space-y-1">
                    {coverage.ungoverned.map((u, i) => (
                      <div key={i} className="flex justify-between text-sm">
                        <span className="text-gray-300">{u.clause_type || '(unset)'}</span>
                        <span className="text-orange-400 font-medium">{u.count} clauses</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <p className="text-gray-500 text-sm">Loading coverage data…</p>
          )}
        </div>
      )}

      {/* ============================================================== */}
      {/* TAB: HEATMAP                                                     */}
      {/* ============================================================== */}
      {!loading && tab === TAB_HEATMAP && (
        <div className="max-w-6xl mx-auto mt-6 space-y-5">
          <h2 className="text-lg font-semibold text-gray-200">Clause Risk × Playbook Drift Heatmap</h2>
          <p className="text-gray-500 text-sm">
            Each tile shows a clause type's average similarity and drift rate. Colour indicates governance health.
          </p>
          <div className="flex gap-4 flex-wrap text-xs">
            {[
              { bg: 'bg-red-800',    label: 'Broken – update playbook immediately' },
              { bg: 'bg-orange-600', label: 'Degrading – monitor' },
              { bg: 'bg-yellow-500', label: 'Drifting – negotiation pressure' },
              { bg: 'bg-green-600',  label: 'Healthy – standards holding' },
            ].map(({ bg, label }, i) => (
              <div key={i} className="flex items-center gap-1.5">
                <div className={`w-3 h-3 rounded ${bg}`} />
                <span className="text-gray-400">{label}</span>
              </div>
            ))}
          </div>
          <HeatmapPanel heatmapData={heatmapData} />
        </div>
      )}

      {/* ============================================================== */}
      {/* TAB: UPDATE SUGGESTIONS                                          */}
      {/* ============================================================== */}
      {!loading && tab === TAB_UPDATES && (
        <div className="max-w-6xl mx-auto mt-6 space-y-5">
          <h2 className="text-lg font-semibold text-gray-200">Playbook Update Suggestions</h2>
          <p className="text-gray-500 text-sm">
            When sustained drift is detected, the system proposes updating the playbook's standard language.
            A reviewer must approve or reject each suggestion before any playbook entry changes.
          </p>
          <UpdateSuggestionsPanel
            suggestions={suggestions}
            onApprove={approveSuggestion}
            onReject={rejectSuggestion}
          />
        </div>
      )}

      {/* ============================================================== */}
      {/* TAB: KNOWLEDGE GRAPH – EdgeQuake-style Sigma.js visualization    */}
      {/* ============================================================== */}
      {!loading && tab === TAB_GRAPH && (
        <div className="max-w-7xl mx-auto mt-6 space-y-5">
          <div className="bg-gradient-to-r from-purple-900/30 to-cyan-900/30 border border-purple-500/30 rounded-xl p-6">
            <h2 className="text-xl font-semibold text-white flex items-center gap-2 mb-2">
              <Network className="w-6 h-6 text-purple-400" />
              Playbook Knowledge Graph
              <span className="text-xs bg-purple-600/30 text-purple-300 px-2 py-1 rounded-full ml-2">
                EdgeQuake-inspired
              </span>
            </h2>
            <p className="text-gray-400 text-sm">
              Interactive network visualization showing playbooks, clauses, drift patterns, and community clusters.
              Uses <span className="text-purple-400 font-semibold">Sigma.js</span> with <span className="text-cyan-400 font-semibold">ForceAtlas2</span> layout algorithm
              for superior graph exploration.
            </p>
          </div>

          {playbooks && (
            <PlaybookKnowledgeGraph
              playbooksData={playbooks}
              driftData={driftData?.snapshots || []}
            />
          )}

          {!playbooks && (
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-12 text-center">
              <Network className="w-16 h-16 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">No playbook data available yet.</p>
              <p className="text-slate-500 text-sm mt-2">
                Create playbooks to see the knowledge graph visualization.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
