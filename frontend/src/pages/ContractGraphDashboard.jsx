import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Network, TrendingUp, AlertTriangle, CheckCircle, Clock, Loader, Shield, FlaskConical } from 'lucide-react';
import api from '../utils/api';
import useThemeStore from '../store/themeStore';

export default function ContractGraphDashboard() {
  const { contractId } = useParams();
  const navigate = useNavigate();
  const { currentTheme } = useThemeStore();
  const theme = currentTheme; // For backwards compatibility

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    console.log('🔍 ContractGraphDashboard mounted with contractId:', contractId);

    // Redirect to contracts list if no contract ID or if it's "list" (route collision)
    if (!contractId || contractId === 'list') {
      console.log('❌ Invalid contract ID or route collision, redirecting to list');
      navigate('/contracts/list', { replace: true });
      return;
    }

    // Validate UUID format (basic check)
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (!uuidRegex.test(contractId)) {
      console.log('❌ Invalid UUID format, redirecting to list:', contractId);
      navigate('/contracts/list', { replace: true });
      return;
    }

    console.log('✅ Valid contract ID, loading graph dashboard');
    fetchDashboardData();
  }, [contractId, navigate]);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.get(`/contracts/${contractId}/graph-dashboard`);
      console.log('✅ Graph dashboard API response:', response.data);
      console.log('✅ Response status:', response.status);
      console.log('✅ Has data:', !!response.data);
      console.log('✅ Success field:', response.data?.success);

      // If we get HTTP 200 and have response data, consider it successful
      if (response.status === 200 && response.data) {
        setData(response.data);
        console.log('✅ Graph data loaded successfully!');
      } else {
        console.error('❌ API returned invalid response:', response);
        setError('Invalid response from server');
      }
    } catch (err) {
      console.error('Dashboard error:', err);

      // If contract not found (404), redirect to contracts list
      if (err.response?.status === 404) {
        setTimeout(() => {
          navigate('/contracts/list');
        }, 2000); // Give user time to see the error
      }

      setError(err.response?.data?.error || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (score) => {
    if (score >= 0.7) return 'text-red-600';
    if (score >= 0.5) return 'text-orange-600';
    if (score >= 0.3) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getRiskBg = (score) => {
    if (score >= 0.7) return 'bg-red-50 border-red-200';
    if (score >= 0.5) return 'bg-orange-50 border-orange-200';
    if (score >= 0.3) return 'bg-yellow-50 border-yellow-200';
    return 'bg-green-50 border-green-200';
  };

  const getPriorityColor = (priority) => {
    if (priority === 'HIGH') return 'text-red-600 bg-red-50 border-red-200';
    if (priority === 'MEDIUM') return 'text-orange-600 bg-orange-50 border-orange-200';
    return 'text-green-600 bg-green-50 border-green-200';
  };

  if (loading) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'}`}>
        <div className="text-center">
          <Loader className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className={theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}>Building graph intelligence...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`min-h-screen p-6 ${theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'}`}>
        <div className="max-w-2xl mx-auto">
          <div className={`rounded-lg shadow-lg p-8 text-center ${
            theme === 'dark' ? 'bg-gray-800 border border-gray-700' : 'bg-white'
          }`}>
            <AlertTriangle className="w-16 h-16 text-red-600 mx-auto mb-4" />
            <h2 className={`text-2xl font-bold mb-2 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
              Dashboard Unavailable
            </h2>
            <p className={`mb-6 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>{error}</p>
            <button
              onClick={() => navigate('/contracts/list')}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Back to Contracts
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Safety check: if loading is done but no data, show error
  if (!loading && !data) {
    console.warn('No data loaded for graph dashboard');
    return (
      <div className={`min-h-screen p-6 ${theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'}`}>
        <div className="max-w-2xl mx-auto mt-20">
          <div className={`rounded-lg shadow-lg p-8 text-center ${
            theme === 'dark' ? 'bg-gray-800 border border-gray-700' : 'bg-white'
          }`}>
            <AlertTriangle className="w-16 h-16 text-orange-600 mx-auto mb-4" />
            <h2 className={`text-2xl font-bold mb-2 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
              No Graph Data Available
            </h2>
            <p className={`mb-6 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
              Graph intelligence hasn't been generated yet. Try refreshing or go back to contracts.
            </p>
            <button
              onClick={() => fetchDashboardData()}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors mr-3"
            >
              Retry
            </button>
            <button
              onClick={() => navigate('/contracts/list', { replace: true })}
              className="bg-gray-600 text-white px-6 py-2 rounded-lg hover:bg-gray-700 transition-colors"
            >
              Back to Contracts
            </button>
          </div>
        </div>
      </div>
    );
  }

  const graphSummary = data?.graph_summary || {};
  const riskTimeline = data?.risk_timeline || {};
  const negotiationAdvice = data?.negotiation_advice || [];

  const highPriorityItems = negotiationAdvice.filter(a => a.priority === 'HIGH');
  const mediumPriorityItems = negotiationAdvice.filter(a => a.priority === 'MEDIUM');

  return (
    <div className={`min-h-screen p-6 ${theme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'}`}>
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-6">
        <button
          onClick={() => navigate('/contracts/list')}
          className={`flex items-center mb-4 transition-colors ${
            theme === 'dark'
              ? 'text-gray-400 hover:text-white'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Contracts
        </button>

        <div className={`rounded-lg shadow-lg p-6 ${
          theme === 'dark'
            ? 'bg-gradient-to-r from-blue-900 to-purple-900 border border-blue-800'
            : 'bg-gradient-to-r from-blue-600 to-purple-600'
        } text-white`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="bg-white bg-opacity-20 p-3 rounded-lg">
                <Network className="w-8 h-8" />
              </div>
              <div>
                <h1 className="text-3xl font-bold">Graph Intelligence Dashboard</h1>
                <p className={`mt-1 ${theme === 'dark' ? 'text-blue-200' : 'text-blue-100'}`}>
                  {data?.contract_name}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => navigate(`/contracts/${contractId}/what-if`)}
                className="flex items-center space-x-2 bg-white bg-opacity-20 px-4 py-2 rounded-lg hover:bg-opacity-30 transition-colors"
              >
                <FlaskConical className="w-5 h-5" />
                <span className="text-sm font-medium">What-If Analysis</span>
              </button>
              {data?.neo4j_synced && (
                <div className="flex items-center space-x-2 bg-green-500 bg-opacity-30 px-4 py-2 rounded-lg">
                  <CheckCircle className="w-5 h-5" />
                  <span className="text-sm font-medium">Neo4j Synced</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Total Clauses */}
          <div className={`rounded-lg shadow p-6 border-l-4 border-blue-500 ${
            theme === 'dark' ? 'bg-gray-800' : 'bg-white'
          }`}>
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-sm font-medium ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                  Total Clauses
                </p>
                <p className={`text-3xl font-bold mt-1 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                  {graphSummary.metrics?.total_nodes || 0}
                </p>
              </div>
              <Shield className="w-10 h-10 text-blue-500 opacity-50" />
            </div>
          </div>

          {/* Interactions */}
          <div className={`rounded-lg shadow p-6 border-l-4 border-purple-500 ${
            theme === 'dark' ? 'bg-gray-800' : 'bg-white'
          }`}>
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-sm font-medium ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                  Interactions
                </p>
                <p className={`text-3xl font-bold mt-1 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                  {graphSummary.metrics?.total_edges || 0}
                </p>
              </div>
              <Network className="w-10 h-10 text-purple-500 opacity-50" />
            </div>
          </div>

          {/* Total Risk */}
          <div className={`rounded-lg shadow p-6 border-l-4 ${
            riskTimeline.total_risk >= 0.7 ? 'border-red-500' :
            riskTimeline.total_risk >= 0.5 ? 'border-orange-500' : 'border-yellow-500'
          } ${theme === 'dark' ? 'bg-gray-800' : 'bg-white'}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-sm font-medium ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                  Total Risk
                </p>
                <p className={`text-3xl font-bold mt-1 ${getRiskColor(riskTimeline.total_risk || 0)}`}>
                  {(riskTimeline.total_risk || 0).toFixed(2)}
                </p>
              </div>
              <TrendingUp className="w-10 h-10 text-orange-500 opacity-50" />
            </div>
          </div>

          {/* High Priority */}
          <div className={`rounded-lg shadow p-6 border-l-4 border-red-500 ${
            theme === 'dark' ? 'bg-gray-800' : 'bg-white'
          }`}>
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-sm font-medium ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                  High Priority
                </p>
                <p className="text-3xl font-bold text-red-600 mt-1">
                  {highPriorityItems.length}
                </p>
              </div>
              <AlertTriangle className="w-10 h-10 text-red-500 opacity-50" />
            </div>
          </div>
        </div>
      </div>

      {/* Risk Propagation Timeline */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className={`rounded-lg shadow-lg p-6 ${theme === 'dark' ? 'bg-gray-800 border border-gray-700' : 'bg-white'}`}>
          <div className="flex items-center space-x-3 mb-6">
            <TrendingUp className="w-6 h-6 text-blue-600" />
            <h2 className={`text-xl font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
              Risk Propagation Timeline
            </h2>
          </div>

          {riskTimeline.timeline && riskTimeline.timeline.length > 0 ? (
            <div className="space-y-4">
              {riskTimeline.timeline.map((step, index) => (
                <div key={index} className="border-l-4 border-blue-500 pl-4 pb-4">
                  <div className="flex items-center space-x-3 mb-2">
                    <div className={`px-3 py-1 rounded-full text-sm font-bold ${
                      theme === 'dark' ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-700'
                    }`}>
                      Step {step.step}
                    </div>
                    <p className={`font-medium ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                      {step.description}
                    </p>
                  </div>

                  {step.activated_clauses && (
                    <div className="mt-2 space-y-2">
                      {step.activated_clauses.map((clause, idx) => (
                        <div key={idx} className={`p-3 rounded-lg border ${
                          theme === 'dark'
                            ? getRiskBg(clause.risk_score).replace('bg-', 'bg-opacity-20 border-') + ' bg-gray-700'
                            : getRiskBg(clause.risk_score)
                        }`}>
                          <div className="flex items-center justify-between">
                            <span className={`font-bold text-base ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                              {clause.clause_type || 'Unknown Clause'}
                            </span>
                            <span className={`text-sm font-bold ${getRiskColor(clause.risk_score)}`}>
                              Risk: {clause.risk_score.toFixed(2)}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {step.newly_activated && step.newly_activated.length > 0 && (
                    <div className="mt-2">
                      <p className={`text-sm mb-2 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                        Newly activated clauses:
                      </p>
                      <div className="space-y-2">
                        {step.newly_activated.map((clause, idx) => (
                          <div key={idx} className={`p-2 rounded ${
                            theme === 'dark'
                              ? 'bg-orange-900 bg-opacity-30 border border-orange-800'
                              : 'bg-orange-50 border border-orange-200'
                          }`}>
                            <div className="flex items-center justify-between">
                              <span className={`text-sm font-bold ${theme === 'dark' ? 'text-orange-300' : 'text-gray-900'}`}>
                                {clause.clause_type || 'Unknown Clause'}
                              </span>
                              <span className={`text-sm font-bold ${theme === 'dark' ? 'text-orange-400' : 'text-orange-600'}`}>
                                Accumulated: +{clause.accumulated_risk.toFixed(2)}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className={`text-center py-8 ${theme === 'dark' ? 'text-gray-500' : 'text-gray-500'}`}>
              No risk propagation data available
            </p>
          )}
        </div>
      </div>

      {/* Negotiation Priority Advice */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className={`rounded-lg shadow-lg p-6 ${theme === 'dark' ? 'bg-gray-800 border border-gray-700' : 'bg-white'}`}>
          <div className="flex items-center space-x-3 mb-6">
            <AlertTriangle className="w-6 h-6 text-orange-600" />
            <h2 className={`text-xl font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
              Negotiation Priority Advice
            </h2>
          </div>

          {/* High Priority */}
          {highPriorityItems.length > 0 && (
            <div className="mb-6">
              <h3 className={`text-lg font-semibold mb-3 ${theme === 'dark' ? 'text-red-400' : 'text-red-600'}`}>
                High Priority
              </h3>
              <div className="space-y-3">
                {highPriorityItems.map((item, index) => (
                  <div key={index} className={`p-4 rounded-lg border ${
                    theme === 'dark'
                      ? 'bg-red-900 bg-opacity-20 border-red-800'
                      : 'bg-red-50 border-red-200'
                  }`}>
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center space-x-3">
                        <span className={`text-lg font-bold ${theme === 'dark' ? 'text-red-400' : 'text-red-600'}`}>
                          {item.clause_type || 'Unknown Clause'}
                        </span>
                      </div>
                      <span className={`text-sm font-medium ${theme === 'dark' ? 'text-red-400' : 'text-red-600'}`}>
                        Score: {item.priority_score.toFixed(2)}
                      </span>
                    </div>
                    <p className={`text-sm mb-3 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                      {item.rationale}
                    </p>
                    {item.suggestions && item.suggestions.length > 0 && (
                      <div className="mt-2 space-y-1">
                        <p className={`text-xs font-semibold mb-1 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                          Suggestions:
                        </p>
                        {item.suggestions.map((suggestion, idx) => (
                          <div key={idx} className={`text-sm flex items-start ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>
                            <span className="mr-2">•</span>
                            <span>{suggestion}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Medium Priority */}
          {mediumPriorityItems.length > 0 && (
            <div>
              <h3 className={`text-lg font-semibold mb-3 ${theme === 'dark' ? 'text-orange-400' : 'text-orange-600'}`}>
                Medium Priority
              </h3>
              <div className="space-y-3">
                {mediumPriorityItems.slice(0, 5).map((item, index) => (
                  <div key={index} className={`p-4 rounded-lg border ${
                    theme === 'dark'
                      ? 'bg-orange-900 bg-opacity-20 border-orange-800'
                      : 'bg-orange-50 border-orange-200'
                  }`}>
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center space-x-3">
                        <span className={`text-lg font-bold ${theme === 'dark' ? 'text-orange-400' : 'text-orange-600'}`}>
                          {item.clause_type || 'Unknown Clause'}
                        </span>
                      </div>
                      <span className={`text-sm font-medium ${theme === 'dark' ? 'text-orange-400' : 'text-orange-600'}`}>
                        Score: {item.priority_score.toFixed(2)}
                      </span>
                    </div>
                    <p className={`text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                      {item.rationale}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {negotiationAdvice.length === 0 && (
            <p className={`text-center py-8 ${theme === 'dark' ? 'text-gray-500' : 'text-gray-500'}`}>
              No negotiation advice available
            </p>
          )}
        </div>
      </div>

      {/* Footer Info */}
      <div className="max-w-7xl mx-auto">
        <div className={`rounded-lg p-4 flex items-center justify-between ${
          theme === 'dark'
            ? 'bg-blue-900 bg-opacity-30 border border-blue-800'
            : 'bg-blue-50 border border-blue-200'
        }`}>
          <div className={`flex items-center space-x-2 ${theme === 'dark' ? 'text-blue-300' : 'text-blue-700'}`}>
            <Clock className="w-4 h-4" />
            <span className="text-sm">
              Last updated: {new Date(data?.updated_at).toLocaleString()}
            </span>
          </div>
          <button
            onClick={fetchDashboardData}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-sm font-medium transition-colors"
          >
            Refresh Dashboard
          </button>
        </div>
      </div>
    </div>
  );
}
