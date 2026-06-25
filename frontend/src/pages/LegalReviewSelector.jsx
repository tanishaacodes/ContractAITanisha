/**
 * Legal Review – Contract Selector + Portfolio Risk Heatmap
 * Route: /legal-review
 * Tab 1: Select a contract → navigate to /contracts/:id/legal-review
 * Tab 2: Portfolio Risk Heatmap — real ₹ exposure across ALL contracts
 */

import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  Scale, Search, Loader2, AlertTriangle, ChevronRight,
  FileText, RefreshCw, Calendar, Building2, Globe,
  TrendingUp, BarChart3, IndianRupee, ShieldAlert, Layers,
  ArrowUpRight, Info, CheckCircle, XCircle, Sparkles,
  Activity, Shield, Zap,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Cell, ResponsiveContainer,
  PieChart, Pie, Legend, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, CartesianGrid,
} from 'recharts';
import useAuthStore from '../store/authStore';

const API_BASE = (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));

const RISK_COLORS = {
  HIGH:       { text: 'text-red-400',    bg: 'bg-red-500/15',     border: 'border-red-500/30',    hex: '#F16667' },
  CRITICAL:   { text: 'text-red-500',    bg: 'bg-red-600/20',     border: 'border-red-600/40',    hex: '#ef4444' },
  MEDIUM:     { text: 'text-yellow-400', bg: 'bg-yellow-500/15',  border: 'border-yellow-500/30', hex: '#FFD86E' },
  LOW:        { text: 'text-green-400',  bg: 'bg-green-500/15',   border: 'border-green-500/30',  hex: '#68BC00' },
  UNANALYZED: { text: 'text-slate-400',  bg: 'bg-slate-500/15',   border: 'border-slate-500/30',  hex: '#475569' },
  UNKNOWN:    { text: 'text-slate-400',  bg: 'bg-slate-500/15',   border: 'border-slate-500/30',  hex: '#64748b' },
};

const getRiskStyle = (r) => RISK_COLORS[(r || '').toUpperCase()] || RISK_COLORS.UNKNOWN;

const formatINR = (n) => {
  if (!n || n === 0) return '—';
  if (n >= 1e7)  return `₹${(n / 1e7).toFixed(2)} Cr`;
  if (n >= 1e5)  return `₹${(n / 1e5).toFixed(2)} L`;
  if (n >= 1e3)  return `₹${(n / 1e3).toFixed(1)} K`;
  return `₹${n.toFixed(0)}`;
};

const TABS = [
  { id: 'select',   label: 'Select Contract',       icon: FileText },
  { id: 'heatmap',  label: 'Portfolio Risk Heatmap', icon: BarChart3 },
];

const TOOLTIP_STYLE = { background: '#0f172a', border: '1px solid #334155', borderRadius: 8, fontSize: 11, color: '#e2e8f0' };

