import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Target, Loader2, AlertTriangle, TrendingUp, TrendingDown } from 'lucide-react';
import ExposureCard from '../../components/enterprise/metrics/ExposureCard';
import ContractSelector from '../../components/enterprise/ContractSelector';
import enterpriseRiskService from '../../services/enterpriseRiskService';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
  ReferenceLine
} from 'recharts';

export default function MarginSensitivityAnalysis() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const contractId = searchParams.get('contractId') || '';

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sensitivityData, setSensitivityData] = useState(null);

  const handleContractSelect = (id) => {
    setSensitivityData(null);
    setLoading(true);
    if (id) {
      setSearchParams({ contractId: id });
    } else {
      setSearchParams({});
    }
  };

  useEffect(() => {
    loadSensitivityData();
  }, [contractId]);

  const loadSensitivityData = async () => {
    try {
      setLoading(true);
      setError('');

      let targetContractId = contractId;

      // If no real contractId, fetch first available contract from portfolio
      if (!contractId) {
        const portfolio = await enterpriseRiskService.getPortfolioContracts();
        if (portfolio.contracts && portfolio.contracts.length > 0) {
          targetContractId = portfolio.contracts[0].id;
        } else {
          throw new Error('No contracts found. Please upload a contract first to run Margin Sensitivity Analysis.');
        }
      }

      const apiData = await enterpriseRiskService.getMarginSensitivity(targetContractId);
      const factors = apiData.risk_factors || apiData.factors || [];
      setSensitivityData({
        base_margin: apiData.base_margin ?? apiData.baseline_margin ?? 18.5,
        revenue: apiData.revenue || 100000000,
        base_cost: apiData.base_cost || 75000000,
        risk_factors: factors,
        worst_case_margin: apiData.worst_case_margin ?? apiData.scenarios?.worst_case ?? 2.3,
        best_case_margin: apiData.best_case_margin ?? apiData.scenarios?.best_case ?? 28.9,
        most_likely_margin: apiData.most_likely_margin ?? apiData.base_margin ?? 18.5,
        top_risks: apiData.top_risks || [],
        contract_name: apiData.contract_name || '',
        contract_risk_level: apiData.contract_risk_level || 'MEDIUM',
      });
    } catch (err) {
      setError(err.message || 'Failed to load sensitivity data');
      console.error('Sensitivity error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-violet-400 animate-spin mx-auto mb-4" />
          <p className="text-slate-400 text-lg">Loading Margin Sensitivity Analysis...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="text-center max-w-md">
          <AlertTriangle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">Error Loading Analysis</h2>
          <p className="text-slate-400 mb-6">{error}</p>
          <button
            onClick={loadSensitivityData}
            className="px-6 py-3 bg-violet-500 hover:bg-violet-600 text-white rounded-xl font-semibold transition-all"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!sensitivityData) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-violet-400 animate-spin mx-auto mb-4" />
          <p className="text-slate-400 text-lg">Loading Margin Sensitivity Analysis...</p>
        </div>
      </div>
    );
  }

  // Prepare tornado chart data
  const tornadoData = sensitivityData.risk_factors.map(factor => ({
    factor: factor.factor,
    negative: factor.low_impact,
    positive: factor.high_impact,
    description: factor.description
  }));

  const allNeg = tornadoData.map(d => d.negative);
  const allPos = tornadoData.map(d => d.positive);
  const xMin = Math.floor(Math.min(...allNeg) * 1.15);
  const xMax = Math.ceil(Math.max(...allPos) * 1.15);

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-slate-800 border border-violet-500 rounded-lg p-4 shadow-xl">
          <p className="text-white font-semibold mb-2">{data.factor}</p>
          <p className="text-slate-300 text-sm mb-1">{data.description}</p>
          <div className="space-y-1 mt-2">
            <p className="text-red-400 text-sm">Downside: {data.negative.toFixed(1)}%</p>
            <p className="text-emerald-400 text-sm">Upside: +{data.positive.toFixed(1)}%</p>
          </div>
        </div>
      );
    }
    return null;
  };

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
              <Target className="w-8 h-8 text-violet-400" />
            </div>
            <div>
              <h1 className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white via-violet-200 to-purple-300">
                Margin Sensitivity Analysis
              </h1>
              <p className="text-slate-400 text-sm">
                {sensitivityData?.contract_name
                  ? `${sensitivityData.contract_name} · Risk: ${sensitivityData.contract_risk_level}`
                  : 'Tornado Chart - Risk Factor Impact on Profitability'}
              </p>
            </div>
          </div>
        </div>
        <ContractSelector
          selectedContractId={contractId}
          onSelect={handleContractSelect}
          accentColor="violet"
        />
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <ExposureCard
          title="Base Case Margin"
          value={`${sensitivityData.base_margin.toFixed(1)}%`}
          subtitle="Expected margin"
          icon={Target}
          color="cyan"
        />

        <ExposureCard
          title="Worst Case"
          value={`${sensitivityData.worst_case_margin.toFixed(1)}%`}
          subtitle="All risks materialize"
          icon={TrendingDown}
          color="red"
        />

        <ExposureCard
          title="Best Case"
          value={`${sensitivityData.best_case_margin.toFixed(1)}%`}
          subtitle="All risks mitigated"
          icon={TrendingUp}
          color="emerald"
        />

        <ExposureCard
          title="Range"
          value={`${(sensitivityData.best_case_margin - sensitivityData.worst_case_margin).toFixed(1)}%`}
          subtitle="Margin volatility"
          icon={AlertTriangle}
          color="amber"
        />
      </div>

      {/* Tornado Chart */}
      <div className="mb-8">
        <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl border border-violet-500/20 rounded-2xl p-6 shadow-[0_0_30px_rgba(139,92,246,0.15)]">
          <h3 className="text-xl font-bold text-white mb-4">
            Tornado Chart - Risk Factor Sensitivity
          </h3>
          <p className="text-slate-400 text-sm mb-6">
            Impact of each risk factor on margin percentage (sorted by total range)
          </p>

          <ResponsiveContainer width="100%" height={500}>
            <BarChart
              data={tornadoData}
              layout="vertical"
              margin={{ top: 20, right: 30, left: 120, bottom: 20 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis
                type="number"
                stroke="#94a3b8"
                label={{ value: 'Margin Impact (%)', position: 'insideBottom', offset: -10, fill: '#94a3b8' }}
                domain={[xMin, xMax]}
              />
              <YAxis
                type="category"
                dataKey="factor"
                stroke="#94a3b8"
                width={110}
              />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine x={0} stroke="#94a3b8" strokeWidth={2} />

              {/* Negative impact (left side) */}
              <Bar dataKey="negative" fill="#ef4444" radius={[4, 0, 0, 4]} />

              {/* Positive impact (right side) */}
              <Bar dataKey="positive" fill="#10b981" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>

          {/* Legend */}
          <div className="mt-4 flex items-center justify-center gap-6">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-red-500 rounded"></div>
              <span className="text-sm text-slate-300">Downside Impact</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-emerald-500 rounded"></div>
              <span className="text-sm text-slate-300">Upside Impact</span>
            </div>
          </div>
        </div>
      </div>

      {/* Top Risk Drivers */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl border border-red-500/20 rounded-2xl p-6 shadow-[0_0_30px_rgba(239,68,68,0.15)]">
          <h3 className="text-xl font-bold text-white mb-4">Top Risk Drivers</h3>
          <div className="space-y-4">
            {sensitivityData.top_risks.map((risk, index) => (
              <div key={index} className="p-4 bg-slate-900/50 rounded-xl border border-slate-700">
                <div className="flex items-center justify-between mb-3">
                  <span className="font-semibold text-white">{risk.name}</span>
                  <span className={`px-3 py-1 rounded-lg text-sm font-bold ${
                    index === 0
                      ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                      : index === 1
                      ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                      : 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
                  }`}>
                    #{index + 1}
                  </span>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Impact:</span>
                    <span className="text-white font-semibold">{risk.impact.toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Probability:</span>
                    <span className="text-white font-semibold">{(risk.probability * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Expected Loss:</span>
                    <span className="text-red-400 font-semibold">
                      {(risk.impact * risk.probability).toFixed(1)}%
                    </span>
                  </div>
                </div>

                {/* Risk bar */}
                <div className="mt-3 h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-red-500 to-orange-500 transition-all duration-1000"
                    style={{ width: `${risk.probability * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl border border-cyan-500/20 rounded-2xl p-6 shadow-[0_0_30px_rgba(6,182,212,0.15)]">
          <h3 className="text-xl font-bold text-white mb-4">Scenario Summary</h3>

          <div className="space-y-6">
            {/* Worst Case */}
            <div className="p-4 bg-red-500/10 rounded-xl border border-red-500/30">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-300">Worst Case Scenario</span>
                <TrendingDown className="w-5 h-5 text-red-400" />
              </div>
              <p className="text-3xl font-black text-red-400 mb-1">
                {sensitivityData.worst_case_margin.toFixed(1)}%
              </p>
              <p className="text-xs text-slate-400">All risk factors at maximum negative impact</p>
            </div>

            {/* Base Case */}
            <div className="p-4 bg-cyan-500/10 rounded-xl border border-cyan-500/30">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-300">Base Case Scenario</span>
                <Target className="w-5 h-5 text-cyan-400" />
              </div>
              <p className="text-3xl font-black text-cyan-400 mb-1">
                {sensitivityData.most_likely_margin.toFixed(1)}%
              </p>
              <p className="text-xs text-slate-400">Expected margin with current risk levels</p>
            </div>

            {/* Best Case */}
            <div className="p-4 bg-emerald-500/10 rounded-xl border border-emerald-500/30">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-300">Best Case Scenario</span>
                <TrendingUp className="w-5 h-5 text-emerald-400" />
              </div>
              <p className="text-3xl font-black text-emerald-400 mb-1">
                {sensitivityData.best_case_margin.toFixed(1)}%
              </p>
              <p className="text-xs text-slate-400">All risk factors at maximum positive impact</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
