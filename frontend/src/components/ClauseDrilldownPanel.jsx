/**
 * ClauseDrilldownPanel  –  v2
 * Slide-over panel triggered when a user clicks a contract dot on a quadrant map.
 *
 * Three tabs:
 *   CLAUSES      – full clause list sorted by risk (original behaviour, enhanced)
 *   RISK TREND   – time-series chart from ContractRiskHistory (new)
 *   AUTO-REDLINE – one-click batch redline of every high-risk clause (new)
 */
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { X, AlertCircle, TrendingDown, Zap, BarChart2 } from 'lucide-react';
import RiskTrendChart from './RiskTrendChart';

const API = import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));
const headers = () => ({ Authorization: `Bearer ${localStorage.getItem('token')}` });

/* ─── helpers ─── */
const getRiskColor = (score) => {
  if (score >= 0.7) return { bg: 'rgba(127,29,29,0.35)',  text: '#fca5a5', border: 'rgba(239,68,68,0.35)'  };
  if (score >= 0.4) return { bg: 'rgba(133,100,30,0.35)', text: '#fde047', border: 'rgba(234,179,8,0.35)'  };
  return               { bg: 'rgba(14,76,48,0.35)',   text: '#86efac', border: 'rgba(34,197,94,0.35)'  };
};

const getRiskLabel = (score) => score >= 0.7 ? 'HIGH' : score >= 0.4 ? 'MED' : 'LOW';

/* ─── sub-components ─── */

/** Inline badge used in the stats bar */
const StatBadge = ({ count, label, color }) => (
  <div className="flex flex-col items-center">
    <span className="text-lg font-black" style={{ color }}>{count}</span>
    <span className="text-[9px] text-slate-500 uppercase tracking-widest">{label}</span>
  </div>
);

