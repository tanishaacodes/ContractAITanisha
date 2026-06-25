import React from 'react';

/**
 * ClauseHeatmap Component
 * Displays clause acceptance rates as a horizontal bar chart
 */
const ClauseHeatmap = ({ data }) => {
  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="text-center text-slate-400 py-8">
        No clause acceptance data available
      </div>
    );
  }

  const getBarColor = (score) => {
    if (score > 0.7) return 'bg-gradient-to-r from-emerald-500 to-green-400';
    if (score > 0.4) return 'bg-gradient-to-r from-yellow-500 to-amber-400';
    return 'bg-gradient-to-r from-red-600 to-red-400';
  };

  const getTextColor = (score) => {
    if (score > 0.7) return 'text-emerald-400';
    if (score > 0.4) return 'text-yellow-400';
    return 'text-red-400';
  };

  // Sort by acceptance rate (lowest first to show problem areas)
  const sortedEntries = Object.entries(data).sort(([, a], [, b]) => a - b);

  return (
    <div className="space-y-4">
      {sortedEntries.map(([clause, score]) => (
        <div key={clause} className="group">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-slate-300 group-hover:text-white transition-colors">
              {clause}
            </span>
            <span className={`text-sm font-bold ${getTextColor(score)}`}>
              {Math.round(score * 100)}%
            </span>
          </div>

          <div className="relative w-full h-6 bg-slate-700/30 rounded-full overflow-hidden group-hover:shadow-[0_0_15px_rgba(6,182,212,0.2)] transition-shadow">
            <div
              className={`h-full ${getBarColor(score)} transition-all duration-500 ease-out flex items-center justify-end pr-2`}
              style={{ width: `${score * 100}%` }}
            >
              {score > 0.15 && (
                <span className="text-xs font-semibold text-white">
                  {Math.round(score * 100)}%
                </span>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ClauseHeatmap;
