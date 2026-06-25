import React from 'react';
import { X, AlertTriangle, Shield, FileText, TrendingUp, Scale, Users, Info, Target, DollarSign, XOctagon } from 'lucide-react';

/**
 * ExculpatorySummarySidebar Component
 * Full Summary Sidebar based on Prof. Murali's paper
 * Shows comprehensive analysis of exculpatory clauses in construction contracts
 *
 * Core Concepts from Paper:
 * 1. Risk Allocation vs Risk Capability
 * 2. Pattern-based clause identification
 * 3. Imbalanced risk detection
 * 4. Bid decision support
 */
const ExculpatorySummarySidebar = ({ open, onClose, summary, contractName }) => {
  if (!open || !summary) return null;

  const getRiskColor = (level) => {
    switch (level) {
      case 'LOW_RISK':
        return 'text-green-400 bg-green-500/10 border-green-500/30';
      case 'MEDIUM_RISK':
        return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30';
      case 'HIGH_RISK':
        return 'text-orange-400 bg-orange-500/10 border-orange-500/30';
      case 'VERY_HIGH_RISK':
        return 'text-red-400 bg-red-500/10 border-red-500/30';
      default:
        return 'text-slate-400 bg-slate-500/10 border-slate-500/30';
    }
  };

  const getRiskIcon = (level) => {
    switch (level) {
      case 'LOW_RISK':
        return <Shield className="w-5 h-5" />;
      case 'MEDIUM_RISK':
        return <Info className="w-5 h-5" />;
      case 'HIGH_RISK':
      case 'VERY_HIGH_RISK':
        return <AlertTriangle className="w-5 h-5" />;
      default:
        return <Info className="w-5 h-5" />;
    }
  };

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
        onClick={onClose}
      />

      {/* Sidebar */}
      <div className="fixed right-0 top-0 h-full w-[480px] bg-gradient-to-b from-slate-900 via-slate-900 to-slate-950 shadow-2xl z-50 overflow-y-auto border-l border-cyan-500/20">
        {/* Header */}
        <div className="sticky top-0 bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border-b border-cyan-500/30 p-6 z-10">
          <div className="flex items-start justify-between mb-2">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-cyan-500/10 rounded-lg border border-cyan-500/30">
                <FileText className="w-6 h-6 text-cyan-400" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">Contract Analysis</h2>
                <p className="text-xs text-slate-400 mt-1">Exculpatory Clause Detection</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-slate-700/50 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-slate-400" />
            </button>
          </div>
          {contractName && (
            <div className="text-sm text-cyan-300 font-medium mt-2 px-2 py-1 bg-cyan-500/5 rounded border border-cyan-500/20">
              {contractName}
            </div>
          )}
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Overall Recommendation */}
          <div className={`rounded-xl p-5 border-2 ${getRiskColor(summary.recommendation?.decision)}`}>
            <div className="flex items-start gap-3 mb-3">
              {getRiskIcon(summary.recommendation?.decision)}
              <div className="flex-1">
                <h3 className="font-bold text-base mb-1">
                  {summary.recommendation?.decision?.replace(/_/g, ' ') || 'Risk Assessment'}
                </h3>
                <p className="text-sm opacity-90">
                  {summary.recommendation?.message || 'Analysis complete'}
                </p>
              </div>
            </div>
          </div>

          {/* Risk Distribution */}
          <div className="bg-slate-800/60 backdrop-blur-xl rounded-xl p-5 border border-slate-700/50">
            <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-cyan-400" />
              Risk Distribution
            </h3>

            <div className="space-y-3">
              {/* High Risk */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-slate-300">High Risk Clauses</span>
                  <span className="text-xs font-bold text-red-400">
                    {summary.risk_distribution?.high || 0} ({summary.risk_percentages?.high || 0}%)
                  </span>
                </div>
                <div className="w-full bg-slate-700/50 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-red-600 to-red-500 h-full rounded-full transition-all duration-500"
                    style={{ width: `${summary.risk_percentages?.high || 0}%` }}
                  />
                </div>
              </div>

              {/* Medium Risk */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-slate-300">Medium Risk Clauses</span>
                  <span className="text-xs font-bold text-yellow-400">
                    {summary.risk_distribution?.medium || 0} ({summary.risk_percentages?.medium || 0}%)
                  </span>
                </div>
                <div className="w-full bg-slate-700/50 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-yellow-600 to-yellow-500 h-full rounded-full transition-all duration-500"
                    style={{ width: `${summary.risk_percentages?.medium || 0}%` }}
                  />
                </div>
              </div>

              {/* Low Risk */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-slate-300">Low Risk Clauses</span>
                  <span className="text-xs font-bold text-green-400">
                    {summary.risk_distribution?.low || 0} ({summary.risk_percentages?.low || 0}%)
                  </span>
                </div>
                <div className="w-full bg-slate-700/50 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-green-600 to-green-500 h-full rounded-full transition-all duration-500"
                    style={{ width: `${summary.risk_percentages?.low || 0}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Risk Imbalance Alert */}
          {summary.imbalanced_clauses > 0 && (
            <div className="bg-orange-500/10 border-2 border-orange-500/30 rounded-xl p-4">
              <div className="flex items-start gap-3">
                <Scale className="w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-bold text-sm text-orange-300 mb-1">
                    Risk Allocation Imbalance Detected
                  </h4>
                  <p className="text-xs text-orange-200/80">
                    {summary.imbalanced_clauses} clause{summary.imbalanced_clauses > 1 ? 's' : ''} allocate risk to parties without control
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Risk Categories Breakdown */}
          {summary.category_breakdown && Object.keys(summary.category_breakdown).length > 0 && (
            <div className="bg-slate-800/60 backdrop-blur-xl rounded-xl p-5 border border-slate-700/50">
              <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-cyan-400" />
                Risk Categories
              </h3>
              <div className="space-y-2">
                {Object.entries(summary.category_breakdown).map(([category, count]) => (
                  <div
                    key={category}
                    className="flex items-center justify-between py-2 px-3 bg-slate-700/30 rounded-lg border border-slate-600/30"
                  >
                    <span className="text-xs font-medium text-slate-300">
                      {category.replace(/_/g, ' ')}
                    </span>
                    <span className="px-2 py-1 bg-cyan-500/20 rounded text-xs font-bold text-cyan-300">
                      {count}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Key Metrics */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-slate-800/60 backdrop-blur-xl rounded-lg p-4 border border-slate-700/50">
              <div className="text-xs text-slate-400 mb-1">Total Clauses</div>
              <div className="text-2xl font-bold text-white">{summary.total_clauses || 0}</div>
            </div>
            <div className="bg-red-500/10 backdrop-blur-xl rounded-lg p-4 border border-red-500/30">
              <div className="text-xs text-red-400 mb-1">Exculpatory</div>
              <div className="text-2xl font-bold text-red-400">{summary.risk_distribution?.high || 0}</div>
            </div>
          </div>

          {/* Detailed Analysis Section */}
          <div className="bg-slate-800/60 backdrop-blur-xl rounded-xl p-5 border border-slate-700/50">
            <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
              <Users className="w-4 h-4 text-cyan-400" />
              Risk Analysis Summary
            </h3>

            <div className="space-y-4 text-sm text-slate-300">
              {/* Pattern Detection Summary */}
              <div>
                <h4 className="font-semibold text-white mb-2">Pattern Detection</h4>
                <p className="text-xs leading-relaxed text-slate-400">
                  {summary.risk_distribution?.high > 0 ? (
                    <>Detected <span className="text-red-400 font-bold">{summary.risk_distribution.high}</span> high-risk exculpatory patterns that shift unfair liability to the contractor.</>
                  ) : summary.risk_distribution?.medium > 0 ? (
                    <>Found <span className="text-yellow-400 font-bold">{summary.risk_distribution.medium}</span> clauses with moderate risk patterns requiring review.</>
                  ) : (
                    <>No high-risk exculpatory patterns detected. Standard contractual terms identified.</>
                  )}
                </p>
              </div>

              {/* Risk Allocation Analysis */}
              <div>
                <h4 className="font-semibold text-white mb-2">Risk Allocation</h4>
                <p className="text-xs leading-relaxed text-slate-400">
                  {summary.imbalanced_clauses > 0 ? (
                    <>
                      <span className="text-orange-400 font-bold">{summary.imbalanced_clauses}</span> clause{summary.imbalanced_clauses > 1 ? 's allocate' : ' allocates'} risk to parties without control capability.
                      This violates fair risk allocation principles from Prof. Murali's research.
                    </>
                  ) : (
                    <>Risk allocation appears balanced - risks are assigned to parties with control capability.</>
                  )}
                </p>
              </div>

              {/* Bid Strategy */}
              <div>
                <h4 className="font-semibold text-white mb-2">Bid Strategy</h4>
                <p className="text-xs leading-relaxed text-slate-400">
                  {summary.recommendation?.decision === 'VERY_HIGH_RISK' && (
                    <>Consider <span className="text-red-400 font-bold">rejecting bid</span> or demand major clause revisions. High financial exposure detected.</>
                  )}
                  {summary.recommendation?.decision === 'HIGH_RISK' && (
                    <>Proceed with <span className="text-orange-400 font-bold">defensive pricing</span>. Negotiate key clauses or include contingency reserves.</>
                  )}
                  {summary.recommendation?.decision === 'MEDIUM_RISK' && (
                    <>Acceptable with <span className="text-yellow-400 font-bold">moderate adjustments</span>. Negotiate specific high-risk clauses before signing.</>
                  )}
                  {summary.recommendation?.decision === 'LOW_RISK' && (
                    <>Safe to proceed with <span className="text-green-400 font-bold">standard pricing</span>. Minor concerns can be addressed through negotiation.</>
                  )}
                </p>
              </div>

              {/* NLP Confidence */}
              <div className="pt-3 border-t border-slate-700/50">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-500">Analysis Method</span>
                  <span className="text-cyan-400 font-medium">MiniLM Embeddings + Pattern Matching</span>
                </div>
                <div className="flex items-center justify-between text-xs mt-1">
                  <span className="text-slate-500">Similarity Threshold</span>
                  <span className="text-cyan-400 font-medium">50% (Balanced Detection)</span>
                </div>
              </div>
            </div>
          </div>

          {/* NEW: Deal Breakers and Negotiation Priorities */}
          {summary.deal_breakers > 0 && (
            <div className="bg-red-600/20 backdrop-blur-xl rounded-xl p-5 border-2 border-red-500/50 shadow-[0_0_20px_rgba(239,68,68,0.2)]">
              <h3 className="text-sm font-bold text-red-300 mb-3 flex items-center gap-2">
                <XOctagon className="w-5 h-5 animate-pulse" />
                Critical Deal Breakers
              </h3>
              <div className="bg-red-500/10 rounded-lg p-3 mb-3">
                <p className="text-xs text-red-200/90 leading-relaxed">
                  <span className="font-bold text-red-300">{summary.deal_breakers}</span> clause{summary.deal_breakers > 1 ? 's contain' : ' contains'} extreme risks that could
                  bankrupt your company. These are severe enough to consider walking away if not negotiated.
                </p>
              </div>
            </div>
          )}

          {/* NEW: Financial Exposure Summary */}
          {summary.total_financial_exposure && summary.total_financial_exposure.likely_exposure > 0 && (
            <div className="bg-gradient-to-br from-green-900/20 to-red-900/20 backdrop-blur-xl rounded-xl p-5 border border-green-500/30">
              <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                <DollarSign className="w-5 h-5 text-green-400" />
                Total Financial Exposure
              </h3>
              <div className="grid grid-cols-3 gap-2 mb-3">
                <div className="bg-slate-900/60 rounded p-2 text-center">
                  <div className="text-xs text-slate-400 mb-1">Best</div>
                  <div className="text-sm font-bold text-green-400">
                    ${(summary.total_financial_exposure.minimum_exposure / 1000).toFixed(0)}K
                  </div>
                </div>
                <div className="bg-slate-900/60 rounded p-2 text-center border-2 border-yellow-500/40">
                  <div className="text-xs text-yellow-400 mb-1 font-bold">Likely</div>
                  <div className="text-base font-bold text-yellow-400">
                    ${(summary.total_financial_exposure.likely_exposure / 1000).toFixed(0)}K
                  </div>
                </div>
                <div className="bg-slate-900/60 rounded p-2 text-center">
                  <div className="text-xs text-slate-400 mb-1">Worst</div>
                  <div className="text-sm font-bold text-red-400">
                    ${(summary.total_financial_exposure.maximum_exposure / 1000).toFixed(0)}K
                  </div>
                </div>
              </div>
              <p className="text-xs text-slate-400">
                Add this exposure to your bid pricing or negotiate to reduce liability.
              </p>
            </div>
          )}

          {/* NEW: Prioritized Negotiation Points */}
          {summary.negotiation_priorities && summary.negotiation_priorities.length > 0 && (
            <div className="bg-cyan-500/5 backdrop-blur-xl rounded-xl p-5 border border-cyan-500/20">
              <h3 className="text-sm font-bold text-cyan-300 mb-3 flex items-center gap-2">
                <Target className="w-5 h-5" />
                Negotiation Priorities
              </h3>
              <div className="space-y-3">
                {summary.negotiation_priorities.slice(0, 5).map((priority, idx) => (
                  <div key={idx} className="bg-slate-900/60 rounded-lg p-3 border border-slate-700/50">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="flex items-center justify-center w-6 h-6 rounded-full bg-cyan-500/20 text-cyan-300 text-xs font-bold">
                        {priority.rank}
                      </span>
                      <h4 className="text-xs font-bold text-white flex-1">
                        {priority.risk_type.replace(/_/g, ' ')}
                      </h4>
                      <span className={`px-2 py-0.5 text-xs font-bold rounded ${
                        priority.severity === 'CRITICAL' ? 'bg-red-600/30 text-red-300' :
                        priority.severity === 'HIGH' ? 'bg-orange-600/30 text-orange-300' :
                        'bg-yellow-600/30 text-yellow-300'
                      }`}>
                        {priority.severity}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mb-2">{priority.description}</p>
                    <div className="text-xs text-cyan-300/80 bg-cyan-500/5 rounded p-2">
                      <span className="font-semibold">Action:</span> {priority.action}
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                      Clauses: {priority.involved_clauses.join(', ')}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* NEW: Compound Risk Score */}
          {summary.compound_risk_score && summary.base_risk_score && (
            <div className="bg-purple-500/5 backdrop-blur-xl rounded-xl p-5 border border-purple-500/20">
              <h3 className="text-sm font-bold text-purple-300 mb-3">Risk Amplification Analysis</h3>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-slate-400">Base Risk Score:</span>
                <span className="text-sm font-bold text-white">{(summary.base_risk_score * 100).toFixed(0)}%</span>
              </div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-slate-400">Compound Risk Score:</span>
                <span className="text-sm font-bold text-purple-400">{(summary.compound_risk_score * 100).toFixed(0)}%</span>
              </div>
              <div className="flex items-center justify-between pt-2 border-t border-purple-500/20">
                <span className="text-xs text-purple-300 font-bold">Risk Multiplier:</span>
                <span className="text-lg font-bold text-purple-400">
                  {(summary.compound_risk_score / summary.base_risk_score).toFixed(2)}x
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-2">
                Clause interactions amplify individual risks. Compound score is higher due to dangerous clause combinations.
              </p>
            </div>
          )}

          {/* Top Risk Clauses (if any) */}
          {(summary.risk_distribution?.high > 0 || summary.risk_distribution?.medium > 0) && (
            <div className="bg-red-500/5 backdrop-blur-xl rounded-xl p-5 border border-red-500/20">
              <h3 className="text-sm font-bold text-red-300 mb-3 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" />
                Action Required
              </h3>
              <div className="space-y-2 text-xs text-red-200/80">
                {summary.risk_distribution?.high > 0 && (
                  <div className="flex items-start gap-2">
                    <div className="w-1.5 h-1.5 bg-red-400 rounded-full mt-1.5 flex-shrink-0" />
                    <span>Review all HIGH RISK clauses and negotiate removal or modification</span>
                  </div>
                )}
                {summary.risk_distribution?.medium > 0 && (
                  <div className="flex items-start gap-2">
                    <div className="w-1.5 h-1.5 bg-yellow-400 rounded-full mt-1.5 flex-shrink-0" />
                    <span>Assess MEDIUM RISK clauses and determine if pricing adjustments needed</span>
                  </div>
                )}
                {summary.imbalanced_clauses > 0 && (
                  <div className="flex items-start gap-2">
                    <div className="w-1.5 h-1.5 bg-orange-400 rounded-full mt-1.5 flex-shrink-0" />
                    <span>Focus on imbalanced risk allocation - request fair distribution</span>
                  </div>
                )}
              </div>
            </div>
          )}

        </div>
      </div>
    </>
  );
};

export default ExculpatorySummarySidebar;
