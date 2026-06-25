/**
 * Tender Overview — Premium Redesign
 */
import React, { useState, useEffect } from 'react';
import tenderService from '../../services/tenderService';

const fmtCurrency = (val) => {
  if (!val) return 'N/A';
  const n = parseFloat(val);
  if (n >= 10000000) return `₹${(n / 10000000).toFixed(2)} Cr`;
  if (n >= 100000)   return `₹${(n / 100000).toFixed(2)} L`;
  return `₹${n.toLocaleString('en-IN')}`;
};

const fmtDateSafe = (d, referenceDate) => {
  if (!d) return '—';
  // If this date is identical to the reference date, the parser couldn't extract it separately
  if (referenceDate && d !== referenceDate) {
    const a = new Date(d).getTime();
    const b = new Date(referenceDate).getTime();
    if (a === b) return '—';
  }
  return new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' });
};

const fmtDate = (d) => {
  if (!d) return 'N/A';
  return new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' });
};

/* ─── Glowing metric card ──────────────────────────────────────── */
const MetricCard = ({ label, value, sub, icon, accent }) => {
  const accents = {
    blue:    { ring: 'ring-blue-500/20',    bg: 'bg-blue-500/10',    text: 'text-blue-400',    icon: 'bg-blue-500/20' },
    emerald: { ring: 'ring-emerald-500/20', bg: 'bg-emerald-500/10', text: 'text-emerald-400', icon: 'bg-emerald-500/20' },
    purple:  { ring: 'ring-purple-500/20',  bg: 'bg-purple-500/10',  text: 'text-purple-400',  icon: 'bg-purple-500/20' },
    amber:   { ring: 'ring-amber-500/20',   bg: 'bg-amber-500/10',   text: 'text-amber-400',   icon: 'bg-amber-500/20' },
    cyan:    { ring: 'ring-cyan-500/20',    bg: 'bg-cyan-500/10',    text: 'text-cyan-400',    icon: 'bg-cyan-500/20' },
    rose:    { ring: 'ring-rose-500/20',    bg: 'bg-rose-500/10',    text: 'text-rose-400',    icon: 'bg-rose-500/20' },
  };
  const a = accents[accent] || accents.blue;

  return (
    <div className={`relative rounded-2xl bg-slate-800/50 border border-slate-700/50 ring-1 ${a.ring} p-5 overflow-hidden`}>
      <div className={`absolute inset-0 ${a.bg} opacity-30`} />
      <div className="relative flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <p className="text-xs text-slate-500 uppercase tracking-widest font-medium mb-2">{label}</p>
          <p className={`text-xl font-bold ${a.text} leading-none break-words`}>{value}</p>
          {sub && <p className="text-xs text-slate-600 mt-1.5">{sub}</p>}
        </div>
        <div className={`w-9 h-9 rounded-xl ${a.icon} flex items-center justify-center shrink-0`}>
          {icon}
        </div>
      </div>
    </div>
  );
};

/* ─── Info row ─────────────────────────────────────────────────── */
const InfoRow = ({ label, value }) => (
  <div className="flex flex-col gap-0.5">
    <span className="text-xs text-slate-500 uppercase tracking-wider font-medium">{label}</span>
    <span className="text-sm text-slate-200 font-medium">{value || 'N/A'}</span>
  </div>
);