/** Single clause card – used on the CLAUSES tab */
const ClauseCard = ({ clause, index }) => {
  const { bg, text, border } = getRiskColor(clause.risk_score);
  return (
    <div className="rounded-lg p-4" style={{ background: 'rgba(15,23,42,0.7)', border: `1px solid ${border}` }}>
      {/* header row */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-black text-slate-500">#{index + 1}</span>
          <span className="text-[12px] font-semibold text-slate-300">{clause.clause_type}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-2 py-0.5 rounded-full text-[10px] font-black tracking-wide"
            style={{ background: bg, color: text, border: `1px solid ${border}` }}>
            {getRiskLabel(clause.risk_score)}
          </span>
          <span className="text-[12px] font-black text-white">{(clause.risk_score * 100).toFixed(0)}%</span>
        </div>
      </div>

      {/* text */}
      <p className="text-[12px] text-slate-300 leading-relaxed">{clause.extracted_text}</p>

      {/* risk reason */}
      {clause.risk_reason && clause.risk_reason !== 'No risk patterns detected' && (
        <div className="mt-2 rounded px-3 py-1.5" style={{ background: 'rgba(127,29,29,0.25)', border: '1px solid rgba(239,68,68,0.25)' }}>
          <p className="text-[10px] text-red-300">
            <strong>Risk factors:</strong> {clause.risk_reason}
          </p>
        </div>
      )}
    </div>
  );
};

/** Single redline diff card – used on the AUTO-REDLINE tab */
const RedlineCard = ({ item, index }) => {
  const [expanded, setExpanded] = useState(false);
  const scoreNorm = item.risk_score / 100;                 // back to 0-1 for colour helper
  const { border } = getRiskColor(scoreNorm);

  return (
    <div className="rounded-lg overflow-hidden" style={{ border: `1px solid ${border}`, background: 'rgba(15,23,42,0.7)' }}>
      {/* clickable header */}
      <button onClick={() => setExpanded(!expanded)}
        className="w-full text-left p-3 flex items-center justify-between"
        style={{ background: expanded ? 'rgba(15,23,42,0.95)' : 'rgba(15,23,42,0.5)' }}>
        <div className="flex items-center gap-2.5">
          <span className="text-[10px] font-black text-slate-500">#{index + 1}</span>
          <span className="text-[11px] font-bold text-slate-300 truncate max-w-[180px]">{item.clause_type}</span>
          <span className="px-1.5 py-0.5 rounded text-[9px] font-black text-slate-400"
            style={{ background: 'rgba(51,65,85,0.5)' }}>{item.risk_type}</span>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <span className="text-[11px] font-black text-red-300">{item.risk_score}</span>
          {item.changed && <span className="text-[9px] font-black px-1.5 py-0.5 rounded" style={{ background: 'rgba(34,197,94,0.2)', color: '#86efac', border: '1px solid rgba(34,197,94,0.3)' }}>FIXED</span>}
          <span className="text-slate-500 text-xs">{expanded ? '▲' : '▼'}</span>
        </div>
      </button>

      {/* expandable body */}
      {expanded && (
        <div className="p-3 border-t" style={{ borderColor: 'rgba(51,65,85,0.35)' }}>
          {/* explanation */}
          <p className="text-[10px] text-slate-400 mb-3 italic">{item.risk_explanation}</p>

          {/* original */}
          <div className="mb-2">
            <p className="text-[9px] font-black text-red-400 uppercase tracking-widest mb-1">Original</p>
            <p className="text-[11px] text-slate-300 leading-relaxed rounded px-2 py-1.5"
              style={{ background: 'rgba(127,29,29,0.15)', border: '1px solid rgba(239,68,68,0.15)' }}>
              {item.original_text}
            </p>
          </div>

          {/* suggested */}
          <div>
            <p className="text-[9px] font-black text-green-400 uppercase tracking-widest mb-1">Suggested</p>
            <p className="text-[11px] text-slate-200 leading-relaxed rounded px-2 py-1.5"
              style={{ background: 'rgba(34,197,94,0.12)', border: '1px solid rgba(34,197,94,0.2)' }}>
              {item.changed ? item.suggested_text : '— No changes needed —'}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

/* ─── main panel ─── */

const ClauseDrilldownPanel = ({ contractId, contractName, businessUnit, version, onClose }) => {
  /* state */
  const [clauses,      setClauses]      = useState([]);
  const [redlines,     setRedlines]     = useState(null);   // null = not yet fetched
  const [tab,          setTab]          = useState('clauses');
  const [loadingTab,   setLoadingTab]   = useState({ clauses: true, redlines: false });
  const [redlineError, setRedlineError] = useState(null);

  /* ── fetch clauses on mount ── */
  useEffect(() => {
    let cancelled = false;
    const fetch = async () => {
      try {
        const res = await axios.get(
          `${API}/api/contracts/${contractId}/clauses/drilldown/`,
          { headers: headers() }
        );
        if (!cancelled) setClauses(res.data);
      } catch {}                                            // silent – empty state handles it
      finally { if (!cancelled) setLoadingTab(p => ({ ...p, clauses: false })); }
    };
    fetch();
    return () => { cancelled = true; };
  }, [contractId]);

  /* ── lazy-fetch redlines only when the user clicks that tab ── */
  const triggerAutoRedline = async () => {
    if (redlines !== null) return;                          // already fetched
    setLoadingTab(p => ({ ...p, redlines: true }));
    setRedlineError(null);
    try {
      const res = await axios.post(
        `${API}/api/contracts/${contractId}/clauses/auto-redline/`,
        {},
        { headers: headers() }
      );
      setRedlines(res.data.redlines);
    } catch (e) {
      setRedlineError(e.response?.data?.error || 'Failed to generate redlines');
    } finally {
      setLoadingTab(p => ({ ...p, redlines: false }));
    }
  };

  /* ── derived stats from clauses ── */
  const high = clauses.filter(c => c.risk_score >= 0.7).length;
  const med  = clauses.filter(c => c.risk_score >= 0.4 && c.risk_score < 0.7).length;
  const low  = clauses.filter(c => c.risk_score < 0.4).length;
  const avgRisk = clauses.length
    ? clauses.reduce((s, c) => s + c.risk_score, 0) / clauses.length
    : 0;

  /* ── tab definitions ── */
  const TABS = [
    { id: 'clauses',   label: 'Clauses',     Icon: BarChart2 },
    { id: 'trend',     label: 'Risk Trend',  Icon: TrendingDown },
    { id: 'redline',   label: 'Auto-Redline', Icon: Zap },
  ];

  /* ── render ── */
  return (
    <div className="fixed right-0 top-0 h-full w-[620px] flex flex-col z-50 overflow-hidden"
      style={{ background: 'rgba(10,18,34,0.97)', borderLeft: '1px solid rgba(51,65,85,0.4)', boxShadow: '-8px 0 40px rgba(0,0,0,0.4)' }}>

      {/* ═══ HEADER ═══ */}
      <div className="flex-shrink-0 p-4" style={{ borderBottom: '1px solid rgba(51,65,85,0.35)', background: 'rgba(15,23,42,0.6)' }}>
        <div className="flex items-start justify-between">
          <div className="min-w-0 flex-1 pr-3">
            <div className="flex items-center gap-2 mb-1">
              <h2 className="text-base font-black text-white tracking-wide">Contract Drill-Down</h2>
              {version && (
                <span className="px-2 py-0.5 text-[9px] font-black rounded"
                  style={{ background: 'rgba(59,130,246,0.2)', color: '#60a5fa', border: '1px solid rgba(59,130,246,0.35)' }}>
                  v{version}
                </span>
              )}
            </div>
            <p className="text-[12px] font-semibold text-cyan-400 truncate" title={contractName}>{contractName}</p>
            {businessUnit && <p className="text-[10px] text-slate-500 mt-0.5">{businessUnit}</p>}
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-slate-500 hover:text-white transition"
            style={{ background: 'rgba(51,65,85,0.3)' }}>
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* ── stats bar ── */}
        <div className="flex items-center gap-6 mt-3 pt-3" style={{ borderTop: '1px solid rgba(51,65,85,0.25)' }}>
          <StatBadge count={clauses.length} label="Total"   color="#e2e8f0" />
          <StatBadge count={high}           label="High"    color="#f87171" />
          <StatBadge count={med}            label="Medium"  color="#fde047" />
          <StatBadge count={low}            label="Low"     color="#86efac" />
          <div className="ml-auto flex flex-col items-end">
            <span className="text-[10px] text-slate-500">Avg Risk</span>
            <span className="text-[13px] font-black" style={{ color: avgRisk >= 0.7 ? '#f87171' : avgRisk >= 0.4 ? '#fde047' : '#86efac' }}>
              {(avgRisk * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      </div>

      {/* ═══ TABS ═══ */}
      <div className="flex-shrink-0 flex" style={{ borderBottom: '1px solid rgba(51,65,85,0.3)', background: 'rgba(15,23,42,0.5)' }}>
        {TABS.map(({ id, label, Icon }) => {
          const active = tab === id;
          return (
            <button key={id}
              onClick={() => {
                setTab(id);
                if (id === 'redline') triggerAutoRedline();
              }}
              className="flex-1 flex items-center justify-center gap-1.5 py-2.5 text-[11px] font-bold tracking-wide transition"
              style={{
                color: active ? '#22d3ee' : '#94a3b8',
                borderBottom: active ? '2px solid #22d3ee' : '2px solid transparent',
                background: active ? 'rgba(34,211,238,0.06)' : 'transparent',
              }}>
              <Icon size={13} />
              {label}
            </button>
          );
        })}
      </div>

      {/* ═══ TAB CONTENT ═══ */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3" style={{ background: 'rgba(10,18,34,0.9)' }}>

        {/* ── CLAUSES tab ── */}
        {tab === 'clauses' && (
          loadingTab.clauses
            ? <div className="flex items-center justify-center h-full"><div className="animate-spin rounded-full h-10 w-10 border-b-2 border-cyan-400" /></div>
            : clauses.length === 0
              ? <div className="flex flex-col items-center justify-center h-full text-slate-500">
                  <AlertCircle className="w-10 h-10 mb-2" />
                  <p className="text-sm">No clauses extracted yet</p>
                  <p className="text-xs mt-1">Run clause extraction on this contract first</p>
                </div>
              : clauses.map((c, i) => <ClauseCard key={c.clause_id} clause={c} index={i} />)
        )}

        {/* ── RISK TREND tab ── */}
        {tab === 'trend' && (
          <div>
            <p className="text-[10px] text-slate-500 mb-3">
              Risk score evolution across contract versions. Snapshots are recorded each time the contract is analysed through the maps pipeline.
            </p>
            <div className="rounded-xl p-3" style={{ background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(51,65,85,0.3)' }}>
              <RiskTrendChart contractId={contractId} currentRisk={avgRisk * 100} />
            </div>
            {/* legend callout when single-point fallback */}
            <div className="mt-3 rounded-lg px-3 py-2" style={{ background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.25)' }}>
              <p className="text-[10px] text-blue-300">
                <strong>How it works:</strong> Each time you upload a new version or re-analyse the contract, a risk snapshot is recorded. The trend shows how risk moved over those snapshots.
              </p>
            </div>
          </div>
        )}

        {/* ── AUTO-REDLINE tab ── */}
        {tab === 'redline' && (
          loadingTab.redlines
            ? <div className="flex items-center justify-center h-40">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400" />
              </div>
            : redlineError
              ? <div className="flex flex-col items-center justify-center h-40 text-red-400">
                  <AlertCircle className="w-8 h-8 mb-2" />
                  <p className="text-sm">{redlineError}</p>
                </div>
              : redlines === null
                ? <div className="flex flex-col items-center justify-center h-40 text-slate-500">
                    <p>Waiting…</p>
                  </div>
                : redlines.length === 0
                  ? <div className="flex flex-col items-center justify-center h-40 text-slate-500">
                      <AlertCircle className="w-10 h-10 mb-2" />
                      <p className="text-sm">No high-risk clauses detected</p>
                      <p className="text-xs mt-1">All clauses scored below the 60% risk threshold</p>
                    </div>
                  : <>
                      {/* summary strip */}
                      <div className="rounded-lg px-3 py-2 flex items-center justify-between"
                        style={{ background: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.25)' }}>
                        <p className="text-[11px] text-green-300 font-bold">
                          {redlines.filter(r => r.changed).length} of {redlines.length} clauses have suggested fixes
                        </p>
                        <span className="text-[9px] text-green-400 font-black px-1.5 py-0.5 rounded"
                          style={{ background: 'rgba(34,197,94,0.2)', border: '1px solid rgba(34,197,94,0.3)' }}>
                          AUTO-REDLINED
                        </span>
                      </div>

                      {/* redline cards */}
                      {redlines.map((item, i) => <RedlineCard key={item.clause_id} item={item} index={i} />)}
                    </>
        )}
      </div>
    </div>
  );
};

export default ClauseDrilldownPanel;