// ─────────────────────────────────────────────────────────
// CUSTOM TOOLTIP
// ─────────────────────────────────────────────────────────
const CustomBarTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  const rs = getRiskStyle(d.risk_level);
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-3 shadow-xl min-w-[200px]">
      <p className="text-white text-xs font-semibold mb-2 truncate">{d.name}</p>
      <div className="space-y-1">
        <div className="flex justify-between gap-4">
          <span className="text-slate-400 text-[10px]">Contract Value</span>
          <span className="text-blue-300 text-[10px] font-bold">{formatINR(d.value)}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-slate-400 text-[10px]">Risk Exposure</span>
          <span className="text-red-400 text-[10px] font-bold">{formatINR(d.exposure)}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-slate-400 text-[10px]">Risk Level</span>
          <span className={`text-[10px] font-bold ${rs.text}`}>{d.risk_level}</span>
        </div>
        {d.risk_score > 0 && (
          <div className="flex justify-between gap-4">
            <span className="text-slate-400 text-[10px]">Risk Score</span>
            <span className="text-violet-300 text-[10px] font-bold">{d.risk_score}/100</span>
          </div>
        )}
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────
// PORTFOLIO HEATMAP TAB
// ─────────────────────────────────────────────────────────
const PortfolioHeatmap = ({ token }) => {
  const navigate = useNavigate();
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);
  const [sortBy, setSortBy]   = useState('exposure');
  const [riskFilter, setRiskFilter] = useState('');

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(`${API_BASE}/api/legal-review/portfolio-heatmap`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setData(res.data);
    } catch {
      setError('Failed to load portfolio data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  if (loading) return (
    <div className="flex items-center justify-center py-32 gap-3">
      <Loader2 size={28} className="animate-spin text-violet-400" />
      <p className="text-slate-400 text-sm">Analysing portfolio risk…</p>
    </div>
  );

  if (error) return (
    <div className="flex flex-col items-center justify-center py-20 gap-4">
      <AlertTriangle size={36} className="text-red-400" />
      <p className="text-red-400 text-sm">{error}</p>
      <button onClick={fetchData} className="flex items-center gap-2 px-4 py-2 rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-sm">
        <RefreshCw size={14} /> Retry
      </button>
    </div>
  );

  if (!data) return null;

  const { contracts, summary } = data;
  const { total_value, total_exposure, risk_breakdown, type_exposure, jurisdiction_exposure, total_contracts } = summary;

  // Bar chart top 8
  const barData = contracts.slice(0, 8).map(c => ({
    ...c,
    name: c.name.length > 20 ? c.name.slice(0, 20) + '…' : c.name,
  }));

  // Pie data
  const pieData = [
    { name: 'CRITICAL',   value: (risk_breakdown.CRITICAL   || 0), fill: '#ef4444' },
    { name: 'HIGH',       value: (risk_breakdown.HIGH       || 0), fill: '#F16667' },
    { name: 'MEDIUM',     value: (risk_breakdown.MEDIUM     || 0), fill: '#FFD86E' },
    { name: 'LOW',        value: (risk_breakdown.LOW        || 0), fill: '#68BC00' },
    { name: 'UNANALYZED', value: (risk_breakdown.UNANALYZED || 0), fill: '#475569' },
  ].filter(d => d.value > 0);

  // Radar by type
  const radarData = (type_exposure || []).slice(0, 6).map(([type, exp]) => ({
    type: type.slice(0, 16),
    exposure: exp,
  }));

  // Sorted + filtered table
  const tableRows = [...contracts]
    .filter(c => !riskFilter || c.risk_level === riskFilter)
    .sort((a, b) => {
      if (sortBy === 'exposure') return b.exposure - a.exposure;
      if (sortBy === 'value')    return b.value - a.value;
      if (sortBy === 'risk')     return b.risk_score - a.risk_score;
      return 0;
    });

  const exposurePct = total_value > 0 ? ((total_exposure / total_value) * 100).toFixed(1) : 0;

  return (
    <div className="space-y-6">

      {/* Info banner */}
      <div className="flex items-start gap-3 bg-gradient-to-r from-violet-900/30 to-blue-900/20 border border-violet-500/30 rounded-xl px-4 py-3">
        <Info size={14} className="text-violet-400 mt-0.5 shrink-0" />
        <p className="text-slate-300 text-xs leading-relaxed">
          Exposure = <span className="text-violet-300 font-semibold">Contract Value × Risk Multiplier</span> (CRITICAL=50%, HIGH=35%, MEDIUM=15%, LOW=5%).
          Risk levels pulled from real AI risk analysis. Click any row to open full Legal Review.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-7 gap-3">
        {[
          { label: 'Total Portfolio',    value: formatINR(total_value),    color: 'text-blue-400',   border: 'border-blue-500/30',    bg: 'bg-blue-500/10',   icon: IndianRupee,  sub: `${total_contracts} contracts` },
          { label: 'Total Exposure',     value: formatINR(total_exposure), color: 'text-red-400',    border: 'border-red-500/30',     bg: 'bg-red-500/10',    icon: ShieldAlert,  sub: `${exposurePct}% of portfolio` },
          { label: 'Critical Risk',  value: risk_breakdown.CRITICAL   || 0, color: 'text-red-500',    border: 'border-red-600/30',    bg: 'bg-red-600/10',    icon: XCircle,      sub: 'contracts' },
          { label: 'High Risk',     value: risk_breakdown.HIGH       || 0, color: 'text-red-400',    border: 'border-red-500/30',    bg: 'bg-red-500/10',    icon: AlertTriangle, sub: 'contracts' },
          { label: 'Medium Risk',   value: risk_breakdown.MEDIUM     || 0, color: 'text-yellow-400', border: 'border-yellow-500/30', bg: 'bg-yellow-500/10', icon: Activity,     sub: 'contracts' },
          { label: 'Low Risk',      value: risk_breakdown.LOW        || 0, color: 'text-green-400',  border: 'border-green-500/30',  bg: 'bg-green-500/10',  icon: CheckCircle,  sub: 'contracts' },
          { label: 'Not Analyzed',  value: risk_breakdown.UNANALYZED || 0, color: 'text-slate-400',  border: 'border-slate-600/30',  bg: 'bg-slate-700/20',  icon: Zap,          sub: 'run Legal Review' },
        ].map((k, i) => (
          <div key={i} className={`${k.bg} border ${k.border} rounded-xl p-4 text-center relative overflow-hidden`}>
            <div className={`absolute top-0 right-0 w-16 h-16 rounded-full opacity-10 blur-xl ${k.bg}`} />
            <k.icon size={16} className={`${k.color} mx-auto mb-2`} />
            <p className="text-slate-500 text-[9px] uppercase tracking-widest mb-1">{k.label}</p>
            <p className={`text-2xl font-bold ${k.color}`}>{k.value}</p>
            <p className="text-slate-600 text-[9px] mt-0.5">{k.sub}</p>
          </div>
        ))}
      </div>

      {/* Charts row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">

        {/* Bar chart — 3/5 width */}
        <div className="lg:col-span-3 bg-slate-800/60 border border-slate-700/50 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-1">
            <BarChart3 size={15} className="text-violet-400" />
            <p className="text-slate-200 text-sm font-semibold">Top Contracts by Risk Exposure</p>
          </div>
          <p className="text-slate-500 text-xs mb-4">Click any bar to open Legal Review for that contract</p>
          <ResponsiveContainer width="100%" height={230}>
            <BarChart data={barData} margin={{ top: 5, right: 5, bottom: 55, left: 5 }}
              onClick={d => d?.activePayload?.[0]?.payload?.id && navigate(`/contracts/${d.activePayload[0].payload.id}/legal-review`)}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 9 }} angle={-40} textAnchor="end" interval={0} />
              <YAxis tick={{ fill: '#64748b', fontSize: 10 }} tickFormatter={v => formatINR(v)} width={70} />
              <Tooltip content={<CustomBarTooltip />} />
              <Bar dataKey="exposure" barSize={26} radius={[6, 6, 0, 0]} cursor="pointer">
                {barData.map((d, i) => (
                  <Cell key={i} fill={getRiskStyle(d.risk_level).hex}
                    style={{ filter: `drop-shadow(0 0 6px ${getRiskStyle(d.risk_level).hex}60)` }} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Pie — 2/5 width */}
        <div className="lg:col-span-2 bg-slate-800/60 border border-slate-700/50 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <ShieldAlert size={15} className="text-red-400" />
            <p className="text-slate-200 text-sm font-semibold">Contracts by Risk Level</p>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name"
                cx="50%" cy="50%" outerRadius={80} innerRadius={45}
                label={({ name, value }) => `${name} (${value})`}
                labelLine={{ stroke: '#475569' }}>
                {pieData.map((d, i) => (
                  <Cell key={i} fill={d.fill} style={{ filter: `drop-shadow(0 0 4px ${d.fill}50)` }} />
                ))}
              </Pie>
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v, n) => [`${v} contracts`, n]} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

        {/* Radar by contract type */}
        {radarData.length > 2 && (
          <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5">
            <div className="flex items-center gap-2 mb-4">
              <Layers size={15} className="text-cyan-400" />
              <p className="text-slate-200 text-sm font-semibold">Exposure by Contract Type</p>
            </div>
            <ResponsiveContainer width="100%" height={220}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#334155" />
                <PolarAngleAxis dataKey="type" tick={{ fill: '#94a3b8', fontSize: 9 }} />
                <PolarRadiusAxis angle={90} tick={false} axisLine={false} />
                <Radar name="Exposure" dataKey="exposure" stroke="#a78bfa" fill="#a78bfa" fillOpacity={0.2} strokeWidth={2} />
                <Tooltip contentStyle={TOOLTIP_STYLE} formatter={v => [formatINR(v), 'Exposure']} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Jurisdiction breakdown */}
        <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <Globe size={15} className="text-amber-400" />
            <p className="text-slate-200 text-sm font-semibold">Exposure by Jurisdiction</p>
          </div>
          {(jurisdiction_exposure || []).length === 0 || (jurisdiction_exposure.length === 1 && jurisdiction_exposure[0][0] === 'Unknown') ? (
            <div className="flex flex-col items-center justify-center h-[180px] gap-2">
              <Globe size={28} className="text-slate-600" />
              <p className="text-slate-500 text-xs">No jurisdiction data in contracts</p>
            </div>
          ) : (
            <div className="space-y-3">
              {(jurisdiction_exposure || []).map(([jur, exp], i) => {
                const pct = total_exposure > 0 ? (exp / total_exposure) * 100 : 0;
                return (
                  <div key={i}>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-slate-300 text-xs font-medium flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-amber-400 shrink-0" />
                        {jur}
                      </span>
                      <div className="flex items-center gap-3">
                        <span className="text-slate-500 text-[10px]">{pct.toFixed(1)}%</span>
                        <span className="text-amber-400 text-xs font-bold">{formatINR(exp)}</span>
                      </div>
                    </div>
                    <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div className="h-full rounded-full transition-all duration-700"
                        style={{ width: `${pct}%`, background: 'linear-gradient(90deg, #f59e0b, #fbbf24)' }} />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Full table */}
      <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl overflow-hidden">
        {/* Table header */}
        <div className="flex items-center gap-3 px-5 py-4 border-b border-slate-700/50 flex-wrap gap-y-2">
          <div className="flex items-center gap-2">
            <TrendingUp size={15} className="text-violet-400" />
            <p className="text-slate-200 text-sm font-semibold">All Contracts — Risk Exposure Table</p>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-violet-500/20 text-violet-300 border border-violet-500/30 font-semibold">
              {tableRows.length} contracts
            </span>
          </div>
          <div className="ml-auto flex items-center gap-2 flex-wrap">
            {/* Risk filter */}
            <select value={riskFilter} onChange={e => setRiskFilter(e.target.value)}
              className="bg-slate-700 border border-slate-600 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 outline-none">
              <option value="">All Risk Levels</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
              <option value="UNANALYZED">Not Analyzed</option>
            </select>
            {/* Sort */}
            <select value={sortBy} onChange={e => setSortBy(e.target.value)}
              className="bg-slate-700 border border-slate-600 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 outline-none">
              <option value="exposure">Sort: Exposure</option>
              <option value="value">Sort: Value</option>
              <option value="risk">Sort: Risk Score</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-slate-700/50 bg-slate-900/30">
                {['Contract', 'Type', 'Value', 'Risk', 'Score', 'Exposure', 'Deviations', 'Jurisdiction', 'Action'].map((h, i) => (
                  <th key={i} className="text-left text-slate-500 font-semibold uppercase tracking-wider px-4 py-3 whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/30">
              {tableRows.map((c, i) => {
                const rs = getRiskStyle(c.risk_level);
                const hasRisk = c.has_risk_analysis;
                return (
                  <tr key={i} onClick={() => navigate(`/contracts/${c.id}/legal-review`)}
                    className="hover:bg-slate-700/30 cursor-pointer transition-colors group">

                    {/* Contract name */}
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-lg bg-violet-500/15 border border-violet-500/30 flex items-center justify-center shrink-0">
                          <FileText size={12} className="text-violet-400" />
                        </div>
                        <div>
                          <p className="text-slate-200 font-semibold truncate max-w-[180px] group-hover:text-violet-300 transition-colors">{c.name}</p>
                          {c.party_b && <p className="text-slate-500 text-[10px] truncate max-w-[180px]">{c.party_b}</p>}
                        </div>
                      </div>
                    </td>

                    {/* Type */}
                    <td className="px-4 py-3">
                      <span className="text-slate-400 truncate max-w-[120px] block">{c.contract_type || '—'}</span>
                    </td>

                    {/* Value */}
                    <td className="px-4 py-3">
                      <span className={`font-mono font-semibold ${c.value > 0 ? 'text-blue-300' : 'text-slate-600'}`}>
                        {formatINR(c.value)}
                      </span>
                    </td>

                    {/* Risk badge */}
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5">
                        <span className={`px-2 py-0.5 rounded-full border text-[10px] font-bold whitespace-nowrap ${rs.text} ${rs.bg} ${rs.border}`}>
                          {c.risk_level}
                        </span>
                        {!hasRisk && (
                          <span className="text-[9px] text-slate-500" title="No AI analysis yet">N/A</span>
                        )}
                      </div>
                    </td>

                    {/* Risk score bar */}
                    <td className="px-4 py-3">
                      {c.risk_score > 0 ? (
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                            <div className="h-full rounded-full" style={{
                              width: `${Math.min(c.risk_score, 100)}%`,
                              background: rs.hex,
                            }} />
                          </div>
                          <span className={`font-mono text-[10px] ${rs.text}`}>{c.risk_score}</span>
                        </div>
                      ) : <span className="text-slate-600">—</span>}
                    </td>

                    {/* Exposure */}
                    <td className="px-4 py-3">
                      {c.exposure > 0 ? (
                        <div>
                          <span className="text-red-400 font-bold font-mono">{formatINR(c.exposure)}</span>
                          <p className="text-slate-600 text-[9px]">{(c.multiplier * 100).toFixed(0)}% multiplier</p>
                        </div>
                      ) : <span className="text-slate-600">—</span>}
                    </td>

                    {/* Deviations */}
                    <td className="px-4 py-3">
                      {c.total_deviations > 0 ? (
                        <div className="flex items-center gap-1">
                          {c.critical_issues > 0 && (
                            <span className="text-[9px] px-1.5 py-0.5 rounded bg-red-500/20 text-red-400 font-bold">{c.critical_issues}C</span>
                          )}
                          {c.medium_issues > 0 && (
                            <span className="text-[9px] px-1.5 py-0.5 rounded bg-yellow-500/20 text-yellow-400 font-bold">{c.medium_issues}M</span>
                          )}
                          {c.low_issues > 0 && (
                            <span className="text-[9px] px-1.5 py-0.5 rounded bg-green-500/20 text-green-400 font-bold">{c.low_issues}L</span>
                          )}
                        </div>
                      ) : <span className="text-slate-600">—</span>}
                    </td>

                    {/* Jurisdiction */}
                    <td className="px-4 py-3 text-slate-400">{c.jurisdiction || '—'}</td>

                    {/* Action */}
                    <td className="px-4 py-3">
                      <span className="flex items-center gap-1 text-violet-400 group-hover:text-violet-300 font-semibold whitespace-nowrap">
                        Analyze <ArrowUpRight size={11} />
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────
// MAIN PAGE
// ─────────────────────────────────────────────────────────
export default function LegalReviewSelector() {
  const navigate = useNavigate();
  const { token } = useAuthStore();

  const [activeTab, setActiveTab] = useState('select');
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState(null);
  const [search, setSearch]       = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const fetchContracts = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(`${API_BASE}/api/contracts/list`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const list = Array.isArray(res.data) ? res.data : (res.data.results || res.data.contracts || []);
      setContracts(list);
    } catch {
      setError('Failed to load contracts. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchContracts(); }, []);

  const filtered = contracts.filter(c => {
    const q = search.toLowerCase();
    const name = c.originalFilename || c.original_filename || c.filename || c.title || c.name || '';
    const matchSearch = !q ||
      name.toLowerCase().includes(q) ||
      (c.counterparty || c.partyB || '').toLowerCase().includes(q) ||
      (c.jurisdiction || '').toLowerCase().includes(q);
    const matchStatus = !statusFilter || (c.status || '').toLowerCase() === statusFilter.toLowerCase();
    return matchSearch && matchStatus;
  });

  const statuses = [...new Set(contracts.map(c => c.status).filter(Boolean))];

  return (
    <div className="px-4 lg:px-8 py-6 space-y-5 min-h-screen">

      {/* Header */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-violet-600/30 to-purple-600/20 border border-violet-500/40 flex items-center justify-center shadow-lg shadow-violet-500/20">
            <Scale size={22} className="text-violet-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-white">Adv. Legal Review</h1>
              <span className="bg-gradient-to-r from-violet-500/20 to-purple-500/20 text-violet-300 text-xs px-2 py-0.5 rounded-full border border-violet-500/30 font-medium flex items-center gap-1">
                <Sparkles size={10} /> AI-Powered
              </span>
            </div>
            <p className="text-slate-400 text-xs mt-0.5">
              {activeTab === 'select'
                ? 'Select a contract for clause-by-clause AI legal analysis'
                : 'Real ₹ risk exposure across your entire contract portfolio'}
            </p>
          </div>
        </div>
        <button onClick={fetchContracts}
          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-sm transition-all">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-slate-700/50">
        {TABS.map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium transition-all border-b-2 -mb-px ${
              activeTab === tab.id
                ? 'border-violet-500 text-violet-300 bg-violet-500/10'
                : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}>
            <tab.icon size={13} />
            {tab.label}
            {tab.id === 'heatmap' && contracts.length > 0 && (
              <span className="ml-1 text-[9px] px-1.5 py-0.5 rounded-full bg-red-500/20 text-red-300 font-bold border border-red-500/30 animate-pulse">
                {contracts.length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* SELECT CONTRACT TAB */}
      {activeTab === 'select' && (
        <>
          {loading && (
            <div className="flex items-center justify-center py-20 gap-3">
              <Loader2 size={28} className="animate-spin text-violet-400" />
              <p className="text-slate-400 text-sm">Loading your contracts…</p>
            </div>
          )}
          {error && !loading && (
            <div className="flex flex-col items-center justify-center py-16 gap-4">
              <AlertTriangle size={36} className="text-red-400" />
              <p className="text-red-400 text-sm">{error}</p>
              <button onClick={fetchContracts} className="flex items-center gap-2 px-4 py-2 rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-sm">
                <RefreshCw size={14} /> Retry
              </button>
            </div>
          )}
          {!loading && !error && (
            <div className="space-y-4">
              {/* Search + filter */}
              <div className="flex gap-3 flex-wrap">
                <div className="flex items-center gap-2 flex-1 min-w-[220px] bg-slate-800/80 border border-slate-700 rounded-xl px-4 py-2.5 focus-within:border-violet-500/60 transition-colors">
                  <Search size={14} className="text-slate-400 shrink-0" />
                  <input value={search} onChange={e => setSearch(e.target.value)}
                    placeholder="Search by name, counterparty, jurisdiction…"
                    className="flex-1 bg-transparent text-sm text-slate-200 placeholder-slate-500 outline-none" />
                </div>
                {statuses.length > 0 && (
                  <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
                    className="bg-slate-800 border border-slate-700 rounded-xl px-3 py-2.5 text-sm text-slate-200 outline-none focus:border-violet-500">
                    <option value="">All Statuses</option>
                    {statuses.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                )}
                <div className="flex items-center px-3 py-2.5 bg-slate-800/60 border border-slate-700/50 rounded-xl">
                  <span className="text-slate-400 text-xs">{filtered.length} contract{filtered.length !== 1 ? 's' : ''}</span>
                </div>
              </div>

              {filtered.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
                  <FileText size={40} className="text-slate-600" />
                  <p className="text-slate-400 text-sm">
                    {search || statusFilter ? 'No contracts match your filter.' : 'No contracts found. Upload a contract first.'}
                  </p>
                  {!search && !statusFilter && (
                    <button onClick={() => navigate('/upload')}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-sm">
                      Upload Contract
                    </button>
                  )}
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                  {filtered.map(contract => {
                    const riskStyle = getRiskStyle(contract.risk_level || contract.overall_risk);
                    const id = contract.id || contract.contract_id;
                    const name = contract.originalFilename || contract.original_filename || contract.filename || contract.title || contract.name || `Contract ${id?.slice(0,8)}`;
                    return (
                      <button key={id} onClick={() => navigate(`/contracts/${id}/legal-review`)}
                        className="group text-left bg-slate-800/60 border border-slate-700/50 rounded-xl p-5 hover:border-violet-500/50 hover:bg-slate-800/90 hover:shadow-xl hover:shadow-violet-500/10 transition-all relative overflow-hidden">
                        {/* Glow */}
                        <div className="absolute top-0 right-0 w-24 h-24 bg-violet-500/5 rounded-full blur-2xl group-hover:bg-violet-500/10 transition-all" />

                        <div className="flex items-start justify-between gap-3 mb-3">
                          <div className="w-9 h-9 rounded-lg bg-violet-600/15 border border-violet-500/30 flex items-center justify-center shrink-0">
                            <FileText size={16} className="text-violet-400" />
                          </div>
                          <div className="flex items-center gap-2">
                            {(contract.risk_level || contract.overall_risk) && (
                              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${riskStyle.text} ${riskStyle.bg} ${riskStyle.border}`}>
                                {(contract.risk_level || contract.overall_risk || '').toUpperCase()}
                              </span>
                            )}
                            <ChevronRight size={16} className="text-slate-500 group-hover:text-violet-400 transition-colors" />
                          </div>
                        </div>

                        <p className="text-white text-sm font-semibold leading-snug mb-1 group-hover:text-violet-200 transition-colors line-clamp-2">
                          {name}
                        </p>

                        <div className="space-y-1.5 mt-3">
                          {(contract.partyB || contract.counterparty) && (
                            <div className="flex items-center gap-2 text-slate-400 text-xs">
                              <Building2 size={11} className="shrink-0" />
                              <span className="truncate">{contract.partyB || contract.counterparty}</span>
                            </div>
                          )}
                          {contract.jurisdiction && (
                            <div className="flex items-center gap-2 text-slate-400 text-xs">
                              <Globe size={11} className="shrink-0" />
                              <span>{contract.jurisdiction}</span>
                            </div>
                          )}
                          {(contract.uploadedAt || contract.uploaded_at || contract.created_at) && (
                            <div className="flex items-center gap-2 text-slate-400 text-xs">
                              <Calendar size={11} className="shrink-0" />
                              <span>{new Date(contract.uploadedAt || contract.uploaded_at || contract.created_at).toLocaleDateString()}</span>
                            </div>
                          )}
                          {(contract.contractValue || contract.contract_value) && (
                            <div className="flex items-center gap-2 text-blue-400 text-xs font-semibold">
                              <IndianRupee size={11} className="shrink-0" />
                              <span>{contract.contractValue || contract.contract_value}</span>
                            </div>
                          )}
                        </div>

                        {contract.status && (
                          <div className="mt-3 pt-3 border-t border-slate-700/40 flex items-center justify-between">
                            <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-700/60 text-slate-300 font-medium">
                              {contract.status}
                            </span>
                            <span className="text-[10px] text-violet-400 font-semibold group-hover:underline flex items-center gap-1">
                              <Zap size={10} /> Analyze
                            </span>
                          </div>
                        )}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* PORTFOLIO HEATMAP TAB */}
      {activeTab === 'heatmap' && <PortfolioHeatmap token={token} />}
    </div>
  );
}
