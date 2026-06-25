/**
 * ClauseRewritesPanel.jsx
 * ========================
 * AI-powered clause rewriting suggestions
 * Shows LLM-generated improvements for high-risk clauses
 */

import { useState, useEffect } from 'react';
import { Sparkles, ChevronDown, ChevronUp, Check, X, AlertTriangle } from 'lucide-react';
import { getClauseRewrites, rewriteClause } from '../../services/arbitrationService';

const STRATEGY_OPTIONS = [
  { value: 'buyer_favorable', label: 'Buyer Favorable', color: '#68BC00' },
  { value: 'balanced', label: 'Balanced', color: '#4C8EDA' },
  { value: 'supplier_favorable', label: 'Supplier Favorable', color: '#F79767' },
];

export default function ClauseRewritesPanel({ analysisId }) {
  const [rewrites, setRewrites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedId, setExpandedId] = useState(null);

  useEffect(() => {
    if (analysisId) {
      loadRewrites();
    }
  }, [analysisId]);

  const loadRewrites = async () => {
    try {
      setLoading(true);
      const data = await getClauseRewrites(analysisId);
      setRewrites(data.rewrites || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
        <p className="text-red-400">Failed to load clause rewrites: {error}</p>
      </div>
    );
  }

  if (!rewrites || rewrites.length === 0) {
    return (
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-8 text-center">
        <Sparkles className="mx-auto mb-4" size={48} color="#4C8EDA" />
        <h3 className="text-lg font-semibold mb-2">No AI Rewrites Available</h3>
        <p className="text-slate-400 text-sm">
          Run a new analysis with clause rewriting enabled to see AI-powered improvements.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles size={20} color="#4C8EDA" />
          <h3 className="text-lg font-semibold">AI Clause Rewrites</h3>
        </div>
        <div className="text-sm text-slate-400">
          {rewrites.length} improvement{rewrites.length !== 1 ? 's' : ''} suggested
        </div>
      </div>

      {/* Rewrites List */}
      <div className="space-y-3">
        {rewrites.map((rewrite) => {
          const isExpanded = expandedId === rewrite.id;
          const riskReduction = ((rewrite.original_risk_score - rewrite.predicted_risk_score) / rewrite.original_risk_score * 100);

          return (
            <div
              key={rewrite.id}
              className="bg-slate-800/50 border border-slate-700 rounded-lg overflow-hidden"
            >
              {/* Summary */}
              <div
                className="p-4 cursor-pointer hover:bg-slate-800/70 transition-colors"
                onClick={() => setExpandedId(isExpanded ? null : rewrite.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="px-2 py-1 rounded text-xs font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                        {rewrite.rewrite_strategy}
                      </span>
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${
                          riskReduction > 30
                            ? 'bg-green-500/10 text-green-400 border border-green-500/30'
                            : riskReduction > 15
                            ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/30'
                            : 'bg-blue-500/10 text-blue-400 border border-blue-500/30'
                        }`}
                      >
                        {riskReduction.toFixed(0)}% risk reduction
                      </span>
                    </div>
                    <p className="text-sm text-slate-300 line-clamp-2">
                      {rewrite.original_text.substring(0, 150)}...
                    </p>
                  </div>
                  <div className="ml-4">
                    {isExpanded ? (
                      <ChevronUp size={20} className="text-slate-400" />
                    ) : (
                      <ChevronDown size={20} className="text-slate-400" />
                    )}
                  </div>
                </div>
              </div>

              {/* Expanded Details */}
              {isExpanded && (
                <div className="border-t border-slate-700 p-4 space-y-4">
                  {/* Risk Comparison */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
                      <div className="text-xs text-red-400 mb-1">Original Risk</div>
                      <div className="text-2xl font-bold text-red-400">
                        {(rewrite.original_risk_score * 100).toFixed(0)}
                      </div>
                    </div>
                    <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-3">
                      <div className="text-xs text-green-400 mb-1">New Risk</div>
                      <div className="text-2xl font-bold text-green-400">
                        {(rewrite.predicted_risk_score * 100).toFixed(0)}
                      </div>
                    </div>
                  </div>

                  {/* Original Text */}
                  <div>
                    <div className="text-xs text-slate-400 mb-2 flex items-center gap-1">
                      <X size={14} className="text-red-400" />
                      Original Clause
                    </div>
                    <div className="bg-slate-900/50 border border-slate-700 rounded p-3 text-sm text-slate-300">
                      {rewrite.original_text}
                    </div>
                  </div>

                  {/* Rewritten Text */}
                  <div>
                    <div className="text-xs text-slate-400 mb-2 flex items-center gap-1">
                      <Check size={14} className="text-green-400" />
                      AI-Generated Improvement
                    </div>
                    <div className="bg-green-500/5 border border-green-500/30 rounded p-3 text-sm text-slate-300">
                      {rewrite.rewritten_text}
                    </div>
                  </div>

                  {/* Improvements */}
                  {rewrite.improvements && rewrite.improvements.length > 0 && (
                    <div>
                      <div className="text-xs text-slate-400 mb-2">Key Improvements</div>
                      <div className="flex flex-wrap gap-2">
                        {rewrite.improvements.map((imp, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-1 rounded text-xs bg-cyan-500/10 text-cyan-400 border border-cyan-500/30"
                          >
                            {imp}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Status */}
                  <div className="flex items-center justify-between pt-2 border-t border-slate-700">
                    <div className="flex items-center gap-2 text-xs text-slate-400">
                      <div className={`w-2 h-2 rounded-full ${
                        rewrite.status === 'APPROVED' ? 'bg-green-500' :
                        rewrite.status === 'REJECTED' ? 'bg-red-500' :
                        'bg-yellow-500'
                      }`}></div>
                      Status: {rewrite.status}
                    </div>
                    <div className="text-xs text-slate-500">
                      Model: {rewrite.llm_model}
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
