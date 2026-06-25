import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft, AlertTriangle, CheckCircle, TrendingDown, TrendingUp,
  Loader, GitCompare, BarChart2, Activity, Info
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid, Legend, ReferenceLine
} from 'recharts';
import api from '../utils/api';

const STATUS_COLOR = { critical: 'red', warning: 'yellow', healthy: 'green' };
const STATUS_BG = {
  critical: 'bg-red-900/30 border-red-700',
  warning: 'bg-yellow-900/30 border-yellow-700',
  healthy: 'bg-green-900/30 border-green-700',
};

export default function ClauseDriftDashboard() {
  const navigate = useNavigate();
  const [summary, setSummary] = useState([]);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [tab, setTab] = useState('overview'); // 'overview' | 'detail' | 'timeline'

  useEffect(() => {
    api.get('/clause-library/drift/summary/')
      .then(r => setSummary(r.data.summary || []))
      .catch(e => console.error(e))
      .finally(() => setLoading(false));
  }, []);

  const loadDetail = async (clauseType) => {
    setDetailLoading(true);
    setSelected(clauseType);
    try {
      const [det, tl] = await Promise.all([
        api.get(`/clause-library/drift/type/${encodeURIComponent(clauseType)}/`),
        api.get(`/clause-library/drift/timeline/${encodeURIComponent(clauseType)}/`),
      ]);
      setDetail(det.data);
      setTimeline(tl.data.timeline || []);
      setTab('detail');
    } catch (e) {
      console.error(e);
    } finally {
      setDetailLoading(false);
    }
  };

  const criticalCount = summary.filter(s => s.status === 'critical').length;
  const warningCount = summary.filter(s => s.status === 'warning').length;
  const healthyCount = summary.filter(s => s.status === 'healthy').length;

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen">
      <Loader className="w-10 h-10 text-purple-400 animate-spin" />
    </div>
  );

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button onClick={() => navigate(-1)} className="p-2 hover:bg-slate-800 rounded-lg">
          <ArrowLeft className="w-6 h-6 text-blue-400" />
        </button>
        <div>
          <div className="flex items-center gap-3 mb-1">
            <GitCompare className="w-8 h-8 text-purple-400" />
            <h1 className="text-3xl font-bold text-white">Clause Drift Detection</h1>
          </div>
          <p className="text-slate-400 text-sm">BERT cosine similarity across contracts — identify deviating clauses</p>
        </div>
      </div>

      {/* KPI Bar */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Critical Drift', count: criticalCount, color: 'text-red-400', bg: 'bg-red-900/20 border-red-800' },
          { label: 'Warning', count: warningCount, color: 'text-yellow-400', bg: 'bg-yellow-900/20 border-yellow-800' },
          { label: 'Healthy', count: healthyCount, color: 'text-green-400', bg: 'bg-green-900/20 border-green-800' },
        ].map(k => (
          <div key={k.label} className={`${k.bg} border rounded-xl p-4 text-center`}>
            <p className={`text-3xl font-bold ${k.color}`}>{k.count}</p>
            <p className="text-slate-400 text-sm mt-1">{k.label}</p>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-2">
        {['overview', 'detail', 'timeline'].map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-lg text-sm font-semibold capitalize transition ${
              tab === t ? 'bg-purple-600 text-white' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {tab === 'overview' && (
        <div className="space-y-4">
          {/* Bar chart: drift rate by clause type */}
          {summary.length > 0 && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <BarChart2 className="w-5 h-5 text-purple-400" />
                Drift Rate by Clause Type
              </h2>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={summary.slice(0, 12)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="clause_type" tick={{ fill: '#94a3b8', fontSize: 10 }}
                    angle={-25} textAnchor="end" height={50} />
                  <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} tickFormatter={v => `${(v * 100).toFixed(0)}%`} />
                  <Tooltip
                    contentStyle={{ background: '#1e293b', border: '1px solid #475569', borderRadius: 8 }}
                    formatter={(v) => [`${(v * 100).toFixed(1)}%`, 'Drift Rate']}
                  />
                  <ReferenceLine y={0.5} stroke="#ef4444" strokeDasharray="4 4" label={{ value: 'Critical', fill: '#ef4444', fontSize: 10 }} />
                  <ReferenceLine y={0.2} stroke="#f59e0b" strokeDasharray="4 4" label={{ value: 'Warning', fill: '#f59e0b', fontSize: 10 }} />
                  <Bar dataKey="drift_rate" fill="#a855f7" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {summary.map(s => (
              <button
                key={s.clause_type}
                onClick={() => loadDetail(s.clause_type)}
                className={`${STATUS_BG[s.status]} border rounded-xl p-4 text-left hover:scale-[1.01] transition`}
              >
                <div className="flex items-start justify-between mb-2">
                  <span className="font-semibold text-white text-sm">{s.clause_type}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full border font-bold
                    ${s.status === 'critical' ? 'border-red-600 text-red-400 bg-red-900/30' :
                      s.status === 'warning' ? 'border-yellow-600 text-yellow-400 bg-yellow-900/30' :
                      'border-green-600 text-green-400 bg-green-900/30'}`}>
                    {s.status.toUpperCase()}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-xs text-slate-400">
                  <div>
                    <p className="text-white font-bold">{(s.drift_rate * 100).toFixed(0)}%</p>
                    <p>Drift Rate</p>
                  </div>
                  <div>
                    <p className="text-white font-bold">{s.drifted_count}/{s.total_count}</p>
                    <p>Drifted</p>
                  </div>
                  <div>
                    <p className="text-white font-bold">{s.avg_similarity ? (s.avg_similarity * 100).toFixed(0) + '%' : 'N/A'}</p>
                    <p>Avg Sim</p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Detail Tab */}
      {tab === 'detail' && (
        <div className="space-y-4">
          {!detail && !detailLoading && (
            <div className="text-center py-12 text-slate-400">
              Select a clause type from the Overview tab to see details.
            </div>
          )}
          {detailLoading && (
            <div className="flex justify-center py-12">
              <Loader className="w-8 h-8 text-purple-400 animate-spin" />
            </div>
          )}
          {detail && !detailLoading && (
            <>
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                <h2 className="text-xl font-bold text-white mb-1">{detail.clause_type}</h2>
                <p className="text-slate-400 text-sm mb-4">
                  {detail.drifted_count} / {detail.total_count} clauses drifted
                  &nbsp;·&nbsp; Avg similarity: {detail.avg_similarity ? (detail.avg_similarity * 100).toFixed(1) + '%' : 'N/A'}
                </p>
                {detail.standard && (
                  <div className="bg-blue-900/20 border border-blue-800 rounded-lg p-3 mb-4">
                    <p className="text-xs text-blue-300 font-semibold mb-1">Standard Template (from: {detail.standard.contract_name})</p>
                    <p className="text-slate-300 text-xs">{detail.standard.text?.slice(0, 300)}...</p>
                  </div>
                )}
                <div className="space-y-3">
                  {(detail.clauses || []).map(c => (
                    <div key={c.id} className={`border rounded-lg p-3 ${c.is_drifted ? 'border-red-800 bg-red-900/10' : 'border-slate-700 bg-slate-800/30'}`}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-semibold text-white">{c.clause_name || c.id.slice(0, 8)}</span>
                        <div className="flex items-center gap-2">
                          {c.is_drifted
                            ? <span className="text-xs text-red-400 flex items-center gap-1"><AlertTriangle className="w-3 h-3" /> DRIFTED</span>
                            : <span className="text-xs text-green-400 flex items-center gap-1"><CheckCircle className="w-3 h-3" /> OK</span>
                          }
                          <span className="text-xs text-slate-400">{(c.similarity * 100).toFixed(1)}% match</span>
                        </div>
                      </div>
                      <p className="text-xs text-slate-500">{c.contract_name} · {c.risk_level}</p>
                      {/* Similarity bar */}
                      <div className="mt-2 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${c.similarity > 0.75 ? 'bg-green-500' : c.similarity > 0.5 ? 'bg-yellow-500' : 'bg-red-500'}`}
                          style={{ width: `${c.similarity * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* Timeline Tab */}
      {tab === 'timeline' && (
        <div className="space-y-4">
          {!timeline.length && (
            <div className="text-center py-12 text-slate-400">
              Select a clause type from Overview to see its drift timeline.
            </div>
          )}
          {timeline.length > 0 && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <Activity className="w-5 h-5 text-purple-400" />
                Drift Timeline — {selected}
              </h2>
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={timeline}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 10 }}
                    tickFormatter={v => v?.slice(0, 10)} angle={-20} textAnchor="end" height={40} />
                  <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} domain={[0, 1]} tickFormatter={v => `${(v * 100).toFixed(0)}%`} />
                  <Tooltip
                    contentStyle={{ background: '#1e293b', border: '1px solid #475569', borderRadius: 8 }}
                    formatter={(v, n) => [`${(v * 100).toFixed(1)}%`, n]}
                    labelFormatter={l => l?.slice(0, 10)}
                  />
                  <Legend />
                  <ReferenceLine y={0.75} stroke="#10b981" strokeDasharray="5 5" label={{ value: 'Threshold (75%)', fill: '#10b981', fontSize: 10 }} />
                  <Line type="monotone" dataKey="similarity" stroke="#a855f7" strokeWidth={2} dot={{ fill: '#a855f7', r: 4 }} name="Similarity" />
                  <Line type="monotone" dataKey="drift_score" stroke="#ef4444" strokeWidth={2} dot={false} name="Drift Score" strokeDasharray="4 4" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
