import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Loader, ChevronDown, ChevronUp, AlertCircle, CheckCircle, Eye, Shield, AlertTriangle, Info, Target, Sparkles, Brain } from 'lucide-react';
import api from '../utils/api';
import TextSpanHighlighter from '../components/TextSpanHighlighter';
import FullContractViewer from '../components/FullContractViewer';

export default function ClauseExtraction() {
  const { contractId } = useParams();
  const navigate = useNavigate();

  const [contract, setContract] = useState(null);
  const [clauses, setClauses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [extracting, setExtracting] = useState(false);
  const [error, setError] = useState('');
  const [expandedClauses, setExpandedClauses] = useState({});
  const [showFullContractViewer, setShowFullContractViewer] = useState(false);
  const [riskAnalysis, setRiskAnalysis] = useState(null);
  const [analyzingRisk, setAnalyzingRisk] = useState(false);
  const [showRiskAnalysis, setShowRiskAnalysis] = useState(false);
  const [riskAnalysisExpanded, setRiskAnalysisExpanded] = useState(true);

  useEffect(() => {
    fetchContractAndClauses();
  }, [contractId]);

  const fetchContractAndClauses = async () => {
    try {
      setLoading(true);
      const contractResponse = await api.get(`/contracts/${contractId}`);
      setContract(contractResponse.data.contract);

      // Try to fetch existing clauses
      try {
        const clausesResponse = await api.get(`/contracts/${contractId}/clauses`);
        setClauses(clausesResponse.data.clauses || []);
      } catch (clauseErr) {
        // If no clauses exist yet, that's okay
        setClauses([]);
      }

      // Try to fetch existing risk analysis
      try {
        const riskResponse = await api.get(`/contracts/${contractId}/risk-analysis`);
        if (riskResponse.data.riskAnalysis) {
          setRiskAnalysis(riskResponse.data.riskAnalysis);
          setShowRiskAnalysis(true);
        }
      } catch (riskErr) {
        // No risk analysis yet, that's okay
        setRiskAnalysis(null);
      }

      setError('');
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to load contract');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeRisk = async () => {
    try {
      setAnalyzingRisk(true);
      setError('');

      const response = await api.post(`/contracts/${contractId}/analyze-risk`);
      setRiskAnalysis(response.data.riskAnalysis);
      setShowRiskAnalysis(true);

      alert('Risk analysis completed successfully!');
    } catch (err) {
      const errorMsg = err.response?.data?.error || err.response?.data?.message || 'Failed to analyze risk';
      setError(errorMsg);
      console.error('Risk analysis error:', err);
    } finally {
      setAnalyzingRisk(false);
    }
  };

  const handleExtractClauses = async () => {
    try {
      setExtracting(true);
      setError('');

      const response = await api.post(`/contracts/${contractId}/extract-clauses`);
      setClauses(response.data.clauses || []);

      // Show success message
      alert(`Successfully extracted ${response.data.clausesFound} clauses!`);
    } catch (err) {
      const errorMsg = err.response?.data?.error || err.response?.data?.message || 'Failed to extract clauses';
      setError(errorMsg);
      console.error('Extraction error:', err);
    } finally {
      setExtracting(false);
    }
  };

  const toggleClause = (clauseId) => {
    setExpandedClauses(prev => ({
      ...prev,
      [clauseId]: !prev[clauseId]
    }));
  };

  const renderHighlightedText = (clause) => {
    // DEBUG: Log clause data to see what we're receiving
    console.log('🔍 DEBUG - Clause data:', {
      hasExtractedText: !!clause.extracted_text,
      extractedTextLength: clause.extracted_text?.length || 0,
      extractedTextPreview: clause.extracted_text?.substring(0, 100),
      contextSentencesCount: clause.contextSentences?.length || 0
    });

    // ALWAYS prioritize extracted_text if available (full clause content)
    if (clause.extracted_text && clause.extracted_text.trim()) {
      return (
        <div className="mb-3 p-4 bg-slate-800 rounded border border-slate-700">
          <p className="text-sm text-slate-200 whitespace-pre-wrap leading-relaxed">
            {clause.extracted_text}
          </p>
        </div>
      );
    }

    // Fallback to contextSentences if extracted_text not available
    if (!clause.contextSentences || clause.contextSentences.length === 0) {
      return <p className="text-slate-400 text-sm">No clause text available</p>;
    }

    return clause.contextSentences.map((sentence, idx) => {
      const { text, keyword, keywordStart, keywordEnd } = sentence;

      // If keyword position is available, highlight just the keyword
      if (keywordStart !== undefined && keywordStart >= 0 && keywordEnd > keywordStart) {
        return (
          <div key={idx} className="mb-3 p-3 bg-slate-800 rounded border border-slate-700">
            <p className="text-sm text-slate-200 leading-relaxed">
              <span className="text-slate-300">
                {text.substring(0, keywordStart)}
              </span>
              <span className="bg-yellow-400/40 text-yellow-100 font-bold px-1.5 rounded py-0.5 inline-block">
                {text.substring(keywordStart, keywordEnd)}
              </span>
              <span className="text-slate-300">
                {text.substring(keywordEnd)}
              </span>
            </p>
          </div>
        );
      }

      // Fallback to old behavior if keyword position not available
      return (
        <div key={idx} className="mb-3 p-3 bg-slate-800 rounded border border-slate-700">
          <p className="text-sm text-slate-200 whitespace-pre-wrap">
            {text}
          </p>
        </div>
      );
    });
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 75) return 'text-green-400';
    if (confidence >= 50) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getConfidenceBgColor = (confidence) => {
    if (confidence >= 75) return 'bg-green-500';
    if (confidence >= 50) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getRiskLevelColor = (level) => {
    if (level === 'LOW') return 'text-green-400 bg-green-900/30 border-green-800';
    if (level === 'MEDIUM') return 'text-yellow-400 bg-yellow-900/30 border-yellow-800';
    if (level === 'HIGH') return 'text-red-400 bg-red-900/30 border-red-800';
    return 'text-slate-400 bg-slate-900/30 border-slate-800';
  };

  const getSeverityColor = (severity) => {
    if (severity === 'LOW') return 'bg-green-900/30 border-green-800 text-green-400';
    if (severity === 'MEDIUM') return 'bg-yellow-900/30 border-yellow-800 text-yellow-400';
    if (severity === 'HIGH') return 'bg-red-900/30 border-red-800 text-red-400';
    return 'bg-slate-900/30 border-slate-800 text-slate-400';
  };

  const getSeverityIcon = (severity) => {
    if (severity === 'HIGH') return <AlertCircle className="w-5 h-5" />;
    if (severity === 'MEDIUM') return <AlertTriangle className="w-5 h-5" />;
    return <Info className="w-5 h-5" />;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader className="w-8 h-8 animate-spin text-blue-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
        {/* Header */}
        <div>
          <button
            onClick={() => navigate(-1)}
            className="text-blue-400 hover:text-blue-300 mb-4 text-sm"
          >
            ← Back
          </button>
          <h1 className="text-4xl font-bold mb-2 text-white">Clause Extraction</h1>
          <p className="text-slate-400">
            {contract?.originalFilename || 'Contract'}
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-900/20 border border-red-800 rounded-lg p-4 flex gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <p className="text-red-200">{error}</p>
          </div>
        )}

        {/* Extract Button */}
        {clauses.length === 0 ? (
          <button
            onClick={handleExtractClauses}
            disabled={extracting}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-white px-6 py-3 rounded-xl font-semibold transition flex items-center justify-center gap-2 shadow-md hover:shadow-lg"
          >
            {extracting ? (
              <>
                <Loader className="w-5 h-5 animate-spin" />
                Extracting Clauses...
              </>
            ) : (
              <>
                <CheckCircle className="w-5 h-5" />
                Extract Clauses
              </>
            )}
          </button>
        ) : (
          <button
            onClick={handleExtractClauses}
            disabled={extracting}
            className="bg-slate-700 hover:bg-slate-600 text-slate-200 px-4 py-2 rounded-lg font-medium transition text-sm"
          >
            {extracting ? 'Re-extracting...' : 'Re-extract Clauses'}
          </button>
        )}

        {/* Action Buttons */}
        {clauses.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* View Full Contract Button */}
            {contract?.fullText && (
              <button
                onClick={() => setShowFullContractViewer(true)}
                className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-xl font-semibold transition flex items-center justify-center gap-2 shadow-md hover:shadow-lg"
              >
                <Eye className="w-5 h-5" />
                View Full Contract with Highlighted Spans
              </button>
            )}

            {/* Intent Mining Button */}
            <button
              onClick={() => navigate(`/contract/${contractId}/intents`)}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-6 py-3 rounded-xl font-semibold transition flex items-center justify-center gap-2 shadow-md hover:shadow-lg"
            >
              <Sparkles className="w-5 h-5" />
              Analyze Intent Mining
            </button>
          </div>
        )}

        {/* Analyze Risk Button */}
        {clauses.length > 0 && (
          <button
            onClick={handleAnalyzeRisk}
            disabled={analyzingRisk}
            className="w-full bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700 disabled:from-slate-700 disabled:to-slate-700 disabled:cursor-not-allowed text-white px-6 py-3 rounded-xl font-semibold transition flex items-center justify-center gap-2 shadow-md hover:shadow-lg"
          >
            {analyzingRisk ? (
              <>
                <Loader className="w-5 h-5 animate-spin" />
                Analyzing Risk & Deviations...
              </>
            ) : (
              <>
                <Shield className="w-5 h-5" />
                {riskAnalysis ? 'Re-analyze Risk & Deviations' : 'Analyze Risk & Deviations'}
              </>
            )}
          </button>
        )}

        {/* Risk Analysis Results */}
        {showRiskAnalysis && riskAnalysis && (
          <div className="space-y-6">
            {/* Risk Level Summary - Collapsible */}
            <div className={`border rounded-xl ${getRiskLevelColor(riskAnalysis.risk_level)}`}>
              {/* Clickable Header */}
              <button
                onClick={() => setRiskAnalysisExpanded(!riskAnalysisExpanded)}
                className="w-full p-6 hover:opacity-90 transition text-left"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 flex-1">
                    <Shield className="w-8 h-8" />
                    <div>
                      <h2 className="text-2xl font-bold">Risk Analysis Complete</h2>
                      <p className="text-sm opacity-80">{contract?.contractType || 'Contract'}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-sm opacity-80">Risk Level</p>
                      <p className="text-3xl font-bold">{riskAnalysis.risk_level}</p>
                    </div>
                    {riskAnalysisExpanded ? (
                      <ChevronUp className="w-6 h-6 flex-shrink-0" />
                    ) : (
                      <ChevronDown className="w-6 h-6 flex-shrink-0" />
                    )}
                  </div>
                </div>
              </button>

              {/* Collapsible Content */}
              {riskAnalysisExpanded && (
                <div className="px-6 pb-6 border-t border-current/20 pt-4">
                  <p className="text-sm opacity-90 mb-4">{riskAnalysis.analysis_summary}</p>

                  <div className="grid grid-cols-4 gap-4">
                    <div className="bg-black/20 rounded-lg p-3 text-center">
                      <p className="text-xs opacity-80 mb-1">Risk Score</p>
                      <p className="text-2xl font-bold">{riskAnalysis.risk_score}/100</p>
                    </div>
                    <div className="bg-black/20 rounded-lg p-3 text-center">
                      <p className="text-xs opacity-80 mb-1">Critical</p>
                      <p className="text-2xl font-bold text-red-400">{riskAnalysis.critical_issues}</p>
                    </div>
                    <div className="bg-black/20 rounded-lg p-3 text-center">
                      <p className="text-xs opacity-80 mb-1">Medium</p>
                      <p className="text-2xl font-bold text-yellow-400">{riskAnalysis.medium_issues}</p>
                    </div>
                    <div className="bg-black/20 rounded-lg p-3 text-center">
                      <p className="text-xs opacity-80 mb-1">Low</p>
                      <p className="text-2xl font-bold text-green-400">{riskAnalysis.low_issues}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Deviations List */}
            {riskAnalysisExpanded && riskAnalysis.deviations && riskAnalysis.deviations.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                  <AlertTriangle className="w-6 h-6 text-orange-400" />
                  Deviations Found ({riskAnalysis.deviations.length})
                </h3>

                {riskAnalysis.deviations.map((deviation, idx) => (
                  <div
                    key={deviation.id || idx}
                    className={`border rounded-lg p-4 ${getSeverityColor(deviation.severity)}`}
                  >
                    <div className="flex items-start gap-3">
                      {getSeverityIcon(deviation.severity)}
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-semibold">{deviation.clause_name}</h4>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-semibold px-2 py-1 bg-black/30 rounded">
                              {deviation.deviation_type}
                            </span>
                            <span className="text-xs font-semibold px-2 py-1 bg-black/30 rounded">
                              {deviation.severity}
                            </span>
                          </div>
                        </div>
                        <p className="text-sm opacity-90 mb-2">{deviation.description}</p>
                        {deviation.recommendation && (
                          <div className="mt-3 p-3 bg-black/20 rounded text-sm">
                            <p className="font-semibold opacity-80 mb-1">Recommendation:</p>
                            <p className="opacity-90">{deviation.recommendation}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Summary Stats */}
        {clauses.length > 0 && (
          <div className="grid grid-cols-3 gap-4">
            {/* Show Risk Issues if risk analysis exists, otherwise show clauses found */}
            {riskAnalysis ? (
              <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
                <p className="text-slate-400 text-sm mb-1">Total Risk Issues</p>
                <p className="text-3xl font-bold text-orange-400">
                  {riskAnalysis.total_deviations || 0}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  From risk analysis
                </p>
              </div>
            ) : (
              <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
                <p className="text-slate-400 text-sm mb-1">Clauses Found</p>
                <p className="text-3xl font-bold text-green-400">
                  {clauses.filter(c => c.found).length}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  Template clauses
                </p>
              </div>
            )}
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
              <p className="text-slate-400 text-sm mb-1">Total Analyzed</p>
              <p className="text-3xl font-bold text-blue-400">
                {clauses.length}
              </p>
              <p className="text-xs text-slate-500 mt-1">
                Clauses checked
              </p>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
              <p className="text-slate-400 text-sm mb-1">Avg Confidence</p>
              <p className="text-3xl font-bold text-yellow-400">
                {clauses.length > 0
                  ? Math.round(
                      clauses.filter(c => c.found).reduce((sum, c) => sum + c.confidence, 0) /
                      Math.max(1, clauses.filter(c => c.found).length)
                    )
                  : 0}%
              </p>
            </div>
          </div>
        )}

        {/* Clauses List */}
        <div className="space-y-3">
          {clauses.length === 0 ? (
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-8 text-center text-slate-400">
              <p>Click "Extract Clauses" to analyze the contract and identify standard clauses</p>
            </div>
          ) : (
            clauses.map(clause => (
              <div key={clause.id} className="bg-slate-900 border border-slate-800 rounded-lg">
                {/* Clause Header */}
                <button
                  onClick={() => toggleClause(clause.id)}
                  className="w-full p-4 flex items-center justify-between hover:bg-slate-800 transition"
                >
                  <div className="flex items-center gap-4 text-left flex-1">
                    {clause.found ? (
                      <CheckCircle className="w-6 h-6 text-green-400 flex-shrink-0" />
                    ) : (
                      <AlertCircle className="w-6 h-6 text-slate-600 flex-shrink-0" />
                    )}
                    <div className="flex-1">
                      <h3 className="font-semibold text-white">{clause.clauseName}</h3>
                      {clause.found && (
                        <p className="text-xs text-slate-400 mt-1">
                          {clause.matchCount} matches found
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    {clause.found && (
                      <div className="text-right">
                        <p className={`font-semibold text-sm ${getConfidenceColor(clause.confidence)}`}>
                          {clause.confidence.toFixed(1)}%
                        </p>
                        <div className="w-16 h-2 bg-slate-800 rounded-full mt-1">
                          <div
                            className={`h-2 rounded-full ${getConfidenceBgColor(clause.confidence)}`}
                            style={{ width: `${clause.confidence}%` }}
                          />
                        </div>
                      </div>
                    )}
                    {expandedClauses[clause.id] ? (
                      <ChevronUp className="w-5 h-5 text-slate-400" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-slate-400" />
                    )}
                  </div>
                </button>

                {/* Clause Details */}
                {expandedClauses[clause.id] && clause.found && (
                  <div className="border-t border-slate-800 p-4 space-y-6">
                    {/* Intelligence Button */}
                    <div className="flex justify-end">
                      <button
                        onClick={() => navigate(`/clauses/${clause.id}/intelligence`)}
                        className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded-lg transition shadow-lg hover:shadow-cyan-500/50"
                      >
                        <Brain className="w-4 h-4" />
                        View Clause Intelligence
                      </button>
                    </div>

                    {/* Keyword location in document (short heading match) */}
                    {clause.textSpans && clause.textSpans.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-slate-300 mb-4">
                          📍 Keyword Location in Document
                        </h4>
                        <TextSpanHighlighter
                          fullText={contract?.fullText || ''}
                          clause={clause}
                          allClauses={clauses}
                        />
                      </div>
                    )}

                    {/* Full extracted clause body */}
                    {clause.extracted_text && clause.extracted_text.trim() && (
                      <div>
                        <h4 className="text-sm font-semibold text-slate-300 mb-3">
                          📄 Full Clause Text
                        </h4>
                        <div className="bg-slate-800/60 border border-slate-700/50 rounded-lg p-4">
                          <p className="text-sm text-slate-200 whitespace-pre-wrap leading-relaxed">
                            {clause.extracted_text}
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Footer Info */}
        {clauses.length > 0 && (
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
            <p className="text-xs text-slate-400">
              💡 <strong>Tip:</strong> Clauses are extracted using keyword matching and pattern recognition.
              Confidence scores indicate how confident the system is that a clause was found.
              Review extracted clauses carefully for accuracy.
            </p>
          </div>
        )}

      {/* Full Contract Viewer Modal */}
      {showFullContractViewer && contract?.fullText && (
        <FullContractViewer
          fullText={contract.fullText}
          clauses={clauses}
          onClose={() => setShowFullContractViewer(false)}
        />
      )}
    </div>
  );
}
