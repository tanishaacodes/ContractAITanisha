import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  BarChart, Bar, LineChart, Line, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, Cell, ReferenceLine,
} from 'recharts';
import {
  getBuyerDashboard, getWinnerRecommendation, getCollusionAnalysis,
  getLegalGrid, seedDemoData, getBids, getVendors, submitBid, createVendor, deleteBid,
} from '../services/buyerBidService';

// ─────────────────────────────────────────────────────────────────────────────
// CONSTANTS
// ─────────────────────────────────────────────────────────────────────────────
const TABS = [
  { id: 'overview',     label: 'Overview',              icon: '⊞' },
  { id: 'competitive',  label: 'Competitive Positioning', icon: '⊡' },
  { id: 'evolution',    label: 'Bid Evolution',          icon: '◎' },
  { id: 'winner',       label: 'Winner Recommendation',  icon: '★' },
  { id: 'collusion',    label: 'Collusion Detection',    icon: '⚠' },
  { id: 'heatmap',      label: 'Legal Heatmap',          icon: '⊟' },
  { id: 'submit',       label: 'Submit Bid',             icon: '+' },
];

const ROUND_COLORS = ['#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd'];

const fmt = (n) => {
  if (!n && n !== 0) return '—';
  if (n >= 1e7) return `₹${(n / 1e7).toFixed(2)} Cr`;
  if (n >= 1e5) return `₹${(n / 1e5).toFixed(2)} L`;
  return `₹${Number(n).toLocaleString('en-IN')}`;
};

const fmtScore = (n) => (n != null ? Number(n).toFixed(2) : '—');

const DEVIATION_COLOR = (v) => {
  if (v === null || v === undefined) return '#374151';
  if (v > 0.5) return '#ef4444';
  if (v > 0.2) return '#f59e0b';
  return '#22c55e';
};

// ─────────────────────────────────────────────────────────────────────────────
// KPI CARD
// ─────────────────────────────────────────────────────────────────────────────
const KpiCard = ({ label, value, sub, accent = '#6366f1', icon }) => (
  <div
    style={{
      background: `linear-gradient(135deg, #1e1b4b 0%, #1a1a2e 100%)`,
      border: `1px solid ${accent}33`,
      borderRadius: 16,
      padding: '20px 24px',
      position: 'relative',
      overflow: 'hidden',
    }}
  >
    {/* glow */}
    <div style={{
      position: 'absolute', top: -20, right: -20, width: 80, height: 80,
      background: `radial-gradient(circle, ${accent}22 0%, transparent 70%)`,
      borderRadius: '50%',
    }} />
    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
      <div style={{
        width: 36, height: 36, borderRadius: 8,
        background: `${accent}22`, border: `1px solid ${accent}44`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 16,
      }}>{icon}</div>
      <span style={{ color: '#94a3b8', fontSize: 12, fontWeight: 500, letterSpacing: 1, textTransform: 'uppercase' }}>{label}</span>
    </div>
    <div style={{ fontSize: 28, fontWeight: 700, color: '#f1f5f9' }}>{value}</div>
    {sub && <div style={{ color: '#64748b', fontSize: 12, marginTop: 4 }}>{sub}</div>}
  </div>
);

// ─────────────────────────────────────────────────────────────────────────────
// RANK BADGE
// ─────────────────────────────────────────────────────────────────────────────
const RankBadge = ({ rank, recommendation }) => {
  const cfg = {
    1: { bg: '#ffd70022', border: '#ffd700', text: '#ffd700', label: '🏆 #1' },
    2: { bg: '#94a3b822', border: '#94a3b8', text: '#94a3b8', label: '🥈 #2' },
    3: { bg: '#cd7f3222', border: '#cd7f32', text: '#cd7f32', label: '🥉 #3' },
  }[rank] || { bg: '#1e293b', border: '#334155', text: '#64748b', label: `#${rank}` };

  return (
    <div style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      padding: '4px 12px', borderRadius: 20,
      background: cfg.bg, border: `1px solid ${cfg.border}`,
    }}>
      <span style={{ color: cfg.text, fontWeight: 700, fontSize: 13 }}>{cfg.label}</span>
      {rank === 1 && (
        <span style={{ color: '#ffd700', fontSize: 10, fontWeight: 600 }}>{recommendation}</span>
      )}
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// SCORE BAR
// ─────────────────────────────────────────────────────────────────────────────
const ScoreBar = ({ value, max = 1, color = '#6366f1', label }) => (
  <div style={{ marginBottom: 6 }}>
    {label && <div style={{ color: '#94a3b8', fontSize: 11, marginBottom: 3 }}>{label}</div>}
    <div style={{ background: '#1e293b', borderRadius: 4, height: 6, overflow: 'hidden' }}>
      <div style={{
        height: '100%', borderRadius: 4,
        width: `${Math.min(100, (value / max) * 100)}%`,
        background: `linear-gradient(90deg, ${color}, ${color}99)`,
        transition: 'width 0.6s ease',
      }} />
    </div>
  </div>
);

