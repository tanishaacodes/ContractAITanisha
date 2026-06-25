/**
 * Risk Analysis Component
 * Displays identified risks and conflicts
 */
import React, { useState } from 'react';
import tenderService from '../../services/tenderService';

const RiskAnalysis = ({ risks = [], conflicts = [], tenderId, onReanalyzed }) => {
  const [activeView, setActiveView] = useState('risks');
  const [reanalyzing, setReanalyzing] = useState(false);
  const [reanalyzeError, setReanalyzeError] = useState(null);

  const handleReanalyze = async () => {
    if (!tenderId) return;
    setReanalyzing(true);
    setReanalyzeError(null);
    try {
      const updated = await tenderService.reanalyze(tenderId);
      if (onReanalyzed) onReanalyzed(updated);
    } catch (err) {
      setReanalyzeError(err.response?.data?.error || 'Re-analysis failed.');
    } finally {
      setReanalyzing(false);
    }
  };

  const getSeverityColor = (severity) => {
    const colors = {
      CRITICAL: 'bg-red-100 text-red-800 border-red-300',
      HIGH: 'bg-orange-100 text-orange-800 border-orange-300',
      MEDIUM: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      LOW: 'bg-green-100 text-green-800 border-green-300',
    };
    return colors[severity] || colors.MEDIUM;
  };

  const getSeverityIcon = (severity) => {
    const icons = {
      CRITICAL: '🔴',
      HIGH: '🟠',
      MEDIUM: '🟡',
      LOW: '🟢',
    };
    return icons[severity] || '⚪';
  };

  const categoryStats = risks.reduce((acc, risk) => {
    const severity = risk.severity || 'MEDIUM';
    acc[severity] = (acc[severity] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-4">
          <div className="text-sm text-slate-400 mb-1">Total Risks</div>
          <div className="text-3xl font-bold text-white">{risks.length}</div>
        </div>
        {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((severity) => (
          <div key={severity} className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-400 mb-1">{severity}</div>
                <div className="text-3xl font-bold text-white">
                  {categoryStats[severity] || 0}
                </div>
              </div>
              <div className="text-3xl">{getSeverityIcon(severity)}</div>
            </div>
          </div>
        ))}
      </div>

      {/* View Toggle */}
      <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-1 inline-flex">
        <button
          onClick={() => setActiveView('risks')}
          className={`px-6 py-2 rounded-md text-sm font-medium transition-colors ${
            activeView === 'risks'
              ? 'bg-blue-600 text-white'
              : 'text-slate-300 hover:text-white'
          }`}
        >
          Risks ({risks.length})
        </button>
        <button
          onClick={() => setActiveView('conflicts')}
          className={`px-6 py-2 rounded-md text-sm font-medium transition-colors ${
            activeView === 'conflicts'
              ? 'bg-blue-600 text-white'
              : 'text-slate-300 hover:text-white'
          }`}
        >
          Conflicts ({conflicts.length})
        </button>
      </div>

      {/* Risks View */}
      {activeView === 'risks' && (
        <div className="space-y-4">
          {risks.length === 0 ? (
            <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-12 text-center">
              <div className="text-6xl mb-4">✅</div>
              <h3 className="text-lg font-medium text-white mb-2">No Risks Detected</h3>
              <p className="text-slate-300 mb-4">This tender appears to have standard terms.</p>
              {tenderId && (
                <div>
                  <p className="text-slate-500 text-sm mb-3">
                    Run Re-analyze to apply the latest risk detection patterns.
                  </p>
                  {reanalyzeError && <p className="text-red-400 text-sm mb-3">{reanalyzeError}</p>}
                  <button
                    onClick={handleReanalyze}
                    disabled={reanalyzing}
                    className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white text-sm rounded-lg disabled:opacity-50 inline-flex items-center"
                  >
                    {reanalyzing ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Re-analyzing...
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                        Re-analyze for Risks
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>
          ) : (
            risks.map((risk, index) => (
              <div
                key={index}
                className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-start">
                    <div className="text-3xl mr-4">{getSeverityIcon(risk.severity)}</div>
                    <div>
                      <h3 className="text-lg font-bold text-white mb-1">
                        {risk.category.replace(/_/g, ' ')}
                      </h3>
                      {risk.clause_reference && (
                        <span className="text-sm text-slate-400">
                          Reference: {risk.clause_reference}
                        </span>
                      )}
                    </div>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getSeverityColor(risk.severity)}`}>
                    {risk.severity}
                  </span>
                </div>

                <p className="text-slate-200 mb-4">{risk.description}</p>

                {risk.financial_exposure && (
                  <div className="bg-red-900/30 border border-red-700/50 rounded-lg p-3 mb-4">
                    <div className="text-sm text-red-800">
                      <strong>Financial Exposure:</strong> ₹
                      {(risk.financial_exposure / 10000000).toFixed(2)} Cr
                    </div>
                  </div>
                )}

                {risk.mitigation_suggestion && (
                  <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg p-3">
                    <div className="text-sm text-blue-900">
                      <strong>Mitigation:</strong> {risk.mitigation_suggestion}
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* Conflicts View */}
      {activeView === 'conflicts' && (
        <div className="space-y-4">
          {conflicts.length === 0 ? (
            <div className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-12 text-center">
              <div className="text-6xl mb-4">✅</div>
              <h3 className="text-lg font-medium text-white mb-2">No Conflicts Detected</h3>
              <p className="text-slate-300">The tender clauses appear to be consistent.</p>
            </div>
          ) : (
            conflicts.map((conflict, index) => (
              <div
                key={index}
                className="bg-slate-800 rounded-lg shadow-sm border border-slate-700 p-6"
              >
                <div className="flex items-start mb-4">
                  <div className="text-3xl mr-4">⚡</div>
                  <div className="flex-1">
                    <h3 className="text-lg font-bold text-white mb-1">
                      Conflict Detected
                    </h3>
                    <p className="text-sm text-slate-400">
                      Contradiction Score: {(conflict.contradiction_score * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="bg-orange-900/20 border border-orange-600/50 rounded-lg p-4">
                    <div className="text-sm text-orange-400 mb-2 font-semibold">
                      Clause A {conflict.clause_a_reference && `(${conflict.clause_a_reference})`}
                    </div>
                    <p className="text-white leading-relaxed">{conflict.clause_a}</p>
                  </div>

                  <div className="text-center text-gray-400">
                    <svg className="w-6 h-6 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
                    </svg>
                  </div>

                  <div className="bg-yellow-900/20 border border-yellow-600/50 rounded-lg p-4">
                    <div className="text-sm text-yellow-400 mb-2 font-semibold">
                      Clause B {conflict.clause_b_reference && `(${conflict.clause_b_reference})`}
                    </div>
                    <p className="text-white leading-relaxed">{conflict.clause_b}</p>
                  </div>

                  {conflict.explanation && (
                    <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg p-4">
                      <div className="text-sm text-blue-900">
                        <strong>Explanation:</strong> {conflict.explanation}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default RiskAnalysis;
