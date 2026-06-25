import { useState, useEffect } from 'react';
import {
  AlertTriangle,
  Shield,
  BarChart3,
  Loader2,
  TrendingUp,
  CheckCircle,
  XCircle,
  AlertCircle,
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
  LineChart,
  Line,
} from 'recharts';
import api from '../utils/api';

const ComplianceDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dashboard, setDashboard] = useState(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const response = await api.get('/compliance/dashboard');
      setDashboard(response.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load compliance dashboard');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const FRAMEWORK_COLORS = {
    GDPR: '#3b82f6',
    SOX: '#8b5cf6',
    HIPAA: '#ec4899',
    GST: '#f59e0b',
  };

  const CRITICALITY_COLORS = {
    CRITICAL: '#ef4444',
    HIGH: '#f97316',
    MEDIUM: '#f59e0b',
    LOW: '#10b981',
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

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-400';
    if (score >= 60) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getScoreBgColor = (score) => {
    if (score >= 80) return 'bg-green-900/30 border-green-700/50';
    if (score >= 60) return 'bg-yellow-900/30 border-yellow-700/50';
    return 'bg-red-900/30 border-red-700/50';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-900">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-slate-400">Loading compliance dashboard...</p>
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

  if (!dashboard) {
    return null;
  }

  const {
    total_contracts_analyzed = 0,
    avg_compliance_score = 0,
    total_violations = 0,
    critical_violations = 0,
    frameworks_tracked = 0,
    framework_distribution = [],
    violation_breakdown = [],
    high_risk_contracts = [],
  } = dashboard;

  // Prepare data for framework scores chart
  const frameworkScoresData = Object.entries(dashboard.framework_scores || {}).map(([code, data]) => ({
    name: code,
    score: parseFloat((data.score || 0).toFixed(1)),
    coverage: data.coverage || 0,
  }));

  return (
    <div className="min-h-screen bg-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Compliance Dashboard</h1>
          <p className="text-slate-400">
            Portfolio-wide compliance tracking across GDPR, SOX, HIPAA, and GST frameworks
          </p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
          {/* Total Contracts */}
          <div className="bg-gradient-to-br from-blue-900/30 to-blue-800/20 border border-blue-700/50 rounded-lg p-5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-blue-400">Contracts Analyzed</span>
              <Shield className="w-5 h-5 text-blue-400" />
            </div>
            <div className="text-3xl font-bold text-white">{total_contracts_analyzed}</div>
          </div>

          {/* Avg Compliance Score */}
          <div className={`bg-gradient-to-br ${getScoreBgColor(avg_compliance_score)} border rounded-lg p-5`}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-slate-300">Avg Compliance</span>
              <TrendingUp className="w-5 h-5" />
            </div>
            <div className={`text-3xl font-bold ${getScoreColor(avg_compliance_score)}`}>
              {parseFloat(avg_compliance_score.toFixed(1))}%
            </div>
          </div>

          {/* Total Violations */}
          <div className="bg-gradient-to-br from-orange-900/30 to-orange-800/20 border border-orange-700/50 rounded-lg p-5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-orange-400">Total Violations</span>
              <AlertCircle className="w-5 h-5 text-orange-400" />
            </div>
            <div className="text-3xl font-bold text-white">{total_violations}</div>
          </div>

          {/* Critical Violations */}
          <div className="bg-gradient-to-br from-red-900/30 to-red-800/20 border border-red-700/50 rounded-lg p-5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-red-400">Critical</span>
              <AlertTriangle className="w-5 h-5 text-red-400" />
            </div>
            <div className="text-3xl font-bold text-white">{critical_violations}</div>
          </div>

          {/* Frameworks Tracked */}
          <div className="bg-gradient-to-br from-purple-900/30 to-purple-800/20 border border-purple-700/50 rounded-lg p-5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-purple-400">Frameworks</span>
              <BarChart3 className="w-5 h-5 text-purple-400" />
            </div>
            <div className="text-3xl font-bold text-white">{frameworks_tracked}</div>
          </div>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Framework Distribution */}
          {framework_distribution && framework_distribution.length > 0 && (
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Framework Distribution
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={framework_distribution}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, count }) => `${name}: ${count}`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="count"
                  >
                    {framework_distribution.map((entry) => (
                      <Cell key={`cell-${entry.name}`} fill={FRAMEWORK_COLORS[entry.name]} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Framework Scores */}
          {frameworkScoresData && frameworkScoresData.length > 0 && (
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                Framework Compliance Scores
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={frameworkScoresData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="name" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" domain={[0, 100]} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      border: '1px solid #475569',
                      borderRadius: '0.5rem'
                    }}
                    labelStyle={{ color: '#fff' }}
                  />
                  <Bar dataKey="score" fill="#3b82f6" name="Compliance Score" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Violation Breakdown */}
          {violation_breakdown && violation_breakdown.length > 0 && (
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5" />
                Violations by Criticality
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={violation_breakdown}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="criticality" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      border: '1px solid #475569',
                      borderRadius: '0.5rem'
                    }}
                    labelStyle={{ color: '#fff' }}
                  />
                  <Bar dataKey="count" fill="#ef4444" name="Violation Count" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* High Risk Contracts Table */}
        {high_risk_contracts && high_risk_contracts.length > 0 && (
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5" />
              High-Risk Contracts
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-600">
                    <th className="text-left py-3 px-4 text-slate-300 font-semibold">Contract</th>
                    <th className="text-left py-3 px-4 text-slate-300 font-semibold">Compliance Score</th>
                    <th className="text-left py-3 px-4 text-slate-300 font-semibold">Critical</th>
                    <th className="text-left py-3 px-4 text-slate-300 font-semibold">Risk Score</th>
                    <th className="text-left py-3 px-4 text-slate-300 font-semibold">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {high_risk_contracts.map((contract, idx) => (
                    <tr key={idx} className="border-b border-slate-700 hover:bg-slate-700/50">
                      <td className="py-3 px-4 text-slate-200">{contract.original_filename}</td>
                      <td className="py-3 px-4">
                        <div className={`inline-block px-2 py-1 rounded text-sm font-semibold ${getScoreColor(contract.compliance_score)} ${getScoreBgColor(contract.compliance_score)}`}>
                          {parseFloat(contract.compliance_score.toFixed(1))}%
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <span className="inline-block px-2 py-1 rounded text-sm font-semibold bg-red-900/30 text-red-300">
                          {contract.critical_violations}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span className="text-slate-300">{parseFloat((contract.risk_score * 100).toFixed(1))}%</span>
                      </td>
                      <td className="py-3 px-4">
                        {contract.compliance_score >= 80 ? (
                          <span className="flex items-center gap-1 text-green-400">
                            <CheckCircle size={16} /> Compliant
                          </span>
                        ) : contract.compliance_score >= 60 ? (
                          <span className="flex items-center gap-1 text-yellow-400">
                            <AlertCircle size={16} /> At Risk
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-red-400">
                            <XCircle size={16} /> Non-Compliant
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ComplianceDashboard;
