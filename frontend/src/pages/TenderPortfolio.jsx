/**
 * Tender Portfolio Dashboard
 * Multi-tender $100M+ project portfolio intelligence
 * Route: /tenders/portfolio
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import tenderService from '../services/tenderService';

// ─── Helpers ───────────────────────────────────────────────────────────────
function generateActionItemsFromTender(tender) {
  const items = [];
  const categoryDeptMap = {
    CIVIL: 'Civil', MECHANICAL: 'Mechanical', ELECTRICAL: 'Electrical',
    MEP: 'MEP', PLUMBING: 'MEP', HVAC: 'Mechanical', OTHER: 'Civil',
  };
  (tender.work_items || []).forEach(wi => {
    const exp = parseFloat(wi.estimated_cost || wi.final_unit_cost || 0);
    const dept = categoryDeptMap[wi.category] || 'Civil';
    items.push({ department: dept, risk_score: Math.min(0.9, exp / 50000000), financial_exposure: exp, priority: exp > 5000000 ? 'High' : 'Medium' });
  });
  const riskDeptMap = { UNLIMITED_LIABILITY: 'Legal', HIGH_LD: 'Legal', TERMINATION: 'Legal', PAYMENT_TERMS: 'Finance', PRICE_ESCALATION: 'Finance', FORCE_MAJEURE: 'Legal', INDEMNITY: 'Legal', INSURANCE: 'HSE', SAFETY: 'HSE' };
  (tender.risks || []).forEach(r => {
    const dept = riskDeptMap[r.risk_type] || 'Legal';
    const rs = r.severity === 'CRITICAL' ? 0.9 : r.severity === 'HIGH' ? 0.7 : r.severity === 'MEDIUM' ? 0.4 : 0.2;
    items.push({ department: dept, risk_score: rs, financial_exposure: parseFloat(r.financial_exposure || 0), priority: r.severity });
  });
  items.push({ department: 'Planning', risk_score: 0.5, financial_exposure: 0, priority: 'High' });
  items.push({ department: 'Procurement', risk_score: 0.4, financial_exposure: 0, priority: 'Medium' });
  items.push({ department: 'HSE', risk_score: 0.3, financial_exposure: 0, priority: 'Medium' });
  return items;
}

function computeTenderStats(tender) {
  const items = generateActionItemsFromTender(tender);
  const totalExposure = items.reduce((s, a) => s + a.financial_exposure, 0);
  const avgRisk = items.length ? items.reduce((s, a) => s + a.risk_score, 0) / items.length : 0;
  const criticalCount = items.filter(a => a.priority === 'Critical' || a.priority === 'CRITICAL').length;
  const bestWinProb = tender.bid_scenarios?.length
    ? Math.max(...tender.bid_scenarios.map(s => parseFloat(s.win_probability || 0)))
    : 0;

  // Readiness 0-100
  const checks = [
    (tender.work_items?.length || 0) > 0,
    (tender.risks?.length || 0) > 0,
    (tender.bid_scenarios?.length || 0) > 0,
    !!tender.proposal,
    (tender.negotiations?.length || 0) > 0,
  ];
  const readiness = Math.round((checks.filter(Boolean).length / checks.length) * 100);

  return { totalExposure, avgRisk, criticalCount, bestWinProb, readiness, actionCount: items.length };
}

const STATUS_COLORS = {
  DRAFT: 'bg-slate-700/60 text-slate-300',
  ANALYZING: 'bg-yellow-900/50 text-yellow-300 border border-yellow-700/50',
  ANALYZED: 'bg-green-900/50 text-green-300 border border-green-700/50',
  BIDDING: 'bg-blue-900/50 text-blue-300 border border-blue-700/50',
  SUBMITTED: 'bg-purple-900/50 text-purple-300 border border-purple-700/50',
  WON: 'bg-emerald-900/50 text-emerald-300 border border-emerald-700/50',
  LOST: 'bg-red-900/50 text-red-300 border border-red-700/50',
};

// ─── Main Component ────────────────────────────────────────────────────────
const TenderPortfolio = () => {
  const navigate = useNavigate();
  const [tenders, setTenders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortBy, setSortBy] = useState('value');
  const [search, setSearch] = useState('');

  useEffect(() => { loadTenders(); }, []);

  const loadTenders = async () => {
    try {
      setLoading(true);
      const data = await tenderService.getAllTenders();
      const list = Array.isArray(data) ? data : (data.results || []);

      // Fetch details for each tender to get work_items, risks, etc.
      const detailed = await Promise.all(
        list.map(t => tenderService.getTenderDetails(t.id).catch(() => t))
      );
      setTenders(detailed);
    } catch (err) {
      setError('Failed to load portfolio');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
        <p className="text-slate-400">Loading Portfolio Intelligence...</p>
      </div>
    </div>
  );

  if (error) return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center">
      <div className="text-center">
        <p className="text-red-400 mb-4">{error}</p>
        <button onClick={loadTenders} className="px-4 py-2 bg-slate-700 text-white rounded-lg">Retry</button>
      </div>
    </div>
  );

  // Compute stats per tender
  const tenderStats = tenders.map(t => ({ tender: t, stats: computeTenderStats(t) }));

  // Portfolio aggregates
  const totalValue = tenders.reduce((s, t) => s + parseFloat(t.estimated_value || 0), 0);
  const totalExposure = tenderStats.reduce((s, ts) => s + ts.stats.totalExposure, 0);
  const avgRisk = tenderStats.length
    ? tenderStats.reduce((s, ts) => s + ts.stats.avgRisk, 0) / tenderStats.length
    : 0;
  const avgReadiness = tenderStats.length
    ? Math.round(tenderStats.reduce((s, ts) => s + ts.stats.readiness, 0) / tenderStats.length)
    : 0;
  const avgWinProb = tenderStats.length
    ? tenderStats.reduce((s, ts) => s + ts.stats.bestWinProb, 0) / tenderStats.length
    : 0;
  const totalActions = tenderStats.reduce((s, ts) => s + ts.stats.actionCount, 0);
  const totalCritical = tenderStats.reduce((s, ts) => s + ts.stats.criticalCount, 0);

  // Filter + sort
  const filtered = tenderStats
    .filter(ts => !search || ts.tender.title?.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => {
      if (sortBy === 'value') return parseFloat(b.tender.estimated_value || 0) - parseFloat(a.tender.estimated_value || 0);
      if (sortBy === 'risk') return b.stats.avgRisk - a.stats.avgRisk;
      if (sortBy === 'readiness') return b.stats.readiness - a.stats.readiness;
      if (sortBy === 'win') return b.stats.bestWinProb - a.stats.bestWinProb;
      return new Date(b.tender.created_at) - new Date(a.tender.created_at);
    });

  // Status distribution
  const statusDist = tenders.reduce((acc, t) => {
    acc[t.status] = (acc[t.status] || 0) + 1;
    return acc;
  }, {});

  // Top risk dept across portfolio
  const deptRiskMap = {};
  tenderStats.forEach(ts => {
    generateActionItemsFromTender(ts.tender).forEach(item => {
      if (!deptRiskMap[item.department]) deptRiskMap[item.department] = [];
      deptRiskMap[item.department].push(item.risk_score);
    });
  });
  const deptRiskSummary = Object.entries(deptRiskMap)
    .map(([dept, scores]) => ({ dept, avgRisk: scores.reduce((a, b) => a + b, 0) / scores.length, count: scores.length }))
    .sort((a, b) => b.avgRisk - a.avgRisk)
    .slice(0, 8);

  return (
    <div className="min-h-screen bg-slate-900 p-6">
      {/* Header */}
      <div className="mb-8">
        <button onClick={() => navigate('/tenders')}
          className="flex items-center text-slate-400 hover:text-white text-sm mb-4 transition-colors">
          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Tenders
        </button>

        <div className="bg-gradient-to-r from-indigo-900/40 via-purple-900/30 to-slate-800 border border-indigo-700/30 rounded-xl p-6">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <span className="text-2xl">🏛</span>
                <span className="text-indigo-300 text-sm font-semibold uppercase tracking-wider">Portfolio Intelligence</span>
                <span className="text-xs bg-indigo-900/60 border border-indigo-700/50 text-indigo-300 px-2 py-0.5 rounded-full">
                  {tenders.length} Tenders
                </span>
              </div>
              <h1 className="text-2xl font-bold text-white">$100M+ Multi-Project Portfolio</h1>
              <p className="text-slate-400 text-sm mt-1">Cross-tender risk, readiness, and win probability intelligence</p>
            </div>
            <button onClick={loadTenders}
              className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 hover:text-white rounded-lg text-sm transition-colors">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* ── Portfolio KPIs ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-7 gap-4 mb-8">
        <PortfolioKpi label="Total Tenders" value={tenders.length} color="text-white" />
        <PortfolioKpi label="Pipeline Value" value={`₹${(totalValue / 10000000).toFixed(1)} Cr`} color="text-emerald-400" />
        <PortfolioKpi label="Total Exposure" value={`₹${(totalExposure / 10000000).toFixed(1)} Cr`} color="text-yellow-400" />
        <PortfolioKpi label="Avg Risk" value={`${Math.round(avgRisk * 100)}%`} color={avgRisk > 0.6 ? 'text-red-400' : avgRisk > 0.4 ? 'text-orange-400' : 'text-green-400'} />
        <PortfolioKpi label="Avg Readiness" value={`${avgReadiness}%`} color="text-blue-400" />
        <PortfolioKpi label="Avg Win Prob" value={`${avgWinProb.toFixed(1)}%`} color="text-purple-400" />
        <PortfolioKpi label="Total Actions" value={totalActions} color="text-slate-300" />
      </div>

      {/* ── Two-column analytics ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Status distribution */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
          <h3 className="text-base font-semibold text-white mb-4">Portfolio Status Distribution</h3>
          <div className="space-y-3">
            {Object.entries(statusDist).map(([status, count]) => (
              <div key={status} className="flex items-center gap-3">
                <span className={`text-xs px-2 py-0.5 rounded-full w-24 text-center ${STATUS_COLORS[status] || STATUS_COLORS.DRAFT}`}>
                  {status}
                </span>
                <div className="flex-1 h-5 bg-slate-700 rounded overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-indigo-600 to-purple-500 rounded"
                    style={{ width: `${(count / tenders.length) * 100}%` }} />
                </div>
                <span className="text-xs text-slate-400 w-8 text-right">{count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Portfolio risk by department */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
          <h3 className="text-base font-semibold text-white mb-4">Portfolio Risk by Department</h3>
          <div className="space-y-2">
            {deptRiskSummary.map(d => (
              <div key={d.dept} className="flex items-center gap-3">
                <span className="text-xs text-slate-400 w-24 flex-shrink-0">{d.dept}</span>
                <div className="flex-1 h-5 bg-slate-700 rounded overflow-hidden">
                  <div className={`h-full rounded ${d.avgRisk > 0.7 ? 'bg-red-500' : d.avgRisk > 0.5 ? 'bg-orange-500' : d.avgRisk > 0.3 ? 'bg-yellow-500' : 'bg-green-500'}`}
                    style={{ width: `${Math.max(4, Math.round(d.avgRisk * 100))}%` }} />
                </div>
                <span className="text-xs text-slate-400 w-8 text-right">{Math.round(d.avgRisk * 100)}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* Value vs Readiness scatter */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
          <h3 className="text-base font-semibold text-white mb-4">Value vs. Bid Readiness</h3>
          <div className="relative h-48 bg-slate-900/60 rounded-lg border border-slate-700 p-3">
            {/* Axes labels */}
            <span className="absolute bottom-1 left-1/2 -translate-x-1/2 text-xs text-slate-500">Readiness →</span>
            <span className="absolute left-1 top-1/2 -translate-y-1/2 text-xs text-slate-500" style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg) translateY(50%)' }}>Value →</span>
            <svg width="100%" height="100%" className="overflow-visible">
              {tenderStats.map((ts, i) => {
                const xPct = ts.stats.readiness;
                const maxVal = Math.max(...tenderStats.map(t => parseFloat(t.tender.estimated_value || 0))) || 1;
                const yPct = 100 - ((parseFloat(ts.tender.estimated_value || 0) / maxVal) * 85);
                const risk = ts.stats.avgRisk;
                const color = risk > 0.6 ? '#ef4444' : risk > 0.4 ? '#f97316' : '#22c55e';
                return (
                  <g key={ts.tender.id}
                    onClick={() => navigate(`/tenders/${ts.tender.id}/bid-management`)}
                    style={{ cursor: 'pointer' }}>
                    <circle cx={`${xPct}%`} cy={`${yPct}%`} r="7" fill={color} fillOpacity="0.8"
                      stroke={color} strokeWidth="1.5" />
                    <title>{ts.tender.title} — Readiness {ts.stats.readiness}% — ₹{(parseFloat(ts.tender.estimated_value || 0) / 10000000).toFixed(1)} Cr</title>
                  </g>
                );
              })}
            </svg>
          </div>
          <div className="flex gap-4 mt-2 text-xs text-slate-500">
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500 inline-block"></span>High risk</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-orange-500 inline-block"></span>Med risk</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500 inline-block"></span>Low risk</span>
          </div>
        </div>

        {/* Critical actions summary */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
          <h3 className="text-base font-semibold text-white mb-4">Portfolio Risk Summary</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center p-3 bg-slate-700/40 rounded-lg">
              <span className="text-sm text-slate-300">Total Action Items</span>
              <span className="text-lg font-bold text-white">{totalActions}</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-red-900/20 border border-red-700/30 rounded-lg">
              <span className="text-sm text-red-300">Critical Risk Items</span>
              <span className="text-lg font-bold text-red-400">{totalCritical}</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-slate-700/40 rounded-lg">
              <span className="text-sm text-slate-300">Avg Win Probability</span>
              <span className="text-lg font-bold text-purple-400">{avgWinProb.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-slate-700/40 rounded-lg">
              <span className="text-sm text-slate-300">Avg Bid Readiness</span>
              <span className="text-lg font-bold text-blue-400">{avgReadiness}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Tender Table ── */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl">
        <div className="flex items-center justify-between p-5 border-b border-slate-700 flex-wrap gap-3">
          <h3 className="text-base font-semibold text-white">All Tenders — Portfolio View</h3>
          <div className="flex gap-3">
            <div className="relative">
              <svg className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search..."
                className="pl-8 pr-3 py-1.5 bg-slate-700 border border-slate-600 text-white text-sm rounded-lg focus:ring-1 focus:ring-purple-500 w-44" />
            </div>
            <select value={sortBy} onChange={e => setSortBy(e.target.value)}
              className="px-3 py-1.5 bg-slate-700 border border-slate-600 text-white text-sm rounded-lg focus:ring-1 focus:ring-purple-500">
              <option value="value">Sort: Value</option>
              <option value="risk">Sort: Risk</option>
              <option value="readiness">Sort: Readiness</option>
              <option value="win">Sort: Win Prob</option>
              <option value="date">Sort: Newest</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-slate-400 border-b border-slate-700 uppercase tracking-wider">
                <th className="text-left px-5 py-3">Tender</th>
                <th className="text-left px-4 py-3">Status</th>
                <th className="text-right px-4 py-3">Value</th>
                <th className="text-right px-4 py-3">Exposure</th>
                <th className="text-right px-4 py-3">Avg Risk</th>
                <th className="text-right px-4 py-3">Win Prob</th>
                <th className="text-center px-4 py-3">Readiness</th>
                <th className="text-right px-4 py-3">Actions</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr><td colSpan={9} className="text-center py-12 text-slate-500">No tenders found</td></tr>
              ) : filtered.map(({ tender, stats }) => (
                <tr key={tender.id} className="border-b border-slate-700/50 hover:bg-slate-700/20 transition-colors">
                  <td className="px-5 py-4">
                    <div className="font-medium text-white max-w-xs truncate">{tender.title}</div>
                    {tender.reference_number && (
                      <div className="text-xs text-slate-500 font-mono mt-0.5">{tender.reference_number}</div>
                    )}
                  </td>
                  <td className="px-4 py-4">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[tender.status] || STATUS_COLORS.DRAFT}`}>
                      {tender.status}
                    </span>
                  </td>
                  <td className="px-4 py-4 text-right text-emerald-400 font-medium">
                    {tender.estimated_value ? `₹${(parseFloat(tender.estimated_value) / 10000000).toFixed(2)} Cr` : '—'}
                  </td>
                  <td className="px-4 py-4 text-right text-yellow-400">
                    {stats.totalExposure > 0 ? `₹${(stats.totalExposure / 10000000).toFixed(2)} Cr` : '—'}
                  </td>
                  <td className="px-4 py-4 text-right">
                    <span className={`font-semibold ${stats.avgRisk > 0.7 ? 'text-red-400' : stats.avgRisk > 0.4 ? 'text-orange-400' : 'text-green-400'}`}>
                      {Math.round(stats.avgRisk * 100)}%
                    </span>
                  </td>
                  <td className="px-4 py-4 text-right text-purple-400 font-medium">
                    {stats.bestWinProb > 0 ? `${stats.bestWinProb.toFixed(1)}%` : '—'}
                  </td>
                  <td className="px-4 py-4">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden min-w-[60px]">
                        <div className={`h-full rounded-full ${stats.readiness >= 80 ? 'bg-green-500' : stats.readiness >= 50 ? 'bg-blue-500' : 'bg-yellow-500'}`}
                          style={{ width: `${stats.readiness}%` }} />
                      </div>
                      <span className="text-xs text-slate-400">{stats.readiness}%</span>
                    </div>
                  </td>
                  <td className="px-4 py-4 text-right text-slate-400 text-xs">{stats.actionCount}</td>
                  <td className="px-4 py-4">
                    <button onClick={() => navigate(`/tenders/${tender.id}/bid-management`)}
                      className="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white text-xs rounded-lg transition-colors whitespace-nowrap">
                      Bid Mgmt →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-slate-700 flex items-center justify-between text-xs text-slate-400">
          <span>{filtered.length} of {tenders.length} tenders</span>
          <span>Portfolio Value: ₹{(totalValue / 10000000).toFixed(1)} Cr</span>
        </div>
      </div>
    </div>
  );
};

const PortfolioKpi = ({ label, value, color }) => (
  <div className="bg-slate-800 border border-slate-700 rounded-xl p-4">
    <div className="text-xs text-slate-400 mb-1">{label}</div>
    <div className={`text-xl font-bold ${color}`}>{value}</div>
  </div>
);

export default TenderPortfolio;
