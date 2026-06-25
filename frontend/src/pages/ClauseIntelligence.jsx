import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, TrendingUp, Activity, AlertTriangle, BarChart3, Info } from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';
import ClauseTimeline from '../components/ClauseTimeline';
import DriftGauge from '../components/DriftGauge';
import ClauseMetrics from '../components/ClauseMetrics';
import API from '../utils/api';

export default function ClauseIntelligence() {
  const { clauseId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchClauseDrift();
  }, [clauseId]);

  const fetchClauseDrift = async () => {
    try {
      setLoading(true);
      const response = await API.get(`/clauses/${clauseId}/drift`);
      setData(response.data);
    } catch (err) {
      console.error('Error fetching clause drift:', err);
      setError(err.response?.data?.error || 'Failed to load clause intelligence');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-screen bg-gray-900">
          <div className="text-center">
            <Activity className="w-16 h-16 animate-spin text-cyan-400 mx-auto mb-4" />
            <p className="text-gray-400 text-lg">Analyzing clause drift patterns...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-screen bg-gray-900">
          <div className="text-center">
            <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-4" />
            <p className="text-red-400 text-lg mb-4">{error}</p>
            <button
              onClick={() => navigate(-1)}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition"
            >
              Go Back
            </button>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (!data) return null;

  // Determine risk color based on drift probability
  const getDriftColor = (drift) => {
    if (drift < 0.4) return 'text-green-400';
    if (drift < 0.7) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getDriftBadge = (drift) => {
    if (drift < 0.4) return 'bg-green-900/50 text-green-400';
    if (drift < 0.7) return 'bg-yellow-900/50 text-yellow-400';
    return 'bg-red-900/50 text-red-400';
  };

  return (
    <DashboardLayout>
      <div className="min-h-screen bg-gray-900 p-6">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center text-gray-400 hover:text-gray-200 mb-4 transition"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            Back to Contract
          </button>

          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">
                Clause Intelligence
              </h1>
              <p className="text-xl text-gray-300">{data.clause_name}</p>
              <p className="text-sm text-gray-500 mt-1">Clause Type: {data.clause_type}</p>
            </div>

            {/* Drift Badge */}
            <div className={`px-6 py-3 rounded-lg ${getDriftBadge(data.drift_probability)}`}>
              <div className="text-center">
                <p className="text-xs uppercase tracking-wide mb-1">Drift Probability</p>
                <p className="text-3xl font-bold">
                  {(data.drift_probability * 100).toFixed(0)}%
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Alert for Pristine Clause */}
        {data.is_pristine && (
          <div className="mb-6 bg-blue-900/30 border border-blue-500/50 rounded-lg p-4 flex items-start">
            <Info className="w-5 h-5 text-blue-400 mr-3 mt-1 flex-shrink-0" />
            <div>
              <p className="text-blue-400 font-semibold mb-1">No Modification History</p>
              <p className="text-gray-300 text-sm">
                {data.message || "This clause has not been modified yet. Drift metrics show potential risk based on clause type and content."}
              </p>
            </div>
          </div>
        )}

        {/* Alert for High Drift */}
        {!data.is_pristine && data.drift_probability > 0.7 && (
          <div className="mb-6 bg-red-900/30 border border-red-500/50 rounded-lg p-4 flex items-start">
            <AlertTriangle className="w-5 h-5 text-red-400 mr-3 mt-1 flex-shrink-0" />
            <div>
              <p className="text-red-400 font-semibold mb-1">High Drift Detected</p>
              <p className="text-gray-300 text-sm">
                This clause has significantly deviated from its original version. Review changes carefully
                and consider whether drift increases risk exposure.
              </p>
            </div>
          </div>
        )}

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Timeline (2/3 width) */}
          <div className="lg:col-span-2">
            <ClauseTimeline data={data} />
          </div>

          {/* Right Column - Metrics (1/3 width) */}
          <div className="space-y-6">
            {/* Drift Gauge */}
            <DriftGauge value={data.drift_probability * 100} />

            {/* Metrics Panel */}
            <ClauseMetrics data={data} />

            {/* Risk Info Card */}
            {data.risk_score && (
              <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
                <div className="flex items-center text-gray-300 mb-3">
                  <BarChart3 className="w-5 h-5 mr-2" />
                  <h3 className="font-semibold">Current Risk Profile</h3>
                </div>

                <div className="space-y-3">
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Risk Score</p>
                    <div className="flex items-center justify-between">
                      <p className="text-2xl font-bold text-white">
                        {(data.risk_score * 100).toFixed(0)}
                      </p>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-semibold ${
                          data.risk_level === 'HIGH'
                            ? 'bg-red-900/50 text-red-400'
                            : data.risk_level === 'MEDIUM'
                            ? 'bg-yellow-900/50 text-yellow-400'
                            : 'bg-green-900/50 text-green-400'
                        }`}
                      >
                        {data.risk_level || 'UNKNOWN'}
                      </span>
                    </div>
                  </div>

                  <div>
                    <p className="text-xs text-gray-500 mb-1">Version Count</p>
                    <p className="text-lg font-semibold text-gray-300">
                      {data.version_count} {data.version_count === 1 ? 'version' : 'versions'}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer Stats */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard
            icon={TrendingUp}
            label="Drift Probability"
            value={`${(data.drift_probability * 100).toFixed(1)}%`}
            color={getDriftColor(data.drift_probability)}
          />
          <StatCard
            icon={Activity}
            label="Volatility Index"
            value={data.volatility_index.toFixed(2)}
            color="text-blue-400"
          />
          <StatCard
            icon={BarChart3}
            label="Historical Deviation"
            value={`${data.historical_deviation_pct}%`}
            color="text-purple-400"
          />
          <StatCard
            icon={AlertTriangle}
            label="Counterparty Bias"
            value={data.counterparty_bias.toFixed(2)}
            color="text-orange-400"
          />
        </div>
      </div>
    </DashboardLayout>
  );
}

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
      <div className="flex items-center text-gray-400 mb-2">
        <Icon className="w-4 h-4 mr-2" />
        <p className="text-xs uppercase tracking-wide">{label}</p>
      </div>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
    </div>
  );
}
