import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_BASE_URL = (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));

const NegotiationHeatMap = () => {
  const { contractId } = useParams();
  const navigate = useNavigate();
  const [heatData, setHeatData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (contractId) {
      fetchContractHeatMap();
    } else {
      fetchPortfolioHeatStats();
    }
  }, [contractId]);

  const fetchContractHeatMap = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API_BASE_URL}/api/contracts/${contractId}/heat-map/`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setHeatData(response.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching heat map:', err);
      setError(err.response?.data?.error || 'Failed to load heat map');
    } finally {
      setLoading(false);
    }
  };

  const fetchPortfolioHeatStats = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API_BASE_URL}/api/heat/portfolio-stats/`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setHeatData({
        ...response.data,
        clauses: response.data.hottest_clauses || []
      });
      setError(null);
    } catch (err) {
      console.error('Error fetching portfolio heat:', err);
      setError(err.response?.data?.error || 'Failed to load portfolio heat');
    } finally {
      setLoading(false);
    }
  };

  const getHeatColor = (heat) => {
    if (heat >= 0.8) return '#dc2626';
    if (heat >= 0.6) return '#ef4444';
    if (heat >= 0.4) return '#f59e0b';
    if (heat >= 0.2) return '#fbbf24';
    return '#10b981';
  };

  const getHeatIcon = (level) => {
    switch (level) {
      case 'CRITICAL': return '🔥🔥🔥';
      case 'HIGH': return '🔥🔥';
      case 'MEDIUM': return '🔥';
      case 'LOW': return '⚠️';
      default: return '✅';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading heat map...</p>
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

  if (!heatData) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-100">Negotiation Heat Map</h1>
          <p className="text-gray-400 mt-1">
            {contractId ? 'Contract-level heat analysis' : 'Portfolio-wide heat analysis'}
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="text-sm text-gray-400 mb-1">Total Clauses</div>
            <div className="text-2xl font-bold text-gray-100">{heatData.total_clauses || 0}</div>
          </div>

          <div className="bg-gray-800 rounded-lg p-4 border border-orange-700">
            <div className="text-sm text-gray-400 mb-1">Average Heat</div>
            <div className="text-2xl font-bold text-orange-400">
              {((heatData.avg_heat || 0) * 100).toFixed(0)}%
            </div>
          </div>

          {heatData.distribution && (
            <>
              <div className="bg-gray-800 rounded-lg p-4 border border-red-700">
                <div className="text-sm text-gray-400 mb-1">Critical Heat</div>
                <div className="text-2xl font-bold text-red-400">{heatData.distribution.critical}</div>
              </div>

              <div className="bg-gray-800 rounded-lg p-4 border border-orange-700">
                <div className="text-sm text-gray-400 mb-1">High Heat</div>
                <div className="text-2xl font-bold text-orange-400">{heatData.distribution.high}</div>
              </div>
            </>
          )}

          {heatData.hot_clause_count !== undefined && (
            <div className="bg-gray-800 rounded-lg p-4 border border-red-700">
              <div className="text-sm text-gray-400 mb-1">Hot Clauses</div>
              <div className="text-2xl font-bold text-red-400">{heatData.hot_clause_count}</div>
            </div>
          )}
        </div>

        {/* Heat Distribution */}
        {heatData.distribution && (
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-6">
            <h3 className="text-lg font-semibold text-gray-200 mb-4">Heat Distribution</h3>
            <div className="grid grid-cols-4 gap-4">
              {Object.entries(heatData.distribution).map(([level, count]) => (
                <div key={level} className="text-center">
                  <div className="text-3xl mb-2">
                    {getHeatIcon(level.toUpperCase())}
                  </div>
                  <div className="text-2xl font-bold text-gray-200">{count}</div>
                  <div className="text-xs text-gray-400 mt-1">{level.toUpperCase()}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Clause Heat Map */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-gray-200 mb-4">
            Clause Heat Details ({heatData.clauses?.length || 0})
          </h3>

          {heatData.clauses && heatData.clauses.length > 0 ? (
            <div className="space-y-3">
              {heatData.clauses.map((clause) => (
                <div
                  key={clause.clause_id}
                  className="bg-gray-900/50 rounded-lg p-4 border border-gray-700 hover:border-orange-500 transition-colors cursor-pointer"
                  onClick={() => navigate(`/clauses/${clause.clause_id}/heat`)}
                  style={{
                    borderLeftWidth: '4px',
                    borderLeftColor: getHeatColor(clause.heat_score)
                  }}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="text-2xl">{getHeatIcon(clause.heat_level)}</div>
                      <div>
                        <div className="text-sm font-medium text-gray-200">
                          Clause {clause.clause_id}
                        </div>
                        <div className="text-xs text-gray-400">
                          {clause.total_rounds} rounds | {clause.loop_analysis?.loop_count || 0} loops
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div
                        className="text-lg font-bold"
                        style={{ color: getHeatColor(clause.heat_score) }}
                      >
                        {(clause.heat_score * 100).toFixed(0)}%
                      </div>
                      <div className="text-xs text-gray-400">{clause.heat_level}</div>
                    </div>
                  </div>

                  {/* Heat Breakdown */}
                  <div className="grid grid-cols-3 gap-3 text-xs">
                    <div>
                      <span className="text-gray-400">Emotion:</span>
                      <span className="ml-2 text-gray-200">
                        {((clause.emotion_analysis?.current_friction || 0) * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-400">Loops:</span>
                      <span className="ml-2 text-gray-200">
                        {clause.loop_analysis?.loop_count || 0}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-400">Stall Risk:</span>
                      <span className="ml-2 text-gray-200">
                        {((clause.stall_probability || 0) * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>

                  {/* Explosion Risk Alert */}
                  {clause.explosion_risk && clause.explosion_risk.risk_level !== 'LOW' && (
                    <div className="mt-3 p-2 bg-red-900/20 border border-red-700 rounded text-xs text-red-400">
                      💥 {clause.explosion_risk.recommendation}
                    </div>
                  )}

                  {/* Deal Velocity */}
                  {clause.deal_velocity && (
                    <div className="mt-2 text-xs text-gray-400">
                      ⏱️ Estimated: {clause.deal_velocity.estimated_days} days ({clause.deal_velocity.velocity})
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-400">
              No negotiation data available
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default NegotiationHeatMap;
