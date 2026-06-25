/**
 * Tender Intelligence — List Page (Premium Redesign)
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import tenderService from '../services/tenderService';

const STATUS_META = {
  DRAFT:     { color: 'bg-slate-700/60 text-slate-300 border-slate-600',     dot: 'bg-slate-400',    label: 'Draft' },
  ANALYZING: { color: 'bg-amber-900/40 text-amber-300 border-amber-700/50',  dot: 'bg-amber-400 animate-pulse', label: 'Analyzing' },
  ANALYZED:  { color: 'bg-emerald-900/40 text-emerald-300 border-emerald-700/50', dot: 'bg-emerald-400', label: 'Analyzed' },
  BIDDING:   { color: 'bg-blue-900/40 text-blue-300 border-blue-700/50',     dot: 'bg-blue-400',     label: 'Bidding' },
  SUBMITTED: { color: 'bg-purple-900/40 text-purple-300 border-purple-700/50', dot: 'bg-purple-400', label: 'Submitted' },
  WON:       { color: 'bg-green-900/40 text-green-300 border-green-700/50',  dot: 'bg-green-400',    label: 'Won' },
  LOST:      { color: 'bg-red-900/40 text-red-300 border-red-700/50',        dot: 'bg-red-400',      label: 'Lost' },
};

const BID_MGMT_ENABLED = ['ANALYZED', 'BIDDING', 'SUBMITTED', 'WON', 'LOST'];

const fmtCr = (val) => {
  const n = parseFloat(val || 0);
  if (n >= 10000000) return `₹${(n / 10000000).toFixed(2)} Cr`;
  if (n >= 100000)   return `₹${(n / 100000).toFixed(1)} L`;
  return `₹${n.toLocaleString('en-IN')}`;
};

/* ─── Stat Card ─────────────────────────────────────────────────── */
const StatCard = ({ label, value, sub, gradient, icon }) => (
  <div className={`relative overflow-hidden rounded-2xl p-5 border border-white/5 ${gradient}`}>
    <div className="absolute inset-0 opacity-10 bg-[radial-gradient(ellipse_at_top_right,_white_0%,_transparent_70%)]" />
    <div className="flex items-start justify-between">
      <div>
        <p className="text-xs font-medium text-white/60 uppercase tracking-widest mb-1">{label}</p>
        <p className="text-3xl font-bold text-white leading-none">{value}</p>
        {sub && <p className="text-xs text-white/50 mt-1.5">{sub}</p>}
      </div>
      <div className="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center text-lg">{icon}</div>
    </div>
  </div>
);

