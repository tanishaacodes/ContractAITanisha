import { ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, ReferenceArea } from 'recharts';
import { Activity, AlertCircle } from 'lucide-react';

const TailRiskChart = ({ data }) => {
  // Sort by loss amount (ascending)
  const sortedData = [...data].sort((a, b) => a.loss - b.loss);

  // Normalize probabilities to ensure they sum to 100
  const totalProb = sortedData.reduce((sum, point) => sum + parseFloat(point.prob_pct), 0);
  const normalizationFactor = totalProb > 0 ? 100 / totalProb : 1;

  // Build exceedance curve: for each loss level, calculate probability of exceeding it
  const exceedanceData = sortedData.map((point, index) => {
    const lossMidpoint = (point.loss + point.loss_max) / 2;
    const normalizedProb = parseFloat(point.prob_pct) * normalizationFactor;

    // Exceedance = sum of probabilities for all bins ABOVE this one
    let exceedance = 0;
    for (let j = index + 1; j < sortedData.length; j++) {
      exceedance += parseFloat(sortedData[j].prob_pct) * normalizationFactor;
    }

    // Percentile = 100 - exceedance
    const percentile = 100 - exceedance;

    return {
      loss: point.loss,
      lossMax: point.loss_max,
      lossMidpoint: lossMidpoint,
      lossMillion: lossMidpoint / 1_000_000,
      probability: normalizedProb,
      percentile: percentile,
      exceedance: exceedance,
      exceedanceLabel: `${exceedance.toFixed(0)}%`,
      lossFormatted: `₹${(lossMidpoint / 1_000_000).toFixed(1)}M`,
      lossRange: `₹${(point.loss / 1_000_000).toFixed(1)}M - ₹${(point.loss_max / 1_000_000).toFixed(1)}M`
    };
  }).reverse(); // Reverse so chart plots correctly: high loss (low exceedance) to low loss (high exceedance)

  // Calculate percentile values with interpolation for better accuracy
  const findLossAtPercentile = (pct) => {
    if (!exceedanceData.length) return 0;

    // After reversing, array goes from high loss (low percentile) to low loss (high percentile)
    // Search from end to start to find where percentile crosses pct
    for (let i = exceedanceData.length - 1; i >= 0; i--) {
      if (exceedanceData[i].percentile >= pct) {
        // Found the bin - use linear interpolation if possible
        if (i < exceedanceData.length - 1) {
          const curr = exceedanceData[i];
          const next = exceedanceData[i + 1];
          const ratio = (pct - curr.percentile) / (next.percentile - curr.percentile);
          if (ratio >= 0 && ratio <= 1) {
            return curr.lossMillion + ratio * (next.lossMillion - curr.lossMillion);
          }
        }
        return exceedanceData[i].lossMillion;
      }
    }
    // If pct is very low, return the highest loss
    return exceedanceData[0]?.lossMillion || 0;
  };

  const p50val = findLossAtPercentile(50);
  const p75val = findLossAtPercentile(75);
  const p90val = findLossAtPercentile(90);
  const p95val = findLossAtPercentile(95);
  const p99val = findLossAtPercentile(99);
  const minVal = exceedanceData[0]?.lossMillion || 0;
  const maxVal = exceedanceData[exceedanceData.length - 1]?.lossMillion || 0;

  const PERCENTILES = [
    { label: 'Typical Case (P50)', val: p50val, color: '#68BC00', desc: '50/50 chance' },
    { label: 'Elevated Risk (P75)', val: p75val, color: '#F1C40F', desc: '1-in-4 chance' },
    { label: 'Bad Case (P90)', val: p90val, color: '#F79767', desc: '1-in-10 chance' },
    { label: 'Stress Test (P95)', val: p95val, color: '#F16667', desc: '1-in-20 chance' },
    { label: 'Catastrophic (P99)', val: p99val, color: '#9063CD', desc: '1-in-100 chance' },
  ];

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;
    const d = payload[0]?.payload;
    return (
      <div style={{ background: '#1e293b', border: '1px solid #ef4444', borderRadius: 10, padding: '10px 14px', fontSize: 11 }}>
        <div style={{ color: '#94a3b8', marginBottom: 4 }}>Exceedance: <b style={{ color: '#fff' }}>{d?.exceedanceLabel}</b></div>
        <div style={{ color: '#94a3b8' }}>Loss: <b style={{ color: '#ef4444' }}>{d?.lossFormatted}</b></div>
        <div style={{ color: '#94a3b8', fontSize: 10, marginTop: 2 }}>Range: {d?.lossRange}</div>
        <div style={{ marginTop: 4, color: '#64748b', fontSize: 10 }}>
          <b style={{ color: '#fff' }}>{d?.exceedanceLabel}</b> of scenarios EXCEED this loss
        </div>
      </div>
    );
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-red-400" />
          <h3 className="text-sm font-semibold text-white">Tail Risk Exceedance Curve</h3>
        </div>
        <div className="flex gap-3 text-xs">
          {[['#F16667', 'Catastrophic'], ['#F79767', 'Bad Case'], ['#F1C40F', 'Elevated'], ['#68BC00', 'Typical']].map(([c, l]) => (
            <div key={l} className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-sm" style={{ background: c }} />
              <span className="text-slate-500">{l}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Exceedance Chart */}
      {exceedanceData && exceedanceData.length > 0 ? (
        <ResponsiveContainer width="100%" height={350}>
          <ComposedChart data={exceedanceData} margin={{ top: 15, right: 20, left: 10, bottom: 10 }}>
            <defs>
              <linearGradient id="tailExceedGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#ef4444" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#ef4444" stopOpacity={0.05} />
              </linearGradient>
            </defs>

            {/* Risk zone shading */}
            <ReferenceArea y1={0} y2={p50val} fill="#68BC00" fillOpacity={0.04} />
            <ReferenceArea y1={p50val} y2={p75val} fill="#F1C40F" fillOpacity={0.04} />
            <ReferenceArea y1={p75val} y2={p95val} fill="#F79767" fillOpacity={0.05} />
            <ReferenceArea y1={p95val} y2={maxVal * 1.1} fill="#F16667" fillOpacity={0.07} />

            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
            <XAxis
              dataKey="exceedanceLabel"
              tick={{ fill: '#94a3b8', fontSize: 10 }}
              axisLine={{ stroke: '#475569' }}
              tickLine={false}
              label={{ value: 'Exceedance Probability', position: 'insideBottom', offset: -5, fill: '#cbd5e1', fontSize: 10 }}
              reversed
            />
            <YAxis
              domain={[0, 'auto']}
              tick={{ fill: '#94a3b8', fontSize: 10 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={v => `₹${v.toFixed(0)}M`}
              label={{ value: 'Loss Amount', angle: -90, position: 'insideLeft', fill: '#cbd5e1', fontSize: 10 }}
            />
            <Tooltip content={<CustomTooltip />} />

            {/* Reference lines */}
            <ReferenceLine y={p50val} stroke="#68BC00" strokeDasharray="4 3" strokeWidth={1.5}
              label={{ value: 'Typical (P50)', position: 'right', fill: '#68BC00', fontSize: 9 }} />
            <ReferenceLine y={p90val} stroke="#F79767" strokeDasharray="4 3" strokeWidth={1.5}
              label={{ value: 'Bad Case (P90)', position: 'right', fill: '#F79767', fontSize: 9 }} />
            <ReferenceLine y={p95val} stroke="#F16667" strokeDasharray="4 3" strokeWidth={1.5}
              label={{ value: 'Stress Test (P95)', position: 'right', fill: '#F16667', fontSize: 9 }} />

            {/* Area fill */}
            <Area type="monotone" dataKey="lossMillion" stroke="none" fill="url(#tailExceedGrad)" dot={false} legendType="none" isAnimationActive={false} />

            {/* Main line */}
            <Line type="monotone" dataKey="lossMillion" stroke="#ef4444" strokeWidth={3} dot={false} isAnimationActive={false} />
          </ComposedChart>
        </ResponsiveContainer>
      ) : (
        <div className="flex items-center justify-center h-[350px] bg-slate-800/30 rounded-lg">
          <p className="text-slate-500 text-sm">No tail risk data available</p>
        </div>
      )}

      {/* Percentile Cards */}
      <div className="mt-6 grid grid-cols-5 gap-2">
        {PERCENTILES.map(p => (
          <div key={p.label} className="bg-slate-800/60 border border-slate-700 rounded-lg p-3 text-center hover:border-red-500/50 transition">
            <div className="text-xs font-bold mb-1" style={{ color: p.color }}>{p.label}</div>
            <div className="text-sm font-black text-white">₹{p.val.toFixed(1)}M</div>
            <div className="text-slate-500 text-xs mt-1">{p.desc}</div>
            <div className="mt-2 bg-slate-700 rounded-full h-1">
              <div className="h-1 rounded-full" style={{ width: `${Math.round((p.val / maxVal) * 100)}%`, background: p.color }} />
            </div>
          </div>
        ))}
      </div>

      {/* Stats Panel */}
      <div className="mt-4 bg-slate-800/60 border border-slate-700 rounded-lg p-4 grid grid-cols-3 gap-4">
        {[
          { label: 'Tail Risk Spread', val: `₹${(p99val - p50val).toFixed(1)}M`, color: '#F16667', sub: 'P99 to P50 range' },
          { label: 'Stress Test (P95)', val: `₹${p95val.toFixed(1)}M`, color: '#F79767', sub: '1-in-20 worst case' },
          { label: 'Catastrophic (P99)', val: `₹${p99val.toFixed(1)}M`, color: '#9063CD', sub: '1-in-100 black swan' },
        ].map((s, i) => (
          <div key={i}>
            <div className="text-slate-500 text-xs mb-1">{s.label}</div>
            <div className="text-lg font-black" style={{ color: s.color }}>{s.val}</div>
            <div className="text-slate-600 text-xs mt-0.5">{s.sub}</div>
          </div>
        ))}
      </div>

      {/* Info Panel */}
      <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="p-3 bg-red-900/20 border border-red-500/30 rounded-lg">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-2.5 h-2.5 rounded-full bg-red-500"></div>
            <p className="text-xs text-slate-300 font-semibold">Tail Events</p>
          </div>
          <p className="text-xs text-slate-400">
            Low exceedance probabilities represent extreme loss scenarios with high impact.
          </p>
        </div>

        <div className="p-3 bg-orange-900/20 border border-orange-500/30 rounded-lg">
          <div className="flex items-center gap-2 mb-1">
            <AlertCircle className="w-3 h-3 text-orange-400" />
            <p className="text-xs text-slate-300 font-semibold">Stress Test (P95)</p>
          </div>
          <p className="text-xs text-slate-400">
            5% chance of exceeding this value — reserve buffer for planning and capital allocation.
          </p>
        </div>

        <div className="p-3 bg-amber-900/20 border border-amber-500/30 rounded-lg">
          <div className="flex items-center gap-2 mb-1">
            <Activity className="w-3 h-3 text-amber-400" />
            <p className="text-xs text-slate-300 font-semibold">Risk Modeling</p>
          </div>
          <p className="text-xs text-slate-400">
            2,000 Monte Carlo simulations capture realistic loss patterns with long tail distributions.
          </p>
        </div>
      </div>
    </div>
  );
};

export default TailRiskChart;
