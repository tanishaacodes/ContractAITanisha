import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Briefcase, Loader2, AlertTriangle, TrendingUp, Shield, Activity, DollarSign } from 'lucide-react';
import enterpriseRiskService from '../../services/enterpriseRiskService';
import ContractSelector from '../../components/enterprise/ContractSelector';
import ExposureCard from '../../components/enterprise/metrics/ExposureCard';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  ZAxis
} from 'recharts';

export default function PortfolioVaRDashboard() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedContractId = searchParams.get('contractId') || '';

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [portfolioData, setPortfolioData] = useState(null);

  useEffect(() => {
    loadPortfolioData();
  }, []);

  const handleContractSelect = (id) => {
    if (id) {
      // Navigate to the contract-specific dashboard for deeper analysis
      navigate(`/enterprise/risk-dashboard?contractId=${id}`);
    }
  };

  const loadPortfolioData = async () => {
    try {
      setLoading(true);
      setError('');

      const data = await enterpriseRiskService.getPortfolioVaR();
      setPortfolioData(data);
    } catch (err) {
      setError(err.message || 'Failed to load portfolio data');
      console.error('Portfolio error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-cyan-400 animate-spin mx-auto mb-4" />
          <p className="text-slate-400 text-lg">Loading Portfolio VaR Analysis...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="text-center max-w-md">
          <AlertTriangle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">Error Loading Portfolio</h2>
          <p className="text-slate-400 mb-6">{error}</p>
          <button
            onClick={loadPortfolioData}
            className="px-6 py-3 bg-cyan-500 hover:bg-cyan-600 text-white rounded-xl font-semibold transition-all"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const COLORS = ['#06b6d4', '#8b5cf6', '#f59e0b', '#ef4444', '#10b981'];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/enterprise/risk-dashboard')}
            className="p-3 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-cyan-500/50 transition-all"
          >
            <ArrowLeft className="w-5 h-5 text-slate-400" />
          </button>
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-500/20 border border-cyan-500/30">
              <Briefcase className="w-8 h-8 text-cyan-400" />
            </div>
            <div>
              <h1 className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white via-cyan-200 to-blue-300">
                Portfolio VaR Dashboard
              </h1>
              <p className="text-slate-400 text-sm">Portfolio-Level Risk Aggregation & Concentration Analysis</p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-500 hidden sm:block">Jump to contract →</span>
          <ContractSelector
            selectedContractId={selectedContractId}
            onSelect={handleContractSelect}
            accentColor="cyan"
          />
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <ExposureCard
          title="Total Portfolio Exposure"
          value={`₹${(portfolioData.total_exposure / 1000000).toFixed(0)}M`}
          subtitle={`${portfolioData.total_contracts} contracts`}
          icon={DollarSign}
          color="cyan"
        />

        <ExposureCard
          title="Portfolio VaR (95%)"
          value={`₹${(portfolioData.portfolio_var_95 / 1000000).toFixed(0)}M`}
          subtitle={`${((portfolioData.portfolio_var_95 / portfolioData.total_exposure) * 100).toFixed(1)}% of exposure`}
          icon={AlertTriangle}
          color="amber"
        />

        <ExposureCard
          title="Portfolio VaR (99%)"
          value={`₹${(portfolioData.portfolio_var_99 / 1000000).toFixed(0)}M`}
          subtitle={`${((portfolioData.portfolio_var_99 / portfolioData.total_exposure) * 100).toFixed(1)}% of exposure`}
          icon={Shield}
          color="red"
        />

        <ExposureCard
          title="Weighted Margin"
          value={`${portfolioData.weighted_margin.toFixed(1)}%`}
          subtitle="Portfolio average"
          icon={TrendingUp}
          color="emerald"
        />
      </div>

      {/* Risk Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Risk Categories Pie Chart */}
        <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl border border-cyan-500/20 rounded-2xl p-6 shadow-[0_0_30px_rgba(6,182,212,0.15)]">
          <h3 className="text-xl font-bold text-white mb-4">Risk Distribution by Category</h3>
          <ResponsiveContainer width="100%" height={350}>
            <PieChart>
              <Pie
                data={portfolioData.risk_categories}
                dataKey="exposure"
                nameKey="category"
                cx="50%"
                cy="50%"
                outerRadius={120}
                label={(entry) => `${entry.category}: ${entry.percentage}%`}
              >
                {portfolioData.risk_categories.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #06b6d4',
                  borderRadius: '0.5rem'
                }}
                formatter={(value) => [`₹${(value / 1000000).toFixed(1)}M`, 'Exposure']}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Top Risk Contracts */}
        <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl border border-violet-500/20 rounded-2xl p-6 shadow-[0_0_30px_rgba(139,92,246,0.15)]">
          <h3 className="text-xl font-bold text-white mb-4">Top 5 High-Risk Contracts</h3>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={portfolioData.top_risk_contracts} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis type="number" stroke="#94a3b8" />
              <YAxis type="category" dataKey="name" stroke="#94a3b8" width={120} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #8b5cf6',
                  borderRadius: '0.5rem'
                }}
                formatter={(value, name) => {
                  if (name === 'risk') return [(value * 100).toFixed(0) + '%', 'Risk Score'];
                  return [`₹${(value / 1000000).toFixed(1)}M`, 'Exposure'];
                }}
              />
              <Bar dataKey="risk" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Contract Details Table */}
      <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl border border-emerald-500/20 rounded-2xl p-6 shadow-[0_0_30px_rgba(16,185,129,0.15)] mb-8">
        <h3 className="text-xl font-bold text-white mb-4">Contract Portfolio Details</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left py-3 px-4 text-sm font-semibold text-slate-300">Contract Name</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-slate-300">Counterparty</th>
                <th className="text-right py-3 px-4 text-sm font-semibold text-slate-300">Exposure</th>
                <th className="text-right py-3 px-4 text-sm font-semibold text-slate-300">VaR (95%)</th>
                <th className="text-right py-3 px-4 text-sm font-semibold text-slate-300">Margin</th>
                <th className="text-right py-3 px-4 text-sm font-semibold text-slate-300">Risk Score</th>
              </tr>
            </thead>
            <tbody>
              {portfolioData.contracts.map((contract, index) => (
                <tr
                  key={contract.id}
                  className="border-b border-slate-700/50 hover:bg-slate-700/20 transition-colors cursor-pointer"
                  onClick={() => navigate(`/enterprise/risk-dashboard?contractId=${contract.id}`)}
                >
                  <td className="py-3 px-4 text-sm text-white font-medium">{contract.name}</td>
                  <td className="py-3 px-4 text-sm text-slate-300">{contract.counterparty}</td>
                  <td className="py-3 px-4 text-sm text-right text-white">
                    ₹{(contract.exposure / 1000000).toFixed(1)}M
                  </td>
                  <td className="py-3 px-4 text-sm text-right text-amber-400">
                    ₹{(contract.var_95 / 1000000).toFixed(1)}M
                  </td>
                  <td className="py-3 px-4 text-sm text-right">
                    <span className={`px-2 py-1 rounded-lg font-semibold ${
                      contract.margin >= 20
                        ? 'bg-emerald-500/20 text-emerald-400'
                        : contract.margin >= 15
                        ? 'bg-cyan-500/20 text-cyan-400'
                        : 'bg-amber-500/20 text-amber-400'
                    }`}>
                      {contract.margin.toFixed(1)}%
                    </span>
                  </td>
                  <td className="py-3 px-4 text-sm text-right">
                    <span className={`px-2 py-1 rounded-lg font-semibold ${
                      contract.risk_score >= 0.7
                        ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                        : contract.risk_score >= 0.4
                        ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                        : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    }`}>
                      {(contract.risk_score * 100).toFixed(0)}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Concentration Risk */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl border border-red-500/20 rounded-2xl p-6 shadow-[0_0_30px_rgba(239,68,68,0.15)]">
          <div className="flex items-center gap-3 mb-4">
            <Activity className="w-6 h-6 text-red-400" />
            <h3 className="text-lg font-bold text-white">Counterparty Concentration</h3>
          </div>
          <p className="text-4xl font-black text-red-400 mb-2">
            {(portfolioData.diversification.counterparty_concentration * 100).toFixed(0)}%
          </p>
          <div className="h-2 bg-slate-700 rounded-full overflow-hidden mt-3">
            <div
              className="h-full bg-gradient-to-r from-red-500 to-orange-500 transition-all duration-1000"
              style={{ width: `${portfolioData.diversification.counterparty_concentration * 100}%` }}
            />
          </div>
        </div>

        <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl border border-amber-500/20 rounded-2xl p-6 shadow-[0_0_30px_rgba(245,158,11,0.15)]">
          <div className="flex items-center gap-3 mb-4">
            <Activity className="w-6 h-6 text-amber-400" />
            <h3 className="text-lg font-bold text-white">Geographic Concentration</h3>
          </div>
          <p className="text-4xl font-black text-amber-400 mb-2">
            {(portfolioData.diversification.geographic_concentration * 100).toFixed(0)}%
          </p>
          <div className="h-2 bg-slate-700 rounded-full overflow-hidden mt-3">
            <div
              className="h-full bg-gradient-to-r from-amber-500 to-yellow-500 transition-all duration-1000"
              style={{ width: `${portfolioData.diversification.geographic_concentration * 100}%` }}
            />
          </div>
        </div>

        <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl border border-violet-500/20 rounded-2xl p-6 shadow-[0_0_30px_rgba(139,92,246,0.15)]">
          <div className="flex items-center gap-3 mb-4">
            <Activity className="w-6 h-6 text-violet-400" />
            <h3 className="text-lg font-bold text-white">Sector Concentration</h3>
          </div>
          <p className="text-4xl font-black text-violet-400 mb-2">
            {(portfolioData.diversification.sector_concentration * 100).toFixed(0)}%
          </p>
          <div className="h-2 bg-slate-700 rounded-full overflow-hidden mt-3">
            <div
              className="h-full bg-gradient-to-r from-violet-500 to-purple-500 transition-all duration-1000"
              style={{ width: `${portfolioData.diversification.sector_concentration * 100}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
