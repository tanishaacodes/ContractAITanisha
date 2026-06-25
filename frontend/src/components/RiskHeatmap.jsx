import React from 'react';
import useThemeStore from '../store/themeStore';

/**
 * RiskHeatmap Component
 *
 * Displays a color-coded heatmap of contract risks by clause category.
 * Feature 3.1: Risk Heatmap UI Component
 *
 * Color Encoding:
 * - 🟢 Green (SAFE): 0.90-1.00 similarity
 * - 🟡 Yellow (REVIEW): 0.75-0.90 similarity
 * - 🔴 Red (HIGH_RISK): <0.75 similarity
 * - ⚫ Grey (MISSING): Missing clause/safeguard
 */

const RiskHeatmap = ({ risks, onSelect, selectedClauseType }) => {
  const { theme } = useThemeStore();

  // Color mapping based on risk status
  const getStatusColor = (status, riskScore) => {
    switch (status) {
      case 'SAFE':
        return {
          bg: 'bg-green-500',
          bgHover: 'hover:bg-green-600',
          text: 'text-white',
          border: 'border-green-600'
        };
      case 'REVIEW':
        return {
          bg: 'bg-yellow-400',
          bgHover: 'hover:bg-yellow-500',
          text: 'text-gray-900',
          border: 'border-yellow-500'
        };
      case 'HIGH_RISK':
        return {
          bg: 'bg-red-500',
          bgHover: 'hover:bg-red-600',
          text: 'text-white',
          border: 'border-red-600'
        };
      case 'MISSING':
      case 'WEAK':
        return {
          bg: 'bg-gray-500',
          bgHover: 'hover:bg-gray-600',
          text: 'text-white',
          border: 'border-gray-600'
        };
      default:
        return {
          bg: 'bg-gray-400',
          bgHover: 'hover:bg-gray-500',
          text: 'text-white',
          border: 'border-gray-500'
        };
    }
  };

  // Format risk score as percentage
  const formatRiskScore = (score, status) => {
    if (status === 'MISSING') {
      return 'N/A';
    }
    // For deviation scores, higher is better
    return `${(score * 100).toFixed(0)}%`;
  };

  // Get status emoji
  const getStatusEmoji = (status) => {
    switch (status) {
      case 'SAFE':
        return '✅';
      case 'REVIEW':
        return '⚠️';
      case 'HIGH_RISK':
        return '🔴';
      case 'MISSING':
        return '❌';
      case 'WEAK':
        return '⚠️';
      default:
        return '❓';
    }
  };

  if (!risks || risks.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>No risk data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="mb-4">
        <h3 className="text-lg font-bold mb-1" style={{ color: theme.colors.textPrimary }}>
          Risk Heatmap
        </h3>
        <p className="text-sm text-gray-500">
          Click on any item to view details
        </p>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 mb-4 p-3 rounded" style={{ backgroundColor: theme.colors.surface }}>
        <div className="flex items-center gap-1 text-sm">
          <div className="w-4 h-4 rounded bg-green-500"></div>
          <span style={{ color: theme.colors.textSecondary }}>Safe (≥90%)</span>
        </div>
        <div className="flex items-center gap-1 text-sm">
          <div className="w-4 h-4 rounded bg-yellow-400"></div>
          <span style={{ color: theme.colors.textSecondary }}>Review (75-90%)</span>
        </div>
        <div className="flex items-center gap-1 text-sm">
          <div className="w-4 h-4 rounded bg-red-500"></div>
          <span style={{ color: theme.colors.textSecondary }}>High Risk (&lt;75%)</span>
        </div>
        <div className="flex items-center gap-1 text-sm">
          <div className="w-4 h-4 rounded bg-gray-500"></div>
          <span style={{ color: theme.colors.textSecondary }}>Missing/Weak</span>
        </div>
      </div>

      {/* Heatmap Items */}
      <div className="grid grid-cols-1 gap-2 max-h-[600px] overflow-y-auto">
        {risks.map((risk, index) => {
          const colors = getStatusColor(risk.status, risk.riskScore);
          const isSelected = selectedClauseType === risk.clauseType;

          return (
            <div
              key={index}
              onClick={() => onSelect(risk)}
              className={`
                ${colors.bg} ${colors.bgHover}
                ${isSelected ? `ring-4 ${colors.border}` : ''}
                p-3 rounded-lg cursor-pointer transition-all duration-200
                transform hover:scale-[1.02] hover:shadow-lg
              `}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{getStatusEmoji(risk.status)}</span>
                    <h4 className={`font-semibold ${colors.text} text-sm`}>
                      {risk.clauseType}
                    </h4>
                  </div>

                  {risk.category && (
                    <p className={`text-xs mt-1 ${colors.text} opacity-80`}>
                      Category: {risk.category.replace(/_/g, ' ')}
                    </p>
                  )}

                  {risk.type && (
                    <p className={`text-xs mt-1 ${colors.text} opacity-80`}>
                      Type: {risk.type === 'DEVIATION' ? 'Deviation' : 'Missing Safeguard'}
                    </p>
                  )}
                </div>

                <div className="text-right">
                  <div className={`text-lg font-bold ${colors.text}`}>
                    {formatRiskScore(risk.riskScore, risk.status)}
                  </div>
                  <div className={`text-xs ${colors.text} opacity-80 uppercase mt-1`}>
                    {risk.status.replace(/_/g, ' ')}
                  </div>
                </div>
              </div>

              {/* Show quick preview on hover */}
              {risk.details && risk.details.risk_type && (
                <div className={`text-xs mt-2 ${colors.text} opacity-90`}>
                  {risk.details.risk_type}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Summary Stats */}
      <div className="mt-4 p-3 rounded" style={{ backgroundColor: theme.colors.surface }}>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <span className="font-semibold" style={{ color: theme.colors.textPrimary }}>
              Total Items:
            </span>
            <span className="ml-2" style={{ color: theme.colors.textSecondary }}>
              {risks.length}
            </span>
          </div>
          <div>
            <span className="font-semibold text-red-500">
              High Risk:
            </span>
            <span className="ml-2" style={{ color: theme.colors.textSecondary }}>
              {risks.filter(r => r.status === 'HIGH_RISK').length}
            </span>
          </div>
          <div>
            <span className="font-semibold text-yellow-500">
              Review:
            </span>
            <span className="ml-2" style={{ color: theme.colors.textSecondary }}>
              {risks.filter(r => r.status === 'REVIEW').length}
            </span>
          </div>
          <div>
            <span className="font-semibold text-green-500">
              Safe:
            </span>
            <span className="ml-2" style={{ color: theme.colors.textSecondary }}>
              {risks.filter(r => r.status === 'SAFE').length}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RiskHeatmap;
