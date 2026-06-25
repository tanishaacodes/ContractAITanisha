/**
 * AgentPanel Component
 * Provides intelligent agentic contract analysis using LangGraph orchestrator.
 *
 * Features 5 AI-powered analysis modes:
 * 1. Risk Scoring
 * 2. Intent Mining
 * 3. Executive Summary
 * 4. Classification
 * 5. Clause Extraction
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  AlertTriangle,
  Brain,
  FileText,
  Tag,
  FileSearch,
  Loader2,
  CheckCircle,
  XCircle,
  Sparkles
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from './ui/card';
import useThemeStore from '../store/themeStore';
import { config } from '../config/api.config';

const API_BASE_URL = config.BASE_URL;

const AgentPanel = ({ contractId }) => {
  const { theme } = useThemeStore();
  const [loading, setLoading] = useState(false);
  const [activeMode, setActiveMode] = useState(null);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [existingAnalysis, setExistingAnalysis] = useState(null);

  // Load cached results on mount so user sees something immediately
  useEffect(() => {
    if (contractId) {
      setResults(null);
      setExistingAnalysis(null);
      setError(null);
      loadExistingAnalysis();
    }
  }, [contractId]);

  const loadExistingAnalysis = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API_BASE_URL}/api/agent/contracts/${contractId}/results`,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (response.data.status === 'success') {
        setExistingAnalysis(response.data.analysis);
      }
    } catch (err) {
      // No existing analysis, that's okay
      console.log('No existing analysis found');
    }
  };

  // Map mode to quick endpoint for faster single-purpose analysis
  const QUICK_ENDPOINTS = {
    risk:    'quick-risk',
    intent:  'quick-intent',
    summary: 'quick-summary',
    classify:'quick-classify',
    extract: 'quick-extract',
  };

  const runAgent = async (mode) => {
    setLoading(true);
    setActiveMode(mode);
    setError(null);

    const endpoint = QUICK_ENDPOINTS[mode]
      ? `${API_BASE_URL}/api/agent/contracts/${contractId}/${QUICK_ENDPOINTS[mode]}`
      : `${API_BASE_URL}/api/agent/contracts/${contractId}/analyze`;

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        endpoint,
        QUICK_ENDPOINTS[mode] ? {} : { mode },
        { headers: { Authorization: `Bearer ${token}` }, timeout: 90000 }
      );

      if (response.data.status === 'success') {
        setResults(response.data.results);
        loadExistingAnalysis();
      } else {
        setError(response.data.message || 'Analysis failed');
      }
    } catch (err) {
      if (err.code === 'ECONNABORTED') {
        setError('Analysis timed out. The AI model is busy — try again in a moment.');
      } else {
        setError(err.response?.data?.message || 'Error running agent analysis');
      }
    } finally {
      setLoading(false);
      setActiveMode(null);
    }
  };

  const runFullAnalysis = async () => {
    setLoading(true);
    setActiveMode('full');
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_BASE_URL}/api/agent/contracts/${contractId}/analyze`,
        { mode: 'full' },
        { headers: { Authorization: `Bearer ${token}` }, timeout: 120000 }
      );

      if (response.data.status === 'success') {
        setResults(response.data.results);
        loadExistingAnalysis();
      } else {
        setError(response.data.message || 'Analysis failed');
      }
    } catch (err) {
      if (err.code === 'ECONNABORTED') {
        setError('Full analysis timed out. Try individual analysis buttons instead — they are faster.');
      } else {
        setError(err.response?.data?.message || 'Error running full analysis');
      }
    } finally {
      setLoading(false);
      setActiveMode(null);
    }
  };

  // Helper to get risk color
  const getRiskColor = (level) => {
    const colors = {
      'LOW': 'text-green-400 bg-green-400/10 border-green-400/20',
      'MEDIUM': 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20',
      'HIGH': 'text-orange-400 bg-orange-400/10 border-orange-400/20',
      'CRITICAL': 'text-red-400 bg-red-400/10 border-red-400/20'
    };
    return colors[level] || 'text-gray-400 bg-gray-400/10 border-gray-400/20';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Sparkles className="w-6 h-6 text-purple-400" />
            <div>
              <CardTitle>Agentic AI Analysis</CardTitle>
              <CardDescription>
                Intelligent multi-step contract analysis powered by LangGraph
              </CardDescription>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {/* Full Analysis Button */}
          <button
            onClick={runFullAnalysis}
            disabled={loading}
            className="w-full mb-6 px-6 py-4 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700
                     text-white font-semibold rounded-xl shadow-lg transition-all duration-200 disabled:opacity-50
                     disabled:cursor-not-allowed flex items-center justify-center gap-3"
          >
            {loading && activeMode === 'full' ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Running Full Analysis...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                Run Full AI Analysis
              </>
            )}
          </button>

          {/* Individual Action Buttons */}
          <div className="grid grid-cols-2 gap-4">
            {/* Risk Score */}
            <button
              onClick={() => runAgent('risk')}
              disabled={loading}
              className="p-4 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 rounded-xl
                       transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed group"
            >
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-red-400 group-hover:scale-110 transition-transform" />
                <div className="text-left flex-1">
                  <div className={`font-semibold ${theme.colors.textPrimary} text-sm`}>Score Risk</div>
                  <div className={`text-xs ${theme.colors.textSecondary} mt-1`}>Analyze contract risk factors</div>
                  {loading && activeMode === 'risk' && (
                    <Loader2 className="w-4 h-4 text-red-400 animate-spin mt-2" />
                  )}
                </div>
              </div>
            </button>

            {/* Intent Mining */}
            <button
              onClick={() => runAgent('intent')}
              disabled={loading}
              className="p-4 bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/30 rounded-xl
                       transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed group"
            >
              <div className="flex items-start gap-3">
                <Brain className="w-5 h-5 text-purple-400 group-hover:scale-110 transition-transform" />
                <div className="text-left flex-1">
                  <div className={`font-semibold ${theme.colors.textPrimary} text-sm`}>Mine Intent</div>
                  <div className={`text-xs ${theme.colors.textSecondary} mt-1`}>Discover business purpose</div>
                  {loading && activeMode === 'intent' && (
                    <Loader2 className="w-4 h-4 text-purple-400 animate-spin mt-2" />
                  )}
                </div>
              </div>
            </button>

            {/* Executive Summary */}
            <button
              onClick={() => runAgent('summary')}
              disabled={loading}
              className="p-4 bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/30 rounded-xl
                       transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed group"
            >
              <div className="flex items-start gap-3">
                <FileText className="w-5 h-5 text-blue-400 group-hover:scale-110 transition-transform" />
                <div className="text-left flex-1">
                  <div className={`font-semibold ${theme.colors.textPrimary} text-sm`}>Summarize</div>
                  <div className={`text-xs ${theme.colors.textSecondary} mt-1`}>Generate executive summary</div>
                  {loading && activeMode === 'summary' && (
                    <Loader2 className="w-4 h-4 text-blue-400 animate-spin mt-2" />
                  )}
                </div>
              </div>
            </button>

            {/* Classification */}
            <button
              onClick={() => runAgent('classify')}
              disabled={loading}
              className="p-4 bg-green-500/10 hover:bg-green-500/20 border border-green-500/30 rounded-xl
                       transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed group"
            >
              <div className="flex items-start gap-3">
                <Tag className="w-5 h-5 text-green-400 group-hover:scale-110 transition-transform" />
                <div className="text-left flex-1">
                  <div className={`font-semibold ${theme.colors.textPrimary} text-sm`}>Classify</div>
                  <div className={`text-xs ${theme.colors.textSecondary} mt-1`}>Determine contract type</div>
                  {loading && activeMode === 'classify' && (
                    <Loader2 className="w-4 h-4 text-green-400 animate-spin mt-2" />
                  )}
                </div>
              </div>
            </button>

            {/* Clause Extraction */}
            <button
              onClick={() => runAgent('extract')}
              disabled={loading}
              className="p-4 bg-yellow-500/10 hover:bg-yellow-500/20 border border-yellow-500/30 rounded-xl
                       transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed group"
            >
              <div className="flex items-start gap-3">
                <FileSearch className="w-5 h-5 text-yellow-400 group-hover:scale-110 transition-transform" />
                <div className="text-left flex-1">
                  <div className={`font-semibold ${theme.colors.textPrimary} text-sm`}>Extract Clauses</div>
                  <div className={`text-xs ${theme.colors.textSecondary} mt-1`}>Extract key contract provisions</div>
                  {loading && activeMode === 'extract' && (
                    <Loader2 className="w-4 h-4 text-yellow-400 animate-spin mt-2" />
                  )}
                </div>
              </div>
            </button>

            {/* Suggest Improvements - NEW */}
            <button
              onClick={() => runAgent('suggest')}
              disabled={loading}
              className="p-4 bg-orange-500/10 hover:bg-orange-500/20 border border-orange-500/30 rounded-xl
                       transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed group"
            >
              <div className="flex items-start gap-3">
                <Sparkles className="w-5 h-5 text-orange-400 group-hover:scale-110 transition-transform" />
                <div className="text-left flex-1">
                  <div className={`font-semibold ${theme.colors.textPrimary} text-sm`}>Suggest Improvements</div>
                  <div className={`text-xs ${theme.colors.textSecondary} mt-1`}>AI-powered clause suggestions</div>
                  {loading && activeMode === 'suggest' && (
                    <Loader2 className="w-4 h-4 text-orange-400 animate-spin mt-2" />
                  )}
                </div>
              </div>
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Card className="border-red-500/30 bg-red-500/5">
          <CardContent className="py-4">
            <div className="flex items-center gap-3 text-red-400">
              <XCircle className="w-5 h-5" />
              <span>{error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results Display */}
      {(results || existingAnalysis) && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <CheckCircle className="w-5 h-5 text-green-400" />
              <CardTitle>Analysis Results</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Risk Analysis */}
              {(results?.risk_analysis || existingAnalysis?.risk_analysis) && (
                <div className={`p-4 ${theme.colors.surfaceHover} rounded-lg border ${theme.colors.surfaceBorder}`}>
                  <h4 className={`font-semibold ${theme.colors.textPrimary} mb-2 flex items-center gap-2`}>
                    <AlertTriangle className="w-4 h-4 text-red-400" />
                    Risk Analysis
                  </h4>
                  {(() => {
                    const riskData = results?.risk_analysis || existingAnalysis?.risk_analysis;
                    return (
                      <div className="space-y-2">
                        <div className="flex items-center gap-3">
                          <span className={`text-sm ${theme.colors.textSecondary}`}>Risk Score:</span>
                          <span className={`font-bold ${theme.colors.textPrimary} text-lg`}>{riskData.risk_score || 'N/A'}</span>
                          <span className={`px-2 py-1 rounded-md text-xs font-semibold border ${getRiskColor(riskData.risk_level)}`}>
                            {riskData.risk_level || 'Not Assessed'}
                          </span>
                        </div>
                        {riskData.risk_flags && riskData.risk_flags.length > 0 && (
                          <div>
                            <span className={`text-sm ${theme.colors.textSecondary}`}>Risk Flags:</span>
                            <ul className="mt-1 space-y-1">
                              {riskData.risk_flags.slice(0, 3).map((flag, idx) => (
                                <li key={idx} className={`text-sm ${theme.colors.textSecondary} ml-4`}>• {flag.clause_name || flag}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    );
                  })()}
                </div>
              )}

              {/* Intent Analysis */}
              {(results?.intent_analysis || existingAnalysis?.intent_analysis) && (
                <div className={`p-4 ${theme.colors.surfaceHover} rounded-lg border ${theme.colors.surfaceBorder}`}>
                  <h4 className={`font-semibold ${theme.colors.textPrimary} mb-2 flex items-center gap-2`}>
                    <Brain className="w-4 h-4 text-purple-400" />
                    Business Intent
                  </h4>
                  {(() => {
                    const intentData = results?.intent_analysis || existingAnalysis?.intent_analysis;
                    return (
                      <div className="space-y-2">
                        <div>
                          <span className={`text-sm ${theme.colors.textSecondary}`}>Primary Intent:</span>
                          <p className={`${theme.colors.textPrimary} mt-1`}>{intentData.primary_intent || intentData.metadata?.primary_intent || 'Unknown'}</p>
                        </div>
                        {intentData.confidence !== undefined && (
                          <div className={`text-sm ${theme.colors.textSecondary}`}>
                            Confidence: <span className={theme.colors.textPrimary}>{(intentData.confidence * 100).toFixed(0)}%</span>
                          </div>
                        )}
                      </div>
                    );
                  })()}
                </div>
              )}

              {/* Executive Summary */}
              {(results?.executive_summary || existingAnalysis?.executive_summary) && (
                <div className={`p-4 ${theme.colors.surfaceHover} rounded-lg border ${theme.colors.surfaceBorder}`}>
                  <h4 className={`font-semibold ${theme.colors.textPrimary} mb-2 flex items-center gap-2`}>
                    <FileText className="w-4 h-4 text-blue-400" />
                    Executive Summary
                  </h4>
                  {(() => {
                    const summaryData = results?.executive_summary || existingAnalysis;
                    const summaryText = summaryData?.summary_text || summaryData?.executive_summary || 'No summary available';
                    return (
                      <pre className={`text-sm ${theme.colors.textSecondary} whitespace-pre-wrap font-sans`}>{summaryText}</pre>
                    );
                  })()}
                </div>
              )}

              {/* Classification */}
              {results?.classification && (
                <div className={`p-4 ${theme.colors.surfaceHover} rounded-lg border ${theme.colors.surfaceBorder}`}>
                  <h4 className={`font-semibold ${theme.colors.textPrimary} mb-2 flex items-center gap-2`}>
                    <Tag className="w-4 h-4 text-green-400" />
                    Classification
                  </h4>
                  <div className="space-y-2">
                    <div>
                      <span className={`text-sm ${theme.colors.textSecondary}`}>Contract Type:</span>
                      <p className={`${theme.colors.textPrimary} mt-1`}>
                        {results.classification.classified_as ||
                         results.classification.filename ||
                         'Not classified yet'}
                      </p>
                    </div>
                    {results.classification.confidence !== undefined && (
                      <div className={`text-sm ${theme.colors.textSecondary}`}>
                        Confidence: <span className={theme.colors.textPrimary}>{(results.classification.confidence * 100).toFixed(0)}%</span>
                      </div>
                    )}
                    {results.classification.message && (
                      <div className={`text-xs ${theme.colors.textTertiary} mt-2`}>
                        {results.classification.message}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Extracted Clauses */}
              {(results?.extracted_clauses || existingAnalysis?.extracted_clauses) && (
                <div className={`p-4 ${theme.colors.surfaceHover} rounded-lg border ${theme.colors.surfaceBorder}`}>
                  <h4 className={`font-semibold ${theme.colors.textPrimary} mb-2 flex items-center gap-2`}>
                    <FileSearch className="w-4 h-4 text-yellow-400" />
                    Extracted Clauses
                  </h4>
                  {(() => {
                    const clausesData = results?.extracted_clauses?.extracted_clauses || existingAnalysis?.extracted_clauses || {};
                    return (
                      <div className="space-y-2">
                        {Object.entries(clausesData).map(([clauseName, clauseData]) => (
                          <div key={clauseName} className="border-l-2 border-yellow-400/30 pl-3">
                            <div className={`text-sm font-semibold ${theme.colors.textPrimary}`}>{clauseName}</div>
                            <div className={`text-xs ${theme.colors.textSecondary} mt-1`}>
                              {typeof clauseData === 'string' ? clauseData : clauseData.text || 'Not found'}
                            </div>
                          </div>
                        ))}
                        {Object.keys(clausesData).length === 0 && (
                          <p className={`text-sm ${theme.colors.textSecondary}`}>No clauses extracted yet</p>
                        )}
                      </div>
                    );
                  })()}
                </div>
              )}

              {/* Clause Improvement Suggestions - NEW */}
              {results?.clause_suggestions && (
                <div className={`p-4 ${theme.colors.surfaceHover} rounded-lg border border-orange-500/30`}>
                  <h4 className={`font-semibold ${theme.colors.textPrimary} mb-3 flex items-center gap-2`}>
                    <Sparkles className="w-4 h-4 text-orange-400" />
                    AI Improvement Suggestions
                  </h4>

                  {/* Summary Stats */}
                  <div className={`grid grid-cols-3 gap-2 mb-4 p-3 ${theme.colors.surface} rounded-lg`}>
                    <div className="text-center">
                      <div className={`text-xs ${theme.colors.textSecondary}`}>Total Suggestions</div>
                      <div className={`text-lg font-bold ${theme.colors.textPrimary}`}>{results.clause_suggestions.total_suggestions || 0}</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xs text-red-400">Critical</div>
                      <div className="text-lg font-bold text-red-400">{results.clause_suggestions.critical_count || 0}</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xs text-yellow-400">Medium</div>
                      <div className="text-lg font-bold text-yellow-400">{results.clause_suggestions.medium_count || 0}</div>
                    </div>
                  </div>

                  {/* Suggestions List */}
                  <div className="space-y-3">
                    {results.clause_suggestions.suggestions?.map((suggestion, idx) => (
                      <div key={idx} className={`border ${theme.colors.surfaceBorder} rounded-lg p-3 hover:border-orange-500/50 transition-colors`}>
                        <div className="flex items-start justify-between mb-2">
                          <div className={`font-semibold ${theme.colors.textPrimary} text-sm`}>{suggestion.clause_name}</div>
                          <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                            suggestion.severity === 'HIGH' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                            suggestion.severity === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' :
                            'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                          }`}>
                            {suggestion.severity}
                          </span>
                        </div>

                        <div className="space-y-2 text-xs">
                          <div>
                            <span className={theme.colors.textSecondary}>Current: </span>
                            <span className={theme.colors.textSecondary}>{suggestion.current_text}</span>
                          </div>

                          <div>
                            <span className="text-green-400">Suggested: </span>
                            <span className={theme.colors.textPrimary}>{suggestion.suggested_text}</span>
                          </div>

                          <div className={`pt-2 border-t ${theme.colors.surfaceBorder}`}>
                            <span className={theme.colors.textSecondary}>Rationale: </span>
                            <span className={theme.colors.textSecondary}>{suggestion.rationale}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AgentPanel;
