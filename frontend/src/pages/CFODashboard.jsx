import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft, DollarSign, TrendingUp, AlertTriangle, BarChart2,
  Loader, FileText, Calendar, Layers
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid, Legend, AreaChart, Area,
  Cell
} from 'recharts';
import api from '../utils/api';

const RISK_COLORS = {
  HIGH: '#ef4444',
  MEDIUM: '#f59e0b',
  LOW: '#10b981',
};

const BAR_COLORS = ['#a855f7', '#6366f1', '#3b82f6', '#06b6d4', '#10b981', '#f59e0b', '#f97316', '#ef4444'];

export default function CFODashboard() {
  const navigate = useNavigate();
  const [tab, setTab] = useState('summary');
  const [kpis, setKpis] = useState(null);
  const [lossByType, setLossByType] = useState([]);
  const [lossByContract, setLossByContract] = useState([]);
  const [cashFlow, setCashFlow] = useState([]);
  const [heatmap, setHeatmap] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const [sumR, typeR, contR, cfR, hmR] = await Promise.all([
          api.get('/analytics/cfo/summary/'),
          api.get('/analytics/cfo/loss-by-type/'),
          api.get('/analytics/cfo/loss-by-contract/'),
          api.get('/analytics/cfo/cash-flow/'),
          api.get('/analytics/cfo/risk-heatmap/'),
        ]);
        setKpis(sumR.data.kpis);
        setLossByType(typeR.data.data || []);
        setLossByContract(contR.data.data || []);
        setCashFlow(cfR.data.projection || []);
        setHeatmap(hmR.data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const fmt = (v) => v >= 1e6 ? `$${(v / 1e6).toFixed(1)}M` : v >= 1e3 ? `$${(v / 1e3).toFixed(0)}K` : `$${v.toFixed(0)}`;

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen">
      <Loader className="w-10 h-10 text-green-400 animate-spin" />
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
            <DollarSign className="w-8 h-8 text-green-400" />
            <h1 className="text-3xl font-bold text-white">CFO Financial Analytics</h1>
          </div>
          <p className="text-slate-400 text-sm">Clause-level financial exposure, cash flow projections, and risk heatmap</p>
        </div>
      </div>

      {/* KPI Cards */}
      {kpis && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {[
            { label: 'Total Exposure', value: fmt(kpis.total_exposure), color: 'text-red-400', icon: DollarSign },
            { label: 'Avg Risk Score', value: `${(kpis.avg_risk_score * 100).toFixed(1)}%`, color: 'text-orange-400', icon: TrendingUp },
            { label: 'High Risk Clauses', value: kpis.high_risk_clauses, color: 'text-red-400', icon: AlertTriangle },
            { label: 'Total Clauses', value: kpis.total_clauses, color: 'text-blue-400', icon: FileText },
            { label: 'Contracts', value: kpis.total_contracts, color: 'text-purple-400', icon: Layers },
            { label: 'Per Contract', value: fmt(kpis.exposure_per_contract), color: 'text-yellow-400', icon: DollarSign },
          ].map(k => (
            <div key={k.label} className="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <k.icon className={`w-4 h-4 ${k.color}`} />
                <p className="text-xs text-slate-400">{k.label}</p>
              </div>
              <p className={`text-xl font-bold ${k.color}`}>{k.value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 flex-wrap">
        {[
          { id: 'summary', label: 'Top Exposure' },
          { id: 'bytype', label: 'Loss by Type' },
          { id: 'bycontract', label: 'Loss by Contract' },
          { id: 'cashflow', label: 'Cash Flow' },
          { id: 'heatmap', label: 'Risk Heatmap' },
        ].map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition ${
              tab === t.id ? 'bg-green-600 text-white' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Summary Tab */}
      {tab === 'summary' && kpis && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h2 className="text-lg font-bold text-white mb-4">Top 5 Highest Exposure Clauses</h2>
          <div className="space-y-3">
            {(kpis.top_exposure_clauses || []).map((c, i) => (
              <div key={c.id} className="flex items-center gap-4 bg-slate-800/50 rounded-lg p-3">
                <span className="text-slate-500 font-mono text-sm w-5">#{i + 1}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-white font-semibold text-sm truncate">{c.clause_name}</p>
                  <p className="text-slate-400 text-xs">{c.clause_type} · {c.contract_name}</p>
                </div>
                <div className="text-right">
                  <p className="text-red-400 font-bold">{fmt(c.financial_impact)}</p>
                  <span className={`text-xs px-1.5 py-0.5 rounded ${
                    c.risk_level === 'HIGH' ? 'bg-red-900/40 text-red-400' :
                    c.risk_level === 'MEDIUM' ? 'bg-yellow-900/40 text-yellow-400' :
                    'bg-green-900/40 text-green-400'
                  }`}>{c.risk_level}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Loss By Type Tab */}
      {tab === 'bytype' && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <BarChart2 className="w-5 h-5 text-green-400" />
            Financial Exposure by Clause Type
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={lossByType.slice(0, 12)} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 10 }} tickFormatter={fmt} />
              <YAxis type="category" dataKey="clause_type" tick={{ fill: '#94a3b8', fontSize: 10 }} width={130} />
              <Tooltip
                contentStyle={{ background: '#1e293b', border: '1px solid #475569', borderRadius: 8 }}
                formatter={(v, n) => [fmt(v), n]}
              />
              <Bar dataKey="total_loss" name="Total Exposure" radius={[0, 4, 4, 0]}>
                {lossByType.slice(0, 12).map((_, i) => (
                  <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          {/* Table */}
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-slate-400 text-left border-b border-slate-700">
                  <th className="pb-2">Clause Type</th>
                  <th className="pb-2 text-right">Total Exposure</th>
                  <th className="pb-2 text-right">Avg per Clause</th>
                  <th className="pb-2 text-right">Count</th>
                  <th className="pb-2 text-right">Avg Risk</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {lossByType.map(r => (
                  <tr key={r.clause_type} className="text-slate-300 hover:bg-slate-800/40">
                    <td className="py-2">{r.clause_type}</td>
                    <td className="py-2 text-right text-red-400 font-semibold">{fmt(r.total_loss)}</td>
                    <td className="py-2 text-right">{fmt(r.avg_loss)}</td>
                    <td className="py-2 text-right">{r.clause_count}</td>
                    <td className="py-2 text-right">{(r.avg_risk_score * 100).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Loss By Contract Tab */}
      {tab === 'bycontract' && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h2 className="text-lg font-bold text-white mb-4">Financial Exposure by Contract</h2>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={lossByContract.slice(0, 10)}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="contract_name" tick={{ fill: '#94a3b8', fontSize: 10 }}
                angle={-20} textAnchor="end" height={50} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 10 }} tickFormatter={fmt} />
              <Tooltip
                contentStyle={{ background: '#1e293b', border: '1px solid #475569', borderRadius: 8 }}
                formatter={(v) => [fmt(v), 'Total Exposure']}
              />
              <Bar dataKey="total_loss" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Cash Flow Tab */}
      {tab === 'cashflow' && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h2 className="text-lg font-bold text-white mb-1 flex items-center gap-2">
            <Calendar className="w-5 h-5 text-blue-400" />
            Risk Exposure Cash Flow Projection (24 months)
          </h2>
          <p className="text-slate-400 text-xs mb-4">Projected materialization of financial risk from clause types over time</p>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={cashFlow}>
              <defs>
                <linearGradient id="expGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="cumGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#a855f7" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="month" tick={{ fill: '#94a3b8', fontSize: 10 }} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 10 }} tickFormatter={fmt} />
              <Tooltip
                contentStyle={{ background: '#1e293b', border: '1px solid #475569', borderRadius: 8 }}
                formatter={(v) => [fmt(v)]}
              />
              <Legend />
              <Area type="monotone" dataKey="exposure" stroke="#ef4444" fill="url(#expGrad)" strokeWidth={2} name="Monthly Exposure" />
              <Area type="monotone" dataKey="cumulative" stroke="#a855f7" fill="url(#cumGrad)" strokeWidth={2} name="Cumulative Exposure" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Risk Heatmap Tab */}
      {tab === 'heatmap' && heatmap && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 overflow-x-auto">
          <h2 className="text-lg font-bold text-white mb-4">Risk Heatmap: Clause Type × Contract</h2>
          {heatmap.rows?.length > 0 ? (
            <table className="text-xs border-collapse">
              <thead>
                <tr>
                  <th className="p-2 text-left text-slate-400 border border-slate-700 min-w-[140px]">Clause Type</th>
                  {heatmap.contracts?.map(c => (
                    <th key={c} className="p-2 text-center text-slate-400 border border-slate-700 min-w-[100px]">{c}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {heatmap.rows.map(row => (
                  <tr key={row.clause_type}>
                    <td className="p-2 text-slate-300 border border-slate-700 font-medium">{row.clause_type}</td>
                    {row.values?.map((v, i) => {
                      const risk = v.risk || 0;
                      const alpha = Math.min(risk * 1.5, 1);
                      const bg = risk > 0.7 ? `rgba(239,68,68,${alpha})` :
                                 risk > 0.4 ? `rgba(245,158,11,${alpha})` :
                                 risk > 0 ? `rgba(16,185,129,${alpha * 0.7})` : 'transparent';
                      return (
                        <td key={i} className="p-2 text-center border border-slate-700 font-mono"
                          style={{ background: bg, color: risk > 0.3 ? '#fff' : '#64748b' }}>
                          {risk > 0 ? `${(risk * 100).toFixed(0)}%` : '—'}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-slate-400">No heatmap data available. Process contracts to generate risk scores first.</p>
          )}
        </div>
      )}
    </div>
  );
}
