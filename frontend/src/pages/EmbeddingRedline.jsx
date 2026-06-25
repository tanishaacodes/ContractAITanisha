import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { FileEdit, CheckCircle, XCircle, ArrowRight, Shield, AlertCircle } from 'lucide-react';
import useThemeStore from '../store/themeStore';

const API_BASE_URL = (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));

const EmbeddingRedline = () => {
  const { contractId } = useParams();
  const { theme } = useThemeStore();
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [protectionLevel, setProtectionLevel] = useState('BALANCED');
  const [minRiskLevel, setMinRiskLevel] = useState('MEDIUM');

  const getSuggestions = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/embedding/contracts/${contractId}/suggest-redlines`,
        {
          protection_level: protectionLevel,
          min_risk_level: minRiskLevel
        },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      setSuggestions(response.data.suggestions || []);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to get suggestions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (contractId) {
      getSuggestions();
    }
  }, [contractId, protectionLevel, minRiskLevel]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg p-6">
        <h1 className="text-2xl font-bold mb-2">Embedding-Based Redlining</h1>
        <p className="text-purple-100 text-sm">
          Safer pre-approved alternatives • Zero hallucinations • Court-vetted language
        </p>
      </div>

      {/* Controls */}
      <div className={`${theme.colors.surface} rounded-lg border ${theme.colors.surfaceBorder} p-6`}>
        <h2 className={`text-lg font-semibold mb-4 ${theme.colors.textPrimary}`}>Redlining Preferences</h2>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={`block text-sm font-medium ${theme.colors.textPrimary} mb-2`}>
              Protection Level
            </label>
            <select
              value={protectionLevel}
              onChange={(e) => setProtectionLevel(e.target.value)}
              className={`w-full px-4 py-2 border ${theme.colors.surfaceBorder} ${theme.colors.surface} ${theme.colors.textPrimary} rounded-lg focus:ring-2 focus:ring-purple-500`}
            >
              <option value="MAXIMUM">Maximum Protection</option>
              <option value="BALANCED">Balanced / Market Standard</option>
              <option value="MINIMUM">Minimum Acceptable</option>
            </select>
            <p className={`text-xs ${theme.colors.textSecondary} mt-1`}>
              How protective the suggested clauses should be
            </p>
          </div>

          <div>
            <label className={`block text-sm font-medium ${theme.colors.textPrimary} mb-2`}>
              Minimum Risk Level
            </label>
            <select
              value={minRiskLevel}
              onChange={(e) => setMinRiskLevel(e.target.value)}
              className={`w-full px-4 py-2 border ${theme.colors.surfaceBorder} ${theme.colors.surface} ${theme.colors.textPrimary} rounded-lg focus:ring-2 focus:ring-purple-500`}
            >
              <option value="LOW">Low Risk and Above</option>
              <option value="MEDIUM">Medium Risk and Above</option>
              <option value="HIGH">High Risk Only</option>
            </select>
            <p className={`text-xs ${theme.colors.textSecondary} mt-1`}>
              Only suggest changes for clauses above this risk level
            </p>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-900 bg-opacity-20 border border-red-500 rounded-lg p-4">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {/* Suggestions */}
      {suggestions.length === 0 ? (
        <div className="bg-green-900 bg-opacity-20 border border-green-500 rounded-lg p-6 text-center">
          <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-3" />
          <h3 className={`text-lg font-semibold ${theme.colors.textPrimary} mb-2`}>
            No High-Risk Clauses Found!
          </h3>
          <p className="text-green-400">
            All clauses meet the selected risk threshold. Your contract looks good!
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Summary */}
          <div className={`${theme.colors.surface} rounded-lg border-l-4 border-purple-500 ${theme.colors.surfaceBorder} p-6`}>
            <div className="flex items-center justify-between">
              <div>
                <h2 className={`text-xl font-semibold ${theme.colors.textPrimary}`}>Redline Suggestions</h2>
                <p className={`${theme.colors.textSecondary} text-sm mt-1`}>
                  Found {suggestions.length} clause{suggestions.length !== 1 ? 's' : ''} that could be improved
                </p>
              </div>
              <div className="bg-purple-900 bg-opacity-30 text-purple-400 px-4 py-2 rounded-lg font-semibold border border-purple-500">
                {protectionLevel}
              </div>
            </div>
          </div>

          {/* Individual Suggestions */}
          {suggestions.map((suggestion, index) => (
            <div key={suggestion.clause_id} className={`${theme.colors.surface} rounded-lg border ${theme.colors.surfaceBorder} overflow-hidden`}>
              {/* Header */}
              <div className={`${theme.colors.surface} border-b ${theme.colors.surfaceBorder} p-4`}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <FileEdit className="w-5 h-5 text-purple-400" />
                      <h3 className={`font-semibold text-lg ${theme.colors.textPrimary}`}>{suggestion.clause_name}</h3>
                    </div>
                    <p className={`text-sm ${theme.colors.textSecondary}`}>
                      Intent Detected: <span className="font-medium text-purple-400">{suggestion.intent_detected}</span>
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center gap-2 bg-red-900 bg-opacity-30 text-red-400 border border-red-500 px-3 py-1 rounded-full text-sm font-medium mb-2">
                      <AlertCircle className="w-4 h-4" />
                      Risk Reduction: {suggestion.risk_reduction}%
                    </div>
                    <p className={`text-xs ${theme.colors.textSecondary}`}>
                      Similarity: {suggestion.similarity_to_original}%
                    </p>
                  </div>
                </div>
              </div>

              {/* Side-by-side comparison */}
              <div className="grid grid-cols-2 gap-4 p-6">
                {/* Original */}
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <XCircle className="w-5 h-5 text-red-400" />
                    <h4 className="font-semibold text-red-400">Original Clause</h4>
                  </div>
                  <div className="bg-red-900 bg-opacity-20 border border-red-500 rounded-lg p-4 text-sm">
                    <pre className={`whitespace-pre-wrap font-sans ${theme.colors.textPrimary}`}>
                      {suggestion.original_text}
                    </pre>
                  </div>
                </div>

                {/* Suggested */}
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <CheckCircle className="w-5 h-5 text-green-400" />
                    <h4 className="font-semibold text-green-400">
                      Suggested: {suggestion.approved_clause_name}
                    </h4>
                  </div>
                  <div className="bg-green-900 bg-opacity-20 border border-green-500 rounded-lg p-4 text-sm">
                    <pre className={`whitespace-pre-wrap font-sans ${theme.colors.textPrimary}`}>
                      {suggestion.suggested_text}
                    </pre>
                  </div>
                  <div className={`mt-2 flex items-center gap-2 text-xs ${theme.colors.textSecondary}`}>
                    <Shield className="w-4 h-4" />
                    Protection: {suggestion.protection_level}
                  </div>
                </div>
              </div>

              {/* Rationale */}
              <div className="bg-blue-900 bg-opacity-20 border-t border-blue-500 p-4">
                <h4 className="font-semibold text-blue-400 mb-2 flex items-center gap-2">
                  <ArrowRight className="w-4 h-4" />
                  Why This Change Is Recommended
                </h4>
                <div className={`text-sm ${theme.colors.textSecondary} whitespace-pre-wrap`}>
                  {suggestion.rationale}
                </div>
              </div>

              {/* Diff View (Optional) */}
              {suggestion.redline_diff && (
                <details className={`border-t ${theme.colors.surfaceBorder}`}>
                  <summary className={`cursor-pointer p-4 hover:${theme.colors.surface} font-medium text-sm ${theme.colors.textPrimary}`}>
                    View Detailed Diff
                  </summary>
                  <div className="bg-gray-900 text-green-400 p-4 text-xs font-mono overflow-x-auto">
                    <pre>{suggestion.redline_diff}</pre>
                  </div>
                </details>
              )}

              {/* Actions */}
              <div className={`${theme.colors.surface} border-t ${theme.colors.surfaceBorder} p-4 flex gap-3`}>
                <button
                  className="flex-1 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                  onClick={() => {
                    // TODO: Implement accept suggestion
                    alert('Accept suggestion - Integrate with your clause editing system');
                  }}
                >
                  Accept Suggestion
                </button>
                <button
                  className={`flex-1 ${theme.colors.surface} border ${theme.colors.surfaceBorder} hover:bg-gray-700 ${theme.colors.textPrimary} px-4 py-2 rounded-lg font-medium transition-colors`}
                  onClick={() => {
                    // TODO: Implement reject
                    alert('Reject suggestion');
                  }}
                >
                  Reject
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Info Box */}
      <div className="bg-purple-900 bg-opacity-20 border border-purple-500 rounded-lg p-4">
        <h3 className="font-semibold mb-2 text-sm text-purple-400">About Embedding-Based Redlining</h3>
        <ul className={`text-sm ${theme.colors.textSecondary} space-y-1`}>
          <li>✓ All suggestions come from pre-approved clause library</li>
          <li>✓ Zero hallucinations - only legally-vetted language</li>
          <li>✓ Deterministic - same clause always gets same suggestion</li>
          <li>✓ Explainable - shows similarity scores and matched patterns</li>
          <li>✓ Court-safe - approved by legal teams</li>
        </ul>
      </div>
    </div>
  );
};

export default EmbeddingRedline;
