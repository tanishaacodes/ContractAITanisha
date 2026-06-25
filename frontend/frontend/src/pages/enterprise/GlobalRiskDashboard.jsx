import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Globe,
  TrendingUp,
  Shield,
  AlertTriangle,
  Activity,
  DollarSign,
  Network,
  Map,
  BarChart3,
  Loader2,
  ChevronRight,
  Target
} from 'lucide-react';
import ExposureCard from '../../components/enterprise/metrics/ExposureCard';
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
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line
} from 'recharts';

export default function GlobalRiskDashboard() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const contractId = searchParams.get('contractId') || 'CONTRACT_X';

  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    loadDashboardData();
  }, [contractId]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError('');

      // For now, using mock data - will connect to backend API
      const mockData = {
        exposure: {
          base_exposure: 15000000,
          total_exposure: 22500000,
          systemic_multiplier: 1.5
        },
        monte_carlo: {
          mean: 23000000,
          p95: 34500000,
          p99: 42000000
        },
        commodity_risk: {
          commodity_risk_exposure: 2500000
        },
        margin: 18.5,
        supply_chain_risk_score: 0.35,
        geo_political_risk_score: 0.28,
        trend: {
          exposure: -2.3,
          margin: 1.8,
          var: 5.2
        }
      };

      setData(mockData);
    } catch (err) {
      setError(err.message || 'Failed to load dashboard data');
      console.error('Dashboard error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-cyan-400 animate-spin mx-auto mb-4" />
          <p className="text-slate-400 text-lg">Loading Enterprise Risk Intelligence...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="text-center max-w-md">
          <AlertTriangle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">Error Loading Dashboard</h2>
          <p className="text-slate-400 mb-6">{error}</p>
          <button
            onClick={loadDashboardData}
            className="px-6 py-3 bg-cyan-500 hover:bg-cyan-600 text-white rounded-xl font-semibold transition-all"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const exposureData = [
    { name: 'Base Exposure', value: data.exposure.base_exposure / 1000000 },
    { name: 'Systemic Exposure', value: data.exposure.total_exposure / 1000000 }
  ];

  const varData = [
    { name: 'Mean', value: data.monte_carlo.mean / 1000000, fill: '#06b6d4' },
    { name: 'P95', value: data.monte_carlo.p95 / 1000000, fill: '#f59e0b' },
    { name: 'P99', value: data.monte_carlo.p99 / 1000000, fill: '#ef4444' }
  ];

  const quickLinks = [
    {
      title: 'Contract Knowledge Graph',
      description: 'Interactive graph visualization',
      icon: Network,
      path: '/enterprise/contract-graph',
      color: 'cyan'
    },
    {
      title: 'Supply Chain Risk',
      description: 'Multi-tier supplier analysis',
      icon: Activity,
      path: '/enterprise/supply-chain',
      color: 'violet'
    },
    {
      title: 'Geo-Political Risk',
      description: 'Global risk heatmap',
      icon: Map,
      path: '/enterprise/geo-risk',
      color: 'emerald'
    },
    {
      title: 'Commodity Forecast',
      description: 'Price simulation & volatility',
      icon: TrendingUp,
      path: '/enterprise/commodity',
      color: 'amber'
    },
    {
      title: 'Monte Carlo VaR',
      description: 'Value-at-Risk simulation',
      icon: BarChart3,
      path: '/enterprise/monte-carlo',
      color: 'red'
    },
    {
      title: 'Portfolio VaR',
      description: 'Portfolio-level analytics',
      icon: Target,
      path: '/enterprise/portfolio-var',
      color: 'cyan'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-3">
          <div className="p-3 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-500/20 border border-cyan-500/30">
            <Globe className="w-8 h-8 text-cyan-400" />
          </div>
          <div>
            <h1 className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-white via-cyan-200 to-blue-300">
              Global Enterprise Risk Intelligence
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              CFO-Grade Contract Risk & Profitability Analytics Platform
            </p>
          </div>
        </div>
      </div>

      {/* Key Metrics - Top Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <ExposureCard
          title="Total Risk Exposure"
          value={`₹${(data.exposure.total_exposure / 1000000).toFixed(1)}M`}
          subtitle="Risk-adjusted liability"
          trend={data.trend.exposure}
          icon={Shield}
          color="red"
        />

        <ExposureCard
          title="Expected Margin"
          value={`${data.margin.toFixed(1)}%`}
          subtitle="After risk adjustment"
          trend={data.trend.margin}
          icon={DollarSign}
          color="emerald"
        />

        <ExposureCard
          title="VaR (P95)"
          value={`₹${(data.monte_carlo.p95 / 1000000).toFixed(1)}M`}
          subtitle="95th percentile loss"
          trend={data.trend.var}
          icon={AlertTriangle}
          color="amber"
        />

        <ExposureCard
          title="VaR (P99)"
          value={`₹${(data.monte_carlo.p99 / 1000000).toFixed(1)}M`}
          subtitle="99th percentile loss"
          icon={BarChart3}
          color="violet"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Exposure Breakdown */}
        <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl border border-cyan-500/20 rounded-2xl p-6 shadow-[0_0_30px_rgba(6,182,212,0.15)]">
          <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <Shield className="w-5 h-5 text-cyan-400" />
            Exposure Breakdown
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={exposureData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="name" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" label={{ value: '₹ Million', angle: -90, position: 'insideLeft', fill: '#94a3b8' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #06b6d4',
                  borderRadius: '0.5rem'
                }}
              />
              <Bar dataKey="value" fill="#06b6d4" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Monte Carlo VaR Distribution */}
        <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl border border-violet-500/20 rounded-2xl p-6 shadow-[0_0_30px_rgba(139,92,246,0.15)]">
          <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-violet-400" />
            Monte Carlo VaR
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={varData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={(entry) => `${entry.name}: ₹${entry.value.toFixed(1)}M`}
              >
                {varData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #8b5cf6',
                  borderRadius: '0.5rem'
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Risk Scores */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl border border-emerald-500/20 rounded-2xl p-6 shadow-[0_0_30px_rgba(16,185,129,0.15)]">
          <h3 className="text-xl font-bold text-white mb-4">Supply Chain Risk</h3>
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="h-4 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500 transition-all duration-1000"
                  style={{ width: `${data.supply_chain_risk_score * 100}%` }}
                />
              </div>
            </div>
            <span className="text-3xl font-black text-emerald-400">
              {(data.supply_chain_risk_score * 100).toFixed(0)}%
            </span>
          </div>
        </div>

        <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl border border-amber-500/20 rounded-2xl p-6 shadow-[0_0_30px_rgba(245,158,11,0.15)]">
          <h3 className="text-xl font-bold text-white mb-4">Geo-Political Risk</h3>
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="h-4 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-amber-500 to-red-500 transition-all duration-1000"
                  style={{ width: `${data.geo_political_risk_score * 100}%` }}
                />
              </div>
            </div>
            <span className="text-3xl font-black text-amber-400">
              {(data.geo_political_risk_score * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      </div>

      {/* Quick Access Modules */}
      <div>
        <h2 className="text-2xl font-bold text-white mb-4">Risk Intelligence Modules</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {quickLinks.map((link, index) => {
            const Icon = link.icon;
            const colorMap = {
              cyan: 'from-cyan-500/20 to-blue-500/20 border-cyan-500/30 hover:border-cyan-400/50',
              violet: 'from-violet-500/20 to-purple-500/20 border-violet-500/30 hover:border-violet-400/50',
              emerald: 'from-emerald-500/20 to-green-500/20 border-emerald-500/30 hover:border-emerald-400/50',
              amber: 'from-amber-500/20 to-orange-500/20 border-amber-500/30 hover:border-amber-400/50',
              red: 'from-red-500/20 to-rose-500/20 border-red-500/30 hover:border-red-400/50'
            };

            return (
              <button
                key={index}
                onClick={() => navigate(`${link.path}?contractId=${contractId}`)}
                className={`relative group p-6 rounded-2xl bg-gradient-to-br ${colorMap[link.color]} border backdrop-blur-xl transition-all duration-500 hover:scale-[1.02] hover:shadow-[0_0_40px_rgba(6,182,212,0.3)] text-left`}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className={`p-3 rounded-xl bg-gradient-to-br ${colorMap[link.color]} border`}>
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  <ChevronRight className="w-5 h-5 text-slate-400 group-hover:text-white group-hover:translate-x-1 transition-all" />
                </div>
                <h3 className="text-lg font-bold text-white mb-2">{link.title}</h3>
                <p className="text-sm text-slate-400">{link.description}</p>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
