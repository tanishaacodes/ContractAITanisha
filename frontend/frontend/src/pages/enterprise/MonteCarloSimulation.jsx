import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, BarChart3, Loader2, AlertTriangle, TrendingUp, Play, RefreshCw } from 'lucide-react';
import ExposureCard from '../../components/enterprise/metrics/ExposureCard';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  ReferenceLine
} from 'recharts';

export default function MonteCarloSimulation() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const contractId = searchParams.get('contractId') || 'CONTRACT_X';

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [simulating, setSimulating] = useState(false);
  const [simulationData, setSimulationData] = useState(null);
  const [iterations, setIterations] = useState(30000);

  useEffect(() => {
    runSimulation();
  }, [contractId]);

  const runSimulation = async () => {
    try {
      setSimulating(true);
      setError('');

      // Simulate delay for realistic feel
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Generate mock Monte Carlo distribution
      const generateDistribution = () => {
        const distribution = [];
        const buckets = 50;
        const mean = 23000000;
        const stdDev = 8000000;

        for (let i = 0; i < buckets; i++) {
          const x = mean + (i - buckets / 2) * (stdDev / 5);
          const z = (x - mean) / stdDev;
          const y = Math.exp(-0.5 * z * z) * 1000;
          distribution.push({
            exposure: x / 1000000,
            frequency: Math.round(y)
          });
        }
        return distribution;
      };

      const mockData = {
        iterations: iterations,
        mean: 23000000,
        median: 22500000,
        std_dev: 8000000,
        p90: 32000000,
        p95: 34500000,
        p99: 42000000,
        var_95: 34500000,
        var_99: 42000000,
        cvar_95: 38000000,
        cvar_99: 45000000,
        min: 8000000,
        max: 55000000,
        distribution: generateDistribution(),
        convergence: Array.from({ length: 100 }, (_, i) => ({
          iteration: i * (iterations / 100),
          mean: 23000000 + (Math.random() - 0.5) * 2000000
        }))
      };

      setSimulationData(mockData);
    } catch (err) {
      setError(err.message || 'Failed to run Monte Carlo simulation');
      console.error('Simulation error:', err);
    } finally {
      setSimulating(false);
    }
  };

  if (!simulationData && simulating) {
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

        <button
          onClick={runSimulation}
          disabled={simulating}
          className="px-6 py-3 bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white rounded-xl font-semibold transition-all flex items-center gap-2 disabled:opacity-50"
        >
          {simulating ? <Loader2 className="w-5 h-5 animate-spin" /> : <RefreshCw className="w-5 h-5" />}
          Re-run Simulation
        </button>
      </div>

      {/* VaR Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <ExposureCard
          title="Mean Exposure"
          value={`₹${(simulationData.mean / 1000000).toFixed(1)}M`}
          subtitle="Expected value"
          icon={TrendingUp}
          color="cyan"
        />

        <ExposureCard
          title="VaR (95%)"
          value={`₹${(simulationData.var_95 / 1000000).toFixed(1)}M`}
          subtitle="95th percentile"
          icon={AlertTriangle}
          color="amber"
        />

        <ExposureCard
          title="VaR (99%)"
          value={`₹${(simulationData.var_99 / 1000000).toFixed(1)}M`}
          subtitle="99th percentile"
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

      {/* Distribution Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="lg:col-span-2">
          <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl border border-violet-500/20 rounded-2xl p-6 shadow-[0_0_30px_rgba(139,92,246,0.15)]">
            <h3 className="text-xl font-bold text-white mb-4">Exposure Distribution</h3>
            <ResponsiveContainer width="100%" height={400}>
              <AreaChart data={simulationData.distribution}>
                <defs>
                  <linearGradient id="colorExposure" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="exposure"
                  stroke="#94a3b8"
                  label={{ value: 'Exposure (₹ Million)', position: 'insideBottom', offset: -5, fill: '#94a3b8' }}
                />
                <YAxis
                  stroke="#94a3b8"
                  label={{ value: 'Frequency', angle: -90, position: 'insideLeft', fill: '#94a3b8' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #8b5cf6',
                    borderRadius: '0.5rem'
                  }}
                />
                <ReferenceLine
                  x={simulationData.mean / 1000000}
                  stroke="#06b6d4"
                  strokeDasharray="3 3"
                  label={{ value: 'Mean', fill: '#06b6d4', position: 'top' }}
                />
                <ReferenceLine
                  x={simulationData.var_95 / 1000000}
                  stroke="#f59e0b"
                  strokeDasharray="3 3"
                  label={{ value: 'VaR 95%', fill: '#f59e0b', position: 'top' }}
                />
                <ReferenceLine
                  x={simulationData.var_99 / 1000000}
                  stroke="#ef4444"
                  strokeDasharray="3 3"
                  label={{ value: 'VaR 99%', fill: '#ef4444', position: 'top' }}
                />
                <Area
                  type="monotone"
                  dataKey="frequency"
                  stroke="#8b5cf6"
                  fillOpacity={1}
                  fill="url(#colorExposure)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Statistics Panel */}
        <div className="lg:col-span-1">
          <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl border border-cyan-500/20 rounded-2xl p-6 shadow-[0_0_30px_rgba(6,182,212,0.15)]">
            <h3 className="text-xl font-bold text-white mb-4">Simulation Statistics</h3>
            <div className="space-y-4">
              {[
                { label: 'Iterations', value: simulationData.iterations.toLocaleString() },
                { label: 'Mean', value: `₹${(simulationData.mean / 1000000).toFixed(2)}M` },
                { label: 'Median', value: `₹${(simulationData.median / 1000000).toFixed(2)}M` },
                { label: 'Std Dev', value: `₹${(simulationData.std_dev / 1000000).toFixed(2)}M` },
                { label: 'Minimum', value: `₹${(simulationData.min / 1000000).toFixed(2)}M` },
                { label: 'Maximum', value: `₹${(simulationData.max / 1000000).toFixed(2)}M` },
                { label: 'P90', value: `₹${(simulationData.p90 / 1000000).toFixed(2)}M` },
                { label: 'P95', value: `₹${(simulationData.p95 / 1000000).toFixed(2)}M` },
                { label: 'P99', value: `₹${(simulationData.p99 / 1000000).toFixed(2)}M` },
                { label: 'CVaR 95%', value: `₹${(simulationData.cvar_95 / 1000000).toFixed(2)}M` },
                { label: 'CVaR 99%', value: `₹${(simulationData.cvar_99 / 1000000).toFixed(2)}M` }
              ].map((stat, index) => (
                <div key={index} className="flex justify-between items-center pb-2 border-b border-slate-700/50 last:border-0">
                  <span className="text-sm text-slate-400">{stat.label}</span>
                  <span className="text-sm font-bold text-white">{stat.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

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
