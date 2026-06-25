import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import ForceGraph2D from 'react-force-graph-2d';

const API_BASE_URL = (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));

const TrustPropagationGraph = () => {
  const { clauseId } = useParams();
  const navigate = useNavigate();
  const [impactData, setImpactData] = useState(null);
  const [simulation, setSimulation] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [maxDepth, setMaxDepth] = useState(3);

  useEffect(() => {
    fetchImpactData();
    fetchRecommendations();
  }, [clauseId, maxDepth]);

  const fetchImpactData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API_BASE_URL}/api/clauses/${clauseId}/trust/impact/?depth=${maxDepth}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setImpactData(response.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching trust impact:', err);
      setError(err.response?.data?.error || 'Failed to load trust impact data');
    } finally {
      setLoading(false);
    }
  };

  const fetchRecommendations = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API_BASE_URL}/api/clauses/${clauseId}/trust/repair-recommendations/`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setRecommendations(response.data);
    } catch (err) {
      console.error('Error fetching recommendations:', err);
    }
  };

  const handleSimulateFailure = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_BASE_URL}/api/clauses/${clauseId}/trust/simulate-failure/`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setSimulation(response.data);
    } catch (err) {
      console.error('Error running simulation:', err);
      setError(err.response?.data?.error || 'Simulation failed');
    }
  };

  const prepareGraphData = () => {
    if (!impactData || !impactData.affected_clauses) {
      return { nodes: [], links: [] };
    }

    const nodes = [
      {
        id: clauseId,
        label: 'Source',
        trust: 1.0,
        color: '#3b82f6',
        size: 12
      }
    ];

    const links = [];

    impactData.affected_clauses.forEach((clause) => {
      const trustColor = clause.propagated_trust > 0.7 ? '#10b981' :
                         clause.propagated_trust > 0.5 ? '#f59e0b' : '#ef4444';

      nodes.push({
        id: clause.clause_id,
        label: `Clause ${clause.clause_id.substring(0, 8)}`,
        trust: clause.propagated_trust,
        current_trust: clause.current_trust,
        trust_delta: clause.trust_delta,
        distance: clause.distance,
        color: trustColor,
        size: 8 - clause.distance
      });

      links.push({
        source: clauseId,
        target: clause.clause_id,
        distance: clause.distance,
        trust_weight: clause.propagated_trust
      });
    });

    return { nodes, links };
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading trust propagation data...</p>
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

  const graphData = prepareGraphData();

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-100">Trust Propagation Graph</h1>
            <p className="text-gray-400 mt-1">Impact radius and trust contagion analysis</p>
          </div>
          <div className="flex gap-3">
            <select
              value={maxDepth}
              onChange={(e) => setMaxDepth(parseInt(e.target.value))}
              className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-gray-200"
            >
              <option value="1">Depth: 1</option>
              <option value="2">Depth: 2</option>
              <option value="3">Depth: 3</option>
              <option value="4">Depth: 4</option>
              <option value="5">Depth: 5</option>
            </select>
            <button
              onClick={handleSimulateFailure}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
            >
              💥 Simulate Failure
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        {impactData && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="text-sm text-gray-400 mb-1">Affected Clauses</div>
              <div className="text-2xl font-bold text-gray-100">{impactData.affected_count}</div>
            </div>

            {simulation && (
              <>
                <div className="bg-gray-800 rounded-lg p-4 border border-red-700">
                  <div className="text-sm text-gray-400 mb-1">Critical Impact</div>
                  <div className="text-2xl font-bold text-red-400">{simulation.critical_count}</div>
                </div>

                <div className="bg-gray-800 rounded-lg p-4 border border-orange-700">
                  <div className="text-sm text-gray-400 mb-1">High Impact</div>
                  <div className="text-2xl font-bold text-orange-400">{simulation.high_count}</div>
                </div>

                <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                  <div className="text-sm text-gray-400 mb-1">Total Impact</div>
                  <div className="text-2xl font-bold text-gray-100">{simulation.affected_count}</div>
                </div>
              </>
            )}
          </div>
        )}

        {/* Graph Visualization */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-6" style={{ height: '600px' }}>
          <h3 className="text-lg font-semibold text-gray-200 mb-4">Trust Impact Network</h3>
          {graphData.nodes.length > 0 ? (
            <ForceGraph2D
              graphData={graphData}
              nodeLabel={(node) => `${node.label}\nTrust: ${(node.trust * 100).toFixed(0)}%\nDistance: ${node.distance || 0}`}
              nodeColor={(node) => node.color}
              nodeVal={(node) => node.size}
              linkWidth={2}
              linkDirectionalParticles={2}
              linkDirectionalParticleSpeed={0.005}
              onNodeClick={(node) => navigate(`/clauses/${node.id}/trust`)}
              backgroundColor="#1f2937"
            />
          ) : (
            <div className="flex items-center justify-center h-full">
              <p className="text-gray-400">No propagation data available</p>
            </div>
          )}
        </div>

        {/* Affected Clauses List */}
        {impactData && impactData.affected_clauses && impactData.affected_clauses.length > 0 && (
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-6">
            <h3 className="text-lg font-semibold text-gray-200 mb-4">Affected Clauses</h3>
            <div className="space-y-2">
              {impactData.affected_clauses.map((clause) => (
                <div
                  key={clause.clause_id}
                  className="bg-gray-900/50 rounded-lg p-4 border border-gray-700 hover:border-blue-500 transition-colors cursor-pointer"
                  onClick={() => navigate(`/clauses/${clause.clause_id}/trust`)}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm font-medium text-gray-200">
                        Clause {clause.clause_id}
                      </div>
                      <div className="text-xs text-gray-400">
                        Distance: {clause.distance} hops
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-semibold text-gray-200">
                        Current: {(clause.current_trust * 100).toFixed(0)}% →
                        Propagated: {(clause.propagated_trust * 100).toFixed(0)}%
                      </div>
                      <div
                        className="text-xs font-semibold"
                        style={{
                          color: clause.trust_delta > 0 ? '#10b981' : '#ef4444'
                        }}
                      >
                        {clause.trust_delta > 0 ? '+' : ''}{(clause.trust_delta * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recommendations */}
        {recommendations && recommendations.recommendations && (
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-gray-200 mb-4">🔧 Repair Recommendations</h3>
            <ul className="space-y-2">
              {recommendations.recommendations.map((rec, idx) => (
                <li key={idx} className="text-sm text-gray-300 flex items-start gap-2">
                  <span className="text-blue-400">→</span>
                  {rec}
                </li>
              ))}
            </ul>

            {recommendations.alternatives && recommendations.alternatives.length > 0 && (
              <div className="mt-4">
                <h4 className="text-sm font-semibold text-gray-400 mb-2">High-Trust Alternatives:</h4>
                <div className="space-y-2">
                  {recommendations.alternatives.map((alt, idx) => (
                    <div
                      key={idx}
                      className="bg-gray-900/50 rounded-lg p-3 border border-gray-700 hover:border-green-500 transition-colors cursor-pointer"
                      onClick={() => navigate(`/clauses/${alt.id}/trust`)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="text-sm text-gray-200">Clause {alt.id}</div>
                        <div className="text-sm font-semibold text-green-400">
                          {(alt.trust * 100).toFixed(0)}% ({alt.badge})
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default TrustPropagationGraph;
