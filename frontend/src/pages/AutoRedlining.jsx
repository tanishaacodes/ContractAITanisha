import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft, FileEdit, Loader, AlertTriangle, CheckCircle,
  Download, Eye, ChevronDown, ChevronUp, Zap, Info
} from 'lucide-react';
import api from '../utils/api';

const RISK_COLOR = { HIGH: 'text-red-400', MEDIUM: 'text-yellow-400', LOW: 'text-green-400', UNKNOWN: 'text-slate-400' };

function DiffViewer({ diff }) {
  if (!diff || diff.length === 0) return <p className="text-slate-500 text-xs">No diff available</p>;
  return (
    <p className="text-xs leading-relaxed font-mono whitespace-pre-wrap">
      {diff.map((token, i) => {
        if (token.type === 'delete')
          return <span key={i} className="bg-red-900/50 text-red-300 line-through px-0.5">{token.text} </span>;
        if (token.type === 'insert')
          return <span key={i} className="bg-green-900/50 text-green-300 px-0.5">{token.text} </span>;
        return <span key={i} className="text-slate-400">{token.text} </span>;
      })}
    </p>
  );
}

function RedlineCard({ r, index }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className={`border rounded-xl transition ${r.needs_redline ? 'border-red-800 bg-red-900/10' : 'border-slate-700 bg-slate-900'}`}>
      <button
        className="w-full flex items-center justify-between p-4 text-left"
        onClick={() => setExpanded(e => !e)}
      >
        <div className="flex items-center gap-3 min-w-0">
          <span className="text-slate-500 text-sm w-6 flex-shrink-0">#{index + 1}</span>
          <div className="min-w-0">
            <p className="text-white font-semibold text-sm truncate">{r.clause_name || r.clause_type}</p>
            <p className="text-xs text-slate-400">{r.clause_type} · Similarity: {(r.similarity * 100).toFixed(1)}%</p>
          </div>
        </div>
        <div className="flex items-center gap-3 flex-shrink-0 ml-3">
          <span className={`text-xs font-semibold ${RISK_COLOR[r.risk_level]}`}>{r.risk_level}</span>
          {r.needs_redline
            ? <span className="flex items-center gap-1 text-xs text-red-400 bg-red-900/30 px-2 py-0.5 rounded-full border border-red-800">
                <AlertTriangle className="w-3 h-3" /> REDLINE
              </span>
            : <span className="flex items-center gap-1 text-xs text-green-400 bg-green-900/30 px-2 py-0.5 rounded-full border border-green-800">
                <CheckCircle className="w-3 h-3" /> OK
              </span>
          }
          {expanded ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
        </div>
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-4 border-t border-slate-800 pt-4">
          {/* Similarity bar */}
          <div>
            <div className="flex justify-between text-xs text-slate-400 mb-1">
              <span>Similarity to Standard Template</span>
              <span className={r.similarity < 0.75 ? 'text-red-400' : 'text-green-400'}>
                {(r.similarity * 100).toFixed(1)}%
              </span>
            </div>
            <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${r.similarity > 0.75 ? 'bg-green-500' : r.similarity > 0.5 ? 'bg-yellow-500' : 'bg-red-500'}`}
                style={{ width: `${r.similarity * 100}%` }}
              />
            </div>
          </div>

          {r.needs_redline && (
            <>
              {/* Side by side */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-xs font-semibold text-red-400 mb-2 flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-red-500" /> Original Text
                  </p>
                  <div className="bg-slate-800/60 rounded-lg p-3 text-xs text-slate-300 leading-relaxed max-h-40 overflow-y-auto">
                    {r.original_text || 'No text available'}
                  </div>
                </div>
                <div>
                  <p className="text-xs font-semibold text-green-400 mb-2 flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-green-500" /> Suggested Redline
                  </p>
                  <div className="bg-slate-800/60 rounded-lg p-3 text-xs text-slate-300 leading-relaxed max-h-40 overflow-y-auto">
                    {r.suggested_text || 'No suggestion generated'}
                  </div>
                </div>
              </div>
              {/* Inline diff */}
              {r.diff && r.diff.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-purple-400 mb-2">Inline Diff</p>
                  <div className="bg-slate-800/60 rounded-lg p-3 max-h-32 overflow-y-auto">
                    <DiffViewer diff={r.diff} />
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default function AutoRedlining() {
  const navigate = useNavigate();
  const { contractId } = useParams();
  const [redlines, setRedlines] = useState(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState('');
  const [threshold, setThreshold] = useState(0.75);
  const [generateSuggestions, setGenerateSuggestions] = useState(true);
  const [filter, setFilter] = useState('all'); // 'all' | 'drifted' | 'ok'

  const runRedline = async () => {
    if (!contractId) { setError('No contract ID provided'); return; }
    try {
      setLoading(true);
      setError('');
      const r = await api.post(`/contracts/${contractId}/redline/`, {
        threshold,
        generate_suggestions: generateSuggestions,
      });
      setRedlines(r.data);
    } catch (e) {
      setError(e.response?.data?.error || 'Redline analysis failed');
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const exportReport = async () => {
    if (!redlines) return;
    try {
      setExporting(true);
      const r = await api.post(`/contracts/${contractId}/redline/export/`, {
        redlines: redlines.redlines,
      }, { responseType: 'blob' });
      const url = URL.createObjectURL(r.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = `redline_${contractId}.txt`;
      a.click();
    } catch (e) {
      console.error(e);
    } finally {
      setExporting(false);
    }
  };

  const filtered = redlines?.redlines?.filter(r => {
    if (filter === 'drifted') return r.needs_redline;
    if (filter === 'ok') return !r.needs_redline;
    return true;
  }) || [];

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button onClick={() => navigate(-1)} className="p-2 hover:bg-slate-800 rounded-lg">
          <ArrowLeft className="w-6 h-6 text-blue-400" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-1">
            <FileEdit className="w-8 h-8 text-orange-400" />
            <h1 className="text-3xl font-bold text-white">Auto Contract Redlining</h1>
          </div>
          <p className="text-slate-400 text-sm">
            AI-powered redline analysis — compare clauses vs standard templates, view inline diffs
          </p>
        </div>
        {redlines && (
          <button onClick={exportReport} disabled={exporting}
            className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-semibold">
            {exporting ? <Loader className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            Export Report
          </button>
        )}
      </div>

      {/* Config Panel */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="flex flex-wrap items-center gap-6">
          <div>
            <label className="text-slate-400 text-xs block mb-1">Similarity Threshold</label>
            <div className="flex items-center gap-3">
              <input type="range" min="0.5" max="0.95" step="0.05" value={threshold}
                onChange={e => setThreshold(parseFloat(e.target.value))}
                className="accent-orange-500 w-32" />
              <span className="text-white font-bold text-sm">{(threshold * 100).toFixed(0)}%</span>
            </div>
            <p className="text-slate-500 text-xs mt-1">Clauses below this similarity will be flagged</p>
          </div>
          <div className="flex items-center gap-2">
            <input type="checkbox" id="genSugg" checked={generateSuggestions}
              onChange={e => setGenerateSuggestions(e.target.checked)}
              className="accent-orange-500 w-4 h-4" />
            <label htmlFor="genSugg" className="text-slate-300 text-sm">
              Generate AI suggestions
            </label>
          </div>
          <button onClick={runRedline} disabled={loading}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-lg font-semibold text-sm transition ${
              loading ? 'bg-slate-700 text-slate-500 cursor-not-allowed' : 'bg-orange-600 hover:bg-orange-700 text-white'
            }`}>
            {loading ? <Loader className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
            {loading ? 'Analyzing...' : 'Run Redline Analysis'}
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-900/20 border border-red-800 rounded-xl p-4 flex gap-3">
          <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
          <p className="text-red-300">{error}</p>
        </div>
      )}

      {/* Results */}
      {redlines && (
        <div className="space-y-4">
          {/* Summary bar */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Total Clauses', value: redlines.total_clauses, color: 'text-blue-400' },
              { label: 'Needs Redline', value: redlines.drifted_clauses, color: 'text-red-400' },
              { label: 'Compliant', value: (redlines.total_clauses - redlines.drifted_clauses), color: 'text-green-400' },
              { label: 'Threshold', value: `${(redlines.threshold * 100).toFixed(0)}%`, color: 'text-orange-400' },
            ].map(k => (
              <div key={k.label} className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center">
                <p className={`text-2xl font-bold ${k.color}`}>{k.value}</p>
                <p className="text-slate-400 text-xs mt-1">{k.label}</p>
              </div>
            ))}
          </div>

          {/* Filter tabs */}
          <div className="flex gap-2">
            {[
              { id: 'all', label: `All (${redlines.total_clauses})` },
              { id: 'drifted', label: `Needs Redline (${redlines.drifted_clauses})` },
              { id: 'ok', label: `Compliant (${redlines.total_clauses - redlines.drifted_clauses})` },
            ].map(f => (
              <button key={f.id} onClick={() => setFilter(f.id)}
                className={`px-3 py-1.5 rounded-lg text-sm font-semibold transition ${
                  filter === f.id ? 'bg-orange-600 text-white' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}>
                {f.label}
              </button>
            ))}
          </div>

          {/* Legend */}
          <div className="flex items-center gap-4 text-xs text-slate-400 bg-slate-900 border border-slate-800 rounded-lg px-4 py-2">
            <Info className="w-3.5 h-3.5" />
            <span className="bg-red-900/50 text-red-300 px-1 rounded">deleted text</span>
            <span className="bg-green-900/50 text-green-300 px-1 rounded">inserted text</span>
            <span className="text-slate-400">unchanged</span>
          </div>

          {/* Clause Cards */}
          <div className="space-y-3">
            {filtered.length === 0 && (
              <div className="text-center py-8 text-slate-400">No clauses match this filter.</div>
            )}
            {filtered.map((r, i) => (
              <RedlineCard key={r.clause_id} r={r} index={i} />
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {!redlines && !loading && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center">
          <FileEdit className="w-16 h-16 text-slate-600 mx-auto mb-4" />
          <p className="text-slate-400 text-lg mb-2">Ready to analyze</p>
          <p className="text-slate-500 text-sm">Configure options above and click "Run Redline Analysis" to compare your contract clauses against standard templates.</p>
        </div>
      )}
    </div>
  );
}
