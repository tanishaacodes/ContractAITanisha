import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, BarChart3, Loader2, AlertTriangle, TrendingUp, RefreshCw } from 'lucide-react';
import ExposureCard from '../../components/enterprise/metrics/ExposureCard';
import ContractSelector from '../../components/enterprise/ContractSelector';
import enterpriseRiskService from '../../services/enterpriseRiskService';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  ReferenceLine,
  ComposedChart,
  ReferenceArea
} from 'recharts';

export default function MonteCarloSimulation() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const contractId = searchParams.get('contractId') || '';

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [simulating, setSimulating] = useState(false);
  const [simulationData, setSimulationData] = useState(null);
  const [iterations, setIterations] = useState(30000);
  const [resolvedContractId, setResolvedContractId] = useState('');

  const handleContractSelect = (id) => {
    setSimulationData(null);
    if (id) {
      setSearchParams({ contractId: id });
    } else {
      setSearchParams({});
    }
  };

  useEffect(() => {
    runSimulation();
  }, [contractId]);

  const runSimulation = async () => {
    try {
      setSimulating(true);
      setError('');

      let targetContractId = contractId;

      // If no real contractId, fetch first available contract from portfolio
      if (!contractId) {
        const portfolio = await enterpriseRiskService.getPortfolioContracts();
        if (portfolio.contracts && portfolio.contracts.length > 0) {
          targetContractId = portfolio.contracts[0].id;
        } else {
          throw new Error('No contracts found. Please upload a contract first to run Monte Carlo simulation.');
        }
      }

      setResolvedContractId(targetContractId);
      const backendData = await enterpriseRiskService.runMonteCarloSimulation(targetContractId, iterations);
      setSimulationData(backendData);
    } catch (err) {
      setError(err.message || 'Failed to run Monte Carlo simulation');
      console.error('Simulation error:', err);
    } finally {
      setSimulating(false);
    }
  };

  if (!simulationData || simulating) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="text-center">
          <Loader2 className="w-16 h-16 text-violet-400 animate-spin mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">Running Monte Carlo Simulation</h2>
          <p className="text-slate-400">Simulating {iterations.toLocaleString()} scenarios...</p>
          <div className="mt-6 w-64 mx-auto">
            <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-violet-500 to-purple-600 animate-pulse" style={{ width: '100%' }} />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="text-center max-w-md">
          <AlertTriangle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">Simulation Error</h2>
          <p className="text-slate-400 mb-6">{error}</p>
          <button
            onClick={runSimulation}
            className="px-6 py-3 bg-violet-500 hover:bg-violet-600 text-white rounded-xl font-semibold transition-all"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/enterprise/risk-dashboard')}
            className="p-3 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-violet-500/50 transition-all"
          >
            <ArrowLeft className="w-5 h-5 text-slate-400" />
          </button>
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-gradient-to-br from-violet-500/20 to-purple-500/20 border border-violet-500/30">
              <BarChart3 className="w-8 h-8 text-violet-400" />
            </div>
            <div>
              <h1 className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white via-violet-200 to-purple-300">
                Monte Carlo VaR Simulation
              </h1>
              <p className="text-slate-400 text-sm">
                {simulationData?.iterations.toLocaleString()} Iterations | Value-at-Risk Analysis
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <ContractSelector
            selectedContractId={contractId}
            onSelect={handleContractSelect}
            accentColor="violet"
          />
          <button
            onClick={runSimulation}
            disabled={simulating}
            className="px-6 py-3 bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white rounded-xl font-semibold transition-all flex items-center gap-2 disabled:opacity-50"
          >
            {simulating ? <Loader2 className="w-5 h-5 animate-spin" /> : <RefreshCw className="w-5 h-5" />}
            Re-run Simulation
          </button>
        </div>
      </div>

      {/* Insurance Offset Banner */}
      {simulationData.risk_parameters?.insurance_coverage > 0 && (
        <div className="mb-6 p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-emerald-500/20">
              <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <div className="flex-1">
              <p className="text-emerald-300 font-semibold">✓ Insurance Coverage Active</p>
              <p className="text-emerald-400/70 text-sm">
                Base Exposure: ₹{(simulationData.risk_parameters.base_exposure / 1000000).toFixed(1)}M
                {' → '}
                Net Exposure: ₹{(simulationData.risk_parameters.net_exposure / 1000000).toFixed(1)}M
                (Coverage: ₹{(simulationData.risk_parameters.insurance_coverage / 1000000).toFixed(1)}M)
              </p>
            </div>
          </div>
        </div>
      )}

      {/* VaR Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <ExposureCard
          title="Mean Exposure"
          value={`₹${(simulationData.mean / 1000000).toFixed(1)}M`}
          subtitle={simulationData.risk_parameters?.insurance_coverage > 0 ? "After insurance" : "Expected value"}
          icon={TrendingUp}
          color="cyan"
        />

        <ExposureCard
          title="Stress Test (VaR 95%)"
          value={`₹${(simulationData.var_95 / 1000000).toFixed(1)}M`}
          subtitle="1-in-20 stress scenario"
          icon={AlertTriangle}
          color="amber"
        />

        <ExposureCard
          title="Catastrophic (VaR 99%)"
          value={`₹${(simulationData.var_99 / 1000000).toFixed(1)}M`}
          subtitle="1-in-100 worst case"
          icon={AlertTriangle}
          color="red"
        />

        <ExposureCard
          title="CVaR (95%)"
          value={`₹${(simulationData.cvar_95 / 1000000).toFixed(1)}M`}
          subtitle="Conditional VaR"
          icon={BarChart3}
          color="violet"
        />
      </div>

      {/* Exceedance Curve */}
      {(() => {
        // Extract percentile values in millions
        const minVal = simulationData.min / 1000000;
        const p50val = simulationData.median / 1000000;
        const p90val = simulationData.p90 / 1000000;
        const p95val = simulationData.p95 / 1000000;
        const p99val = simulationData.p99 / 1000000;
        const meanVal = simulationData.mean / 1000000;
        const maxVal = simulationData.max / 1000000;

        // Calculate P25 and P75 by interpolation
        const p25val = minVal + (p50val - minVal) * 0.5;
        const p75val = p50val + (p90val - p50val) * 0.625;

        // Get base exposure for percentage calculations
        const baseExposure = simulationData.risk_parameters?.base_exposure || simulationData.mean;

        // Create exceedance curve data (101 points from P0 to P100)
        const exceedanceData = Array.from({ length: 101 }, (_, i) => {
          const percentile = i; // 0, 1, 2, ..., 100
          const exceedance = 100 - percentile; // 100%, 99%, ..., 0%

          // Interpolate exposure at this percentile using cubic spline-like interpolation
          let exposure;
          if (percentile === 0) {
            exposure = minVal;
          } else if (percentile <= 25) {
            exposure = minVal + (p25val - minVal) * (percentile / 25);
          } else if (percentile <= 50) {
            exposure = p25val + (p50val - p25val) * ((percentile - 25) / 25);
          } else if (percentile <= 75) {
            exposure = p50val + (p75val - p50val) * ((percentile - 50) / 25);
          } else if (percentile <= 90) {
            exposure = p75val + (p90val - p75val) * ((percentile - 75) / 15);
          } else if (percentile <= 95) {
            exposure = p90val + (p95val - p90val) * ((percentile - 90) / 5);
          } else if (percentile <= 99) {
            exposure = p95val + (p99val - p95val) * ((percentile - 95) / 4);
          } else {
            exposure = p99val + (maxVal - p99val) * ((percentile - 99) / 1);
          }

          // Show labels only for major ticks (every 10%)
          const showLabel = percentile % 10 === 0;

          return {
            percentile: percentile,
            exceedance: exceedance,
            exceedanceLabel: showLabel ? `${exceedance}%` : '',
            exceedanceFull: `${exceedance}%`,
            exposure: Math.max(0, exposure), // Ensure non-negative
            zone: i < 50 ? 'safe' : i < 75 ? 'moderate' : i < 90 ? 'high' : 'critical',
            barColor: i < 50 ? '#68BC00' : i < 75 ? '#F1C40F' : i < 90 ? '#F79767' : '#F16667',
          };
        });

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
            <div style={{ background: '#1e293b', border: '1px solid #8b5cf6', borderRadius: 10, padding: '10px 14px', fontSize: 11 }}>
              <div style={{ color: '#94a3b8', marginBottom: 4 }}>Exceedance Probability: <b style={{ color: '#fff' }}>{d?.exceedanceFull}</b></div>
              <div style={{ color: '#94a3b8' }}>Exposure at P{d?.percentile}: <b style={{ color: '#a78bfa' }}>₹{(d?.exposure || 0).toFixed(1)}M</b></div>
              <div style={{ marginTop: 4, color: '#64748b', fontSize: 10 }}>
                <b style={{ color: '#fff' }}>{d?.exceedanceFull}</b> of scenarios will EXCEED this exposure
              </div>
            </div>
          );
        };

        return (
          <div className="space-y-6 mb-8">
            {/* Main Exceedance Chart */}
            <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl border border-violet-500/20 rounded-2xl p-6 shadow-[0_0_30px_rgba(139,92,246,0.15)]">
              <div className="flex items-start justify-between mb-1">
                <div>
                  <h3 className="text-xl font-bold text-white">VaR Exceedance Curve</h3>
                  <p className="text-slate-500 text-xs mt-0.5">{simulationData.iterations.toLocaleString()} iterations · probability of EXCEEDING each exposure level</p>
                </div>
                <div className="flex gap-3 text-xs">
                  {[['#F16667', 'Catastrophic (1-in-20+)'], ['#F79767', 'Bad Case (1-in-4 to 1-in-20)'], ['#F1C40F', 'Elevated (1-in-2 to 1-in-4)'], ['#68BC00', 'Typical (<50%)']].map(([c, l]) => (
                    <div key={l} className="flex items-center gap-1">
                      <div className="w-2.5 h-2.5 rounded-sm" style={{ background: c }} />
                      <span className="text-slate-400">{l}</span>
                    </div>
                  ))}
                </div>
              </div>

              <ResponsiveContainer width="100%" height={400}>
                <ComposedChart data={exceedanceData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                  <defs>
                    <linearGradient id="mcSafeGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0.05} />
                    </linearGradient>
                  </defs>

                  {/* Risk zone shading */}
                  <ReferenceArea x1="100%" x2="50%" fill="#68BC00" fillOpacity={0.04} />
                  <ReferenceArea x1="50%" x2="25%" fill="#F1C40F" fillOpacity={0.04} />
                  <ReferenceArea x1="25%" x2="10%" fill="#F79767" fillOpacity={0.05} />
                  <ReferenceArea x1="10%" x2="0%" fill="#F16667" fillOpacity={0.07} />

                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                  <XAxis
                    dataKey="exceedanceLabel"
                    tick={{ fill: '#94a3b8', fontSize: 11 }}
                    axisLine={{ stroke: '#475569' }}
                    tickLine={false}
                    interval={0}
                    label={{ value: 'Exceedance Probability', position: 'insideBottom', offset: -10, fill: '#cbd5e1', fontSize: 11 }}
                    reversed
                  />
                  <YAxis
                    domain={[0, 'auto']}
                    tick={{ fill: '#94a3b8', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={v => `₹${v.toFixed(0)}M`}
                    label={{ value: 'Exposure Amount', angle: -90, position: 'insideLeft', fill: '#cbd5e1', fontSize: 11 }}
                  />
                  <Tooltip content={<CustomTooltip />} />

                  {/* Reference lines for key percentiles */}
                  <ReferenceLine x="50%" stroke="#68BC00" strokeDasharray="4 3" strokeWidth={1.5}
                    label={{ value: 'Typical (50/50)', position: 'top', fill: '#68BC00', fontSize: 9 }} />
                  <ReferenceLine x="25%" stroke="#F1C40F" strokeDasharray="4 3" strokeWidth={1.5}
                    label={{ value: 'Elevated (1-in-4)', position: 'top', fill: '#F1C40F', fontSize: 9 }} />
                  <ReferenceLine x="5%" stroke="#F16667" strokeDasharray="4 3" strokeWidth={1.5}
                    label={{ value: 'Stress Test (1-in-20)', position: 'top', fill: '#F16667', fontSize: 9 }} />

                  {/* Mean reference line */}
                  <ReferenceLine y={meanVal} stroke="#fff" strokeDasharray="6 3" strokeWidth={1.5} strokeOpacity={0.5}
                    label={{ value: `Mean ₹${meanVal.toFixed(1)}M`, position: 'insideTopRight', fill: '#e5e7eb', fontSize: 9 }} />

                  {/* Area fill */}
                  <Area type="monotone" dataKey="exposure" stroke="none" fill="url(#mcSafeGrad)" dot={false} legendType="none" isAnimationActive={false} />

                  {/* Main line */}
                  <Line type="monotone" dataKey="exposure" stroke="#a78bfa" strokeWidth={3} dot={false} isAnimationActive={false} />

                  {/* Dots at key percentiles */}
                  <Line type="monotone" dataKey="exposure" strokeWidth={0} dot={(props) => {
                    const keyIdx = [50, 75, 90, 95, 99]; // P50, P75, P90, P95, P99
                    const colors = ['#68BC00', '#F1C40F', '#F79767', '#F16667', '#9063CD'];
                    const pos = keyIdx.indexOf(props.index);
                    if (pos === -1) return null;
                    return <circle key={props.index} cx={props.cx} cy={props.cy} r={6} fill={colors[pos]} stroke="#1e293b" strokeWidth={2} />;
                  }} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            {/* Percentile Cards */}
            <div className="grid grid-cols-5 gap-3">
              {PERCENTILES.map(p => (
                <div key={p.label} className="bg-slate-800/60 border border-slate-700 rounded-xl p-4 text-center hover:border-violet-500/50 transition">
                  <div className="text-xs font-bold mb-1" style={{ color: p.color }}>{p.label}</div>
                  <div className="text-lg font-black text-white">₹{p.val.toFixed(1)}M</div>
                  <div className="text-slate-500 text-xs mt-1 leading-relaxed">{p.desc}</div>
                  <div className="mt-2 bg-slate-700 rounded-full h-1">
                    <div className="h-1 rounded-full" style={{ width: `${Math.round((p.val / maxVal) * 100)}%`, background: p.color }} />
                  </div>
                </div>
              ))}
            </div>

            {/* Stats Row */}
            <div className="bg-slate-800/60 border border-slate-700 rounded-xl p-5 grid grid-cols-4 gap-6">
              {[
                { label: 'Expected Exposure', val: `₹${meanVal.toFixed(1)}M`, color: '#8b5cf6', sub: 'mean of all iterations' },
                { label: 'Risk Spread (Catastrophic to Typical)', val: `₹${(p99val - p50val).toFixed(1)}M`, color: '#F16667', sub: 'spread of uncertainty' },
                { label: 'Prob > Expected', val: `~50%`, color: '#F79767', sub: 'by definition of mean' },
                { label: '% of Base Exposure', val: `${Math.min(100, Math.round((meanVal * 1000000 / baseExposure) * 100))}%`, color: '#68BC00', sub: `of ₹${(baseExposure / 1000000).toFixed(1)}M base` },
              ].map((s, i) => (
                <div key={i}>
                  <div className="text-slate-500 text-xs mb-1">{s.label}</div>
                  <div className="text-xl font-black" style={{ color: s.color }}>{s.val}</div>
                  <div className="text-slate-600 text-xs mt-0.5">{s.sub}</div>
                </div>
              ))}
            </div>
          </div>
        );
      })()}

      {/* Convergence Chart */}
      <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl border border-emerald-500/20 rounded-2xl p-6 shadow-[0_0_30px_rgba(16,185,129,0.15)]">
        <h3 className="text-xl font-bold text-white mb-4">Simulation Convergence</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={simulationData.convergence}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="iteration"
              stroke="#94a3b8"
              label={{ value: 'Iteration', position: 'insideBottom', offset: -5, fill: '#94a3b8' }}
            />
            <YAxis
              stroke="#94a3b8"
              label={{ value: 'Mean Exposure (₹)', angle: -90, position: 'insideLeft', fill: '#94a3b8' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #10b981',
                borderRadius: '0.5rem'
              }}
            />
            <Line type="monotone" dataKey="mean" stroke="#10b981" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
