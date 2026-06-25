import { useState, useEffect } from 'react';
import {
  TrendingUp,
  AlertTriangle,
  Shield,
  Users,
  Target,
  BarChart3,
  Loader2,
  FileText,
  Activity,
} from 'lucide-react';
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
  ZAxis,
} from 'recharts';
import api from '../utils/api';

const PortfolioAnalytics = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [analytics, setAnalytics] = useState(null);
  const [portfolioRisk, setPortfolioRisk] = useState(null);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      setLoading(true);

      // Load both analytics and portfolio risk in parallel
      const [analyticsRes, riskRes] = await Promise.all([
        api.get('/intents/analytics'),
        api.get('/portfolio/risk')
      ]);

      setAnalytics(analyticsRes.data);
      setPortfolioRisk(riskRes.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load analytics');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const COLORS = [
    '#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b',
    '#10b981', '#06b6d4', '#6366f1', '#14b8a6',
    '#f97316', '#84cc16'
  ];

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'HIGH': return '#ef4444';
      case 'MEDIUM': return '#f59e0b';
      case 'LOW': return '#10b981';
      default: return '#94a3b8';
    }
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-slate-800 border border-slate-600 rounded-lg p-3 shadow-xl">
          <p className="text-white font-semibold mb-1">{payload[0].name}</p>
          <p className="text-slate-300 text-sm">Value: {payload[0].value}</p>
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-900">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-slate-400">Loading portfolio analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-900 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-900/20 border border-red-800 text-red-300 rounded-lg p-4">
            <AlertTriangle size={20} className="inline mr-2" />
            {error}
          </div>
        </div>
      </div>
    );
  }

  if (!analytics) {
    return null;
  }

  const { summary, visualizations, high_risk_items } = analytics;

  // Prepare intent distribution data for bubble chart
  const intentBubbleData = visualizations.intent_distribution.map((item, idx) => ({
    name: item.name,
    occurrences: item.occurrence_count,
    confidence: parseFloat((item.confidence * 100).toFixed(1)),
    risk: 50, // Can be calculated based on risk scores
  }));

  return (
    <div className="min-h-screen bg-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Portfolio Analytics</h1>
          <p className="text-slate-400">
            Comprehensive insights across all contracts with intent mining
          </p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
          <div className="bg-gradient-to-br from-blue-900/30 to-blue-800/20 border border-blue-700/50 rounded-lg p-5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-blue-400">Total Intents</span>
              <Target className="w-5 h-5 text-blue-400" />
            </div>
            <div className="text-3xl font-bold text-white">{summary.total_intents}</div>
          </div>

          <div className="bg-gradient-to-br from-yellow-900/30 to-yellow-800/20 border border-yellow-700/50 rounded-lg p-5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-yellow-400">Obligations</span>
              <Activity className="w-5 h-5 text-yellow-400" />
            </div>
            <div className="text-3xl font-bold text-white">{summary.total_obligations}</div>
          </div>

          <div className="bg-gradient-to-br from-green-900/30 to-green-800/20 border border-green-700/50 rounded-lg p-5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-green-400">Rights</span>
              <Shield className="w-5 h-5 text-green-400" />
            </div>
            <div className="text-3xl font-bold text-white">{summary.total_rights}</div>
          </div>

          <div className="bg-gradient-to-br from-red-900/30 to-red-800/20 border border-red-700/50 rounded-lg p-5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-red-400">High Risk Obligations</span>
              <AlertTriangle className="w-5 h-5 text-red-400" />
            </div>
            <div className="text-3xl font-bold text-white">{summary.high_risk_obligations_count}</div>
          </div>

          <div className="bg-gradient-to-br from-orange-900/30 to-orange-800/20 border border-orange-700/50 rounded-lg p-5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-orange-400">High Risk Rights</span>
              <AlertTriangle className="w-5 h-5 text-orange-400" />
            </div>
            <div className="text-3xl font-bold text-white">{summary.high_risk_rights_count}</div>
          </div>
        </div>

        {/* Portfolio Risk Score Card - NEW */}
        {portfolioRisk && (
          <div className={`mb-8 rounded-xl p-6 border-2 ${
            portfolioRisk.severity === 'HIGH'
              ? 'bg-red-900/20 border-red-700'
              : portfolioRisk.severity === 'MEDIUM'
              ? 'bg-yellow-900/20 border-yellow-700'
              : 'bg-green-900/20 border-green-700'
          }`}>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold text-white mb-1">Portfolio Risk Score</h2>
                <p className="text-slate-400">Aggregated risk across all {portfolioRisk.summary.total_contracts} contracts</p>
              </div>
              <div className="text-right">
                <div className={`text-5xl font-bold mb-1 ${
                  portfolioRisk.severity === 'HIGH' ? 'text-red-400' :
                  portfolioRisk.severity === 'MEDIUM' ? 'text-yellow-400' :
                  'text-green-400'
                }`}>
                  {(portfolioRisk.portfolio_risk_score * 100).toFixed(0)}%
                </div>
                <div className={`px-4 py-1 rounded-full text-sm font-semibold inline-block ${
                  portfolioRisk.severity === 'HIGH' ? 'bg-red-900/40 text-red-300' :
                  portfolioRisk.severity === 'MEDIUM' ? 'bg-yellow-900/40 text-yellow-300' :
                  'bg-green-900/40 text-green-300'
                }`}>
                  {portfolioRisk.severity} RISK
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-slate-900/50 rounded-lg p-4">
                <div className="text-sm text-slate-400 mb-1">Avg Obligation Risk</div>
                <div className="text-2xl font-bold text-white">
                  {(portfolioRisk.summary.avg_obligation_risk * 100).toFixed(0)}%
                </div>
              </div>
              <div className="bg-slate-900/50 rounded-lg p-4">
                <div className="text-sm text-slate-400 mb-1">Avg Rights Risk</div>
                <div className="text-2xl font-bold text-white">
                  {(portfolioRisk.summary.avg_rights_risk * 100).toFixed(0)}%
                </div>
              </div>
              <div className="bg-slate-900/50 rounded-lg p-4">
                <div className="text-sm text-slate-400 mb-1">High Risk Items</div>
                <div className="text-2xl font-bold text-red-400">
                  {portfolioRisk.summary.high_risk_items}
                </div>
              </div>
              <div className="bg-slate-900/50 rounded-lg p-4">
                <div className="text-sm text-slate-400 mb-1">Total Items</div>
                <div className="text-2xl font-bold text-white">
                  {portfolioRisk.summary.total_obligations + portfolioRisk.summary.total_rights}
                </div>
              </div>
            </div>

            {/* Top Risk Contracts */}
            {portfolioRisk.top_risk_contributors.contracts.length > 0 && (
              <div className="mt-6">
                <h3 className="text-lg font-semibold text-white mb-3">Top 5 Riskiest Contracts</h3>
                <div className="space-y-2">
                  {portfolioRisk.top_risk_contributors.contracts.map((contract, idx) => (
                    <div key={idx} className="bg-slate-900/50 rounded-lg p-3 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="text-lg font-bold text-slate-500">#{idx + 1}</div>
                        <div>
                          <div className="text-white font-medium">{contract.filename}</div>
                          <div className="text-sm text-slate-400">
                            Obligations: {(contract.obligation_avg_risk * 100).toFixed(0)}% |
                            Rights: {(contract.rights_avg_risk * 100).toFixed(0)}%
                          </div>
                        </div>
                      </div>
                      <div className={`text-2xl font-bold ${
                        contract.risk_score >= 0.7 ? 'text-red-400' :
                        contract.risk_score >= 0.4 ? 'text-yellow-400' :
                        'text-green-400'
                      }`}>
                        {(contract.risk_score * 100).toFixed(0)}%
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Intent Distribution */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Target className="w-5 h-5" />
              Top Intents Across Portfolio
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={visualizations.intent_distribution.slice(0, 10)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="name"
                  stroke="#94a3b8"
                  angle={-45}
                  textAnchor="end"
                  height={120}
                  fontSize={11}
                />
                <YAxis stroke="#94a3b8" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #475569',
                    borderRadius: '0.5rem'
                  }}
                  labelStyle={{ color: '#fff' }}
                />
                <Bar dataKey="occurrence_count" fill="#3b82f6" name="Occurrences" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Obligation Priority Distribution */}
          {visualizations.obligation_priority.length > 0 && (
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Activity className="w-5 h-5" />
                Obligation Priority Distribution
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={visualizations.obligation_priority}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ priority, count }) => `${priority}: ${count}`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="count"
                  >
                    {visualizations.obligation_priority.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={getPriorityColor(entry.priority)} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Party Exposure - Obligations */}
          {visualizations.obligation_party.length > 0 && (
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Users className="w-5 h-5" />
                Obligations by Party
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={visualizations.obligation_party}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ party, count }) => `${party.replace('_', ' ')}: ${count}`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="count"
                  >
                    {visualizations.obligation_party.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Party Exposure - Rights */}
          {visualizations.rights_party.length > 0 && (
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Rights by Party
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={visualizations.rights_party}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ party, count }) => `${party.replace('_', ' ')}: ${count}`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="count"
                  >
                    {visualizations.rights_party.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Intent Risk Scores */}
        {visualizations.intent_risk_scores.length > 0 && (
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 mb-8">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              Risk Scores by Intent (Top 15)
            </h3>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={visualizations.intent_risk_scores}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="name"
                  stroke="#94a3b8"
                  angle={-45}
                  textAnchor="end"
                  height={150}
                  fontSize={11}
                />
                <YAxis stroke="#94a3b8" domain={[0, 1]} label={{ value: 'Risk Score', angle: -90, position: 'insideLeft', fill: '#94a3b8' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #475569',
                    borderRadius: '0.5rem'
                  }}
                  labelStyle={{ color: '#fff' }}
                  formatter={(value) => value !== null ? value.toFixed(2) : 'N/A'}
                />
                <Legend />
                <Bar dataKey="avg_obligation_risk" fill="#ef4444" name="Avg Obligation Risk" />
                <Bar dataKey="avg_right_risk" fill="#f59e0b" name="Avg Right Risk" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* High Risk Items */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* High Risk Obligations */}
          {high_risk_items.obligations && high_risk_items.obligations.length > 0 && (
            <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
              <div className="px-6 py-4 bg-red-900/20 border-b border-red-800/50">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-red-400" />
                  High Risk Obligations (Top 10)
                </h3>
              </div>
              <div className="divide-y divide-slate-700 max-h-96 overflow-y-auto">
                {high_risk_items.obligations.map((obl, idx) => (
                  <div key={idx} className="p-4 hover:bg-slate-700/30 transition">
                    <div className="flex items-start justify-between mb-2">
                      <span className="text-sm font-medium text-slate-300">{obl.party.replace('_', ' ')}</span>
                      <span className="px-2 py-1 text-xs rounded-full bg-red-900/30 text-red-400 border border-red-700">
                        Risk: {(obl.risk_score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-slate-400 text-sm mb-1">{obl.action}</p>
                    <div className="flex gap-2 mt-2">
                      <span className={`px-2 py-0.5 text-xs rounded-full ${
                        obl.priority === 'HIGH' ? 'bg-red-900/30 text-red-400' :
                        obl.priority === 'MEDIUM' ? 'bg-yellow-900/30 text-yellow-400' :
                        'bg-green-900/30 text-green-400'
                      }`}>
                        {obl.priority}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* High Risk Rights */}
          {high_risk_items.rights && high_risk_items.rights.length > 0 && (
            <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
              <div className="px-6 py-4 bg-orange-900/20 border-b border-orange-800/50">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-orange-400" />
                  High Risk Rights (Top 10)
                </h3>
              </div>
              <div className="divide-y divide-slate-700 max-h-96 overflow-y-auto">
                {high_risk_items.rights.map((right, idx) => (
                  <div key={idx} className="p-4 hover:bg-slate-700/30 transition">
                    <div className="flex items-start justify-between mb-2">
                      <span className="text-sm font-medium text-slate-300">{right.party.replace('_', ' ')}</span>
                      <span className="px-2 py-1 text-xs rounded-full bg-orange-900/30 text-orange-400 border border-orange-700">
                        Risk: {(right.risk_score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-slate-400 text-sm mb-1">{right.entitlement}</p>
                    {right.trigger && (
                      <p className="text-slate-500 text-xs mt-1">
                        <span className="font-semibold">Trigger:</span> {right.trigger}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* No Data State */}
        {summary.total_intents === 0 && (
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-12 text-center">
            <FileText className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">No Intent Data Yet</h3>
            <p className="text-slate-400">
              Start analyzing contracts to see portfolio-wide insights
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default PortfolioAnalytics;
