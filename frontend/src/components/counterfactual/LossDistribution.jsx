import { ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, ReferenceArea } from 'recharts';
import { BarChart3 } from 'lucide-react';

const LossDistribution = ({ data }) => {
  // Sort loss distribution by loss amount (ascending)
  const sortedDist = [...data.loss_distribution].sort((a, b) => a.loss - b.loss);

  // Calculate cumulative distribution and convert to exceedance
  let cumSum = 0;
  const exceedanceData = sortedDist.map((point, index) => {
    cumSum += point.prob;
    const percentile = cumSum * 100; // 0% to 100%
    const exceedance = 100 - percentile; // 100% to 0%

    return {
      loss: point.loss,
      lossMillion: point.loss / 1000000,
      percentile: percentile,
      exceedance: exceedance,
      exceedanceLabel: `${Math.max(0, exceedance).toFixed(0)}%`,
      lossFormatted: `₹${(point.loss / 1000000).toFixed(1)}M`
    };
  }); // Keep original order: low loss (high exceedance) → high loss (low exceedance)

  // Calculate percentile values
  const findLossAtPercentile = (pct) => {
    const target = pct;
    for (let i = 0; i < sortedDist.length; i++) {
      let sum = 0;
      for (let j = 0; j <= i; j++) sum += sortedDist[j].prob;
      if (sum * 100 >= target) return sortedDist[i].loss / 1000000;
    }
    return (sortedDist[sortedDist.length - 1]?.loss || 0) / 1000000;
  };

  const p50val = findLossAtPercentile(50);
  const p75val = findLossAtPercentile(75);
  const p90val = findLossAtPercentile(90);
  const p95val = findLossAtPercentile(95);
  const p99val = data.percentile_99_inr / 1000000;
  const meanVal = data.avg_loss_inr / 1000000;
  const maxVal = Math.max(...sortedDist.map(d => d.loss)) / 1000000;

  const PERCENTILES = [
    { label: 'Typical Case (P50)', val: p50val, color: '#68BC00', desc: '50/50 chance — half of scenarios are worse' },
    { label: 'Elevated Risk (P75)', val: p75val, color: '#F1C40F', desc: '1-in-4 chance — 25% of scenarios are worse' },
    { label: 'Bad Case (P90)', val: p90val, color: '#F79767', desc: '1-in-10 chance — 10% of scenarios are worse' },
    { label: 'Stress Test (P95)', val: p95val, color: '#F16667', desc: '1-in-20 chance — reserve buffer for planning' },
    { label: 'Catastrophic (P99)', val: p99val, color: '#9063CD', desc: '1-in-100 chance — black swan event' },
  ];

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;
    const d = payload[0]?.payload;
    return (
      <div style={{ background: '#1e293b', border: '1px solid #a855f7', borderRadius: 10, padding: '10px 14px', fontSize: 11 }}>
        <div style={{ color: '#94a3b8', marginBottom: 4 }}>Exceedance Probability: <b style={{ color: '#fff' }}>{d?.exceedanceLabel}</b></div>
        <div style={{ color: '#94a3b8' }}>Loss Amount: <b style={{ color: '#a855f7' }}>{d?.lossFormatted}</b></div>
        <div style={{ marginTop: 4, color: '#64748b', fontSize: 10 }}>
          <b style={{ color: '#fff' }}>{d?.exceedanceLabel}</b> of scenarios will EXCEED this loss
        </div>
      </div>
    );
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-purple-400" />
          <h3 className="text-sm font-semibold text-white">Loss Exceedance Curve</h3>
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

      {/* Exceedance Curve Chart */}
      {exceedanceData && exceedanceData.length > 0 ? (
        <ResponsiveContainer width="100%" height={350}>
          <ComposedChart data={exceedanceData} margin={{ top: 15, right: 20, left: 10, bottom: 10 }}>
            <defs>
              <linearGradient id="lossExceedGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#a855f7" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#a855f7" stopOpacity={0.05} />
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

            {/* Reference lines for key percentiles */}
            <ReferenceLine y={p50val} stroke="#68BC00" strokeDasharray="4 3" strokeWidth={1.5}
              label={{ value: 'Typical (P50)', position: 'right', fill: '#68BC00', fontSize: 9 }} />
            <ReferenceLine y={p90val} stroke="#F79767" strokeDasharray="4 3" strokeWidth={1.5}
              label={{ value: 'Bad Case (P90)', position: 'right', fill: '#F79767', fontSize: 9 }} />
            <ReferenceLine y={p95val} stroke="#F16667" strokeDasharray="4 3" strokeWidth={1.5}
              label={{ value: 'Stress Test (P95)', position: 'right', fill: '#F16667', fontSize: 9 }} />

            {/* Mean reference line */}
            <ReferenceLine y={meanVal} stroke="#fff" strokeDasharray="6 3" strokeWidth={1.5} strokeOpacity={0.5}
              label={{ value: `Mean ₹${meanVal.toFixed(1)}M`, position: 'insideTopRight', fill: '#e5e7eb', fontSize: 9 }} />

            {/* Area fill */}
            <Area type="monotone" dataKey="lossMillion" stroke="none" fill="url(#lossExceedGrad)" dot={false} legendType="none" isAnimationActive={false} />

            {/* Main line */}
            <Line type="monotone" dataKey="lossMillion" stroke="#a855f7" strokeWidth={3} dot={false} isAnimationActive={false} />
          </ComposedChart>
        </ResponsiveContainer>
      ) : (
        <div className="flex items-center justify-center h-[350px] bg-slate-800/30 rounded-lg">
          <p className="text-slate-500 text-sm">No distribution data available</p>
        </div>
      )}

      {/* Percentile Cards */}
      <div className="mt-6 grid grid-cols-5 gap-2">
        {PERCENTILES.map(p => (
          <div key={p.label} className="bg-slate-800/60 border border-slate-700 rounded-lg p-3 text-center hover:border-purple-500/50 transition">
            <div className="text-xs font-bold mb-1" style={{ color: p.color }}>{p.label}</div>
            <div className="text-sm font-black text-white">₹{p.val.toFixed(1)}M</div>
            <div className="text-slate-500 text-xs mt-1 leading-tight">{p.desc}</div>
            <div className="mt-2 bg-slate-700 rounded-full h-1">
              <div className="h-1 rounded-full" style={{ width: `${Math.round((p.val / maxVal) * 100)}%`, background: p.color }} />
            </div>
          </div>
        ))}
      </div>

      {/* Statistical Summary */}
      <div className="mt-6 bg-slate-800/60 border border-slate-700 rounded-lg p-4 grid grid-cols-4 gap-4">
        {[
          { label: 'Expected Loss', val: `₹${meanVal.toFixed(1)}M`, color: '#a855f7', sub: 'mean of all iterations' },
          { label: 'Risk Spread (Catastrophic to Typical)', val: `₹${(p99val - p50val).toFixed(1)}M`, color: '#F16667', sub: 'spread of uncertainty' },
          { label: 'Prob > Expected', val: `~50%`, color: '#F79767', sub: 'by definition of mean' },
          { label: 'Risk Change', val: `${data.risk_delta > 0 ? '+' : ''}${data.risk_delta_percentage}%`, color: data.risk_delta < 0 ? '#68BC00' : data.risk_delta > 0 ? '#F16667' : '#64748b', sub: 'from baseline scenario' },
        ].map((s, i) => (
          <div key={i}>
            <div className="text-slate-500 text-xs mb-1">{s.label}</div>
            <div className="text-lg font-black" style={{ color: s.color }}>{s.val}</div>
            <div className="text-slate-600 text-xs mt-0.5">{s.sub}</div>
          </div>
        ))}
      </div>

      {/* Interpretation */}
      <div className="mt-4 p-3 bg-slate-800/50 border border-slate-700 rounded-lg">
        <p className="text-xs text-slate-400">
          <span className="font-semibold text-slate-300">Interpretation:</span> This exceedance curve shows the probability of EXCEEDING each loss level across 1,000 Monte Carlo simulations. Higher exceedance percentages indicate greater certainty, while lower percentages represent tail risk scenarios.
        </p>
      </div>
    </div>
  );
};

export default LossDistribution;
