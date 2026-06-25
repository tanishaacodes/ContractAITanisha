/**
 * RiskTrendChart
 * Time-series risk visualisation for a single contract.
 * Pulls from /api/maps/timeline/<contractId>/ which returns
 * ContractRiskHistory records keyed by version number.
 *
 * If the history table is empty (contract never versioned through
 * the maps pipeline), renders a single-point "current" marker
 * using the overall risk score passed in via the `currentRisk` prop.
 */
import React, { useEffect, useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import axios from 'axios';

const API = import.meta.env.VITE_API_URL || (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));

const RiskTrendChart = ({ contractId, currentRisk }) => {
  const [history, setHistory]   = useState([]);
  const [loading, setLoading]   = useState(true);
  const [failed,  setFailed]    = useState(false);

  useEffect(() => {
    let cancelled = false;
    const fetch = async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await axios.get(
          `${API}/api/maps/timeline/${contractId}/`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        if (!cancelled) {
          setHistory(res.data);
          setFailed(false);
        }
      } catch {
        if (!cancelled) setFailed(true);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    fetch();
    return () => { cancelled = true; };
  }, [contractId]);

  /* ── derive the dataset the chart will render ── */
  const chartData = history.length > 0
    ? history.map(h => ({
        version:         h.version,
        'Overall Risk':  h.overall_risk,
        'IP Risk':       h.ip_risk,
        'Liability':     h.liability_risk,
        'Geography':     h.geography_risk,
      }))
    : currentRisk != null
      ? [{ version: 'Now', 'Overall Risk': currentRisk }]
      : [];

  /* ── loading / empty states ── */
  if (loading) {
    return (
      <div className="flex items-center justify-center h-40">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400" />
      </div>
    );
  }

  if (chartData.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-40 text-slate-500 text-sm">
        <p>No risk-history snapshots recorded yet.</p>
        <p className="text-xs mt-1">Snapshots are captured each time a contract version is analysed.</p>
      </div>
    );
  }

  /* ── custom dark tooltip ── */
  const DarkTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    return (
      <div className="rounded-lg p-3 shadow-lg" style={{
        background: 'rgba(15,23,42,0.95)',
        border: '1px solid rgba(51,65,85,0.5)',
      }}>
        <p className="text-xs text-slate-400 mb-1 font-bold tracking-wide">
          {history.length > 0 ? `Version ${label}` : 'Current'}
        </p>
        {payload.map((entry, i) => (
          <p key={i} className="text-xs" style={{ color: entry.color }}>
            {entry.name}: <span className="font-bold">{Number(entry.value).toFixed(1)}</span>
          </p>
        ))}
      </div>
    );
  };

  const showDimensions = history.length > 0;   // only when we have real multi-version data

  return (
    <div style={{ width: '100%', height: 200 }}>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={chartData} margin={{ top: 8, right: 16, bottom: 4, left: -10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(51,65,85,0.35)" />
          <XAxis
            dataKey="version"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={{ stroke: 'rgba(51,65,85,0.5)' }}
            tickLine={false}
            label={{ value: 'Version', position: 'insideBottomRight', offset: -4, style: { fill: '#64748b', fontSize: 10 } }}
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={{ stroke: 'rgba(51,65,85,0.5)' }}
            tickLine={false}
          />
          <Tooltip content={<DarkTooltip />} />
          {showDimensions && (
            <Legend
              wrapperStyle={{ fontSize: 11, paddingTop: 4 }}
              iconType="circle"
              iconSize={8}
            />
          )}

          <Line type="monotone" dataKey="Overall Risk"  stroke="#f43f5e" strokeWidth={2.5} dot={{ r: 3 }} activeDot={{ r: 5 }} />
          {showDimensions && <Line type="monotone" dataKey="IP Risk"      stroke="#a78bfa" strokeWidth={1.5} strokeDasharray="4 2" dot={false} />}
          {showDimensions && <Line type="monotone" dataKey="Liability"    stroke="#fb923c" strokeWidth={1.5} strokeDasharray="4 2" dot={false} />}
          {showDimensions && <Line type="monotone" dataKey="Geography"    stroke="#22d3ee" strokeWidth={1.5} strokeDasharray="4 2" dot={false} />}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default RiskTrendChart;
