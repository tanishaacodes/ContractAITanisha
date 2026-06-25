import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft, TrendingUp, TrendingDown, Minus, Loader,
  Brain, AlertTriangle, Activity, ChevronRight
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, ReferenceLine, Area, AreaChart
} from 'recharts';
import api from '../utils/api';

const OUTLOOK_COLOR = { HIGH: 'text-red-400', MEDIUM: 'text-yellow-400', LOW: 'text-green-400' };
const OUTLOOK_BG = {
  HIGH: 'bg-red-900/20 border-red-700',
  MEDIUM: 'bg-yellow-900/20 border-yellow-700',
  LOW: 'bg-green-900/20 border-green-700',
};
const METHOD_BADGE = {
  xgboost: 'bg-blue-900/40 text-blue-300',
  linear: 'bg-purple-900/40 text-purple-300',
  exp_smoothing: 'bg-slate-700 text-slate-300',
  constant: 'bg-slate-700 text-slate-400',
};

export default function PredictiveRiskEngine() {
  const navigate = useNavigate();
  const [forecasts, setForecasts] = useState([]);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [horizon, setHorizon] = useState(6);

  useEffect(() => {
    api.get(`/analytics/predictive-risk/?horizon=${horizon}`)
      .then(r => setForecasts(r.data.forecasts || []))
      .catch(e => console.error(e))
      .finally(() => setLoading(false));
  }, [horizon]);

  const loadDetail = async (clauseType) => {
    setDetailLoading(true);
    setSelected(clauseType);
    try {
      const r = await api.get(`/analytics/predictive-risk/${encodeURIComponent(clauseType)}/?horizon=${horizon}`);
      setDetail(r.data);
    } catch (e) {
      console.error(e);
    } finally {
      setDetailLoading(false);
    }
  };

  const buildChartData = (f) => {
    if (!f) return [];
    const history = (f.history || []).map(h => ({
      month: h.month,
      actual: h.avg_risk,
      predicted: null,
      lower: null,
      upper: null,
    }));
    const forecast = (f.forecast || []).map(p => ({
      month: p.month,
      actual: null,
      predicted: p.predicted_risk,
      lower: p.lower,
      upper: p.upper,
    }));
    return [...history, ...forecast];
  };

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen">
      <Loader className="w-10 h-10 text-blue-400 animate-spin" />
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
            <Brain className="w-8 h-8 text-blue-400" />
            <h1 className="text-3xl font-bold text-white">Predictive Risk Engine</h1>
          </div>
          <p className="text-slate-400 text-sm">XGBoost + Linear regression forecasting of clause risk trajectories</p>
        </div>
        {/* Horizon selector */}
        <div className="ml-auto flex items-center gap-2">
          <span className="text-slate-400 text-sm">Horizon:</span>
          {[3, 6, 12].map(h => (
            <button key={h} onClick={() => setHorizon(h)}
              className={`px-3 py-1 rounded text-sm font-semibold transition ${
                horizon === h ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-300'
              }`}>
              {h}mo
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Forecast List */}
        <div className="lg:col-span-1">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <h2 className="text-sm font-bold text-slate-300 mb-3 uppercase tracking-wide">All Clause Types</h2>
            <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
              {forecasts.length === 0 && (
                <p className="text-slate-400 text-sm text-center py-6">No risk history found.<br />Process contracts first.</p>
              )}
              {forecasts.map(f => (
                <button key={f.clause_type}
                  onClick={() => loadDetail(f.clause_type)}
                  className={`w-full text-left p-3 rounded-lg border transition ${
                    selected === f.clause_type
                      ? 'border-blue-600 bg-blue-900/20'
                      : 'border-slate-700 bg-slate-800/30 hover:border-slate-600'
                  }`}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-semibold text-white truncate pr-2">{f.clause_type}</span>
                    <ChevronRight className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
                  </div>
                  <div className="flex items-center gap-3 text-xs">
                    <span className={OUTLOOK_COLOR[f.risk_outlook]}>
                      {f.risk_outlook === 'HIGH' ? <AlertTriangle className="w-3 h-3 inline mr-0.5" /> : null}
                      {f.risk_outlook}
                    </span>
                    <span className="text-slate-400">
                      {f.trend === 'increasing' ? <TrendingUp className="w-3 h-3 inline text-red-400 mr-0.5" /> :
                       f.trend === 'decreasing' ? <TrendingDown className="w-3 h-3 inline text-green-400 mr-0.5" /> :
                       <Minus className="w-3 h-3 inline text-slate-400 mr-0.5" />}
                      {f.trend}
                    </span>
                    <span className={`px-1.5 py-0.5 rounded text-xs ${METHOD_BADGE[f.method] || 'bg-slate-700 text-slate-400'}`}>
                      {f.method}
                    </span>
                  </div>
                  {/* Mini bar */}
                  <div className="mt-2 h-1 bg-slate-700 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-500 rounded-full"
                      style={{ width: `${Math.min(f.forecast_avg_risk * 100, 100)}%` }} />
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right: Detail Chart */}
        <div className="lg:col-span-2">
          {!detail && !detailLoading && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center">
              <Activity className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400">Select a clause type to see its forecast</p>
            </div>
          )}
          {detailLoading && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 flex justify-center">
              <Loader className="w-8 h-8 text-blue-400 animate-spin" />
            </div>
          )}
          {detail && !detailLoading && (
            <div className="space-y-4">
              {/* KPI row */}
              <div className={`${OUTLOOK_BG[detail.risk_outlook]} border rounded-xl p-5`}>
                <div className="flex items-center justify-between mb-3">
                  <h2 className="text-xl font-bold text-white">{detail.clause_type}</h2>
                  <span className={`font-bold text-lg ${OUTLOOK_COLOR[detail.risk_outlook]}`}>
                    {detail.risk_outlook} RISK OUTLOOK
                  </span>
                </div>
                <div className="grid grid-cols-4 gap-4 text-sm">
                  <div>
                    <p className="text-slate-400 text-xs">Current Risk</p>
                    <p className="text-white font-bold text-base">{(detail.current_avg_risk * 100).toFixed(1)}%</p>
                  </div>
                  <div>
                    <p className="text-slate-400 text-xs">Forecast Avg</p>
                    <p className="text-white font-bold text-base">{(detail.forecast_avg_risk * 100).toFixed(1)}%</p>
                  </div>
                  <div>
                    <p className="text-slate-400 text-xs">Trend</p>
                    <p className="text-white font-bold text-base capitalize">{detail.trend}</p>
                  </div>
                  <div>
                    <p className="text-slate-400 text-xs">Method</p>
                    <span className={`text-xs px-2 py-1 rounded ${METHOD_BADGE[detail.method] || 'bg-slate-700 text-slate-300'}`}>
                      {detail.method}
                    </span>
                  </div>
                </div>
              </div>

              {/* Chart */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                <h3 className="text-sm font-bold text-slate-300 mb-4 uppercase tracking-wide">Risk Score Forecast</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={buildChartData(detail)}>
                    <defs>
                      <linearGradient id="actGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="predGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#a855f7" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="month" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                    <YAxis domain={[0, 1]} tick={{ fill: '#94a3b8', fontSize: 10 }}
                      tickFormatter={v => `${(v * 100).toFixed(0)}%`} />
                    <Tooltip
                      contentStyle={{ background: '#1e293b', border: '1px solid #475569', borderRadius: 8 }}
                      formatter={(v) => v !== null ? [`${(v * 100).toFixed(1)}%`] : ['N/A']}
                    />
                    <Legend />
                    <ReferenceLine y={0.7} stroke="#ef4444" strokeDasharray="4 4"
                      label={{ value: 'High Risk', fill: '#ef4444', fontSize: 10 }} />
                    <Area type="monotone" dataKey="actual" stroke="#3b82f6" fill="url(#actGrad)"
                      strokeWidth={2} name="Historical" connectNulls={false} />
                    <Area type="monotone" dataKey="predicted" stroke="#a855f7" fill="url(#predGrad)"
                      strokeWidth={2} strokeDasharray="5 5" name="Forecast" connectNulls={false} />
                    <Line type="monotone" dataKey="upper" stroke="#a855f7" strokeWidth={1}
                      strokeDasharray="2 2" dot={false} name="Upper CI" opacity={0.5} />
                    <Line type="monotone" dataKey="lower" stroke="#a855f7" strokeWidth={1}
                      strokeDasharray="2 2" dot={false} name="Lower CI" opacity={0.5} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Forecast Table */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <h3 className="text-sm font-bold text-slate-300 mb-3 uppercase tracking-wide">Monthly Forecast</h3>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-slate-400 text-xs text-left border-b border-slate-700">
                      <th className="pb-2">Month</th>
                      <th className="pb-2 text-right">Predicted Risk</th>
                      <th className="pb-2 text-right">Lower</th>
                      <th className="pb-2 text-right">Upper</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {(detail.forecast || []).map(p => (
                      <tr key={p.month} className="text-slate-300">
                        <td className="py-2 font-mono text-xs">{p.month}</td>
                        <td className="py-2 text-right font-semibold">
                          <span className={
                            p.predicted_risk > 0.7 ? 'text-red-400' :
                            p.predicted_risk > 0.4 ? 'text-yellow-400' : 'text-green-400'
                          }>
                            {(p.predicted_risk * 100).toFixed(1)}%
                          </span>
                        </td>
                        <td className="py-2 text-right text-slate-400">{(p.lower * 100).toFixed(1)}%</td>
                        <td className="py-2 text-right text-slate-400">{(p.upper * 100).toFixed(1)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
