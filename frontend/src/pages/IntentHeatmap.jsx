import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Target, AlertTriangle, TrendingUp, Info } from 'lucide-react';
import DashboardLayout from '../components/DashboardLayout';
import IntentHeatmapGrid from '../components/IntentHeatmapGrid';
import IntentAlerts from '../components/IntentAlerts';
import IntentLegend from '../components/IntentLegend';
import IntentKnowledgeGraph from '../components/graph/IntentKnowledgeGraph';
import API from '../utils/api';

export default function IntentHeatmap() {
  const { contractId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchIntentHeatmap();
  }, [contractId]);

  const fetchIntentHeatmap = async () => {
    try {
      setLoading(true);
      const response = await API.get(`/contracts/${contractId}/intent-heatmap`);
      setData(response.data);
    } catch (err) {
      console.error('Error fetching intent heatmap:', err);
      setError(err.response?.data?.error || 'Failed to load intent heatmap');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-screen bg-gray-900">
          <div className="text-center">
            <Target className="w-16 h-16 animate-spin text-purple-400 mx-auto mb-4" />
            <p className="text-gray-400 text-lg">Analyzing contract intents...</p>
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
                Contract Intent Mapping
              </h1>
              <p className="text-xl text-gray-300">{data.contract_name}</p>
              <p className="text-sm text-gray-500 mt-1">
                {data.total_clauses} clauses analyzed
              </p>
            </div>

            {/* Bias Badge */}
            <div className={`px-6 py-3 rounded-lg ${
              data.counterparty_mismatch.level === 'HIGH'
                ? 'bg-red-900/30 border border-red-500/50'
                : data.counterparty_mismatch.level === 'MEDIUM'
                ? 'bg-yellow-900/30 border border-yellow-500/50'
                : 'bg-green-900/30 border border-green-500/50'
            }`}>
              <div className="text-center">
                <p className="text-xs uppercase tracking-wide mb-1 text-gray-400">
                  Counterparty Bias
                </p>
                <p className={`text-2xl font-bold ${
                  data.counterparty_mismatch.level === 'HIGH' ? 'text-red-400' :
                  data.counterparty_mismatch.level === 'MEDIUM' ? 'text-yellow-400' :
                  'text-green-400'
                }`}>
                  {data.counterparty_mismatch.level}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Score: {(data.counterparty_mismatch.score * 100).toFixed(0)}%
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Alerts */}
        <IntentAlerts
          intentDrift={data.intent_drift}
          counterpartyMismatch={data.counterparty_mismatch}
        />

        {/* Info Card */}
        {data.message && (
          <div className="mb-6 bg-blue-900/20 border border-blue-500/30 rounded-lg p-4 flex items-start">
            <Info className="w-5 h-5 text-blue-400 mr-3 mt-1 flex-shrink-0" />
            <div>
              <p className="text-blue-400 font-semibold mb-1">Information</p>
              <p className="text-gray-300 text-sm">{data.message}</p>
            </div>
          </div>
        )}

        {/* Legend */}
        <IntentLegend />

        {/* Heatmap Grid */}
        {data.rows && data.rows.length > 0 ? (
          <IntentHeatmapGrid rows={data.rows} />
        ) : (
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-8 text-center">
            <Target className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400 text-lg mb-2">No Intent Data Available</p>
            <p className="text-gray-500 text-sm">
              Extract clauses from this contract to generate intent analysis.
            </p>
          </div>
        )}

        {/* Aggregate Stats */}
        {data.aggregate_intents && Object.keys(data.aggregate_intents).length > 0 && (
          <div className="mt-6 bg-gray-800 border border-gray-700 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
              <TrendingUp className="w-5 h-5 mr-2 text-purple-400" />
              Aggregate Intent Profile
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {Object.entries(data.aggregate_intents).map(([intent, score]) => (
                <div key={intent} className="bg-gray-900/50 rounded-lg p-4">
                  <p className="text-xs text-gray-500 mb-1 capitalize">
                    {intent.replace(/_/g, ' ')}
                  </p>
                  <p className="text-2xl font-bold text-white">
                    {(score * 100).toFixed(0)}%
                  </p>
                  <div className="mt-2 h-1 bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${
                        score > 0.7 ? 'bg-red-500' :
                        score > 0.4 ? 'bg-yellow-500' :
                        'bg-green-500'
                      }`}
                      style={{ width: `${score * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Neo4j-Style Intent Knowledge Graph */}
        {data.rows && data.rows.length > 0 && (
          <IntentKnowledgeGraph heatmapData={data} />
        )}
      </div>
    </DashboardLayout>
  );
}