/* ─── Timeline item ────────────────────────────────────────────── */
const TimelineItem = ({ label, date, isPast, isActive, icon }) => {
  const notFound = date === '—';
  return (
    <div className="flex items-start gap-3">
      <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 text-base transition-all ${
        notFound ? 'bg-slate-800/30 opacity-40' :
        isActive ? 'bg-blue-500/20 ring-1 ring-blue-500/40' :
        isPast   ? 'bg-slate-700/40' :
                   'bg-slate-800/60'
      }`}>
        {icon}
      </div>
      <div>
        <p className="text-xs text-slate-500 font-medium">{label}</p>
        {notFound ? (
          <p className="text-xs text-slate-600 italic">Not found in PDF</p>
        ) : (
          <p className={`text-sm font-semibold ${isActive ? 'text-blue-300' : isPast ? 'text-slate-500 line-through decoration-slate-600' : 'text-slate-200'}`}>
            {date}
          </p>
        )}
      </div>
    </div>
  );
};

/* ─── Win probability ring ─────────────────────────────────────── */
const WinRing = ({ prob, loading }) => {
  const r = 28, circ = 2 * Math.PI * r;
  const filled = loading || prob === null ? 0 : (prob / 100) * circ;
  const color = prob >= 70 ? '#10b981' : prob >= 50 ? '#f59e0b' : prob >= 30 ? '#f97316' : '#ef4444';

  return (
    <div className="flex items-center gap-4">
      <div className="relative w-20 h-20">
        <svg className="w-20 h-20 -rotate-90" viewBox="0 0 72 72">
          <circle cx="36" cy="36" r={r} fill="none" stroke="#1e293b" strokeWidth="6" />
          {!loading && prob !== null && (
            <circle cx="36" cy="36" r={r} fill="none" stroke={color} strokeWidth="6"
              strokeDasharray={circ} strokeDashoffset={circ - filled}
              strokeLinecap="round" style={{ transition: 'stroke-dashoffset 1s ease' }} />
          )}
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          {loading ? (
            <div className="w-5 h-5 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
          ) : prob !== null ? (
            <span className="text-base font-bold" style={{ color }}>{prob.toFixed(0)}%</span>
          ) : (
            <span className="text-slate-600 text-xs">N/A</span>
          )}
        </div>
      </div>
      <div>
        <p className="text-sm font-semibold text-white">Win Probability</p>
        <p className="text-xs text-slate-500 mt-0.5">
          {loading ? 'Calculating…' :
           prob === null ? 'Not available' :
           prob >= 70 ? 'Strong position' :
           prob >= 50 ? 'Competitive' :
           prob >= 30 ? 'Challenging' :
           'Low chance'}
        </p>
      </div>
    </div>
  );
};

/* ─── Main component ───────────────────────────────────────────── */
const TenderOverview = ({ tender }) => {
  const [winProb, setWinProb]       = useState(null);
  const [loadingWin, setLoadingWin] = useState(false);

  useEffect(() => {
    setWinProb(null);
    setLoadingWin(true);
    tenderService.simulateWinProbability(tender.id)
      .then(r => setWinProb(r.win_probability))
      .catch(() => {})
      .finally(() => setLoadingWin(false));
  }, [tender.id]);

  const now = new Date();
  const deadlinePast = tender.submission_deadline && new Date(tender.submission_deadline) < now;

  return (
    <div className="space-y-6">

      {/* ── Row 1: Six metric cards ── */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <MetricCard
          label="Contract Value"
          value={fmtCurrency(tender.estimated_value)}
          icon={<svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
          accent="emerald"
        />
        <MetricCard
          label="EMD / Bid Security"
          value={fmtCurrency(tender.bid_security || tender.emd_amount)}
          icon={<svg className="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>}
          accent="blue"
        />
        <MetricCard
          label="Completion"
          value={tender.completion_period_days ? `${tender.completion_period_days}d` : 'N/A'}
          sub={tender.completion_period_days ? `≈ ${Math.round(tender.completion_period_days / 30)} months` : null}
          icon={<svg className="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
          accent="purple"
        />
        <MetricCard
          label="BOQ Items"
          value={tender.work_items?.length || 0}
          sub="Work packages"
          icon={<svg className="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" /></svg>}
          accent="cyan"
        />
        <MetricCard
          label="Risks Found"
          value={tender.risks?.length || 0}
          sub={`${tender.risks?.filter(r => r.severity === 'HIGH' || r.severity === 'CRITICAL').length || 0} critical`}
          icon={<svg className="w-4 h-4 text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>}
          accent="rose"
        />
        <MetricCard
          label="Pre-Bid Q&A"
          value={tender.prebid_questions?.length || 0}
          sub="Questions tracked"
          icon={<svg className="w-4 h-4 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
          accent="amber"
        />
      </div>

      {/* ── Row 2: Info + Timeline + Win Prob ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* Basic Info */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-7 h-7 rounded-lg bg-blue-500/15 flex items-center justify-center">
              <svg className="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-sm font-semibold text-white">Basic Information</h3>
          </div>
          <div className="space-y-3 divide-y divide-slate-700/30">
            <InfoRow label="Reference" value={tender.reference_number} />
            <div className="pt-3"><InfoRow label="Organisation" value={tender.organization} /></div>
            <div className="pt-3">
              <span className="text-xs text-slate-500 uppercase tracking-wider font-medium">Scope of Work</span>
              <p className="text-sm text-slate-300 mt-1 leading-relaxed line-clamp-4">
                {tender.scope_of_work || 'N/A'}
              </p>
            </div>
          </div>
        </div>

        {/* Timeline */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-7 h-7 rounded-lg bg-emerald-500/15 flex items-center justify-center">
              <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <h3 className="text-sm font-semibold text-white">Key Dates</h3>
          </div>
          <div className="space-y-4">
            <TimelineItem
              label="Submission Deadline"
              date={fmtDate(tender.submission_deadline)}
              isPast={deadlinePast}
              isActive={!deadlinePast && tender.submission_deadline}
              icon="📅"
            />
            <TimelineItem
              label="Technical Opening"
              date={(() => {
                if (!tender.technical_opening_date) return '—';
                // If identical to submission deadline, parser couldn't find it separately
                if (tender.submission_deadline &&
                    new Date(tender.technical_opening_date).getTime() === new Date(tender.submission_deadline).getTime())
                  return '—';
                return fmtDate(tender.technical_opening_date);
              })()}
              isPast={tender.technical_opening_date &&
                      new Date(tender.technical_opening_date).getTime() !== new Date(tender.submission_deadline).getTime() &&
                      new Date(tender.technical_opening_date) < now}
              icon="📂"
            />
            <TimelineItem
              label="Financial Opening"
              date={(() => {
                if (!tender.financial_opening_date) return '—';
                if (tender.submission_deadline &&
                    new Date(tender.financial_opening_date).getTime() === new Date(tender.submission_deadline).getTime())
                  return '—';
                return fmtDate(tender.financial_opening_date);
              })()}
              isPast={tender.financial_opening_date &&
                      new Date(tender.financial_opening_date).getTime() !== new Date(tender.submission_deadline).getTime() &&
                      new Date(tender.financial_opening_date) < now}
              icon="💵"
            />
          </div>
        </div>

        {/* Win Probability + quick stats */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5 flex flex-col gap-5">
          <WinRing prob={winProb} loading={loadingWin} />

          <div className="border-t border-slate-700/40 pt-4 grid grid-cols-2 gap-3">
            {[
              { label: 'Conflicts', value: tender.conflicts?.length || 0, color: 'text-orange-400' },
              { label: 'Amendments', value: tender.amendments?.length || 0, color: 'text-sky-400' },
              { label: 'Negotiations', value: tender.negotiations?.length || 0, color: 'text-violet-400' },
              { label: 'Status', value: tender.status, color: 'text-slate-300' },
            ].map(item => (
              <div key={item.label} className="bg-slate-900/40 rounded-xl p-3">
                <p className="text-[10px] text-slate-600 uppercase tracking-wider mb-1">{item.label}</p>
                <p className={`text-lg font-bold ${item.color}`}>{item.value}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Row 3: Summary ── */}
      {tender.summary && (
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-7 h-7 rounded-lg bg-purple-500/15 flex items-center justify-center">
              <svg className="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-sm font-semibold text-white">AI-Extracted Summary</h3>
            <span className="text-[10px] bg-purple-900/40 text-purple-400 border border-purple-700/30 px-2 py-0.5 rounded-full font-medium">AI</span>
          </div>
          <p className="text-slate-300 text-sm leading-relaxed">{tender.summary}</p>
        </div>
      )}

      {/* ── Row 4: BOQ category breakdown ── */}
      {tender.work_items?.length > 0 && (() => {
        const cats = tender.work_items.reduce((acc, wi) => {
          const c = wi.category || 'OTHER';
          acc[c] = (acc[c] || 0) + parseFloat(wi.estimated_cost || 0);
          return acc;
        }, {});
        const total = Object.values(cats).reduce((s, v) => s + v, 0);
        const sorted = Object.entries(cats).sort((a, b) => b[1] - a[1]);
        const BAR_COLORS = ['bg-blue-500', 'bg-emerald-500', 'bg-purple-500', 'bg-amber-500', 'bg-cyan-500', 'bg-rose-500'];

        return (
          <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-7 h-7 rounded-lg bg-cyan-500/15 flex items-center justify-center">
                <svg className="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-sm font-semibold text-white">BOQ Category Breakdown</h3>
              <span className="text-[11px] text-slate-500 ml-auto">{tender.work_items.length} items · {fmtCurrency(total)}</span>
            </div>
            <div className="space-y-3">
              {sorted.map(([cat, val], i) => {
                const pct = total > 0 ? (val / total) * 100 : 0;
                return (
                  <div key={cat}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-slate-300 font-medium capitalize">{cat.toLowerCase().replace(/_/g, ' ')}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-slate-500">{fmtCurrency(val)}</span>
                        <span className="text-xs font-semibold text-slate-400 w-10 text-right">{pct.toFixed(1)}%</span>
                      </div>
                    </div>
                    <div className="h-1.5 bg-slate-700/60 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${BAR_COLORS[i % BAR_COLORS.length]}`}
                        style={{ width: `${pct}%`, transition: 'width 0.8s ease' }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })()}
    </div>
  );
};

export default TenderOverview;
