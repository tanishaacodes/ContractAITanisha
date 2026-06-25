import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import { riskToColor, formatExposure } from '../../utils/riskColor';

/**
 * HeatmapCell with Portal-based tooltip
 */
const HeatmapCell = ({ risk, clauseA, clauseB }) => {
  const [showTooltip, setShowTooltip] = useState(false);
  if (!risk) {
    return (
      <div
        className="bg-slate-800/30 border border-slate-700/30"
        style={{ width: '100px', height: '60px' }}
      />
    );
  }

  const { financial_exposure, confidence, risk_type, severity = 'MEDIUM', description } = risk;
  const colorClass = riskToColor(financial_exposure, confidence);

  return (
    <>
      {/* Cell */}
      <div
        className={`border border-slate-600/30 cursor-pointer transition-all hover:scale-110 hover:border-cyan-400 hover:shadow-[0_0_20px_rgba(6,182,212,0.6)] flex items-center justify-center ${colorClass}`}
        style={{ width: '100px', height: '60px' }}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        {financial_exposure > 0 && (
          <span className="text-xs font-bold drop-shadow-lg">
            {formatExposure(financial_exposure)}
          </span>
        )}
      </div>

      {/* Tooltip Portal - Renders at body level */}
      {showTooltip && createPortal(
        <div className="fixed left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 z-[10000] pointer-events-none animate-in fade-in duration-200">
          <div className="bg-slate-900 border-2 border-cyan-500 rounded-lg shadow-[0_0_50px_cyan] p-4 w-96">
          {/* Header */}
          <div className="flex items-center gap-2 mb-3">
            <svg className="w-5 h-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <h3 className="font-bold text-white">Silent Risk Detected</h3>
          </div>

          {/* Risk Type */}
          <div className="mb-2">
            <span className="px-2 py-1 bg-purple-600 text-white text-xs font-bold rounded">
              {risk_type.replace(/_/g, ' ')}
            </span>
          </div>

          {/* Clauses */}
          <div className="mb-3 p-2 bg-purple-900/30 border border-purple-500 rounded">
            <p className="text-xs text-purple-300 font-bold">Interacting Clauses:</p>
            <p className="text-xs text-white mt-1">
              {clauseA} <span className="text-cyan-400">+</span> {clauseB}
            </p>
          </div>

          {/* Metrics */}
          <div className="grid grid-cols-2 gap-2 mb-3">
            <div className="p-2 bg-red-900/30 border border-red-500 rounded">
              <p className="text-xs text-red-400 font-bold">Exposure</p>
              <p className="text-lg font-bold text-white">
                {formatExposure(financial_exposure)}
              </p>
            </div>
            <div className="p-2 bg-cyan-900/30 border border-cyan-500 rounded">
              <p className="text-xs text-cyan-400 font-bold">Confidence</p>
              <p className="text-lg font-bold text-white">
                {Math.round(confidence * 100)}%
              </p>
            </div>
          </div>

          {/* Severity */}
          <div className="text-center">
            <span className={`px-4 py-1 rounded-full text-xs font-bold ${
              severity === 'CRITICAL' ? 'bg-red-900 text-white' :
              severity === 'HIGH' ? 'bg-red-600 text-white' :
              'bg-yellow-500 text-black'
            }`}>
              {severity}
            </span>
          </div>
          </div>
        </div>,
        document.body
      )}
    </>
  );
};

export default HeatmapCell;
