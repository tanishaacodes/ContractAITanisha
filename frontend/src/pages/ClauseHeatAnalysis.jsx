import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';

const API_BASE_URL = (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));

const ClauseHeatAnalysis = () => {
  const { clauseId } = useParams();
  const [heatData, setHeatData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchClauseHeat();
  }, [clauseId]);

  const fetchClauseHeat = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API_BASE_URL}/api/clauses/${clauseId}/heat/`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setHeatData(response.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching clause heat:', err);
      setError(err.response?.data?.error || 'Failed to load clause heat');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Analyzing heat...</p>
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

  const heatColor = heatData.color || '#f59e0b';

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-100">Clause Heat Analysis</h1>
          <p className="text-gray-400 mt-1">Negotiation friction and loop detection</p>
        </div>

        {/* Heat Score Card */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-6">
          <div className="text-center">
            <div className="text-6xl mb-4">
              {heatData.heat_level === 'CRITICAL' && '🔥🔥🔥'}
              {heatData.heat_level === 'HIGH' && '🔥🔥'}
              {heatData.heat_level === 'MEDIUM' && '🔥'}
              {heatData.heat_level === 'LOW' && '⚠️'}
              {heatData.heat_level === 'MINIMAL' && '✅'}
            </div>
            <div className="text-5xl font-bold mb-2" style={{ color: heatColor }}>
              {(heatData.heat_score * 100).toFixed(0)}%
            </div>
            <div className="text-xl text-gray-300 mb-4">{heatData.heat_level} HEAT</div>
            <div className="text-sm text-gray-400">
              {heatData.total_rounds} negotiation rounds analyzed
            </div>
          </div>
        </div>

        {/* Component Breakdown */}
        {heatData.breakdown && (
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-6">
            <h3 className="text-lg font-semibold text-gray-200 mb-4">Heat Components</h3>
            <div className="space-y-4">
              {Object.entries(heatData.breakdown.components).map(([key, comp]) => (
                <div key={key}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-200 capitalize">
                      {key.replace('_', ' ')}
                    </span>
                    <span className="text-sm text-gray-400">
                      {(comp.normalized * 100).toFixed(0)}% (weight: {(comp.weight * 100)}%)
                    </span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div
                      className="h-2 rounded-full transition-all"
                      style={{
                        width: `${comp.normalized * 100}%`,
                        backgroundColor: comp.normalized > 0.7 ? '#ef4444' : comp.normalized > 0.4 ? '#f59e0b' : '#10b981'
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Emotion Analysis */}
        {heatData.emotion_analysis && (
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-6">
            <h3 className="text-lg font-semibold text-gray-200 mb-4">😤 Emotional Friction</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <div className="text-xs text-gray-400 mb-1">Current</div>
                <div className="text-lg font-bold text-gray-200">
                  {(heatData.emotion_analysis.current_friction * 100).toFixed(0)}%
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-400 mb-1">Average</div>
                <div className="text-lg font-bold text-gray-200">
                  {(heatData.emotion_analysis.avg_friction * 100).toFixed(0)}%
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-400 mb-1">Trend</div>
                <div className="text-lg font-bold text-gray-200">
                  {heatData.emotion_analysis.trend}
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-400 mb-1">Escalating</div>
                <div className="text-lg font-bold text-gray-200">
                  {heatData.emotion_analysis.escalating ? 'YES' : 'NO'}
                </div>
              </div>
            </div>

            {heatData.emotion_analysis.escalating && (
              <div className="mt-4 p-3 bg-red-900/20 border border-red-700 rounded text-sm text-red-400">
                ⚠️ Emotional friction is escalating. Consider cooling strategies.
              </div>
            )}
          </div>
        )}

        {/* Loop Analysis */}
        {heatData.loop_analysis && (
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-6">
            <h3 className="text-lg font-semibold text-gray-200 mb-4">🔁 Negotiation Loops</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div>
                <div className="text-xs text-gray-400 mb-1">Loop Count</div>
                <div className="text-lg font-bold text-gray-200">
                  {heatData.loop_analysis.loop_count}
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-400 mb-1">Avg Similarity</div>
                <div className="text-lg font-bold text-gray-200">
                  {(heatData.loop_analysis.avg_similarity * 100).toFixed(0)}%
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-400 mb-1">Stalled</div>
                <div className="text-lg font-bold text-gray-200">
                  {heatData.loop_analysis.stalled ? 'YES' : 'NO'}
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-400 mb-1">Has Loops</div>
                <div className="text-lg font-bold text-gray-200">
                  {heatData.loop_analysis.has_loops ? 'YES' : 'NO'}
                </div>
              </div>
            </div>

            {heatData.loop_analysis.loop_positions && heatData.loop_analysis.loop_positions.length > 0 && (
              <div>
                <div className="text-sm font-semibold text-gray-400 mb-2">Loop Positions:</div>
                <div className="space-y-2">
                  {heatData.loop_analysis.loop_positions.map((loop, idx) => (
                    <div key={idx} className="text-sm text-gray-300">
                      Round {loop.round}: {(loop.similarity * 100).toFixed(1)}% similar to previous
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Explosion Risk */}
        {heatData.explosion_risk && (
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-6">
            <h3 className="text-lg font-semibold text-gray-200 mb-4">💥 Explosion Risk</h3>
            <div className="mb-4">
              <div className="text-3xl font-bold mb-2" style={{
                color: heatData.explosion_risk.explosion_score > 0.7 ? '#ef4444' : '#f59e0b'
              }}>
                {(heatData.explosion_risk.explosion_score * 100).toFixed(0)}%
              </div>
              <div className="text-sm text-gray-300">{heatData.explosion_risk.risk_level}</div>
            </div>
            <div className="p-3 bg-orange-900/20 border border-orange-700 rounded text-sm text-orange-400">
              {heatData.explosion_risk.recommendation}
            </div>
          </div>
        )}

        {/* Deal Velocity */}
        {heatData.deal_velocity && (
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-6">
            <h3 className="text-lg font-semibold text-gray-200 mb-4">⏱️ Deal Velocity</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-xs text-gray-400 mb-1">Estimated Days</div>
                <div className="text-2xl font-bold text-gray-200">
                  {heatData.deal_velocity.estimated_days}
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-400 mb-1">Velocity</div>
                <div className="text-2xl font-bold text-gray-200">
                  {heatData.deal_velocity.velocity}
                </div>
              </div>
            </div>
            <div className="mt-3 text-sm text-gray-400">
              {heatData.deal_velocity.heat_impact}
            </div>
          </div>
        )}

        {/* Cooling Strategies */}
        {heatData.cooling_strategies && heatData.cooling_strategies.length > 0 && (
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-gray-200 mb-4">🧊 Cooling Strategies</h3>
            <div className="space-y-3">
              {heatData.cooling_strategies.map((strategy, idx) => (
                <div
                  key={idx}
                  className={`p-4 rounded-lg border ${
                    strategy.priority === 'CRITICAL' ? 'bg-red-900/20 border-red-700' :
                    strategy.priority === 'HIGH' ? 'bg-orange-900/20 border-orange-700' :
                    'bg-blue-900/20 border-blue-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-semibold text-gray-200">{strategy.strategy}</div>
                    <div className="text-xs px-2 py-1 rounded" style={{
                      backgroundColor: strategy.priority === 'CRITICAL' ? '#7f1d1d' :
                                     strategy.priority === 'HIGH' ? '#78350f' : '#1e3a8a',
                      color: '#fff'
                    }}>
                      {strategy.priority}
                    </div>
                  </div>
                  <div className="text-sm text-gray-300">{strategy.action}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ClauseHeatAnalysis;
