import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Shield, AlertTriangle, Info, CheckCircle2, XCircle, ArrowLeft, RefreshCw } from 'lucide-react';
import axios from 'axios';
import useAuthStore from '../store/authStore';

const RiskExplainability = () => {
  const { contractId } = useParams();
  const navigate = useNavigate();
  const { token } = useAuthStore();

  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchExplanation();
  }, [contractId]);

  const fetchExplanation = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.get(
        `${import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002')}/api/risk/contracts/${contractId}/explain`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      if (response.data.success) {
        setExplanation(response.data.data);
      }
    } catch (err) {
      console.error('Error fetching explanation:', err);
      setError(err.response?.data?.error || 'Failed to load risk explanation');
    } finally {
      setLoading(false);
    }
  };

  const getRiskLevelColor = (level) => {
    const colors = {
      CRITICAL: 'bg-red-100 text-red-800 border-red-300',
      HIGH: 'bg-orange-100 text-orange-800 border-orange-300',
      MEDIUM: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      LOW: 'bg-green-100 text-green-800 border-green-300'
    };
    return colors[level] || colors.MEDIUM;
  };

  const getRiskIcon = (level) => {
    if (level === 'CRITICAL' || level === 'HIGH') {
      return <AlertTriangle className="w-6 h-6" />;
    }
    return <Shield className="w-6 h-6" />;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Analyzing risk factors...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="bg-white p-8 rounded-lg shadow-lg max-w-md">
          <AlertTriangle className="w-12 h-12 text-red-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">Error</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => navigate(-1)}
            className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  if (!explanation) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>Back to Risk Dashboard</span>
        </button>

        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`p-3 rounded-lg ${
              explanation.risk_level === 'CRITICAL' || explanation.risk_level === 'HIGH'
                ? 'bg-red-600'
                : explanation.risk_level === 'MEDIUM'
                ? 'bg-yellow-600'
                : 'bg-green-600'
            }`}>
              {getRiskIcon(explanation.risk_level)}
              <Shield className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Risk Explanation</h1>
              <p className="text-gray-600">{explanation.contract_name}</p>
            </div>
          </div>

          <button
            onClick={fetchExplanation}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center space-x-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Risk Summary Card */}
      <div className={`border-2 rounded-lg p-6 mb-6 ${getRiskLevelColor(explanation.risk_level)}`}>
        <div className="flex items-start space-x-4">
          <div className="flex-shrink-0">
            <div className={`p-3 rounded-full ${
              explanation.risk_level === 'CRITICAL' ? 'bg-red-200' :
              explanation.risk_level === 'HIGH' ? 'bg-orange-200' :
              explanation.risk_level === 'MEDIUM' ? 'bg-yellow-200' :
              'bg-green-200'
            }`}>
              {getRiskIcon(explanation.risk_level)}
            </div>
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-lg font-bold">
                {explanation.risk_level} RISK LEVEL
              </h3>
              <span className="text-3xl font-bold">{explanation.risk_score.toFixed(2)}</span>
            </div>
            <p className="text-sm leading-relaxed">{explanation.explanation_summary}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Top Risk Factors */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5 text-orange-600" />
              <span>Top Risk Factors</span>
            </h3>

            {explanation.top_risk_factors && explanation.top_risk_factors.length > 0 ? (
              <div className="space-y-4">
                {explanation.top_risk_factors.map((factor, index) => (
                  <div
                    key={index}
                    className="border border-gray-200 rounded-lg p-4 hover:border-orange-300 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-900 capitalize">
                          {factor.clause_category || 'Unknown Clause'}
                        </h4>
                        {factor.risk_type && (
                          <span className="text-sm text-gray-600 capitalize">
                            {factor.risk_type.replace('_', ' ')} Risk
                          </span>
                        )}
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-orange-600">
                          {(factor.risk_score * 100).toFixed(0)}%
                        </div>
                        {factor.was_negotiated && (
                          <span className="text-xs text-green-600 flex items-center space-x-1">
                            <CheckCircle2 className="w-3 h-3" />
                            <span>Negotiated</span>
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="mt-2">
                      <div className="bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            factor.risk_score >= 0.8 ? 'bg-red-600' :
                            factor.risk_score >= 0.6 ? 'bg-orange-600' :
                            factor.risk_score >= 0.3 ? 'bg-yellow-600' :
                            'bg-green-600'
                          }`}
                          style={{ width: `${factor.risk_score * 100}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Info className="w-12 h-12 mx-auto mb-2 opacity-20" />
                <p>No specific risk factors identified</p>
              </div>
            )}
          </div>

          {/* Recommendations */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
              <CheckCircle2 className="w-5 h-5 text-green-600" />
              <span>Recommendations</span>
            </h3>

            {explanation.recommendations && explanation.recommendations.length > 0 ? (
              <ul className="space-y-3">
                {explanation.recommendations.map((rec, index) => (
                  <li key={index} className="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg">
                    <div className="flex-shrink-0 mt-0.5">
                      <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-semibold">
                        {index + 1}
                      </div>
                    </div>
                    <p className="text-gray-700 flex-1">{rec}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500 text-center py-4">No specific recommendations</p>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Contract Info */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Contract Information</h3>

            <div className="space-y-3">
              <div>
                <label className="text-sm text-gray-600">Contract ID</label>
                <p className="font-mono text-sm text-gray-900 truncate">{explanation.contract_id}</p>
              </div>

              {explanation.party && (
                <div>
                  <label className="text-sm text-gray-600">Party/Vendor</label>
                  <p className="text-gray-900">{explanation.party}</p>
                </div>
              )}

              {explanation.region && (
                <div>
                  <label className="text-sm text-gray-600">Region</label>
                  <p className="text-gray-900">{explanation.region}</p>
                </div>
              )}

              <div>
                <label className="text-sm text-gray-600">Risk Score</label>
                <div className="flex items-center space-x-2">
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        explanation.risk_score >= 0.8 ? 'bg-red-600' :
                        explanation.risk_score >= 0.6 ? 'bg-orange-600' :
                        explanation.risk_score >= 0.3 ? 'bg-yellow-600' :
                        'bg-green-600'
                      }`}
                      style={{ width: `${explanation.risk_score * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-semibold">{explanation.risk_score.toFixed(2)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Cross-Contract Correlations */}
          {explanation.correlated_contracts_count > 0 && (
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Risk Propagation</h3>

              <div className="text-center py-4">
                <div className="text-4xl font-bold text-purple-600 mb-2">
                  {explanation.correlated_contracts_count}
                </div>
                <p className="text-sm text-gray-600">
                  Correlated contracts detected
                </p>
                <p className="text-xs text-gray-500 mt-2">
                  This contract shares risk factors with {explanation.correlated_contracts_count} other contracts
                </p>
              </div>

              <button
                onClick={() => navigate(`/risk-network`)}
                className="w-full bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 mt-4 text-sm"
              >
                View in Network Graph
              </button>
            </div>
          )}

          {/* Actions */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Actions</h3>

            <div className="space-y-2">
              <button
                onClick={() => navigate(`/contract-analysis/${contractId}`)}
                className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm"
              >
                View Full Contract
              </button>

              <button
                onClick={() => navigate(`/clause-extraction/${contractId}`)}
                className="w-full bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 text-sm"
              >
                View Clause Breakdown
              </button>

              <button
                onClick={() => window.print()}
                className="w-full border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50 text-sm"
              >
                Export Report
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RiskExplainability;
