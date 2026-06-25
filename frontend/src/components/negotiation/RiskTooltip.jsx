import React from 'react';
import { X, AlertTriangle } from 'lucide-react';
import { formatExposure, riskTypeToBadgeColor, severityToColor } from '../../utils/riskColor';

/**
 * RiskTooltip Component
 * Displays detailed information about a silent risk on hover/click
 * Fixed positioning for proper display over scrollable heatmap
 */
const RiskTooltip = ({ risk, clauseA, clauseB, onClose }) => {
  const {
    risk_type,
    description,
    financial_exposure,
    confidence,
    severity = 'MEDIUM',
  } = risk;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-[9998] bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Tooltip Modal */}
      <div className="fixed z-[9999] left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 max-w-[90vw] bg-slate-900 border-2 border-cyan-500/50 backdrop-blur-xl rounded-lg shadow-[0_0_50px_rgba(6,182,212,0.5)] p-4 animate-fadeIn">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-400" style={{ filter: 'drop-shadow(0 0 8px rgba(239, 68, 68, 0.5))' }} />
            <h3 className="font-bold text-white text-sm">Silent Risk Detected</h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Risk Type Badge */}
        <div className="mb-3">
          <span className={`inline-block px-2 py-1 rounded text-xs font-semibold ${riskTypeToBadgeColor(risk_type)}`}>
            {risk_type.replace(/_/g, ' ')}
          </span>
        </div>

        {/* Clause Pair */}
        <div className="mb-3 p-2 bg-purple-500/10 border border-purple-500/30 rounded">
          <p className="text-xs font-semibold text-purple-400 mb-1">Interacting Clauses:</p>
          <p className="text-xs text-slate-300">
            <span className="font-medium">{clauseA}</span>
            {' + '}
            <span className="font-medium">{clauseB}</span>
          </p>
        </div>

        {/* Description */}
        <div className="mb-3">
          <p className="text-sm text-slate-300 leading-relaxed">
            {description}
          </p>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-2 gap-2 mb-3">
          <div className="p-2 bg-red-500/10 border border-red-500/30 rounded">
            <p className="text-xs text-red-400 font-semibold">Financial Exposure</p>
            <p className="text-lg font-bold text-white">
              {formatExposure(financial_exposure)}
            </p>
          </div>
          <div className="p-2 bg-cyan-500/10 border border-cyan-500/30 rounded">
            <p className="text-xs text-cyan-400 font-semibold">Confidence</p>
            <p className="text-lg font-bold text-white">
              {Math.round(confidence * 100)}%
            </p>
          </div>
        </div>

        {/* Severity */}
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs text-slate-400 font-medium">Severity:</span>
          <span className={`px-3 py-1 rounded-full text-xs font-bold ${severityToColor(severity)}`}>
            {severity}
          </span>
        </div>

        {/* Action Hint */}
        <div className="pt-3 border-t border-slate-700/50">
          <p className="text-xs text-slate-400 italic">
            This risk emerges from clause interaction rather than individual wording
          </p>
        </div>
      </div>
    </>
  );
};

export default RiskTooltip;