/* ─── Tender Card ────────────────────────────────────────────────── */
const TenderCard = ({ tender, onClick, onDelete, onBidManagement, onBuyerEval }) => {
  const meta = STATUS_META[tender.status] || STATUS_META.DRAFT;
  const daysLeft = tender.submission_deadline
    ? Math.ceil((new Date(tender.submission_deadline) - new Date()) / 86400000)
    : null;

  const deadlineColor =
    daysLeft === null      ? 'text-slate-500' :
    daysLeft < 0           ? 'text-red-400'   :
    daysLeft <= 7          ? 'text-orange-400' :
    daysLeft <= 30         ? 'text-yellow-400' :
                             'text-emerald-400';

  const deadlineLabel =
    daysLeft === null ? 'No deadline' :
    daysLeft < 0      ? `${Math.abs(daysLeft)}d overdue` :
    daysLeft === 0    ? 'Due today' :
                        `${daysLeft}d left`;

  const bidEnabled = BID_MGMT_ENABLED.includes(tender.status);

  return (
    <div
      onClick={onClick}
      className="group relative bg-slate-800/60 backdrop-blur-sm border border-slate-700/60 rounded-2xl p-5 cursor-pointer
                 hover:border-blue-500/40 hover:shadow-2xl hover:shadow-blue-950/50 transition-all duration-300 flex flex-col"
    >
      {/* Hover glow */}
      <div className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300
                      bg-[radial-gradient(ellipse_at_top_left,_rgba(59,130,246,0.06)_0%,_transparent_60%)] pointer-events-none" />

      {/* Top row */}
      <div className="flex items-center justify-between mb-3">
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${meta.color}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${meta.dot}`} />
          {meta.label}
        </span>
        {tender.reference_number && (
          <span className="text-[11px] text-slate-500 font-mono bg-slate-900/60 border border-slate-700/40 px-2 py-0.5 rounded-md">
            {tender.reference_number}
          </span>
        )}
      </div>

      {/* Title */}
      <h3 className="text-[15px] font-semibold text-white group-hover:text-blue-300 transition-colors line-clamp-2 mb-4 flex-1 leading-snug">
        {tender.title}
      </h3>

      {/* Value + Deadline row */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-1.5">
          <div className="w-6 h-6 rounded-lg bg-emerald-900/50 flex items-center justify-center">
            <svg className="w-3.5 h-3.5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <span className="text-sm font-bold text-emerald-400">
            {tender.estimated_value ? fmtCr(tender.estimated_value) : '—'}
          </span>
        </div>

        <div className={`flex items-center gap-1 text-xs font-medium ${deadlineColor}`}>
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          {deadlineLabel}
        </div>
      </div>

      {/* Uploaded date */}
      <p className="text-[11px] text-slate-600 mb-4">
        Uploaded {new Date(tender.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
      </p>

      {/* Divider */}
      <div className="border-t border-slate-700/50 pt-3 flex items-center gap-2">
        <button
          onClick={e => { e.stopPropagation(); onBidManagement(); }}
          disabled={!bidEnabled}
          className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl text-xs font-semibold transition-all ${
            bidEnabled
              ? 'bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 text-white shadow-md shadow-purple-900/40'
              : 'bg-slate-700/40 text-slate-600 cursor-not-allowed border border-slate-700/30'
          }`}
          title={bidEnabled ? 'Open Bid Management' : 'Analyse tender first'}
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          Bid Management
        </button>
        <button
          onClick={e => { e.stopPropagation(); onBuyerEval(); }}
          disabled={!bidEnabled}
          className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl text-xs font-semibold transition-all ${
            bidEnabled
              ? 'bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white shadow-md shadow-indigo-900/40'
              : 'bg-slate-700/40 text-slate-600 cursor-not-allowed border border-slate-700/30'
          }`}
          title={bidEnabled ? 'Open Buyer Evaluation' : 'Analyse tender first'}
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          Buyer Eval
        </button>

        <button
          onClick={e => { e.stopPropagation(); onClick(); }}
          className="flex items-center gap-1 px-3 py-2 bg-slate-700/50 hover:bg-slate-600/60 text-slate-300 hover:text-white border border-slate-700/40 rounded-xl text-xs font-medium transition-all"
        >
          Open
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>

        <button
          onClick={e => { e.stopPropagation(); onDelete(); }}
          className="p-2 text-slate-600 hover:text-red-400 hover:bg-red-900/20 rounded-xl border border-transparent hover:border-red-900/30 transition-all"
          title="Delete"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
    </div>
  );
};

/* ─── Main Page ──────────────────────────────────────────────────── */
const TenderList = () => {
  const navigate = useNavigate();
  const [tenders, setTenders]         = useState([]);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState(null);
  const [search, setSearch]           = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [sortBy, setSortBy]           = useState('created_at');

  useEffect(() => { loadTenders(); }, []);

  const loadTenders = async () => {
    try {
      setLoading(true);
      const data = await tenderService.getAllTenders();
      setTenders(Array.isArray(data) ? data : (data.results || []));
      setError(null);
    } catch (err) {
      setError('Failed to load tenders');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id, title) => {
    if (!window.confirm(`Delete "${title}"? This cannot be undone.`)) return;
    try {
      await tenderService.deleteTender(id);
      loadTenders();
    } catch {
      alert('Failed to delete tender.');
    }
  };

  const filtered = tenders
    .filter(t => {
      const q = search.toLowerCase();
      return (!q || t.title?.toLowerCase().includes(q) || t.reference_number?.toLowerCase().includes(q))
          && (statusFilter === 'ALL' || t.status === statusFilter);
    })
    .sort((a, b) => {
      if (sortBy === 'estimated_value') return (parseFloat(b.estimated_value) || 0) - (parseFloat(a.estimated_value) || 0);
      if (sortBy === 'submission_deadline') return new Date(a.submission_deadline || 0) - new Date(b.submission_deadline || 0);
      return new Date(b.created_at) - new Date(a.created_at);
    });

  const counts = tenders.reduce((a, t) => ({ ...a, [t.status]: (a[t.status] || 0) + 1 }), {});
  const totalValue = tenders.reduce((s, t) => s + parseFloat(t.estimated_value || 0), 0);

  return (
    <div className="min-h-screen bg-slate-950 p-6">

      {/* ── Page Header ── */}
      <div className="mb-8">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-900/40">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white tracking-tight">Tender Intelligence</h1>
                <p className="text-slate-500 text-sm">Manage, analyse and bid on government tenders</p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/tenders/company-profile')}
              className="flex items-center gap-2 px-4 py-2.5 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700/50 text-slate-300 hover:text-white rounded-xl text-sm font-medium transition-all"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
              Company Profile
            </button>
            <button
              onClick={() => navigate('/tenders/upload')}
              className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500
                         text-white rounded-xl text-sm font-semibold transition-all shadow-lg shadow-blue-900/40"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Upload Tender
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <StatCard label="Total Tenders"  value={tenders.length}                    icon="📋" gradient="bg-gradient-to-br from-slate-800 to-slate-900"         sub={`${counts.ANALYZING || 0} analysing now`} />
          <StatCard label="Pipeline Value" value={fmtCr(totalValue)}                 icon="💰" gradient="bg-gradient-to-br from-emerald-900/80 to-slate-900"    sub="Estimated contract value" />
          <StatCard label="Analysed"       value={counts.ANALYZED || 0}              icon="✅" gradient="bg-gradient-to-br from-green-900/60 to-slate-900"      sub="Ready for bidding" />
          <StatCard label="In Bidding"     value={(counts.BIDDING || 0) + (counts.SUBMITTED || 0)} icon="🎯" gradient="bg-gradient-to-br from-blue-900/60 to-slate-900" sub={`${counts.WON || 0} won · ${counts.LOST || 0} lost`} />
        </div>
      </div>

      {/* ── Filters ── */}
      <div className="flex flex-col md:flex-row gap-3 mb-6">
        <div className="relative flex-1">
          <svg className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            placeholder="Search by title or reference number…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-slate-800/70 border border-slate-700/50 text-white placeholder-slate-500
                       rounded-xl focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 text-sm transition-all"
          />
        </div>
        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          className="px-4 py-2.5 bg-slate-800/70 border border-slate-700/50 text-white rounded-xl focus:ring-2 focus:ring-blue-500/50 text-sm"
        >
          <option value="ALL">All Statuses</option>
          {Object.keys(STATUS_META).map(s => (
            <option key={s} value={s}>{STATUS_META[s].label}</option>
          ))}
        </select>
        <select
          value={sortBy}
          onChange={e => setSortBy(e.target.value)}
          className="px-4 py-2.5 bg-slate-800/70 border border-slate-700/50 text-white rounded-xl focus:ring-2 focus:ring-blue-500/50 text-sm"
        >
          <option value="created_at">Newest First</option>
          <option value="estimated_value">Highest Value</option>
          <option value="submission_deadline">Deadline Soonest</option>
        </select>
      </div>

      {/* Result count */}
      {!loading && !error && (
        <p className="text-xs text-slate-600 mb-4">
          Showing <span className="text-slate-400 font-semibold">{filtered.length}</span> of {tenders.length} tenders
        </p>
      )}

      {/* ── Content ── */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-32 gap-4">
          <div className="relative w-16 h-16">
            <div className="absolute inset-0 rounded-full border-2 border-blue-500/20" />
            <div className="absolute inset-0 rounded-full border-t-2 border-blue-500 animate-spin" />
          </div>
          <p className="text-slate-500 text-sm">Loading tenders…</p>
        </div>
      ) : error ? (
        <div className="bg-red-900/20 border border-red-700/30 rounded-2xl p-8 text-center">
          <p className="text-red-400 mb-4">{error}</p>
          <button onClick={loadTenders} className="px-5 py-2 bg-red-600 hover:bg-red-700 text-white rounded-xl text-sm font-medium">
            Retry
          </button>
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-32 text-center">
          <div className="w-20 h-20 rounded-2xl bg-slate-800/60 border border-slate-700/40 flex items-center justify-center text-4xl mb-5">
            📋
          </div>
          <h3 className="text-lg font-semibold text-white mb-2">
            {tenders.length === 0 ? 'No tenders yet' : 'No matching tenders'}
          </h3>
          <p className="text-slate-500 text-sm mb-6 max-w-xs">
            {tenders.length === 0 ? 'Upload your first tender PDF to get started with AI analysis' : 'Try adjusting your search or filters'}
          </p>
          {tenders.length === 0 && (
            <button
              onClick={() => navigate('/tenders/upload')}
              className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl font-medium text-sm
                         shadow-lg shadow-blue-900/30 hover:from-blue-500 hover:to-indigo-500 transition-all"
            >
              Upload First Tender
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map(t => (
            <TenderCard
              key={t.id}
              tender={t}
              onClick={() => navigate(`/tenders/${t.id}`)}
              onDelete={() => handleDelete(t.id, t.title)}
              onBidManagement={() => navigate(`/tenders/${t.id}/bid-management`)}
              onBuyerEval={() => navigate(`/tenders/${t.id}/buyer`)}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default TenderList;
