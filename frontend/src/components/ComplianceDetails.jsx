import { useState, useEffect } from 'react';
import {
  AlertTriangle,
  CheckCircle,
  AlertCircle,
  XCircle,
  Loader2,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import api from '../utils/api';

const ComplianceDetails = ({ contractId }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [compliance, setCompliance] = useState(null);
  const [expandedMapping, setExpandedMapping] = useState(null);
  const [activeTab, setActiveTab] = useState('GDPR');
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    loadComplianceDetails();
  }, [contractId]);

  const loadComplianceDetails = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/contracts/${contractId}/compliance`);
      setCompliance(response.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load compliance details');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const runComplianceAnalysis = async () => {
    console.log('[COMPLIANCE] Starting analysis for contract:', contractId);
    try {
      setAnalyzing(true);
      setError('');
      console.log('[COMPLIANCE] Making API request...');
      const response = await api.post(`/contracts/${contractId}/compliance/analyze`);
      console.log('[COMPLIANCE] Analysis response:', response.data);
      // Reload compliance data after analysis
      console.log('[COMPLIANCE] Reloading compliance details...');
      await loadComplianceDetails();
      console.log('[COMPLIANCE] Analysis complete!');
    } catch (err) {
      console.error('[COMPLIANCE] Error during analysis:', err);
      console.error('[COMPLIANCE] Error response:', err.response);
      setError(err.response?.data?.error || err.message || 'Failed to run compliance analysis');
    } finally {
      setAnalyzing(false);
    }
  };

  const CRITICALITY_COLORS = {
    CRITICAL: { bg: 'bg-red-900/30', border: 'border-red-700/50', text: 'text-red-400' },
    HIGH: { bg: 'bg-orange-900/30', border: 'border-orange-700/50', text: 'text-orange-400' },
    MEDIUM: { bg: 'bg-yellow-900/30', border: 'border-yellow-700/50', text: 'text-yellow-400' },
    LOW: { bg: 'bg-green-900/30', border: 'border-green-700/50', text: 'text-green-400' },
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'COMPLIANT':
        return { bg: 'bg-green-900/30', border: 'border-green-700', text: 'text-green-400', icon: CheckCircle };
      case 'PARTIAL':
        return { bg: 'bg-yellow-900/30', border: 'border-yellow-700', text: 'text-yellow-400', icon: AlertCircle };
      case 'NON_COMPLIANT':
        return { bg: 'bg-red-900/30', border: 'border-red-700', text: 'text-red-400', icon: XCircle };
      default:
        return { bg: 'bg-slate-900/30', border: 'border-slate-700', text: 'text-slate-400', icon: AlertCircle };
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <Loader2 className="w-8 h-8 text-blue-500 animate-spin mx-auto mb-2" />
          <p className="text-slate-400">Loading compliance analysis...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-800 text-red-300 rounded-lg p-4">
        <AlertTriangle size={20} className="inline mr-2" />
        {error}
      </div>
    );
  }

  if (!compliance) {
    return null;
  }

  const {
    analysis,
    framework_scores,
    mappings,
  } = compliance;

  const frameworks = Object.keys(framework_scores || {});
  const currentFramework = activeTab;
  const frameworkMappings = mappings?.filter(m => m.frameworkCode === currentFramework) || [];
  const currentFrameworkScore = framework_scores?.[currentFramework];

  // Show analyze button if no analysis has been run
  const showAnalyzeButton = analysis?.total_requirements_checked === 0;

  return (
    <div className="space-y-6">
      {/* Analyze Button */}
      {showAnalyzeButton && (
        <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-4 flex items-center justify-between">
          <div>
            <p className="text-white font-semibold">Compliance Analysis Not Run</p>
            <p className="text-slate-400 text-sm">Click the button to analyze this contract against compliance frameworks (GDPR, SOX, HIPAA, GST)</p>
          </div>
          <button
            onClick={runComplianceAnalysis}
            disabled={analyzing}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white px-6 py-2 rounded-lg font-semibold flex items-center gap-2 transition-colors"
          >
            {analyzing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              'Run Analysis'
            )}
          </button>
        </div>
      )}

      {/* Header with Overall Score */}
      <div className="bg-gradient-to-br from-purple-900/30 to-purple-800/20 border border-purple-700/50 rounded-lg p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Overall Compliance Score */}
          <div className="flex flex-col items-center justify-center">
            <div className="relative w-24 h-24 mb-4">
              <svg className="w-full h-full" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="45" fill="none" stroke="#334155" strokeWidth="8" />
                <circle
                  cx="50"
                  cy="50"
                  r="45"
                  fill="none"
                  stroke={
                    analysis?.overall_compliance_score >= 80
                      ? '#10b981'
                      : analysis?.overall_compliance_score >= 60
                      ? '#f59e0b'
                      : '#ef4444'
                  }
                  strokeWidth="8"
                  strokeDasharray={`${(analysis?.overall_compliance_score || 0) * 2.827} 282.7`}
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-2xl font-bold text-white">
                  {parseFloat((analysis?.overall_compliance_score || 0).toFixed(1))}%
                </span>
              </div>
            </div>
            <p className="text-slate-300 text-sm font-semibold">Overall Score</p>
          </div>

          {/* Requirements Status */}
          <div className="flex flex-col justify-center space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Total Checked:</span>
              <span className="text-white font-semibold">{analysis?.total_requirements_checked || 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-green-400">Compliant:</span>
              <span className="text-white font-semibold">{analysis?.compliant_count || 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-yellow-400">Partial:</span>
              <span className="text-white font-semibold">{analysis?.partial_count || 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-red-400">Non-Compliant:</span>
              <span className="text-white font-semibold">{analysis?.non_compliant_count || 0}</span>
            </div>
          </div>

          {/* Risk Assessment */}
          <div className="flex flex-col justify-center space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Compliance Risk:</span>
              <span className={`font-semibold ${
                (analysis?.compliance_risk_score || 0) >= 0.7
                  ? 'text-red-400'
                  : (analysis?.compliance_risk_score || 0) >= 0.4
                  ? 'text-yellow-400'
                  : 'text-green-400'
              }`}>
                {parseFloat(((analysis?.compliance_risk_score || 0) * 100).toFixed(1))}%
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-red-400">Critical:</span>
              <span className="text-white font-semibold">{analysis?.critical_violations || 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-orange-400">High:</span>
              <span className="text-white font-semibold">{analysis?.high_violations || 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-yellow-400">Medium:</span>
              <span className="text-white font-semibold">{analysis?.medium_violations || 0}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Framework Tabs */}
      {frameworks && frameworks.length > 0 && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
          {/* Tabs */}
          <div className="flex border-b border-slate-700 bg-slate-900/50">
            {frameworks.map((framework) => (
              <button
                key={framework}
                onClick={() => setActiveTab(framework)}
                className={`flex-1 py-3 px-4 text-center font-semibold transition-all ${
                  activeTab === framework
                    ? 'bg-slate-700 text-white border-b-2 border-blue-500'
                    : 'text-slate-400 hover:text-slate-300'
                }`}
              >
                {framework}
                {currentFrameworkScore && (
                  <span className="ml-2 text-xs">
                    ({parseFloat(currentFrameworkScore.score.toFixed(1))}%)
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Framework Content */}
          <div className="p-6">
            {currentFrameworkScore && (
              <div className="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-slate-400 text-sm mb-2">Framework Score</p>
                  <div className="text-3xl font-bold text-blue-400">
                    {parseFloat(currentFrameworkScore.score.toFixed(1))}%
                  </div>
                </div>
                <div>
                  <p className="text-slate-400 text-sm mb-2">Requirements Covered</p>
                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-bold text-white">{currentFrameworkScore.coverage}</span>
                    <span className="text-slate-400">requirements</span>
                  </div>
                </div>
              </div>
            )}

            {/* Requirements Table */}
            {frameworkMappings && frameworkMappings.length > 0 ? (
              <div className="space-y-2">
                {frameworkMappings.map((mapping) => {
                  const statusColor = getStatusColor(mapping.complianceStatus);
                  const StatusIcon = statusColor.icon;
                  const expanded = expandedMapping === mapping.id;

                  return (
                    <div
                      key={mapping.id}
                      className={`border rounded-lg overflow-hidden transition-all ${
                        statusColor.bg
                      } ${statusColor.border}`}
                    >
                      <button
                        onClick={() =>
                          setExpandedMapping(expanded ? null : mapping.id)
                        }
                        className="w-full p-4 flex items-center justify-between hover:bg-slate-700/20 transition-colors"
                      >
                        <div className="flex items-center gap-3 flex-1 text-left">
                          <StatusIcon size={20} className={statusColor.text} />
                          <div className="flex-1">
                            <p className="text-white font-semibold">
                              {mapping.requirementCode}
                            </p>
                            <p className="text-slate-400 text-sm">{mapping.requirementName}</p>
                          </div>
                          <div className="ml-4 text-right">
                            <div className={`text-sm font-semibold ${CRITICALITY_COLORS[mapping.criticality]?.text}`}>
                              {mapping.criticality}
                            </div>
                            <div className="text-xs text-slate-400">
                              Risk: {parseFloat((mapping.riskScore * 100).toFixed(1))}%
                            </div>
                          </div>
                        </div>
                        {expanded ? (
                          <ChevronUp size={20} className="text-slate-400 ml-2" />
                        ) : (
                          <ChevronDown size={20} className="text-slate-400 ml-2" />
                        )}
                      </button>

                      {/* Expanded Content */}
                      {expanded && (
                        <div className="border-t border-slate-700 p-4 bg-slate-900/30">
                          <div className="space-y-4">
                            <div>
                              <p className="text-slate-400 text-sm font-semibold mb-1">
                                Analysis Summary
                              </p>
                              <p className="text-slate-300">{mapping.analysisSummary}</p>
                            </div>

                            {mapping.gapDescription && (
                              <div>
                                <p className="text-slate-400 text-sm font-semibold mb-1">
                                  Gap Description
                                </p>
                                <p className="text-slate-300">{mapping.gapDescription}</p>
                              </div>
                            )}

                            {mapping.recommendation && (
                              <div>
                                <p className="text-slate-400 text-sm font-semibold mb-1">
                                  Recommendation
                                </p>
                                <p className="text-slate-300">{mapping.recommendation}</p>
                              </div>
                            )}

                            <div className="grid grid-cols-2 gap-4 pt-2 border-t border-slate-700">
                              <div>
                                <p className="text-slate-400 text-xs mb-1">Relevance Score</p>
                                <p className="text-white font-semibold">
                                  {parseFloat((mapping.relevanceScore * 100).toFixed(1))}%
                                </p>
                              </div>
                              <div>
                                <p className="text-slate-400 text-xs mb-1">Risk Score</p>
                                <p className="text-white font-semibold">
                                  {parseFloat((mapping.riskScore * 100).toFixed(1))}%
                                </p>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-slate-400">No requirements mapped for this framework.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ComplianceDetails;
