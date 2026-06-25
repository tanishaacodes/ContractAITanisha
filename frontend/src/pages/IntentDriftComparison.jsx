import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Plus,
  Minus,
  Edit,
  CheckCircle,
  Loader2,
  Activity,
  Shield,
  Target,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';
import api from '../utils/api';

const IntentDriftComparison = () => {
  const { contractId, version1Id, version2Id } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [driftData, setDriftData] = useState(null);

  useEffect(() => {
    loadDriftComparison();
  }, [contractId, version1Id, version2Id]);

  const loadDriftComparison = async () => {
    try {
      setLoading(true);
      setError('');

      const response = await api.get(
        `/contracts/${contractId}/versions/${version1Id}/compare/${version2Id}`
      );

      setDriftData(response.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load drift comparison');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getDriftSeverityColor = (score) => {
    if (score >= 0.7) return 'text-red-400 bg-red-900/30 border-red-700';
    if (score >= 0.3) return 'text-yellow-400 bg-yellow-900/30 border-yellow-700';
    return 'text-green-400 bg-green-900/30 border-green-700';
  };

  const getRiskDeltaColor = (delta) => {
    if (delta > 0.1) return 'text-red-400';
    if (delta < -0.1) return 'text-green-400';
    return 'text-slate-400';
  };

  const getRiskDeltaIcon = (delta) => {
    if (delta > 0.01) return <TrendingUp className="w-4 h-4" />;
    if (delta < -0.01) return <TrendingDown className="w-4 h-4" />;
    return <Activity className="w-4 h-4" />;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-900">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-slate-400">Analyzing intent drift...</p>
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

  if (!driftData || !driftData.success) {
    return null;
  }

  const {
    version1,
    version2,
    overall_drift_score,
    intent_drift,
    obligation_drift,
    right_drift,
    risk_delta,
    summary,
  } = driftData;

  // Prepare drift distribution data for chart
  const driftDistribution = [
    { name: 'Intents', changes: intent_drift.change_count, total: Math.max(intent_drift.total_v1, intent_drift.total_v2) },
    { name: 'Obligations', changes: obligation_drift.change_count, total: Math.max(obligation_drift.total_v1, obligation_drift.total_v2) },
    { name: 'Rights', changes: right_drift.change_count, total: Math.max(right_drift.total_v1, right_drift.total_v2) },
  ];

  // Prepare radar chart data
  const radarData = [
    {
      category: 'Intents',
      v1: intent_drift.total_v1,
      v2: intent_drift.total_v2,
    },
    {
      category: 'Obligations',
      v1: obligation_drift.total_v1,
      v2: obligation_drift.total_v2,
    },
    {
      category: 'Rights',
      v1: right_drift.total_v1,
      v2: right_drift.total_v2,
    },
  ];

  return (
    <div className="min-h-screen bg-slate-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate(`/contract/${contractId}/clauses`)}
            className="flex items-center gap-2 text-slate-400 hover:text-white mb-4 transition"
          >
            <ArrowLeft size={20} />
            Back to Contract
          </button>

          <h1 className="text-3xl font-bold text-white mb-2">Intent Drift Analysis</h1>
          <p className="text-slate-400">
            Comparing version {version1.version_number} vs version {version2.version_number}
          </p>
        </div>

        {/* Summary Card */}
        <div className={`rounded-xl p-6 mb-6 border ${getDriftSeverityColor(overall_drift_score)}`}>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-2xl font-bold mb-2">{summary}</h2>
              <p className="text-sm opacity-80">
                Version {version1.version_number} ({new Date(version1.created_at).toLocaleDateString()}) →
                Version {version2.version_number} ({new Date(version2.created_at).toLocaleDateString()})
              </p>
            </div>
            <div className="text-right">
              <div className="text-4xl font-bold mb-1">{(overall_drift_score * 100).toFixed(0)}%</div>
              <div className="text-sm opacity-80">Drift Score</div>
            </div>
          </div>

          {/* Risk Delta */}
          <div className="flex items-center gap-4 pt-4 border-t border-current/30">
            <div className="flex items-center gap-2">
              {getRiskDeltaIcon(risk_delta.delta)}
              <span className="font-semibold">Risk Change:</span>
            </div>
            <div className={`flex items-center gap-2 ${getRiskDeltaColor(risk_delta.delta)}`}>
              <span className="text-lg font-bold">
                {risk_delta.delta > 0 ? '+' : ''}
                {(risk_delta.delta * 100).toFixed(1)}%
              </span>
              <span className="text-sm opacity-80">
                ({(risk_delta.previous_risk * 100).toFixed(1)}% → {(risk_delta.current_risk * 100).toFixed(1)}%)
              </span>
            </div>
            <div className="ml-auto">
              <span
                className={`px-3 py-1 rounded-full text-sm font-semibold ${
                  risk_delta.direction === 'INCREASED'
                    ? 'bg-red-900/30 text-red-400'
                    : risk_delta.direction === 'DECREASED'
                    ? 'bg-green-900/30 text-green-400'
                    : 'bg-slate-700 text-slate-300'
                }`}
              >
                {risk_delta.direction}
              </span>
            </div>
          </div>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Drift Distribution */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5" />
              Change Distribution
            </h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={driftDistribution}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #475569',
                    borderRadius: '0.5rem',
                  }}
                  labelStyle={{ color: '#fff' }}
                />
                <Legend />
                <Bar dataKey="changes" fill="#ef4444" name="Changes" />
                <Bar dataKey="total" fill="#3b82f6" name="Total Items" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Version Comparison Radar */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Target className="w-5 h-5" />
              Version Comparison
            </h3>
            <ResponsiveContainer width="100%" height={250}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#475569" />
                <PolarAngleAxis dataKey="category" stroke="#94a3b8" />
                <PolarRadiusAxis stroke="#94a3b8" />
                <Radar name={`v${version1.version_number}`} dataKey="v1" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
                <Radar name={`v${version2.version_number}`} dataKey="v2" stroke="#10b981" fill="#10b981" fillOpacity={0.3} />
                <Legend />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Intent Changes */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden mb-6">
          <div className="px-6 py-4 border-b border-slate-700">
            <h2 className="text-xl font-semibold text-white flex items-center gap-2">
              <Target className="w-6 h-6" />
              Intent Changes
            </h2>
          </div>

          <div className="p-6 space-y-6">
            {/* Added Intents */}
            {intent_drift.added && intent_drift.added.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Plus className="w-5 h-5 text-green-400" />
                  <h3 className="text-lg font-semibold text-green-400">
                    Added Intents ({intent_drift.added.length})
                  </h3>
                </div>
                <div className="space-y-2">
                  {intent_drift.added.map((intent, idx) => (
                    <div key={idx} className="bg-green-900/20 border border-green-700 rounded-lg p-3">
                      <div className="flex items-center justify-between">
                        <span className="text-white font-medium">{intent.intent_name}</span>
                        <span className="text-sm text-green-400">
                          Confidence: {(intent.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p className="text-sm text-slate-400 mt-1">{intent.clause}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Removed Intents */}
            {intent_drift.removed && intent_drift.removed.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Minus className="w-5 h-5 text-red-400" />
                  <h3 className="text-lg font-semibold text-red-400">
                    Removed Intents ({intent_drift.removed.length})
                  </h3>
                </div>
                <div className="space-y-2">
                  {intent_drift.removed.map((intent, idx) => (
                    <div key={idx} className="bg-red-900/20 border border-red-700 rounded-lg p-3">
                      <div className="flex items-center justify-between">
                        <span className="text-white font-medium">{intent.intent_name}</span>
                        <span className="text-sm text-red-400">
                          Confidence: {(intent.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p className="text-sm text-slate-400 mt-1">{intent.clause}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Modified Intents */}
            {intent_drift.modified && intent_drift.modified.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Edit className="w-5 h-5 text-yellow-400" />
                  <h3 className="text-lg font-semibold text-yellow-400">
                    Modified Intents ({intent_drift.modified.length})
                  </h3>
                </div>
                <div className="space-y-2">
                  {intent_drift.modified.map((intent, idx) => (
                    <div key={idx} className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-white font-medium">{intent.intent_name}</span>
                        <span className="text-sm text-yellow-400">
                          Similarity: {(intent.similarity * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div>
                          <div className="text-slate-500">Version {version1.version_number}:</div>
                          <div className="text-slate-300">Confidence: {(intent.v1_confidence * 100).toFixed(0)}%</div>
                          <div className="text-slate-400 text-xs mt-1">{intent.clause_v1}</div>
                        </div>
                        <div>
                          <div className="text-slate-500">Version {version2.version_number}:</div>
                          <div className="text-slate-300">Confidence: {(intent.v2_confidence * 100).toFixed(0)}%</div>
                          <div className="text-slate-400 text-xs mt-1">{intent.clause_v2}</div>
                        </div>
                      </div>
                      <div className="mt-2 text-sm">
                        <span className={`font-semibold ${getRiskDeltaColor(intent.confidence_change)}`}>
                          Confidence Change: {intent.confidence_change > 0 ? '+' : ''}
                          {(intent.confidence_change * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Unchanged Intents */}
            {intent_drift.unchanged && intent_drift.unchanged.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <CheckCircle className="w-5 h-5 text-slate-400" />
                  <h3 className="text-lg font-semibold text-slate-400">
                    Unchanged Intents ({intent_drift.unchanged.length})
                  </h3>
                </div>
                <div className="text-sm text-slate-500">
                  {intent_drift.unchanged.length} intents remained consistent between versions
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Risk Breakdown Details */}
        {risk_delta && risk_delta.breakdown && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Obligations Risk Delta */}
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5" />
                Obligations Risk Change
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Previous Risk:</span>
                  <span className="text-white font-semibold">
                    {(risk_delta.breakdown.obligations.previous * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Current Risk:</span>
                  <span className="text-white font-semibold">
                    {(risk_delta.breakdown.obligations.current * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between items-center pt-3 border-t border-slate-700">
                  <span className="text-slate-400">Change:</span>
                  <span className={`font-bold ${getRiskDeltaColor(risk_delta.breakdown.obligations.delta)}`}>
                    {risk_delta.breakdown.obligations.delta > 0 ? '+' : ''}
                    {(risk_delta.breakdown.obligations.delta * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>

            {/* Rights Risk Delta */}
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Rights Risk Change
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Previous Risk:</span>
                  <span className="text-white font-semibold">
                    {(risk_delta.breakdown.rights.previous * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Current Risk:</span>
                  <span className="text-white font-semibold">
                    {(risk_delta.breakdown.rights.current * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between items-center pt-3 border-t border-slate-700">
                  <span className="text-slate-400">Change:</span>
                  <span className={`font-bold ${getRiskDeltaColor(risk_delta.breakdown.rights.delta)}`}>
                    {risk_delta.breakdown.rights.delta > 0 ? '+' : ''}
                    {(risk_delta.breakdown.rights.delta * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default IntentDriftComparison;