// ─────────────────────────────────────────────────────────────────────────────
// MAIN COMPONENT
// ─────────────────────────────────────────────────────────────────────────────
export default function BuyerBidDashboard() {
  const { tenderId } = useParams();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading]     = useState(false);
  const [seeding, setSeeding]     = useState(false);

  const [dashboard, setDashboard]   = useState(null);
  const [winner, setWinner]         = useState(null);
  const [collusion, setCollusion]   = useState(null);
  const [legalGrid, setLegalGrid]   = useState(null);
  const [vendors, setVendors]       = useState([]);
  const [bids, setBids]             = useState([]);

  // Submit-bid form state
  const [form, setForm] = useState({
    vendor_id: '', round_number: 1, total_price: '',
    technical_score: '', commercial_score: '', notes: '',
  });
  const [newVendorName, setNewVendorName] = useState('');
  const [submitMsg, setSubmitMsg] = useState('');

  // ── Fetch data ──────────────────────────────────────────────────────────
  const loadAll = useCallback(async () => {
    if (!tenderId) return;
    setLoading(true);
    try {
      const [dashRes, winRes, colRes, gridRes, vendRes, bidRes] = await Promise.allSettled([
        getBuyerDashboard(tenderId),
        getWinnerRecommendation(tenderId),
        getCollusionAnalysis(tenderId),
        getLegalGrid(tenderId),
        getVendors(),
        getBids(tenderId),
      ]);
      if (dashRes.status === 'fulfilled') setDashboard(dashRes.value.data);
      if (winRes.status  === 'fulfilled') setWinner(winRes.value.data);
      if (colRes.status  === 'fulfilled') setCollusion(colRes.value.data);
      if (gridRes.status === 'fulfilled') setLegalGrid(gridRes.value.data);
      if (vendRes.status === 'fulfilled') setVendors(vendRes.value.data);
      if (bidRes.status  === 'fulfilled') setBids(bidRes.value.data);
    } finally {
      setLoading(false);
    }
  }, [tenderId]);

  useEffect(() => { loadAll(); }, [loadAll]);

  // ── Seed demo ────────────────────────────────────────────────────────────
  const handleSeedDemo = async () => {
    setSeeding(true);
    try {
      await seedDemoData(tenderId);
      await loadAll();
    } finally {
      setSeeding(false);
    }
  };

  // ── Submit bid ───────────────────────────────────────────────────────────
  const handleCreateVendor = async () => {
    if (!newVendorName.trim()) return;
    const res = await createVendor({ name: newVendorName });
    setVendors(prev => [...prev, res.data]);
    setForm(f => ({ ...f, vendor_id: res.data.id }));
    setNewVendorName('');
  };

  const handleSubmitBid = async () => {
    if (!form.vendor_id || !form.total_price) {
      setSubmitMsg('Please fill vendor and total price.');
      return;
    }
    try {
      await submitBid(tenderId, { ...form });
      setSubmitMsg('Bid submitted successfully!');
      setForm({ vendor_id: '', round_number: 1, total_price: '', technical_score: '', commercial_score: '', notes: '' });
      await loadAll();
    } catch (e) {
      setSubmitMsg('Error submitting bid. Please try again.');
    }
  };

  const handleDeleteBid = async (bidId) => {
    if (!window.confirm('Are you sure you want to delete this bid?')) return;
    try {
      await deleteBid(tenderId, bidId);
      setSubmitMsg('Bid deleted successfully!');
      await loadAll();
    } catch (e) {
      setSubmitMsg('Error deleting bid. Please try again.');
    }
  };

  // ─────────────────────────────────────────────────────────────────────────
  // BUILD CHART DATA
  // ─────────────────────────────────────────────────────────────────────────
  const competitiveChartData = (dashboard?.competitive_positioning || [])
    .filter(r => r.round === 1)
    .map(r => ({
      vendor       : r.vendor.split(' ')[0],
      price        : Math.round(r.price / 1e7),
      technical    : r.technical_score,
      position_score: +(r.positioning_score * 100).toFixed(1),
    }));

  const evolutionVendors = dashboard
    ? Object.keys(dashboard.bid_evolution || {})
    : [];

  const evolutionChartData = (() => {
    const rounds = [1, 2, 3, 4];
    return rounds.map(r => {
      const obj = { round: `R${r}` };
      evolutionVendors.forEach(v => {
        const rd = (dashboard?.bid_evolution?.[v]?.rounds || []).find(x => x.round === r);
        if (rd) obj[v.split(' ')[0]] = +(rd.price / 1e7).toFixed(2);
      });
      return obj;
    }).filter(row => Object.keys(row).length > 1);
  })();

  const radarData = winner?.ranking?.slice(0, 5).map(r => ({
    vendor     : r.vendor.split(' ')[0],
    Technical  : r.technical_score,
    Commercial : r.commercial_score,
    Financial  : +(r.financial_rating * 100).toFixed(0),
    Performance: +(r.performance * 100).toFixed(0),
    'Low Risk' : +(100 - r.legal_risk * 100).toFixed(0),
  })) || [];

  // ─────────────────────────────────────────────────────────────────────────
  // RENDER HELPERS
  // ─────────────────────────────────────────────────────────────────────────

  const overallRisk = collusion?.overall_risk;
  const riskBadge = { CRITICAL: ['#ef4444', '#fca5a5'], HIGH: ['#f59e0b', '#fcd34d'], LOW: ['#22c55e', '#86efac'] }[overallRisk] || ['#6366f1', '#a5b4fc'];

  // ─────────────────────────────────────────────────────────────────────────
  // MAIN RENDER
  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div style={{ background: '#0a0a14', minHeight: '100vh', color: '#f1f5f9', fontFamily: "'Inter', sans-serif" }}>

      {/* ── HERO HEADER ─────────────────────────────────────────────────── */}
      <div style={{
        background: 'linear-gradient(135deg, #1e1b4b 0%, #0f172a 40%, #0a0a14 100%)',
        borderBottom: '1px solid #1e293b',
        padding: '32px 40px 24px',
        position: 'relative', overflow: 'hidden',
      }}>
        {/* Ambient glow */}
        <div style={{ position: 'absolute', top: -60, left: -60, width: 300, height: 300, background: 'radial-gradient(circle, #6366f122 0%, transparent 70%)', pointerEvents: 'none' }} />
        <div style={{ position: 'absolute', top: -40, right: 100, width: 200, height: 200, background: 'radial-gradient(circle, #8b5cf622 0%, transparent 70%)', pointerEvents: 'none' }} />

        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 20, flexWrap: 'wrap' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
              <button onClick={() => navigate(-1)} style={{ background: '#1e293b', border: '1px solid #334155', color: '#94a3b8', borderRadius: 8, padding: '6px 12px', cursor: 'pointer', fontSize: 13 }}>← Back</button>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{ width: 44, height: 44, borderRadius: 12, background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22 }}>⊞</div>
                <div>
                  <div style={{ fontSize: 11, color: '#6366f1', fontWeight: 700, letterSpacing: 2, textTransform: 'uppercase' }}>Buyer Intelligence Platform</div>
                  <h1 style={{ margin: 0, fontSize: 26, fontWeight: 800, color: '#f1f5f9', letterSpacing: -0.5 }}>
                    Enterprise Bid Evaluation
                  </h1>
                </div>
              </div>
            </div>
            {dashboard && (
              <p style={{ margin: 0, color: '#64748b', fontSize: 14 }}>
                Tender: <span style={{ color: '#94a3b8' }}>{dashboard.tender_reference || '—'}</span>
                &nbsp;·&nbsp;
                {dashboard.tender_title?.slice(0, 60)}
              </p>
            )}
          </div>

          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <button
              onClick={handleSeedDemo}
              disabled={seeding}
              style={{
                background: seeding ? '#1e293b' : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                border: 'none', borderRadius: 10, color: '#fff',
                padding: '10px 20px', cursor: seeding ? 'not-allowed' : 'pointer',
                fontWeight: 600, fontSize: 13,
              }}
            >
              {seeding ? 'Seeding…' : '+ Seed Demo Data'}
            </button>
            <button
              onClick={loadAll}
              style={{ background: '#1e293b', border: '1px solid #334155', color: '#94a3b8', borderRadius: 10, padding: '10px 20px', cursor: 'pointer', fontSize: 13 }}
            >
              ↻ Refresh
            </button>
          </div>
        </div>

        {/* KPI row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 16, marginTop: 28 }}>
          <KpiCard icon="🏢" accent="#6366f1" label="Vendors"     value={dashboard?.vendor_count ?? '—'} sub="Active bidders" />
          <KpiCard icon="🔄" accent="#8b5cf6" label="Bid Rounds"  value={dashboard?.round_count  ?? '—'} sub="Rounds completed" />
          <KpiCard icon="📋" accent="#a78bfa" label="Total Bids"  value={dashboard?.bid_count    ?? '—'} sub="Submissions" />
          <KpiCard icon="⚠️" accent={riskBadge[0]} label="Collusion Risk" value={overallRisk ?? '—'} sub={`${collusion?.total_alerts ?? 0} alerts`} />
          <KpiCard
            icon="🏆"
            accent="#ffd700"
            label="Recommended Winner"
            value={winner?.ranking?.[0]?.vendor?.split(' ')[0] ?? '—'}
            sub={winner?.ranking?.[0] ? `Score: ${fmtScore(winner.ranking[0].composite_score)}` : 'No data'}
          />
        </div>
      </div>

      {/* ── TAB STRIP ───────────────────────────────────────────────────── */}
      <div style={{ background: '#0f172a', borderBottom: '1px solid #1e293b', display: 'flex', overflowX: 'auto', padding: '0 40px' }}>
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '14px 22px', border: 'none', cursor: 'pointer',
              background: activeTab === tab.id ? '#0a0a14' : 'transparent',
              color: activeTab === tab.id ? '#818cf8' : '#64748b',
              borderTop: activeTab === tab.id ? '2px solid #6366f1' : '2px solid transparent',
              fontWeight: activeTab === tab.id ? 700 : 500,
              fontSize: 13, whiteSpace: 'nowrap',
              display: 'flex', alignItems: 'center', gap: 7,
              transition: 'all 0.2s',
            }}
          >
            <span>{tab.icon}</span> {tab.label}
          </button>
        ))}
      </div>

      {/* ── TAB CONTENT ─────────────────────────────────────────────────── */}
      <div style={{ padding: '32px 40px' }}>

        {loading && (
          <div style={{ textAlign: 'center', padding: 80, color: '#64748b' }}>
            <div style={{ width: 40, height: 40, border: '3px solid #334155', borderTop: '3px solid #6366f1', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 16px' }} />
            Loading intelligence data…
          </div>
        )}

        {/* ── OVERVIEW ──────────────────────────────────────────────────── */}
        {!loading && activeTab === 'overview' && (
          <div style={{ display: 'grid', gap: 28 }}>

            {/* No data banner */}
            {(!dashboard || dashboard.vendor_count === 0) && (
              <div style={{ background: '#1e1b4b', border: '1px solid #6366f155', borderRadius: 16, padding: 40, textAlign: 'center' }}>
                <div style={{ fontSize: 48, marginBottom: 12 }}>📊</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: '#f1f5f9', marginBottom: 8 }}>No Bids Yet</div>
                <div style={{ color: '#64748b', marginBottom: 24 }}>Seed demo data or submit vendor bids to get started.</div>
                <button onClick={handleSeedDemo} style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', border: 'none', color: '#fff', borderRadius: 10, padding: '12px 28px', cursor: 'pointer', fontWeight: 600 }}>
                  {seeding ? 'Seeding…' : '+ Seed 6 Demo Vendors'}
                </button>
              </div>
            )}

            {/* Price comparison chart */}
            {competitiveChartData.length > 0 && (
              <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 16, padding: 28 }}>
                <h3 style={{ margin: '0 0 20px', color: '#f1f5f9', fontWeight: 700 }}>Price vs Technical Score (Round 1)</h3>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={competitiveChartData} barGap={4}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="vendor" tick={{ fill: '#64748b', fontSize: 11 }} />
                    <YAxis yAxisId="left" tick={{ fill: '#64748b', fontSize: 11 }} label={{ value: 'Price (Cr)', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 11 }} />
                    <YAxis yAxisId="right" orientation="right" domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 11 }} label={{ value: 'Score', angle: 90, position: 'insideRight', fill: '#64748b', fontSize: 11 }} />
                    <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, color: '#f1f5f9' }} />
                    <Legend />
                    <Bar yAxisId="left" dataKey="price" name="Price (Cr)" radius={[4, 4, 0, 0]}>
                      {competitiveChartData.map((_, i) => <Cell key={i} fill={ROUND_COLORS[i % ROUND_COLORS.length]} />)}
                    </Bar>
                    <Bar yAxisId="right" dataKey="technical" name="Technical Score" fill="#22c55e44" stroke="#22c55e" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Bid Evolution lines */}
            {evolutionChartData.length > 0 && (
              <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 16, padding: 28 }}>
                <h3 style={{ margin: '0 0 20px', color: '#f1f5f9', fontWeight: 700 }}>Bid Price Evolution by Round (Cr)</h3>
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={evolutionChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="round" tick={{ fill: '#64748b', fontSize: 12 }} />
                    <YAxis tick={{ fill: '#64748b', fontSize: 11 }} />
                    <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, color: '#f1f5f9' }} />
                    <Legend />
                    {evolutionVendors.map((v, i) => (
                      <Line
                        key={v} type="monotone"
                        dataKey={v.split(' ')[0]}
                        stroke={ROUND_COLORS[i % ROUND_COLORS.length]}
                        strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        )}

        {/* ── COMPETITIVE POSITIONING ───────────────────────────────────── */}
        {!loading && activeTab === 'competitive' && (
          <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 16, padding: 28, overflowX: 'auto' }}>
            <h3 style={{ margin: '0 0 20px', color: '#f1f5f9', fontWeight: 700 }}>Competitive Positioning Grid</h3>
            {(dashboard?.competitive_positioning || []).length === 0 ? (
              <div style={{ color: '#64748b', textAlign: 'center', padding: 40 }}>No data — seed demo or submit bids.</div>
            ) : (
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #1e293b' }}>
                    {['Vendor', 'Round', 'Price', 'vs Lowest', 'vs Avg %', 'Technical', 'Commercial', 'Legal Risk', 'Aggression', 'Position Score'].map(h => (
                      <th key={h} style={{ textAlign: 'left', padding: '10px 14px', color: '#64748b', fontWeight: 600, fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.8, whiteSpace: 'nowrap' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(dashboard?.competitive_positioning || []).map((row, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid #0f172a', background: i % 2 === 0 ? '#0a0a1466' : 'transparent' }}>
                      <td style={{ padding: '12px 14px', color: '#f1f5f9', fontWeight: 600 }}>{row.vendor}</td>
                      <td style={{ padding: '12px 14px' }}>
                        <span style={{ background: '#6366f122', border: '1px solid #6366f144', color: '#818cf8', borderRadius: 6, padding: '2px 8px', fontSize: 11 }}>R{row.round}</span>
                      </td>
                      <td style={{ padding: '12px 14px', color: '#a78bfa', fontWeight: 600 }}>{fmt(row.price)}</td>
                      <td style={{ padding: '12px 14px', color: row.price_gap_from_lowest === 0 ? '#22c55e' : '#f59e0b' }}>
                        {row.price_gap_from_lowest === 0 ? '✓ Lowest' : `+${fmt(row.price_gap_from_lowest)}`}
                      </td>
                      <td style={{ padding: '12px 14px', color: row.price_vs_avg < 0 ? '#22c55e' : '#f59e0b' }}>
                        {row.price_vs_avg > 0 ? '+' : ''}{row.price_vs_avg}%
                      </td>
                      <td style={{ padding: '12px 14px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <div style={{ flex: 1, background: '#1e293b', borderRadius: 3, height: 4 }}>
                            <div style={{ width: `${row.technical_score}%`, height: '100%', background: '#22c55e', borderRadius: 3 }} />
                          </div>
                          <span style={{ color: '#94a3b8', minWidth: 28 }}>{fmtScore(row.technical_score)}</span>
                        </div>
                      </td>
                      <td style={{ padding: '12px 14px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <div style={{ flex: 1, background: '#1e293b', borderRadius: 3, height: 4 }}>
                            <div style={{ width: `${row.commercial_score}%`, height: '100%', background: '#6366f1', borderRadius: 3 }} />
                          </div>
                          <span style={{ color: '#94a3b8', minWidth: 28 }}>{fmtScore(row.commercial_score)}</span>
                        </div>
                      </td>
                      <td style={{ padding: '12px 14px' }}>
                        <span style={{ color: row.legal_risk_score > 0.4 ? '#ef4444' : '#22c55e', fontWeight: 600 }}>
                          {(row.legal_risk_score * 100).toFixed(0)}%
                        </span>
                      </td>
                      <td style={{ padding: '12px 14px' }}>
                        <div style={{ width: 60, height: 6, background: '#1e293b', borderRadius: 3 }}>
                          <div style={{ width: `${row.aggression_index * 100}%`, height: '100%', background: 'linear-gradient(90deg, #f59e0b, #ef4444)', borderRadius: 3 }} />
                        </div>
                      </td>
                      <td style={{ padding: '12px 14px' }}>
                        <span style={{
                          background: row.positioning_score > 0.6 ? '#22c55e22' : row.positioning_score > 0.4 ? '#f59e0b22' : '#ef444422',
                          border: `1px solid ${row.positioning_score > 0.6 ? '#22c55e' : row.positioning_score > 0.4 ? '#f59e0b' : '#ef4444'}`,
                          color: row.positioning_score > 0.6 ? '#22c55e' : row.positioning_score > 0.4 ? '#f59e0b' : '#ef4444',
                          borderRadius: 8, padding: '3px 10px', fontWeight: 700,
                        }}>
                          {fmtScore(row.positioning_score)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* ── BID EVOLUTION ─────────────────────────────────────────────── */}
        {!loading && activeTab === 'evolution' && (
          <div style={{ display: 'grid', gap: 24 }}>
            {evolutionVendors.length === 0 ? (
              <div style={{ color: '#64748b', textAlign: 'center', padding: 60 }}>No evolution data available.</div>
            ) : evolutionVendors.map((vendorName, vi) => {
              const info = dashboard.bid_evolution[vendorName];
              const rounds = info.rounds || [];
              return (
                <div key={vendorName} style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 16, padding: 24 }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                    <div>
                      <h4 style={{ margin: 0, color: '#f1f5f9', fontWeight: 700, fontSize: 16 }}>{vendorName}</h4>
                      <span style={{ color: info.price_delta_pct < 0 ? '#22c55e' : '#f59e0b', fontSize: 13 }}>
                        Price change: {info.price_delta_pct > 0 ? '+' : ''}{info.price_delta_pct}% across rounds
                      </span>
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      {rounds.map(r => (
                        <div key={r.round} style={{ textAlign: 'center', padding: '8px 14px', background: '#1e293b', borderRadius: 10 }}>
                          <div style={{ color: ROUND_COLORS[r.round - 1], fontWeight: 700, fontSize: 15 }}>R{r.round}</div>
                          <div style={{ color: '#f1f5f9', fontSize: 13 }}>{fmt(r.price)}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                  <ResponsiveContainer width="100%" height={180}>
                    <LineChart data={rounds}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="round" tickFormatter={v => `R${v}`} tick={{ fill: '#64748b', fontSize: 11 }} />
                      <YAxis tick={{ fill: '#64748b', fontSize: 11 }} tickFormatter={v => `${(v / 1e7).toFixed(0)}Cr`} />
                      <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, color: '#f1f5f9' }} formatter={v => [fmt(v)]} />
                      <Line type="monotone" dataKey="price" stroke={ROUND_COLORS[vi % ROUND_COLORS.length]} strokeWidth={2.5} dot={{ r: 5 }} activeDot={{ r: 7 }} name="Price" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              );
            })}
          </div>
        )}

        {/* ── WINNER RECOMMENDATION ─────────────────────────────────────── */}
        {!loading && activeTab === 'winner' && (
          <div style={{ display: 'grid', gap: 24 }}>
            {/* Radar chart */}
            {radarData.length > 0 && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
                <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 16, padding: 28 }}>
                  <h3 style={{ margin: '0 0 20px', color: '#f1f5f9', fontWeight: 700 }}>Multi-Factor Radar (Top Vendor)</h3>
                  <ResponsiveContainer width="100%" height={280}>
                    <RadarChart data={Object.entries(radarData[0] || {}).filter(([k]) => k !== 'vendor').map(([k, v]) => ({ factor: k, score: v }))}>
                      <PolarGrid stroke="#1e293b" />
                      <PolarAngleAxis dataKey="factor" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                      <PolarRadiusAxis domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 10 }} />
                      <Radar dataKey="score" stroke="#6366f1" fill="#6366f133" strokeWidth={2} />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
                <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 16, padding: 28 }}>
                  <h3 style={{ margin: '0 0 20px', color: '#f1f5f9', fontWeight: 700 }}>Score Weights</h3>
                  {winner?.weights && Object.entries(winner.weights).map(([k, v]) => (
                    <div key={k} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid #1e293b' }}>
                      <span style={{ color: '#94a3b8', textTransform: 'capitalize' }}>{k.replace(/_/g, ' ')}</span>
                      <span style={{ color: v.startsWith('-') ? '#ef4444' : '#22c55e', fontWeight: 700, fontSize: 15 }}>{v}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Ranking table */}
            <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 16, padding: 28 }}>
              <h3 style={{ margin: '0 0 20px', color: '#f1f5f9', fontWeight: 700 }}>AI Recommended Winner Ranking</h3>
              {(winner?.ranking || []).length === 0 ? (
                <div style={{ color: '#64748b', textAlign: 'center', padding: 40 }}>No bids available for ranking.</div>
              ) : (winner.ranking || []).map((r, i) => (
                <div key={r.vendor_id || i} style={{
                  background: i === 0 ? '#ffd70011' : '#0a0a1466',
                  border: i === 0 ? '1px solid #ffd70033' : '1px solid #1e293b',
                  borderRadius: 12, padding: '20px 24px', marginBottom: 12,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                      <RankBadge rank={r.rank} recommendation={r.recommendation} />
                      <div>
                        <div style={{ fontWeight: 700, color: '#f1f5f9', fontSize: 16 }}>{r.vendor}</div>
                        <div style={{ color: '#64748b', fontSize: 13 }}>Round {r.round} · {fmt(r.price)}</div>
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: 26, fontWeight: 800, color: i === 0 ? '#ffd700' : '#818cf8' }}>{(r.composite_score * 100).toFixed(1)}</div>
                      <div style={{ color: '#64748b', fontSize: 11 }}>Composite Score</div>
                    </div>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 8 }}>
                    {r.score_breakdown && Object.entries(r.score_breakdown).map(([k, v]) => (
                      <div key={k} style={{ textAlign: 'center' }}>
                        <div style={{ color: v < 0 ? '#ef4444' : '#22c55e', fontWeight: 700, fontSize: 13 }}>{v > 0 ? '+' : ''}{(v * 100).toFixed(1)}</div>
                        <div style={{ color: '#64748b', fontSize: 10, textTransform: 'capitalize' }}>{k.replace(/_/g, ' ')}</div>
                      </div>
                    ))}
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginTop: 14 }}>
                    <ScoreBar value={r.technical_score / 100} label="Technical" color="#22c55e" />
                    <ScoreBar value={r.commercial_score / 100} label="Commercial" color="#6366f1" />
                    <ScoreBar value={r.financial_rating} label="Financial" color="#f59e0b" />
                    <ScoreBar value={1 - r.legal_risk} label="Legal Compliance" color="#a78bfa" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── COLLUSION DETECTION ───────────────────────────────────────── */}
        {!loading && activeTab === 'collusion' && (
          <div style={{ display: 'grid', gap: 24 }}>
            {/* Risk banner */}
            <div style={{
              background: overallRisk === 'CRITICAL' ? '#ef444415' : overallRisk === 'HIGH' ? '#f59e0b15' : '#22c55e15',
              border: `1px solid ${overallRisk === 'CRITICAL' ? '#ef4444' : overallRisk === 'HIGH' ? '#f59e0b' : '#22c55e'}44`,
              borderRadius: 16, padding: '24px 28px',
              display: 'flex', alignItems: 'center', gap: 20,
            }}>
              <div style={{ fontSize: 40 }}>{overallRisk === 'CRITICAL' ? '🚨' : overallRisk === 'HIGH' ? '⚠️' : '✅'}</div>
              <div>
                <div style={{ fontWeight: 800, fontSize: 22, color: riskBadge[1] }}>{overallRisk ?? '—'} COLLUSION RISK</div>
                <div style={{ color: '#94a3b8', fontSize: 14, marginTop: 4 }}>
                  {collusion?.total_alerts ?? 0} suspicious pattern(s) detected across {collusion?.price_collusion?.length ?? 0} price pairs and {collusion?.clause_collusion?.length ?? 0} clause pairs.
                </div>
              </div>
            </div>

            {/* Price Collusion */}
            <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 16, padding: 28 }}>
              <h3 style={{ margin: '0 0 20px', color: '#f1f5f9', fontWeight: 700, display: 'flex', alignItems: 'center', gap: 10 }}>
                💰 Price Collusion Alerts
                <span style={{ background: '#ef444422', border: '1px solid #ef4444', color: '#ef4444', borderRadius: 10, padding: '2px 10px', fontSize: 12 }}>
                  {collusion?.price_collusion?.length ?? 0}
                </span>
              </h3>
              {(collusion?.price_collusion || []).length === 0 ? (
                <div style={{ color: '#22c55e', display: 'flex', alignItems: 'center', gap: 8 }}>✓ No suspicious price patterns detected.</div>
              ) : (collusion.price_collusion || []).map((alert, i) => (
                <div key={i} style={{ background: '#1a0a0a', border: '1px solid #ef444422', borderRadius: 10, padding: '16px 20px', marginBottom: 10 }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ fontWeight: 600, color: '#fca5a5' }}>
                      {alert.vendor1} ↔ {alert.vendor2}
                    </div>
                    <span style={{ background: '#ef444422', border: '1px solid #ef4444', color: '#ef4444', borderRadius: 8, padding: '3px 10px', fontSize: 12, fontWeight: 700 }}>
                      {alert.risk_level}
                    </span>
                  </div>
                  <div style={{ color: '#64748b', fontSize: 13, marginTop: 6 }}>
                    Price similarity: <strong style={{ color: '#f87171' }}>{(alert.similarity * 100).toFixed(1)}%</strong> — {alert.reason}
                  </div>
                </div>
              ))}
            </div>

            {/* Clause Collusion */}
            <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 16, padding: 28 }}>
              <h3 style={{ margin: '0 0 20px', color: '#f1f5f9', fontWeight: 700, display: 'flex', alignItems: 'center', gap: 10 }}>
                📄 Clause Similarity Alerts
                <span style={{ background: '#f59e0b22', border: '1px solid #f59e0b', color: '#f59e0b', borderRadius: 10, padding: '2px 10px', fontSize: 12 }}>
                  {collusion?.clause_collusion?.length ?? 0}
                </span>
              </h3>
              {(collusion?.clause_collusion || []).length === 0 ? (
                <div style={{ color: '#22c55e', display: 'flex', alignItems: 'center', gap: 8 }}>✓ No suspicious clause patterns detected.</div>
              ) : (collusion.clause_collusion || []).map((alert, i) => (
                <div key={i} style={{ background: '#1a1000', border: '1px solid #f59e0b22', borderRadius: 10, padding: '16px 20px', marginBottom: 10 }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ fontWeight: 600, color: '#fcd34d' }}>
                      {alert.vendor1} ↔ {alert.vendor2}
                    </div>
                    <span style={{ background: '#f59e0b22', border: '1px solid #f59e0b', color: '#f59e0b', borderRadius: 8, padding: '3px 10px', fontSize: 12, fontWeight: 700 }}>
                      {alert.risk_level}
                    </span>
                  </div>
                  <div style={{ color: '#64748b', fontSize: 13, marginTop: 6 }}>
                    Clause similarity: <strong style={{ color: '#fbbf24' }}>{(alert.clause_similarity * 100).toFixed(1)}%</strong> — {alert.reason}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── LEGAL HEATMAP ─────────────────────────────────────────────── */}
        {!loading && activeTab === 'heatmap' && (
          <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 16, padding: 28, overflowX: 'auto' }}>
            <h3 style={{ margin: '0 0 8px', color: '#f1f5f9', fontWeight: 700 }}>Legal Clause Deviation Heatmap</h3>
            <p style={{ color: '#64748b', fontSize: 13, margin: '0 0 24px' }}>Deviation from tender baseline — 🟩 Low · 🟨 Medium · 🟥 High</p>
            {(!legalGrid?.comparison_grid || legalGrid.comparison_grid.length === 0) ? (
              <div style={{ color: '#64748b', textAlign: 'center', padding: 40 }}>No clause data available. Submit bids with clause deviations.</div>
            ) : (
              <table style={{ borderCollapse: 'collapse', minWidth: 900 }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left', padding: '10px 16px', color: '#64748b', fontWeight: 600, fontSize: 11, textTransform: 'uppercase', position: 'sticky', left: 0, background: '#0f172a', zIndex: 2 }}>Clause Type</th>
                    {(legalGrid.comparison_grid[0]?.vendors || []).map((v, i) => (
                      <th key={i} style={{ padding: '10px 12px', color: '#94a3b8', fontWeight: 600, fontSize: 11, whiteSpace: 'nowrap', textAlign: 'center' }}>
                        {v.vendor.split(' ')[0]}<br />
                        <span style={{ color: '#64748b', fontSize: 10 }}>R{v.round}</span>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {legalGrid.comparison_grid.map((row, ri) => (
                    <tr key={ri} style={{ borderBottom: '1px solid #0a0a14' }}>
                      <td style={{ padding: '12px 16px', color: '#f1f5f9', fontWeight: 600, fontSize: 13, position: 'sticky', left: 0, background: '#0f172a' }}>
                        {row.clause_type.replace(/_/g, ' ')}
                      </td>
                      {row.vendors.map((v, vi) => (
                        <td key={vi} style={{ padding: '8px 12px', textAlign: 'center' }}>
                          {v.deviation !== null ? (
                            <div style={{
                              background: DEVIATION_COLOR(v.deviation) + '22',
                              border: `1px solid ${DEVIATION_COLOR(v.deviation)}55`,
                              color: DEVIATION_COLOR(v.deviation),
                              borderRadius: 8, padding: '6px 10px',
                              fontWeight: 700, fontSize: 13,
                            }}>
                              {(v.deviation * 100).toFixed(0)}%
                            </div>
                          ) : (
                            <span style={{ color: '#374151', fontSize: 18 }}>—</span>
                          )}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* ── SUBMIT BID ────────────────────────────────────────────────── */}
        {!loading && activeTab === 'submit' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, maxWidth: 900 }}>

            {/* Create Vendor */}
            <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 16, padding: 28 }}>
              <h3 style={{ margin: '0 0 20px', color: '#f1f5f9', fontWeight: 700 }}>Create Vendor</h3>
              <input
                placeholder="Vendor Name"
                value={newVendorName}
                onChange={e => setNewVendorName(e.target.value)}
                style={{ width: '100%', background: '#1e293b', border: '1px solid #334155', color: '#f1f5f9', borderRadius: 10, padding: '12px 16px', fontSize: 14, marginBottom: 12, boxSizing: 'border-box' }}
              />
              <button onClick={handleCreateVendor} style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', border: 'none', color: '#fff', borderRadius: 10, padding: '12px 24px', cursor: 'pointer', fontWeight: 600, width: '100%' }}>
                Create Vendor
              </button>
              {vendors.length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <div style={{ color: '#64748b', fontSize: 12, marginBottom: 8 }}>Existing Vendors ({vendors.length})</div>
                  <div style={{ maxHeight: 200, overflowY: 'auto' }}>
                    {vendors.map(v => (
                      <div key={v.id} style={{ padding: '6px 0', borderBottom: '1px solid #1e293b', color: '#94a3b8', fontSize: 13 }}>
                        {v.name}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Submit Bid */}
            <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 16, padding: 28 }}>
              <h3 style={{ margin: '0 0 20px', color: '#f1f5f9', fontWeight: 700 }}>Submit Vendor Bid</h3>

              <label style={{ color: '#64748b', fontSize: 12, display: 'block', marginBottom: 4 }}>Select Vendor</label>
              <select
                value={form.vendor_id}
                onChange={e => setForm(f => ({ ...f, vendor_id: e.target.value }))}
                style={{ width: '100%', background: '#1e293b', border: '1px solid #334155', color: '#f1f5f9', borderRadius: 10, padding: '12px 16px', fontSize: 14, marginBottom: 12, boxSizing: 'border-box' }}
              >
                <option value="">— Select Vendor —</option>
                {vendors.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}
              </select>

              <label style={{ color: '#64748b', fontSize: 12, display: 'block', marginBottom: 4 }}>Bid Round</label>
              <select
                value={form.round_number}
                onChange={e => setForm(f => ({ ...f, round_number: e.target.value }))}
                style={{ width: '100%', background: '#1e293b', border: '1px solid #334155', color: '#f1f5f9', borderRadius: 10, padding: '12px 16px', fontSize: 14, marginBottom: 12, boxSizing: 'border-box' }}
              >
                {[1, 2, 3, 4].map(r => <option key={r} value={r}>Round {r}{r === 4 ? ' (BAFO)' : ''}</option>)}
              </select>

              {[
                { key: 'total_price', label: 'Total Price (₹)', placeholder: 'e.g. 5000000000' },
                { key: 'technical_score', label: 'Technical Score (0-100)', placeholder: 'e.g. 82' },
                { key: 'commercial_score', label: 'Commercial Score (0-100)', placeholder: 'e.g. 75' },
              ].map(({ key, label, placeholder }) => (
                <div key={key}>
                  <label style={{ color: '#64748b', fontSize: 12, display: 'block', marginBottom: 4 }}>{label}</label>
                  <input
                    type="number"
                    placeholder={placeholder}
                    value={form[key]}
                    onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
                    style={{ width: '100%', background: '#1e293b', border: '1px solid #334155', color: '#f1f5f9', borderRadius: 10, padding: '12px 16px', fontSize: 14, marginBottom: 12, boxSizing: 'border-box' }}
                  />
                </div>
              ))}

              <label style={{ color: '#64748b', fontSize: 12, display: 'block', marginBottom: 4 }}>Notes</label>
              <textarea
                placeholder="Optional notes"
                value={form.notes}
                onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
                rows={3}
                style={{ width: '100%', background: '#1e293b', border: '1px solid #334155', color: '#f1f5f9', borderRadius: 10, padding: '12px 16px', fontSize: 14, marginBottom: 16, boxSizing: 'border-box', resize: 'vertical' }}
              />

              <button onClick={handleSubmitBid} style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', border: 'none', color: '#fff', borderRadius: 10, padding: '14px 24px', cursor: 'pointer', fontWeight: 700, width: '100%', fontSize: 15 }}>
                Submit Bid
              </button>
              {submitMsg && (
                <div style={{ marginTop: 12, color: submitMsg.includes('Error') ? '#ef4444' : '#22c55e', fontSize: 13 }}>
                  {submitMsg}
                </div>
              )}
            </div>
            </div>

            {/* Existing Bids - Delete Management */}
            {bids.length > 0 && (
              <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 16, padding: 28, maxWidth: 900 }}>
                <h3 style={{ margin: '0 0 20px', color: '#f1f5f9', fontWeight: 700 }}>Existing Bids ({bids.length})</h3>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ borderBottom: '2px solid #1e293b' }}>
                        <th style={{ padding: '12px 8px', textAlign: 'left', color: '#64748b', fontSize: 12, fontWeight: 600 }}>VENDOR</th>
                        <th style={{ padding: '12px 8px', textAlign: 'center', color: '#64748b', fontSize: 12, fontWeight: 600 }}>ROUND</th>
                        <th style={{ padding: '12px 8px', textAlign: 'right', color: '#64748b', fontSize: 12, fontWeight: 600 }}>PRICE</th>
                        <th style={{ padding: '12px 8px', textAlign: 'center', color: '#64748b', fontSize: 12, fontWeight: 600 }}>TECH</th>
                        <th style={{ padding: '12px 8px', textAlign: 'center', color: '#64748b', fontSize: 12, fontWeight: 600 }}>COMM</th>
                        <th style={{ padding: '12px 8px', textAlign: 'center', color: '#64748b', fontSize: 12, fontWeight: 600 }}>ACTION</th>
                      </tr>
                    </thead>
                    <tbody>
                      {bids.map(bid => (
                        <tr key={bid.id} style={{ borderBottom: '1px solid #1e293b' }}>
                          <td style={{ padding: '12px 8px', color: '#f1f5f9', fontSize: 14 }}>{bid.vendor__name}</td>
                          <td style={{ padding: '12px 8px', textAlign: 'center', color: '#94a3b8', fontSize: 13 }}>R{bid.round_number}</td>
                          <td style={{ padding: '12px 8px', textAlign: 'right', color: '#f1f5f9', fontWeight: 600, fontSize: 14 }}>{fmt(bid.total_price)}</td>
                          <td style={{ padding: '12px 8px', textAlign: 'center', color: '#94a3b8', fontSize: 13 }}>{bid.technical_score}</td>
                          <td style={{ padding: '12px 8px', textAlign: 'center', color: '#94a3b8', fontSize: 13 }}>{bid.commercial_score}</td>
                          <td style={{ padding: '12px 8px', textAlign: 'center' }}>
                            <button
                              onClick={() => handleDeleteBid(bid.id)}
                              style={{
                                background: '#ef444422',
                                border: '1px solid #ef4444',
                                color: '#ef4444',
                                borderRadius: 8,
                                padding: '6px 12px',
                                cursor: 'pointer',
                                fontSize: 12,
                                fontWeight: 600
                              }}
                            >
                              Delete
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

      </div>

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        * { box-sizing: border-box; }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #0a0a14; }
        ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 3px; }
        select option { background: #1e293b; color: #f1f5f9; }
      `}</style>
    </div>
  );
}
