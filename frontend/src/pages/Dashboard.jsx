import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileText, TrendingUp, Clock, Shield, Target, Zap } from 'lucide-react';
import useAuthStore from '../store/authStore';
import useThemeStore from '../store/themeStore';
import api from '../utils/api';
import DocumentGrid from '../components/DocumentGrid';
import GlobalCommandHeader from '../components/GlobalCommandHeader';

// Mini Sparkline Component
const Sparkline = ({ data, color }) => {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;

  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * 100;
    const y = 100 - ((value - min) / range) * 100;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg className="w-full h-8" viewBox="0 0 100 100" preserveAspectRatio="none">
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
};


const Dashboard = () => {
  const navigate = useNavigate();
  const { user, clearFirstLoginFlag } = useAuthStore();
  const { theme } = useThemeStore();
  const isFirstLogin = localStorage.getItem('isFirstLogin') === 'true';
  const [dashboardStats, setDashboardStats] = useState({
    totalContracts: 0,
    analysisComplete: 0,
    pendingReview: 0,
    riskScoreAvg: 0.0
  });

  useEffect(() => {
    if (isFirstLogin) {
      clearFirstLoginFlag();
    }
  }, [isFirstLogin, clearFirstLoginFlag]);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await api.get('/dashboard/stats');
        setDashboardStats(response.data);
      } catch (err) {
        console.error('Failed to fetch dashboard stats:', err);
      }
    };
    fetchStats();
  }, []);

  // Mock sparkline data (last 7 days trend)
  const trendData = {
    contracts: [15, 22, 18, 25, 20, 28, dashboardStats.totalContracts || 29],
    analysis: [10, 15, 12, 18, 15, 20, dashboardStats.analysisComplete || 22],
    pending: [5, 7, 6, 10, 8, 12, dashboardStats.pendingReview || 8]
  };

  // Enhanced stats with gradients and sparklines
  const stats = [
    {
      label: 'Total Contracts',
      value: String(dashboardStats.totalContracts),
      icon: FileText,
      gradient: 'from-blue-600 via-blue-500 to-cyan-500',
      bgGradient: 'from-blue-500/10 to-cyan-500/10',
      sparkline: trendData.contracts,
      sparklineColor: '#3b82f6',
      change: '+12%',
      filter: 'all',
      route: '/contracts'
    },
    {
      label: 'Analysis Complete',
      value: String(dashboardStats.analysisComplete),
      icon: TrendingUp,
      gradient: 'from-emerald-600 via-emerald-500 to-green-500',
      bgGradient: 'from-emerald-500/10 to-green-500/10',
      sparkline: trendData.analysis,
      sparklineColor: '#10b981',
      change: '+8%',
      filter: 'analyzed',
      route: '/contracts'
    },
    {
      label: 'Pending Review',
      value: String(dashboardStats.pendingReview),
      icon: Clock,
      gradient: 'from-amber-600 via-amber-500 to-yellow-500',
      bgGradient: 'from-amber-500/10 to-yellow-500/10',
      sparkline: trendData.pending,
      sparklineColor: '#f59e0b',
      change: '-5%',
      filter: 'pending',
      route: '/contracts'
    },
  ];

  // Quick stats for overview
  const quickStats = [
    { label: 'Avg Risk Score', value: dashboardStats.riskScoreAvg?.toFixed(1) || '0.0', icon: Target, color: 'text-purple-400', bg: 'bg-purple-500/10' },
    { label: 'Time Saved', value: '48h', icon: Zap, color: 'text-yellow-400', bg: 'bg-yellow-500/10' },
    { label: 'AI Accuracy', value: '99.2%', icon: Shield, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
  ];

  return (
    <div className="space-y-4">
      {/* Global Command Header - Dashboard Only */}
      <GlobalCommandHeader />

      {/* Compact Welcome Section */}
      <div className="relative overflow-hidden bg-gradient-to-r from-blue-600/10 via-purple-600/10 to-emerald-600/10 border border-slate-800 rounded-xl p-4">
        <div className="relative z-10">
          <div className="flex items-center justify-between">
            <div>
              <h1 className={`text-xl font-bold ${theme.colors.textPrimary} mb-1 flex items-center gap-2`}>
                {isFirstLogin ? `Welcome, ${user?.firstName}! 🎉` : `Welcome back, ${user?.firstName}! 👋`}
              </h1>
              <p className={`${theme.colors.textSecondary} text-xs mb-2`}>
                {isFirstLogin
                  ? 'Get started by uploading your first contract'
                  : 'Manage and analyze your contracts with AI-powered intelligence'
                }
              </p>
              {/* Quick Stats Pills */}
              <div className="flex flex-wrap gap-2">
                {quickStats.map((stat, index) => {
                  const Icon = stat.icon;
                  return (
                    <div key={index} className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md ${stat.bg} border border-slate-700/50 text-xs`}>
                      <Icon className={`h-3 w-3 ${stat.color}`} />
                      <span className="font-medium text-slate-400">{stat.label}:</span>
                      <span className={`font-bold ${stat.color}`}>{stat.value}</span>
                    </div>
                  );
                })}
              </div>
            </div>
            <button
              onClick={() => navigate('/upload')}
              className="px-4 py-2 bg-gradient-to-r from-blue-600 to-emerald-600 hover:from-blue-700 hover:to-emerald-700 text-white rounded-lg font-medium text-sm transition-all duration-200 flex items-center gap-2"
            >
              <Upload className="h-4 w-4" />
              Upload Contract
            </button>
          </div>
        </div>
      </div>

      {/* Compact Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          const isPositive = stat.change.startsWith('+');

          return (
            <div
              key={index}
              onClick={() => {
                if (stat.filter) {
                  navigate(`${stat.route}?filter=${stat.filter}`);
                } else if (stat.route) {
                  navigate(stat.route);
                }
              }}
              className={`group relative overflow-hidden bg-gradient-to-br ${stat.bgGradient} border border-slate-800 rounded-xl p-4 cursor-pointer transition-all duration-200 hover:scale-[1.02] hover:border-slate-700`}
            >
              <div className="relative z-10">
                {/* Header */}
                <div className="flex items-center justify-between mb-2">
                  <div className={`p-2 rounded-lg bg-gradient-to-br ${stat.gradient}`}>
                    <Icon className="h-4 w-4 text-white" />
                  </div>
                  <div className={`flex items-center gap-0.5 text-[10px] font-semibold px-1.5 py-0.5 rounded-full ${isPositive ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                    <TrendingUp className={`h-2.5 w-2.5 ${!isPositive && 'rotate-180'}`} />
                    {stat.change}
                  </div>
                </div>

                {/* Value */}
                <p className="text-2xl font-bold text-white">{stat.value}</p>
                <p className="text-xs text-slate-400">{stat.label}</p>

                {/* Sparkline */}
                <div className="mt-2 opacity-50 group-hover:opacity-80 transition-opacity">
                  <Sparkline data={stat.sparkline} color={stat.sparklineColor} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Contract Summary Table */}
      <DocumentGrid showPagination={true} itemsPerPage={5} />
    </div>
  );
};

export default Dashboard;
