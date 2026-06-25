import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, TrendingUp, Loader2, AlertTriangle, DollarSign, Activity, BarChart3, RefreshCw } from 'lucide-react';
import ExposureCard from '../../components/enterprise/metrics/ExposureCard';
import ContractSelector from '../../components/enterprise/ContractSelector';
import enterpriseRiskService from '../../services/enterpriseRiskService';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  BarChart,
  Bar,
  Cell
} from 'recharts';

export default function CommodityForecastDashboard() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const contractId = searchParams.get('contractId') || '';

  const handleContractSelect = (id) => {
    if (id) {
      setSearchParams({ contractId: id });
    } else {
      setSearchParams({});
    }
  };

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [forecastData, setForecastData] = useState(null);
  const [simulating, setSimulating] = useState(false);
  const [selectedCommodity, setSelectedCommodity] = useState('Steel');

  useEffect(() => {
    runForecast();
  }, [contractId, selectedCommodity]);

  const runForecast = async () => {
    try {
      setSimulating(true);
      setError('');

      // Backend runs real GBM simulation using commodity data from DB
      const backendData = await enterpriseRiskService.getCommodityForecast(
        contractId,
        { commodity: selectedCommodity }
      );
      setForecastData(backendData);
    } catch (err) {
      setError(err.message || 'Failed to run commodity forecast');
      console.error('Forecast error:', err);
    } finally {
      setSimulating(false);
    }
  };

  if (!forecastData || simulating) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="text-center">
          <Loader2 className="w-16 h-16 text-amber-400 animate-spin mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">Running Commodity Forecast</h2>
          <p className="text-slate-400">Simulating {selectedCommodity} price evolution...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="text-center max-w-md">
          <AlertTriangle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">Forecast Error</h2>
          <p className="text-slate-400 mb-6">{error}</p>
          <button
            onClick={runForecast}
            className="px-6 py-3 bg-amber-500 hover:bg-amber-600 text-white rounded-xl font-semibold transition-all"
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
            className="p-3 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-amber-500/50 transition-all"
          >
            <ArrowLeft className="w-5 h-5 text-slate-400" />
          </button>
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-gradient-to-br from-amber-500/20 to-orange-500/20 border border-amber-500/30">
              <TrendingUp className="w-8 h-8 text-amber-400" />
            </div>
            <div>
              <h1 className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white via-amber-200 to-orange-300">
                Commodity Price Forecast
              </h1>
              <p className="text-slate-400 text-sm">Stochastic Price Simulation & Volatility Analysis</p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <ContractSelector
            selectedContractId={contractId}
            onSelect={handleContractSelect}
            accentColor="amber"
          />
          <button
            onClick={runForecast}
            disabled={simulating}
            className="px-6 py-3 bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white rounded-xl font-semibold transition-all flex items-center gap-2 disabled:opacity-50"
          >
            {simulating ? <Loader2 className="w-5 h-5 animate-spin" /> : <RefreshCw className="w-5 h-5" />}
            Re-run Forecast
          </button>
        </div>
      </div>

      {/* Contract context banner */}
      {forecastData.contract_name && (
        <div className="mb-4 flex items-center gap-3 px-4 py-3 rounded-xl bg-amber-500/10 border border-amber-500/20">
          <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse flex-shrink-0" />
          <p className="text-sm text-amber-300 font-medium">
            Showing contract-specific forecast for <span className="font-bold text-white">{forecastData.contract_name}</span>
          </p>
          {forecastData.commodities_used?.length > 0 && (
            <span className="ml-auto text-xs text-slate-400">
              Contract uses: <span className="text-amber-300 font-semibold">{forecastData.commodities_used.join(', ')}</span>
            </span>
          )}
        </div>
      )}

      {/* Commodity Selector */}
      <div className="mb-6">
        <div className="flex items-center gap-3 flex-wrap">
          {['Steel', 'Copper', 'Oil', 'Aluminum', 'Gold', 'Cement', 'Aggregate', 'Electrical Cable'].map((commodity) => {
            const isUsed = forecastData.commodities_used?.includes(commodity);
            const isSelected = selectedCommodity === commodity;
            return (
              <button
                key={commodity}
                onClick={() => setSelectedCommodity(commodity)}
                className={`relative px-5 py-2.5 rounded-xl font-semibold transition-all text-sm ${
                  isSelected
                    ? 'bg-gradient-to-r from-amber-500 to-orange-600 text-white shadow-[0_0_30px_rgba(245,158,11,0.3)]'
                    : isUsed
                    ? 'bg-amber-500/15 text-amber-300 border border-amber-500/40 hover:bg-amber-500/25'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700 border border-slate-700'
                }`}
              >
                {commodity}
                {isUsed && !isSelected && (
                  <span className="absolute -top-1.5 -right-1.5 w-3 h-3 rounded-full bg-amber-400 border-2 border-slate-900" />
                )}
              </button>
            );
          })}
        </div>
        {forecastData.commodities_used?.length > 0 && (
          <p className="mt-2 text-xs text-slate-500">
            <span className="inline-block w-2.5 h-2.5 rounded-full bg-amber-400 mr-1.5" />
            Highlighted = commodities actually used in this contract
          </p>
        )}
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <ExposureCard
          title="Current Price"
          value={`$${forecastData.current_price.toFixed(0)}`}
          subtitle={`Per unit`}
          icon={DollarSign}
          color="cyan"
        />

        <ExposureCard
          title="Expected Price (1Y)"
          value={`$${forecastData.expected_price.toFixed(0)}`}
          subtitle={`${forecastData.price_change_percent >= 0 ? '+' : ''}${forecastData.price_change_percent.toFixed(1)}%`}
          trend={forecastData.price_change_percent}
          icon={TrendingUp}
          color={forecastData.price_change_percent >= 0 ? 'emerald' : 'red'}
        />

        <ExposureCard
          title="Volatility"
          value={`${(forecastData.volatility * 100).toFixed(0)}%`}
          subtitle="Annual volatility"
          icon={Activity}
          color="amber"
        />

        <ExposureCard
          title="Risk Impact"
          value={`₹${(forecastData.risk_impact / 1000000).toFixed(1)}M`}
          subtitle="Exposure × volatility"
          icon={BarChart3}
          color="red"
        />
      </div>

      {/* Price Forecast Chart */}
      <div className="mb-8">
        <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl border border-amber-500/20 rounded-2xl p-6 shadow-[0_0_30px_rgba(245,158,11,0.15)]">
          <h3 className="text-xl font-bold text-white mb-4">
            {forecastData.commodity} Price Evolution - Geometric Brownian Motion
          </h3>
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={forecastData.forecast}>
              <defs>
                <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.1} />
                </linearGradient>
                <linearGradient id="colorBand" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#64748b" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#64748b" stopOpacity={0.05} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis
                dataKey="day"
                stroke="#94a3b8"
                label={{ value: 'Trading Days', position: 'insideBottom', offset: -5, fill: '#94a3b8' }}
              />
              <YAxis
                stroke="#94a3b8"
                label={{ value: 'Price ($)', angle: -90, position: 'insideLeft', fill: '#94a3b8' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #f59e0b',
                  borderRadius: '0.5rem'
                }}
                formatter={(value) => [`$${value.toFixed(2)}`, 'Price']}
              />
              <Legend />
              <Area
                type="monotone"
                dataKey="upper"
                stroke="#64748b"
                fill="url(#colorBand)"
                name="Upper Band"
                strokeDasharray="3 3"
              />
              <Area
                type="monotone"
                dataKey="lower"
                stroke="#64748b"
                fill="url(#colorBand)"
                name="Lower Band"
                strokeDasharray="3 3"
              />
              <Line
                type="monotone"
                dataKey="price"
                stroke="#f59e0b"
                strokeWidth={3}
                dot={false}
                name="Simulated Price"
              />
              <ReferenceLine
                y={forecastData.current_price}
                stroke="#06b6d4"
                strokeDasharray="3 3"
                label={{ value: 'Current Price', fill: '#06b6d4', position: 'right' }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Scenario Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl border border-cyan-500/20 rounded-2xl p-6 shadow-[0_0_30px_rgba(6,182,212,0.15)]">
          <h3 className="text-xl font-bold text-white mb-4">Price Statistics</h3>
          <div className="space-y-3">
            {[
              { label: 'Current Price',       value: `$${forecastData.current_price.toFixed(2)}`,                              color: 'text-white' },
              { label: 'Expected Price (1Y)', value: `$${forecastData.expected_price.toFixed(2)}`,                             color: forecastData.price_change_percent >= 0 ? 'text-emerald-400' : 'text-red-400' },
              { label: 'Maximum Price',       value: `$${forecastData.max_price.toFixed(2)}`,                                  color: 'text-emerald-400' },
              { label: 'Minimum Price',       value: `$${forecastData.min_price.toFixed(2)}`,                                  color: 'text-red-400' },
              { label: 'Price Range',         value: `$${(forecastData.max_price - forecastData.min_price).toFixed(2)}`,        color: 'text-amber-400' },
              { label: 'Base Volatility (σ)', value: `${((forecastData.base_volatility ?? forecastData.volatility) * 100).toFixed(1)}%`, color: 'text-slate-300' },
              { label: 'Contract Volatility', value: `${(forecastData.volatility * 100).toFixed(1)}%${forecastData.volatility_adj > 0 ? ` (+${(forecastData.volatility_adj*100).toFixed(1)}% risk adj)` : ''}`, color: 'text-amber-400' },
              { label: 'Drift (μ)',           value: `${(forecastData.drift * 100).toFixed(2)}%`,                              color: forecastData.drift >= 0 ? 'text-emerald-400' : 'text-red-400' },
              { label: 'Contract Exposure',   value: `₹${(forecastData.contract_exposure / 1000000).toFixed(2)}M`,              color: 'text-cyan-400' },
              { label: 'Risk Impact',         value: `₹${(forecastData.risk_impact / 1000000).toFixed(2)}M`,                    color: 'text-red-400' },
            ].map((stat, index) => (
              <div key={index} className="flex justify-between items-center pb-2 border-b border-slate-700/40 last:border-0">
                <span className="text-sm text-slate-400">{stat.label}</span>
                <span className={`text-sm font-bold ${stat.color}`}>{stat.value}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl border border-violet-500/20 rounded-2xl p-6 shadow-[0_0_30px_rgba(139,92,246,0.15)]">
          <h3 className="text-xl font-bold text-white mb-4">Scenario Analysis</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={forecastData.volatility_scenarios} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="scenario" stroke="#94a3b8" tick={{ fontSize: 11 }} />
              <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #8b5cf6', borderRadius: '0.5rem' }}
                formatter={(v, n) => [`$${Number(v).toFixed(0)}`, n]}
              />
              <Bar dataKey="price" radius={[6, 6, 0, 0]}>
                {forecastData.volatility_scenarios.map((s, i) => (
                  <Cell key={i} fill={
                    s.scenario === 'Stress'    ? '#ef4444' :
                    s.scenario === 'High Vol'  ? '#f59e0b' :
                    s.scenario === 'Base Case' ? '#8b5cf6' : '#10b981'
                  } />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>

          <div className="mt-4 space-y-2">
            {forecastData.volatility_scenarios.map((scenario, index) => {
              const color = scenario.scenario === 'Stress'    ? 'border-red-500/30 bg-red-500/10 text-red-400'
                          : scenario.scenario === 'High Vol'  ? 'border-amber-500/30 bg-amber-500/10 text-amber-400'
                          : scenario.scenario === 'Base Case' ? 'border-violet-500/30 bg-violet-500/10 text-violet-400'
                          : 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400';
              return (
                <div key={index} className={`flex items-center justify-between p-3 rounded-lg border ${color}`}>
                  <div>
                    <span className="text-sm font-bold">{scenario.scenario}</span>
                    {scenario.volatility != null && (
                      <span className="ml-2 text-xs opacity-70">σ={((scenario.volatility)*100).toFixed(1)}%</span>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-bold text-white">${scenario.price?.toFixed(0)}</span>
                    <span className="text-xs opacity-70">({(scenario.probability * 100).toFixed(0)}% prob)</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
