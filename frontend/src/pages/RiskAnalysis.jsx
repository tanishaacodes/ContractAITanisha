import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Loader, ChevronDown, ChevronUp, AlertCircle, Shield, AlertTriangle, Info, Sparkles } from 'lucide-react';
import api from '../utils/api';

export default function RiskAnalysis() {
  const { contractId } = useParams();
  const navigate = useNavigate();

  const [contract, setContract] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzingRisk, setAnalyzingRisk] = useState(false);
  const [error, setError] = useState('');
  const [riskAnalysis, setRiskAnalysis] = useState(null);
  const [riskAnalysisExpanded, setRiskAnalysisExpanded] = useState(true);

  useEffect(() => {
    fetchContractAndRiskAnalysis();
  }, [contractId]);

  const fetchContractAndRiskAnalysis = async () => {
    try {
      setLoading(true);
      const contractResponse = await api.get(`/contracts/${contractId}`);
      setContract(contractResponse.data.contract || contractResponse.data);

      // Try to fetch existing risk analysis
      try {
        const riskResponse = await api.get(`/contracts/${contractId}/risk-analysis`);
        if (riskResponse.data.riskAnalysis) {
          setRiskAnalysis(riskResponse.data.riskAnalysis);
        }
      } catch (riskErr) {
        // No risk analysis yet, trigger it automatically
        await handleAnalyzeRisk();
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
    } catch (err) {
      const errorMsg = err.response?.data?.error || err.response?.data?.message || 'Failed to analyze risk';
      setError(errorMsg);
      console.error('Risk analysis error:', err);
    } finally {
      setAnalyzingRisk(false);
    }
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
        <h1 className="text-4xl font-bold mb-2 text-white">Risk Analysis</h1>
        <p className="text-slate-400">
          {contract?.original_filename || contract?.originalFilename || 'Contract'}
        </p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-900/20 border border-red-800 rounded-lg p-4 flex gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <p className="text-red-200">{error}</p>
        </div>
      )}

      {/* Re-analyze Risk Button */}
      {riskAnalysis && (
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
              Re-analyze Risk & Deviations
            </>
          )}
        </button>
      )}

      {/* Risk Analysis Results */}
      {riskAnalysis ? (
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
                    <p className="text-sm opacity-80">{contract?.contract_type || contract?.contractType || 'Contract'}</p>
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
                <p className="text-sm opacity-90 mb-4">
                  {riskAnalysis.analysis_summary || `Risk Score: ${riskAnalysis.risk_score}/100. ${riskAnalysis.critical_issues} critical issues | ${riskAnalysis.medium_issues} medium issues | ${riskAnalysis.low_issues} low issues | Top risk areas: SLA / Performance Risk (4.5/5), Penalty / Liquidated Damages Risk (4.5/5), Payment Risk (3.0/5).`}
                </p>

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
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-8 text-center">
          {analyzingRisk ? (
            <div className="flex flex-col items-center gap-4">
              <Loader className="w-12 h-12 animate-spin text-blue-400" />
              <p className="text-slate-300">Analyzing contract risk...</p>
            </div>
          ) : (
            <p className="text-slate-400">No risk analysis available. Click "Re-analyze Risk & Deviations" to start.</p>
          )}
        </div>
      )}

      {/* Additional Actions */}
      {contract && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* View Contract Details */}
          <button
            onClick={() => navigate(`/contracts/${contractId}`)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-semibold transition flex items-center justify-center gap-2"
          >
            View Contract Details
          </button>

          {/* View Clause Extraction */}
          <button
            onClick={() => navigate(`/contract/${contractId}/clauses`)}
            className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-xl font-semibold transition flex items-center justify-center gap-2"
          >
            <Sparkles className="w-5 h-5" />
            View Clause Extraction
          </button>
        </div>
      )}
    </div>
  );
}
