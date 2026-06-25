import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { ShieldAlert, AlertTriangle, CheckCircle, Info, TrendingUp } from 'lucide-react';
import useThemeStore from '../store/themeStore';

const API_BASE_URL = (import.meta.env.VITE_API_URL||(import.meta.env.VITE_API_URL||'http://localhost:8002'));

const EmbeddingRiskAnalysis = () => {
  const { contractId } = useParams();
  const { theme } = useThemeStore();
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const analyzeRisk = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/embedding/contracts/${contractId}/analyze-risk`,
        {},
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      setAnalysis(response.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to analyze risk');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (contractId) {
      analyzeRisk();
    }
  }, [contractId]);

  const getRiskColor = (level) => {
    switch (level) {
      case 'HIGH': return 'text-red-400 bg-red-900 bg-opacity-20 border-red-500';
      case 'MEDIUM': return 'text-orange-400 bg-orange-900 bg-opacity-20 border-orange-500';
      case 'LOW': return 'text-green-400 bg-green-900 bg-opacity-20 border-green-500';
      default: return `${theme.colors.textSecondary} ${theme.colors.surface} ${theme.colors.surfaceBorder}`;
    }
  };

  const getRiskIcon = (level) => {
    switch (level) {
      case 'HIGH': return <ShieldAlert className="w-5 h-5" />;
      case 'MEDIUM': return <AlertTriangle className="w-5 h-5" />;
      case 'LOW': return <CheckCircle className="w-5 h-5" />;
      default: return <Info className="w-5 h-5" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900 bg-opacity-20 border border-red-500 rounded-lg p-4">
        <p className="text-red-400">{error}</p>
      </div>
    );
  }

  if (!analysis) return null;

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg p-6">
        <h1 className="text-2xl font-bold mb-2">Embedding-Based Risk Analysis</h1>
        <p className="text-blue-100 text-sm">
          Deterministic • Explainable • Zero Hallucinations
        </p>
      </div>

      {/* Overall Risk Summary */}
      <div className={`${theme.colors.surface} rounded-lg p-6 border-l-4 border-blue-500 ${theme.colors.surfaceBorder}`}>
        <div className="flex items-center justify-between mb-4">
          <h2 className={`text-xl font-semibold ${theme.colors.textPrimary}`}>Overall Risk Assessment</h2>
          <span className={`px-4 py-2 rounded-full font-semibold flex items-center gap-2 ${getRiskColor(analysis.overall_risk_level)}`}>
            {getRiskIcon(analysis.overall_risk_level)}
            {analysis.overall_risk_level} RISK
          </span>
        </div>

        <div className="grid grid-cols-4 gap-4 mt-6">
          <div className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded-lg p-4`}>
            <p className={`${theme.colors.textSecondary} text-sm`}>Total Clauses</p>
            <p className={`text-2xl font-bold ${theme.colors.textPrimary}`}>{analysis.total_clauses}</p>
          </div>
          <div className="bg-red-900 bg-opacity-20 border border-red-500 rounded-lg p-4">
            <p className={`${theme.colors.textSecondary} text-sm`}>High Risk</p>
            <p className="text-2xl font-bold text-red-400">{analysis.high_risk_count}</p>
          </div>
          <div className="bg-orange-900 bg-opacity-20 border border-orange-500 rounded-lg p-4">
            <p className={`${theme.colors.textSecondary} text-sm`}>Medium Risk</p>
            <p className="text-2xl font-bold text-orange-400">{analysis.medium_risk_count}</p>
          </div>
          <div className="bg-green-900 bg-opacity-20 border border-green-500 rounded-lg p-4">
            <p className={`${theme.colors.textSecondary} text-sm`}>Low Risk</p>
            <p className="text-2xl font-bold text-green-400">{analysis.low_risk_count}</p>
          </div>
        </div>

        <div className={`mt-6 flex items-center gap-2 text-sm ${theme.colors.textSecondary}`}>
          <TrendingUp className="w-4 h-4" />
          Average Risk Score: <span className="font-semibold">{analysis.average_risk_score}/100</span>
        </div>
      </div>

      {/* Analysis Method Badge */}
      <div className="bg-blue-900 bg-opacity-20 border border-blue-500 rounded-lg p-4 flex items-start gap-3">
        <Info className="w-5 h-5 text-blue-400 mt-0.5" />
        <div>
          <p className="font-semibold text-blue-400">Analysis Method: {analysis.analysis_method}</p>
          <p className={`text-sm ${theme.colors.textSecondary} mt-1`}>
            Using {analysis.model} embeddings for deterministic risk scoring.
            Risk Score = Similarity × Severity Weight
          </p>
        </div>
      </div>

      {/* Clause-by-Clause Risk Breakdown */}
      <div className={`${theme.colors.surface} rounded-lg p-6 border ${theme.colors.surfaceBorder}`}>
        <h2 className={`text-xl font-semibold mb-4 ${theme.colors.textPrimary}`}>Clause Risk Details</h2>

        <div className="space-y-4">
          {analysis.clause_scores.map((clause, index) => (
            <div
              key={clause.clause_id}
              className={`border-l-4 rounded-lg p-4 border ${getRiskColor(clause.risk_level)}`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    {getRiskIcon(clause.risk_level)}
                    <h3 className={`font-semibold ${theme.colors.textPrimary}`}>{clause.clause_name}</h3>
                  </div>

                  {clause.matched_risk && (
                    <div className="mt-2">
                      <p className={`text-sm font-medium ${theme.colors.textSecondary}`}>
                        Matched Pattern: <span className="font-bold">{clause.matched_risk}</span>
                      </p>
                      <p className={`text-sm mt-1 ${theme.colors.textSecondary}`}>
                        Risk Type: {clause.risk_type} |
                        Similarity: {clause.similarity}% |
                        Severity: {clause.severity_weight}
                      </p>
                    </div>
                  )}
                </div>

                <div className="text-right">
                  <div className={`text-2xl font-bold ${theme.colors.textPrimary}`}>
                    {clause.risk_score}
                  </div>
                  <div className={`text-xs ${theme.colors.textSecondary}`}>out of 100</div>
                </div>
              </div>

              {clause.explanation && (
                <div className={`mt-3 ${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded p-3`}>
                  <p className={`text-sm ${theme.colors.textSecondary}`}>{clause.explanation}</p>
                </div>
              )}

              {clause.court_treatment && (
                <div className={`mt-2 text-sm ${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded p-2`}>
                  <p className={`font-semibold ${theme.colors.textPrimary}`}>Court Treatment:</p>
                  <p className={`text-xs mt-1 ${theme.colors.textSecondary}`}>{clause.court_treatment}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className={`${theme.colors.surface} border ${theme.colors.surfaceBorder} rounded-lg p-4`}>
        <h3 className={`font-semibold mb-2 text-sm ${theme.colors.textPrimary}`}>How Risk Scores Work</h3>
        <ul className={`text-sm ${theme.colors.textSecondary} space-y-1`}>
          <li>• Risk Score = Similarity to Known Risk Pattern × Severity Weight</li>
          <li>• HIGH Risk: Score ≥ 70 (Requires immediate attention)</li>
          <li>• MEDIUM Risk: Score 40-69 (Should be reviewed)</li>
          <li>• LOW Risk: Score &lt; 40 (Standard clause)</li>
          <li>• All scores are deterministic and explainable</li>
        </ul>
      </div>
    </div>
  );
};

export default EmbeddingRiskAnalysis;
