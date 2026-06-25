import React, { useState, useEffect } from 'react';
import { AlertTriangle, Loader2, Info, Scale, TrendingUp, Shield, Lightbulb, DollarSign, XOctagon, Zap, Target, RefreshCw } from 'lucide-react';

/**
 * ExculpatoryAnalysisView Component
 * Main visualization for exculpatory clause analysis based on Prof. Murali's paper
 * Displays analyzed clauses with risk scores and patterns
 */
const ExculpatoryAnalysisView = ({ contractId, onSummaryClick }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [analysisData, setAnalysisData] = useState(null);

  useEffect(() => {
    if (contractId) {
      loadAnalysis();
    }
  }, [contractId]);

  const loadAnalysis = async (forceRefresh = false) => {
    try {
      setLoading(true);
      setError(null);

      // Import exculpatory API
      const { exculpatoryAPI } = await import('../../services/negotiationAPI');

      // Call backend API with force parameter
      const response = await exculpatoryAPI.analyzeContract(contractId, forceRefresh);

      // Extract clauses and summary from response
      const analysisData = {
        clauses: response.clauses || [],
        summary: response.summary || {}
      };

      setAnalysisData(analysisData);
      setLoading(false);
    } catch (err) {
      console.error('Error loading analysis:', err);
      setError('Failed to load exculpatory clause analysis');
      setLoading(false);
    }

      /* Mock data fallback for reference (commented out)
      setTimeout(() => {
        const mockData = {
          clauses: [
            {
              id: 1,
              clause_name: "Site Conditions Clause",
              text: "The Contractor shall be deemed to have inspected the site and satisfied itself as to all matters affecting the execution of the works. No claims for unforeseen site conditions will be entertained.",
              risk_score: 0.85,
              is_exculpatory: true,
              risk_category: "SITE_CONDITIONS",
              imbalance: {
                controlled_by: "employer",
                bearer: "contractor",
                is_imbalanced: true,
                explanation: "Employer controls site access and information, but contractor bears all risk"
              },
              pattern_matches: [
                { pattern: "No Liability Clause", similarity: 0.78 }
              ]
            },
            {
              id: 2,
              clause_name: "Statutory Approvals",
              text: "All statutory approvals and permits required shall be the responsibility of the Contractor at their own cost.",
              risk_score: 0.72,
              is_exculpatory: true,
              risk_category: "STATUTORY_APPROVALS",
              imbalance: {
                controlled_by: "employer",
                bearer: "contractor",
                is_imbalanced: true,
                explanation: "Employer has more influence with authorities but shifts approval risk"
              },
              pattern_matches: [
                { pattern: "Risk Assumption", similarity: 0.65 }
              ]
            },
            {
              id: 3,
              clause_name: "Delay Clause",
              text: "Any delays arising from utilities, traffic restrictions, or third parties shall be at the Contractor's risk with no time extension granted.",
              risk_score: 0.88,
              is_exculpatory: true,
              risk_category: "DELAY",
              imbalance: {
                controlled_by: "employer",
                bearer: "contractor",
                is_imbalanced: true,
                explanation: "Contractor cannot control third-party delays but bears full consequence"
              },
              pattern_matches: [
                { pattern: "Waiver of Claims", similarity: 0.82 }
              ]
            },
            {
              id: 4,
              clause_name: "Workmanship Standards",
              text: "The Contractor shall ensure all works meet the highest industry standards and rectify any defects at their own cost.",
              risk_score: 0.25,
              is_exculpatory: false,
              risk_category: "WORKMANSHIP",
              imbalance: {
                controlled_by: "contractor",
                bearer: "contractor",
                is_imbalanced: false,
                explanation: "Contractor controls workmanship and appropriately bears related risk"
              },
              pattern_matches: []
            },
            {
              id: 5,
              clause_name: "Payment Terms",
              text: "Payment shall be made within 30 days of invoice submission, subject to work completion and approval.",
              risk_score: 0.30,
              is_exculpatory: false,
              risk_category: "PAYMENT",
              imbalance: {
                controlled_by: "both",
                bearer: "both",
                is_imbalanced: false,
                explanation: "Balanced allocation with mutual obligations"
              },
              pattern_matches: []
            }
          ],
          summary: {
            total_clauses: 45,
            analyzed_clauses: 5,
            risk_distribution: {
              high: 8,
              medium: 12,
              low: 25
            },
            risk_percentages: {
              high: 17.8,
              medium: 26.7,
              low: 55.5
            },
            imbalanced_clauses: 5,
            category_breakdown: {
              'SITE_CONDITIONS': 3,
              'STATUTORY_APPROVALS': 2,
              'DELAY': 4,
              'WORKMANSHIP': 1
            },
            recommendation: {
              decision: 'HIGH_RISK',
              message: 'Significant risk imbalance detected. Several clauses allocate site-condition and approval risks to contractor without adequate control. Negotiate key clauses or price defensively.'
            }
          }
        };
        setAnalysisData(mockData);
        setLoading(false);
      }, 1500);
      */
  };

  const getRiskColor = (score) => {
    if (score >= 0.7) return 'border-red-500/50 bg-red-500/10';
    if (score >= 0.4) return 'border-yellow-500/50 bg-yellow-500/10';
    return 'border-green-500/50 bg-green-500/10';
  };

  const getRiskBadge = (score, isExculpatory) => {
    if (score >= 0.7) {
      return (
        <span className="px-3 py-1 bg-red-600/20 text-red-400 text-xs font-bold rounded-full border border-red-500/30">
          HIGH RISK
        </span>
      );
    }
    if (score >= 0.4) {
      return (
        <span className="px-3 py-1 bg-yellow-600/20 text-yellow-400 text-xs font-bold rounded-full border border-yellow-500/30">
          MEDIUM RISK
        </span>
      );
    }
    return (
      <span className="px-3 py-1 bg-green-600/20 text-green-400 text-xs font-bold rounded-full border border-green-500/30">
        LOW RISK
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12 bg-slate-800/60 backdrop-blur-xl rounded-xl border border-orange-500/20">
        <Loader2 className="w-8 h-8 animate-spin text-orange-400" />
        <span className="ml-3 text-slate-300">Analyzing exculpatory clauses...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 backdrop-blur-xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-red-400">
            <AlertTriangle className="w-5 h-5" />
            <span className="font-semibold">{error}</span>
          </div>
          <button
            onClick={() => loadAnalysis(false)}
            className="px-4 py-2 bg-gradient-to-r from-red-600 to-red-700 hover:from-red-500 hover:to-red-600 text-white rounded-lg font-bold text-sm transition-all duration-300 flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!analysisData || !analysisData.clauses) {
    return (
      <div className="bg-slate-800/60 border border-slate-600/30 rounded-xl p-6 backdrop-blur-xl">
        <div className="flex items-center gap-2 text-slate-400">
          <Info className="w-5 h-5" />
          <span>No clauses available for analysis</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Summary Button */}
      <div className="flex items-center justify-between bg-slate-800/60 backdrop-blur-xl rounded-xl p-6 border border-orange-500/20">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Scale className="w-6 h-6 text-orange-400" style={{ filter: 'drop-shadow(0 0 8px rgba(249, 115, 22, 0.5))' }} />
            Exculpatory Clause Analysis
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            {analysisData.clauses.length} clauses analyzed • {analysisData.clauses.filter(c => c.is_exculpatory).length} exculpatory detected
            {analysisData.clauses.filter(c => c.deal_breaker).length > 0 && (
              <span className="ml-2 text-red-400 font-bold">
                • {analysisData.clauses.filter(c => c.deal_breaker).length} deal breaker(s)
              </span>
            )}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => loadAnalysis(true)}
            disabled={loading}
            className="px-4 py-3 bg-gradient-to-r from-cyan-600 to-cyan-700 hover:from-cyan-500 hover:to-cyan-600 text-white rounded-lg font-bold text-sm shadow-[0_0_20px_rgba(6,182,212,0.3)] transition-all duration-300 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className="w-4 h-4 inline-block mr-2" />
            Reanalyze
          </button>
          <button
            onClick={() => onSummaryClick && onSummaryClick(analysisData.summary)}
            className="px-6 py-3 bg-gradient-to-r from-orange-600 to-orange-700 hover:from-orange-500 hover:to-orange-600 text-white rounded-lg font-bold text-sm shadow-[0_0_20px_rgba(249,115,22,0.3)] transition-all duration-300 transform hover:scale-105"
          >
            <TrendingUp className="w-4 h-4 inline-block mr-2" />
            View Full Summary
          </button>
        </div>
      </div>

      {/* Risk Heatmap - Visual Overview */}
      <div className="bg-slate-800/60 backdrop-blur-xl rounded-xl p-6 border border-cyan-500/20">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <Shield className="w-5 h-5 text-cyan-400" />
            Risk Heatmap
            <span className="text-xs text-slate-400 font-normal ml-2">
              (Click a clause to navigate)
            </span>
          </h3>
          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-green-500"></div>
              <span className="text-slate-400">Low (0-0.3)</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-yellow-500"></div>
              <span className="text-slate-400">Medium (0.3-0.6)</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-red-500"></div>
              <span className="text-slate-400">High (0.6-1.0)</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-10 gap-2">
          {analysisData.clauses.map((clause, idx) => {
            const cellColor =
              clause.risk_score >= 0.7 ? 'bg-red-500/80 hover:bg-red-400 border-red-400' :
              clause.risk_score >= 0.4 ? 'bg-yellow-500/80 hover:bg-yellow-400 border-yellow-400' :
              'bg-green-500/80 hover:bg-green-400 border-green-400';

            const dealBreakerPulse = clause.deal_breaker ? 'animate-pulse shadow-[0_0_20px_rgba(239,68,68,0.8)]' : '';

            return (
              <div key={clause.id} className="relative group">
                <button
                  onClick={() => {
                    const element = document.getElementById(`clause-${clause.id}`);
                    if (element) {
                      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
                      element.classList.add('ring-4', 'ring-cyan-500/50');
                      setTimeout(() => {
                        element.classList.remove('ring-4', 'ring-cyan-500/50');
                      }, 2000);
                    }
                  }}
                  className={`w-full aspect-square rounded-lg border-2 ${cellColor} ${dealBreakerPulse} transition-all duration-300 transform hover:scale-110 cursor-pointer relative`}
                  title={`${clause.clause_name} - ${Math.round(clause.risk_score * 100)}% risk`}
                >
                  {clause.deal_breaker && (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <XOctagon className="w-4 h-4 text-white drop-shadow-lg" />
                    </div>
                  )}
                </button>

                {/* Tooltip on hover */}
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block z-50">
                  <div className="bg-slate-900 border border-slate-600 rounded-lg p-3 shadow-xl min-w-[200px]">
                    <div className="text-xs font-bold text-white mb-1">{clause.clause_name}</div>
                    <div className="text-xs text-slate-300 mb-1">
                      Risk: <span className="font-bold text-orange-400">{Math.round(clause.risk_score * 100)}%</span>
                    </div>
                    {clause.risk_category && (
                      <div className="text-xs text-slate-400">
                        {clause.risk_category.replace(/_/g, ' ')}
                      </div>
                    )}
                    {clause.deal_breaker && (
                      <div className="text-xs text-red-400 font-bold mt-1">
                        ⚠ DEAL BREAKER
                      </div>
                    )}
                  </div>
                </div>

                {/* Clause number label */}
                <div className="text-center mt-1 text-xs text-slate-500 font-mono">
                  {idx + 1}
                </div>
              </div>
            );
          })}
        </div>

        {/* Summary stats below heatmap */}
        <div className="mt-4 pt-4 border-t border-slate-700/50 flex items-center justify-center gap-6 text-xs text-slate-400">
          <span>
            <span className="font-bold text-red-400">{analysisData.clauses.filter(c => c.risk_score >= 0.7).length}</span> High Risk
          </span>
          <span>
            <span className="font-bold text-yellow-400">{analysisData.clauses.filter(c => c.risk_score >= 0.4 && c.risk_score < 0.7).length}</span> Medium Risk
          </span>
          <span>
            <span className="font-bold text-green-400">{analysisData.clauses.filter(c => c.risk_score < 0.4).length}</span> Low Risk
          </span>
          {analysisData.clauses.filter(c => c.deal_breaker).length > 0 && (
            <span>
              <span className="font-bold text-red-300">{analysisData.clauses.filter(c => c.deal_breaker).length}</span> Deal Breaker{analysisData.clauses.filter(c => c.deal_breaker).length > 1 ? 's' : ''}
            </span>
          )}
        </div>
      </div>

      {/* Compound Risk Alert Banner - NEW */}
      {analysisData.summary?.interaction_risks && analysisData.summary.interaction_risks.length > 0 && (
        <div className="bg-red-900/30 border-2 border-red-500/50 rounded-xl p-6 backdrop-blur-xl shadow-[0_0_30px_rgba(239,68,68,0.3)]">
          <div className="flex items-start gap-4">
            <Zap className="w-8 h-8 text-red-400 flex-shrink-0 animate-pulse" />
            <div className="flex-1">
              <h3 className="text-xl font-bold text-red-300 mb-2 flex items-center gap-2">
                COMPOUND RISK ALERT
                <span className="px-2 py-1 bg-red-600/30 text-red-300 text-xs font-bold rounded-full">
                  {analysisData.summary.interaction_risks.length} dangerous interaction{analysisData.summary.interaction_risks.length > 1 ? 's' : ''}
                </span>
              </h3>
              <p className="text-sm text-red-200/80 mb-4">
                Individual clauses combine to create severe risk traps. These interactions amplify financial exposure beyond individual clause risks.
              </p>
              <div className="space-y-3">
                {analysisData.summary.interaction_risks.slice(0, 3).map((interaction, idx) => (
                  <div key={idx} className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-sm font-bold text-red-300">
                        {interaction.risk_type.replace(/_/g, ' ')}
                      </h4>
                      <span className={`px-2 py-1 text-xs font-bold rounded-full ${
                        interaction.severity === 'CRITICAL' ? 'bg-red-600/40 text-red-200' :
                        interaction.severity === 'HIGH' ? 'bg-orange-600/40 text-orange-200' :
                        'bg-yellow-600/40 text-yellow-200'
                      }`}>
                        {interaction.severity}
                      </span>
                    </div>
                    <p className="text-xs text-red-200/70 mb-2">{interaction.description}</p>
                    <div className="flex items-center gap-4 text-xs">
                      <span className="text-red-300">
                        Financial Multiplier: <span className="font-bold">{interaction.financial_multiplier}x</span>
                      </span>
                      <span className="text-red-300/70">
                        Involves: {interaction.involved_clauses.join(', ')}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Clause Cards */}
      <div className="space-y-4">
        {analysisData.clauses.map((clause) => (
          <div
            key={clause.id}
            id={`clause-${clause.id}`}
            className={`bg-slate-800/60 backdrop-blur-xl rounded-xl p-6 border-2 ${getRiskColor(clause.risk_score)} transition-all duration-300 hover:shadow-[0_0_20px_rgba(249,115,22,0.2)]`}
          >
            {/* Clause Header */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="text-lg font-bold text-white">{clause.clause_name}</h3>
                  {clause.deal_breaker && (
                    <span className="px-2 py-1 bg-red-600/30 text-red-300 text-xs font-bold rounded-full border border-red-500/50 flex items-center gap-1 animate-pulse">
                      <XOctagon className="w-3 h-3" />
                      DEAL BREAKER
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  <p className="text-xs text-slate-400 uppercase tracking-wider">
                    {clause.risk_category.replace(/_/g, ' ')}
                  </p>
                  {clause.imbalance_severity && clause.imbalance_severity !== 'LOW' && clause.imbalance_severity !== 'BALANCED' && (
                    <span className={`px-2 py-1 text-xs font-bold rounded ${
                      clause.imbalance_severity === 'EXTREME' ? 'bg-red-600/20 text-red-400 border border-red-500/30' :
                      clause.imbalance_severity === 'HIGH' ? 'bg-orange-600/20 text-orange-400 border border-orange-500/30' :
                      'bg-yellow-600/20 text-yellow-400 border border-yellow-500/30'
                    }`}>
                      {clause.imbalance_severity} IMBALANCE
                    </span>
                  )}
                  {clause.probability && (
                    <span className="text-xs text-slate-500">
                      Probability: <span className={`font-semibold ${
                        clause.probability === 'HIGH' ? 'text-red-400' :
                        clause.probability === 'MEDIUM' ? 'text-yellow-400' :
                        'text-green-400'
                      }`}>{clause.probability}</span>
                    </span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-3">
                {getRiskBadge(clause.risk_score, clause.is_exculpatory)}
                <div className="text-right">
                  <div className="text-2xl font-bold text-orange-400">
                    {Math.round(clause.risk_score * 100)}%
                  </div>
                  <div className="text-xs text-slate-400">Risk Score</div>
                </div>
              </div>
            </div>

            {/* Clause Text */}
            <div className="bg-slate-900/60 rounded-lg p-4 mb-4 border border-slate-700/50">
              <p className="text-sm text-slate-300 leading-relaxed">{clause.text}</p>
            </div>

            {/* Financial Exposure - NEW */}
            {clause.financial_exposure && Object.keys(clause.financial_exposure).length > 0 && (
              <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-4 mb-4">
                <div className="flex items-start gap-3">
                  <DollarSign className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <h4 className="text-sm font-bold text-green-300 mb-2">Estimated Financial Exposure</h4>
                    <div className="grid grid-cols-3 gap-3">
                      <div className="bg-slate-900/60 rounded p-2 text-center">
                        <div className="text-xs text-slate-400 mb-1">Minimum</div>
                        <div className="text-sm font-bold text-green-400">
                          ${(clause.financial_exposure.minimum_exposure || 0).toLocaleString()}
                        </div>
                      </div>
                      <div className="bg-slate-900/60 rounded p-2 text-center border-2 border-yellow-500/30">
                        <div className="text-xs text-yellow-400 mb-1">Likely</div>
                        <div className="text-base font-bold text-yellow-400">
                          ${(clause.financial_exposure.likely_exposure || 0).toLocaleString()}
                        </div>
                      </div>
                      <div className="bg-slate-900/60 rounded p-2 text-center">
                        <div className="text-xs text-slate-400 mb-1">Maximum</div>
                        <div className="text-sm font-bold text-red-400">
                          ${(clause.financial_exposure.maximum_exposure || 0).toLocaleString()}
                        </div>
                      </div>
                    </div>
                    {clause.financial_exposure.exposure_percentage && (
                      <p className="text-xs text-green-300/70 mt-2">
                        Risk exposure: {clause.financial_exposure.exposure_percentage.toFixed(1)}% of contract value
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Risk Imbalance Alert */}
            {clause.imbalance?.is_imbalanced && (
              <div className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-4 mb-4">
                <div className="flex items-start gap-3">
                  <Scale className="w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-sm font-bold text-orange-300 mb-1">Risk Allocation Imbalance</h4>
                    <p className="text-xs text-orange-200/80">
                      {clause.imbalance.explanation}
                    </p>
                    <div className="flex items-center gap-4 mt-2 text-xs">
                      <span className="text-slate-400">
                        Controller: <span className="font-semibold text-cyan-400">{clause.imbalance.controlled_by}</span>
                      </span>
                      <span className="text-slate-400">
                        Bearer: <span className="font-semibold text-red-400">{clause.imbalance.bearer}</span>
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Pattern Matches */}
            {clause.pattern_matches && clause.pattern_matches.length > 0 && (
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs text-slate-500 font-semibold">Similar to:</span>
                {clause.pattern_matches.map((match, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1 bg-cyan-500/10 text-cyan-400 text-xs rounded-full border border-cyan-500/20"
                  >
                    {match.pattern} ({Math.round(match.similarity * 100)}%)
                  </span>
                ))}
              </div>
            )}

            {/* FIDIC Proper Allocation Advice - NEW */}
            {clause.proper_allocation_advice && clause.risk_score >= 0.4 && (
              <div className="mt-3 p-4 bg-purple-500/5 border border-purple-500/20 rounded-lg">
                <h4 className="text-sm font-bold text-purple-300 mb-2 flex items-center gap-2">
                  <Target className="w-4 h-4" />
                  FIDIC Proper Risk Allocation
                </h4>
                <div className="text-xs text-slate-300 whitespace-pre-line">
                  {clause.proper_allocation_advice}
                </div>
              </div>
            )}

            {/* Risk Mitigation Suggestions */}
            {clause.suggestions && clause.suggestions.length > 0 && (
              <div className="mt-3 p-4 bg-blue-500/5 border border-blue-500/20 rounded-lg">
                <h4 className="text-sm font-bold text-blue-300 mb-2 flex items-center gap-2">
                  <Lightbulb className="w-4 h-4" />
                  Mitigation Suggestions
                </h4>
                <ul className="space-y-2">
                  {clause.suggestions.map((suggestion, idx) => (
                    <li key={idx} className="text-xs text-slate-300 flex items-start gap-2">
                      <span className="text-blue-400 mt-0.5">•</span>
                      <span>{suggestion}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Impact Chain (WHY → WHAT → HOW) - NEW */}
            {clause.impact_chain_data && clause.risk_score >= 0.4 && (
              <div className="mt-3 p-4 bg-indigo-500/5 border border-indigo-500/20 rounded-lg">
                <h4 className="text-sm font-bold text-indigo-300 mb-3">Complete Risk Analysis</h4>

                {/* WHY - Risk Rationale */}
                {clause.impact_chain_data.risk_rationale && (
                  <div className="mb-3">
                    <h5 className="text-xs font-bold text-indigo-400 mb-1">WHY is this risky?</h5>
                    <div className="text-xs text-slate-300 whitespace-pre-line pl-3 border-l-2 border-indigo-500/30">
                      {clause.impact_chain_data.risk_rationale}
                    </div>
                  </div>
                )}

                {/* WHAT - Business Impact */}
                {clause.impact_chain_data.business_impact && (
                  <div className="mb-3">
                    <h5 className="text-xs font-bold text-yellow-400 mb-1">WHAT is the business impact?</h5>
                    <div className="text-xs text-slate-300 whitespace-pre-line pl-3 border-l-2 border-yellow-500/30">
                      {clause.impact_chain_data.business_impact}
                    </div>
                  </div>
                )}

                {/* HOW - Negotiation Strategy */}
                {clause.impact_chain_data.negotiation_strategy && (
                  <div className="mb-3">
                    <h5 className="text-xs font-bold text-cyan-400 mb-1">HOW to negotiate?</h5>
                    <div className="text-xs text-slate-300 whitespace-pre-line pl-3 border-l-2 border-cyan-500/30">
                      {clause.impact_chain_data.negotiation_strategy}
                    </div>
                  </div>
                )}

                {/* Fallback Position */}
                {clause.impact_chain_data.fallback_position && (
                  <div className="bg-slate-900/60 rounded p-2 mt-2">
                    <h5 className="text-xs font-bold text-orange-400 mb-1">Fallback Position:</h5>
                    <p className="text-xs text-slate-300">{clause.impact_chain_data.fallback_position}</p>
                  </div>
                )}
              </div>
            )}

            {/* Balanced Clause Indicator */}
            {!clause.imbalance?.is_imbalanced && clause.risk_score < 0.4 && (
              <div className="flex items-center gap-2 text-green-400 text-sm">
                <Shield className="w-4 h-4" />
                <span className="font-medium">Fair risk allocation - No concerns detected</span>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Bottom Summary Stats */}
      <div className="bg-slate-800/60 backdrop-blur-xl rounded-xl p-6 border border-slate-700/50">
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
          <div className="text-center p-4 bg-slate-900/60 rounded-lg">
            <div className="text-2xl font-bold text-white mb-1">{analysisData.summary.total_clauses}</div>
            <div className="text-xs text-slate-400">Total Clauses</div>
          </div>
          <div className="text-center p-4 bg-red-500/10 rounded-lg border border-red-500/30">
            <div className="text-2xl font-bold text-red-400 mb-1">{analysisData.summary.risk_distribution.high}</div>
            <div className="text-xs text-red-400">High Risk</div>
          </div>
          <div className="text-center p-4 bg-yellow-500/10 rounded-lg border border-yellow-500/30">
            <div className="text-2xl font-bold text-yellow-400 mb-1">{analysisData.summary.risk_distribution.medium}</div>
            <div className="text-xs text-yellow-400">Medium Risk</div>
          </div>
          <div className="text-center p-4 bg-green-500/10 rounded-lg border border-green-500/30">
            <div className="text-2xl font-bold text-green-400 mb-1">{analysisData.summary.risk_distribution.low}</div>
            <div className="text-xs text-green-400">Low Risk</div>
          </div>
          {/* NEW: Deal Breakers */}
          {analysisData.summary.deal_breakers !== undefined && (
            <div className="text-center p-4 bg-red-600/20 rounded-lg border-2 border-red-500/50">
              <div className="text-2xl font-bold text-red-300 mb-1">{analysisData.summary.deal_breakers}</div>
              <div className="text-xs text-red-300 font-bold">Deal Breakers</div>
            </div>
          )}
          {/* NEW: Risk Multiplier */}
          {analysisData.summary.compound_risk_score && analysisData.summary.base_risk_score && (
            <div className="text-center p-4 bg-purple-500/10 rounded-lg border border-purple-500/30">
              <div className="text-2xl font-bold text-purple-400 mb-1">
                {((analysisData.summary.compound_risk_score / analysisData.summary.base_risk_score) || 1).toFixed(1)}x
              </div>
              <div className="text-xs text-purple-400">Risk Multiplier</div>
            </div>
          )}
        </div>

        {/* NEW: Total Financial Exposure */}
        {analysisData.summary.total_financial_exposure && analysisData.summary.total_financial_exposure.likely_exposure > 0 && (
          <div className="mt-4 p-4 bg-gradient-to-r from-green-900/30 to-red-900/30 border border-green-500/30 rounded-lg">
            <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-green-400" />
              Aggregate Financial Exposure
            </h3>
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-slate-900/60 rounded p-3 text-center">
                <div className="text-xs text-slate-400 mb-1">Best Case</div>
                <div className="text-lg font-bold text-green-400">
                  ${(analysisData.summary.total_financial_exposure.minimum_exposure || 0).toLocaleString()}
                </div>
              </div>
              <div className="bg-slate-900/60 rounded p-3 text-center border-2 border-yellow-500/50">
                <div className="text-xs text-yellow-400 mb-1 font-bold">Most Likely</div>
                <div className="text-xl font-bold text-yellow-400">
                  ${(analysisData.summary.total_financial_exposure.likely_exposure || 0).toLocaleString()}
                </div>
              </div>
              <div className="bg-slate-900/60 rounded p-3 text-center">
                <div className="text-xs text-slate-400 mb-1">Worst Case</div>
                <div className="text-lg font-bold text-red-400">
                  ${(analysisData.summary.total_financial_exposure.maximum_exposure || 0).toLocaleString()}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ExculpatoryAnalysisView;
