import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import TrustScoreCard from '../components/trust/TrustScoreCard';
import TrustRadarChart from '../components/trust/TrustRadarChart';
import TrustBreakdown from '../components/trust/TrustBreakdown';
import TrustBadge from '../components/trust/TrustBadge';

const API_BASE_URL = (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));

const ClauseTrustDashboard = () => {
  const { clauseId } = useParams();
  const [trustData, setTrustData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    fetchTrustScore();
  }, [clauseId]);

  const fetchTrustScore = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API_BASE_URL}/api/clauses/${clauseId}/trust/`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setTrustData(response.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching trust score:', err);
      setError(err.response?.data?.error || 'Failed to load trust score');
    } finally {
      setLoading(false);
    }
  };

  const handleRecalculate = async () => {
    try {
      setUpdating(true);
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_BASE_URL}/api/clauses/${clauseId}/trust/update/`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setTrustData(response.data.trust_data);
      setError(null);
    } catch (err) {
      console.error('Error updating trust score:', err);
      setError(err.response?.data?.error || 'Failed to update trust score');
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading trust score...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 text-gray-100 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-900/20 border border-red-500 rounded-lg p-4">
            <p className="text-red-400">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!trustData) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-100">Clause Trust Score</h1>
            <p className="text-gray-400 mt-1">Outcome-based trust analysis</p>
          </div>
          <button
            onClick={handleRecalculate}
            disabled={updating}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded-lg transition-colors flex items-center gap-2"
          >
            {updating ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Recalculating...
              </>
            ) : (
              <>
                🔄 Recalculate Trust Score
              </>
            )}
          </button>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          {/* Trust Score Card */}
          <div className="lg:col-span-1">
            <TrustScoreCard trustData={trustData} />
          </div>

          {/* Trust Radar Chart */}
          <div className="lg:col-span-2">
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-lg font-semibold text-gray-200 mb-4">Trust Dimensions</h3>
              <TrustRadarChart trustData={trustData} />
            </div>
          </div>
        </div>

        {/* Trust Breakdown */}
        <div className="mb-6">
          <TrustBreakdown breakdown={trustData.breakdown} />
        </div>

        {/* Recommendations & Factors */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recommendation */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-gray-200 mb-4">💡 Recommendation</h3>
            <p className="text-gray-300 mb-4">{trustData.recommendation}</p>

            {trustData.alternatives && trustData.alternatives.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-gray-400 mb-2">Alternative Actions:</h4>
                <ul className="space-y-2">
                  {trustData.alternatives.map((alt, idx) => (
                    <li key={idx} className="text-sm text-gray-300 flex items-start gap-2">
                      <span className="text-blue-400">→</span>
                      {alt}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Factors */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-gray-200 mb-4">📊 Key Factors</h3>

            {/* Enforceability Factors */}
            {trustData.enforceability_factors && (
              <div className="mb-4">
                <h4 className="text-sm font-semibold text-gray-400 mb-2">Enforceability:</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-gray-400">Status:</span>
                    <span className="ml-2 text-gray-200">{trustData.enforceability_factors.status}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Sample Size:</span>
                    <span className="ml-2 text-gray-200">{trustData.enforceability_factors.sample_size}</span>
                  </div>
                  {trustData.enforceability_factors.win_rate !== null && (
                    <>
                      <div>
                        <span className="text-gray-400">Win Rate:</span>
                        <span className="ml-2 text-gray-200">
                          {(trustData.enforceability_factors.win_rate * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-400">Avg Outcome:</span>
                        <span className="ml-2 text-gray-200">
                          {(trustData.enforceability_factors.avg_outcome * 100).toFixed(0)}%
                        </span>
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}

            {/* Negotiability Factors */}
            {trustData.negotiability_factors && (
              <div className="mb-4">
                <h4 className="text-sm font-semibold text-gray-400 mb-2">Negotiability:</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-gray-400">Status:</span>
                    <span className="ml-2 text-gray-200">{trustData.negotiability_factors.status}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Total Outcomes:</span>
                    <span className="ml-2 text-gray-200">{trustData.negotiability_factors.total_outcomes}</span>
                  </div>
                  {trustData.negotiability_factors.dispute_rate !== null && (
                    <>
                      <div>
                        <span className="text-gray-400">Dispute Rate:</span>
                        <span className="ml-2 text-gray-200">
                          {(trustData.negotiability_factors.dispute_rate * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-400">Closure Rate:</span>
                        <span className="ml-2 text-gray-200">
                          {(trustData.negotiability_factors.closure_rate * 100).toFixed(0)}%
                        </span>
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}

            {/* Ambiguous Terms */}
            {trustData.ambiguous_terms && trustData.ambiguous_terms.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-gray-400 mb-2">Ambiguous Terms Found:</h4>
                <div className="flex flex-wrap gap-2">
                  {trustData.ambiguous_terms.map((term, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-1 bg-yellow-900/30 text-yellow-400 rounded text-xs border border-yellow-700"
                    >
                      {term}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Outcome History */}
        {trustData.outcome_count > 0 && (
          <div className="mt-6 bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-gray-200 mb-2">📈 Outcome History</h3>
            <p className="text-sm text-gray-400">
              This clause has {trustData.outcome_count} recorded outcome{trustData.outcome_count !== 1 ? 's' : ''}.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ClauseTrustDashboard;
